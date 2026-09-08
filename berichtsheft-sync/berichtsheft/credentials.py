"""Store BLok credentials in macOS Keychain (ideal) or local secrets file (fallback)."""

from __future__ import annotations

import getpass
import os
import platform
import subprocess
from pathlib import Path

from berichtsheft.config_loader import load_dotenv

SERVICE_PREFIX = "berichtsheft-sync"
SECRETS_DIR = Path.home() / ".berichtsheft"
SECRETS_FILE = SECRETS_DIR / "credentials.local"


def _service_name(service: str) -> str:
    return f"{SERVICE_PREFIX}.{service}"


def _keychain_available() -> bool:
    return platform.system() == "Darwin"


def _validate_username(username: str) -> None:
    if not username or not password_allowed_chars(username):
        raise ValueError("Username BLok kosong atau tidak valid.")
    if " " in username or username.startswith("-") or "python" in username.lower():
        raise ValueError(
            "Username tidak valid (seperti perintah terminal?). "
            "Gunakan username login BLok saja, mis. agwenacimdamero"
        )


def password_allowed_chars(username: str) -> bool:
    return bool(username.strip())


def set_credential(service: str, username: str, password: str) -> None:
    _validate_username(username)
    if _keychain_available():
        subprocess.run(
            [
                "security",
                "add-generic-password",
                "-a",
                username,
                "-s",
                _service_name(service),
                "-w",
                password,
                "-U",
            ],
            check=True,
            capture_output=True,
        )
        print(f"✓ Keychain: {_service_name(service)} (account={username})")
        return

    SECRETS_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    lines = []
    if SECRETS_FILE.exists():
        for line in SECRETS_FILE.read_text().splitlines():
            if not line.startswith(f"{service}:"):
                lines.append(line)
    lines.append(f"{service}:{username}:{password}")
    SECRETS_FILE.write_text("\n".join(lines) + "\n")
    SECRETS_FILE.chmod(0o600)
    print(f"✓ Lokal: {SECRETS_FILE} (chmod 600) — gunakan Mac+Keychain jika memungkinkan")


def get_credential(service: str) -> tuple[str, str] | None:
    """Resolve credentials: Keychain (Mac) → local secrets → env (cloud).

    Env fallback (never commit): BLOK_USERNAME / BLOK_PASSWORD when service == \"blok\".
    Optional BLOK_BASE_URL is handled by callers (worker / live snapshot).
    """
    if service == "blok":
        # Cloud VM has no Keychain; optional .env only. Prefer Keychain when present.
        load_dotenv()

        env_user = os.environ.get("BLOK_USERNAME", "").strip()
        env_pass = os.environ.get("BLOK_PASSWORD", "").strip()
        # Prefer Keychain/secrets below; env used if those miss — checked after
        env_pair = (env_user, env_pass) if env_user and env_pass else None
    else:
        env_pair = None

    if _keychain_available():
        try:
            user_proc = subprocess.run(
                [
                    "security",
                    "find-generic-password",
                    "-s",
                    _service_name(service),
                    "-w",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if user_proc.returncode != 0:
                pass  # fall through to secrets / env
            else:
                password = user_proc.stdout.strip()
                account_proc = subprocess.run(
                    [
                        "security",
                        "find-generic-password",
                        "-s",
                        _service_name(service),
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                account = ""
                for line in account_proc.stdout.splitlines():
                    if '"acct"' in line or "acct" in line:
                        part = line.split("=")[-1].strip().strip('"')
                        account = part
                        break
                if not account:
                    account = "blok-user"
                return account, password
        except subprocess.CalledProcessError:
            pass  # fall through to secrets / env

    if SECRETS_FILE.exists():
        for line in SECRETS_FILE.read_text().splitlines():
            if line.startswith(f"{service}:"):
                _, user, pwd = line.split(":", 2)
                return user, pwd

    if env_pair:
        return env_pair
    return None


def test_credential(service: str) -> bool:
    cred = get_credential(service)
    if not cred:
        print(f"✗ Tidak ada kredensial untuk '{service}'")
        return False
    user, _ = cred
    print(f"✓ Kredensial '{service}' ada (user={user})")
    return True


def prompt_and_set(service: str) -> None:
    print(f"Set kredensial untuk '{service}' (input tidak dikirim ke Cursor/chat).")
    username = input("Username BLok: ").strip()
    password = getpass.getpass("Password BLok: ")
    if not username or not password:
        raise SystemExit("Username/password kosong — dibatalkan.")
    try:
        _validate_username(username)
    except ValueError as e:
        raise SystemExit(str(e)) from e
    set_credential(service, username, password)
