# Flask API Dokumentasyonu

## 📋 Genel Bilgi

Bu Flask servisi, e-ticaret ürünlerini dinamik olarak işlemek ve Excel dosyaları döndürmek için tasarlanmıştır.

**Temel URL:** `http://localhost:5000`

---

## 🚀 Başlangıç

### Gereklilikler
```bash
pip install flask requests openpyxl pandas
```

### Sunucuyu Başlat
```bash
python app.py
```

Sunucu başlatıldığında:
```
INFO:werkzeug: * Running on http://0.0.0.0:5000
```

---

## 📡 API Endpoints

### 1. Health Check
Sunucunun çalışıp çalışmadığını kontrol et.

**URL:** `GET /api/health`

**Response (200):**
```json
{
  "status": "ok",
  "message": "Server çalışıyor"
}
```

**cURL Örneği:**
```bash
curl http://localhost:5000/api/health
```

---

### 2. Process Products (Single Excel)
Ürünleri işle ve başarılı olanların Excel dosyasını döndür.

**URL:** `POST /api/process-products`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "prestates": [
    {
      "code": 145204,
      "price": 30,
      "stock": 12
    },
    {
      "code": 147149,
      "price": 50,
      "stock": 10
    }
  ],
  "supplier": "BALGUNES",
  "static_values": {
    "Satış Kanalı:nurcocuk": "VISIBLE",
    "Tip": "PHYSICAL"
  }
}
```

**Parametreler:**
- `prestates` (Array, **Gerekli**): Ürün bilgilerini içeren dizi
  - `code` (Integer, **Gerekli**): Ürün kodu
  - `price` (Integer, **Gerekli**): Ürün fiyatı
  - `stock` (Integer, **Gerekli**): Stok miktarı
- `supplier` (String, Optional): Tedarikçi ismi (Default: "BALGUNES")
- `static_values` (Object, Optional): Sabit değerler (Default: sistem varsayılanları)

**Response (200):**
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Header `X-Success-Count`: Başarılı ürün sayısı
- Header `X-Failed-Count`: Başarısız ürün sayısı
- Body: Binary Excel dosyası (success.xlsx)

**Response (400):**
```json
{
  "error": "prestates: array formatında olmalı"
}
```

**Response (500):**
```json
{
  "error": "İşleme hatası: ..."
}
```

**cURL Örneği:**
```bash
curl -X POST http://localhost:5000/api/process-products \
  -H "Content-Type: application/json" \
  -d '{
    "prestates": [
      {"code": 145204, "price": 30, "stock": 12},
      {"code": 147149, "price": 50, "stock": 10}
    ]
  }' \
  -o success.xlsx
```

**Python Örneği:**
```python
import requests

payload = {
    "prestates": [
        {"code": 145204, "price": 30, "stock": 12},
        {"code": 147149, "price": 50, "stock": 10}
    ]
}

response = requests.post(
    "http://localhost:5000/api/process-products",
    json=payload
)

# Dosyayı kaydet
with open("success.xlsx", "wb") as f:
    f.write(response.content)

print(f"Başarılı: {response.headers.get('X-Success-Count')}")
print(f"Başarısız: {response.headers.get('X-Failed-Count')}")
```

---

### 3. Process Products ZIP
Ürünleri işle ve başarılı/başarısız Excel dosyalarının ikisini ZIP olarak döndür.

**URL:** `POST /api/process-products-zip`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "prestates": [
    {"code": 145204, "price": 30, "stock": 12},
    {"code": 147149, "price": 50, "stock": 10},
    {"code": 165128, "price": 25, "stock": 12}
  ],
  "supplier": "BALGUNES"
}
```

**Response (200):**
- Content-Type: `application/zip`
- Header `X-Success-Count`: Başarılı ürün sayısı
- Header `X-Failed-Count`: Başarısız ürün sayısı
- Body: ZIP dosyası içeriği
  - `success.xlsx`: Başarılı ürünler
  - `failed.xlsx`: Başarısız ürünler

**cURL Örneği:**
```bash
curl -X POST http://localhost:5000/api/process-products-zip \
  -H "Content-Type: application/json" \
  -d '{
    "prestates": [
      {"code": 145204, "price": 30, "stock": 12}
    ]
  }' \
  -o products.zip
```

**Python Örneği:**
```python
import requests
import zipfile
import io

payload = {
    "prestates": [
        {"code": 145204, "price": 30, "stock": 12},
        {"code": 147149, "price": 50, "stock": 10}
    ]
}

response = requests.post(
    "http://localhost:5000/api/process-products-zip",
    json=payload
)

# ZIP dosyasını kaydet ve aç
with open("products.zip", "wb") as f:
    f.write(response.content)

# ZIP içeriğini kontrol et
with zipfile.ZipFile("products.zip", "r") as zip_ref:
    print("ZIP içeriği:", zip_ref.namelist())
    zip_ref.extractall("./extracted")
```

---

## 🎯 Kullanım Örnekleri

### Örnek 1: Basit İstek
```python
import requests

response = requests.post(
    "http://localhost:5000/api/process-products",
    json={
        "prestates": [
            {"code": 169359, "price": 220, "stock": 1}
        ]
    }
)

if response.status_code == 200:
    with open("result.xlsx", "wb") as f:
        f.write(response.content)
```

### Örnek 2: Dinamik PreState Listesi
```python
# Programatik olarak prestates oluştur
codes = [145204, 147149, 165128, 168942, 169359]
prestates = [
    {"code": code, "price": 100 + i*10, "stock": i+1}
    for i, code in enumerate(codes)
]

response = requests.post(
    "http://localhost:5000/api/process-products-zip",
    json={"prestates": prestates}
)
```

### Örnek 3: Hata Yönetimi
```python
try:
    response = requests.post(
        "http://localhost:5000/api/process-products",
        json={"prestates": []},
        timeout=30
    )
    
    if response.status_code == 200:
        print(f"✓ Başarılı: {response.headers.get('X-Success-Count')}")
    else:
        error = response.json()
        print(f"✗ Hata: {error['error']}")
        
except requests.exceptions.Timeout:
    print("✗ İstek zaman aşımına uğradı")
except requests.exceptions.ConnectionError:
    print("✗ Sunucuya bağlanılamadı")
```

---

## ⚙️ Yapılandırma

### app.py
```python
# Flask app konfigürasyonu
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Static values (varsayılan)
STATIC_VALUES = {
    "Satış Kanalı:nurcocuk": "VISIBLE",
    "Tip": "PHYSICAL"
}
```

### Supported Suppliers
```python
class Suppliers(Enum):
    BALGUNES = {...}
    # İleride başka tedarikçiler eklenebilir
```

---

## 🔒 Hata Kodları

| Kod | Anlam | Çözüm |
|-----|-------|-------|
| 200 | Başarı | - |
| 400 | Geçersiz İstek | Request body formatını kontrol edin |
| 404 | Endpoint Bulunamadı | URL'i kontrol edin |
| 500 | Sunucu Hatası | Sunucu loglarını kontrol edin |

---

## 🧪 Test Etme

Sağlanan `test_api.py` dosyasını kullanarak API'yi test edebilirsiniz:

```bash
# Sunucuyu başlat (Terminal 1)
python app.py

# Test dosyasını çalıştır (Terminal 2)
python test_api.py
```

---

## 📊 İstek/Yanıt Akışı

```
Client                          Server
  |                               |
  |-- POST /api/process-products--|
  |    (prestates JSON)           |
  |                               |-- Ürünleri işle
  |                               |-- Excel oluştur
  |<-- Excel Dosyası (200)       |
  |    (X-Success-Count header)  |
```

---

## 🔌 Integration Örnekleri

### Node.js/JavaScript
```javascript
const fetch = require('node-fetch');
const fs = require('fs');

const payload = {
  prestates: [
    { code: 145204, price: 30, stock: 12 },
    { code: 147149, price: 50, stock: 10 }
  ]
};

fetch('http://localhost:5000/api/process-products', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
})
.then(res => res.buffer())
.then(buffer => fs.writeFileSync('success.xlsx', buffer))
.catch(err => console.error(err));
```

### CURL
```bash
curl -X POST http://localhost:5000/api/process-products \
  -H "Content-Type: application/json" \
  -d @payload.json \
  --output success.xlsx
```

### PowerShell
```powershell
$payload = @{
    prestates = @(
        @{ code = 145204; price = 30; stock = 12 }
    )
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/api/process-products" `
  -Method POST `
  -ContentType "application/json" `
  -Body $payload `
  -OutFile "success.xlsx"
```

---

## 📝 Not

- Sunucu, her isteği işlerken logging bilgisi yazdırır
- `X-Success-Count` ve `X-Failed-Count` header'larından işlem sonuçlarını öğrenebilirsiniz
- PreState'ler `*args` ile dinamik olarak işlenir, sayı sınırı yoktur
- ZIP endpoint'i büyük batch işlemler için tavsiye edilir

