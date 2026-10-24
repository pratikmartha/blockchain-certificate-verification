"""
CertChain Smart Contract Deployment Utility
============================================
Deploy the CertificateVerification Solidity smart contract to:
- Local Py-EVM (in-memory test node)
- Local Ganache / Hardhat / Anvil node (http://127.0.0.1:7545 or 8545)
- Public Testnets (Sepolia, Amoy, Base Sepolia) via RPC URL + Private Key
"""

import os
import sys
import json
import time
import argparse
from web3 import Web3

# Path configurations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTRACT_PATH = os.path.join(BASE_DIR, "contracts", "CertificateVerification.sol")
COMPILED_PATH = os.path.join(BASE_DIR, "compiled_contract.json")
DETAILS_PATH = os.path.join(BASE_DIR, "contract_details.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def load_or_compile_contract(solc_version="0.8.20"):
    """Compile or load ABI and bytecode for CertificateVerification.sol"""
    if os.path.exists(COMPILED_PATH):
        try:
            with open(COMPILED_PATH, "r", encoding="utf-8") as f:
                compiled = json.load(f)
            contract_data = compiled["contracts"]["CertificateVerification.sol"]["CertificateVerification"]
            return contract_data["abi"], contract_data["evm"]["bytecode"]["object"]
        except Exception:
            pass

    print(f"[*] Compiling {CONTRACT_PATH} with py-solc-x ({solc_version})...")
    from solcx import compile_standard, install_solc, set_solc_version
    try:
        install_solc(solc_version)
        set_solc_version(solc_version)
    except Exception as e:
        print(f"[*] Solc note: {e}")

    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"CertificateVerification.sol": {"content": source}},
            "settings": {"outputSelection": {"*": {"*": ["abi", "metadata", "evm.bytecode"]}}},
        },
        solc_version=solc_version,
    )

    with open(COMPILED_PATH, "w", encoding="utf-8") as f:
        json.dump(compiled_sol, f, indent=4)

    contract_data = compiled_sol["contracts"]["CertificateVerification.sol"]["CertificateVerification"]
    return contract_data["abi"], contract_data["evm"]["bytecode"]["object"]


def update_env_file(key, value):
    """Update or append an environment variable in .env"""
    lines = []
    found = False
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"{key}={value}\n")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def deploy(rpc_url=None, private_key=None):
    print("=" * 60)
    print("  CertChain Smart Contract Deployment Engine")
    print("  Contract: CertificateVerification.sol (Solidity ^0.8.20)")
    print("=" * 60)

    # 1. Setup Web3 Provider
    w3 = None
    provider_name = ""

    if rpc_url:
        print(f"[*] Connecting to RPC Endpoint: {rpc_url}")
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
        if not w3.is_connected():
            print(f"[ERROR] Failed to connect to Ethereum node at {rpc_url}")
            sys.exit(1)
        provider_name = f"Custom RPC ({rpc_url})"
    else:
        # Check standard local ports (Ganache 7545 / 8545)
        candidates = ["http://127.0.0.1:7545", "http://127.0.0.1:8545"]
        for c in candidates:
            try:
                temp_w3 = Web3(Web3.HTTPProvider(c, request_kwargs={"timeout": 2}))
                if temp_w3.is_connected():
                    w3 = temp_w3
                    provider_name = f"Ganache Local Node ({c})"
                    print(f"[*] Connected to active local node at {c}")
                    break
            except Exception:
                pass

        if not w3:
            print("[*] No running Ganache/RPC node detected. Using embedded Py-EVM node...")
            from web3 import EthereumTesterProvider
            w3 = Web3(EthereumTesterProvider())
            provider_name = "Py-EVM Local Node (In-Memory)"

    # 2. Account determination
    deployer_account = None
    if private_key:
        if not private_key.startswith("0x") and len(private_key) == 64:
            private_key = "0x" + private_key
        acc = w3.eth.account.from_key(private_key)
        deployer_account = acc.address
        print(f"[*] Deployer Account (from Private Key): {deployer_account}")
    else:
        accounts = w3.eth.accounts
        if accounts and len(accounts) > 0:
            deployer_account = accounts[0]
            print(f"[*] Deployer Account (from node): {deployer_account}")
        else:
            acc = w3.eth.account.create()
            deployer_account = acc.address
            print(f"[*] Generated fresh account: {deployer_account}")

    # Display balance
    balance_wei = w3.eth.get_balance(deployer_account)
    balance_eth = w3.from_wei(balance_wei, "ether")
    print(f"[*] Account Balance: {balance_eth:.6f} ETH")

    if balance_wei == 0 and private_key:
        print("[WARNING] Deployer account balance is 0 ETH! The transaction will likely fail.")

    # 3. Compile or load contract
    print("[*] Loading contract ABI and bytecode...")
    abi, bytecode = load_or_compile_contract()

    # 4. Deploy contract
    print("[*] Broadcasting deployment transaction...")
    contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)

    if private_key:
        nonce = w3.eth.get_transaction_count(deployer_account)
        chain_id = w3.eth.chain_id
        tx = contract_factory.constructor().build_transaction({
            "from": deployer_account,
            "nonce": nonce,
            "gasPrice": w3.eth.gas_price,
            "chainId": chain_id
        })
        signed = w3.eth.account.sign_transaction(tx, private_key)
        raw_tx = getattr(signed, "raw_transaction", getattr(signed, "rawTransaction", None))
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
    else:
        tx_hash = contract_factory.constructor().transact({"from": deployer_account})

    tx_hash_hex = tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)
    print(f"[*] Transaction broadcasted! Tx Hash: {tx_hash_hex}")
    print("[*] Waiting for transaction receipt / block confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = receipt.contractAddress
    print(f"\n[SUCCESS] Contract deployed successfully!")
    print(f"          Contract Address : {contract_address}")
    print(f"          Block Number     : {receipt.blockNumber}")
    print(f"          Gas Used         : {receipt.gasUsed}")

    # 5. Save contract details to file
    details = {
        "address": contract_address,
        "tx_hash": tx_hash_hex,
        "block_number": receipt.blockNumber,
        "deployed_at": time.time(),
        "provider": provider_name,
        "deployer": deployer_account
    }
    with open(DETAILS_PATH, "w", encoding="utf-8") as f:
        json.dump(details, f, indent=4)
    print(f"[*] Saved deployment metadata to {DETAILS_PATH}")

    # 6. Update .env file
    update_env_file("CONTRACT_ADDRESS", contract_address)
    if rpc_url:
        update_env_file("RPC_URL", rpc_url)
    if private_key:
        update_env_file("PRIVATE_KEY", private_key)
    print(f"[*] Updated {ENV_PATH} with CONTRACT_ADDRESS={contract_address}")

    print("\nNext step: Run the web app with `python app.py` or double-click `run.bat`.")
    return details


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy CertificateVerification Smart Contract")
    parser.add_argument("--rpc", help="Ethereum RPC Endpoint (e.g. http://127.0.0.1:7545 or Sepolia URL)", default=os.environ.get("RPC_URL"))
    parser.add_argument("--key", help="Deployer Private Key (hex)", default=os.environ.get("PRIVATE_KEY"))
    args = parser.parse_args()

    deploy(rpc_url=args.rpc, private_key=args.key)
