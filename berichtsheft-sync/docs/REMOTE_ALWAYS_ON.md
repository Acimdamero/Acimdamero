# Remote always-on — Mac hub + akses dari HP / Cloud

**Mac = source of truth.** SQLite (`berichtsheft.db`), Keychain (BLok), WAHA/Docker, Playwright worker, dan bot Telegram/WhatsApp tinggal di Mac. Cloud VM Cursor **bisa tidur**; HP hanya browser. Akses kapan saja lewat **HTTPS tunnel publik** ke `serve` di Mac, dengan **token wajib**.

> Tunnel di Cloud VM hanya demo sementara. Hub permanen = Mac + launchd.

---

## Arsitektur (satu kalimat)

**Mac menjalankan `serve` + bot + Cloudflare Tunnel 24/7; HP/Cloud/apps membuka `https://…/dashboard?token=` (atau sync-pull/push ke URL yang sama).**

```
[HP browser / Cloud Cursor / apps nanti]
        │  HTTPS + DASHBOARD_TOKEN
        ▼
[Cloudflare Tunnel] ──► [MacBook always-on]
                          • python3 -m berichtsheft serve  (0.0.0.0:8765)
                          • SQLite + Keychain + BLok worker
                          • Telegram / WhatsApp bots (prefer di Mac)
                          • data/remote_hub_url.txt (URL publik, gitignored)
```

| Peran | Apa yang hidup di sana |
|-------|-------------------------|
| **Mac (hub)** | DB, Keychain, bots, tunnel, dashboard publik |
| **Cloud VM** | Edit kode, katalog via git; opsional klien sync ke Mac |
| **HP** | Buka dashboard Mac lewat URL+token — tanpa install |
| **GitHub** | Kode / docs / katalog — **bukan** `.db` / `.env` / token |

---

## Setup Mac sekali (lalu biarkan jalan)

### 1. Prasyarat

```bash
cd ~/Projects/berichtsheft-sync   # path Anda
cp -n .env.example .env
cp -n config.example.yaml config.yaml
# Isi .env:
#   DASHBOARD_TOKEN=<random panjang>   # WAJIB untuk remote
#   TELEGRAM_BOT_TOKEN=…               # jika bot di Mac
#   SYNC_TOKEN=…                       # opsional (default = DASHBOARD_TOKEN)

brew install cloudflare/cloudflare/cloudflared   # jika belum
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m berichtsheft init
```

Generate token jika kosong:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
# tempel ke DASHBOARD_TOKEN=… di .env — JANGAN commit .env
```

### 2. Start hub (serve + tunnel)

```bash
./scripts/start_remote_hub.sh --bot
# tanpa bot: ./scripts/start_remote_hub.sh
# stop:     ./scripts/start_remote_hub.sh --stop
```

Script akan:

1. Cek `DASHBOARD_TOKEN` / `SYNC_TOKEN` (wajib — keluar jika kosong)
2. Jalankan `serve` di **0.0.0.0:8765**
3. Opsional bot Telegram/WhatsApp
4. Jalankan `cloudflared tunnel --url http://127.0.0.1:8765`
5. Tulis URL publik ke `data/remote_hub_url.txt` (gitignored)
6. Cetak pola dashboard HP

### 3. launchd KeepAlive (reboot-safe)

Contoh plist: [`scripts/com.berichtsheft.hub.plist`](../scripts/com.berichtsheft.hub.plist)

```bash
# 1) Edit path REPLACE_ME di plist → folder berichtsheft-sync Anda
cp scripts/com.berichtsheft.hub.plist ~/Library/LaunchAgents/
nano ~/Library/LaunchAgents/com.berichtsheft.hub.plist

# 2) Load
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.berichtsheft.hub.plist

# 3) Cek
launchctl print gui/$(id -u)/com.berichtsheft.hub
cat ~/Projects/berichtsheft-sync/data/remote_hub_url.txt

# Unload
launchctl bootout gui/$(id -u)/com.berichtsheft.hub
```

**Catatan quick tunnel:** URL `*.trycloudflare.com` **berubah** setiap restart. Setelah relaunch, baca ulang `data/remote_hub_url.txt` dan update bookmark HP / Cloud `.env`. Untuk hostname tetap, buat **named tunnel** + DNS di Cloudflare Zero Trust (lihat docs Cloudflare).

---

## Pola URL HP (buka kapan saja)

```text
https://<PUBLIC-HOST>/dashboard?token=<DASHBOARD_TOKEN>
```

Contoh (token disensor):

```text
https://eat-trials-traditional-blair.trycloudflare.com/dashboard?token=••••
```

- Bookmark di Safari / Chrome HP
- Token sama dengan `.env` Mac (`DASHBOARD_TOKEN`)
- Tanpa token → 401 jika token di-set (wajib untuk remote)

Auth alternatif: header `Authorization: Bearer …` atau `X-Dashboard-Token`.

---

## Cloud Cursor / agent (klien remote)

Di Cloud `.env` (jangan commit):

```bash
BERICHTSHEFT_REMOTE_API=https://<PUBLIC-HOST>
BERICHTSHEFT_REMOTE_TOKEN=<sama dengan DASHBOARD_TOKEN Mac>
BERICHTSHEFT_API=https://<PUBLIC-HOST>
```

Lalu:

```bash
python3 -m berichtsheft sync-pull    # tarik snapshot dari Mac
python3 -m berichtsheft sync-push    # dorong edits ke Mac
python3 -m berichtsheft sync-status
```

Dashboard Cloud panel **Cloud ↔ Mac**:

1. Isi Remote API URL + Remote token → **Save**
2. **Health-check remote** (cek `/health` + `/dashboard/api/health`)
3. **Open Mac dashboard** (deep-link ke hub publik)
4. Pull / Push snapshot jika perlu sync offline

---

## Telegram / WhatsApp: jalankan di Mac

| Tempat | Rekomendasi |
|--------|-------------|
| **Mac** | **Prefer** — bot polling 24/7, DB lokal, WAHA Docker |
| **Cloud VM** | Hanya sementara; VM sleep = bot mati |

```bash
# Di Mac (sudah termasuk jika start_remote_hub.sh --bot):
python3 -m berichtsheft bot          # Telegram
python3 -m berichtsheft wa-bot       # WhatsApp (butuh WAHA)
```

Cloud boleh *poin* `BERICHTSHEFT_API` ke tunnel Mac agar bot Cloud (jika dijalankan) menulis ke DB Mac — tapi untuk persistensi, biarkan bot di Mac.

---

## Keamanan

- [ ] `DASHBOARD_TOKEN` / `SYNC_TOKEN` **wajib** sebelum tunnel publik
- [ ] Jangan commit `.env`, `*.db`, `data/remote_hub_url.txt`, `data/sync_config.json`
- [ ] Rotasi token jika URL+token pernah dibocorkan di chat
- [ ] Prefer Cloudflare Tunnel / Tailscale daripada port-forward mentah
- [ ] Quick tunnel = bagus untuk mulai; produksi → named tunnel + akses terkontrol

---

## Troubleshooting

| Gejala | Cek |
|--------|-----|
| HP 401 | Token di URL vs `.env` Mac; cookie lama |
| Tunnel URL 502 | `serve` mati — `curl http://127.0.0.1:8765/health` |
| URL berubah | Baca `data/remote_hub_url.txt` lagi; update bookmark |
| Bot diam | Bot harus di Mac; cek `logs/hub-bot.log` |
| Cloud sync gagal | `BERICHTSHEFT_REMOTE_API` + `BERICHTSHEFT_REMOTE_TOKEN`; panel Health-check |

Lihat juga: [CLOUD_LOCAL_BRIDGE.md](CLOUD_LOCAL_BRIDGE.md), [DASHBOARD.md](DASHBOARD.md), [CLOUD_RUN.md](CLOUD_RUN.md), [TELEGRAM.md](TELEGRAM.md).
