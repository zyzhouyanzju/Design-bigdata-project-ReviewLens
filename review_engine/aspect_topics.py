"""Cluster evidence snippets within each configured aspect using sparse TF-IDF."""
import argparse
import json
import re
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

GENERAL = {'good','great','excellent','amazing','love','nice','best','perfect','product','item','buy','bought','purchase','purchased','work','works','really','just','like','use','using','used','earbuds','earbud','headphones','earphones','earphone'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--evidence',required=True); p.add_argument('--config',required=True); p.add_argument('--output',required=True); p.add_argument('--clusters',type=int,default=5); p.add_argument('--seed',type=int,default=42); p.add_argument('--min-rows',type=int,default=50); a=p.parse_args()
    if a.clusters < 2 or a.min_rows < a.clusters: p.error('clusters must be >= 2 and min-rows >= clusters')
    start=time.perf_counter(); cfg=json.loads(Path(a.config).read_text(encoding='utf-8')); data=pd.read_csv(a.evidence,keep_default_na=False)
    required={'review_id','product_id','aspect','evidence'}
    if not required.issubset(data.columns): raise ValueError('evidence.csv is missing required columns')
    data=data.drop_duplicates(['review_id','product_id','aspect','evidence']).reset_index(drop=True)
    topics=[]; assignments=[]; skipped=[]
    for aspect, group in data.groupby('aspect',sort=True):
        group=group.reset_index(drop=True)
        if len(group)<a.min_rows: skipped.append({'aspect':aspect,'reason':'insufficient snippets','count':len(group)}); continue
        # Remove aspect anchor terms, so clusters describe details instead of merely repeating the aspect name.
        anchor={token for phrase in cfg.get('aspects',{}).get(aspect,[]) for token in re.findall(r'[a-z]+',phrase.lower())}
        stop=sorted(set(ENGLISH_STOP_WORDS)|GENERAL|anchor)
        vectorizer=TfidfVectorizer(stop_words=stop,min_df=2,max_df=.95,max_features=12000,ngram_range=(1,2),sublinear_tf=True)
        try: matrix=vectorizer.fit_transform(group.evidence.astype(str))
        except ValueError: skipped.append({'aspect':aspect,'reason':'insufficient vocabulary','count':len(group)}); continue
        active=np.flatnonzero(np.asarray(matrix.getnnz(axis=1)).ravel()>0)
        if len(active)<a.min_rows: skipped.append({'aspect':aspect,'reason':'insufficient nonempty vectors','count':len(active)}); continue
        vectors=matrix[active]; model=MiniBatchKMeans(n_clusters=a.clusters,n_init=10,batch_size=512,max_iter=200,random_state=a.seed).fit(vectors)
        names=np.asarray(vectorizer.get_feature_names_out())
        for cid in range(a.clusters):
            members=np.flatnonzero(model.labels_==cid)
            if not len(members): continue
            original=active[members]; mean=np.asarray(matrix[original].mean(axis=0)).ravel(); positive=np.flatnonzero(mean>0); indices=positive[np.argsort(mean[positive])[-10:][::-1]]
            similarities=np.asarray(vectors[members] @ model.cluster_centers_[cid]).ravel(); closest=original[np.argsort(similarities)[-3:][::-1]]
            examples=group.iloc[closest]
            topics.append({'aspect':aspect,'cluster':cid,'snippets':len(members),'unique_reviews':group.iloc[original].review_id.nunique(),'top_terms':', '.join(names[indices]),'representative_ids':' | '.join(examples.review_id.astype(str)),'representative_texts':' | '.join(examples.evidence.astype(str))})
        for row_index,cid in zip(active,model.labels_):
            row=group.iloc[row_index]; assignments.append({'review_id':row.review_id,'product_id':row.product_id,'aspect':aspect,'cluster':int(cid),'evidence':row.evidence})
        print(f'{aspect}: {len(group)} 条片段，{len(active)} 个有效向量，耗时 {time.perf_counter()-start:.1f}s',flush=True)
    out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(topics,columns=['aspect','cluster','snippets','unique_reviews','top_terms','representative_ids','representative_texts']).to_csv(out/'topics.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(assignments,columns=['review_id','product_id','aspect','cluster','evidence']).to_csv(out/'assignments.csv',index=False,encoding='utf-8-sig')
    meta={'method':'aspect-specific sparse TF-IDF + MiniBatchKMeans','input_snippets':len(data),'assigned_snippets':len(assignments),'topics':len(topics),'seed':a.seed,'clusters_per_aspect':a.clusters,'skipped':skipped,'elapsed_seconds':time.perf_counter()-start}
    (out/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(meta,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__': main()
