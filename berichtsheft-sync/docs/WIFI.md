# WiFi portal otomatis (Mac)

Portal tanpa password = biasanya satu tombol **Login / Accept**.

## Konfigurasi (`config.yaml`)

```yaml
wifi:
  ssid: "NAMA-WIFI-HOTEL"
  portal_url: "http://..."   # URL setelah captive redirect (isi setelah 1x buka manual)
  login_button_selector: "button#login"  # CSS — inspect di browser
  check_interval_minutes: 10
```

## Uji

```bash
python3 scripts/wifi_portal.py --dry-run
python3 scripts/wifi_portal.py   # hanya jika SSID cocok + internet gagal
```

## launchd (opsional)

Buat `~/Library/LaunchAgents/de.berichtsheft.wifi.plist` yang menjalankan skrip tiap 600 detik.

**Kebijakan IT:** pastikan automasi portal diperbolehkan di perusahaan Anda.
