
from typing import Dict, Optional
from enum import Enum

class Suppliers(Enum):
    BALGUNES = {"prefix" : "11",
                "name" : "BALGÜNEŞ", 
                "search_link_prefix" : "https://www.balgunestekstil.com/urunler/arama?q={code}"
                }
    BABEXI = {"prefix" : "12",
                "name" : "BABEXI", 
                "search_link_prefix" : "https://www.toptanbebegiyim.com/urunler/arama?q={code}"
                }
    MALKOC = {"prefix" : "13",
                "name" : "MALKOÇ", 
                "search_link_prefix" : "https://www.malkocbebe.com/urunler/arama?q={code}"
                }       
    
class PreState:
    """Ürünün çekilip çekilmeme durumuna bakılmaksızın geçirelecek stok, ürün kodu ve fiyat bilgisi"""
    def __init__(self, code:int, price:Optional[int] = None, stock:Optional[int] = None):
        self.stock = stock
        self.code = code
        self.price = price
        
    def __repr__(self):
        return f"PreState {self.code} {self.price} {self.stock}"
    
class Product:
    """Ürün bilgilerini temsil eden sınıf"""
    
    def __init__(self, 
                 urun_kodu: Optional[str] = None,
                 urun_ismi: Optional[str] = None,
                 kategori: Optional[str] = None,
                 kategori_url: Optional[str] = None,
                 gorsel_url: Optional[str] = None,
                 fiyat: Optional[str] = None,
                 stok: Optional[str] = None,
                 aciklama: Optional[str] = None,
                 puan: Optional[str] = None,
                 marka: Optional[Suppliers] = None
                 ):
        """
        Product başlatıcı
        
        Args:
            urun_kodu: Ürün kodu
            urun_ismi: Ürün ismi
            kategori: Ürün kategorisi
            kategori_url: Kategori URL'si
            gorsel_url: Ürün görseli URL'si
            fiyat: Ürün fiyatı
            stok: Stok bilgisi
            aciklama: Ürün açıklaması
            puan: Ürün puanı
            marka: Ürün markası
        """
        if marka:
            self.urun_kodu = int("".join([marka.value["prefix"],str(urun_kodu)]))
        else:
            self.urun_kodu = urun_kodu
        self.urun_ismi = urun_ismi
        self.kategori = kategori
        self.kategori_url = kategori_url
        self.gorsel_url = gorsel_url
        self.fiyat = fiyat
        self.stok = stok
        self.aciklama = aciklama
        self.puan = puan
        self.marka = marka

    
    def to_dict(self) -> Dict:
        """Product instance'ını dictionary'e dönüştür"""
        return {
            'urun_kodu': self.urun_kodu,
            'urun_ismi': self.urun_ismi,
            'kategori': self.kategori,
            'kategori_url': self.kategori_url,
            'gorsel_url': self.gorsel_url,
            'fiyat': self.fiyat,
            'stok': self.stok,
            'aciklama': self.aciklama,
            'puan': self.puan,
            'marka' : self.marka.value["prefix"]
        }
    
    def serialize(self):
        return f"{self.urun_kodu}-{self.urun_ismi}-{self.kategori}-{self.kategori_url}-{self.gorsel_url}-{self.fiyat}-{self.stok}-{self.aciklama}-{self.puan}-{self.marka.value['prefix']}"

    def __repr__(self) -> str:
        return f"Product(kodu={self.urun_kodu}, ismi={self.urun_ismi})"
    
    def __str__(self) -> str:
        return f"{self.urun_kodu} - {self.urun_ismi}"

