from bs4 import BeautifulSoup
from typing import Optional
import logging
from .structers.product import Product,Suppliers
import requests

"""
Önce ürün kodu ile ürün araması yapan sonra bu başarılı olduğunda ürün bilgilerini (Product)
classıyla döndüren
SaveLikeİkas class'ıyla da ikas ürün template (xlsx) olarak bu ürünleri dolduran kod parçaları
"""

class ProductScraper:
    """Ürün bilgilerini web'den çeken ve işleyen sınıf"""
    
    def __init__(self, timeout: int = 10):
        """
        ProductScraper başlatıcı
        
        Args:
            timeout: İstek zaman aşımı (saniye)
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_product(self, url: str, supplier: Suppliers) -> Optional[Product]:
        """
        Verilen URL'den ürün bilgilerini çeker
        
        Args:
            url: Ürün sayfası URL'si
            
        Returns:
            Product instance veya hata durumunda None
        """
        try:
            logging.info(f"Sending: {url}")
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
    

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ürün bilgilerini çek
            product = self._extract_product_info(soup, supplier)
            
            if product:
                logging.info(f"Fecthed: {product.urun_ismi}")
            else:
                logging.warning("Product information not found")
            
            return product
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Request Error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected Error: {e}")
            return None
    
    def _extract_product_info(self, soup: BeautifulSoup, supplier:Suppliers) -> Optional[Product]:
        """
        BeautifulSoup nesnesinden ürün bilgilerini ayıklar
        
        Args:
            soup: BeautifulSoup nesnesi
            
        Returns:
            Product instance
        """
        try:
            # 1. Ürün Kodu: <h6 class="pro-detail-urun-kodu mb-0">169359</h6>
            urun_kodu_elem = soup.find('h6', class_='pro-detail-urun-kodu')
            urun_kodu = urun_kodu_elem.get_text(strip=True) if urun_kodu_elem else None
            
            # 2. Ürün İsmi: <h4 class="pro-detail-title"> 4/8 YAŞ ERKEK 2Lİ ATKI BERE TAKIM </h4>
            urun_ismi_elem = soup.find('h4', class_='pro-detail-title')
            urun_ismi = urun_ismi_elem.get_text(strip=True) if urun_ismi_elem else None
            
            # 3. Kategori: <a href="https://www.balgunestekstil.com/tr/category/cocuk-bere-eldiven--131" class="text-black text-decoration-none">Çocuk Bere & Eldiven</a>
            kategori_link = soup.find('a', href=lambda x: x and 'category' in x, class_='text-black text-decoration-none')
            kategori = kategori_link.get_text(strip=True) if kategori_link else None
            kategori_url = kategori_link.get('href') if kategori_link else None
            
            # 4. Görsel URL: data-src veya src özniteliğinden
            # <img data-src="https://balgunes.sercdn.com/resimler/73d784dd52938ef089d7882b72fa4a66.jpg" 
            #      src="https://balgunes.sercdn.com/resimler/73d784dd52938ef089d7882b72fa4a66.jpg" 
            #      class="w-100 mainImg lazyloaded" alt="...">
            gorsel_elem = soup.find('img', class_='mainImg')
            gorsel_url = gorsel_elem.get('data-src') or gorsel_elem.get('src') if gorsel_elem else None
            
            # Ürün instance'ı oluştur ve döndür
            product = Product(
                urun_kodu=urun_kodu,
                urun_ismi=urun_ismi,
                kategori=kategori,
                kategori_url=kategori_url,
                gorsel_url=gorsel_url,
                marka=supplier
            )
            
            return product
            
        except Exception as e:
            logging.error(f"Product info exception: {e}")
            return None

    
    def extract_product_href_using_search(self,html_content):
        """
        BeautifulSoup kullanarak HTML sayfasından ürün href değerini çıkarır.
        
        Aranacak yapı:
        <a href="https://www.balgunestekstil.com/tr/product/...">
            <img ... class="mainImg" ... alt="...">
        </a>
        
        Args:
            html_content (str): HTML içeriği
            
        Returns:
            tuple: (href_value, found) - href değeri ve bulundu mu (True/False)
                Eğer bulunmazsa (None, False) döner
        """
        try:
            # HTML'i parse et
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Ürün bağlantısını bul
            # Aranan yapı: <a> tag'ı içinde <img class="mainImg"> olan
            product_link = soup.find('a', href=True)
            
            # Daha spesifik arama: <div class="pro card"> içindeki ilk <a> tag'ı
            pro_card = soup.find('div', class_='pro card')
            if pro_card:
                product_link = pro_card.find('a', href=True)
            
            # Alternatif arama: <a> içinde mainImg class'ı olan img
            if not product_link:
                img_with_class = soup.find('img', class_='mainImg')
                if img_with_class:
                    product_link = img_with_class.find_parent('a', href=True)
            
            # Eğer bağlantı bulunmuşsa href'i döndür
            if product_link:
                href = product_link.get('href')
                if href:
                    return href, True
            
            # Bulunamadı
            return None, False
            
        except Exception as e:
            print(f"Hata oluştu: {e}")
            return None, False