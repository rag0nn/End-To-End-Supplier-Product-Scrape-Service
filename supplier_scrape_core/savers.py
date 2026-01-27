from typing import List
import logging
import pandas as pd
from .structers.product import Product
import os

class SaverLikeIkasTemplate:
    
    def __init__(self,template_path:str = None):
        if template_path is None:
            self.template_path = os.path.dirname(__file__) + r"\template\ikas-urunler.xlsx"
        else: 
            self.template_path = template_path
            
        logging.info(f"Template path: {self.template_path}")
        self.template_frame = self._get_template()
        self.column_remap = self._get_column_remap()
        
    def _get_template(self):
        try:
            frame = pd.read_excel(self.template_path)
        except Exception as e:
            logging.error(f"{e} /n Template Okunamadı")
            raise Exception(e)
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
            

