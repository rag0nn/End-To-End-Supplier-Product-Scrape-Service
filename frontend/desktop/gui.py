from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget,QTableWidgetItem,
    QComboBox, QPushButton,QLineEdit,QSpinBox,QCheckBox,
    QMessageBox,QProgressBar
)

from PyQt6.QtGui import QFont
from typing import Dict, List, Callable
import sys
import os
import logging
import yaml

# API kökü dizinini sys.path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from supplier_scrape_core.processer import Processer
from supplier_scrape_core.savers import SaverLikeIkasTemplate
from supplier_scrape_core.structers.product import PreState, Suppliers, Product
from supplier_scrape_core.config.config import STATIC_VALUES
from backend.client import Client


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
        return f'{color}{message}{self.RESET}'


logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter(
    "%(asctime)s - %(levelname)s - %(message)s"
))
logger.addHandler(handler)

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()

        self.config = self.load_config()
        self.setWindowTitle("Ürün Çekme Uygulaması")
        self.setGeometry(100, 100, 1200, 600)
        self.set_central_widget()

    def load_config(self)->Dict:
        pth = f"{os.path.dirname(__file__)}/config.yaml"
        with open(pth) as f:
            config = yaml.safe_load(f)
        return config
    
    def set_central_widget(self):
        """Merkezi widget'ı ve düzenini ayarla"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana düzen
        main_layout = QVBoxLayout()
        
        # Başlık
        title_label = QLabel("Ürün Kazıyıcı")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        form_layout = self.set_form_widgets()
        main_layout.addLayout(form_layout)
        
        self.table_widget = self.create_table()
        main_layout.addWidget(self.table_widget)
        
        self.sendbar_layout = self.create_sendbar()
        main_layout.addLayout(self.sendbar_layout)
        
        central_widget.setLayout(main_layout)
        
    def set_form_widgets(self):
        h_layout = QHBoxLayout()
        spacing = 40

        # supplier kodu
        self.supplier_label = QLabel("Tedarikçi Kodu")
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItems(list(str(x.value["prefix"] + " " + x.value["name"]) for x in Suppliers))
        h_layout.addWidget(self.supplier_label)
        h_layout.addWidget(self.supplier_combo)
        
        h_layout.addSpacing(spacing)

        # ürün kodu
        self.product_code_label = QLabel("Ürün Kodu")
        self.product_code_lineedit = QLineEdit()
        h_layout.addWidget(self.product_code_label)
        h_layout.addWidget(self.product_code_lineedit)
        
        h_layout.addSpacing(spacing)
        
        # ürün fiyatı
        self.product_price_label = QLabel("Ürün Fiyatı")
        self.product_price_lineedit = QLineEdit()
        h_layout.addWidget(self.product_price_label)
        h_layout.addWidget(self.product_price_lineedit)
        
        h_layout.addSpacing(spacing)
        
        # adeti
        self.product_count_label = QLabel("Ürün Adeti")
        self.product_count_box = QSpinBox()
        self.product_count_box.setMinimum(1)
        self.product_count_box.setMaximum(100)
        self.product_count_box.setValue(1)
        h_layout.addWidget(self.product_count_label)
        h_layout.addWidget(self.product_count_box)
        
        h_layout.addSpacing(spacing)
        
        # ekle butonu
        self.add_button = QPushButton("Ekle")
        self.add_button.clicked.connect(self.add_item_to_queue)
        h_layout.addWidget(self.add_button)

        return h_layout
        
    def add_item_to_queue(self):
        self.add_button.setEnabled(False)
        
        # checks
        try:
            product_code = self.product_code_lineedit.text()
            product_code = int(product_code)
        except:
            self.add_button.setEnabled(True)
            if product_code:
                QMessageBox.warning(self, "Hatalı Giriş", "Ürün kodu sadece sayı içermelidir")
            else:
                QMessageBox.warning(self, "Eksik Giriş", "Ürün kodu mutlaka girilmelidir")
            return
            
        try:
            product_price = self.product_price_lineedit.text()
            product_price = int(product_price)
        except:
            self.add_button.setEnabled(True)
            if product_price:
                QMessageBox.warning(self, "Hatalı Giriş", "Ürün miktarı sadece sayı içermelidir")
            else:
                QMessageBox.warning(self, "Eksik Giriş", "Ürün miktarı mutlaka girilmelidir")
            return

        
        supplierIdx =  self.supplier_combo.currentIndex()
        chosenSupplier = list(Suppliers)[supplierIdx]
        product_count = int(self.product_count_box.text())
        
        row = self.table_widget.rowCount()
        self.table_widget.insertRow(row)

        self.table_widget.setItem(row, 0, QTableWidgetItem(chosenSupplier.value["prefix"]))
        self.table_widget.setItem(row, 1, QTableWidgetItem(str(product_code)))
        self.table_widget.setItem(row, 2, QTableWidgetItem(str(product_price)))
        self.table_widget.setItem(row, 3, QTableWidgetItem(str(product_count)))
        self.table_widget.setItem(row, 4, QTableWidgetItem(str(None)))

        self.product_code_lineedit.clear()
        self.product_price_lineedit.clear()
        self.add_button.setEnabled(True)
        
    def create_table(self):
        """Veri tablosu oluştur"""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "Tedarikçi", "Ürün Kodu", "Fiyat", "Adet", "Durum"
        ])
        table.setRowCount(0)
        table.setAlternatingRowColors(True)
        table.setColumnWidth(0, 150)
        table.setColumnWidth(1, 250)
        table.setColumnWidth(2, 250)
        table.setColumnWidth(3, 250)
        table.setColumnWidth(4, 100)
        
        return table

    def create_sendbar(self):
        layout = QHBoxLayout()
        
        # send type
        self.send_type_checkbox = QCheckBox("Çevrimiçi Gönderim")
        layout.addWidget(self.send_type_checkbox)
        
        # progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # send buton
        self.send_button = QPushButton("Gönder")
        self.send_button.clicked.connect(self.send)
        self.send_button.setMaximumWidth(200)
        self.send_button.setFixedHeight(40)

        layout.addWidget(self.send_button)
        
        return layout
        
    def send(self):
        
        if self.table_widget.rowCount() == 0:
            QMessageBox.warning(self, "Hata", "Tabloya herhangi bir öğe eklenmemiş")
            return
        # tedarikçi kategorilerine göre ayıkla, sub_prestates sözlüğünde tut
        data = []
        for row in range(self.table_widget.rowCount()):
            row_data = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                row_data.append(item.text() if item else None)
            data.append(row_data)

        sup_prestates = {}
        for i in Suppliers:
            sup_prestates.update({i : []})
            
        for row in data:
            
            for elem in Suppliers:
                if elem.value["prefix"] == row[0]:
                    supplier = elem
                    break
            
            if supplier is None:
                QMessageBox.warning(self, "Hata", f"Tedarikçi '{row[0]}' bulunamadı")
                continue
            
            try:
                code = int(row[1])
                price = int(row[2])
                stock = int(row[3])
                
                prestate = PreState(code=code, price=price, stock=stock)
                
                sup_prestates[supplier].append(prestate)
                        
            except ValueError as e:
                QMessageBox.warning(self, "Hata", f"Geçersiz veri formatı: {str(e)}")
                continue
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"İşlem hatası: {str(e)}")
                continue
            
        print("SUP PRESTATES", sup_prestates)
            
        # remote ya da local processor seçeneğine göre işlem yap
        if self.send_type_checkbox.isChecked():
            client = Client(self.config["REMOTE_BASE_URL"])
            for k,v in sup_prestates.items():
                if len(v) == 0:
                    continue
                
                successed, failed = client.send(sup_prestates[k],k)
                successed:List[Product]
                failed:List[Product]
                if not successed:
                    QMessageBox.information(self, "Başarılı", f"Veri çekmede bir problem meydana geldi.")   
                    break
                # Table yenile başarılı
                for product in successed:
                    for j, row in enumerate(data):
                        code = int(row[1])     
                        product_code = str(product.urun_kodu)[2:]
                        if str(product_code) == str(code):
                            self.table_widget.setItem(j,4,QTableWidgetItem(str(True)))
                            break
                # Table yenile başarısız
                for product in failed:
                    for j, row in enumerate(data):
                        code = int(row[1])     
                        product_code = str(product.urun_kodu)[2:]
                        if str(product_code) == str(code):
                            self.table_widget.setItem(j,4,QTableWidgetItem(str(False)))
                            break
                        
                saver = SaverLikeIkasTemplate()

                # Başarıyla çekilmiş olanları ikas frame'ine doldur ve kaydet
                out_path = f"./frontend/desktop/output/success_{k.value["name"]}.xlsx"
                filled_frame = saver.fill(successed,STATIC_VALUES)
                saver.write(filled_frame,out_path)
                
                # Başarısız olanları ikas frame'inde doldur ve kaydet
                out_path = f"./frontend/desktop/output/failed_{k.value["name"]}.xlsx"
                filled_frame = saver.fill(failed,STATIC_VALUES)
                saver.write(filled_frame,out_path)

            QMessageBox.information(self, "Başarılı", f"Ürünler başarıyla işlendi")
        else:
            processer = Processer()
 
            for k,v in sup_prestates.items():
                if len(v) == 0:
                    continue
                
                products, failed_producuts = processer.get_with_code(k, *sup_prestates[k])
                products:list[Product]
                failed_producuts:list[Product]
                
                # Table yenile başarılı
                for product in products:
                    for j, row in enumerate(data):
                        code = int(row[1])     
                        product_code = str(product.urun_kodu)[2:]
                        if str(product_code) == str(code):
                            self.table_widget.setItem(j,4,QTableWidgetItem(str(True)))
                            break
                # Table yenile başarısız
                for product in failed_producuts:
                    for j, row in enumerate(data):
                        code = int(row[1])     
                        product_code = str(product.urun_kodu)[2:]
                        if str(product_code) == str(code):
                            self.table_widget.setItem(j,4,QTableWidgetItem(str(False)))
                            break
                        
                saver = SaverLikeIkasTemplate()
                                

                # Başarıyla çekilmiş olanları ikas frame'ine doldur ve kaydet
                saver.fill(products,STATIC_VALUES,f"./frontend/desktop/output/success_{k.value["name"]}.xlsx")
                
                # Başarısız olanları ikas frame'inde doldur ve kaydet
                saver.fill(failed_producuts,STATIC_VALUES,f"./frontend/desktop/output/failed_{k.value["name"]}.xlsx")

            QMessageBox.information(self, "Başarılı", f"Ürünler başarıyla işlendi")

def main():
    """Ana fonksiyon"""
    app = QApplication(sys.argv)
    
    # Uygulamanın stilini ayarla (isteğe bağlı)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
