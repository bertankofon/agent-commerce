"use client";
import { useState, useEffect } from "react";
import { usePrivy } from '@privy-io/react-auth';
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getMyAgents, getLiveAgents, updateAgentStatus, getAgentProducts } from "../lib/api";
import ProductsModal from "../components/ProductsModal";

interface Product {
  id: string;
  name: string;
  price: string;
  stock: number;
  negotiation_percentage: number;
  currency: string;
  description?: string;
  metadata?: any;
}

interface Agent {
  id: string;
  name: string;
  agent_type: 'merchant' | 'client';
  status: 'live' | 'paused' | 'draft';
  avatar_url?: string;
  owner?: string;
  products_count: number;
  created_at: string;
}

export default function MarketPage() {
  const router = useRouter();
  const { authenticated, user } = usePrivy();
  const [activeTab, setActiveTab] = useState<'my-agents' | 'market'>('my-agents');
  const [myAgents, setMyAgents] = useState<Agent[]>([]);
  const [marketAgents, setMarketAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  
  // Products Modal State
  const [showProductsModal, setShowProductsModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);

  useEffect(() => {
    if (!authenticated) {
      router.push('/');
      return;
    }
    loadData();
  }, [authenticated, user]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 2;
      const y = (e.clientY / window.innerHeight - 0.5) * 2;
      setMousePos({ x, y });
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  async function loadData() {
    setLoading(true);
    setError("");
    
    try {
      // Load my agents
      if (user?.wallet?.address) {
        const myData = await getMyAgents(user.wallet.address);
        setMyAgents(myData.agents || []);
      }
      
      // Load market agents
      const marketData = await getLiveAgents();
      setMarketAgents(marketData.agents || []);
    } catch (err: any) {
      console.error("Failed to load agents:", err);
      setError("Failed to load agents");
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleStatus(agentId: string, currentStatus: string) {
    try {
      const newStatus = currentStatus === 'live' ? 'paused' : 'live';
      await updateAgentStatus(agentId, newStatus);
      await loadData(); // Reload
    } catch (err: any) {
      console.error("Failed to update status:", err);
      setError("Failed to update agent status");
    }
  }

  async function handleViewProducts(agent: Agent) {
    setSelectedAgent(agent);
    setLoadingProducts(true);
    setShowProductsModal(true);
    
    try {
      const data = await getAgentProducts(agent.id);
      setProducts(data.products || []);
    } catch (err: any) {
      console.error("Failed to load products:", err);
      setError("Failed to load products");
      setProducts([]);
    } finally {
      setLoadingProducts(false);
    }
  }

  function handleCloseModal() {
    setShowProductsModal(false);
    setSelectedAgent(null);
    setProducts([]);
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'live': return 'text-cyan-400';
      case 'paused': return 'text-orange-400';
      case 'draft': return 'text-gray-400';
      default: return 'text-cyan-400';
    }
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case 'live': return '●';
      case 'paused': return '⏸';
      case 'draft': return '📝';
      default: return '●';
    }
  }

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      {/* Background */}
      <div
        className="space-bg"
        style={{
          transform: `translate(${mousePos.x * 8}px, ${mousePos.y * 8}px)`,
          transition: "transform 0.3s ease-out",
        }}
      >
        <div className="perspective-grid"></div>
        <div className="stars"></div>
      </div>

      {/* Content */}
      <div className="relative z-10 min-h-screen p-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex justify-between items-center mb-8">
            <Link href="/" className="text-cyan-400/60 hover:text-cyan-400 transition-colors">
              ← Back
            </Link>
            <h1 className="text-3xl font-bold neon-text">MARKET</h1>
            <Link href="/deploy" className="text-cyan-400/60 hover:text-cyan-400 transition-colors">
              Deploy Agent →
            </Link>
          </div>

          {/* Tabs */}
          <div className="flex gap-4 mb-8">
            <button
              onClick={() => setActiveTab('my-agents')}
              className={`px-6 py-3 rounded-xl font-semibold transition-all ${
                activeTab === 'my-agents'
                  ? 'bg-cyan-400/20 text-cyan-400 border-2 border-cyan-400'
                  : 'bg-black/40 text-cyan-400/60 border-2 border-cyan-400/20 hover:border-cyan-400/40'
              }`}
            >
              MY AGENTS
            </button>
            <button
              onClick={() => setActiveTab('market')}
              className={`px-6 py-3 rounded-xl font-semibold transition-all ${
                activeTab === 'market'
                  ? 'bg-cyan-400/20 text-cyan-400 border-2 border-cyan-400'
                  : 'bg-black/40 text-cyan-400/60 border-2 border-cyan-400/20 hover:border-cyan-400/40'
              }`}
            >
              ALL AGENTS
            </button>
          </div>

          {/* Error */}
          {error && (
            <div className="border-2 border-red-400 rounded-xl p-4 mb-6 bg-red-400/10">
              <p className="text-red-400 text-center">{error}</p>
            </div>
          )}

          {/* Loading */}
          {loading ? (
            <div className="text-center py-16">
              <div className="text-cyan-400 text-xl">Loading...</div>
            </div>
          ) : (
            <>
              {/* My Agents Tab */}
              {activeTab === 'my-agents' && (
                <div className="space-y-4">
                  {myAgents.length === 0 ? (
                    <div className="border-2 border-cyan-400/20 rounded-2xl p-12 text-center backdrop-blur-sm bg-black/40">
                      <p className="text-cyan-400/60 text-lg mb-4">No agents yet</p>
                      <Link
                        href="/deploy"
                        className="inline-block px-6 py-3 border-2 border-cyan-400 rounded-xl text-cyan-400 hover:bg-cyan-400/10 transition-all"
                      >
                        Deploy Your First Agent
                      </Link>
                    </div>
                  ) : (
                    myAgents.map((agent) => (
                      <div
                        key={agent.id}
                        className="border-2 border-cyan-400/30 rounded-2xl p-6 backdrop-blur-sm bg-black/40 hover:border-cyan-400/60 transition-all"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            {agent.avatar_url ? (
                              <img src={agent.avatar_url} alt={agent.name} className="w-12 h-12 rounded-full" />
                            ) : (
                              <div className="w-12 h-12 rounded-full bg-cyan-400/20 flex items-center justify-center text-cyan-400 text-xl">
                                🤖
                              </div>
                            )}
                            <div>
                              <h3 className="text-xl font-bold text-cyan-300">{agent.name}</h3>
                              <div className="flex items-center gap-3 text-sm mt-1">
                                <span className={`flex items-center gap-1 ${getStatusColor(agent.status)}`}>
                                  {getStatusIcon(agent.status)} {agent.status.toUpperCase()}
                                </span>
                                <span className="text-cyan-400/60">•</span>
                                <span className="text-cyan-400/60">{agent.agent_type.toUpperCase()}</span>
                                <span className="text-cyan-400/60">•</span>
                                <span className="text-cyan-400/60">{agent.products_count} products</span>
                              </div>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            {agent.agent_type === 'merchant' && (
                              <button
                                onClick={() => handleViewProducts(agent)}
                                className="px-4 py-2 border border-cyan-400/50 rounded-lg text-cyan-400 hover:border-cyan-400 transition-all text-sm"
                              >
                                View Products
                              </button>
                            )}
                            <button
                              onClick={() => handleToggleStatus(agent.id, agent.status)}
                              className="px-4 py-2 border border-cyan-400/50 rounded-lg text-cyan-400 hover:border-cyan-400 transition-all text-sm"
                            >
                              {agent.status === 'live' ? 'Pause' : 'Resume'}
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Market Tab */}
              {activeTab === 'market' && (
                <div className="space-y-4">
                  {marketAgents.length === 0 ? (
                    <div className="border-2 border-cyan-400/20 rounded-2xl p-12 text-center backdrop-blur-sm bg-black/40">
                      <p className="text-cyan-400/60 text-lg">No agents in the market yet</p>
                    </div>
                  ) : (
                    marketAgents.map((agent) => (
                      <div
                        key={agent.id}
                        className="border-2 border-cyan-400/30 rounded-2xl p-6 backdrop-blur-sm bg-black/40 hover:border-cyan-400/60 transition-all cursor-pointer"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            {agent.avatar_url ? (
                              <img src={agent.avatar_url} alt={agent.name} className="w-12 h-12 rounded-full" />
                            ) : (
                              <div className="w-12 h-12 rounded-full bg-cyan-400/20 flex items-center justify-center text-cyan-400 text-xl">
                                🏪
                              </div>
                            )}
                            <div>
                              <h3 className="text-xl font-bold text-cyan-300">{agent.name}</h3>
                              <div className="flex items-center gap-3 text-sm mt-1">
                                <span className="text-cyan-400 flex items-center gap-1">
                                  ● LIVE
                                </span>
                                <span className="text-cyan-400/60">•</span>
                                <span className="text-cyan-400/60">{agent.products_count} products</span>
                              </div>
                            </div>
                          </div>
                          <button 
                            onClick={() => handleViewProducts(agent)}
                            className="px-6 py-2 border-2 border-cyan-400 rounded-xl text-cyan-400 hover:bg-cyan-400/10 transition-all font-semibold"
                          >
                            View Products
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Products Modal */}
      <ProductsModal
        isOpen={showProductsModal}
        onClose={handleCloseModal}
        agentName={selectedAgent?.name || ""}
        products={loadingProducts ? [] : products}
      />
    </div>
  );
}

