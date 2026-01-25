import requests
import json
import time
from typing import Dict, List

# Test verileri
TEST_PRESTATES = [
    {"code": 145204, "price": 30, "stock": 12},
    {"code": 147149, "price": 50, "stock": 10},
]

LOCAL_SERVER_URL = "http://localhost:5000"
REMOTE_SERVER_URL = "http://your-remote-server.com"  # Uzak sunucu URL'sini buraya yazın

class ServerTester:
    """Server test sınıfı"""
    
    def __init__(self, base_url: str, server_name: str = "Server"):
        self.base_url = base_url
        self.server_name = server_name
        self.results = []
    
    def print_header(self, text: str):
        """Test başlığı yazdır"""
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
    
    def print_success(self, text: str):
        """Başarı mesajı yazdır"""
        print(f"✓ {text}")
    
    def print_error(self, text: str):
        """Hata mesajı yazdır"""
        print(f"✗ {text}")
    
    def print_info(self, text: str):
        """Bilgi mesajı yazdır"""
        print(f"ℹ {text}")
    
    def test_health_check(self) -> bool:
        """Health check endpoint'ini test et"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Health check başarılı: {data.get('message')}")
                self.results.append(("Health Check", True, response.status_code))
                return True
            else:
                self.print_error(f"Health check başarısız: {response.status_code}")
                self.results.append(("Health Check", False, response.status_code))
                return False
                
        except requests.exceptions.ConnectionError:
            self.print_error(f"Sunucuya bağlanılamadı: {self.base_url}")
            self.results.append(("Health Check", False, "Connection Error"))
            return False
        except Exception as e:
            self.print_error(f"Health check hatası: {str(e)}")
            self.results.append(("Health Check", False, str(e)))
            return False
    
    def test_process_products(self, prestates: List[Dict] = None) -> bool:
        """Process products endpoint'ini test et"""
        if prestates is None:
            prestates = TEST_PRESTATES
        
        try:
            payload = {
                "prestates": prestates,
                "supplier": "BALGUNES"
            }
            
            self.print_info(f"Payload gönderiliyor: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f"{self.base_url}/api/process-products",
                json=payload,
                timeout=30
            )
            
            self.print_info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("Process Products Response: ",data)
                success_count = data.get('success', {}).get('count', 0)
                failed_count = data.get('failed', {}).get('count', 0)
                
                self.print_success(f"Process başarılı!")
                self.print_info(f"  Başarılı ürünler: {success_count}")
                self.print_info(f"  Başarısız ürünler: {failed_count}")
                
                # İlk 2 ürünü göster
                success_products = data.get('success', {}).get('products', [])
                if success_products:
                    self.print_info("Başarılı ürünlerin ilk 2'si:")
                    for product in success_products[:2]:
                        print(f"    - {product}")
                
                self.results.append(("Process Products", True, response.status_code))
                return True
            else:
                error_msg = response.json().get('error', 'Bilinmeyen hata')
                self.print_error(f"Process başarısız: {error_msg}")
                self.results.append(("Process Products", False, response.status_code))
                return False
                
        except requests.exceptions.Timeout:
            self.print_error("İstek zaman aşımına uğradı (timeout)")
            self.results.append(("Process Products", False, "Timeout"))
            return False
        except requests.exceptions.ConnectionError:
            self.print_error(f"Sunucuya bağlanılamadı: {self.base_url}")
            self.results.append(("Process Products", False, "Connection Error"))
            return False
        except Exception as e:
            self.print_error(f"Process hatası: {str(e)}")
            self.results.append(("Process Products", False, str(e)))
            return False
    
    def test_invalid_request(self) -> bool:
        """Geçersiz istek test et"""
        try:
            payload = {
                "prestates": "invalid"  # Geçersiz format
            }
            
            response = requests.post(
                f"{self.base_url}/api/process-products",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 400:
                error_msg = response.json().get('error', '')
                self.print_success(f"Geçersiz istek doğru şekilde reddedildi: {error_msg}")
                self.results.append(("Invalid Request", True, response.status_code))
                return True
            else:
                self.print_error(f"Geçersiz istek doğru şekilde işlenmedi: {response.status_code}")
                self.results.append(("Invalid Request", False, response.status_code))
                return False
                
        except Exception as e:
            self.print_error(f"Geçersiz istek test hatası: {str(e)}")
            self.results.append(("Invalid Request", False, str(e)))
            return False
    
    def test_empty_request(self) -> bool:
        """Boş istek test et"""
        try:
            payload = {
                "prestates": []
            }
            
            response = requests.post(
                f"{self.base_url}/api/process-products",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 400:
                self.print_success(f"Boş istek doğru şekilde reddedildi")
                self.results.append(("Empty Request", True, response.status_code))
                return True
            else:
                self.print_error(f"Boş istek doğru şekilde işlenmedi: {response.status_code}")
                self.results.append(("Empty Request", False, response.status_code))
                return False
                
        except Exception as e:
            self.print_error(f"Boş istek test hatası: {str(e)}")
            self.results.append(("Empty Request", False, str(e)))
            return False
    
    def print_summary(self):
        """Test sonuçlarının özetini yazdır"""
        self.print_header(f"{self.server_name} - Test Özeti")
        
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
    
    def run_all_tests(self):
        """Tüm testleri çalıştır"""
        self.print_header(f"{self.server_name} Testleri Başlıyor")
        
        # Health check
        if not self.test_health_check():
            self.print_error("Sunucu yanıt vermiyor. Diğer testler atlanıyor.")
            self.print_summary()
            return False
        
        time.sleep(1)
        
        # Process products
        self.test_process_products()
        
        time.sleep(1)
        
        # Invalid request
        self.test_invalid_request()
        
        time.sleep(1)
        
        # Empty request
        self.test_empty_request()
        
        self.print_summary()
        return True


def main():
    """Ana test fonksiyonu"""
    
    print("\n" + "="*60)
    print("  Flask API Server Test Suite")
    print("="*60)
    
    # Lokal server test
    print("\n\n")
    local_tester = ServerTester(LOCAL_SERVER_URL, "Lokal Server")
    local_success = local_tester.run_all_tests()
    
    # Uzak server test
    print("\n\n")
    if REMOTE_SERVER_URL != "http://your-remote-server.com":
        remote_tester = ServerTester(REMOTE_SERVER_URL, "Uzak Server")
        remote_success = remote_tester.run_all_tests()
    else:
        print("⚠ Uzak sunucu URL'si yapılandırılmamış.")
        print("  test_server.py dosyasında REMOTE_SERVER_URL değişkenini düzenleyin.")
    
    print("\n" + "="*60)
    print("  Test Tamamlandı")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
