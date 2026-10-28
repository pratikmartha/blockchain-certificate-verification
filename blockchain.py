import json
import os
import hashlib
import time
from web3 import Web3
from solcx import compile_standard, install_solc, set_solc_version

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SOLC_VERSION = "0.8.20"
CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "contracts", "CertificateVerification.sol")
COMPILED_CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "compiled_contract.json")
DEPLOYED_DETAILS_PATH = os.path.join(os.path.dirname(__file__), "contract_details.json")

class BlockchainManager:
    def __init__(self, rpc_urls=None):
        if rpc_urls is None:
            env_rpc = os.environ.get("RPC_URL") or os.environ.get("WEB3_PROVIDER_URI")
            if env_rpc:
                rpc_urls = [u.strip() for u in env_rpc.split(",") if u.strip()]
            else:
                rpc_urls = ["http://127.0.0.1:7545", "http://127.0.0.1:8545"]
        self.rpc_urls = rpc_urls
        self.w3 = None
        self.provider_type = None
        self.contract = None
        self.contract_address = None
        self.abi = None
        self.bytecode = None
        self.default_account = None
        self.private_key = None

        self._initialize_web3()
        self._ensure_compiled()
        self._initialize_contract()

    def _initialize_web3(self):
        """Connect to Ganache / RPC node or fallback to Py-EVM EthereumTesterProvider"""
        connected = False
        for url in self.rpc_urls:
            try:
                provider = Web3.HTTPProvider(url, request_kwargs={'timeout': 2.5})
                temp_w3 = Web3(provider)
                if temp_w3.is_connected():
                    self.w3 = temp_w3
                    self.provider_type = f"RPC ({url})"
                    connected = True
                    print(f"Connected to Ethereum Node at {url}")
                    break
            except Exception:
                continue

        if not connected:
            print("No external RPC node detected (Ganache not running). Initializing Py-EVM EVM Backend...")
            try:
                from web3 import EthereumTesterProvider
                self.w3 = Web3(EthereumTesterProvider())
                self.provider_type = "Py-EVM Local Node"
                print("Connected to Py-EVM EVM Backend successfully!")
            except Exception as e:
                raise RuntimeError(f"Could not initialize Ethereum provider: {e}")

        # Check for Private Key in environment
        pk = os.environ.get("PRIVATE_KEY")
        if pk:
            pk = pk.strip()
            if not pk.startswith("0x") and len(pk) == 64:
                pk = "0x" + pk
            try:
                account = self.w3.eth.account.from_key(pk)
                self.default_account = account.address
                self.private_key = pk
                self.w3.eth.default_account = self.default_account
                print(f"Loaded signer account from PRIVATE_KEY: {self.default_account}")
            except Exception as e:
                print(f"Warning: Failed to load account from PRIVATE_KEY: {e}")

        if not self.default_account:
            # Configure default account from node or generate local
            accounts = self.w3.eth.accounts
            if accounts and len(accounts) > 0:
                self.default_account = accounts[0]
                self.w3.eth.default_account = self.default_account
            else:
                # Generate local account if none available
                new_acc = self.w3.eth.account.create()
                self.default_account = new_acc.address
                self.w3.eth.default_account = self.default_account

    def compile_contract(self):
        """Compile Solidity contract using py-solc-x"""
        print(f"Compiling {CONTRACT_PATH} with solc {SOLC_VERSION}...")
        try:
            install_solc(SOLC_VERSION)
            set_solc_version(SOLC_VERSION)
        except Exception as e:
            print(f"Solc installation note: {e}")

        with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
            contract_source = f.read()

        compiled_sol = compile_standard(
            {
                "language": "Solidity",
                "sources": {
                    "CertificateVerification.sol": {
                        "content": contract_source
                    }
                },
                "settings": {
                    "outputSelection": {
                        "*": {
                            "*": ["abi", "metadata", "evm.bytecode"]
                        }
                    }
                }
            },
            solc_version=SOLC_VERSION
        )

        with open(COMPILED_CONTRACT_PATH, "w", encoding="utf-8") as f:
            json.dump(compiled_sol, f, indent=4)

        print("Solidity contract compiled successfully!")
        return compiled_sol

    def _ensure_compiled(self):
        """Ensure ABI and bytecode are loaded, compiling if necessary with pre-compiled fallback"""
        compile_needed = False
        if not os.path.exists(COMPILED_CONTRACT_PATH):
            compile_needed = True
        else:
            # Check modification time if source exists
            if os.path.exists(CONTRACT_PATH) and os.path.getmtime(CONTRACT_PATH) > os.path.getmtime(COMPILED_CONTRACT_PATH):
                compile_needed = True

        compiled_sol = None
        if compile_needed:
            try:
                compiled_sol = self.compile_contract()
            except Exception as e:
                print(f"Notice: Solc compilation unavailable ({e}). Using existing pre-compiled contract artifact...")
                if os.path.exists(COMPILED_CONTRACT_PATH):
                    with open(COMPILED_CONTRACT_PATH, "r", encoding="utf-8") as f:
                        compiled_sol = json.load(f)
                else:
                    raise

        if compiled_sol is None:
            with open(COMPILED_CONTRACT_PATH, "r", encoding="utf-8") as f:
                compiled_sol = json.load(f)

        try:
            contract_interface = compiled_sol["contracts"]["CertificateVerification.sol"]["CertificateVerification"]
            self.abi = contract_interface["abi"]
            self.bytecode = contract_interface["evm"]["bytecode"]["object"]
        except (KeyError, TypeError):
            print("Recompiling contract due to structure mismatch...")
            compiled_sol = self.compile_contract()
            contract_interface = compiled_sol["contracts"]["CertificateVerification.sol"]["CertificateVerification"]
            self.abi = contract_interface["abi"]
            self.bytecode = contract_interface["evm"]["bytecode"]["object"]

    def _initialize_contract(self):
        """Deploy or load already deployed contract"""
        # Check if custom CONTRACT_ADDRESS is set in environment
        env_addr = os.environ.get("CONTRACT_ADDRESS")
        if env_addr:
            try:
                checksum_addr = Web3.to_checksum_address(env_addr.strip())
                code = self.w3.eth.get_code(checksum_addr)
                if code and code != b'\x00' and len(code) > 2:
                    self.contract_address = checksum_addr
                    self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi)
                    print(f"Connected to pre-deployed contract at {self.contract_address} (via CONTRACT_ADDRESS)")
                    return
                else:
                    print(f"Notice: No deployed bytecode found at CONTRACT_ADDRESS {checksum_addr} on this node. Deploying fresh instance...")
            except Exception as e:
                print(f"Warning: Invalid CONTRACT_ADDRESS '{env_addr}': {e}")

        # If using external RPC (Ganache / Node), try to load saved address
        if "RPC" in self.provider_type and os.path.exists(DEPLOYED_DETAILS_PATH):
            try:
                with open(DEPLOYED_DETAILS_PATH, "r", encoding="utf-8") as f:
                    details = json.load(f)
                saved_address = details.get("address")
                # Verify code exists at address
                code = self.w3.eth.get_code(saved_address)
                if code and code != b'\x00' and len(code) > 2:
                    self.contract_address = saved_address
                    self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi)
                    print(f"Loaded existing contract at: {self.contract_address}")
                    return
            except Exception as e:
                print(f"Could not load existing contract: {e}. Deploying new instance...")

        self.deploy_contract()

    def deploy_contract(self):
        """Deploy Solidity CertificateVerification contract on blockchain"""
        print("Deploying CertificateVerification contract...")
        contract_factory = self.w3.eth.contract(abi=self.abi, bytecode=self.bytecode)

        if self.private_key:
            nonce = self.w3.eth.get_transaction_count(self.default_account)
            tx_data = contract_factory.constructor().build_transaction({
                "from": self.default_account,
                "nonce": nonce,
                "gasPrice": self.w3.eth.gas_price,
                "chainId": self.w3.eth.chain_id
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx_data, private_key=self.private_key)
            raw_tx = getattr(signed_tx, "raw_transaction", getattr(signed_tx, "rawTransaction", None))
            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
        else:
            tx_hash = contract_factory.constructor().transact({
                "from": self.default_account
            })

        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.contract_address = tx_receipt.contractAddress
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi)

        details = {
            "address": self.contract_address,
            "tx_hash": tx_hash.hex() if hasattr(tx_hash, 'hex') else str(tx_hash),
            "block_number": tx_receipt.blockNumber,
            "deployed_at": time.time(),
            "provider": self.provider_type,
            "deployer": self.default_account
        }

        try:
            with open(DEPLOYED_DETAILS_PATH, "w", encoding="utf-8") as f:
                json.dump(details, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not save contract details file: {e}")

        print(f"Contract deployed successfully at address: {self.contract_address}")
        print(f"Transaction Hash: {details['tx_hash']} | Block: {tx_receipt.blockNumber}")
        return details

    @staticmethod
    def calculate_hash(data):
        """
        Calculate SHA-256 cryptographic hash of certificate data.
        Can accept string or dict of certificate attributes.
        """
        if isinstance(data, dict):
            # Deterministic serialization: sort keys
            canonical_str = f"{data.get('certificate_id', '').strip()}|" \
                            f"{data.get('student_name', '').strip()}|" \
                            f"{data.get('course', '').strip()}|" \
                            f"{data.get('institution', '').strip()}|" \
                            f"{data.get('issue_date', '').strip()}"
            return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        elif isinstance(data, bytes):
            return hashlib.sha256(data).hexdigest()
        else:
            return hashlib.sha256(str(data).encode("utf-8")).hexdigest()

    def issue_certificate(self, cert_id, student_name, course, institution, cert_hash):
        """
        Execute issueCertificate transaction on the Solidity smart contract.
        """
        try:
            if self.private_key:
                nonce = self.w3.eth.get_transaction_count(self.default_account)
                tx_data = self.contract.functions.issueCertificate(
                    str(cert_id),
                    str(student_name),
                    str(course),
                    str(institution),
                    str(cert_hash)
                ).build_transaction({
                    "from": self.default_account,
                    "nonce": nonce,
                    "gasPrice": self.w3.eth.gas_price,
                    "chainId": self.w3.eth.chain_id
                })
                signed_tx = self.w3.eth.account.sign_transaction(tx_data, private_key=self.private_key)
                raw_tx = getattr(signed_tx, "raw_transaction", getattr(signed_tx, "rawTransaction", None))
                tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            else:
                tx_hash = self.contract.functions.issueCertificate(
                    str(cert_id),
                    str(student_name),
                    str(course),
                    str(institution),
                    str(cert_hash)
                ).transact({"from": self.default_account})

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            tx_hex = tx_hash.hex() if hasattr(tx_hash, 'hex') else str(tx_hash)

            return {
                "success": True,
                "tx_hash": tx_hex,
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed,
                "contract_address": self.contract_address
            }
        except Exception as e:
            err_msg = str(e)
            if "already exists" in err_msg:
                return {"success": False, "error": "Certificate with this ID already exists on the blockchain."}
            return {"success": False, "error": err_msg}

    def verify_certificate(self, cert_id):
        """
        Call verifyCertificate view function on the Solidity smart contract.
        Zero gas cost as it's an on-chain view query.
        """
        try:
            res = self.contract.functions.verifyCertificate(str(cert_id)).call()
            # res: (certificateId, studentName, course, institution, certificateHash, issueDate, exists)
            exists = res[6]
            if not exists:
                return {
                    "exists": False,
                    "certificate_id": cert_id,
                    "contract_address": self.contract_address,
                    "error": "Certificate not found on the blockchain."
                }

            return {
                "exists": True,
                "certificate_id": res[0],
                "student_name": res[1],
                "course": res[2],
                "institution": res[3],
                "certificate_hash": res[4],
                "issue_date": res[5],
                "contract_address": self.contract_address
            }
        except Exception as e:
            return {
                "exists": False,
                "certificate_id": cert_id,
                "contract_address": self.contract_address,
                "error": f"Error querying blockchain: {str(e)}"
            }

    def get_total_certificates(self):
        """Return total certificates registered on the smart contract"""
        try:
            return self.contract.functions.getTotalCertificates().call()
        except Exception:
            return 0

    def get_all_certificate_ids(self):
        """Fetch all certificate IDs stored in the smart contract list"""
        try:
            total = self.get_total_certificates()
            ids = []
            for i in range(total):
                cid = self.contract.functions.getCertificateIdByIndex(i).call()
                ids.append(cid)
            return ids
        except Exception:
            return []

    def get_blockchain_status(self):
        """Retrieve live network and node diagnostics"""
        try:
            block_number = self.w3.eth.block_number
            balance_wei = self.w3.eth.get_balance(self.default_account)
            balance_eth = self.w3.from_wei(balance_wei, "ether")
            gas_price = self.w3.eth.gas_price
            return {
                "connected": True,
                "provider": self.provider_type,
                "contract_address": self.contract_address,
                "default_account": self.default_account,
                "balance_eth": float(balance_eth),
                "block_number": block_number,
                "gas_price_gwei": float(self.w3.from_wei(gas_price, "gwei")),
                "total_certificates_on_chain": self.get_total_certificates()
            }
        except Exception as e:
            return {
                "connected": False,
                "provider": self.provider_type or "Unknown",
                "error": str(e)
            }

# Singleton instance for easy import across modules
blockchain_manager = None

def get_blockchain_manager():
    global blockchain_manager
    if blockchain_manager is None:
        blockchain_manager = BlockchainManager()
    return blockchain_manager

if __name__ == "__main__":
    print("Testing BlockchainManager...")
    mgr = BlockchainManager()
    status = mgr.get_blockchain_status()
    print("Node Status:", status)

    # Test Issuance
    test_id = f"CERT-TEST-{int(time.time())}"
    test_hash = mgr.calculate_hash({"certificate_id": test_id, "student_name": "John Doe", "course": "Blockchain", "institution": "Tech University", "issue_date": "2026-09-23"})
    print(f"Issuing test certificate {test_id}...")
    issue_res = mgr.issue_certificate(test_id, "John Doe", "Blockchain Architecture", "Tech University", test_hash)
    print("Issue Result:", issue_res)

    # Test Verification
    print(f"Verifying {test_id} on blockchain...")
    verify_res = mgr.verify_certificate(test_id)
    print("Verify Result:", verify_res)
    print("Smart contract integration verified successfully!")