"""Validate the real migration decision without credentials or network."""
import ast,pathlib,re,copy
source=ast.parse(pathlib.Path('scripts/apply-lifecycle.py').read_text());functions=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in {'candidate_kind','lifecycle_patch','enc'}];ns={'re':re};exec(compile(ast.Module(body=functions,type_ignores=[]),'migration-guards','exec'),ns)
old={'name':'Single Pole Breaker 20A','sku':'ELEC-132','qty':0,'stockNote':'Unknown panel','recordType':None,'photoUrl':'old-photo'}
plan={'expected':{'name':old['name'],'sku':old['sku'],'recordType':None},'fields':{'recordType':'family'},'generic':True};products={'new':{'family':'breakers','recordType':'product','brand':'Siemens','manufacturerPart':'Q120','active':True}}
before=copy.deepcopy(old);patch=ns['lifecycle_patch'](old,plan,products);assert patch['active'] is False and old==before
assert not {'qty','sku','photoUrl','materialId','matId'}.intersection(patch)
patch=ns['lifecycle_patch']({**old,'qty':8},plan,products);assert 'active' not in patch and 'Stock remains' in patch['catalogReviewReason']
assert 'active' not in ns['lifecycle_patch'](old,plan,{})
try:ns['lifecycle_patch']({**old,'name':'Changed by owner'},plan,products)
except AssertionError:pass
else:raise AssertionError('Stale reviewed identity accepted')
print('PASS migration: archive without deletion; stock identification guard; no automatic relink; stale identity rejection')
