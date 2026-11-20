"""Tablo agent'ı: Claude Agent SDK ile çalışan bir spreadsheet agent'ı.

Çalıştırma:
  python data/ornek_olustur.py        # örnek çalışma kitabını üret
  python agent.py                     # etkileşimli sohbet

Agent'ın talimatları CLAUDE.md'dedir; bu dosya yalnızca runtime'ı yapılandırır:
hangi araçlar açık, hangi hook'lar çalışır, hangi subagent tanımlı, yazma onayı nasıl alınır.

Bu dosya kontrollü bir PROTOTİP yapılandırmasıdır, güvenli bir üretim yapılandırması değil:
Bash ön onaylıdır ve sandbox varsayılan olarak kapalıdır. Yalnızca örnek veriyle, kendi
makinenizde çalıştırın. TABLO_SANDBOX=1 ile SDK'nın bash sandbox'ı açılabilir.
"""
import asyncio
import os
from pathlib import Path

from claude_agent_sdk import (
    AgentDefinition, AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, HookMatcher,
    PermissionResultAllow, PermissionResultDeny, ResultMessage, TextBlock, ToolUseBlock,
)

from araclar import tablo_sunucusu
from kancalar import Kancalar, komut_ozeti

KOK = Path(__file__).parent
YAZMA_ARACLARI = {"mcp__tablo__hucre_yaz", "mcp__tablo__geri_al"}

DENETCI = AgentDefinition(
    description="Tabloda yapılan değişiklikleri ve ana agent'ın vardığı sonucu bağımsız olarak "
                "denetler. Bir yazma işleminden sonra ve sayısal bir sonuç bildirmeden önce çağır.",
    prompt="Sen şüpheci bir finans denetçisisin. Önündeki iş deneyimsiz bir analistin elinden çıktı. "
           "Sonuca güvenme: scripts/ altındaki betiklerle veriyi kendin oku, toplamları kendin hesapla. "
           "Bulduğun her tutarsızlığı hücre adresiyle listele. Hiçbir şeyi değiştirme; yalnızca raporla.",
    tools=["Bash", "Read", "Grep", "Glob"],
)


async def yazma_onayi(arac: str, girdi: dict, baglam) -> PermissionResultAllow | PermissionResultDeny:
    """allowed_tools listesinde olmayan her araç buraya düşer."""
    if arac not in YAZMA_ARACLARI:
        return PermissionResultDeny(message=f"{arac} bu agent'ta kullanılamaz.")
    print(f"\n  [onay] {arac}: {girdi}")
    cevap = await asyncio.to_thread(input, "  Bu değişikliği onaylıyor musun? [e/h] ")
    if cevap.strip().lower().startswith("e"):
        return PermissionResultAllow()
    return PermissionResultDeny(message="Kullanıcı bu değişikliği reddetti. Nedenini sor.")


def secenekler(k: Kancalar) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=str(KOK),
        system_prompt={"type": "preset", "preset": "claude_code"},
        setting_sources=["project"],                 # CLAUDE.md buradan yüklenir
        tools=["Bash", "Read", "Grep", "Glob", "Agent"],
        # DİKKAT: Bash burada koşulsuz ön onaylıdır; yazma_onayi Bash çağrılarını hiç görmez.
        # Bu bir prototip yapılandırmasıdır. Üretimde: sandbox + dar izin kuralları (bkz. README).
        allowed_tools=["Bash", "Read", "Grep", "Glob", "Agent"],  # sorulmadan çalışır
        mcp_servers={"tablo": tablo_sunucusu},       # hucre_yaz, geri_al: her seferinde onay
        permission_mode="default",                   # auto mode varsayılan olabilir; onay akışını sabitle
        can_use_tool=yazma_onayi,
        agents={"denetci": DENETCI},
        hooks={
            "PreToolUse": [
                HookMatcher(matcher="Bash|Write|Edit", hooks=[k.xlsx_koruma]),
            ],
            "PostToolUse": [HookMatcher(matcher="mcp__tablo__hucre_yaz", hooks=[k.yazim_sonrasi])],
            "Stop": [HookMatcher(hooks=[k.kanitsiz_cevap])],
        },
        sandbox={"enabled": True} if os.environ.get("TABLO_SANDBOX") == "1" else None,  # isteğe bağlı
        max_turns=40,
        # Bu bağlantının tahmini koşan toplamına uygulanır; kalıcı bir oturum bütçesi değildir.
        max_budget_usd=float(os.environ.get("TABLO_BUTCE_USD", "1.0")),
        model=os.environ.get("TABLO_MODEL") or None,
    )


def yazdir(mesaj) -> None:
    """Her araç çağrısını görünür kıl: agent tasarımının ana girdisi transkripttir."""
    if isinstance(mesaj, AssistantMessage):
        for blok in mesaj.content:
            if isinstance(blok, TextBlock):
                print(f"\nAgent: {blok.text}")
            elif isinstance(blok, ToolUseBlock):
                ayrinti = komut_ozeti(blok.input.get("command", "")) if blok.name == "Bash" else blok.input
                print(f"  → {blok.name}: {ayrinti}")
    elif isinstance(mesaj, ResultMessage):
        maliyet = f"${mesaj.total_cost_usd:.4f}" if mesaj.total_cost_usd is not None else "?"
        print(f"\n  [tur: {mesaj.num_turns} · tahmini toplam maliyet: {maliyet} · durum: {mesaj.subtype}]")


async def main() -> None:
    k = Kancalar()
    async with ClaudeSDKClient(options=secenekler(k)) as istemci:
        print("Tablo agent'ı hazır. Çıkmak için boş satır.")
        while soru := (await asyncio.to_thread(input, "\nSen: ")).strip():
            k.yeni_istek()                    # kanıt sayacı: istek başına
            await istemci.query(soru)
            async for mesaj in istemci.receive_response():
                yazdir(mesaj)


if __name__ == "__main__":
    asyncio.run(main())
