"""Run: python -m review_engine.run --input reviews.jsonl --config config/earbuds.json --output outputs/engine."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from .core import normalize, extract, aggregate, read_jsonl

def write_csv(path, rows, columns):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=columns); writer.writeheader(); writer.writerows(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True); p.add_argument('--config',required=True); p.add_argument('--output',required=True); p.add_argument('--min-evidence',type=int,default=20)
    a=p.parse_args(); source=Path(a.input); cfg_path=Path(a.config); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads(cfg_path.read_text(encoding='utf-8')); counts=Counter(); seen=set(); evidence=[]; products={}
    for number, raw in read_jsonl(source):
        counts['input']+=1; review=normalize(raw,number)
        if review is None: counts['missing_product_or_text']+=1; continue
        if review['review_id'] in seen: counts['duplicates']+=1; continue
        seen.add(review['review_id']); counts['reviews']+=1; products[review['product_id']]=review['product_name']; evidence.extend(extract(review,cfg))
    summaries=aggregate(evidence,a.min_evidence)
    ecols=['review_id','product_id','aspect','scene','sentiment','issue_type','evidence','start','end','rating','timestamp']
    scols=['product_id','aspect','scene','positive','negative','mixed','unknown','review_count','positive_ratio','wilson_low','wilson_high','conflict_score','sufficient']
    write_csv(out/'evidence.csv',evidence,ecols); write_csv(out/'summary.csv',summaries,scols)
    (out/'products.json').write_text(json.dumps(products,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest={'input':str(source),'input_sha256':hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),'config_sha256':hashlib.sha256(cfg_path.read_bytes()).hexdigest(),'category':cfg.get('category'),'counts':dict(counts),'products':len(products),'evidence_rows':len(evidence),'summary_groups':len(summaries),'min_evidence':a.min_evidence}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
