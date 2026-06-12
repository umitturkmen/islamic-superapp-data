import os
import json
import requests
import urllib.parse
import re
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def dosya_adi_duzelt(metin):
    ceviriler = str.maketrans("ğĞıİöÖüÜşŞçÇ", "gGiIoOuUsScC")
    metin = metin.translate(ceviriler).lower()
    metin = re.sub(r'[^a-z0-9]+', '_', metin)
    return metin.strip('_')

def guncel_hutbeyi_cek():
    print("🕵️‍♂️ Ajan devrede: Kamuflaj giyildi, e-Devlet kapısına dayanıyoruz...")
    
    # SENIOR DOKUNUŞU: Bağlantı koparsa pes etme, 5 kez yeniden dene!
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=2, status_forcelist=[ 500, 502, 503, 504 ])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive'
    }
    
    try:
        ana_sayfa = "https://www.turkiye.gov.tr/diyanet-isleri-cuma-ve-bayram-hutbeleri"
        session.get(ana_sayfa, headers=headers, timeout=20)
        print("🍪 Ziyaretçi çerezleri cebe atıldı...")

        url = "https://www.turkiye.gov.tr/diyanet-isleri-cuma-ve-bayram-hutbeleri?hutbe=Indir&siraNo=0&tur=pdf&sf=&download=1"
        response = session.get(url, headers=headers, stream=True, timeout=20)
        response.raise_for_status()
        
        icerik_tipi = response.headers.get('Content-Type', '')
        if 'html' in icerik_tipi.lower():
            print("❌ İptal: e-Devlet Giriş (Login) sayfasına yönlendirdi!")
            return

        content_disposition = response.headers.get('content-disposition', '')
        if not content_disposition:
            print("❌ Kırmızı Alarm: Sunucu PDF adını vermiyor!")
            return
            
        match = re.search(r'filename="?([^"]+)"?', content_disposition)
        if not match: return
            
        orijinal_dosya_adi = urllib.parse.unquote(match.group(1))
        try: orijinal_dosya_adi = orijinal_dosya_adi.encode('iso-8859-1').decode('utf-8')
        except: pass
        
        baslik = orijinal_dosya_adi.lower().replace(".pdf", "").replace(".doc", "").title().strip()
        print(f"✅ Hedef Hutbe Tespit Edildi: {baslik}")
        
        bugun = datetime.now()
        kisa_yil = bugun.strftime("%y")
        uzun_yil = bugun.strftime("%Y")
        hafta_no = bugun.isocalendar()[1]
        db_tarih = bugun.strftime("%Y-%m-%d")
        
        hutbe_id = f"{uzun_yil}_{hafta_no:02d}"
        yeni_dosya_adi = f"{kisa_yil}-{hafta_no:02d}-{dosya_adi_duzelt(baslik)}.pdf"
        
        json_dosyasi = "Hutbeler_Arsiv/hutbeler.json"
        hutbeler_json = []
        if os.path.exists(json_dosyasi):
            with open(json_dosyasi, 'r', encoding='utf-8') as f:
                hutbeler_json = json.load(f)
                
        for h in hutbeler_json:
            if h.get("id") == hutbe_id:
                print(f"⚠️ Kalkan Devrede: '{baslik}' zaten arşivimizde var. Pas geçiliyor.")
                return
        
        yil_klasoru = os.path.join("Hutbeler_Arsiv", uzun_yil)
        os.makedirs(yil_klasoru, exist_ok=True)
        hedef_yol = os.path.join(yil_klasoru, yeni_dosya_adi)
        
        print(f"📥 PDF indiriliyor -> {yeni_dosya_adi}")
        with open(hedef_yol, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
                
        cdn_link = f"https://cdn.jsdelivr.net/gh/umitturkmen/islamic-superapp-data@main/Hutbeler_Arsiv/{uzun_yil}/{yeni_dosya_adi}"
        
        hutbeler_json.insert(0, {
            "id": hutbe_id, "title": baslik, "date": db_tarih, "year": int(uzun_yil),
            "week": hafta_no, "file_name": yeni_dosya_adi, "status": "Kopyalandi", "link": cdn_link
        })
        
        with open(json_dosyasi, 'w', encoding='utf-8') as f:
            json.dump(hutbeler_json, f, ensure_ascii=False, indent=2)
            
        print(f"🎉 Görev Şahane! Yeni hutbe sisteme entegre edildi.")
        
    except Exception as e:
        print(f"❌ Kırmızı Alarm! Bir hata oluştu: {e}")

if __name__ == "__main__":
    guncel_hutbeyi_cek()