"""SQLite veritabanında salt-okunur sorgu çalıştırır, sonucu JSON döndürür.

Veritabanı 'mode=ro' ile açılır: agent bu yoldan veriyi değiştiremez.
Kullanım: python scripts/sql.py work/kitap.db 'SELECT * FROM Gelir LIMIT 5'
"""
import argparse
import json
import sqlite3

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("db")
    p.add_argument("sorgu")
    a = p.parse_args()
    con = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    imlec = con.execute(a.sorgu)
    kolonlar = [d[0] for d in imlec.description or []]
    print(json.dumps([dict(zip(kolonlar, r)) for r in imlec.fetchall()], ensure_ascii=False, indent=2))
    from _kayit import kaydet
    kaydet("sql", a.sorgu)
