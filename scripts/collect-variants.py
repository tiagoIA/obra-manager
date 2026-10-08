"""Bounded supplier variant review; read-only public catalog access."""
import pathlib
src=pathlib.Path('scripts/collect-catalog.py').read_text()
src=src.replace('QUERIES=[','ORIGINAL_QUERIES=[',1)
queries=[(p,'breakers',['panel','circuit']) for p in ['Q115','Q120','Q230','Q240','Q250','Q260','QA115AFC','QA120AFC','QF120A','QF220A','BR115','BR120','BR230','BR240','BR250','BR260','QO115','QO120','QO230','QO240','HOM115','HOM120','HOM230','HOM240']]
queries += [(p,'accessories',['devices','circuit']) for p in ['machine screw','sheet metal screw','self drilling screw','concrete screw','hex nut','washer','threaded rod']]
src=src.replace('http=requests.Session()', 'QUERIES='+repr(queries)+'\nhttp=requests.Session()')
src=src[:src.index('# A bounded manufacturer supplement')]+src[src.index('# Validate that every photo'):]
src=src.replace('if added>=6:break','if added>=3:break')
exec(compile(src,'variant-collector','exec'))
