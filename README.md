# tablo-ajani

Periskop yazısına eşlik eden repo: **"Claude Agent SDK ile İlk Agent: Prototipten Üretime"** (iki bölümlük yazının ikinci bölümü).

Claude Agent SDK (Python) ile kurulmuş bir spreadsheet agent'ı. Thariq Shihipar'ın (Anthropic)
Claude Agent SDK workshop'undaki ilkeleri çalışan koda çevirir:

| İlke | Repo'daki karşılığı |
| --- | --- |
| Bağlamı agent kendisi toplar, tablo asla tamamen okunmaz | `scripts/sayfa_bilgisi.py`, `scripts/aralik_oku.py` |
| Problemi modelin bildiği dile çevir (SQL, A1 aralığı) | `scripts/sqlite_aktar.py`, `scripts/sql.py` |
| Okuma/arama bash ile, geri alınması zor eylemler tool ile | `araclar.py` (`hucre_yaz`, `geri_al`) |
| Önce deterministik doğrulama | `scripts/dogrula.py` + PostToolUse hook |
| Kontrol noktası → yazma → doğrulama → kabul / geri alma | `hucre_yaz` yeni sorun sokan yazmayı otomatik geri alır |
| Kural ihlalinde agent'a geri bildirim | 50 hücre sınırı, `xlsx_koruma` hook'u |
| Veriye bakmadan cevap verme | `kanitsiz_cevap` Stop hook'u + istek başına erişim kaydı (`scripts/_kayit.py`) |
| Şüpheci, temiz bağlamlı denetçi | `denetci` subagent'ı (`agent.py`) |
| Geri alınabilirlik | her yazmada kontrol noktası, `geri_al` |
| Talimatlar kodda değil dosyada | `CLAUDE.md` |

## Kurulum

Python 3.10+ ve bir `ANTHROPIC_API_KEY` gerekir. `claude-agent-sdk` paketi Claude Code CLI'ını içinde taşır.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python data/ornek_olustur.py      # data/kuzey_elektronik.xlsx (bilerek iki kusurlu)
python testler/test_cevrimdisi.py  # API anahtarı gerektirmez
export ANTHROPIC_API_KEY=...
python agent.py
```

İsteğe bağlı ortam değişkenleri: `TABLO_MODEL` (model adı), `TABLO_BUTCE_USD` (oturum bütçesi, varsayılan 1.0).

## Denenecek sorular

1. `2026'da toplam gelir ne?`
2. `Tablodaki sorunları bul.`
3. `Pazarlama giderindeki sorunu düzelt.` (onay istenir)
4. `Son değişikliği geri al.` (onay istenir)

Her oturumda transkripti okuyun: agent önce haritayı mı çıkarıyor, sayının kaynağını gösteriyor mu,
yazmadan önce soruyor mu, denetçiyi çağırıyor mu?

## Bu bir prototip yapılandırmasıdır

`agent.py` kontrollü bir prototip içindir; güvenli bir üretim yapılandırması değildir:

- **Bash ön onaylıdır.** `allowed_tools` içinde olduğu için her Bash komutu sorulmadan çalışır ve
  `can_use_tool` (onay akışı) Bash çağrılarını hiç görmez. Onay yalnızca `hucre_yaz` ve `geri_al` içindir.
- **`xlsx_koruma` bir güvenlik sınırı değildir.** Komut metninde `.xlsx` arar; dosya adını dolaylı
  kuran bir komut onu aşar. Agent'ı doğru araca yönlendiren bir geri bildirimdir.
- **Sandbox varsayılan olarak kapalıdır.** `TABLO_SANDBOX=1` SDK'nın bash sandbox'ını açar
  (macOS/Linux); bu seçenek canlı çalıştırmayla doğrulanmadı.
- **`TABLO_BUTCE_USD` kalıcı bir bütçe değildir.** Açık bağlantının tahmini koşan toplamına uygulanır,
  sınırı aşan yanıt kadar aşılabilir, programı yeniden başlatınca sıfırlanır.

Üretim için gerekenler: container, açık sandbox ve ağ kısıtı, dar kapsamlı izin kuralları,
kullanıcı başına yalıtılmış çalışma dizini, uygulama düzeyinde maliyet takibi
(bkz. https://code.claude.com/docs/en/agent-sdk/secure-deployment).

## Bilinen sınırlar

- **Hesaplama motoru yok.** `openpyxl` formülleri hesaplamaz; `dogrula.py` bir formülün üreteceği
  hatayı (`=A1/B1` → `#DIV/0!`) göremez. Yazmadan sonra formül sonuçları ancak dosya Excel/LibreOffice
  ile açılıp yeniden hesaplanınca oluşur.
- **SQLite kopyası kayıplıdır.** Örnek veride `Gider!C4` metin olarak `"210.000"` içerir; SQLite bunu
  210.0 sayar ve `SUM("2025")` 2.642.000 yerine 2.432.210 döndürür. `sqlite_aktar.py` bu hücreleri
  listeleyip uyarır.
- **Erişim kaydı doğruluk kanıtı değildir.** Agent'ın bu istekte veriye baktığını gösterir; doğru
  hücreye baktığını ya da doğru yorumladığını göstermez.

## Durum

- Çevrimdışı testler (`testler/test_cevrimdisi.py`) `claude-agent-sdk` 0.2.186 ile geçer.
- Agent modelle iki kısa oturumda uçtan uca çalıştırıldı (20 Kasım 2026, Windows).
  Doğrulananlar: özel tool'lar görünüyor, onay sorusu `hucre_yaz` ve `geri_al` için terminale düşüyor,
  `denetci` çağrılıyor, Stop hook'u veriye bakılmayan cevabı geri çeviriyor, geri alma çalışıyor,
  `xlsx_koruma` subagent içinde de çalışıp denetçinin doğrudan openpyxl komutunu reddediyor,
  iki düzeltmeden sonra `dogrula.py` sıfır sorun buluyor.
- Henüz sınanmayanlar: SQLite yolu (agent hiç kullanmadı), otomatik geri alınan bir yazma,
  `TABLO_SANDBOX=1`. Denetçi talimatındaki son ek (yedekleri betiklerle oku, geçici dosya bırakma)
  ikinci oturumdan sonra eklendi.
- Birkaç oturum kanıt değildir; model ya da SDK sürümü değişince davranış değişebilir.
