"use client";
import { useState, useEffect, useMemo } from "react";
import { usePrivy } from '@privy-io/react-auth';
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getMyAgents, getLiveAgents, updateAgentStatus, getAgentProducts, getAllPixelClaims } from "../lib/api";
import ProductsModal from "../components/ProductsModal";
import { getCategoryColor, getCategoryById } from "../lib/categories";
import WalletButton from "../components/WalletButton";

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
  category?: string;
}

interface PixelClaim {
  x: number;
  y: number;
  agent_id: string;
  agents?: {
    name: string;
    category: string;
    avatar_url?: string;
  };
}

export default function MarketPage() {
  const router = useRouter();
  const { authenticated, user } = usePrivy();
  const [activeTab, setActiveTab] = useState<'my-agents' | 'market' | 'pixel-map'>('pixel-map');
  const [myAgents, setMyAgents] = useState<Agent[]>([]);
  const [marketAgents, setMarketAgents] = useState<Agent[]>([]);
  const [pixelClaims, setPixelClaims] = useState<PixelClaim[]>([]);
  const [hoveredPixel, setHoveredPixel] = useState<PixelClaim | null>(null);
  const [lastHoveredPixel, setLastHoveredPixel] = useState<PixelClaim | null>(null);
  const [loading, setLoading] = useState(true);
  const [pixelsLoading, setPixelsLoading] = useState(false);
  const [error, setError] = useState("");
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  
  // Pixel Selection for Merchant Deploy
  const [isSelectingPixels, setIsSelectingPixels] = useState(false);
  const [selectedPixels, setSelectedPixels] = useState<Array<{x: number, y: number}>>([]);
  const [dragStart, setDragStart] = useState<{x: number, y: number} | null>(null);
  const [dragEnd, setDragEnd] = useState<{x: number, y: number} | null>(null);
  
  // Products Modal State
  const [showProductsModal, setShowProductsModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  
  // Fund Modal State
  const [showFundModal, setShowFundModal] = useState(false);
  const [fundingAgent, setFundingAgent] = useState<Agent | null>(null);
  const [fundAmount, setFundAmount] = useState("1.0");
  const [fundingInProgress, setFundingInProgress] = useState(false);
  const [fundError, setFundError] = useState("");

  useEffect(() => {
    if (!authenticated) {
      router.push('/');
      return;
    }
    loadInitialData();
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

  // Initial load: Load ALL data at once so agents are ready for negotiation
  async function loadInitialData() {
    setLoading(true);
    setError("");
    
    try {
      // Load everything in parallel for instant access
      const promises: Promise<any>[] = [
        getAllPixelClaims().then(data => setPixelClaims(data.pixels || [])),
        getLiveAgents().then(data => setMarketAgents(data.agents || []))
      ];
      
      if (user?.wallet?.address) {
        promises.push(
          getMyAgents(user.wallet.address).then(data => setMyAgents(data.agents || []))
        );
      }
      
      await Promise.all(promises);
    } catch (err: any) {
      console.error("Failed to load data:", err);
      setError("Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  // Reload only pixels when switching to pixel-map tab
  async function reloadPixels() {
    if (pixelClaims.length > 0) return; // Already loaded
    
    setPixelsLoading(true);
    try {
      const pixelData = await getAllPixelClaims();
      setPixelClaims(pixelData.pixels || []);
    } catch (err: any) {
      console.error("Failed to reload pixels:", err);
    } finally {
      setPixelsLoading(false);
    }
  }

  // Reload pixels when tab changes to pixel-map (if needed)
  useEffect(() => {
    if (authenticated && !loading && activeTab === 'pixel-map') {
      reloadPixels();
    }
  }, [activeTab]);

  async function handleToggleStatus(agentId: string, currentStatus: string) {
    try {
      const newStatus = currentStatus === 'live' ? 'paused' : 'live';
      await updateAgentStatus(agentId, newStatus);
      
      // Reload only agents, not pixels
      const promises: Promise<any>[] = [
        getLiveAgents().then(data => setMarketAgents(data.agents || []))
      ];
      
      if (user?.wallet?.address) {
        promises.push(
          getMyAgents(user.wallet.address).then(data => setMyAgents(data.agents || []))
        );
      }
      
      await Promise.all(promises);
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

  async function handleFundAgent() {
    if (!fundingAgent || !user?.wallet?.address) return;
    
    setFundingInProgress(true);
    setFundError("");
    
    try {
      const amount = parseFloat(fundAmount);
      if (isNaN(amount) || amount <= 0) {
        throw new Error("Invalid amount");
      }
      
      // Get agent's wallet address
      const response = await fetch(`http://localhost:8000/agent/${fundingAgent.id}`);
      const data = await response.json();
      
      const walletAddress = data.public_address || data.wallet_address;
      
      if (!walletAddress) {
        throw new Error("Agent wallet address not found");
      }
      
      // USDC Contract Address on Base Sepolia
      const USDC_ADDRESS = "0x036CbD53842c5426634e7929541eC2318f3dCF7e";
      const BASE_SEPOLIA_CHAIN_ID = "0x14a34"; // 84532 in hex
      
      // Switch to Base Sepolia network if needed
      try {
        await (window as any).ethereum.request({
          method: "wallet_switchEthereumChain",
          params: [{ chainId: BASE_SEPOLIA_CHAIN_ID }],
        });
      } catch (switchError: any) {
        // This error code indicates that the chain has not been added to MetaMask
        if (switchError.code === 4902) {
          try {
            await (window as any).ethereum.request({
              method: "wallet_addEthereumChain",
              params: [{
                chainId: BASE_SEPOLIA_CHAIN_ID,
                chainName: "Base Sepolia",
                nativeCurrency: {
                  name: "Ethereum",
                  symbol: "ETH",
                  decimals: 18
                },
                rpcUrls: ["https://sepolia.base.org"],
                blockExplorerUrls: ["https://sepolia.basescan.org"]
              }],
            });
          } catch (addError) {
            throw new Error("Failed to add Base Sepolia network to MetaMask");
          }
        } else {
          throw switchError;
        }
      }
      
      // Convert amount to USDC decimals (6 decimals)
      const amountInUSDC = Math.floor(amount * 1_000_000).toString();
      
      // ERC-20 Transfer function signature
      const transferData = 
        "0xa9059cbb" + // transfer(address,uint256)
        walletAddress.slice(2).padStart(64, "0") + // to address (remove 0x, pad to 32 bytes)
        parseInt(amountInUSDC).toString(16).padStart(64, "0"); // amount in hex, padded to 32 bytes
      
      // Request transaction from MetaMask
      const txHash = await (window as any).ethereum.request({
        method: "eth_sendTransaction",
        params: [{
          from: user.wallet.address,
          to: USDC_ADDRESS,
          data: transferData,
          chainId: BASE_SEPOLIA_CHAIN_ID
        }]
      });
      
      alert(`✅ Successfully funded ${fundingAgent.name} with ${amount} USDC!\n\nTransaction: ${txHash}\nAgent Wallet: ${walletAddress}`);
      
      setShowFundModal(false);
      setFundingAgent(null);
      setFundAmount("1.0");
    } catch (err: any) {
      console.error("Failed to fund agent:", err);
      setFundError(err.message || err.toString() || "Failed to fund agent");
    } finally {
      setFundingInProgress(false);
    }
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

  function handlePixelMouseDown(x: number, y: number) {
    if (!isSelectingPixels) return;
    const isOccupied = pixelClaims.some(c => c.x === x && c.y === y);
    if (isOccupied) return;
    
    setDragStart({ x, y });
    setDragEnd({ x, y });
  }

  function handlePixelMouseMove(x: number, y: number) {
    if (!isSelectingPixels || !dragStart) return;
    setDragEnd({ x, y });
  }

  function handlePixelMouseUp() {
    if (!isSelectingPixels || !dragStart || !dragEnd) return;

    const minX = Math.min(dragStart.x, dragEnd.x);
    const maxX = Math.max(dragStart.x, dragEnd.x);
    const minY = Math.min(dragStart.y, dragEnd.y);
    const maxY = Math.max(dragStart.y, dragEnd.y);

    const newPixels: Array<{x: number, y: number}> = [];
    for (let x = minX; x <= maxX; x++) {
      for (let y = minY; y <= maxY; y++) {
        const isOccupied = pixelClaims.some(c => c.x === x && c.y === y);
        if (!isOccupied) {
          newPixels.push({ x, y });
        }
      }
    }

    if (newPixels.length > 100) {
      setError("Maximum 100 pixels allowed!");
      setDragStart(null);
      setDragEnd(null);
      return;
    }

    setSelectedPixels(newPixels);
    setDragStart(null);
    setDragEnd(null);
  }

  function isInDragArea(x: number, y: number): boolean {
    if (!dragStart || !dragEnd) return false;
    const minX = Math.min(dragStart.x, dragEnd.x);
    const maxX = Math.max(dragStart.x, dragEnd.x);
    const minY = Math.min(dragStart.y, dragEnd.y);
    const maxY = Math.max(dragStart.y, dragEnd.y);
    return x >= minX && x <= maxX && y >= minY && y <= maxY;
  }

  function handleStartMerchantDeploy() {
    setIsSelectingPixels(true);
    setSelectedPixels([]);
    setError("");
  }

  function handleCancelSelection() {
    setIsSelectingPixels(false);
    setSelectedPixels([]);
    setDragStart(null);
    setDragEnd(null);
  }

  function handleDeployMerchant() {
    if (selectedPixels.length === 0) {
      setError("Please select pixels first!");
      return;
    }
    // Redirect to deploy page with pixels
    const pixelsParam = encodeURIComponent(JSON.stringify(selectedPixels));
    router.push(`/deploy?type=merchant&pixels=${pixelsParam}`);
  }

  function handleDeployClient() {
    // Redirect to deploy page for client
    router.push(`/deploy?type=client`);
  }

  // Memoize pixel claims map for O(1) lookup
  const pixelClaimsMap = useMemo(() => {
    const map = new Map<string, PixelClaim>();
    pixelClaims.forEach(claim => {
      map.set(`${claim.x},${claim.y}`, claim);
    });
    return map;
  }, [pixelClaims]);

  // Memoize selected pixels set for O(1) lookup
  const selectedPixelsSet = useMemo(() => {
    const set = new Set<string>();
    selectedPixels.forEach(p => {
      set.add(`${p.x},${p.y}`);
    });
    return set;
  }, [selectedPixels]);

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      {/* Wallet Button - Top Right */}
      <WalletButton />
      
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
              onClick={() => setActiveTab('pixel-map')}
              className={`px-6 py-3 rounded-xl font-semibold transition-all ${
                activeTab === 'pixel-map'
                  ? 'bg-cyan-400/20 text-cyan-400 border-2 border-cyan-400'
                  : 'bg-black/40 text-cyan-400/60 border-2 border-cyan-400/20 hover:border-cyan-400/40'
              }`}
            >
              PIXEL MAP
            </button>
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
              {/* Pixel Map Tab */}
              {activeTab === 'pixel-map' && (
                <div className="flex flex-col items-center justify-center min-h-[600px]">
                  {/* Deploy Buttons - Above Grid */}
                  <div className="mb-10 flex gap-6">
                    {isSelectingPixels ? (
                      <>
                        <button
                          onClick={handleCancelSelection}
                          className="group relative px-12 py-5 bg-gradient-to-br from-cyan-400 to-cyan-500 rounded-2xl text-black hover:from-cyan-300 hover:to-cyan-400 transition-all duration-300 font-black text-lg shadow-2xl shadow-cyan-400/60 hover:shadow-cyan-300/80 hover:scale-105 overflow-hidden"
                        >
                          <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                          <div className="relative flex items-center justify-center gap-3">
                            <span className="text-2xl">✕</span>
                            <span>CANCEL</span>
                          </div>
                        </button>
                        <button
                          onClick={handleDeployMerchant}
                          disabled={selectedPixels.length === 0}
                          className="group relative px-14 py-5 bg-gradient-to-br from-cyan-400 to-cyan-500 rounded-2xl text-black hover:from-cyan-300 hover:to-cyan-400 transition-all duration-300 font-black text-lg shadow-2xl shadow-cyan-400/60 hover:shadow-cyan-300/80 hover:scale-105 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 overflow-hidden"
                        >
                          <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                          <div className="relative flex items-center justify-center gap-3">
                            <span className="text-2xl">🏪</span>
                            <span>DEPLOY STORE ({selectedPixels.length} PIXELS)</span>
                          </div>
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={handleDeployClient}
                          className="group relative px-14 py-5 bg-gradient-to-br from-cyan-400 to-cyan-500 rounded-2xl text-black hover:from-cyan-300 hover:to-cyan-400 transition-all duration-300 font-black text-lg shadow-2xl shadow-cyan-400/60 hover:shadow-cyan-300/80 hover:scale-105 overflow-hidden"
                        >
                          <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                          <div className="relative flex items-center justify-center gap-3">
                            <span className="text-2xl">👤</span>
                            <span>DEPLOY CLIENT</span>
                          </div>
                        </button>
                        <button
                          onClick={handleStartMerchantDeploy}
                          className="group relative px-14 py-5 bg-gradient-to-br from-cyan-400 to-cyan-500 rounded-2xl text-black hover:from-cyan-300 hover:to-cyan-400 transition-all duration-300 font-black text-lg shadow-2xl shadow-cyan-400/60 hover:shadow-cyan-300/80 hover:scale-105 overflow-hidden"
                        >
                          <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                          <div className="relative flex items-center justify-center gap-3">
                            <span className="text-2xl">🏪</span>
                            <span>DEPLOY MERCHANT</span>
                          </div>
                        </button>
                      </>
                    )}
                  </div>

                  {/* Status Text */}
                  {isSelectingPixels && (
                    <p className="text-cyan-400/60 text-sm mb-4">
                      🎨 Drag to select pixels • {selectedPixels.length}/100 selected
                    </p>
                  )}

                  {/* Pixel Grid - Centered, Extra Large (75x30) */}
                  <div className="border-2 border-cyan-400/30 rounded-xl p-6 bg-black/50 backdrop-blur-sm">
                    <div 
                      className="grid gap-0"
                      style={{
                        gridTemplateColumns: `repeat(75, 20px)`,
                        width: "fit-content"
                      }}
                    >
                        {Array.from({ length: 75 * 30 }, (_, i) => {
                          const x = i % 75;
                          const y = Math.floor(i / 75);
                          const key = `${x},${y}`;
                          const claim = pixelClaimsMap.get(key);
                          const isSelected = selectedPixelsSet.has(key);
                          const isInDrag = isInDragArea(x, y);
                          
                          let bgColor = "#0a0a0a";
                          let borderColor = "#1a1a1a";
                          let opacity = 0.2;
                          let cursor = "default";
                          
                          if (claim && claim.agents) {
                            bgColor = getCategoryColor(claim.agents.category || 'TECH');
                            borderColor = bgColor;
                            opacity = 0.5; // Daha soft, UI'a uyumlu
                            cursor = isSelectingPixels ? "not-allowed" : "pointer";
                          } else if (isSelectingPixels) {
                            cursor = "crosshair";
                            if (isSelected) {
                              bgColor = "#0891B2"; // UI cyan
                              borderColor = "#0891B2";
                              opacity = 0.6;
                            } else if (isInDrag) {
                              bgColor = "#0891B2"; // UI cyan
                              borderColor = "#0891B2";
                              opacity = 0.3;
                            }
                          }
                          
                          return (
                            <div
                              key={`${x}-${y}`}
                              onMouseEnter={() => {
                                if (!isSelectingPixels) {
                                  setHoveredPixel(claim || null);
                                  if (claim) {
                                    setLastHoveredPixel(claim);
                                  }
                                }
                              }}
                              onMouseLeave={() => setHoveredPixel(null)}
                              onMouseDown={() => handlePixelMouseDown(x, y)}
                              onMouseMove={() => handlePixelMouseMove(x, y)}
                              onMouseUp={handlePixelMouseUp}
                              onClick={() => {
                                if (!isSelectingPixels && claim) {
                                  handleViewProducts({ 
                                    id: claim.agent_id, 
                                    name: claim.agents?.name || '',
                                    agent_type: 'merchant',
                                    status: 'live',
                                    avatar_url: claim.agents?.avatar_url,
                                    products_count: 0,
                                    created_at: '',
                                    category: claim.agents?.category
                                  } as Agent);
                                }
                              }}
                              style={{
                                width: "20px",
                                height: "20px",
                                backgroundColor: bgColor,
                                border: `1px solid ${borderColor}`,
                                opacity,
                                cursor,
                                transition: "all 0.1s ease",
                                boxShadow: (claim || isSelected) ? `0 0 8px ${bgColor}50` : "none",
                                userSelect: "none"
                              }}
                              className={claim && !isSelectingPixels ? "hover:scale-110 hover:opacity-100" : ""}
                            />
                          );
                        })}
                      </div>
                  </div>

                  {/* Hover Info - Below Grid (Sticky) */}
                  <div className="mt-8 w-[500px]">
                    {(hoveredPixel || lastHoveredPixel) && (hoveredPixel?.agents || lastHoveredPixel?.agents) ? (
                      <div className="border-2 border-cyan-400/50 rounded-xl p-6 bg-black/60 backdrop-blur-sm">
                        <div className="flex items-center gap-5">
                          {(hoveredPixel?.agents?.avatar_url || lastHoveredPixel?.agents?.avatar_url) && (
                            <div className="text-5xl">
                              {hoveredPixel?.agents?.avatar_url || lastHoveredPixel?.agents?.avatar_url}
                            </div>
                          )}
                          <div className="flex-1">
                            <h3 className="text-xl font-bold text-cyan-300 mb-2">
                              {hoveredPixel?.agents?.name || lastHoveredPixel?.agents?.name}
                            </h3>
                            <p className="text-cyan-400/70 text-sm">
                              {getCategoryById((hoveredPixel?.agents?.category || lastHoveredPixel?.agents?.category) as string)?.emoji}{' '}
                              {getCategoryById((hoveredPixel?.agents?.category || lastHoveredPixel?.agents?.category) as string)?.name}
                            </p>
                          </div>
                          <button
                            onClick={() => {
                              const pixel = hoveredPixel || lastHoveredPixel;
                              if (pixel) {
                                handleViewProducts({ 
                                  id: pixel.agent_id, 
                                  name: pixel.agents?.name || '',
                                  agent_type: 'merchant',
                                  status: 'live',
                                  avatar_url: pixel.agents?.avatar_url,
                                  products_count: 0,
                                  created_at: '',
                                  category: pixel.agents?.category
                                } as Agent);
                              }
                            }}
                            className="px-6 py-3 bg-cyan-400/10 border-2 border-cyan-400 rounded-lg text-cyan-400 hover:bg-cyan-400/20 transition-all font-bold text-sm"
                          >
                            View Store
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="border-2 border-cyan-400/20 rounded-xl p-6 bg-black/30 text-center text-cyan-400/40">
                        <p className="text-base">🗺️ Hover over a claimed pixel to see merchant details</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

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
                              <div className="flex items-center gap-3 mb-2">
                                <h3 className="text-xl font-bold text-cyan-300">{agent.name}</h3>
                                {/* Agent Type Badge */}
                                {agent.agent_type === 'merchant' ? (
                                  <span className="px-3 py-1 bg-gradient-to-r from-cyan-500/20 to-cyan-600/20 border border-cyan-400/50 rounded-full text-cyan-400 text-xs font-bold flex items-center gap-1.5">
                                    🏪 MERCHANT
                                  </span>
                                ) : (
                                  <span className="px-3 py-1 bg-gradient-to-r from-purple-500/20 to-purple-600/20 border border-purple-400/50 rounded-full text-purple-400 text-xs font-bold flex items-center gap-1.5">
                                    👤 CLIENT
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-3 text-sm mt-1">
                                <span className={`flex items-center gap-1 ${getStatusColor(agent.status)}`}>
                                  {getStatusIcon(agent.status)} {agent.status.toUpperCase()}
                                </span>
                                {agent.agent_type === 'merchant' && (
                                  <>
                                    <span className="text-cyan-400/60">•</span>
                                    <span className="text-cyan-400/60">{agent.products_count || 0} products</span>
                                  </>
                                )}
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
                            {agent.agent_type === 'client' && (
                              <button
                                onClick={() => {
                                  setFundingAgent(agent);
                                  setShowFundModal(true);
                                }}
                                className="px-4 py-2 border border-green-400/50 rounded-lg text-green-400 hover:border-green-400 hover:bg-green-400/10 transition-all text-sm font-semibold"
                              >
                                💰 Fund
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
                              <div className="flex items-center gap-3 mb-2">
                                <h3 className="text-xl font-bold text-cyan-300">{agent.name}</h3>
                                {/* Agent Type Badge */}
                                {agent.agent_type === 'merchant' ? (
                                  <span className="px-3 py-1 bg-gradient-to-r from-cyan-500/20 to-cyan-600/20 border border-cyan-400/50 rounded-full text-cyan-400 text-xs font-bold flex items-center gap-1.5">
                                    🏪 MERCHANT
                                  </span>
                                ) : (
                                  <span className="px-3 py-1 bg-gradient-to-r from-purple-500/20 to-purple-600/20 border border-purple-400/50 rounded-full text-purple-400 text-xs font-bold flex items-center gap-1.5">
                                    👤 CLIENT
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-3 text-sm mt-1">
                                <span className="text-cyan-400 flex items-center gap-1">
                                  ● LIVE
                                </span>
                                {agent.agent_type === 'merchant' && (
                                  <>
                                    <span className="text-cyan-400/60">•</span>
                                    <span className="text-cyan-400/60">{agent.products_count || 0} products</span>
                                  </>
                                )}
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

      {/* Fund Modal */}
      {showFundModal && fundingAgent && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
          onClick={() => {
            setShowFundModal(false);
            setFundingAgent(null);
            setFundAmount("1.0");
            setFundError("");
          }}
        >
          <div
            className="relative max-w-md w-full border-2 border-green-400/40 rounded-3xl backdrop-blur-md bg-black/95 shadow-2xl shadow-green-500/20 m-4 p-8"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => {
                setShowFundModal(false);
                setFundingAgent(null);
                setFundAmount("1.0");
                setFundError("");
              }}
              className="absolute top-4 right-4 text-cyan-400/60 hover:text-cyan-400 transition-all text-2xl"
            >
              ✕
            </button>

            <h2 className="text-2xl font-bold text-green-400 mb-2">💰 Fund Agent</h2>
            <p className="text-cyan-300/70 text-sm mb-4">
              Send USDC to <span className="text-cyan-400 font-semibold">{fundingAgent.name}</span>
            </p>
            <div className="bg-blue-500/10 border border-blue-400/30 rounded-lg px-3 py-2 mb-6">
              <p className="text-blue-400 text-xs flex items-center gap-2">
                <span>🔵</span>
                <span>Network: <span className="font-semibold">Base Sepolia</span></span>
              </p>
              <p className="text-blue-400/70 text-xs mt-1 ml-5">
                Token: USDC (0x036C...CF7e)
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-cyan-400/80 text-sm block mb-2">
                  Amount (USDC)
                </label>
                <input
                  type="number"
                  value={fundAmount}
                  onChange={(e) => setFundAmount(e.target.value)}
                  step="0.1"
                  min="0.1"
                  className="w-full px-4 py-3 bg-black/50 border-2 border-green-400/30 rounded-xl text-green-100 focus:border-green-400 transition-all text-lg font-semibold"
                  placeholder="1.0"
                />
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={() => setFundAmount("1.0")}
                    className="px-3 py-1 border border-green-400/30 rounded-lg text-green-400/70 hover:border-green-400 hover:text-green-400 transition-all text-xs"
                  >
                    1 USDC
                  </button>
                  <button
                    onClick={() => setFundAmount("5.0")}
                    className="px-3 py-1 border border-green-400/30 rounded-lg text-green-400/70 hover:border-green-400 hover:text-green-400 transition-all text-xs"
                  >
                    5 USDC
                  </button>
                  <button
                    onClick={() => setFundAmount("10.0")}
                    className="px-3 py-1 border border-green-400/30 rounded-lg text-green-400/70 hover:border-green-400 hover:text-green-400 transition-all text-xs"
                  >
                    10 USDC
                  </button>
                </div>
              </div>

              {fundError && (
                <div className="border border-red-400/50 bg-red-400/10 text-red-400 px-4 py-3 rounded-xl text-sm">
                  ⚠️ {fundError}
                </div>
              )}

              <button
                onClick={handleFundAgent}
                disabled={fundingInProgress}
                className="w-full px-6 py-4 bg-gradient-to-r from-green-500/20 to-emerald-500/20 border-2 border-green-400/50 rounded-xl text-green-400 hover:border-green-400 hover:from-green-500/30 hover:to-emerald-500/30 transition-all font-bold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {fundingInProgress ? (
                  <>
                    <span className="inline-block animate-spin mr-2">⚡</span>
                    Sending...
                  </>
                ) : (
                  `Send ${fundAmount} USDC`
                )}
              </button>

              <div className="text-xs text-cyan-400/40 border border-cyan-400/20 rounded-lg p-3 bg-black/20">
                <strong>Note:</strong> USDC will be sent to the agent's wallet address on Base Sepolia testnet.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Products Modal */}
      <ProductsModal
        isOpen={showProductsModal}
        onClose={handleCloseModal}
        agentName={selectedAgent?.name || ""}
        merchantAgentId={selectedAgent?.id || ""}
        merchantCategory={selectedAgent?.category}
        myClientAgents={myAgents.filter(a => a.agent_type === 'client')}
        products={loadingProducts ? [] : products}
      />
    </div>
  );
}

