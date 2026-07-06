# WhatsApp di iPhone — Kontrol & Otomatisasi

> **Penting:** Saya (Cloud Agent) **tidak bisa** mengakses atau mengontrol WhatsApp di iPhone Anda secara langsung. Dokumen ini = batas legal iOS + cara setup maksimal di Automation Hub.

---

## Apa yang BISA vs TIDAK BISA

| Aksi | Bisa? | Cara |
|------|-------|------|
| Buka WhatsApp | ✅ | `Open App` / URL scheme |
| Buka chat kontak tertentu | ✅ | `wa.me` atau `whatsapp://send?phone=` |
| Prefill pesan (draft) | ✅ | URL + `text=` parameter |
| Kirim pesan **tanpa tap Send** | ❌* | iOS/WhatsApp blokir auto-send |
| Baca inbox / pesan masuk | ❌ | Sandbox iOS |
| Balas otomatis di background | ❌ | Tidak ada API personal |
| Kontrol grup (buka chat grup) | ⚠️ | Terbatas; kontak individual lebih mudah |
| Jadwalkan draft pesan | ✅ | Automation Time of Day → buka draft |
| Kirim dari Mac Hub ke iPhone | ⚠️ | Sheet queue → Shortcut → buka draft |

\*Beberapa versi Shortcuts punya action "Send Message via WhatsApp" — sering **tetap minta konfirmasi** atau hanya prefill. Anggap selalu **human-in-the-loop** (Anda tap Send).

---

## URL Scheme WhatsApp

### Chat + prefill pesan (paling andal)

```
https://wa.me/6281234567890?text=Halo%20dari%20Hub
```

- Nomor: **E.164 tanpa +** (Indonesia: `62...` bukan `+62`)
- Teks: **URL-encoded** (spasi = `%20`)

### Fallback scheme

```
whatsapp://send?phone=6281234567890&text=Halo
```

### Buka app saja

```
whatsapp://
```

---

## Shortcut 1: Hub — WhatsApp Chat

Buat di app Shortcuts:

1. **Receive** input: `Phone`, `Message` (dari Hub atau manual)
2. **Text**: `https://wa.me/` + Phone + `?text=` + Message
3. Atau lebih aman:
   - **Encode Text** (Message) → URL encoding
   - **Text**: `https://wa.me/[Phone]?text=[Encoded]`
4. **Open URL**
5. Nama shortcut: **`Hub — WhatsApp Chat`**

### Test manual

Nomor contoh (ganti milik Anda): `6281234567890`

---

## Shortcut 2: Hub — Execute WhatsApp Command

Integrasi dengan antrian Google Sheet (`device=iphone`, `command=whatsapp-*`):

```
IF command = whatsapp-open
  → Open URL whatsapp://

IF command = whatsapp-chat
  → args = "628xxx|Halo dari Hub"
  → Split args by |
  → Run Hub — WhatsApp Chat

IF command = whatsapp-template
  → args = "template_name" (On My Way / Running Late / dll.)
  → Lookup template text → Run Hub — WhatsApp Chat
```

---

## Template pesan (opsional)

Buat Dictionary di Shortcut:

| Key | Teks |
|-----|------|
| `on-my-way` | Otw, sekitar 15 menit lagi 🚗 |
| `running-late` | Maaf telat, masih di jalan |
| `available` | Sudah available, bisa call |

Hub command: `whatsapp-template` args=`on-my-way|6281234567890`

---

## Integrasi Automation Hub (Google Sheet)

Tambah baris di tab `Queue`:

| id | device | command | status | args |
|----|--------|---------|--------|------|
| wa1 | iphone | whatsapp-chat | pending | 6281234567890\|Backup Mac selesai |
| wa2 | iphone | whatsapp-open | pending | |

iPhone Automation (poll 15 menit) → eksekusi → buka WhatsApp dengan draft.

**Alur Mac → WhatsApp iPhone:**

```
Mac backup selesai
  → Mac/Apps Script append row iphone/whatsapp-chat/pending
  → iPhone poll queue
  → Shortcut buka wa.me dengan pesan
  → Anda tap Send di WhatsApp
```

---

## Automation terjadwal (contoh)

**Automation → Time of Day → 08:00 daily**

1. Run Shortcut: **Hub — WhatsApp Chat**
2. Input: nomor + "Selamat pagi, sudah di kantor"
3. Turn off **Ask Before Running**
4. Saat trigger: WhatsApp terbuka dengan draft — **Anda tap Send**

---

## Siri & akses cepat

- Pin shortcut ke Home Screen
- Back Tap → Run **Hub — WhatsApp Chat**
- Action Button (iPhone 15 Pro+) → shortcut favorit
- "Hey Siri, WhatsApp Hub" → rename shortcut agar Siri mengenali

---

## Keamanan & privasi

- **Jangan** simpan nomor sensitif di Sheet publik — gunakan tab terpisah atau Keychain
- Nomor telepon di Sheet = risiko privasi; batasi akses Sheet hanya Anda
- WhatsApp **tidak** punya API untuk akun personal — hanya Business API (cloud, akun bisnis terpisah)
- Workflow ini **tidak** melanggar ToS WhatsApp (prefill resmi via wa.me)

---

## WhatsApp Business API (jika butuh kirim otomatis sungguhan)

Untuk **kirim tanpa tap Send** (notifikasi order, OTP, dll.) — butuh:

- Akun **WhatsApp Business Platform** (Meta)
- Nomor bisnis terverifikasi
- Server + webhook (bukan app WhatsApp di iPhone)

Ini **beda** dari mengontrol app WhatsApp personal di iPhone. Hub personal kita **tidak** cover Business API — itu layer terpisah.

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Link tidak buka chat | Nomor harus E.164 tanpa `+`, spasi, strip |
| `wa.me` gagal | Coba `whatsapp://send?phone=` |
| Emoji rusak | Pakai action **Encode Text** URL |
| Grup tidak bisa | wa.me untuk individual; grup perlu workaround manual |
| MDM/kantor | Admin bisa blok URL scheme |
| Shortcut tidak jalan locked | iPhone harus unlock untuk Open URL |

---

## File terkait

- `iphone/command-registry.json` — entry `whatsapp-*`
- `iphone/SHORTCUTS-GUIDE.md` — setup SSH & queue
- `google/SHEET-TEMPLATE.md` — antrian perintah
