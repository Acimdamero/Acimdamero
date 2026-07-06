# Akses Akun — 1Password + Apple Keychain

Automation Hub mendukung **keduanya** tanpa menyimpan password mentah di script.

## 1Password CLI (disarankan untuk otomatisasi)

### Install

```bash
brew install 1password-cli
op signin
```

### Simpan item di vault

Buat item **Google Sheets API** dengan field `credential` = OAuth access token (refresh via OAuth flow).

### Pakai di script

Sudah terintegrasi di `mac/scripts/lib.sh`:

```bash
get_op_secret "Google Sheets API" "credential"
```

### Jalankan script dengan secret injected

```bash
op run --env-file=.env.op -- ~/.automation-hub/run-task.sh queue-process
```

File `.env.op`:

```
GOOGLE_ACCESS_TOKEN=op://Private/Google Sheets API/credential
```

---

## Apple Keychain (native Mac)

### Simpan token Google

```bash
security add-generic-password \
  -s "automation-hub" \
  -a "google-sheets-token" \
  -w "YOUR_OAUTH_ACCESS_TOKEN"
```

Script otomatis membaca via `get_keychain_secret "google-sheets-token"`.

### Lihat token (debug)

```bash
security find-generic-password -s automation-hub -a google-sheets-token -w
```

---

## Google OAuth (Sheets API)

1. [Google Cloud Console](https://console.cloud.google.com) → buat project
2. Enable **Google Sheets API** + **Google Drive API**
3. OAuth consent screen → External → scopes: spreadsheets, drive.file
4. Credentials → OAuth 2.0 Client ID → Desktop app
5. Dapatkan refresh token (gunakan `google-auth-oauthlib` atau tool OAuth lokal)
6. Simpan access/refresh token di 1Password atau Keychain

**Alternatif lebih mudah:** pakai **Apps Script Web App** (lihat `google/apps-script/`) — tidak perlu OAuth di Mac untuk antrian dasar.

---

## iPhone Keychain

Di Shortcuts, untuk URL Web App yang butuh auth:

- Simpan URL deploy Apps Script (tidak berisi secret)
- Jangan hardcode API key di Shortcuts
- Gunakan **Ask Each Time** untuk token jika diperlukan

---

## Cursor + Google

1. Gemini API key → [AI Studio](https://aistudio.google.com/apikey)
2. Cursor → Settings → Models → Google → Verify
3. Copy `cursor/mcp.json.example` ke `~/.cursor/mcp.json` atau `.cursor/mcp.json`
4. Restart Cursor → OAuth Google Drive saat diminta
