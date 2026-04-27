"""
auto_install.py
===============
Jo libraries install nahi hain, ye module unhe automatically install kar deta hai.
Bas `from auto_install import setup` likho aur `setup()` call karo — baaki sab khud hoga.
"""

import sys
import subprocess
import importlib
import logging

log = logging.getLogger(__name__)

# ── Required libraries — (import_name, pip_package_name) ──────────────────────
REQUIRED = [
    ("telegram",   "python-telegram-bot==20.7"),
    ("requests",   "requests"),
    ("dotenv",     "python-dotenv"),
]


def _is_installed(import_name: str) -> bool:
    """Check karo library import ho sakti hai ya nahi."""
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False


def _install(pip_package: str) -> bool:
    """pip se ek package install karo. True = success, False = fail."""
    print(f"  Installing {pip_package}...", end=" ", flush=True)
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", pip_package, "--quiet"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("Done!")
        return True
    else:
        print("FAILED!")
        print(f"  Error: {result.stderr.strip()[:200]}")
        return False


def setup():
    """
    Sab required libraries check karo.
    Jo missing ho unhe automatically install karo.
    Agar koi fail ho to clear error do.
    """
    missing  = []
    failed   = []

    # Step 1 — Check karo kya installed hai
    for import_name, pip_name in REQUIRED:
        if not _is_installed(import_name):
            missing.append((import_name, pip_name))

    if not missing:
        print("All libraries already installed!")
        return

    # Step 2 — Missing wale install karo
    print(f"\n{len(missing)} library(s) missing — auto-installing...\n")

    for import_name, pip_name in missing:
        success = _install(pip_name)
        if not success:
            failed.append(pip_name)

    # Step 3 — Result batao
    installed_count = len(missing) - len(failed)
    print(f"\n{installed_count}/{len(missing)} libraries install ho gayi.")

    if failed:
        print("\nYe manually install karo:")
        for pkg in failed:
            print(f"  pip install {pkg}")
        sys.exit(1)

    print("Sab ready hai — bot start ho raha hai!\n")
