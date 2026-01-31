from typing import List
import requests
from .scrape_direct import ProductScraper
import logging
from .structers.product import Product, Suppliers, PreState
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# SSL uyarılarını bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

def create_session_with_retries():
    """Retry mekanizmasıyla session oluştur"""
    session = requests.Session()
    session.headers.update(headers)
    
    # Retry stratejisi tanımla
    retry_strategy = Retry(
        total=3,  # Toplam retry sayısı
        backoff_factor=1,  # İlk 1 saniye, sonra 2, 4 saniye bekleme
        status_forcelist=[403, 429, 500, 502, 503, 504],  # Bu status kodlarında retry et
        allowed_methods=["GET", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

class Processer:
    def __init__(self):
        self.product_scraper = None
    
    def get_with_code(self,supplier:Suppliers,*prestates:List[PreState])->tuple:
        self.product_scraper = ProductScraper()

        products = []
        failed_products = []
        logging.info(f"\n{'=' *140}\nStarting with: {supplier.value['name']} Supplier\n\n")
        for i, prestate in enumerate(prestates):
            prestate:PreState
            url = supplier.value["search_link_prefix"].format(code=str(prestate.code))
            logging.info(f"[{i}][{prestate.code}] Searching url: "+url)
            
            # Retry mekanizmasıyla session oluştur
            session = create_session_with_retries()
            
            logging.debug(f"[{i}][{prestate.code}] Session headers: {session.headers}")

            # çekilememe durumunda atanacak eleman
            failed_product = Product(urun_kodu=prestate.code,marka=supplier,fiyat=prestate.price,stok=prestate.stock)
            
            try:
                # SSL verification devre dışı ve timeout ekle
                logging.info(f"[{i}][{prestate.code}] Fetching with verify=False, timeout=15")
                response = session.get(url, timeout=15, verify=False)
                logging.info(f"[{i}][{prestate.code}] Response status code: {response.status_code}")
                logging.debug(f"[{i}][{prestate.code}] Response headers: {response.headers}")
            except Exception as e:
                logging.error(f"[{i}][{prestate.code}] Exception on finding with search (retry failed): {str(e)}")
                failed_products.append(failed_product)
                continue
            
            if response.status_code == 200:
                html_content = response.text
            else:
                logging.error(f"[{i}][{prestate.code}] Exception on html fetch: {response.status_code}")
                failed_products.append(failed_product)
                continue
            
            link, ret = self.product_scraper.extract_product_href_using_search(html_content)
            
            if ret:
                logging.info(f"[{i}][{prestate.code}] Product Link: "+ link)
            else:
                logging.error(f"[{i}][{prestate.code}] Product not found: ")
                failed_products.append(failed_product)
                continue
            
            product = self.product_scraper.scrape_product(link, supplier)
            if product:
                logging.info(f"[{i}][{prestate.code}] Product fetch Success: {product}")
            else:
                logging.error(f"[{i}][{prestate.code}] Exception on product fetch")
                failed_products.append(failed_product)
                continue
            
            product.fiyat = prestate.price
            product.stok = prestate.stock
            products.append(product)
        logging.info(f"\nTotal Successful: {len(products)} Failed: {len(failed_products)}\n{supplier.value['name']} fetch process ended.\n{'='*140}")
        return products, failed_products
            
