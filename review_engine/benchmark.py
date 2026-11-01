"""Time bounded TF-IDF, SVD and sparse KMeans experiments."""
import argparse, json, os, time
from pathlib import Path
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from .core import read_jsonl, normalize

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output',required=True); p.add_argument('--limit',type=int,default=3000); p.add_argument('--features',type=int,default=5000); p.add_argument('--svd',action='store_true'); a=p.parse_args()
    start=time.perf_counter(); texts=[]; seen=set()
    for line,raw in read_jsonl(a.input):
        r=normalize(raw,line)
        if r and r['review_id'] not in seen: seen.add(r['review_id']); texts.append(r['text'])
        if len(texts)>=a.limit: break
    print(f'读取 {len(texts)} 条：{time.perf_counter()-start:.2f}s',flush=True)
    vec=TfidfVectorizer(stop_words='english',min_df=2,max_features=a.features,ngram_range=(1,2),sublinear_tf=True)
    t=time.perf_counter(); x=vec.fit_transform(texts); tfidf=time.perf_counter()-t; print(f'TF-IDF {x.shape}：{tfidf:.2f}s',flush=True)
    svd=None
    if a.svd:
        t=time.perf_counter(); TruncatedSVD(n_components=min(20,x.shape[1]-1),n_iter=2,random_state=42).fit_transform(x); svd=time.perf_counter()-t; print(f'SVD：{svd:.2f}s',flush=True)
    t=time.perf_counter(); model=MiniBatchKMeans(n_clusters=8,random_state=42,n_init=3,batch_size=512,max_iter=50).fit(x); cluster=time.perf_counter()-t; print(f'稀疏 MiniBatchKMeans：{cluster:.2f}s',flush=True)
    data={'reviews':len(texts),'features':x.shape[1],'nonzero':int(x.nnz),'tfidf_seconds':tfidf,'svd_seconds':svd,'minibatch_seconds':cluster,'inertia':float(model.inertia_),'threads':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']}}
    Path(a.output).write_text(json.dumps(data,indent=2),encoding='utf-8')

if __name__=='__main__': main()
