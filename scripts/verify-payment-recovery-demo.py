#!/usr/bin/env python3
"""Check the script-free demo projection; not a payment evaluator or browser QA."""
from html.parser import HTMLParser
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PIN = 'f842d54679ac0826e2bc635dcd10a321f6d03631'
# Exact selected records from the pinned ContractGraph-QA evidence.
EXPECTED = [
 ('fail_retry_before_reconcile.json','a6705e08d010d8f0e8db4f4c33500c02ec11e499a4afc6c4166094a56a11d876','FAIL',['authorize','submit','ambiguous','retry'],['false','false']),
 ('pass_committed_stop.json','5ccc2766e2175f8ad45517ffcb5d61e12a946cec8f291a5fafa5bf42cf6f7339','PASS',['authorize','submit','ambiguous','reconcile','stop'],['true','true']),
 ('pass_failed_retry_same_identity.json','4883e24b8911fa7c016e8a70e6ece77b5a15570825b0403d31fddeca9f39e76a','PASS',['authorize','submit','ambiguous','reconcile','retry','stop'],['true','true']),
 ('fail_changed_idempotency_after_failed_reconcile.json','0a8894d1fee3a446eb6d632746977705867b4450540bfeae4f58a2bbc1b826b5','FAIL',['authorize','submit','ambiguous','reconcile','retry'],['true','true']),
 ('unknown_stop','983f119047030accf41ee8380ebc645830eb2289630e6e8e0130f49b2670e701','FAIL',['authorize','submit','ambiguous','reconcile','stop'],['true','false']),
 ('submit_after_commit','682024562fbc9eb56a01fd9070aa04cffe1ce67957eeffac7510bd4ad313920a','PASS',['authorize','submit','ambiguous','reconcile','submit'],['true','true']),
]
class Demo(HTMLParser):
 def __init__(self):
  super().__init__(); self.stack=[]; self.cases=[]; self.current=None; self.scripts=0; self.links=[]; self.h1=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='script': self.scripts+=1
  if tag=='h1': self.h1+=1
  if tag=='a': self.links.append(a.get('href',''))
  if tag=='details' and 'data-case' in a:
   self.current={'name':a['data-case'],'hash':a['data-scenario-sha256'],'verdict':[],'events':[],'flags':[]}
  if tag not in {'meta','link','input','br','hr','img'}: self.stack.append((tag,a.get('class','').split()))
 def handle_endtag(self,tag):
  if tag=='details' and self.current is not None:
   self.cases.append(self.current); self.current=None
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i][0]==tag:
    del self.stack[i:];break
 def handle_data(self,data):
  text=data.strip()
  if not self.current or not text:return
  classes={c for _,cs in self.stack for c in cs}
  if 'verdict' in classes:self.current['verdict'].append(text)
  if 'event-name' in classes:self.current['events'].append(text)
  if 'checks' in classes and self.stack[-1][0]=='b':self.current['flags'].append(text)

path=ROOT/'site/payment-recovery-demo.html'
text=path.read_text(encoding='utf-8'); demo=Demo();demo.feed(text)
assert demo.scripts==0, 'Demo controls must not depend on JavaScript'
assert demo.h1==1
assert len(demo.cases)==6
for actual,(name,sha,verdict,events,flags) in zip(demo.cases,EXPECTED):
 assert actual==dict(name=name,hash=sha,verdict=[verdict],events=events,flags=flags),actual
assert 'KNOWN GAP · NOT A SAFE OUTCOME' in text
assert 'NONCRITICAL · OUTCOME UNRESOLVED' in text
assert 'unapplied candidate, not a shipped fix' in text
assert f'blob/{PIN}/proofs/payment-recovery-demo/evidence.json' in text
for name in ('payment-recovery-demo.css','payment-recovery-native.css'):
 assert (ROOT/'site'/name).is_file(),name
assert '@media(prefers-reduced-motion:reduce)' in (ROOT/'site/payment-recovery-native.css').read_text()
print(json.dumps({'result':'PASS','projected_cases':6,'script_count':demo.scripts,'evidence_commit':PIN,'scope':'static HTML projection, not browser or provider verification'}))
