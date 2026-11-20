"""Çalışma kitabının haritasını çıkarır: sayfalar, boyutlar, başlık satırı, ilk satırlar.

Agent'ın bağlam toplamaya başladığı yer burasıdır. Tüm tabloyu değil,
yalnızca bir insanın dosyayı ilk açtığında gördüğü kadarını döndürür.

Kullanım: python scripts/sayfa_bilgisi.py data/kuzey_elektronik.xlsx [--satir 5]
"""
import argparse
import json

from openpyxl import load_workbook


def harita(yol: str, satir: int = 5) -> dict:
    wb = load_workbook(yol, data_only=False)
    sonuc = {"dosya": yol, "sayfalar": []}
    for ws in wb.worksheets:
        ilk = [[c.value for c in r] for r in ws.iter_rows(min_row=1, max_row=min(ws.max_row, satir))]
        sonuc["sayfalar"].append({
            "ad": ws.title,
            "boyut": ws.dimensions,
            "satir_sayisi": ws.max_row,
            "sutun_sayisi": ws.max_column,
            "baslik": ilk[0] if ilk else [],
            "ilk_satirlar": ilk[1:],
        })
    return sonuc


if __name__ == "__main__":
    from _kayit import kaydet, utf8_cikti
    utf8_cikti()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("dosya")
    p.add_argument("--satir", type=int, default=5, help="Her sayfadan kaç satır gösterilsin")
    a = p.parse_args()
    print(json.dumps(harita(a.dosya, a.satir), ensure_ascii=False, indent=2, default=str))
    kaydet("sayfa_bilgisi", a.dosya)
