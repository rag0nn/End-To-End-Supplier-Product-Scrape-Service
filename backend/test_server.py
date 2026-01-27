import requests
import json
import time
import os
from typing import Dict, List
from supplier_scrape_core.structers.product import PreState,Suppliers,Product
from supplier_scrape_core.processer import SaverLikeIkasTemplate
from supplier_scrape_core.config.config import STATIC_VALUES

TEST_PRESTATES = {
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

LOCAL_SERVER_URL = "http://localhost:5000"
REMOTE_SERVER_URL = "http://your-remote-server.com"  # Uzak sunucu URL'sini buraya yazın

class ServerTester:
    """Server test class"""
    
    def __init__(self, base_url: str, server_name: str = "Server"):
        self.base_url = base_url
        self.server_name = server_name
        self.results = []
        
    def _print_header(self, text: str):
        """Test başlığı yazdır"""
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
    
    def _print_success(self, text: str):
        """Başarı mesajı yazdır"""
        print(f"✓ {text}")
    
    def _print_error(self, text: str):
        """Hata mesajı yazdır"""
        print(f"✗ {text}")
    
    def _print_info(self, text: str):
        """Bilgi mesajı yazdır"""
        print(f"ℹ {text}")
        
    def health_check(self) -> bool:
        """Health check"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self._print_success(f"Health check başarılı: {data.get('message')}")
                self.results.append(("Health Check", True, response.status_code))
                return True
            else:
                self._print_error(f"Health check başarısız: {response.status_code}")
                self.results.append(("Health Check", False, response.status_code))
                return False       
        except requests.exceptions.ConnectionError:
            self._print_error(f"Sunucuya bağlanılamadı: {self.base_url}")
            self.results.append(("Health Check", False, "Connection Error"))
            return False
        except Exception as e:
            self._print_error(f"Health check hatası: {str(e)}")
            self.results.append(("Health Check", False, str(e)))
            return False
        
    def fetch_product_check(self,prestates: List[PreState], supplier:Suppliers)->List[Product]:
        try:
            payload = {"prestates" : list(dict(p) for p in prestates),
                "supplier" : supplier.value["prefix"]
                }
            
            self._print_info(f"Payload gönderiliyor: {json.dumps(payload, indent=2)}")
            response = requests.post(
                f"{self.base_url}/fetch-products",
                json = payload,
                timeout = 30
            )
            
            self._print_info(f"Response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                
                successed_count = data.get('successed', {}).get('count',0)
                failed_count = data.get('failed', {}).get('count',0)

                self._print_info(f"Başarılı: {successed_count} Başarısız: {failed_count}")

                self.results.append(("Fetch products", True, response.status_code))
         
                products = []
                for title in ["successed","failed"]:
                    for item in data.get(title).get("products",[]):
                        product = Product.from_Serialize(item)
                        products.append(product)
            return products
        except requests.exceptions.Timeout:
            self._print_error("İstek zaman aşımına uğradı (timeout)")
            self.results.append(("Process Products", False, "Timeout"))
            return False
        except requests.exceptions.ConnectionError:
            self._print_error(f"Sunucuya bağlanılamadı: {self.base_url}")
            self.results.append(("Process Products", False, "Connection Error"))
            return False
        except Exception as e:
            self._print_error(f"Process hatası: {str(e)}")
            self.results.append(("Process Products", False, str(e)))
            return False

    def test_invalid_request(self) -> bool:
        """Geçersiz istek test et"""
        try:
            payload = {
                "prestates": "invalid"  # Geçersiz format
            }
            
            response = requests.post(
                f"{self.base_url}/process-products",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 400:
                error_msg = response.json().get('error', '')
                self._print_success(f"Geçersiz istek doğru şekilde reddedildi: {error_msg}")
                self.results.append(("Invalid Request", True, response.status_code))
                return True
            else:
                self._print_error(f"Geçersiz istek doğru şekilde işlenmedi: {response.status_code}")
                self.results.append(("Invalid Request", False, response.status_code))
                return False
            
        except Exception as e:
            self._print_error(f"Geçersiz istek test hatası: {str(e)}")
            self.results.append(("Invalid Request", False, str(e)))
            return False

    def test_empty_request(self) -> bool:
        """Boş istek test et"""
        try:
            payload = {
                "prestates": []
            }
            
            response = requests.post(
                f"{self.base_url}/process-products",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 400:
                self._print_success(f"Boş istek doğru şekilde reddedildi")
                self.results.append(("Empty Request", True, response.status_code))
                return True
            else:
                self._print_error(f"Boş istek doğru şekilde işlenmedi: {response.status_code}")
                self.results.append(("Empty Request", False, response.status_code))
                return False
                
        except Exception as e:
            self._print_error(f"Boş istek test hatası: {str(e)}")
            self.results.append(("Empty Request", False, str(e)))
            return False
        
    def print_summary(self):
        """Test sonuçlarının özetini yazdır"""
        self._print_header(f"{self.server_name} - Test Özeti")
        
        total = len(self.results)
        passed = sum(1 for _, success, _ in self.results if success is True)
        failed = total - passed
        
        print(f"Toplam Test: {total}")
        print(f"Başarılı: {passed}")
        print(f"Başarısız: {failed}")
        print(f"Başarı Oranı: {(passed/total)*100:.1f}%\n")
        
        for test_name, success, status in self.results:
            status_icon = "✓" if success is True else "✗"
            print(f"{status_icon} {test_name}: {status}")
    
def main(local:bool):
    print("\n" + "="*60)
    print("  Flask API Server Test Suite")
    print("="*60)
    
    if local:
        print("Lokal Sunucu Testi")
        tester = ServerTester(LOCAL_SERVER_URL, "Lokal Server Tester")
    else:
        print("Uzak Sunucu Testi")
        tester = ServerTester(REMOTE_SERVER_URL,"Uzak Sunucu Tester")
    
    # sağlık testi
    result = tester.health_check()
    if not result:
        print("Sunucu sağlığı: False")
        return 
    
    time.sleep(1)
    
    result_products = {}
    
    # ürün testi
    for k,v in TEST_PRESTATES.items():
        saver =  SaverLikeIkasTemplate()
        
        print("Test ediliyor: ", k.name)
        products : List[Product] = tester.fetch_product_check(v,k)
        result_products.update({k.name : products})
        
        try:
            # save outputs
            output_dst_path = f"{os.path.dirname(__file__)}/test_output/{k.name}.xlsx"
            saver.fill(products,STATIC_VALUES,output_dst_path)
        except Exception as e:
            print(f"Kaydetme sırasında bir sorun çıktı \n{e}")
            raise e
        
        
    print("Alınan veri: ", result_products)
    time.sleep(1)
    
    # Geçersiz request testi
    tester.test_invalid_request()
    
    time.sleep(1)
    
    # Boş testi
    tester.test_empty_request()
    
    tester.print_summary()
    return True

if __name__ == '__main__':
    print(STATIC_VALUES)
    local_test = True
    result = main(local_test)
    if result:
        print("Test Başarıyla sonuçlandırıldı")
    else:
        print("Test problem ile sonuçalndırıldı")