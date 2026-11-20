"""Agent'ın tabloya yazdığı TEK yol: hucre_yaz ve geri_al araçları.

Okuma ve arama bash + scripts/ üzerinden serbesttir. Yazma ise atomik,
denetlenebilir ve geri alınabilir olmalıdır; bu yüzden tool olarak tanımlanır.
Akış: kontrol noktası → yazma → deterministik doğrulama → kabul ya da otomatik geri alma.
Bir yazma tabloya YENİ bir sorun sokuyorsa (dogrula.py ölçütüyle) geri alınır ve agent'a
hata döner. Var olan sorunlar yazmayı engellemez; yoksa bozuk bir tablo hiç düzeltilemezdi.
"""
import shutil
import time
from pathlib import Path

from claude_agent_sdk import create_sdk_mcp_server, tool
from openpyxl import load_workbook

from scripts.dogrula import dogrula

KOK = Path(__file__).resolve().parent
YEDEKLER = KOK / "work" / "yedekler"
AZAMI_HUCRE = 50  # tek çağrıda yazılabilecek hücre sayısı; aşılırsa agent'a geri bildirim


def _yanit(metin: str, hata: bool = False) -> dict:
    sonuc = {"content": [{"type": "text", "text": metin}]}
    if hata:
        sonuc["is_error"] = True
    return sonuc


def _guvenli_yol(dosya: str) -> Path:
    yol = (KOK / dosya).resolve()
    if KOK / "data" not in yol.parents or yol.suffix != ".xlsx":
        raise ValueError("Yalnızca data/ altındaki .xlsx dosyalarına yazılabilir.")
    return yol


async def hucre_yaz_isle(args: dict) -> dict:
    try:
        yol = _guvenli_yol(args["dosya"])
    except ValueError as e:
        return _yanit(f"Hata: {e}", hata=True)
    degisiklikler = args["degisiklikler"]
    if len(degisiklikler) > AZAMI_HUCRE:
        return _yanit(f"Hata: tek çağrıda en fazla {AZAMI_HUCRE} hücre yazılabilir; "
                      f"{len(degisiklikler)} istendi. Değişiklikleri parçalara böl.", hata=True)
    wb = load_workbook(yol)
    for d in degisiklikler:
        sayfa, hucre = d["hucre"].split("!", 1)
        if sayfa not in wb.sheetnames:
            return _yanit(f"Hata: '{sayfa}' sayfası yok. Hiçbir hücre yazılmadı.", hata=True)
    onceki = _sorun_kumesi(yol)
    YEDEKLER.mkdir(parents=True, exist_ok=True)
    yedek = YEDEKLER / f"{yol.stem}-{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns() % 10**6}.xlsx"
    shutil.copy2(yol, yedek)                      # 1. kontrol noktası
    for d in degisiklikler:                       # 2. yazma
        sayfa, hucre = d["hucre"].split("!", 1)
        wb[sayfa][hucre] = d["deger"]
    wb.save(yol)
    yeni = sorted(_sorun_kumesi(yol) - onceki)    # 3. doğrulama
    if yeni:                                      # 4a. geri alma
        shutil.copy2(yedek, yol)
        yedek.unlink()
        return _yanit("Hata: bu yazma tabloya yeni sorun soktuğu için GERİ ALINDI. Hiçbir hücre değişmedi. "
                      f"Yeni sorunlar: {[f'{h} ({t})' for h, t in yeni]}", hata=True)
    return _yanit(f"{len(degisiklikler)} hücre yazıldı. Kontrol noktası: {yedek.relative_to(KOK)}")  # 4b. kabul


def _sorun_kumesi(yol: Path) -> set[tuple[str, str]]:
    return {(s["hucre"], s["tur"]) for s in dogrula(str(yol))}


async def geri_al_isle(args: dict) -> dict:
    try:
        yol = _guvenli_yol(args["dosya"])
    except ValueError as e:
        return _yanit(f"Hata: {e}", hata=True)
    adaylar = sorted(YEDEKLER.glob(f"{yol.stem}-*.xlsx"))
    if not adaylar:
        return _yanit("Geri alınacak kontrol noktası yok.", hata=True)
    son = adaylar[-1]
    shutil.copy2(son, yol)
    son.unlink()
    return _yanit(f"{yol.name}, {son.name} kontrol noktasına geri döndürüldü.")


HUCRE_YAZ_SEMA = {
    "type": "object",
    "properties": {
        "dosya": {"type": "string", "description": "Proje köküne göre yol, ör. data/kuzey_elektronik.xlsx"},
        "degisiklikler": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hucre": {"type": "string", "description": "A1 gösterimi, ör. Gider!C4"},
                    "deger": {"description": "Sayı, metin ya da '=' ile başlayan formül"},
                },
                "required": ["hucre", "deger"],
            },
        },
    },
    "required": ["dosya", "degisiklikler"],
}

hucre_yaz = tool(
    "hucre_yaz",
    "Çalışma kitabına hücre değerleri yazar. Tabloyu değiştirmenin tek yoludur. "
    "Yazmadan önce kontrol noktası alır; yazma yeni bir doğrulama sorunu yaratırsa otomatik geri alınır. "
    "Kabul edilen bir yazma geri_al ile geri döndürülebilir.",
    HUCRE_YAZ_SEMA,
)(hucre_yaz_isle)

geri_al = tool(
    "geri_al",
    "Çalışma kitabını son kontrol noktasına geri döndürür.",
    {"type": "object", "properties": {"dosya": {"type": "string"}}, "required": ["dosya"]},
)(geri_al_isle)

tablo_sunucusu = create_sdk_mcp_server(name="tablo", version="1.0.0", tools=[hucre_yaz, geri_al])
