/**
 * CertChain MetaMask & Web3 Provider Module
 * Handles Ethereum wallet connection, account switching, network detection,
 * and gating for certificate issuance and verification.
 */

(function () {
    const NETWORKS = {
        '0x1': { name: 'Ethereum Mainnet', explorer: 'https://etherscan.io' },
        '0xaa36a7': { name: 'Sepolia Testnet', explorer: 'https://sepolia.etherscan.io' },
        '0x4268': { name: 'Holesky Testnet', explorer: 'https://holesky.etherscan.io' },
        '0x89': { name: 'Polygon PoS', explorer: 'https://polygonscan.com' },
        '0x13882': { name: 'Polygon Amoy', explorer: 'https://amoy.polygonscan.com' },
        '0xa4b1': { name: 'Arbitrum One', explorer: 'https://arbiscan.io' },
        '0xa': { name: 'Optimism Mainnet', explorer: 'https://optimistic.etherscan.io' },
        '0x539': { name: 'Ganache Local (1337)', explorer: '' },
        '0x7a69': { name: 'Hardhat / Anvil (31337)', explorer: '' }
    };

    const state = {
        account: null,
        chainId: null,
        balance: '0.0000',
        isConnected: false
    };

    function isMetaMaskInstalled() {
        return typeof window.ethereum !== 'undefined' && Boolean(window.ethereum.isMetaMask);
    }

    function formatAddress(addr) {
        if (!addr) return '';
        return `${addr.substring(0, 6)}...${addr.substring(addr.length - 4)}`;
    }

    function getNetworkName(chainId) {
        if (!chainId) return 'Unknown Network';
        const net = NETWORKS[chainId.toLowerCase()];
        return net ? net.name : `Chain ${parseInt(chainId, 16) || chainId}`;
    }

    function getExplorerUrl(chainId, address) {
        if (!chainId || !address) return '#';
        const net = NETWORKS[chainId.toLowerCase()];
        if (net && net.explorer) {
            return `${net.explorer}/address/${address}`;
        }
        return `https://etherscan.io/address/${address}`;
    }

    async function fetchAccountBalance(account) {
        try {
            if (!window.ethereum || !account) return '0.0000';
            const balHex = await window.ethereum.request({
                method: 'eth_getBalance',
                params: [account, 'latest']
            });
            const wei = BigInt(balHex);
            const eth = Number(wei) / 1e18;
            return eth.toFixed(4);
        } catch (err) {
            console.warn('Failed to fetch balance:', err);
            return '0.0000';
        }
    }

    async function updateState(account, chainId) {
        state.account = account || null;
        state.chainId = chainId || null;
        state.isConnected = Boolean(account);

        if (state.isConnected) {
            state.balance = await fetchAccountBalance(account);
            localStorage.setItem('certchain_metamask_connected', 'true');
        } else {
            state.balance = '0.0000';
            localStorage.removeItem('certchain_metamask_connected');
        }

        renderUI();
        window.dispatchEvent(new CustomEvent('certchain:wallet_changed', { detail: { ...state } }));
    }

    async function connectWallet() {
        if (!isMetaMaskInstalled()) {
            showInstallModal();
            return null;
        }

        try {
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });

            const chainId = await window.ethereum.request({
                method: 'eth_chainId'
            });

            if (accounts && accounts.length > 0) {
                await updateState(accounts[0], chainId);
                showToast(`MetaMask Connected: ${formatAddress(accounts[0])}`);
                return accounts[0];
            }
        } catch (error) {
            console.error('MetaMask connection error:', error);
            if (error.code === 4001) {
                showToast('Connection request was rejected in MetaMask.', 'error');
            } else {
                showToast(`MetaMask error: ${error.message || 'Failed to connect'}`, 'error');
            }
        }
        return null;
    }

    async function disconnectWallet() {
        await updateState(null, null);
        showToast('MetaMask disconnected from CertChain.');
        closeWalletModal();
    }

    async function checkExistingConnection() {
        if (!isMetaMaskInstalled()) return;

        const shouldReconnect = localStorage.getItem('certchain_metamask_connected') === 'true';

        try {
            const accounts = await window.ethereum.request({ method: 'eth_accounts' });
            const chainId = await window.ethereum.request({ method: 'eth_chainId' });

            if (accounts && accounts.length > 0 && shouldReconnect) {
                await updateState(accounts[0], chainId);
            }
        } catch (err) {
            console.warn('Silent reconnect check failed:', err);
        }
    }

    function setupEventListeners() {
        if (!isMetaMaskInstalled()) return;

        window.ethereum.on('accountsChanged', async (accounts) => {
            if (accounts.length === 0) {
                await updateState(null, null);
            } else {
                const chainId = await window.ethereum.request({ method: 'eth_chainId' });
                await updateState(accounts[0], chainId);
                showToast(`Switched account to ${formatAddress(accounts[0])}`);
            }
        });

        window.ethereum.on('chainChanged', async (chainId) => {
            const accounts = await window.ethereum.request({ method: 'eth_accounts' });
            await updateState(accounts[0] || null, chainId);
            showToast(`Switched network to ${getNetworkName(chainId)}`);
        });
    }

    function renderUI() {
        const navBtn = document.getElementById('metamask-connect-btn');
        const hiddenIssuerWallet = document.getElementById('issuer_wallet');

        if (hiddenIssuerWallet) {
            hiddenIssuerWallet.value = state.account || '';
        }

        // 1. Navigation Button
        if (navBtn) {
            if (state.isConnected) {
                navBtn.innerHTML = `
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-2"></span>
                    <span class="mr-1.5 text-base leading-none">🦊</span>
                    <span class="font-mono text-xs font-semibold text-white">${formatAddress(state.account)}</span>
                    <i class="fa-solid fa-chevron-down ml-2 text-[10px] text-slate-400"></i>
                `;
                navBtn.className = "px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-slate-200 text-xs font-medium flex items-center transition shadow-sm cursor-pointer";
                navBtn.onclick = toggleWalletModal;
            } else {
                navBtn.innerHTML = `
                    <span class="mr-1.5 text-base leading-none">🦊</span>
                    <span class="font-medium text-xs">Connect MetaMask</span>
                `;
                navBtn.className = "px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-amber-500/20 via-orange-500/20 to-amber-600/20 hover:from-amber-500/30 hover:to-orange-500/30 border border-amber-500/40 text-amber-300 hover:text-white text-xs font-medium flex items-center transition shadow-md shadow-amber-500/10 cursor-pointer";
                navBtn.onclick = connectWallet;
            }
        }

        // 2. Global text updates
        document.querySelectorAll('.metamask-account-formatted').forEach(el => {
            el.textContent = state.isConnected ? formatAddress(state.account) : 'Not Connected';
        });
        document.querySelectorAll('.metamask-account-full').forEach(el => {
            el.textContent = state.isConnected ? state.account : '';
        });
        document.querySelectorAll('.metamask-network-text').forEach(el => {
            el.textContent = state.isConnected ? getNetworkName(state.chainId) : 'No Network';
        });
        document.querySelectorAll('.metamask-balance-text').forEach(el => {
            el.textContent = state.isConnected ? `${state.balance} ETH` : '0.0000 ETH';
        });

        // 3. Issue Certificate Page Banner / Gating
        const issueGate = document.getElementById('issue-metamask-banner');
        const issueSubmitBtn = document.getElementById('submitBtn');
        if (issueGate) {
            if (state.isConnected) {
                issueGate.innerHTML = `
                    <div class="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div class="flex items-center space-x-3">
                            <div class="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-400 text-lg">
                                <i class="fa-solid fa-shield-check"></i>
                            </div>
                            <div>
                                <div class="flex items-center space-x-2">
                                    <span class="text-xs font-bold uppercase tracking-wider text-emerald-300">Authorized MetaMask Issuer Linked</span>
                                    <span class="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-mono">${getNetworkName(state.chainId)}</span>
                                </div>
                                <div class="text-xs font-mono text-slate-300 mt-0.5">
                                    Signer: <span class="text-white font-bold">${state.account}</span>
                                </div>
                            </div>
                        </div>
                        <div class="text-xs text-slate-400 flex items-center space-x-2">
                            <span>Balance: <strong class="text-white font-mono">${state.balance} ETH</strong></span>
                        </div>
                    </div>
                `;
                if (issueSubmitBtn) {
                    issueSubmitBtn.classList.remove('opacity-60');
                }
            } else {
                issueGate.innerHTML = `
                    <div class="p-5 rounded-2xl bg-gradient-to-r from-amber-950/60 via-slate-900 to-amber-950/40 border border-amber-500/40 text-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
                        <div class="flex items-center space-x-3">
                            <div class="w-11 h-11 rounded-2xl bg-amber-500/20 flex items-center justify-center text-amber-400 text-2xl shrink-0">
                                🦊
                            </div>
                            <div>
                                <h4 class="text-sm font-bold text-white flex items-center">
                                    MetaMask Account Required to Issue Certificate
                                    <span class="ml-2 px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-[10px] uppercase tracking-wider font-semibold">Web3 Gated</span>
                                </h4>
                                <p class="text-xs text-slate-300 mt-0.5">
                                    Connect your institution's MetaMask wallet to authenticate as the authorized issuer and anchor this credential into Ethereum.
                                </p>
                            </div>
                        </div>
                        <button type="button" onclick="window.CertChainMetaMask.connect()" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition flex items-center justify-center shrink-0">
                            <span class="mr-2 text-base">🦊</span>
                            <span>Connect MetaMask</span>
                        </button>
                    </div>
                `;
            }
        }

        // 4. Admin Dashboard Card / Widget
        const dashMetaMaskWidget = document.getElementById('dashboard-metamask-card');
        if (dashMetaMaskWidget) {
            if (state.isConnected) {
                dashMetaMaskWidget.innerHTML = `
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950 border border-emerald-500/30">
                        <div class="flex items-center space-x-3.5">
                            <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-2xl shrink-0">
                                🦊
                            </div>
                            <div>
                                <div class="flex items-center space-x-2">
                                    <span class="text-xs uppercase font-bold text-emerald-400 tracking-wider flex items-center">
                                        <span class="w-2 h-2 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
                                        MetaMask Linked
                                    </span>
                                    <span class="text-slate-600">|</span>
                                    <span class="text-xs text-slate-400 font-mono">${getNetworkName(state.chainId)}</span>
                                </div>
                                <div class="font-mono text-sm font-bold text-white mt-0.5 flex items-center space-x-2">
                                    <span>${state.account}</span>
                                    <button onclick="copyToClipboard('${state.account}', 'Wallet address copied!')" class="text-slate-400 hover:text-indigo-400 transition" title="Copy Address">
                                        <i class="fa-regular fa-copy text-xs"></i>
                                    </button>
                                </div>
                                <div class="text-xs text-slate-400 mt-1">
                                    Available Balance: <span class="font-mono text-slate-200 font-semibold">${state.balance} ETH</span>
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2 self-start sm:self-center">
                            <a href="${getExplorerUrl(state.chainId, state.account)}" target="_blank" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition flex items-center">
                                <i class="fa-solid fa-arrow-up-right-from-square mr-1.5 text-[10px]"></i> Explorer
                            </a>
                            <button onclick="window.CertChainMetaMask.disconnect()" class="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-xs font-medium transition">
                                Disconnect
                            </button>
                        </div>
                    </div>
                `;
            } else {
                dashMetaMaskWidget.innerHTML = `
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-amber-950/30 via-slate-900 to-indigo-950/30 border border-amber-500/30">
                        <div class="flex items-center space-x-3.5">
                            <div class="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-2xl shrink-0">
                                🦊
                            </div>
                            <div>
                                <div class="text-xs uppercase font-bold text-amber-400 tracking-wider">
                                    Action Required: Connect MetaMask Account
                                </div>
                                <p class="text-xs text-slate-300 mt-1 max-w-xl leading-relaxed">
                                    Connect your institution's MetaMask wallet to issue tamper-proof certificates and sign on-chain transactions directly with your cryptographic key.
                                </p>
                            </div>
                        </div>
                        <button type="button" onclick="window.CertChainMetaMask.connect()" class="px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition flex items-center justify-center shrink-0">
                            <span class="mr-2 text-base">🦊</span>
                            <span>Connect MetaMask</span>
                        </button>
                    </div>
                `;
            }
        }

        // 5. Verify Page Banner
        const verifyMetaMaskBanner = document.getElementById('verify-metamask-banner');
        if (verifyMetaMaskBanner) {
            if (state.isConnected) {
                verifyMetaMaskBanner.innerHTML = `
                    <div class="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-700/80 flex items-center justify-between text-xs">
                        <div class="flex items-center space-x-2.5">
                            <span class="text-base">🦊</span>
                            <span class="text-slate-400">Verifying as:</span>
                            <span class="font-mono text-emerald-400 font-semibold">${formatAddress(state.account)}</span>
                            <span class="px-2 py-0.5 rounded-full bg-slate-800 text-[10px] text-slate-400 font-mono">${getNetworkName(state.chainId)}</span>
                        </div>
                        <button onclick="window.CertChainMetaMask.disconnect()" class="text-slate-400 hover:text-rose-400 transition text-[11px]">
                            Disconnect
                        </button>
                    </div>
                `;
            } else {
                verifyMetaMaskBanner.innerHTML = `
                    <div class="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                        <div class="flex items-center space-x-2.5">
                            <span class="text-base">🦊</span>
                            <span class="text-slate-400">Optional: Connect MetaMask to sign verification proofs and view on-chain history</span>
                        </div>
                        <button onclick="window.CertChainMetaMask.connect()" class="text-amber-400 hover:text-amber-300 font-semibold text-xs transition flex items-center">
                            <span>Connect</span> <i class="fa-solid fa-arrow-right ml-1 text-[10px]"></i>
                        </button>
                    </div>
                `;
            }
        }

        // 6. Update modal details if open
        const modalAccount = document.getElementById('metamask-modal-account');
        const modalNetwork = document.getElementById('metamask-modal-network');
        const modalBalance = document.getElementById('metamask-modal-balance');
        const modalExplorerLink = document.getElementById('metamask-modal-explorer');

        if (modalAccount) modalAccount.textContent = state.account || '';
        if (modalNetwork) modalNetwork.textContent = getNetworkName(state.chainId);
        if (modalBalance) modalBalance.textContent = `${state.balance} ETH`;
        if (modalExplorerLink) modalExplorerLink.href = getExplorerUrl(state.chainId, state.account);
    }

    function toggleWalletModal() {
        const modal = document.getElementById('metamask-wallet-modal');
        if (!modal) return;
        if (modal.classList.contains('hidden')) {
            modal.classList.remove('hidden');
        } else {
            modal.classList.add('hidden');
        }
    }

    function closeWalletModal() {
        const modal = document.getElementById('metamask-wallet-modal');
        if (modal) modal.classList.add('hidden');
    }

    function showInstallModal() {
        const existing = document.getElementById('metamask-install-modal');
        if (existing) existing.remove();

        const modal = document.createElement('div');
        modal.id = 'metamask-install-modal';
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in';
        modal.innerHTML = `
            <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl relative text-center">
                <button onclick="this.closest('#metamask-install-modal').remove()" class="absolute top-5 right-5 text-slate-400 hover:text-white transition">
                    <i class="fa-solid fa-xmark text-lg"></i>
                </button>
                <div class="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-4xl mx-auto mb-4">
                    🦊
                </div>
                <h3 class="text-xl font-bold text-white mb-2">MetaMask Not Detected</h3>
                <p class="text-xs text-slate-300 leading-relaxed mb-6">
                    To connect your Ethereum wallet and interact with the CertChain smart contract, you need the MetaMask browser extension.
                </p>
                <div class="space-y-3">
                    <a href="https://metamask.io/download/" target="_blank" rel="noopener noreferrer"
                       class="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-bold text-sm shadow-lg shadow-amber-500/20 transition flex items-center justify-center">
                        <i class="fa-solid fa-download mr-2"></i> Download & Install MetaMask
                    </a>
                    <button onclick="this.closest('#metamask-install-modal').remove()"
                            class="w-full py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition">
                        Close
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    // Initialize on DOM load
    document.addEventListener('DOMContentLoaded', () => {
        checkExistingConnection();
        setupEventListeners();

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const modal = document.getElementById('metamask-wallet-modal');
            const navBtn = document.getElementById('metamask-connect-btn');
            if (modal && !modal.classList.contains('hidden')) {
                if (!modal.contains(e.target) && navBtn && !navBtn.contains(e.target)) {
                    closeWalletModal();
                }
            }
        });
    });

    // Expose Global Public API
    window.CertChainMetaMask = {
        connect: connectWallet,
        disconnect: disconnectWallet,
        getState: () => ({ ...state }),
        isInstalled: isMetaMaskInstalled,
        formatAddress: formatAddress,
        toggleWalletModal: toggleWalletModal,
        closeWalletModal: closeWalletModal,
        requireConnection: async function (callback) {
            if (state.isConnected) {
                if (callback) callback(state.account);
                return true;
            }
            const acc = await connectWallet();
            if (acc && callback) {
                callback(acc);
                return true;
            }
            return false;
        }
    };
})();
