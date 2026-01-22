"""
Flask API Test Örnekleri
========================

Bu dosya Flask API'nı test etmek için örnek kodlar içerir.
"""

import requests
import json
import time

# API URL
BASE_URL = "http://localhost:5000"

# Örnek 1: Sağlık durumu kontrolü
def test_health_check():
    """Sunucunun çalışıp çalışmadığını kontrol et"""
    print("\n" + "="*50)
    print("TEST 1: Health Check")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


# Örnek 2: Ürünleri işle (Success Excel döner)
def test_process_products():
    """Ürünleri işle ve success.xlsx dosyasını indir"""
    print("\n" + "="*50)
    print("TEST 2: Process Products (Single Excel)")
    print("="*50)
    
    payload = {
        "prestates": [
            {"code": 145204, "price": 30, "stock": 12},
            {"code": 147149, "price": 50, "stock": 10},
            {"code": 165128, "price": 25, "stock": 12},
            {"code": 168942, "price": 160, "stock": 1},
            {"code": 169359, "price": 220, "stock": 1},
        ],
        "supplier": "BALGUNES",
        "static_values": {
            "Satış Kanalı:nurcocuk": "VISIBLE",
            "Tip": "PHYSICAL"
        }
    }
    
    print(f"Gönderilen PreState sayısı: {len(payload['prestates'])}")
    
    response = requests.post(
        f"{BASE_URL}/api/process-products",
        json=payload,
        timeout=300  # 5 dakika timeout
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Başarılı: {response.headers.get('X-Success-Count')}")
    print(f"Başarısız: {response.headers.get('X-Failed-Count')}")
    
    if response.status_code == 200:
        # Dosyayı kaydet
        with open("./test_output/success.xlsx", "wb") as f:
            f.write(response.content)
        print("✓ Dosya kaydedildi: ./test_output/success.xlsx")
    else:
        print(f"Error: {response.json()}")


# Örnek 3: Ürünleri işle (ZIP format döner)
def test_process_products_zip():
    """Ürünleri işle ve both Excel'leri ZIP olarak indir"""
    print("\n" + "="*50)
    print("TEST 3: Process Products (ZIP Format)")
    print("="*50)
    
    payload = {
        "prestates": [
            {"code": 145204, "price": 30, "stock": 12},
            {"code": 147149, "price": 50, "stock": 10},
            {"code": 165128, "price": 25, "stock": 12},
        ],
        "supplier": "BALGUNES"
    }
    
    print(f"Gönderilen PreState sayısı: {len(payload['prestates'])}")
    
    response = requests.post(
        f"{BASE_URL}/api/process-products-zip",
        json=payload,
        timeout=300
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Başarılı: {response.headers.get('X-Success-Count')}")
    print(f"Başarısız: {response.headers.get('X-Failed-Count')}")
    
    if response.status_code == 200:
        # Dosyayı kaydet
        with open("./test_output/products.zip", "wb") as f:
            f.write(response.content)
        print("✓ ZIP dosyası kaydedildi: ./test_output/products.zip")
    else:
        print(f"Error: {response.json()}")


# Örnek 4: Birden fazla ürün (*args gibi)
def test_many_products():
    """Çok sayıda ürünü işle"""
    print("\n" + "="*50)
    print("TEST 4: Many Products (Dynamic Count)")
    print("="*50)
    
    # Dinamik olarak PreState oluştur
    prestates = [
        {"code": 145204, "price": 30, "stock": 12},
        {"code": 147149, "price": 50, "stock": 10},
        {"code": 165128, "price": 25, "stock": 12},
        {"code": 168942, "price": 160, "stock": 1},
        {"code": 169359, "price": 220, "stock": 1},
        {"code": 169564, "price": 299, "stock": 1},
        {"code": 175441, "price": 350, "stock": 1},
        {"code": 177031, "price": 420, "stock": 1},
        {"code": 177073, "price": 220, "stock": 6},
        {"code": 178386, "price": 50, "stock": 12},
        {"code": 178897, "price": 25, "stock": 12},
        {"code": 418338, "price": 899, "stock": 4},
        {"code": 439623, "price": 579, "stock": 4},
        {"code": 449090, "price": 285, "stock": 4},
    ]
    
    payload = {
        "prestates": prestates,
        "supplier": "BALGUNES"
    }
    
    print(f"Gönderilen PreState sayısı: {len(payload['prestates'])}")
    print(f"Ürün kodları: {[p['code'] for p in prestates[:3]]}... (toplam {len(prestates)})")
    
    response = requests.post(
        f"{BASE_URL}/api/process-products-zip",
        json=payload,
        timeout=600  # 10 dakika timeout
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Başarılı: {response.headers.get('X-Success-Count')}")
    print(f"Başarısız: {response.headers.get('X-Failed-Count')}")
    
    if response.status_code == 200:
        with open("./test_output/products_many.zip", "wb") as f:
            f.write(response.content)
        print("✓ ZIP dosyası kaydedildi: ./test_output/products_many.zip")
    else:
        print(f"Error: {response.json()}")


# Örnek 5: Hata yönetimi (Geçersiz PreState)
def test_error_handling():
    """Hata durumlarını test et"""
    print("\n" + "="*50)
    print("TEST 5: Error Handling")
    print("="*50)
    
    # Boş prestates
    print("\n--- Boş prestates ---")
    payload = {"prestates": []}
    response = requests.post(f"{BASE_URL}/api/process-products", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Error: {response.json()}")
    
    # Geçersiz format
    print("\n--- Geçersiz format ---")
    payload = {"prestates": "not_a_list"}
    response = requests.post(f"{BASE_URL}/api/process-products", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Error: {response.json()}")
    
    # Boş body
    print("\n--- Boş body ---")
    response = requests.post(f"{BASE_URL}/api/process-products", json={})
    print(f"Status Code: {response.status_code}")
    print(f"Error: {response.json()}")


if __name__ == "__main__":
    import os
    
    # Test output dizinini oluştur
    os.makedirs("./test_output", exist_ok=True)
    
    print("\n" + "="*50)
    print("FLASK API TEST SUITE")
    print("="*50)
    print("\nDikkat: Flask sunucusu çalıştığından emin olun!")
    print("Terminal'de çalıştırın: python app.py\n")
    
    try:
        # Test 1: Health Check
        test_health_check()
        time.sleep(1)
        
        # Test 2: Single Excel
        test_process_products()
        time.sleep(2)
        
        # Test 3: ZIP Format
        test_process_products_zip()
        time.sleep(2)
        
        # Test 4: Many Products
        test_many_products()
        time.sleep(2)
        
        # Test 5: Error Handling
        test_error_handling()
        
        print("\n" + "="*50)
        print("✓ Tüm testler tamamlandı!")
        print("="*50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ HATA: Flask sunucusuna bağlanılamadı!")
        print("Lütfen sunucuyu başlatın: python app.py")
    except Exception as e:
        print(f"\n❌ Test hatası: {e}")
