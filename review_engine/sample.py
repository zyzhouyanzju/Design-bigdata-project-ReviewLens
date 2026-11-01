"""Create a reproducible stratified annotation sample without generating labels."""
import argparse
import pandas as pd

def main():
    p=argparse.ArgumentParser(); p.add_argument('--evidence',required=True); p.add_argument('--output',required=True); p.add_argument('--per-group',type=int,default=10); p.add_argument('--seed',type=int,default=42); a=p.parse_args()
    df=pd.read_csv(a.evidence).drop_duplicates(['product_id','review_id','aspect','sentiment'])
    sample=df.groupby(['product_id','sentiment'],group_keys=False).sample(n=a.per_group,random_state=a.seed,replace=False) if df.groupby(['product_id','sentiment']).size().min()>=a.per_group else df.groupby(['product_id','sentiment'],group_keys=False).apply(lambda x:x.sample(n=min(len(x),a.per_group),random_state=a.seed),include_groups=True)
    sample['gold_sentiment']=''; sample['gold_aspect_correct']=''; sample['gold_scene_correct']=''; sample['annotator_note']=''
    sample.to_csv(a.output,index=False,encoding='utf-8-sig'); print(f'Exported {len(sample)} rows for manual annotation.')

if __name__=='__main__': main()
