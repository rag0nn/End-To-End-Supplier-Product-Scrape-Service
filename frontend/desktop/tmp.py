import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QMenuBar, QMenu, QToolBar, QStatusBar, QDialog, QMessageBox,
    QFileDialog, QInputDialog, QComboBox, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QFont, QColor
from PyQt6.QtCore import pyqtSignal


class MainWindow(QMainWindow):
    """Ana uygulama penceresi"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("E-Ticaret API - Masaüstü Uygulaması")
        self.setGeometry(100, 100, 1200, 800)
        
        # Merkezi widget'ı ayarla
        self.setup_central_widget()
        
        # Menü çubuğunu oluştur
        self.create_menu_bar()
        
        # Araç çubuğunu oluştur
        self.create_toolbar()
        
        # Durum çubuğunu oluştur
        self.create_status_bar()
        
        # Stil ayarla
        self.apply_styles()
    
    def setup_central_widget(self):
        """Merkezi widget'ı ve düzenini ayarla"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana düzen
        main_layout = QVBoxLayout()
        
        # Başlık
        title_label = QLabel("E-Ticaret Ürün Kazıyıcı")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Kontrol paneli
        control_layout = self.create_control_panel()
        main_layout.addLayout(control_layout)
        
        # Tablo bölümü
        self.table_widget = self.create_table()
        main_layout.addWidget(self.table_widget)
        
        # Düğme paneli
        button_layout = self.create_button_panel()
        main_layout.addLayout(button_layout)
        
        central_widget.setLayout(main_layout)
    
    def create_control_panel(self):
        """Kontrol paneli oluştur"""
        control_layout = QHBoxLayout()
        
        # URL girişi
        url_label = QLabel("Website URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        control_layout.addWidget(url_label)
        control_layout.addWidget(self.url_input)
        
        # Kategori seçimi
        category_label = QLabel("Kategori:")
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Tüm", "Elektronik", "Giyim", "Ayakkabı", "Diğer"])
        control_layout.addWidget(category_label)
        control_layout.addWidget(self.category_combo)
        
        # Sayfa sayısı
        pages_label = QLabel("Sayfa Sayısı:")
        self.pages_spin = QSpinBox()
        self.pages_spin.setMinimum(1)
        self.pages_spin.setMaximum(100)
        self.pages_spin.setValue(1)
        control_layout.addWidget(pages_label)
        control_layout.addWidget(self.pages_spin)
        
        # Seçenekler
        self.auto_scroll_check = QCheckBox("Otomatik Scroll")
        control_layout.addWidget(self.auto_scroll_check)
        
        control_layout.addStretch()
        
        return control_layout
    
    def create_table(self):
        """Veri tablosu oluştur"""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "ID", "Ürün Adı", "Kategori", "Fiyat", "URL", "Durum"
        ])
        table.setRowCount(0)
        table.setAlternatingRowColors(True)
        table.setColumnWidth(1, 250)
        table.setColumnWidth(4, 300)
        
        return table
    
    def create_button_panel(self):
        """Düğme paneli oluştur"""
        button_layout = QHBoxLayout()
        
        # Başlat düğmesi
        self.start_btn = QPushButton("Başlat")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_btn.clicked.connect(self.on_start)
        button_layout.addWidget(self.start_btn)
        
        # Durdur düğmesi
        self.stop_btn = QPushButton("Durdur")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.stop_btn.clicked.connect(self.on_stop)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        # Dışa aktarma düğmesi
        self.export_btn = QPushButton("Dışa Aktar")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.export_btn.clicked.connect(self.on_export)
        button_layout.addWidget(self.export_btn)
        
        # Temizle düğmesi
        self.clear_btn = QPushButton("Temizle")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        self.clear_btn.clicked.connect(self.on_clear)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        
        return button_layout
    
    def create_menu_bar(self):
        """Menü çubuğunu oluştur"""
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu("Dosya")
        
        new_action = QAction("Yeni", self)
        new_action.triggered.connect(self.on_new)
        file_menu.addAction(new_action)
        
        open_action = QAction("Aç", self)
        open_action.triggered.connect(self.on_open)
        file_menu.addAction(open_action)
        
        save_action = QAction("Kaydet", self)
        save_action.triggered.connect(self.on_save)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Çıkış", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Düzenleme menüsü
        edit_menu = menubar.addMenu("Düzenleme")
        
        clear_action = QAction("Tabloyu Temizle", self)
        clear_action.triggered.connect(self.on_clear)
        edit_menu.addAction(clear_action)
        
        # Görünüm menüsü
        view_menu = menubar.addMenu("Görünüm")
        
        refresh_action = QAction("Yenile", self)
        refresh_action.triggered.connect(self.on_refresh)
        view_menu.addAction(refresh_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu("Yardım")
        
        about_action = QAction("Hakkında", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Araç çubuğunu oluştur"""
        toolbar = QToolBar("Ana Araç Çubuğu")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # Başlat işlemi
        start_action = QAction("Başlat", self)
        start_action.triggered.connect(self.on_start)
        toolbar.addAction(start_action)
        
        # Durdur işlemi
        stop_action = QAction("Durdur", self)
        stop_action.triggered.connect(self.on_stop)
        toolbar.addAction(stop_action)
        
        toolbar.addSeparator()
        
        # Kaydet işlemi
        save_action = QAction("Kaydet", self)
        save_action.triggered.connect(self.on_save)
        toolbar.addAction(save_action)
        
        # Yenile işlemi
        refresh_action = QAction("Yenile", self)
        refresh_action.triggered.connect(self.on_refresh)
        toolbar.addAction(refresh_action)
    
    def create_status_bar(self):
        """Durum çubuğunu oluştur"""
        self.status_label = QLabel("Hazır")
        self.statusBar().addWidget(self.status_label)
    
    def apply_styles(self):
        """Uygulama stilini ayarla"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
            QTableWidget {
                border: 1px solid #cccccc;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QMenuBar {
                background-color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            QToolBar {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
            }
        """)
    
    # Slot metodları
    def on_start(self):
        """Başlat işlemi"""
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir URL girin!")
            return
        
        self.status_label.setText(f"Kazıma başladı: {url}")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.url_input.setEnabled(False)
        
        # Örnek veri ekle
        self.add_sample_data()
    
    def on_stop(self):
        """Durdur işlemi"""
        self.status_label.setText("İşlem durduruldu")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.url_input.setEnabled(True)
    
    def on_export(self):
        """Dışa aktarma işlemi"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Dosyayı Kaydet", "", "CSV Dosyaları (*.csv);;Excel Dosyaları (*.xlsx)"
        )
        if file_path:
            QMessageBox.information(self, "Başarı", f"Dosya kaydedildi: {file_path}")
            self.status_label.setText(f"Dosya dışa aktarıldı: {file_path}")
    
    def on_clear(self):
        """Tabloyu temizle"""
        reply = QMessageBox.question(
            self, "Onay", "Tabloyu temizlemek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.table_widget.setRowCount(0)
            self.status_label.setText("Tablo temizlendi")
    
    def on_new(self):
        """Yeni dosya oluştur"""
        self.table_widget.setRowCount(0)
        self.url_input.clear()
        self.status_label.setText("Yeni dosya oluşturuldu")
    
    def on_open(self):
        """Dosya aç"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Dosyayı Aç", "", "CSV Dosyaları (*.csv);;Excel Dosyaları (*.xlsx)"
        )
        if file_path:
            self.status_label.setText(f"Dosya açıldı: {file_path}")
    
    def on_save(self):
        """Dosyayı kaydet"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Dosyayı Kaydet", "", "CSV Dosyaları (*.csv);;Excel Dosyaları (*.xlsx)"
        )
        if file_path:
            self.status_label.setText(f"Dosya kaydedildi: {file_path}")
    
    def on_refresh(self):
        """Verileri yenile"""
        self.status_label.setText("Veriler yenilendi")
    
    def on_about(self):
        """Hakkında diyaloğu"""
        QMessageBox.about(
            self, "Hakkında",
            "E-Ticaret API - Masaüstü Uygulaması\n\n"
            "Versiyon: 1.0.0\n"
            "Geliştirici: Geliştirici Ekibi\n\n"
            "Bu uygulama e-ticaret platformlarından ürün kazımak için tasarlanmıştır."
        )
    
    def add_sample_data(self):
        """Örnek veri ekle (test için)"""
        sample_data = [
            ["1", "Laptop", "Elektronik", "$999.99", "https://example.com/1", "Tamamlandı"],
            ["2", "T-Shirt", "Giyim", "$19.99", "https://example.com/2", "Tamamlandı"],
            ["3", "Spor Ayakkabı", "Ayakkabı", "$79.99", "https://example.com/3", "İşleniyor"],
        ]
        
        for row_idx, row_data in enumerate(sample_data):
            self.table_widget.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                self.table_widget.setItem(row_idx, col_idx, item)


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
