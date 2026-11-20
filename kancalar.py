"""Deterministik kurallar: model ne düşünürse düşünsün çalışan hook'lar.

1. xlsx_koruma      (PreToolUse)  — xlsx dosyalarına bash/Write/Edit ile yazmayı engeller.
2. yazim_sonrasi    (PostToolUse) — hucre_yaz'dan sonra kalan sorunları agent'ın bağlamına ekler.
3. kanitsiz_cevap   (Stop)        — son kullanıcı isteğinden beri başarılı bir veri erişimi
                                    yoksa cevabı bir kez geri çevirir.

Kanıt izi: okuma betikleri başarıyla bitince work/erisim.jsonl dosyasına kayıt düşer
(scripts/_kayit.py). yeni_istek() her kullanıcı mesajında sayacı sıfırlar; böylece
kontrol oturum başına değil, istek başına yapılır.

Hook kararları terminale "[hook] ..." satırıyla yazılır; transkript okunurken bir aracın
reddedildiği ya da bir cevabın geri çevrildiği böylece görülür.

Not: Bu hook'lar bir güvenlik sınırı değildir; agent'ı doğru yola iten
geri bildirim mekanizmalarıdır. Güvenlik sınırı sandbox'tır (bkz. README).
"""
import re
import subprocess
import sys
from pathlib import Path

from scripts._kayit import kayit_sayisi

KOK = Path(__file__).resolve().parent
OKUMA_BETIKLERI = ("scripts/sayfa_bilgisi.py", "scripts/aralik_oku.py",
                   "scripts/sqlite_aktar.py", "scripts/sql.py", "scripts/dogrula.py")


class Kancalar:
    def __init__(self) -> None:
        self.istek_baslangici = kayit_sayisi()

    def yeni_istek(self) -> None:
        """Her kullanıcı mesajından önce çağrılır: kanıt sayacı bu istek için sıfırlanır."""
        self.istek_baslangici = kayit_sayisi()

    async def xlsx_koruma(self, girdi, tool_use_id, baglam):
        arac, veri = girdi["tool_name"], girdi["tool_input"]
        if arac in ("Write", "Edit") and str(veri.get("file_path", "")).endswith(".xlsx"):
            return self._reddet("xlsx dosyalarına doğrudan yazılmaz; mcp__tablo__hucre_yaz aracını kullan.")
        if arac == "Bash":
            komut = veri.get("command", "")
            if ".xlsx" in komut and not any(b in komut for b in OKUMA_BETIKLERI):
                return self._reddet("xlsx dosyalarını yalnızca scripts/ altındaki okuma betikleriyle aç; "
                                    "yazmak için mcp__tablo__hucre_yaz aracını kullan.")
        return {}

    async def yazim_sonrasi(self, girdi, tool_use_id, baglam):
        dosya = girdi["tool_input"].get("dosya", "")
        sonuc = subprocess.run([sys.executable, "scripts/dogrula.py", dosya],
                               cwd=KOK, capture_output=True, text=True, encoding="utf-8")
        durum = "temiz" if sonuc.returncode == 0 else "SORUN VAR"
        return {"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"Otomatik doğrulama ({durum}):\n{sonuc.stdout}",
        }}

    async def kanitsiz_cevap(self, girdi, tool_use_id, baglam):
        if girdi.get("stop_hook_active"):      # ikinci kez engelleme: sonsuz döngüye girme
            return {}
        if kayit_sayisi() <= self.istek_baslangici:   # bu istekte başarılı veri erişimi yok
            print("  [hook] durma reddedildi: bu istekte veri erişimi yok")
            return {"decision": "block",
                    "reason": "Bu istekte tablodaki veriye bakmadın. Soru tabloyla ilgiliyse önce "
                              "scripts/ altındaki betiklerle veriyi oku, sonra cevap ver."}
        return {}

    @staticmethod
    def _reddet(neden: str) -> dict:
        print(f"  [hook] reddedildi: {neden}")   # hook kararları transkriptte görünsün
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": neden,
        }}


def komut_ozeti(komut: str, uzunluk: int = 90) -> str:
    """Log için tek satırlık komut özeti."""
    tek = re.sub(r"\s+", " ", komut).strip()
    return tek if len(tek) <= uzunluk else tek[: uzunluk - 1] + "…"
