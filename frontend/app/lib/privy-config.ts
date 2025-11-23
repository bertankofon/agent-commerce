'use client';

export const privyConfig = {
  appearance: {
    theme: 'dark',
    accentColor: '#00ffff', // Cyan - EPOCH theme
    logo: '/favicon.ico',
  },
  // Enable multiple login methods
  // Note: 'wallet' enables all external wallets (MetaMask, Coinbase, WalletConnect, Rainbow, etc.)
  loginMethods: ['email', 'google', 'wallet'] as const,
  embeddedWallets: {
    createOnLogin: 'all-users' as const,
  },
  // This enables all external wallet providers
  externalWallets: {
    coinbaseWallet: {
      connectionOptions: 'all',
    },
  },
  defaultChain: {
    id: 84532,
    name: 'Base Sepolia',
    network: 'base-sepolia',
    nativeCurrency: {
      decimals: 18,
      name: 'Ether',
      symbol: 'ETH',
    },
    rpcUrls: {
      default: {
        http: ['https://sepolia.base.org'],
      },
      public: {
        http: ['https://sepolia.base.org'],
      },
    },
    blockExplorers: {
      default: {
        name: 'BaseScan',
        url: 'https://sepolia.basescan.org',
      },
    },
  },
  // Disable Solana support - only use EVM/Base Sepolia
  solana: {
    enabled: false,
  },
};
