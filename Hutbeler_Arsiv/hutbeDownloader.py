import os
import json
import requests
import urllib.parse
import re
from datetime import datetime

def dosya_adi_duzelt(metin):
    ceviriler = str.maketrans("ğĞıİöÖüÜşŞçÇ", "gGiIoOuUsScC")
    metin = metin.translate(ceviriler).lower()
    metin = re.sub(r'[^a-z0-9]+', '_', metin)
    return metin.strip('_')

def guncel_hutbeyi_cek():
    print("🕵️‍♂️ Ajan devrede: Kamuflaj giyildi, e-Devlet kapısına dayanıyoruz...")
    
    # 1. HAMLE: Gerçek bir tarayıcı gibi davranmak için "Oturum (Session)" başlatıyoruz
    session = requests.Session()
    
    # Kendimizi son sürüm bir Google Chrome gibi gösteren jilet gibi başlıklar (Headers)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    }
    
    try:
        # 2. HAMLE: Önce ana sayfaya gidip sistemden "Ziyaretçi Çerezi (Cookie)" alıyoruz
        ana_sayfa = "https://www.turkiye.gov.tr/diyanet-isleri-cuma-ve-bayram-hutbeleri"
        session.get(ana_sayfa, headers=headers, timeout=15)
        print("🍪 Güvenlik geçildi, ziyaretçi çerezleri cebe atıldı...")

        # 3. HAMLE: Artık elimizdeki çerezle hedef linke saldırıyoruz
        url = "https://www.turkiye.gov.tr/diyanet-isleri-cuma-ve-bayram-hutbeleri?hutbe=Indir&siraNo=0&tur=pdf&sf=&download=1"
        response = session.get(url, headers=headers, stream=True, timeout=15)
        response.raise_for_status()
        
        # Gelen verinin tipini kontrol ediyoruz. Eğer 'html' dönerse bizi Giriş (Login) sayfasına atmış demektir!
        icerik_tipi = response.headers.get('Content-Type', '')
        if 'html' in icerik_tipi.lower():
            print("❌ İptal: e-Devlet bizi Giriş (Login) sayfasına yönlendirdi! Bu link üyeliksiz dışarıya kapalı brom.")
            return

        # Sunucunun gönderdiği dosya adını alıyoruz
        content_disposition = response.headers.get('content-disposition', '')
        
        if not content_disposition:
            print("❌ Kırmızı Alarm: Çerezler işe yaramadı, sunucu PDF adını vermiyor!")
            return
            
        # Dosya adını cımbızla çek
        match = re.search(r'filename="?([^"]+)"?', content_disposition)
        if not match:
            print("❌ Hata: Dosya adı parçalanamadı.")
            return
            
        orijinal_dosya_adi = match.group(1)
        orijinal_dosya_adi = urllib.parse.unquote(orijinal_dosya_adi)
        
        try:
            orijinal_dosya_adi = orijinal_dosya_adi.encode('iso-8859-1').decode('utf-8')
        except:
            pass
        
        baslik = orijinal_dosya_adi.lower().replace(".pdf", "").replace(".doc", "").title().strip()
        print(f"✅ Hedef Hutbe Tespit Edildi: {baslik}")
        
        # --- ZAMAN VE DOSYA İŞLEMLERİ ---
        bugun = datetime.now()
        kisa_yil = bugun.strftime("%y")
        uzun_yil = bugun.strftime("%Y")
        hafta_no = bugun.isocalendar()[1]
        db_tarih = bugun.strftime("%Y-%m-%d")
        
        hutbe_id = f"{uzun_yil}_{hafta_no:02d}"
        temiz_baslik = dosya_adi_duzelt(baslik)
        yeni_dosya_adi = f"{kisa_yil}-{hafta_no:02d}-{temiz_baslik}.pdf"
        
        # JSON kontrolü
        json_dosyasi = "hutbeler.json"
        hutbeler_json = []
        if os.path.exists(json_dosyasi):
            with open(json_dosyasi, 'r', encoding='utf-8') as f:
                hutbeler_json = json.load(f)
                
        for h in hutbeler_json:
            if h.get("id") == hutbe_id:
                print(f"⚠️ Kalkan Devrede: '{baslik}' ({hutbe_id}) zaten arşivimizde var. Pas geçiliyor.")
                return
        
        # Kayıt İşlemleri
        hedef_klasor = "Hutbeler_Arsiv"
        yil_klasoru = os.path.join(hedef_klasor, uzun_yil)
        os.makedirs(yil_klasoru, exist_ok=True)
        hedef_yol = os.path.join(yil_klasoru, yeni_dosya_adi)
        
        print(f"📥 PDF indiriliyor -> {yeni_dosya_adi}")
        with open(hedef_yol, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"✅ Dosya arşive kilitlendi!")
        
        cdn_link = f"https://cdn.jsdelivr.net/gh/umitturkmen/islamic-superapp-data@main/{hedef_klasor}/{uzun_yil}/{yeni_dosya_adi}"
        
        yeni_kayit = {
            "id": hutbe_id,
            "title": baslik,
            "date": db_tarih,
            "year": int(uzun_yil),
            "week": hafta_no,
            "file_name": yeni_dosya_adi,
            "status": "Kopyalandi",
            "link": cdn_link
        }
        
        hutbeler_json.insert(0, yeni_kayit)
        with open(json_dosyasi, 'w', encoding='utf-8') as f:
            json.dump(hutbeler_json, f, ensure_ascii=False, indent=2)
            
        print(f"🎉 Görev Şahane! Yeni hutbe sisteme entegre edildi.")
        
    except Exception as e:
        print(f"❌ Kırmızı Alarm! Bir hata oluştu: {e}")

if __name__ == "__main__":
    guncel_hutbeyi_cek()