"""Erişim kaydı: okuma betikleri başarıyla bittiğinde work/erisim.jsonl dosyasına bir satır ekler.

Stop hook'u (kancalar.py) bu kayda bakar: son kullanıcı isteğinden beri hiç başarılı
veri erişimi yoksa cevabı bir kez geri çevirir. Kayıt betiğin SONUNDA yazılır; hata
verip çıkan bir betik iz bırakmaz. Bu bir güvenlik mekanizması değil, kanıt izidir:
agent'ın veriye gerçekten baktığını gösterir, cevabın doğru olduğunu göstermez.
"""
import json
import time
from pathlib import Path

KAYIT = Path(__file__).resolve().parent.parent / "work" / "erisim.jsonl"


def kaydet(betik: str, hedef: str) -> None:
    KAYIT.parent.mkdir(parents=True, exist_ok=True)
    with KAYIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"zaman": time.time(), "betik": betik, "hedef": hedef}, ensure_ascii=False) + "\n")


def kayit_sayisi() -> int:
    return sum(1 for _ in KAYIT.open(encoding="utf-8")) if KAYIT.exists() else 0
