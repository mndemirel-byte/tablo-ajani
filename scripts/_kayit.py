"""Erişim kaydı: okuma betikleri başarıyla bittiğinde work/erisim.jsonl dosyasına bir satır ekler.

Stop hook'u (kancalar.py) bu kayda bakar: son kullanıcı isteğinden beri hiç başarılı
veri erişimi yoksa cevabı bir kez geri çevirir. Kayıt betiğin SONUNDA yazılır; hata
verip çıkan bir betik iz bırakmaz. Bu bir güvenlik mekanizması değil, kanıt izidir:
agent'ın veriye gerçekten baktığını gösterir, cevabın doğru olduğunu göstermez.
"""
import json
import sys
import time
from pathlib import Path

KAYIT = Path(__file__).resolve().parent.parent / "work" / "erisim.jsonl"


def utf8_cikti() -> None:
    """Windows konsolu varsayılan olarak cp1252/cp1254 kullanır; Türkçe karakterli JSON
    yazdırmak UnicodeEncodeError verir. Çıktıyı platformdan bağımsız UTF-8'e sabitle."""
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8")


def kaydet(betik: str, hedef: str) -> None:
    KAYIT.parent.mkdir(parents=True, exist_ok=True)
    with KAYIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"zaman": time.time(), "betik": betik, "hedef": hedef}, ensure_ascii=False) + "\n")


def kayit_sayisi() -> int:
    return sum(1 for _ in KAYIT.open(encoding="utf-8")) if KAYIT.exists() else 0
