import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from supplier_scrape_core.structers.product import PreState,Suppliers
import logging
from client import Client
def test_client():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    server_url = "http://localhost:5000"
    test_prestates = {
        Suppliers.BALGUNES : [
            PreState(175441,350,1),
            PreState(177031,420,1),
            PreState(177073,220,6)
        ],
        Suppliers.BABEXI : [
            PreState(444493,30,12),
            PreState(436739,30,12),
            PreState(431525,12,3)
        ],
        Suppliers.MALKOC : [
            PreState(543120,30,12),
            PreState(534516,30,12),
            PreState(130777,12,3)
        ]
    }
    
    client = Client(server_url)
    
    save_path = f"{os.path.dirname(__file__)}/test_output"
    for f in os.listdir(save_path):
        os.remove(save_path + "/" + f)
    logging.info("Cleared test_output folder")    
         
    # json response
    for k,v in test_prestates.items():
        success, failed = client.send(v,k,save_path)
        if success:
            print(f"SUCCESS {len(success)} / FAILED {len(failed)}")
            print(success[0])
        else:
            print(f"--> {success}")
    
    # # excel response
    # for k,v in test_prestates.items():
    #     success, failed = client.send_via_direct_excel(v,k,save_path)
    #     if success:
    #         print(f"SUCCESS {len(success)} / FAILED {len(failed)}")
    #         print(success[0])
    #     else:
    #         print(f"--> {success}")
if __name__ == "__main__":
    test_client()