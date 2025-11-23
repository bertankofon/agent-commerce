"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getNegotiation } from "../../lib/api";
import type { Negotiation } from "../../lib/types";

export default function NegotiationViewer() {
  const params = useParams();
  const [negotiation, setNegotiation] = useState<Negotiation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNegotiation();
    const interval = setInterval(loadNegotiation, 1000);
    return () => clearInterval(interval);
  }, [params.id]);

  async function loadNegotiation() {
    try {
      const data = await getNegotiation(params.id as string);
      setNegotiation(data);
      setLoading(false);
    } catch (error) {
      setLoading(false);
    }
  }

  if (loading || !negotiation) {
    return (
      <div className="min-h-screen bg-[#5A7EDC] flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  const isComplete = negotiation.status === "completed";
  const isActive = negotiation.status === "in_progress";

  return (
    <div className="min-h-screen bg-[#5A7EDC] p-8">
      <div className="max-w-5xl mx-auto">
        {/* XP Window */}
        <div className="bg-white rounded-lg shadow-2xl overflow-hidden" style={{ border: '3px solid #0831D9' }}>
          {/* Title Bar */}
          <div className="bg-gradient-to-r from-[#0831D9] to-[#3165F0] px-3 py-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-white rounded-sm"></div>
              <span className="text-white font-bold text-sm">Live Negotiation</span>
            </div>
            <div className="flex gap-1">
              <button className="w-5 h-5 bg-[#2E6EE6] border border-white flex items-center justify-center text-white text-xs">_</button>
              <button className="w-5 h-5 bg-[#2E6EE6] border border-white flex items-center justify-center text-white text-xs">□</button>
              <Link href="/dashboard">
                <button className="w-5 h-5 bg-[#D93831] border border-white flex items-center justify-center text-white text-xs">×</button>
              </Link>
            </div>
          </div>

          {/* Menu Bar */}
          <div className="bg-gradient-to-b from-[#F1F3FD] to-[#D9E4F5] border-b border-[#9CB0D7] px-2 py-1">
            <div className="text-sm font-bold text-gray-700">
              {negotiation.client_name || "Buyer"} ↔ {negotiation.merchant_name || "Seller"}
            </div>
          </div>

          {/* Content */}
          <div className="p-6 bg-gradient-to-b from-[#ECE9D8] to-[#D6D3C9]">
            {/* Status */}
            <div className={`border-2 rounded p-6 mb-6 ${
              isComplete ? "bg-[#E0FFE0]" : isActive ? "bg-[#FFFACD]" : "bg-[#FFE0E0]"
            }`} style={{ borderColor: isComplete ? '#128C12' : isActive ? '#FF8C00' : '#D93831' }}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold mb-1">STATUS</div>
                  <div className="text-3xl font-bold">
                    {negotiation.status.toUpperCase().replace('_', ' ')}
                  </div>
                </div>
                {isComplete && negotiation.final_price && (
                  <div className="text-right">
                    <div className="text-xs font-bold mb-1">FINAL PRICE</div>
                    <div className="text-3xl font-bold text-[#128C12]">
                      ${negotiation.final_price}
                    </div>
                  </div>
                )}
                {isActive && (
                  <div className="w-16 h-16 bg-[#FF8C00] rounded animate-pulse"></div>
                )}
              </div>
            </div>

            {/* Rounds */}
            <div className="space-y-3 mb-6">
              {negotiation.rounds && negotiation.rounds.length > 0 ? (
                negotiation.rounds.map((round, idx) => (
                  <div
                    key={idx}
                    className={`bg-gradient-to-b from-[#D4D0C8] to-[#B8B4AC] border-2 rounded p-4 ${
                      round.speaker === "merchant" ? "ml-12" : "mr-12"
                    }`}
                    style={{ borderColor: '#FFFFFF #404040 #404040 #FFFFFF' }}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-bold text-sm">
                          {round.speaker === "merchant" ? "🏪 SELLER" : "🛒 BUYER"}
                        </div>
                        <div className="text-xs text-gray-600">Round {round.round}</div>
                      </div>
                      {round.price && (
                        <div className="bg-white border-2 px-3 py-1 rounded" style={{ borderColor: '#0831D9' }}>
                          <div className="text-xs font-bold">OFFER</div>
                          <div className="text-lg font-bold text-[#0831D9]">${round.price}</div>
                        </div>
                      )}
                    </div>
                    <div className="text-sm">{round.message}</div>
                  </div>
                ))
              ) : (
                <div className="bg-white border-2 rounded p-8 text-center" style={{ borderColor: '#0831D9' }}>
                  <div className="text-gray-500">Waiting for negotiation...</div>
                </div>
              )}

              {/* Loading */}
              {isActive && (
                <div className="bg-white border-2 rounded p-6 text-center" style={{ borderColor: '#FF8C00' }}>
                  <div className="text-4xl mb-2">⏳</div>
                  <div className="font-bold">Negotiating...</div>
                </div>
              )}
            </div>

            {/* Complete */}
            {isComplete && (
              <div className="bg-[#E0FFE0] border-2 rounded p-8 text-center" style={{ borderColor: '#128C12' }}>
                <div className="text-6xl mb-4">✓</div>
                <div className="text-3xl font-bold mb-2 text-[#128C12]">DEAL COMPLETE</div>
                <div className="text-lg mb-6">
                  Closed in {negotiation.rounds?.length || 0} rounds
                </div>
                <div className="bg-white border-2 inline-block px-8 py-4 rounded" style={{ borderColor: '#128C12' }}>
                  <div className="text-xs font-bold mb-1">TOTAL VALUE</div>
                  <div className="text-4xl font-bold text-[#128C12]">
                    ${((negotiation.final_price || 0) * (negotiation.quantity || 1)).toFixed(2)}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Status Bar */}
          <div className="bg-gradient-to-b from-[#ECE9D8] to-[#D6D3C9] border-t-2 border-white px-3 py-1 flex justify-between text-xs">
            <div>ID: {params.id}</div>
            <div>{isActive ? "⚡ LIVE" : isComplete ? "✓ COMPLETE" : "VIEWING"}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
