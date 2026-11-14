"""KasaTakip - Küçük İşletme Gelir-Gider Takip Sistemi

Kullanıcı gelir ve giderlerini girer. Program toplamları hesaplar,
raporu ekrana yazar ve .txt / .csv dosyalarına kaydeder.
"""

import csv
import math
from datetime import date

# Kategoriler bir sözlükte tutulur: tür -> kategori listesi
KATEGORILER = {
    "gelir": ["satış", "hizmet", "diğer"],
    "gider": ["kira", "fatura", "malzeme", "personel", "diğer"],
}


def kucult(metin):
    """Türkçe harflere dikkat ederek küçük harfe çevirir (İ -> i, I -> ı)."""
    return metin.replace("İ", "i").replace("I", "ı").lower()


def tutar_oku():
    """Geçerli bir tutar girilene kadar sorar (0'dan büyük olmalı)."""
    while True:
        metin = input("Tutar (TL): ").strip().replace(",", ".")
        try:
            tutar = float(metin)
        except ValueError:
            print("Uyarı: Lütfen sayı girin. Örnek: 1250,75")
            continue
        if not math.isfinite(tutar):  # "nan" ve "inf" sayı sayılmaz
            print("Uyarı: Lütfen geçerli bir sayı girin.")
        elif tutar <= 0:
            print("Uyarı: Tutar 0'dan büyük olmalı.")
        elif tutar > 10_000_000:
            print("Uyarı: Tutar en fazla 10.000.000 TL olabilir.")
        else:
            return tutar


def aciklama_oku():
    """Boş olmayan ve en fazla 30 karakterlik bir açıklama girilene kadar sorar."""
    while True:
        aciklama = input("Açıklama (en fazla 30 karakter): ").strip()
        if aciklama == "":
            print("Uyarı: Açıklama boş bırakılamaz.")
        elif len(aciklama) > 30:
            print("Uyarı: Açıklama en fazla 30 karakter olabilir.")
        else:
            return aciklama


def kategori_oku(tur):
    """Seçilen türe uygun bir kategori girilene kadar sorar."""
    secenekler = KATEGORILER[tur]
    while True:
        kategori = kucult(input(f"Kategori ({', '.join(secenekler)}): ").strip())
        if kategori in secenekler:
            return kategori
        print("Uyarı: Listede olmayan bir kategori girdiniz.")


def islem_ekle(islemler, tur):
    """Kullanıcıdan kategori, tutar ve açıklamayı alıp listeye bir işlem ekler."""
    kategori = kategori_oku(tur)
    tutar = tutar_oku()
    aciklama = aciklama_oku()
    islemler.append({"tur": tur, "kategori": kategori, "tutar": tutar, "aciklama": aciklama})
    print(f"Kaydedildi: {tur} - {kategori} - {tutar:.2f} TL")


def listele(islemler):
    """Girilen işlemleri numaralı olarak ekrana yazar."""
    if not islemler:
        print("Henüz işlem girilmedi.")
        return
    for sira, islem in enumerate(islemler, start=1):
        print(f"{sira}. {islem['tur']:<6} {islem['kategori']:<9} "
              f"{islem['tutar']:>10.2f} TL  {islem['aciklama']}")


def ozet_hesapla(islemler):
    """Toplam gelir, toplam gider ve kategori bazlı gider toplamlarını bulur."""
    gelir = 0.0
    gider = 0.0
    gider_dagilimi = {}  # kategori -> toplam gider
    for islem in islemler:
        if islem["tur"] == "gelir":
            gelir += islem["tutar"]
        else:
            gider += islem["tutar"]
            kategori = islem["kategori"]
            gider_dagilimi[kategori] = gider_dagilimi.get(kategori, 0) + islem["tutar"]
    return gelir, gider, gider_dagilimi


def rapor_olustur(tarih, gelir, gider, gider_dagilimi):
    """Raporu biçimli bir metin olarak hazırlar."""
    # Kuruşa yuvarlıyoruz: bilgisayar 0.1 + 0.2'yi tam 0.3 tutamaz,
    # yuvarlamazsak gelir ve gider eşitken "zarar var" diyebilir.
    bakiye = round(gelir - gider, 2)
    if bakiye == 0:
        bakiye = 0.0  # ekranda "-0.00" görünmesin
    satirlar = [f"KASATAKİP RAPORU - {tarih}", "-" * 40,
                f"Toplam gelir : {gelir:>12.2f} TL",
                f"Toplam gider : {gider:>12.2f} TL",
                f"Bakiye       : {bakiye:>12.2f} TL", "-" * 40]
    if gider_dagilimi:
        satirlar.append("Gider dağılımı:")
        for kategori, tutar in gider_dagilimi.items():
            yuzde = tutar / gider * 100
            satirlar.append(f"  {kategori:<9} {tutar:>10.2f} TL  (%{yuzde:.1f})")
        en_buyuk = max(gider_dagilimi, key=gider_dagilimi.get)
        satirlar.append(f"En yüksek gider kalemi: {en_buyuk}")
    if bakiye > 0:
        satirlar.append("Durum: Kâr var.")
    elif bakiye == 0:
        satirlar.append("Durum: Gelir ve gider eşit.")
    else:
        satirlar.append("Durum: Zarar var, giderler gelirden fazla!")
    return "\n".join(satirlar)


def dosyaya_kaydet(tarih, rapor, islemler):
    """Raporu .txt, tüm işlemleri .csv dosyasına yazar."""
    txt_adi = f"kasa_raporu_{tarih}.txt"
    csv_adi = f"islemler_{tarih}.csv"
    with open(txt_adi, "w", encoding="utf-8") as dosya:
        dosya.write(rapor + "\n")
    with open(csv_adi, "w", newline="", encoding="utf-8-sig") as dosya:
        yazici = csv.writer(dosya, delimiter=";")
        yazici.writerow(["Tür", "Kategori", "Tutar", "Açıklama"])
        for islem in islemler:
            yazici.writerow([islem["tur"], islem["kategori"], islem["tutar"], islem["aciklama"]])
    return txt_adi, csv_adi


def main():
    islemler = []  # tüm gelir ve giderler burada tutulur
    print("=== KasaTakip ===")
    while True:
        print("\n1) Gelir ekle\n2) Gider ekle\n3) İşlemleri listele"
              "\n4) Rapor oluştur ve kaydet\n5) Çıkış")
        secim = input("Seçiminiz: ").strip()
        if secim == "1":
            islem_ekle(islemler, "gelir")
        elif secim == "2":
            islem_ekle(islemler, "gider")
        elif secim == "3":
            listele(islemler)
        elif secim == "4":
            if not islemler:
                print("Uyarı: Önce en az bir işlem girmelisiniz.")
                continue
            tarih = date.today().isoformat()
            gelir, gider, dagilim = ozet_hesapla(islemler)
            rapor = rapor_olustur(tarih, gelir, gider, dagilim)
            print("\n" + rapor)
            txt_adi, csv_adi = dosyaya_kaydet(tarih, rapor, islemler)
            print(f"\nDosyalar kaydedildi: {txt_adi}, {csv_adi}")
        elif secim == "5":
            print("Görüşmek üzere!")
            break
        else:
            print("Uyarı: Lütfen 1-5 arasında bir seçim yapın.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):  # Ctrl+C veya Ctrl+D ile çıkış
        print("\nProgram kapatıldı.")
