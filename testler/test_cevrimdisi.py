"""API anahtarı gerektirmeyen testler: betikler, araçlar ve hook'lar.

Agent'ın modelle konuşan kısmını değil, runtime'a verdiğimiz parçaları sınar.
Çalıştırma: python testler/test_cevrimdisi.py
"""
import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))

from araclar import geri_al_isle, hucre_yaz_isle  # noqa: E402
from agent import secenekler  # noqa: E402
from kancalar import Kancalar  # noqa: E402
from openpyxl import load_workbook  # noqa: E402

DOSYA = "data/kuzey_elektronik.xlsx"


def calistir(*arg):
    return subprocess.run([sys.executable, *arg], cwd=KOK, capture_output=True, text=True)


def test_betikler():
    assert calistir("data/ornek_olustur.py").returncode == 0
    harita = json.loads(calistir("scripts/sayfa_bilgisi.py", DOSYA).stdout)
    assert [s["ad"] for s in harita["sayfalar"]] == ["Gelir", "Gider", "Ozet"]
    assert json.loads(calistir("scripts/aralik_oku.py", DOSYA, "Gelir!D5").stdout)["degerler"] == [[905000]]
    aktarim = calistir("scripts/sqlite_aktar.py", DOSYA, "work/kitap.db")
    assert aktarim.returncode == 0 and "UYARI" in aktarim.stdout and "Gider!C4" in aktarim.stdout
    # SQLite'ın sessiz hatası: "210.000" metni 210.0 olarak toplanır (doğrusu 2.642.000)
    yanlis = json.loads(calistir("scripts/sql.py", "work/kitap.db", 'SELECT SUM("2025") AS t FROM Gider').stdout)
    assert yanlis == [{"t": 2432210.0}]
    satir = json.loads(calistir("scripts/sql.py", "work/kitap.db",
                                'SELECT SUM("2026") AS t FROM Gelir').stdout)
    assert satir == [{"t": 4870000}]
    assert calistir("scripts/sql.py", "work/kitap.db", "DELETE FROM Gelir").returncode != 0  # salt okunur
    d = calistir("scripts/dogrula.py", DOSYA)
    assert d.returncode == 1 and json.loads(d.stdout)["sorun_sayisi"] == 2


async def test_araclar():
    shutil.rmtree(KOK / "work" / "yedekler", ignore_errors=True)
    r = await hucre_yaz_isle({"dosya": DOSYA, "degisiklikler": [
        {"hucre": "Gider!C4", "deger": 210000}, {"hucre": "Ozet!D3", "deger": "=SUM(Gider!D2:D5)"}]})
    assert "is_error" not in r, r
    assert calistir("scripts/dogrula.py", DOSYA).returncode == 0
    assert (await hucre_yaz_isle({"dosya": "agent.py", "degisiklikler": []}))["is_error"]
    cok = [{"hucre": f"Gelir!E{i}", "deger": 1} for i in range(51)]
    assert "parçalara böl" in (await hucre_yaz_isle({"dosya": DOSYA, "degisiklikler": cok}))["content"][0]["text"]
    # yeni sorun sokan yazma otomatik geri alınır: dosya değişmez, kontrol noktası kalmaz
    onceki_yedek = len(list((KOK / "work" / "yedekler").glob("*.xlsx")))
    kotu = await hucre_yaz_isle({"dosya": DOSYA, "degisiklikler": [
        {"hucre": "Gelir!B2", "deger": "bir milyon"}, {"hucre": "Gelir!C2", "deger": 1}]})
    assert kotu.get("is_error") and "GERİ ALINDI" in kotu["content"][0]["text"]
    gelir = load_workbook(KOK / DOSYA)["Gelir"]
    assert gelir["B2"].value == 1250000 and gelir["C2"].value == 1610000
    assert len(list((KOK / "work" / "yedekler").glob("*.xlsx"))) == onceki_yedek
    assert "is_error" not in await geri_al_isle({"dosya": DOSYA})
    assert load_workbook(KOK / DOSYA)["Gider"]["C4"].value == "210.000"


async def test_kancalar():
    k = Kancalar()
    red = await k.xlsx_koruma({"tool_name": "Bash", "tool_input": {"command": "rm data/kuzey_elektronik.xlsx"}}, None, None)
    assert red["hookSpecificOutput"]["permissionDecision"] == "deny"
    izin = await k.xlsx_koruma({"tool_name": "Bash", "tool_input": {
        "command": "python scripts/aralik_oku.py data/kuzey_elektronik.xlsx 'Gelir!A1:B2'"}}, None, None)
    assert izin == {}
    dur = {"session_id": "s1", "stop_hook_active": False}
    k.yeni_istek()
    assert (await k.kanitsiz_cevap(dur, None, None))["decision"] == "block"      # veriye bakılmadı
    assert await k.kanitsiz_cevap({**dur, "stop_hook_active": True}, None, None) == {}  # sonsuz döngü yok
    assert calistir("scripts/aralik_oku.py", DOSYA, "Olmayan!A1").returncode != 0
    assert (await k.kanitsiz_cevap(dur, None, None))["decision"] == "block"      # başarısız betik kanıt değil
    assert calistir("scripts/aralik_oku.py", DOSYA, "Gelir!D5").returncode == 0
    assert await k.kanitsiz_cevap(dur, None, None) == {}                         # başarılı erişim: geçer
    k.yeni_istek()                                                               # ikinci soru
    assert (await k.kanitsiz_cevap(dur, None, None))["decision"] == "block"      # kanıt isteğe özgü
    baglam = await k.yazim_sonrasi({"tool_input": {"dosya": DOSYA}}, None, None)
    assert "SORUN VAR" in baglam["hookSpecificOutput"]["additionalContext"]


def test_secenekler():
    o = secenekler(Kancalar())
    assert set(o.hooks) == {"PreToolUse", "PostToolUse", "Stop"} and "denetci" in o.agents


if __name__ == "__main__":
    test_betikler()
    asyncio.run(test_araclar())
    asyncio.run(test_kancalar())
    test_secenekler()
    print("Tüm çevrimdışı testler geçti.")
