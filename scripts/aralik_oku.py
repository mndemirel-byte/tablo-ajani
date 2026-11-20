"""A1 gösterimiyle bir aralığı okur: 'Gelir!B2:D5'.

Model bu sözdizimini Excel/Sheets formüllerinden tanır; arayüzü ona yabancı
olmayan bir dile çevirmek, agentic arama tasarımının çekirdeğidir.

Kullanım: python scripts/aralik_oku.py data/kuzey_elektronik.xlsx "Gelir!B2:D5"
"""
import argparse
import json

from openpyxl import load_workbook


def oku(yol: str, aralik: str) -> dict:
    if "!" not in aralik:
        raise SystemExit("Hata: aralık 'Sayfa!A1:B2' biçiminde olmalı.")
    sayfa, hucreler = aralik.split("!", 1)
    wb = load_workbook(yol, data_only=False)
    if sayfa not in wb.sheetnames:
        raise SystemExit(f"Hata: '{sayfa}' sayfası yok. Mevcut sayfalar: {wb.sheetnames}")
    secim = wb[sayfa][hucreler]
    if not isinstance(secim, tuple):          # tek hücre
        secim = ((secim,),)
    elif secim and not isinstance(secim[0], tuple):  # tek satır/sütun
        secim = (secim,)
    return {"aralik": aralik, "degerler": [[c.value for c in r] for r in secim]}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("dosya")
    p.add_argument("aralik")
    a = p.parse_args()
    print(json.dumps(oku(a.dosya, a.aralik), ensure_ascii=False, indent=2, default=str))
    from _kayit import kaydet
    kaydet("aralik_oku", f"{a.dosya} {a.aralik}")
