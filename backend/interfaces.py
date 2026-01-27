from supplier_scrape_core.structers.product import PreState, Suppliers, Product
from typing import List, Dict

def create_payload(prestates:List[PreState], supplier:Suppliers):
    return {"prestates" : list(dict(p) for p in prestates),
            "supplier" : supplier.value["prefix"]
            }
    
def create_response(successed:List[Product], failed:List[Product])->Dict:
    # ürünleri serialize et
    serialized_successed = [product.serialize() for product in successed]
    serialized_failed = [product.serialize() for product in failed]
    
    # response
    return {
        "successed" : {
            "count" : len(serialized_successed),
            "products" : serialized_successed
        },
        "failed" : {
            "count" : len(serialized_failed),
            "products" : serialized_failed
        }
    }