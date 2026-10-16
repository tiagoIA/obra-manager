import sys,unittest,json
sys.path.insert(0,'scripts')
from collect_product_references import collect_page,safe_url
class Collector(unittest.TestCase):
 def test_exact_and_no_guess(self):
  m={'id':'a','brand':'Siemens','manufacturerPart':'Q120','unit':'ea'};ref={'name':'Home Depot','url':'https://www.homedepot.com/p/test/100','code':'100'}
  def page(**kwargs):
   p={'@type':'Product','sku':'100','mpn':'Q120','brand':{'name':'Siemens'},'offers':{'@type':'Offer','price':'25.00','priceCurrency':'USD'},**kwargs}
   return '<script type="application/ld+json">'+json.dumps(p)+'</script>'
  r=collect_page(m,ref,page());self.assertEqual(r['candidates'][0]['price'],25);self.assertEqual(r['candidates'][0]['unit'],'')
  self.assertFalse(collect_page(m,ref,page(mpn='Q220'))['candidates'])
  self.assertFalse(collect_page(m,ref,'no product data')['candidates'])
  self.assertIsNone(collect_page(m,ref,page(offers={'lowPrice':10,'highPrice':20,'priceCurrency':'USD'}))['candidates'][0]['price'])
 def test_urls(self):
  self.assertFalse(safe_url('http://localhost'));self.assertFalse(safe_url('https://homedepot.com.attacker.com'));self.assertFalse(safe_url('https://user@homedepot.com'));self.assertTrue(safe_url('https://www.homedepot.com/p/100'))
unittest.main()
