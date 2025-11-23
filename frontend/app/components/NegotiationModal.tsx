"use client";

import React, { useState, useEffect } from "react";
import { getCategoryColor } from "../lib/categories";

// Get backend URL from environment variable
// Supports multiple possible variable names
const API_BASE = 
  process.env.NEXT_PUBLIC_NEXT_BACKEND_URL || 
  process.env.NEXT_PUBLIC_next_backend_url ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  'http://localhost:8000';

interface ChatMessage {
  id: string;
  round_number: number;
  sender: { id: string; name: string };
  receiver: { id: string; name: string };
  message: string;
  proposed_price: number;
  accept: boolean;
  reason?: string;
  created_at: string;
}

interface Negotiation {
  id: string;
  session_id: string;
  client_agent: { id: string; name: string; category?: string };
  merchant_agent: { id: string; name: string; category?: string };
  product?: { id: string; name: string; price: number; image_url?: string };
  product_id?: string;
  initial_price: number;
  final_price?: number;
  budget?: number;
  agreed: boolean;
  status: string;
  payment_successful?: boolean | null;
  txn_hash?: string | null;
  chat_history: ChatMessage[];
  created_at: string;
}

interface Agent {
  id: string;
  name: string;
  agent_type: string;
  category?: string;
}

interface NegotiationModalProps {
  isOpen: boolean;
  onClose: () => void;
  merchantAgentId: string;
  productId: string;
  productName: string;
  productPrice: number;
  merchantCategory?: string;
  myClientAgents: Agent[];
  onNegotiationStart?: () => void;
}

export default function NegotiationModal({
  isOpen,
  onClose,
  merchantAgentId,
  productId,
  productName,
  productPrice,
  merchantCategory = "TECH",
  myClientAgents,
  onNegotiationStart,
}: NegotiationModalProps) {
  const [selectedClientAgent, setSelectedClientAgent] = useState<Agent | null>(
    myClientAgents.length === 1 ? myClientAgents[0] : null
  );
  const [isNegotiating, setIsNegotiating] = useState(false);
  const [negotiationResult, setNegotiationResult] = useState<Negotiation | null>(null);
  const [budget, setBudget] = useState<number>(productPrice * 0.8);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<Negotiation[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const categoryColor = getCategoryColor(merchantCategory);

  // Load negotiation history when modal opens
  useEffect(() => {
    if (isOpen && productId) {
      loadNegotiationHistory();
    }
  }, [isOpen, productId]);

  const loadNegotiationHistory = async () => {
    try {
      setLoadingHistory(true);
      // Use Next.js API route for direct Supabase access
      const response = await fetch(
        `/api/negotiations/product/${productId}`
      );
      const data = await response.json();
      
      if (data.success) {
        setHistory(data.negotiations || []);
      }
    } catch (err) {
      console.error("Failed to load negotiation history:", err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const startNegotiation = async () => {
    if (!selectedClientAgent) {
      setError("Please select a client agent first");
      return;
    }

    try {
      setIsNegotiating(true);
      setError(null);
      onNegotiationStart?.();

      const response = await fetch(
        `${API_BASE}/negotiation/single-negotiation`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            client_agent_id: selectedClientAgent.id,
            merchant_agent_id: merchantAgentId,
            product_id: productId,
            budget: budget,
            rounds: 5,
            dry_run: false,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Negotiation failed");
      }

      // Reload history and show the latest negotiation
      await loadNegotiationHistory();
      
      // Find the latest negotiation from the response
      if (data.negotiation) {
        setNegotiationResult(data.negotiation);
      }
    } catch (err: any) {
      console.error("Negotiation error:", err);
      setError(err.message || "Failed to start negotiation");
    } finally {
      setIsNegotiating(false);
    }
  };


  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getStatusColor = (status: string, agreed: boolean, payment_successful?: boolean | null | string | number) => {
    // More robust check for payment_successful - handle boolean, string, number, null, undefined
    const paymentValue = payment_successful;
    const isPaymentSuccessful = 
      paymentValue === true || 
      (typeof paymentValue === "string" && paymentValue === "true") || 
      (typeof paymentValue === "number" && paymentValue === 1) ||
      (paymentValue !== null && paymentValue !== undefined && String(paymentValue).toLowerCase() === "true");
    
    // Green: payment was successful
    if (isPaymentSuccessful) {
      return "text-green-400 border-green-400/50 bg-green-400/10";
    }
    // Blue: agreed but payment not successful (false, null, or undefined)
    if (agreed && !isPaymentSuccessful) {
      return "text-blue-400 border-blue-400/50 bg-blue-400/10";
    }
    // Red: not agreed
    if (!agreed) {
      return "text-red-400 border-red-400/50 bg-red-400/10";
    }
    // Fallback for edge cases
    if (status === "rejected") return "text-red-400 border-red-400/50 bg-red-400/10";
    if (status === "failed") return "text-orange-400 border-orange-400/50 bg-orange-400/10";
    return "text-cyan-400 border-cyan-400/50 bg-cyan-400/10";
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-w-7xl w-full max-h-[90vh] overflow-hidden border-2 border-cyan-400/40 rounded-3xl backdrop-blur-md bg-black/95 shadow-2xl shadow-cyan-500/20 m-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="relative border-b border-cyan-400/30 p-6 bg-gradient-to-r from-cyan-500/10 to-purple-500/10">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-cyan-400/60 hover:text-cyan-400 transition-all text-2xl"
          >
            ✕
          </button>
          
          <h2 className="text-2xl font-bold text-cyan-400 mb-2">
            🤝 Negotiation Center
          </h2>
          <p className="text-cyan-300/70 text-sm">
            {productName} - {formatPrice(productPrice)}
          </p>
        </div>

        {/* 3-Column Split Layout */}
        <div className="flex gap-4 p-6 overflow-hidden max-h-[calc(90vh-180px)]">
          
          {/* LEFT: My Client Agents */}
          <div className="w-1/3 space-y-3 overflow-y-auto border-r border-cyan-400/20 pr-4">
            <h3 className="text-lg font-bold text-cyan-400 mb-3 sticky top-0 bg-black/95 pb-2 z-10">
              🤖 Select Your Agent
            </h3>
            
            {myClientAgents.length === 0 ? (
              <div className="text-center text-cyan-400/60 py-8 border-2 border-cyan-400/20 rounded-xl bg-black/20">
                <p className="mb-4">No client agents found</p>
                <button
                  onClick={() => window.location.href = '/deploy?type=client'}
                  className="px-6 py-3 bg-cyan-400/10 border-2 border-cyan-400/50 rounded-xl text-cyan-400 hover:bg-cyan-400/20 hover:border-cyan-400 transition-all"
                >
                  + Create Client Agent
                </button>
              </div>
            ) : (
              myClientAgents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => setSelectedClientAgent(agent)}
                  className={`w-full p-4 border-2 rounded-xl transition-all text-left ${
                    selectedClientAgent?.id === agent.id
                      ? 'border-cyan-400 bg-cyan-400/20 shadow-lg shadow-cyan-500/20'
                      : 'border-cyan-400/30 hover:border-cyan-400/50 hover:bg-cyan-400/10'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-cyan-400 font-semibold">{agent.name}</div>
                      <div className="text-cyan-400/60 text-xs">{agent.category || 'Client Agent'}</div>
                    </div>
                    {selectedClientAgent?.id === agent.id && (
                      <div className="text-green-400 text-xl">✓</div>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>

          {/* MIDDLE: Negotiation Form */}
          <div className="w-1/3 space-y-4 overflow-y-auto">
            <h3 className="text-lg font-bold text-cyan-400 mb-3 sticky top-0 bg-black/95 pb-2 z-10">
              💰 Set Your Budget
            </h3>
            
            {!selectedClientAgent ? (
              <div className="text-center text-cyan-400/60 py-8 border-2 border-cyan-400/20 rounded-xl bg-black/20">
                ← Select a client agent first
              </div>
            ) : (
              <div className="border-2 border-cyan-400/30 rounded-xl p-6 bg-black/20">
                <label className="text-cyan-400/80 text-sm block mb-2">
                  Maximum Budget (USD)
                </label>
                <input
                  type="number"
                  value={budget}
                  onChange={(e) => setBudget(parseFloat(e.target.value))}
                  step="0.01"
                  min="0"
                  max={productPrice}
                  className="w-full px-4 py-3 bg-black/50 border-2 border-cyan-400/30 rounded-xl text-cyan-100 focus:border-cyan-400 transition-all"
                />
                <div className="flex justify-between text-xs text-cyan-400/60 mt-2">
                  <span>Product: {formatPrice(productPrice)}</span>
                  <span className="text-green-400">
                    Save: {formatPrice(productPrice - budget)} ({(((productPrice - budget) / productPrice) * 100).toFixed(1)}%)
                  </span>
                </div>

                {error && (
                  <div className="mt-3 border border-red-400/50 bg-red-400/10 text-red-400 px-4 py-3 rounded-xl text-sm">
                    ⚠️ {error}
                  </div>
                )}

                <button
                  onClick={startNegotiation}
                  disabled={isNegotiating || !selectedClientAgent}
                  className="w-full mt-4 px-6 py-4 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border-2 border-cyan-400/50 rounded-xl text-cyan-400 hover:border-cyan-400 hover:from-cyan-500/30 hover:to-purple-500/30 transition-all font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isNegotiating ? (
                    <>
                      <span className="inline-block animate-spin mr-2">⚡</span>
                      Negotiating...
                    </>
                  ) : (
                    '🤝 Start Negotiation'
                  )}
                </button>

                <div className="mt-4 text-xs text-cyan-400/40 border border-cyan-400/20 rounded-lg p-3 bg-black/20">
                  <strong>How it works:</strong>
                  <ul className="mt-2 space-y-1 list-disc list-inside">
                    <li>AI agents negotiate (up to 5 rounds)</li>
                    <li>Saved to blockchain</li>
                    <li>Auto payment if deal agreed</li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* RIGHT: History */}
          <div className="w-1/3 space-y-3 overflow-y-auto pl-4">
            <h3 className="text-lg font-bold text-cyan-400 mb-3 sticky top-0 bg-black/95 pb-2 z-10">
              📜 Negotiation History
            </h3>
            
            {loadingHistory ? (
              <div className="text-center text-cyan-400/60 py-8">Loading...</div>
            ) : history.length === 0 ? (
              <div className="text-center text-cyan-400/60 py-8 border-2 border-cyan-400/20 rounded-xl bg-black/20">
                No previous negotiations
              </div>
            ) : (
              history.map((neg) => {
                // Debug logging
                console.log('Negotiation:', {
                  id: neg.id,
                  agreed: neg.agreed,
                  payment_successful: neg.payment_successful,
                  payment_successful_type: typeof neg.payment_successful,
                  status: neg.status
                });
                
                // More robust check for payment_successful
                const paymentValue = neg.payment_successful;
                const isPaymentSuccessful = 
                  paymentValue === true || 
                  (typeof paymentValue === "string" && paymentValue === "true") || 
                  (typeof paymentValue === "number" && paymentValue === 1) ||
                  (paymentValue !== null && paymentValue !== undefined && String(paymentValue).toLowerCase() === "true");
                
                const statusColor = getStatusColor(neg.status, neg.agreed, neg.payment_successful);
                const borderColor = isPaymentSuccessful 
                  ? "border-green-400/40 hover:border-green-400/60" 
                  : neg.agreed && !isPaymentSuccessful
                  ? "border-blue-400/40 hover:border-blue-400/60"
                  : !neg.agreed
                  ? "border-red-400/40 hover:border-red-400/60"
                  : "border-cyan-400/20 hover:border-cyan-400/40";
                
                return (
                <div
                  key={neg.id}
                  onClick={() => setNegotiationResult(neg)}
                  className={`border-2 ${borderColor} rounded-xl p-4 transition-all cursor-pointer ${
                    isPaymentSuccessful ? 'bg-green-400/10' : 'bg-black/20'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      {isPaymentSuccessful && (
                        <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse"></div>
                      )}
                      <div>
                        <div className="text-cyan-400 font-semibold text-sm">
                          {neg.client_agent.name}
                        </div>
                        <div className="text-cyan-400/60 text-xs">
                          {formatDate(neg.created_at)}
                        </div>
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full border ${statusColor}`}>
                      {isPaymentSuccessful 
                        ? '✓ PAID' 
                        : neg.agreed 
                        ? '✓ AGREED' 
                        : '✗ ' + neg.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-cyan-400/70">{formatPrice(neg.initial_price)}</span>
                    {neg.final_price && (
                      <span className="text-green-400 font-semibold">
                        → {formatPrice(neg.final_price)}
                      </span>
                    )}
                  </div>
                </div>
                );
              })
            )}
          </div>
        </div>

        {/* Full Screen Result Modal */}
        {negotiationResult && (
          <div className="absolute inset-0 bg-black/98 z-20 overflow-y-auto p-6">
            <button
              onClick={() => setNegotiationResult(null)}
              className="absolute top-4 right-4 text-cyan-400/60 hover:text-cyan-400 transition-all text-2xl z-30"
            >
              ✕
            </button>

            <div className="max-w-4xl mx-auto space-y-4">
              <div className="border-2 border-cyan-400/30 rounded-xl p-6 bg-black/30">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-cyan-400 mb-2">
                      {negotiationResult.agreed ? "✅ Deal Agreed!" : "❌ No Agreement"}
                    </h3>
                    <div className="flex gap-2 items-center">
                      <span className={`text-xs px-3 py-1 rounded-full border ${getStatusColor(negotiationResult.status, negotiationResult.agreed, negotiationResult.payment_successful)}`}>
                        {negotiationResult.status.toUpperCase()}
                      </span>
                      {(() => {
                        const paymentValue = negotiationResult.payment_successful;
                        const isPaid = paymentValue === true || 
                          (typeof paymentValue === "string" && paymentValue === "true") || 
                          (typeof paymentValue === "number" && paymentValue === 1) ||
                          (paymentValue !== null && paymentValue !== undefined && String(paymentValue).toLowerCase() === "true");
                        return isPaid;
                      })() && (
                        <span className="text-xs px-3 py-1 rounded-full border text-green-400 border-green-400/50 bg-green-400/10">
                          💰 PAID
                        </span>
                      )}
                      {(() => {
                        const paymentValue = negotiationResult.payment_successful;
                        const isPaid = paymentValue === true || 
                          (typeof paymentValue === "string" && paymentValue === "true") || 
                          (typeof paymentValue === "number" && paymentValue === 1) ||
                          (paymentValue !== null && paymentValue !== undefined && String(paymentValue).toLowerCase() === "true");
                        return negotiationResult.agreed && !isPaid;
                      })() && (
                        <span className="text-xs px-3 py-1 rounded-full border text-blue-400 border-blue-400/50 bg-blue-400/10">
                          ⏳ PENDING PAYMENT
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-cyan-400/60 text-sm">Final Price</div>
                    <div className="text-3xl font-bold text-cyan-400">
                      {negotiationResult.final_price
                        ? formatPrice(negotiationResult.final_price)
                        : "N/A"}
                    </div>
                    {negotiationResult.final_price && (
                      <div className="text-green-400 text-sm">
                        💰 Saved {formatPrice(negotiationResult.initial_price - negotiationResult.final_price)}
                      </div>
                    )}
                  </div>
                </div>

                {/* Transaction Hash */}
                {negotiationResult.txn_hash && (
                  <div className="border-t border-cyan-400/20 pt-4 mt-4">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="text-sm font-bold text-cyan-400/80">Transaction Hash:</h4>
                      <span className="text-xs px-2 py-1 rounded-full border text-green-400 border-green-400/50 bg-green-400/10">
                        ✓ x402
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <code className="text-xs text-cyan-300/80 font-mono bg-black/40 px-3 py-2 rounded border border-cyan-400/20 break-all">
                        {negotiationResult.txn_hash}
                      </code>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(negotiationResult.txn_hash || '');
                        }}
                        className="text-cyan-400/60 hover:text-cyan-400 transition-all text-sm px-2 py-1 border border-cyan-400/30 rounded hover:border-cyan-400/50"
                        title="Copy transaction hash"
                      >
                        📋
                      </button>
                    </div>
                  </div>
                )}

                {/* Chat History */}
                <div className="border-t border-cyan-400/20 pt-4 mt-4">
                  <h4 className="text-lg font-bold text-cyan-400/80 mb-3">Negotiation Chat:</h4>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {negotiationResult.chat_history.map((msg) => (
                      <div
                        key={msg.id}
                        className="border border-cyan-400/20 rounded-lg p-4 bg-black/20"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <span className="text-cyan-400 font-semibold text-sm">
                              Round {msg.round_number}: {msg.sender.name}
                            </span>
                            <span className="text-cyan-400/60 text-xs ml-2">
                              → {msg.receiver.name}
                            </span>
                          </div>
                          <span className={`text-sm px-2 py-1 rounded border ${msg.accept ? "border-green-400/50 text-green-400 bg-green-400/10" : "border-orange-400/50 text-orange-400 bg-orange-400/10"}`}>
                            {formatPrice(msg.proposed_price)}
                          </span>
                        </div>
                        <p className="text-cyan-300/80 text-sm">{msg.message}</p>
                        {msg.reason && (
                          <p className="text-cyan-400/60 text-xs mt-1 italic">
                            Reason: {msg.reason}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <button
                onClick={() => setNegotiationResult(null)}
                className="w-full px-6 py-3 bg-cyan-400/10 border-2 border-cyan-400/30 rounded-xl text-cyan-400 hover:bg-cyan-400/20 hover:border-cyan-400 transition-all"
              >
                ← Back to Negotiations
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
