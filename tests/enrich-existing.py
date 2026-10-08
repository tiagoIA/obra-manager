"""Exercise identity, conflict and preservation guards without credentials/network."""
import ast,pathlib,copy
source=ast.parse(pathlib.Path('scripts/enrich-existing.py').read_text())
nodes=[x for x in source.body if isinstance(x,ast.FunctionDef) and x.name in {'fill','enc','dec'} or isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ALLOWED' for t in x.targets)]
ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'enrichment-guards','exec'),ns)
old={'name':'Exact model','sku':'MAT-007','qty':18,'photoUrl':'existing-photo','suppliers':[{'name':'Store','code':'123','price':9,'customField':'keep'}],'privateNote':'keep'}
p={'expectedName':'Exact model','expectedSku':'MAT-007','fields':{'manufacturerPart':'EXACT-1'},'supplier':{'name':'Store','code':'123','url':'https://example.com/item','unit':'un'}}
before=copy.deepcopy(old);patch=ns['fill'](old,p)
assert old==before and patch['suppliers'][0]['customField']=='keep' and patch['suppliers'][0]['price']==9
assert not {'qty','sku','photoUrl','privateNote'}.intersection(patch)
for changed in [{'sku':'different'},{'name':'Different model'},{'isTask':True},{'manufacturerPart':'CONFLICT'}]:
 try:ns['fill']({**old,**changed},p)
 except AssertionError:pass
 else:raise AssertionError('Unsafe identity accepted')
try:ns['fill'](old,{**p,'fields':{'qty':0}})
except AssertionError:pass
else:raise AssertionError('Stock update accepted')
known={'name':'n','sku':'s','brand':'B','specs':'User details','sourceUrl':'https://user.example'}
assert ns['fill'](known,{'expectedName':'n','expectedSku':'s','fields':{'brand':'B','specs':'New details','sourceUrl':'https://different.example'}})=={}
value={'suppliers':[{'name':'S','code':'123','unit':'ft'}],'qty':0,'flag':False,'note':None}
assert ns['dec'](ns['enc'](value))==value
print('PASS enrichment guards: exact identity, conflict rejection, stock/photo preservation, supplier metadata, codec')
