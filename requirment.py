"""
Environment and dependency verifier for Blockchain Certificate Verification System.
Run: python requirment.py
"""

import sys
import subprocess

REQUIRED_PACKAGES = [
    ("flask", "Flask"),
    ("web3", "web3"),
    ("solcx", "py-solc-x"),
    ("eth_tester", "eth-tester"),
    ("eth", "py-evm"),
    ("qrcode", "qrcode"),
    ("Crypto", "pycryptodome"),
]

def check_and_install():
    print("=" * 60)
    print("Checking dependencies for Blockchain Certificate System...")
    print("=" * 60)
    all_ok = True
    for mod_name, pkg_name in REQUIRED_PACKAGES:
        try:
            __import__(mod_name)
            print(f"[OK] {pkg_name} is installed.")
        except ImportError:
            print(f"[MISSING] {pkg_name} is missing. Installing...")
            all_ok = False
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])
                print(f"[INSTALLED] Successfully installed {pkg_name}")
            except Exception as e:
                print(f"[ERROR] Failed to install {pkg_name}: {e}")

    print("\nEnvironment check complete!")
    if all_ok:
        print("All required packages are installed and ready to run.")
    else:
        print("Packages updated. You can now launch: python app.py")

if __name__ == "__main__":
    check_and_install()
