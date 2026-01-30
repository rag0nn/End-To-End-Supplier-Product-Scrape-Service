import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from supplier_scrape_core.structers.product import PreState,Suppliers,Product
from supplier_scrape_core.savers import SaverLikeIkasTemplate
from supplier_scrape_core.config.config import STATIC_VALUES
from interfaces import create_payload
from typing import List, Optional, Tuple
import requests
import logging
import json


class Client:
    
    def __init__(self, base_url):
        self.base_url = base_url
        
        health = self._health_check()
        logging.info(f"Server health {health}")
        
    def _health_check(self):
        """Health check"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:            
                return True
            else:
                return False       
        except requests.exceptions.ConnectionError:
                return False
        except Exception as e:
                return False
            
    def send(self,prestates: List[PreState],supplier:Suppliers, save_path : Optional[str] = None)->Tuple[List[Product],List[Product]]:
        """
        Send prestates to the remote product-fetching endpoint, parse the response and optionally save results to Excel files.
        Parameters
        ----------
        prestates : List[PreState]
            A list of PreState objects to send to the server. Each PreState will be serialized to a dict in the request payload.
        supplier : Suppliers
            Supplier enum value; its .value["prefix"] is used in the payload and its .name is used when saving files.
        save_path : Optional[str]
            If provided, directory path where two Excel files will be written:
            - {save_path}/{supplier.name}_successed.xlsx
            - {save_path}/{supplier.name}_failed.xlsx
            Saving is performed using SaverLikeIkasTemplate().fill(..., STATIC_VALUES, path).
        Returns
        -------
        Tuple[List[Product], List[Product]]
            A tuple (successed_products, failed_products) on success where each element is a list of Product instances
            created via Product.from_Serialize(...) from the server response.
        bool
            Returns False on failure (health check failure, HTTP errors, timeouts, connection errors or other exceptions).
            Note: the implementation currently mixes tuple return and boolean False for error paths.
        Behavior / Side effects
        ----------------------
        - Performs a local health check via self._health_check(); if it returns False, the method logs an error and returns False.
        - Constructs a JSON payload: {"prestates": [dict(p) for p in prestates], "supplier": supplier.value["prefix"]}.
        - Sends a POST to f"{self.base_url}/fetch-products" with a 30s timeout.
        - Expects a JSON response with structure containing "successed" and "failed" blocks, each optionally having "count" and "products".
        - Converts each returned product dict to a Product via Product.from_Serialize and collects separately into successed_products and failed_products.
        - If save_path is provided, attempts to save both lists to Excel files; exceptions during saving are caught and printed (but do not change the method's return on success parsing).
        - Logs status information and errors using the module logger.
        Errors and Logging
        ------------------
        - Catches requests.exceptions.Timeout and requests.exceptions.ConnectionError and logs an appropriate error message, returning False.
        - Catches any other Exception, logs it as a processing error and returns False.
        - Saving-related exceptions are printed to stdout (do not raise).
        """
        health_status = self._health_check()
        if not health_status:
            logging.error("Server Health Status False")
            return False,False
        try:
            payload = create_payload(prestates,supplier)

            logging.info(f"Payload gönderiliyor: {json.dumps(payload, indent=2)}")
            response = requests.post(
                # f"{self.base_url}/fetch-products",
                f"{self.base_url}/fetch-products",
                json = payload,
                timeout = 30
            )
            
            logging.info(f"Response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                
                successed_count = data.get('successed', {}).get('count',0)
                failed_count = data.get('failed', {}).get('count',0)

                logging.info(f"Başarılı: {successed_count} Başarısız: {failed_count}")

                successed_products = []
                failed_products = []
                
                for item in data.get("successed").get("products",[]):
                    product = Product.from_Serialize(item)
                    successed_products.append(product)
                    
                for item in data.get("failed").get("products",[]):
                    product = Product.from_Serialize(item)
                    failed_products.append(product)       
                        
            if save_path is not None:

                try:
                    logging.info(f"[{supplier.name}] Başarılı ürünler kaydediliyor...")
                    # save successed outputs
                    saver = SaverLikeIkasTemplate()
                    output_dst_path = f"{save_path}/{supplier.name}_successed.xlsx"
                    filled_frame = saver.fill(successed_products,STATIC_VALUES)
                    saver.write(filled_frame,output_dst_path)
                    
                    # save failed outputs
                    logging.info(f"[{supplier.name}] Başarısız ürünler kaydediliyor...")
                    saver = SaverLikeIkasTemplate()
                    output_dst_path = f"{save_path}/{supplier.name}_failed.xlsx"
                    filled_frame = saver.fill(failed_products,STATIC_VALUES)
                    saver.write(filled_frame,output_dst_path)
                    
                except Exception as e:
                    print(f"Kaydetme sırasında bir sorun çıktı \n{e}")
            return (successed_products,failed_products)
        except requests.exceptions.Timeout:
            logging.error("İstek zaman aşımına uğradı (timeout)")
            return False,False
        except requests.exceptions.ConnectionError:
            logging.error(f"Sunucuya bağlanılamadı: {self.base_url}")
            return False,False
        except Exception as e:
            logging.error(f"Process hatası: {str(e)}")
            return False,False
        
    def send_via_direct_excel(self,prestates: List[PreState],supplier:Suppliers, save_path : Optional[str] = None)->Tuple[List[Product],List[Product]]:
        """
        Send prestates to the remote product-fetching endpoint, parse the response and optionally save results to Excel files.
        Parameters
        ----------
        prestates : List[PreState]
            A list of PreState objects to send to the server. Each PreState will be serialized to a dict in the request payload.
        supplier : Suppliers
            Supplier enum value; its .value["prefix"] is used in the payload and its .name is used when saving files.
        save_path : Optional[str]
            If provided, directory path where two Excel files will be written:
            - {save_path}/{supplier.name}_successed.xlsx
            - {save_path}/{supplier.name}_failed.xlsx
            Saving is performed using SaverLikeIkasTemplate().fill(..., STATIC_VALUES, path).
        Returns
        -------
        Excel File
        """
        health_status = self._health_check()
        if not health_status:
            logging.error("Server Health Status False")
            return False,False
        try:
            payload = create_payload(prestates,supplier)

            logging.info(f"Payload gönderiliyor: {json.dumps(payload, indent=2)}")
            response = requests.post(
                f"{self.base_url}/fetch-products?excel=true",
                json=payload,
                timeout=30
            )

            logging.info(f"Response status: {response.status_code}")

            if response.status_code != 200:
                logging.error(f"HTTP Error: {response.status_code}")
                return False, False

            if not save_path:
                logging.error("Excel response geldi ama save_path verilmedi")
                return False, False

            output_path = f"{save_path}/{supplier.name}_products_mixed.xlsx"
            with open(output_path, "wb") as f:
                f.write(response.content)

            logging.info(f"Excel kaydedildi: {output_path}")

            # Excel döndüyse Product listesi dönemezsin
            return [], []

        except Exception as e:
            logging.error(f"Send via direkt excel method fail {e}")
            return False,False

                    

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
    
    # json response
    # for k,v in test_prestates.items():
    #     success, failed = client.send(v,k,save_path)
    #     if success:
    #         print(f"SUCCESS {len(success)} / FAILED {len(failed)}")
    #         print(success[0])
    #     else:
    #         print(f"--> {success}")
    
    # # excel response
    for k,v in test_prestates.items():
        success, failed = client.send_via_direct_excel(v,k,save_path)
        if success:
            print(f"SUCCESS {len(success)} / FAILED {len(failed)}")
            print(success[0])
        else:
            print(f"--> {success}")
if __name__ == "__main__":
    test_client()