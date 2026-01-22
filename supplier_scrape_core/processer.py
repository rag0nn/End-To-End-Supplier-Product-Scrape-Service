from typing import List
import requests
from .scrape_balgunes import BalgunesProductScraper
import logging
import pandas as pd
from .structers.product import Product, Suppliers, PreState
import logging
import os

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

class Processer:
    def __init__(self):
        self.product_scraper = None
    
    def get_with_code(self,supplier:Suppliers,*prestates:List[PreState])->tuple:
        if supplier == Suppliers.BALGUNES:
            self.product_scraper = BalgunesProductScraper()
        else:
            raise Exception("Invalid Supplier Choise")
            return
            
        products = []
        failed_products = []
        for i, prestate in enumerate(prestates):
            url = supplier.value["search_link_prefix"].format(code=str(prestate.code))
            logging.info(f"[{i}] Searching url: "+url)
            session = requests.Session()
            session.headers.update(headers)

            # çekilememe durumunda atanacak eleman
            failed_product = Product(urun_kodu=prestate.code,marka=supplier,fiyat=prestate.price,stok=prestate.stock)
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
            else:
                logging.error(f"[{i}] Exception on html fetch:", response.status_code)
                failed_products.append(failed_product)
                continue
            
            link, ret = self.product_scraper.extract_product_href_using_search(html_content)
            
            if ret:
                logging.info(f"[{i}] Product Link: "+ link)
            else:
                logging.error(f"[{i}] Not found product: "+ str(prestate.code))
                failed_products.append(failed_product)
                continue
            
            product = self.product_scraper.scrape_product(link, supplier)
            if product:
                logging.info(f"[{i}] Success: {product}")
            else:
                logging.error(f"[{i}] Exception on product fetch")
                failed_products.append(failed_product)
                continue
            
            product.fiyat = prestate.price
            product.stok = prestate.stock
            products.append(product)
        logging.info(f"Total Successful: {len(products)} Failed: {len(failed_products)}")
        return products, failed_products
            
class SaverLikeIkasTemplate:
    
    def __init__(self,template_path:str = None):
        if template_path is None:
            self.template_path = os.path.dirname(__file__) + r"\template\ikas-urunler.xlsx"
        else: 
            self.template_path = template_path
            
            logging.info(f"Output template path: {self.template_path}")
            print(f"Output template path: {self.template_path}")
        self.template_frame = self._get_template()
        self.column_remap = self._get_column_remap()
        
    def _get_template(self):
        try:
            frame = pd.read_excel(self.template_path)
        except Exception as e:
            logging.error(f"{e} /n Template Okunamadı")
        return frame
    
    def _get_column_remap(self):
        return {
            'urun_kodu': "Barkod Listesi",
            'urun_ismi': "İsim",
            'kategori': "Kategoriler",
            'gorsel_url': "Resim URL",
            'fiyat': "Satış Fiyatı",
            'stok': "Stok:Ana Depo",
            'aciklama': "Açıklama",
            "marka" : "Tedarikçi"
            }
    
    def fill(self, products: List[Product], static_values = None,dist_path = "./output.xlsx"):

        rows = []

        for product in products:
            product_serie = (
                pd.Series(product.to_dict())
                .rename(self.column_remap)
                .reindex(self.template_frame.columns)
            )

            rows.append(product_serie)

        new_df = pd.DataFrame(rows)

        self.filled_frame = pd.concat(
            [self.template_frame, new_df],
            ignore_index=True,
        )

        # statik değerleri fill et
        for k,v in static_values.items():
            self.filled_frame[k] = v
    
        logging.debug(self.filled_frame)
        
        try:
            self.filled_frame.to_excel(dist_path, index=False)
            logging.info(f"Saved To: {dist_path}")
        except Exception as e:
            logging.error(f"Save Fail To: {dist_path} \n{e}")
            

