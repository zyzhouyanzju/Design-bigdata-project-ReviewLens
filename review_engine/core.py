"""Review normalization, evidence extraction, aggregation and retrieval."""
from __future__ import annotations
import hashlib
import html
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?|[0-9]+", re.I)

def clean(value):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]*>', ' ', html.unescape(str(value or '')))).strip()

def matches(text, phrase):
    return list(re.finditer(r'(?<!\w)' + re.escape(phrase.lower()) + r'(?!\w)', text.lower()))

def normalize(raw, line_number):
    product = clean(raw.get('parent_asin') or raw.get('product_id'))
    text = clean(raw.get('text') or raw.get('review_text'))
    if not product or not text:
        return None
    identity = clean(raw.get('review_id')) or hashlib.sha256(f'{product}\0{raw.get("user_id", "")}\0{raw.get("timestamp", "")}\0{text}'.encode()).hexdigest()[:20]
    return {'review_id': identity, 'source_line': line_number, 'product_id': product, 'product_name': clean(raw.get('product_name')) or product, 'text': text, 'rating': raw.get('rating'), 'timestamp': raw.get('timestamp'), 'verified_purchase': raw.get('verified_purchase')}

def clauses(text):
    # Keep offsets so each evidence span can be found in the original normalized review.
    for m in re.finditer(r'[^.!?;]+(?:[.!?;]|$)', text):
        clause_text=m.group(); bounds=[]; last=0
        for marker in re.finditer(r'\b(?:but|however|although|yet)\b',clause_text,re.I):
            bounds.append((last,marker.start())); last=marker.end()
        bounds.append((last,len(clause_text)))
        for lo,hi in bounds:
            raw=clause_text[lo:hi]; lead=len(raw)-len(raw.lstrip(' ,\t\r\n')); content=raw.strip(' ,\t\r\n')
            if content:
                start = m.start()+lo+lead
                yield content, start, start+len(content)

def extract(review, config):
    results=[]
    for clause, start, end in clauses(review['text']):
        lowered=clause.lower(); tokens=list(TOKEN.finditer(lowered))
        aspects={name:[m for phrase in phrases for m in matches(lowered, phrase)] for name,phrases in config['aspects'].items()}
        aspects={name:spans for name,spans in aspects.items() if spans}
        if not aspects: continue
        scenes=[name for name, phrases in config['scenes'].items() if any(matches(lowered, p) for p in phrases)] or ['未知']
        opinions=[]
        for polarity in ('positive','negative'):
            for word in config[polarity]:
                for hit in matches(lowered,word):
                    index=next((i for i,t in enumerate(tokens) if t.start() <= hit.start() < t.end()),0)
                    prior=[t.group() for t in tokens[max(0,index-3):index]]
                    sign=1 if polarity=='positive' else -1
                    if any(t in config['negations'] for t in prior): sign=-sign
                    opinions.append((hit.start(),sign,word))
        for name, spans in aspects.items():
            # Associate opinion words with their closest aspect, avoiding copying one sentiment to every aspect.
            scores=[]
            for pos, sign, word in opinions:
                distances={a:min(abs(pos-s.start()) for s in ss) for a,ss in aspects.items()}
                if distances[name] == min(distances.values()) and list(distances.values()).count(distances[name]) == 1 and distances[name] <= 70:
                    scores.append(sign)
            score=sum(scores)
            sentiment='positive' if score>0 else 'negative' if score<0 else 'unknown'
            for scene in scenes:
                results.append({'review_id':review['review_id'], 'product_id':review['product_id'], 'aspect':name, 'scene':scene, 'sentiment':sentiment, 'issue_type':'possible_quality' if any(matches(lowered,p) for p in config.get('quality_cues',[])) else 'unclassified', 'evidence':clause, 'start':start, 'end':end, 'rating':review['rating'], 'timestamp':review['timestamp']})
    return results

def wilson(pos, n, z=1.96):
    if not n: return None, None
    p=pos/n; d=1+z*z/n; center=(p+z*z/(2*n))/d; margin=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return center-margin,center+margin

def aggregate(evidence, minimum=20):
    groups=defaultdict(lambda:defaultdict(set))
    for row in evidence:
        groups[(row['product_id'],row['aspect'],row['scene'])][row['review_id']].add(row['sentiment'])
    results=[]
    for (product,aspect,scene), reviews in groups.items():
        counts=Counter('mixed' if {'positive','negative'} <= v else 'positive' if 'positive' in v else 'negative' if 'negative' in v else 'unknown' for v in reviews.values())
        pos,neg=counts['positive'],counts['negative']; n=pos+neg; lo,hi=wilson(pos,n)
        score=(2*min(pos,neg)/n)*min(1, math.log1p(n)/math.log1p(100)) if n>=minimum else None
        results.append({'product_id':product,'aspect':aspect,'scene':scene,'positive':pos,'negative':neg,'mixed':counts['mixed'],'unknown':counts['unknown'],'review_count':len(reviews),'positive_ratio':pos/n if n else None,'wilson_low':lo,'wilson_high':hi,'conflict_score':score,'sufficient':n>=minimum})
    return sorted(results,key=lambda x: x['conflict_score'] if x['conflict_score'] is not None else -1, reverse=True)

def build_index(evidence):
    from sklearn.feature_extraction.text import TfidfVectorizer
    texts=[row['evidence'] for row in evidence]
    if not texts: return None,None
    v=TfidfVectorizer(ngram_range=(1,2),min_df=1,stop_words='english',max_features=50000,sublinear_tf=True)
    try: return v,v.fit_transform(texts)
    except ValueError: return None,None

def retrieve(evidence, vectorizer, matrix, query, product_id=None, aspect=None, scene=None, top_k=5):
    if vectorizer is None or not query.strip(): return []
    scores=(matrix @ vectorizer.transform([query]).T).toarray().ravel()
    candidates=[i for i,r in enumerate(evidence) if (product_id is None or r['product_id']==product_id) and (aspect is None or r['aspect']==aspect) and (scene is None or r['scene']==scene) and scores[i]>0]
    candidates.sort(key=lambda i:(-scores[i],i)); seen=set(); out=[]
    for i in candidates:
        key=evidence[i]['review_id']
        if key in seen: continue
        seen.add(key); out.append({**evidence[i], 'retrieval_score':float(scores[i])})
        if len(out)>=top_k: break
    return out

def read_jsonl(path):
    with Path(path).open(encoding='utf-8-sig') as f:
        for line_no,line in enumerate(f,1):
            if line.strip():
                try: yield line_no,json.loads(line)
                except json.JSONDecodeError as exc: raise ValueError(f'Invalid JSON at line {line_no}: {exc}') from exc
