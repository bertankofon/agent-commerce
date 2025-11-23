"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { getAgents, getNegotiations, startNegotiation } from "../lib/api";
import type { Agent, Negotiation } from "../lib/types";

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [negotiations, setNegotiations] = useState<Negotiation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBuyer, setSelectedBuyer] = useState("");
  const [selectedSeller, setSelectedSeller] = useState("");
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, []);

  async function loadData() {
    try {
      const [agentsData, negotiationsData] = await Promise.all([
        getAgents(),
        getNegotiations(),
      ]);
      setAgents(agentsData || []);
      setNegotiations(negotiationsData || []);
      setLoading(false);
    } catch (error) {
      setLoading(false);
    }
  }

  async function handleStartNegotiation() {
    if (!selectedBuyer || !selectedSeller) return;

    setStarting(true);
    try {
      const data = await startNegotiation(selectedBuyer, selectedSeller);
      if (data.id) {
        window.location.href = `/negotiation/${data.id}`;
      }
    } finally {
      setStarting(false);
    }
  }

  const buyers = agents.filter((a) => a.type === "buyer");
  const sellers = agents.filter((a) => a.type === "seller");
  const activeNegotiations = negotiations.filter((n) => n.status === "in_progress");
  const completedNegotiations = negotiations.filter((n) => n.status === "completed");

  if (loading) {
    return (
      <div className="min-h-screen bg-[#5A7EDC] flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#5A7EDC] p-8">
      <div className="max-w-6xl mx-auto">
        {/* XP Window */}
        <div className="bg-white rounded-lg shadow-2xl overflow-hidden" style={{ border: '3px solid #0831D9' }}>
          {/* Title Bar */}
          <div className="bg-gradient-to-r from-[#0831D9] to-[#3165F0] px-3 py-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-white rounded-sm"></div>
              <span className="text-white font-bold text-sm">Dashboard - Agent Commerce</span>
            </div>
            <div className="flex gap-1">
              <button className="w-5 h-5 bg-[#2E6EE6] border border-white flex items-center justify-center text-white text-xs">_</button>
              <button className="w-5 h-5 bg-[#2E6EE6] border border-white flex items-center justify-center text-white text-xs">□</button>
              <button className="w-5 h-5 bg-[#D93831] border border-white flex items-center justify-center text-white text-xs">×</button>
            </div>
          </div>

          {/* Menu Bar */}
          <div className="bg-gradient-to-b from-[#F1F3FD] to-[#D9E4F5] border-b border-[#9CB0D7] px-2 py-1 flex justify-between items-center">
            <div className="flex gap-4 text-sm">
              <span className="hover:bg-[#316AC5] hover:text-white px-2 py-1 cursor-pointer">File</span>
              <span className="hover:bg-[#316AC5] hover:text-white px-2 py-1 cursor-pointer">View</span>
              <span className="hover:bg-[#316AC5] hover:text-white px-2 py-1 cursor-pointer">Tools</span>
            </div>
            <Link
              href="/deploy"
              className="px-4 py-1 bg-gradient-to-b from-[#F0F0F0] to-[#C8C8C8] border-2 rounded text-sm font-bold"
              style={{ borderColor: '#FFFFFF #555555 #555555 #FFFFFF' }}
            >
              Deploy New
            </Link>
          </div>

          {/* Content */}
          <div className="p-6 bg-gradient-to-b from-[#ECE9D8] to-[#D6D3C9]">
            {/* Stats */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-gradient-to-b from-[#D4D0C8] to-[#B8B4AC] border-2 rounded p-4 text-center"
                   style={{ borderColor: '#FFFFFF #404040 #404040 #FFFFFF' }}>
                <div className="text-xs font-bold mb-1">TOTAL</div>
                <div className="text-3xl font-bold text-[#0831D9]">{agents.length}</div>
              </div>
              <div className="bg-gradient-to-b from-[#D4D0C8] to-[#B8B4AC] border-2 rounded p-4 text-center"
                   style={{ borderColor: '#FFFFFF #404040 #404040 #FFFFFF' }}>
                <div className="text-xs font-bold mb-1">BUYERS</div>
                <div className="text-3xl font-bold text-[#128C12]">{buyers.length}</div>
              </div>
              <div className="bg-gradient-to-b from-[#D4D0C8] to-[#B8B4AC] border-2 rounded p-4 text-center"
                   style={{ borderColor: '#FFFFFF #404040 #404040 #FFFFFF' }}>
                <div className="text-xs font-bold mb-1">SELLERS</div>
                <div className="text-3xl font-bold text-[#D93831]">{sellers.length}</div>
              </div>
              <div className="bg-gradient-to-b from-[#D4D0C8] to-[#B8B4AC] border-2 rounded p-4 text-center"
                   style={{ borderColor: '#FFFFFF #404040 #404040 #FFFFFF' }}>
                <div className="text-xs font-bold mb-1">ACTIVE</div>
                <div className="text-3xl font-bold text-[#FF8C00]">{activeNegotiations.length}</div>
              </div>
            </div>

            {/* Start Section */}
            <div className="bg-white border-2 rounded p-4 mb-6" style={{ borderColor: '#0831D9' }}>
              <h2 className="text-lg font-bold text-[#0831D9] mb-4">Start Negotiation</h2>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-bold mb-1">Select Buyer:</label>
                  <select
                    value={selectedBuyer}
                    onChange={(e) => setSelectedBuyer(e.target.value)}
                    className="w-full px-3 py-2 border-2 rounded bg-white"
                    style={{ borderColor: '#7F9DB9' }}
                  >
                    <option value="">Choose...</option>
                    {buyers.map((buyer) => (
                      <option key={buyer.id} value={buyer.id}>
                        {buyer.name} (${buyer.config.max_price})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-bold mb-1">Select Seller:</label>
                  <select
                    value={selectedSeller}
                    onChange={(e) => setSelectedSeller(e.target.value)}
                    className="w-full px-3 py-2 border-2 rounded bg-white"
                    style={{ borderColor: '#7F9DB9' }}
                  >
                    <option value="">Choose...</option>
                    {sellers.map((seller) => (
                      <option key={seller.id} value={seller.id}>
                        {seller.name} (${seller.config.initial_price})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <button
                onClick={handleStartNegotiation}
                disabled={!selectedBuyer || !selectedSeller || starting}
                className="w-full px-6 py-3 bg-gradient-to-b from-[#F0F0F0] to-[#C8C8C8] border-2 rounded shadow-md font-bold disabled:opacity-50"
                style={{ borderColor: '#FFFFFF #555555 #555555 #FFFFFF' }}
              >
                {starting ? "Starting..." : "Start Negotiation"}
              </button>
            </div>

            {/* Active Negotiations */}
            {activeNegotiations.length > 0 && (
              <div className="mb-6">
                <h3 className="text-md font-bold mb-3 text-[#0831D9]">Active Negotiations</h3>
                <div className="space-y-2">
                  {activeNegotiations.map((neg) => (
                    <Link
                      key={neg.id}
                      href={`/negotiation/${neg.id}`}
                      className="block bg-[#FFFACD] border-2 rounded p-3 hover:bg-[#FFEC8B]"
                      style={{ borderColor: '#FF8C00' }}
                    >
                      <div className="flex justify-between items-center">
                        <div className="font-bold">{neg.buyer_name || "Buyer"} → {neg.seller_name || "Seller"}</div>
                        <div className="text-xs bg-[#FF8C00] text-white px-2 py-1 rounded">LIVE</div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Completed */}
            {completedNegotiations.length > 0 && (
              <div>
                <h3 className="text-md font-bold mb-3 text-[#0831D9]">Completed</h3>
                <div className="space-y-2">
                  {completedNegotiations.map((neg) => (
                    <Link
                      key={neg.id}
                      href={`/negotiation/${neg.id}`}
                      className="block bg-[#E0FFE0] border-2 rounded p-3 hover:bg-[#C8FFC8]"
                      style={{ borderColor: '#128C12' }}
                    >
                      <div className="flex justify-between items-center">
                        <div>
                          <div className="font-bold">{neg.buyer_name || "Buyer"} → {neg.seller_name || "Seller"}</div>
                          <div className="text-sm">${neg.final_price} × {neg.quantity}</div>
                        </div>
                        <div className="text-2xl text-[#128C12]">✓</div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Empty State */}
            {agents.length === 0 && (
              <div className="bg-white border-2 rounded p-12 text-center" style={{ borderColor: '#0831D9' }}>
                <div className="text-6xl mb-4">📦</div>
                <h3 className="text-xl font-bold mb-4">No Agents Yet</h3>
                <Link
                  href="/deploy"
                  className="inline-block px-8 py-3 bg-gradient-to-b from-[#F0F0F0] to-[#C8C8C8] border-2 rounded shadow-md font-bold"
                  style={{ borderColor: '#FFFFFF #555555 #555555 #FFFFFF' }}
                >
                  Deploy First Agent
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
