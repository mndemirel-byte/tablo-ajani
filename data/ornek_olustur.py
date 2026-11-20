"""Örnek çalışma kitabını üretir: data/kuzey_elektronik.xlsx

Kurgusal bir şirketin (Kuzey Elektronik) gelir ve gider tabloları.
Bilerek iki kusur bırakılır: Gider sayfasında metin olarak girilmiş bir sayı
ve Ozet sayfasında bozuk bir referans (#REF!). Doğrulama adımı bunları yakalamalıdır.
"""
from pathlib import Path
from openpyxl import Workbook

HEDEF = Path(__file__).parent / "kuzey_elektronik.xlsx"


def olustur() -> Path:
    wb = Workbook()
    gelir = wb.active
    gelir.title = "Gelir"
    gelir.append(["Ürün hattı", "2024", "2025", "2026"])
    for satir in [
        ["Akıllı priz", 1_250_000, 1_610_000, 2_040_000],
        ["Termostat", 980_000, 1_120_000, 1_395_000],
        ["Kapı sensörü", 410_000, 455_000, 530_000],
        ["Sesli asistan modülü", 0, 320_000, 905_000],
    ]:
        gelir.append(satir)

    gider = wb.create_sheet("Gider")
    gider.append(["Kalem", "2024", "2025", "2026"])
    for satir in [
        ["Üretim (fason)", 1_310_000, 1_590_000, 2_120_000],
        ["Personel", 640_000, 780_000, 910_000],
        ["Pazarlama", 150_000, "210.000", 260_000],  # kusur: metin olarak sayı
        ["Bulut ve lisans", 45_000, 62_000, 88_000],
    ]:
        gider.append(satir)

    ozet = wb.create_sheet("Ozet")
    ozet.append(["Gösterge", "2024", "2025", "2026"])
    ozet.append(["Toplam gelir", "=SUM(Gelir!B2:B5)", "=SUM(Gelir!C2:C5)", "=SUM(Gelir!D2:D5)"])
    ozet.append(["Toplam gider", "=SUM(Gider!B2:B5)", "=SUM(Gider!C2:C5)", "=#REF!"])  # kusur
    wb.save(HEDEF)
    return HEDEF


if __name__ == "__main__":
    print(olustur())
