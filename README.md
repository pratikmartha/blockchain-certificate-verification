# CertChain: Blockchain-Based Certificate Verification System

A decentralized, tamper-proof credential verification platform built on **Ethereum** using **Solidity smart contracts**, **Web3.py**, and **Flask**.

---

## 🚀 Key Features

1. **Solidity Smart Contract (`contracts/CertificateVerification.sol`)**:
   - Anchors certificates directly on the Ethereum blockchain.
   - Prevents duplicate certificate IDs (`require(!certificates[id].exists)`).
   - Instant verification via zero-gas view function `verifyCertificate(id)`.
   - Public ledger enumeration through `certificateList` and `getTotalCertificates()`.

2. **Zero-Trust Verification Engine**:
   - **By Unique ID**: Instant lookup against on-chain Ethereum state.
   - **By QR Code**: Live camera scanner or image upload to verify via smartphone or browser.
   - **By Document File (PDF / Image)**: Computes 256-bit SHA-256 hash client-side and matches with on-chain records.

3. **High-Definition Printable Digital Certificates**:
   - Official institutional layout with gold seal, signature lines, and embedded QR code.
   - Print & PDF download optimization (`@media print`).

4. **Cryptographic Tamper Demonstration Lab (`/demo/tamper`)**:
   - Interactive simulation showing what happens if someone alters a student's name, degree, or grade.
   - Demonstrates the **Avalanche Effect of SHA-256** and live smart contract rejection.

5. **Blockchain Node Flexibility**:
   - Seamlessly connects to **Ganache** (`http://127.0.0.1:7545` or `http://127.0.0.1:8545`).
   - Automatically falls back to built-in **Py-EVM local node** if Ganache is not running, so the project works out-of-the-box!

---

## 🛠️ Tech Stack

- **Smart Contract**: Solidity 0.8.20 (`solcx`)
- **Blockchain Interface**: Web3.py 8.0, Py-EVM / Ganache RPC
- **Backend**: Python 3.14, Flask 3.1
- **Database**: SQLite 3 (`database.db`)
- **Frontend**: HTML5, Tailwind CSS, Font Awesome 6, Google Fonts (Cinzel, Inter), HTML5-QRCode
- **Cryptography**: SHA-256 hashing (`hashlib` / Web Crypto API), QR Code generator (`qrcode` + `Pillow`)

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Or run `python requirment.py` to auto-check and install.)*

### 2. Run the Application
Double-click `run.bat` or run:
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 3. Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`
- **Institution**: `Metropolitan University of Technology`

---

## 📁 Project Structure

```
BlockchainCertificate/
├── contracts/
│   └── CertificateVerification.sol    # Solidity Smart Contract (0.8.20)
├── static/
│   ├── css/style.css                   # Custom styles, animations & print rules
│   ├── js/main.js                      # Clipboard, toasts, client-side SHA-256
│   └── qr_codes/                       # Generated certificate QR codes
├── templates/
│   ├── base.html                       # Base layout with navbar & live status
│   ├── index.html                      # Landing page with stats & quick search
│   ├── verify.html                     # Verification portal (ID, QR, Document)
│   ├── verify_result.html              # Verification outcome & blockchain proof
│   ├── certificate_view.html           # Official printable digital certificate
│   ├── explorer.html                   # Blockchain ledger & audit trails
│   ├── tamper_demo.html                # Interactive security simulation
│   ├── login.html                      # Institution admin login
│   ├── register.html                   # New institution registration
│   ├── admin_dashboard.html            # Admin metrics & node diagnostics
│   ├── issue_certificate.html          # Certificate issuance form
│   ├── universities.html               # Bhubaneswar, Odisha Universities & Institutes Hub
│   └── admin_certificates.html         # Repository of all issued certificates
├── app.py                              # Flask Web Application & API routes
├── blockchain.py                       # Web3 manager, Solidity compiler & deployer
├── database.py                         # SQLite database operations & auth
├── requirment.py                       # Dependency and environment verifier
├── requirements.txt                    # Python package requirements
├── run.bat                             # One-click Windows launcher
└── compiled_contract.json              # Compiled Solidity bytecode & ABI
```

---

## 🔒 Security Architecture

```
[ Certificate Details ] ---> SHA-256 Digest ---> [ Ethereum Smart Contract ]
                                                        │
                                                        ▼
[ Verifier: Uploads Doc / Enters ID ] ---> Recalculates Hash ---> Query Contract
                                                                     │
                                             ┌───────────────────────┴───────────────────────┐
                                             ▼                                               ▼
                                      [ Hash Matches ]                                [ Hash Mismatch ]
                                      ✅ Genuine & Valid                              ❌ Tampered / Fraud
```

---

## 🚀 Deployment Options

CertChain is ready to deploy across any cloud, container, or server environment. See [DEPLOYMENT.md](file:///c:/Users/PRATIK/OneDrive/Desktop/BlockchainCertificate/DEPLOYMENT.md) for full documentation.

### 🐳 1. Docker & Docker Compose (Recommended)
```bash
docker compose up -d --build
```
Access at `http://localhost:5000`. Persistent database and QR codes are mounted automatically.

### ☁️ 2. Cloud PaaS (Render / Railway / Heroku)
- **Render.com**: Connect GitHub repository; automatically detects [render.yaml](file:///c:/Users/PRATIK/OneDrive/Desktop/BlockchainCertificate/render.yaml).
- **Railway.app / Heroku**: Automatically detects [Dockerfile](file:///c:/Users/PRATIK/OneDrive/Desktop/BlockchainCertificate/Dockerfile) and [Procfile](file:///c:/Users/PRATIK/OneDrive/Desktop/BlockchainCertificate/Procfile).

### 🖥️ 3. Windows Server / Local Production
```cmd
run_prod.bat
```
Launches multi-threaded **Waitress WSGI** production server on port 5000.

