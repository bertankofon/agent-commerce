"use client";
import { useState } from "react";
import { usePrivy } from "@privy-io/react-auth";

export default function WalletButton() {
  const { ready, authenticated, user, logout } = usePrivy();
  const [showModal, setShowModal] = useState(false);

  if (!ready || !authenticated || !user) {
    return null;
  }

  const walletAddress = user.wallet?.address;
  const email = user.email?.address || user.google?.email;
  const name = user.google?.name;

  return (
    <>
      {/* Wallet Button - Fixed Top Right */}
      <button
        onClick={() => setShowModal(true)}
        className="fixed top-6 right-6 z-50 group"
      >
        <div className="flex items-center gap-3 px-6 py-3 bg-black/80 backdrop-blur-md border-2 border-cyan-400/40 rounded-2xl hover:border-cyan-400 transition-all duration-300 shadow-lg shadow-cyan-400/20 hover:shadow-cyan-400/40">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center text-black font-bold text-lg">
            {name ? name[0].toUpperCase() : '👤'}
          </div>
          <div className="text-left">
            <p className="text-cyan-400 font-semibold text-sm">
              {walletAddress ? `${walletAddress.slice(0, 6)}...${walletAddress.slice(-4)}` : 'Connected'}
            </p>
            {email && (
              <p className="text-cyan-400/60 text-xs">{email}</p>
            )}
          </div>
        </div>
      </button>

      {/* Wallet Modal */}
      {showModal && (
        <div 
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm"
          onClick={() => setShowModal(false)}
        >
          <div 
            className="bg-black/95 border-2 border-cyan-400/50 rounded-3xl p-8 w-full max-w-md shadow-2xl shadow-cyan-400/30"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-cyan-300">Wallet</h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-cyan-400/60 hover:text-cyan-400 transition-colors text-2xl"
              >
                ✕
              </button>
            </div>

            {/* User Info */}
            <div className="space-y-4 mb-6">
              {/* Avatar & Name */}
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center text-black font-black text-2xl shadow-lg shadow-cyan-400/50">
                  {name ? name[0].toUpperCase() : '👤'}
                </div>
                <div>
                  {name && (
                    <p className="text-cyan-300 font-bold text-lg">{name}</p>
                  )}
                  {email && (
                    <p className="text-cyan-400/70 text-sm">{email}</p>
                  )}
                </div>
              </div>

              {/* Wallet Address */}
              <div className="bg-cyan-400/5 border border-cyan-400/20 rounded-xl p-4">
                <p className="text-cyan-400/60 text-xs mb-1 uppercase tracking-wider">Wallet Address</p>
                <p className="text-cyan-300 font-mono text-sm break-all">
                  {walletAddress}
                </p>
                <button
                  onClick={() => {
                    if (walletAddress) {
                      navigator.clipboard.writeText(walletAddress);
                    }
                  }}
                  className="mt-2 text-cyan-400/60 hover:text-cyan-400 text-xs transition-colors"
                >
                  📋 Copy Address
                </button>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-3">
              <button
                onClick={() => {
                  logout();
                  setShowModal(false);
                }}
                className="w-full px-6 py-4 bg-red-500/10 border-2 border-red-500/50 rounded-xl text-red-400 hover:bg-red-500/20 hover:border-red-500 transition-all duration-300 font-bold"
              >
                🚪 Disconnect Wallet
              </button>
              
              <button
                onClick={() => setShowModal(false)}
                className="w-full px-6 py-4 border-2 border-cyan-400/30 rounded-xl text-cyan-400 hover:border-cyan-400 transition-all duration-300 font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

