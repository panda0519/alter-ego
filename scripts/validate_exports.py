"""Validate a completed export batch; does not verify model correctness."""
from pathlib import Path
import json, math, sys
from datetime import date
from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
METHODS = ['idw', 'gcn_lstm', 'gcn_lstm_physics']
def reject_constant(s):
    raise ValueError('JSON non-finite constant: ' + s)
def load(path):
    return json.loads(path.read_text(encoding='utf-8'), parse_constant=reject_constant)
def finite(x):
    if isinstance(x, float) and not math.isfinite(x): raise ValueError('non-finite number')
    if isinstance(x, dict):
        for v in x.values(): finite(v)
    if isinstance(x, list):
        for v in x: finite(v)
def ensure(ok, message):
    if not ok: raise ValueError(message)
def close(a,b):
    return (a is None and b is None) or (a is not None and b is not None and abs(a-b)<0.002)
def main():
    folder = Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'contracts'/'fixtures'
    batch={}
    for name in ['predictions','metrics','run_info','agent_context']:
        value=load(folder/f'{name}.json'); finite(value)
        schema=load(ROOT/'contracts'/f'{name}.schema.json')
        Draft7Validator.check_schema(schema)
        Draft7Validator(schema,format_checker=FormatChecker()).validate(value)
        batch[name]=value
    meta=batch['predictions']['meta']
    for name,value in batch.items(): ensure(value['meta']==meta, 'metadata mismatch: '+name)
    pred=batch['predictions']; dates=pred['dates']; parsed=[date.fromisoformat(d) for d in dates]
    ensure(parsed==sorted(set(parsed)), 'dates must be unique and sorted')
    ensure(dates[-1]==meta['as_of_date'], 'as_of_date must equal final export date')
    ids=[w['id'] for w in pred['wells']]; ensure(len(ids)==len(set(ids)), 'duplicate well ID')
    lookup={w['id']:w for w in pred['wells']}
    for w in pred['wells']:
        ensure(len(w['observations_m'])==len(dates), 'observation length: '+w['id'])
        for m in METHODS:
            seq=w['predictions_m'][m]; s=w['summaries'][m]
            ensure(len(seq)==len(dates), 'prediction length: '+w['id']+'/'+m)
            ensure(close(seq[-1],s['latest_depth_m']), 'latest-depth mismatch')
            earlier=(parsed[-1].toordinal()-30)
            pos=next((i for i,d in enumerate(parsed) if d.toordinal()==earlier),None)
            delta=None if pos is None or seq[-1] is None or seq[pos] is None else seq[-1]-seq[pos]
            ensure(close(delta,s['change_30d_m']), '30-day-change mismatch')
            p='unknown' if delta is None else 'high' if delta>.5 else 'watch' if delta>.2 else 'normal'
            ensure(p==s['priority'], 'priority mismatch')
    agent=batch['agent_context']; ensure(len(agent['wells'])==len(ids),'agent well count')
    ensure({w['id'] for w in agent['wells']}==set(ids),'agent well IDs')
    for a in agent['wells']:
        ensure(a['method']==meta['default_method'],'agent method')
        w=lookup[a['id']]; s=w['summaries'][a['method']]
        ensure(a['role']==w['role'],'agent role')
        for k in s: ensure(a[k]==s[k],'agent summary mismatch: '+k)
    for m,metric in batch['metrics']['methods'].items():
        if metric['status']=='completed':
            ensure(metric['test_pairs']>0 and metric['test_wells']>0,'completed metric needs counts')
            ensure(metric['validation_pairs']>0,'completed metric needs validation count')
            for key in ['validation_mae_m','test_mae_m','test_rmse_m']:
                ensure(metric[key] is not None and metric[key]>=0,'invalid metric '+key)
        else:
            for key in ['validation_mae_m','test_mae_m','test_rmse_m']:
                ensure(metric[key] is None,'noncompleted metric must be null')
    completed=[v for v in batch['metrics']['methods'].values() if v['status']=='completed']
    if len(completed)>1:
        ensure(len({v['test_pairs'] for v in completed})==1,'common test-mask count mismatch')
    if meta['artifact_kind']=='fixture':
        ensure(meta['dataset_kind']=='synthetic','fixture must be synthetic')
        ensure(not completed,'fixture cannot claim completed evaluation')
    print('PASS: schemas, metadata, dates, series, summaries and metric status consistent.')
    print('This does not certify training, leakage prevention, physics or accuracy.')
if __name__=='__main__': main()
