"""Test senaryoları: programı gerçekten çalıştırır, sonucu beklenenle karşılaştırır.

Çalıştırma:  python test_kasatakip.py
"""
import builtins, contextlib, io, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kasatakip

KOD_DOSYASI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kasatakip.py")


def calistir(girdiler):
    """Programı sahte klavye girdileriyle çalıştırır; çıktıyı ve dosyaları döndürür."""
    sira = iter(girdiler)
    cikti = io.StringIO()

    def sahte_input(soru=""):
        cikti.write(soru)
        cevap = next(sira)
        cikti.write(cevap + "\n")
        return cevap

    eski_input, eski_klasor = builtins.input, os.getcwd()
    gecici = tempfile.mkdtemp()
    builtins.input = sahte_input
    os.chdir(gecici)
    try:
        with contextlib.redirect_stdout(cikti):
            kasatakip.main()
        dosyalar = sorted(os.listdir(gecici))
        icerik = {d: open(d, encoding="utf-8-sig").read() for d in dosyalar}
    finally:
        builtins.input = eski_input
        os.chdir(eski_klasor)
    return cikti.getvalue(), icerik


def deger(cikti, baslik):
    """Rapordaki 'Toplam gelir : 5000.00 TL' gibi bir satırın sayısını verir."""
    for satir in cikti.splitlines():
        if satir.startswith(baslik):
            return satir.split(":")[1].replace("TL", "").strip()


def uyarilar(cikti):
    return [s for s in cikti.splitlines() if s.startswith("Uyarı")]


# (ad, girdiler, beklenen, kontrol, gerçek)
# Her işlemde sırayla: kategori, tutar, açıklama girilir.
SENARYOLAR = [
    ("Normal: gelir 5000, kira 2000, fatura 500",
     ["1", "satış", "5000", "Günlük satış", "2", "kira", "2000", "Kasım kirası",
      "2", "fatura", "500", "Elektrik", "4", "5"],
     "Gelir 5000.00; gider 2500.00; bakiye 2500.00; 2 dosya",
     lambda o, d: (deger(o, "Toplam gelir"), deger(o, "Toplam gider"), deger(o, "Bakiye"), len(d))
                  == ("5000.00", "2500.00", "2500.00", 2),
     lambda o, d: f"Gelir {deger(o,'Toplam gelir')}; gider {deger(o,'Toplam gider')}; "
                  f"bakiye {deger(o,'Bakiye')}; {len(d)} dosya"),

    ("Virgüllü tutar: 1250,75",
     ["1", "hizmet", "1250,75", "Danışmanlık", "4", "5"],
     "Uyarı yok; gelir 1250.75",
     lambda o, d: not uyarilar(o) and deger(o, "Toplam gelir") == "1250.75",
     lambda o, d: f"{len(uyarilar(o))} uyarı; gelir {deger(o,'Toplam gelir')}"),

    ("HATALI: tutar yerine abc",
     ["1", "satış", "abc", "100", "Satış", "5"],
     "1 uyarı, çökmez; sonra 100 kabul",
     lambda o, d: len(uyarilar(o)) == 1 and "gelir - satış - 100.00 TL" in o,
     lambda o, d: f"{len(uyarilar(o))} uyarı; 100.00 kaydedildi"),

    ("UÇ: tutar 0 ve -50",
     ["2", "kira", "0", "-50", "300", "Depo kirası", "5"],
     "2 uyarı; 300 kabul",
     lambda o, d: len(uyarilar(o)) == 2 and "gider - kira - 300.00 TL" in o,
     lambda o, d: f"{len(uyarilar(o))} uyarı; 300.00 kaydedildi"),

    ("UÇ: tutar nan ve inf",
     ["1", "satış", "nan", "inf", "200", "Satış", "5"],
     "2 uyarı; 200 kabul",
     lambda o, d: len(uyarilar(o)) == 2 and "gelir - satış - 200.00 TL" in o,
     lambda o, d: f"{len(uyarilar(o))} uyarı; 200.00 kaydedildi"),

    ("HATALI: gider için 'satış' kategorisi",
     ["2", "satış", "kira", "100", "Kira", "5"],
     "1 uyarı; 'kira' kabul",
     lambda o, d: len(uyarilar(o)) == 1 and "gider - kira - 100.00 TL" in o,
     lambda o, d: f"{len(uyarilar(o))} uyarı; 'kira' kabul edildi"),

    ("Türkçe büyük harf: KİRA",
     ["2", "KİRA", "400", "Kira", "5"],
     "Uyarı yok; 'kira' olarak tanınır",
     lambda o, d: not uyarilar(o) and "gider - kira - 400.00 TL" in o,
     lambda o, d: f"{len(uyarilar(o))} uyarı; 'kira' olarak tanındı"),

    ("UÇ: açıklama boş ve 31 karakter",
     ["1", "satış", "100", "", "a" * 31, "Satış", "5"],
     "2 uyarı; 'Satış' kabul",
     lambda o, d: len(uyarilar(o)) == 2 and "gelir - satış - 100.00 TL" in o,
     lambda o, d: f"{len(uyarilar(o))} uyarı; açıklama kabul edildi"),

    ("Aynı kategori iki kez: kira 1000 + 500",
     ["1", "satış", "9000", "Satış", "2", "kira", "1000", "Dükkan", "2", "kira", "500", "Depo", "4", "5"],
     "Dağılımda tek satır: kira 1500.00 (%100.0)",
     lambda o, d: "1500.00 TL  (%100.0)" in o and "En yüksek gider kalemi: kira" in o,
     lambda o, d: "kira 1500.00 (%100.0); en yüksek kalem kira"),

    ("Zarar: gelir 1000, gider 3000",
     ["1", "satış", "1000", "Satış", "2", "malzeme", "3000", "Toptan alım", "4", "5"],
     "Bakiye -2000.00; 'Zarar var'",
     lambda o, d: deger(o, "Bakiye") == "-2000.00" and "Zarar var" in o,
     lambda o, d: f"Bakiye {deger(o,'Bakiye')}; 'Zarar var' yazdı"),

    ("UÇ: gelir 0,3; gider 0,1 + 0,2",
     ["1", "satış", "0,3", "Satış", "2", "kira", "0,1", "Kira", "2", "fatura", "0,2", "Su", "4", "5"],
     "Bakiye 0.00; 'Gelir ve gider eşit'",
     lambda o, d: deger(o, "Bakiye") == "0.00" and "eşit" in o,
     lambda o, d: f"Bakiye {deger(o,'Bakiye')}; " + ("'eşit' yazdı" if "eşit" in o else "'Zarar var' yazdı")),

    ("HATALI: işlem girmeden rapor",
     ["4", "5"],
     "1 uyarı; dosya oluşmaz",
     lambda o, d: len(uyarilar(o)) == 1 and len(d) == 0,
     lambda o, d: f"{len(uyarilar(o))} uyarı; {len(d)} dosya"),

    ("HATALI: menü seçimi 9",
     ["9", "5"],
     "1 uyarı; menü tekrar gelir",
     lambda o, d: len(uyarilar(o)) == 1 and o.count("Seçiminiz:") == 2,
     lambda o, d: f"{len(uyarilar(o))} uyarı; menü tekrar geldi"),
]


def ctrl_d_testi():
    """Girdi aniden kesilirse (Ctrl+D) program hata dökmeden kapanmalı."""
    ortam = dict(os.environ, PYTHONIOENCODING="utf-8")  # Windows'ta Türkçe karakterler bozulmasın
    sonuc = subprocess.run([sys.executable, KOD_DOSYASI], input="1\n", env=ortam,
                           capture_output=True, text=True, encoding="utf-8")
    ok = sonuc.returncode == 0 and "Program kapatıldı" in sonuc.stdout and "Traceback" not in sonuc.stderr
    return {"ad": "UÇ: girdi yarıda kesilir (Ctrl+D)", "girdi": "1 | (girdi biter)",
            "beklenen": "Hata dökmeden 'Program kapatıldı'",
            "gercek": "'Program kapatıldı' yazdı" if ok else "Traceback ile çöktü", "gecti": ok}


def main():
    sonuclar = []
    for ad, girdiler, beklenen, kontrol, gercek in SENARYOLAR:
        cikti, dosyalar = calistir(girdiler)
        sonuclar.append({"ad": ad, "girdi": " | ".join(girdiler), "beklenen": beklenen,
                         "gercek": gercek(cikti, dosyalar), "gecti": bool(kontrol(cikti, dosyalar))})
    sonuclar.append(ctrl_d_testi())
    return sonuclar


if __name__ == "__main__":
    sonuclar = main()
    for s in sonuclar:
        print("GEÇTİ" if s["gecti"] else "KALDI", "-", s["ad"], "->", s["gercek"])
    print(f"\n{sum(s['gecti'] for s in sonuclar)}/{len(sonuclar)} test geçti")
    sys.exit(0 if all(s["gecti"] for s in sonuclar) else 1)
