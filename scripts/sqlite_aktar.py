"""Çalışma kitabını SQLite'a aktarır: her sayfa bir tablo, başlık satırı sütun adı.

Model SQL'i çok iyi bilir. Tabloyu SQL ile sorgulanabilir hâle getirmek,
çok boyutlu soruları ("2026'da gelir") tek bir sorguya indirir.

Dönüşüm kayıplıdır: formüller ve metin olarak girilmiş sayılar SQLite'a metin olarak
gider. Betik bu hücreleri listeleyip uyarır; SQL bir keşif arayüzüdür, tek doğruluk
kaynağı asıl XLSX dosyasıdır.

Kullanım:
  python scripts/sqlite_aktar.py data/kuzey_elektronik.xlsx work/kitap.db
  python scripts/sql.py work/kitap.db 'SELECT "Ürün hattı", "2026" FROM Gelir ORDER BY "2026" DESC'
"""
import argparse
import sqlite3

from openpyxl import load_workbook


def aktar(xlsx: str, db: str) -> tuple[list[str], list[str]]:
    wb = load_workbook(xlsx, data_only=False)
    con = sqlite3.connect(db)
    tablolar, supheli = [], []
    for ws in wb.worksheets:
        satirlar = list(ws.iter_rows(values_only=True))
        if not satirlar:
            continue
        basliklar = [str(b) for b in satirlar[0]]
        kolonlar = ", ".join(f'"{b}"' for b in basliklar)
        con.execute(f'DROP TABLE IF EXISTS "{ws.title}"')
        con.execute(f'CREATE TABLE "{ws.title}" ({kolonlar})')
        yer = ", ".join("?" for _ in basliklar)
        con.executemany(f'INSERT INTO "{ws.title}" VALUES ({yer})',
                        [tuple(r[:len(basliklar)]) for r in satirlar[1:]])
        tablolar.append(ws.title)
        for satir in ws.iter_rows(min_row=2):
            for h in satir:
                if isinstance(h.value, str) and basliklar[h.column - 1].isdigit():
                    supheli.append(f"{ws.title}!{h.coordinate}")
    con.commit()
    con.close()
    return tablolar, supheli


if __name__ == "__main__":
    from _kayit import utf8_cikti
    utf8_cikti()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("xlsx")
    p.add_argument("db")
    a = p.parse_args()
    tablolar, supheli = aktar(a.xlsx, a.db)
    print("Aktarılan tablolar:", ", ".join(tablolar))
    if supheli:
        print("UYARI: sayısal sütunlarda metin ya da formül olarak aktarılan hücreler var:", ", ".join(supheli))
        print("SQLite bunları sayıya zorlar (\"210.000\" -> 210.0, \"=SUM(...)\" -> 0); SUM/AVG sonuçları "
              "yanıltıcı olabilir. Bu hücreleri aralik_oku.py ile ayrıca kontrol et.")
