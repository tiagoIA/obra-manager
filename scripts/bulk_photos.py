"""Legacy entry point now stages exact product images/prices for owner review."""
import sys
from collect_product_references import main
if __name__=='__main__':
 if len(sys.argv)==1:sys.argv.append('--firestore')
 main()
