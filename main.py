import logging
from typing import List
from supplier_scrape_core.processer import Processer,SaverLikeIkasTemplate
from supplier_scrape_core.structers.product import Suppliers, PreState
from pathlib import Path
# erişim
# logging
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",    # Cyan
        logging.INFO: "\033[32m",     # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",    # Red
        logging.CRITICAL: "\033[41m", # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter(
    "%(asctime)s - %(levelname)s - %(message)s"
))
logger.addHandler(handler)

# statement
static_values = {
    "Satış Kanalı:nurcocuk" :"VISIBLE",
    "Tip" : "PHYSICAL"}


prestates : List[PreState] = [
    # PreState(145204,30,12),
    # PreState(147149,50,10),
    # PreState(165128,25,12),
    # PreState(168942,160,1),
    # PreState(169359,220,1),
    # PreState(169564,299,1),
    PreState(175441,350,1),
    PreState(177031,420,1),
    PreState(177073,220,6),
    # PreState(178386,50,12),
    # PreState(178897,25,12),
    # PreState(418338,899,4),
    # PreState(439623,579,4),
    # PreState(449090,285,4),
]

if __name__ == "__main__":
    Path("./output").mkdir(parents=True, exist_ok=True )

    p = Processer()
    # ürün kodları ile birlikte ürünleri çek
    products, failed_producuts = p.get_with_code(Suppliers.BALGUNES,*prestates)

    # İkas templatiyle frame oluştur
    S = SaverLikeIkasTemplate(r"core\template\ikas-urunler.xlsx")
    
    # Başarıyla çekilmiş olanları ikas frame'ine doldur ve kaydet
    S.fill(products,static_values,"./output/success.xlsx")
    
    # Başarısız olanları ikas frame'inde doldur ve kaydet
    S.fill(failed_producuts,static_values,"./output/failed.xlsx")