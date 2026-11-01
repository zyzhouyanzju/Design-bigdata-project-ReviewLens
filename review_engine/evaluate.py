"""Evaluate human-labelled evidence; unknown/blank gold labels are excluded."""
import argparse
import json
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--labels',required=True); parser.add_argument('--output',required=True)
    args=parser.parse_args(); df=pd.read_csv(args.labels,keep_default_na=False)
    needed={'sentiment','gold_sentiment'}
    if not needed.issubset(df.columns): raise ValueError(f'Missing columns: {needed-set(df.columns)}')
    df=df[df.gold_sentiment.isin(['positive','negative','unknown'])]
    if df.empty: raise ValueError('No labelled rows; complete gold_sentiment first.')
    labels=['positive','negative','unknown']
    report={'labelled_rows':len(df),'labels':labels,'classification_report':classification_report(df.gold_sentiment,df.sentiment,labels=labels,output_dict=True,zero_division=0),'confusion_matrix':confusion_matrix(df.gold_sentiment,df.sentiment,labels=labels).tolist()}
    with open(args.output,'w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
