"use client";
import { useState, useEffect } from "react";
import { usePrivy } from '@privy-io/react-auth';
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getMyAgents, updateAgentStatus } from "../lib/api";

interface Agent {
  id: string;
  name: string;
  agent_type: 'merchant' | 'client';
  status: 'live' | 'paused' | 'draft';
  avatar_url?: string;
  owner?: string;
  category?: string;
  pixel_count?: number;
  created_at: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const { authenticated, user } = usePrivy();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authenticated) {
      router.push('/');
      return;
    }
    loadAgents();
  }, [authenticated, user]);

  async function loadAgents() {
    if (!user?.wallet?.address) return;
    
    try {
      setLoading(true);
      setError("");
      const data = await getMyAgents(user.wallet.address);
      setAgents(data.agents || []);
    } catch (err: any) {
      console.error("Error loading agents:", err);
      setError(err.message || "Failed to load agents");
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleStatus(agentId: string, currentStatus: string) {
    const newStatus = currentStatus === 'live' ? 'paused' : 'live';
    try {
      await updateAgentStatus(agentId, newStatus);
      await loadAgents(); // Reload
    } catch (err: any) {
      console.error("Failed to update status:", err);
      setError(err.message);
    }
  }

  const merchantAgents = agents.filter(a => a.agent_type === 'merchant');
  const clientAgents = agents.filter(a => a.agent_type === 'client');

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-cyan-400/60">Loading Your Agents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-cyan-100 relative overflow-hidden">
      {/* Background */}
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,217,255,0.1),transparent_50%)]" />
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#0a0a0a_1px,transparent_1px),linear-gradient(to_bottom,#0a0a0a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_50%,#000,transparent)]" />

      {/* Header */}
      <header className="relative z-10 border-b border-cyan-400/20 bg-black/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-400 to-cyan-600 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <span className="text-black font-bold text-xl">E</span>
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
                MY DASHBOARD
              </h1>
              <p className="text-cyan-400/40 text-xs">Manage Your Agents</p>
            </div>
          </Link>

          <Link
            href="/"
            className="px-4 py-2 border border-cyan-400/50 rounded-lg text-cyan-400 hover:border-cyan-400 hover:bg-cyan-400/10 transition-all text-sm font-semibold"
          >
            ← Back to Marketplace
          </Link>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Merchant Agents */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-cyan-300 flex items-center gap-2">
              <span>🏪</span> Merchant Agents
              <span className="text-cyan-400/60 text-sm">({merchantAgents.length})</span>
            </h2>
          </div>

          {merchantAgents.length === 0 ? (
            <div className="bg-black/50 border-2 border-cyan-400/20 rounded-xl p-12 text-center backdrop-blur-sm">
              <p className="text-cyan-400/40 mb-4">No merchant agents yet</p>
              <Link
                href="/"
                className="inline-block px-6 py-3 bg-gradient-to-r from-cyan-400 to-cyan-600 rounded-lg text-black font-semibold hover:shadow-lg hover:shadow-cyan-400/50 transition-all"
              >
                Open Your First Store
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {merchantAgents.map((agent) => (
                <div
                  key={agent.id}
                  className="bg-black/50 border-2 border-cyan-400/30 rounded-xl p-4 hover:border-cyan-400/60 transition-all backdrop-blur-sm"
                >
                  {/* Avatar */}
                  {agent.avatar_url && (
                    <div className="text-center text-4xl mb-3">
                      {agent.avatar_url}
                    </div>
                  )}

                  {/* Name */}
                  <h3 className="text-lg font-bold text-cyan-300 mb-2 text-center">
                    {agent.name}
                  </h3>

                  {/* Category */}
                  {agent.category && (
                    <p className="text-cyan-400/60 text-xs text-center mb-3">
                      {agent.category}
                    </p>
                  )}

                  {/* Stats */}
                  <div className="space-y-1 text-xs mb-3">
                    <div className="flex justify-between">
                      <span className="text-cyan-400/60">Pixels:</span>
                      <span className="text-cyan-300">{agent.pixel_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-cyan-400/60">Status:</span>
                      <span className={`font-semibold ${
                        agent.status === 'live' ? 'text-green-400' : 
                        agent.status === 'paused' ? 'text-yellow-400' : 
                        'text-gray-400'
                      }`}>
                        {agent.status.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleToggleStatus(agent.id, agent.status)}
                      className="flex-1 px-3 py-2 border border-cyan-400/50 rounded-lg text-cyan-400 hover:border-cyan-400 hover:bg-cyan-400/10 transition-all text-xs font-semibold"
                    >
                      {agent.status === 'live' ? '⏸ Pause' : '▶ Resume'}
                    </button>
                    <Link
                      href="/"
                      className="flex-1 px-3 py-2 border border-cyan-400/50 rounded-lg text-cyan-400 hover:border-cyan-400 hover:bg-cyan-400/10 transition-all text-xs font-semibold text-center"
                    >
                      View on Map
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Client Agents */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-cyan-300 flex items-center gap-2">
              <span>👤</span> Client Agents
              <span className="text-cyan-400/60 text-sm">({clientAgents.length})</span>
            </h2>
          </div>

          {clientAgents.length === 0 ? (
            <div className="bg-black/50 border-2 border-cyan-400/20 rounded-xl p-12 text-center backdrop-blur-sm">
              <p className="text-cyan-400/40 mb-4">No client agents yet</p>
              <p className="text-cyan-400/60 text-sm">
                Client agents are created automatically when you start a negotiation
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {clientAgents.map((agent) => (
                <div
                  key={agent.id}
                  className="bg-black/50 border-2 border-purple-400/30 rounded-xl p-4 hover:border-purple-400/60 transition-all backdrop-blur-sm"
                >
                  {/* Avatar */}
                  {agent.avatar_url && (
                    <div className="text-center text-4xl mb-3">
                      {agent.avatar_url}
                    </div>
                  )}

                  {/* Name */}
                  <h3 className="text-lg font-bold text-purple-300 mb-2 text-center">
                    {agent.name}
                  </h3>

                  {/* Status */}
                  <div className="text-xs mb-3 text-center">
                    <span className={`font-semibold ${
                      agent.status === 'live' ? 'text-green-400' : 
                      agent.status === 'paused' ? 'text-yellow-400' : 
                      'text-gray-400'
                    }`}>
                      {agent.status.toUpperCase()}
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleToggleStatus(agent.id, agent.status)}
                      className="flex-1 px-3 py-2 border border-purple-400/50 rounded-lg text-purple-400 hover:border-purple-400 hover:bg-purple-400/10 transition-all text-xs font-semibold"
                    >
                      {agent.status === 'live' ? '⏸ Pause' : '▶ Resume'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
