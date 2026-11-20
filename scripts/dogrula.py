"""Deterministik doğrulama: model yargısından önce kurallar.

Kontroller:
  1. Hata değerleri (#REF!, #DIV/0!, #VALUE!, #NAME?, #N/A) içeren hücreler
  2. Başlığı yıl olan (sayısal) sütunlarda metin olarak girilmiş değerler
  3. Formüllerde var olmayan bir sayfaya yapılan referanslar

Çıkış kodu: sorun yoksa 0, varsa 1. Çıktı JSON'dur; agent okuyup düzeltir.

Sınır: openpyxl bir hesaplama motoru değildir. Formüller metin olarak okunur, sonuçları
hesaplanmaz; bu betik "=A1/B1" formülünün #DIV/0! üreteceğini göremez. Yalnızca hücreye
yazılmış hata değerlerini ve yapısal kusurları yakalar.
Kullanım: python scripts/dogrula.py data/kuzey_elektronik.xlsx
"""
import argparse
import json
import re
import sys

from openpyxl import load_workbook

HATALAR = ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A")
SAYFA_REF = re.compile(r"([A-Za-zÇĞİÖŞÜçğıöşü_][\wÇĞİÖŞÜçğıöşü]*)!")


def dogrula(yol: str) -> list[dict]:
    wb = load_workbook(yol, data_only=False)
    sorunlar = []
    for ws in wb.worksheets:
        basliklar = [c.value for c in ws[1]]
        for satir in ws.iter_rows(min_row=2):
            for h in satir:
                v, yer = h.value, f"{ws.title}!{h.coordinate}"
                if isinstance(v, str) and any(e in v for e in HATALAR):
                    sorunlar.append({"hucre": yer, "tur": "hata_degeri", "deger": v})
                elif isinstance(v, str) and v.startswith("="):
                    for ref in SAYFA_REF.findall(v):
                        if ref not in wb.sheetnames:
                            sorunlar.append({"hucre": yer, "tur": "olmayan_sayfa", "deger": v})
                elif isinstance(v, str) and str(basliklar[h.column - 1] or "").isdigit():
                    sorunlar.append({"hucre": yer, "tur": "metin_olarak_sayi", "deger": v})
    return sorunlar


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("dosya")
    a = p.parse_args()
    s = dogrula(a.dosya)
    print(json.dumps({"sorun_sayisi": len(s), "sorunlar": s}, ensure_ascii=False, indent=2))
    from _kayit import kaydet
    kaydet("dogrula", a.dosya)
    sys.exit(1 if s else 0)
