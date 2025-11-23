'use client';

export const privyConfig = {
  appearance: {
    theme: 'dark',
    accentColor: '#00ffff', // Cyan - EPOCH theme
    logo: '/favicon.ico',
  },
  loginMethods: ['email', 'google', 'wallet'] as const,
  embeddedWallets: {
    createOnLogin: 'all-users' as const,
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
};

