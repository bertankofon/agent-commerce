"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createAgent } from "../lib/api";
import { AuthGuard } from "../lib/auth-guard";
import { usePrivy } from '@privy-io/react-auth';

interface Product {
  id: string;
  name: string;
  price: number;
  stock: number;
  maxDiscount: number;
  imageUrl?: string;
}

interface SearchItem {
  id: string;
  productName: string;
  targetPrice: number;
  maxBudget: number;
  quantity: number;
}

export default function DeployPage() {
  const router = useRouter();
  const { user, logout } = usePrivy();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  
  const [agentType, setAgentType] = useState<"merchant" | "client">("merchant");
  const [agentName, setAgentName] = useState("");
  const [agentDomain, setAgentDomain] = useState("");
  const [agentDescription, setAgentDescription] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  
  // Merchant
  const [products, setProducts] = useState<Product[]>([]);
  
  // Client
  const [searchItems, setSearchItems] = useState<SearchItem[]>([]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 2;
      const y = (e.clientY / window.innerHeight - 0.5) * 2;
      setMousePos({ x, y });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  function addProduct() {
    setProducts([
      ...products,
      {
        id: Date.now().toString(),
        name: "",
        price: 1000,
        stock: 100,
        maxDiscount: 15,
      },
    ]);
  }

  function removeProduct(id: string) {
    setProducts(products.filter((p) => p.id !== id));
  }

  function updateProduct(id: string, field: keyof Product, value: any) {
    setProducts(
      products.map((p) => (p.id === id ? { ...p, [field]: value } : p))
    );
  }

  function addSearchItem() {
    setSearchItems([
      ...searchItems,
      {
        id: Date.now().toString(),
        productName: "",
        targetPrice: 800,
        maxBudget: 1000,
        quantity: 1,
      },
    ]);
  }

  function removeSearchItem(id: string) {
    setSearchItems(searchItems.filter((s) => s.id !== id));
  }

  function updateSearchItem(id: string, field: keyof SearchItem, value: any) {
    setSearchItems(
      searchItems.map((s) => (s.id === id ? { ...s, [field]: value } : s))
    );
  }

  async function handleDeploy() {
    if (!agentName.trim()) {
      setError("AGENT NAME REQUIRED");
      return;
    }

    if (agentType === "merchant" && products.length === 0) {
      setError("ADD AT LEAST ONE PRODUCT");
      return;
    }

    if (agentType === "client" && searchItems.length === 0) {
      setError("ADD AT LEAST ONE SEARCH ITEM");
      return;
    }

    setLoading(true);
    setError("");

    try {
      // Create FormData for backend
      const formData = new FormData();
      
      formData.append("agent_type", agentType);
      formData.append("name", agentName.trim());
      
      // Domain - auto-generate if not provided
      const domain = agentDomain.trim() || 
        `${agentName.trim().toLowerCase().replace(/\s+/g, '-')}.epoch.com`;
      formData.append("domain", domain);
      
      // Image if selected
      if (selectedImage) {
        formData.append("image", selectedImage);
      }
      
      // Products/search items as JSON metadata (for future use)
      if (agentType === "merchant") {
        formData.append("products_json", JSON.stringify(products));
      } else {
        formData.append("search_items_json", JSON.stringify(searchItems));
      }
      
      // Description if provided
      if (agentDescription.trim()) {
        formData.append("description", agentDescription.trim());
      }

      // Add user wallet address
      if (user?.wallet?.address) {
        formData.append("user_wallet_address", user.wallet.address);
      }
      
      // Add user ID for Supabase tracking
      if (user?.id) {
        formData.append("user_id", user.id);
      }

      const data = await createAgent(formData);

      if (data.agent_id) {
        setSuccess(true);
        setTimeout(() => {
          router.push("/");
        }, 2000);
      } else {
        setError("DEPLOYMENT FAILED");
      }
    } catch (err: any) {
      setError(err.message || "DEPLOYMENT FAILED");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-black relative overflow-hidden">
        {/* User Profile - Top Right */}
        <div className="fixed top-6 right-6 z-50">
          <div className="border-2 border-cyan-400/30 rounded-xl p-3 bg-black/70 backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <div className="text-cyan-400 text-sm">
                {user?.wallet?.address ? (
                  <span>
                    {user.wallet.address.slice(0, 6)}...{user.wallet.address.slice(-4)}
                  </span>
                ) : user?.email?.address ? (
                  <span>{user.email.address}</span>
                ) : (
                  <span>User</span>
                )}
              </div>
              <button
                onClick={() => logout()}
                className="text-cyan-400/60 hover:text-cyan-400 text-xs px-2 py-1 border border-cyan-400/30 rounded hover:border-cyan-400/60 transition-all"
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Space Background */}
        <div
          className="space-bg"
          style={{
            transform: `translate(${mousePos.x * 8}px, ${mousePos.y * 8}px)`,
            transition: "transform 0.3s ease-out",
          }}
        >
          <div className="perspective-grid"></div>
          <div className="stars"></div>
          <div
            className="floating-orb orb-1"
            style={{
              transform: `translate(${mousePos.x * 25}px, ${mousePos.y * 25}px)`,
              transition: "transform 0.5s ease-out",
            }}
          ></div>
          <div
            className="floating-orb orb-2"
            style={{
              transform: `translate(${-mousePos.x * 35}px, ${-mousePos.y * 35}px)`,
              transition: "transform 0.5s ease-out",
            }}
          ></div>
        </div>

        {/* Content */}
        <div className="relative z-10 min-h-screen p-8">
          <div className="max-w-4xl mx-auto">
            {/* Back Button */}
            <Link
              href="/"
              className="inline-flex items-center text-cyan-400/60 hover:text-cyan-400 mb-8 transition-colors"
            >
              <span className="mr-2">←</span>
              <span>Back</span>
            </Link>

            {/* Main Container */}
            <div
              className="border-2 border-cyan-400/30 rounded-3xl p-8 backdrop-blur-sm bg-black/40 shadow-2xl shadow-cyan-500/20"
              style={{
                transform: `perspective(1000px) rotateY(${mousePos.x * 2}deg) rotateX(${-mousePos.y * 2}deg)`,
                transition: "transform 0.3s ease-out",
              }}
            >
              {/* Title */}
              <h1 className="text-4xl font-bold text-center mb-8 neon-text">
                DEPLOY AGENT
              </h1>

              {/* Success Message */}
              {success && (
                <div className="border-2 border-cyan-400 rounded-2xl p-6 mb-8 bg-cyan-400/10 text-center">
                  <div className="text-5xl mb-3">✓</div>
                  <p className="text-cyan-400 text-xl font-semibold">
                    AGENT DEPLOYED
                  </p>
                  <p className="text-cyan-300/60 text-sm mt-2">Redirecting...</p>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="border-2 border-cyan-400 rounded-2xl p-4 mb-6 bg-cyan-400/10">
                  <p className="text-cyan-400 text-center font-semibold">
                    {error}
                  </p>
                </div>
              )}

              {!success && (
              <>
                {/* Type Selector */}
                <div className="grid grid-cols-2 gap-6 mb-8">
                  <button
                    onClick={() => setAgentType("merchant")}
                    className={`neon-card border-2 rounded-2xl p-8 transition-all ${
                      agentType === "merchant"
                        ? "border-cyan-400 shadow-lg shadow-cyan-400/30"
                        : "border-cyan-400/20 hover:border-cyan-400/40"
                    }`}
                  >
                    <div
                      className={`w-16 h-16 mx-auto mb-4 flex items-center justify-center ${
                        agentType === "merchant"
                          ? "text-cyan-400"
                          : "text-cyan-400/30"
                      }`}
                    >
                      <svg
                        className="w-12 h-12"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
                        />
                      </svg>
                    </div>
                    <p className="text-cyan-300 font-bold text-lg">MERCHANT</p>
                  </button>

                  <button
                    onClick={() => setAgentType("client")}
                    className={`neon-card border-2 rounded-2xl p-8 transition-all ${
                      agentType === "client"
                        ? "border-cyan-400 shadow-lg shadow-cyan-400/30"
                        : "border-cyan-400/20 hover:border-cyan-400/40"
                    }`}
                  >
                    <div
                      className={`w-16 h-16 mx-auto mb-4 flex items-center justify-center ${
                        agentType === "client"
                          ? "text-cyan-400"
                          : "text-cyan-400/30"
                      }`}
                    >
                      <svg
                        className="w-12 h-12"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                        />
                      </svg>
                    </div>
                    <p className="text-cyan-300 font-bold text-lg">CLIENT</p>
                  </button>
                </div>

                {/* Agent Info */}
                <div className="space-y-4 mb-6">
                  <div>
                    <label className="block text-cyan-300/70 text-sm mb-2 font-semibold">
                      AGENT NAME
                    </label>
                    <input
                      type="text"
                      value={agentName}
                      onChange={(e) => setAgentName(e.target.value)}
                      className="w-full px-4 py-3 bg-black/50 border-2 border-cyan-400/30 rounded-xl text-cyan-100 placeholder-cyan-400/30 focus:border-cyan-400 transition-all"
                      placeholder={
                        agentType === "merchant"
                          ? "TechStore"
                          : "Budget Shopper"
                      }
                    />
                  </div>

                  <div>
                    <label className="block text-cyan-300/70 text-sm mb-2 font-semibold">
                      DOMAIN
                    </label>
                    <input
                      type="text"
                      value={agentDomain}
                      onChange={(e) => setAgentDomain(e.target.value)}
                      className="w-full px-4 py-3 bg-black/50 border-2 border-cyan-400/30 rounded-xl text-cyan-100 placeholder-cyan-400/30 focus:border-cyan-400 transition-all"
                      placeholder="techstore.epoch.com"
                    />
                  </div>

                  <div>
                    <label className="block text-cyan-300/70 text-sm mb-2 font-semibold">
                      DESCRIPTION (OPTIONAL)
                    </label>
                    <input
                      type="text"
                      value={agentDescription}
                      onChange={(e) => setAgentDescription(e.target.value)}
                      className="w-full px-4 py-3 bg-black/50 border-2 border-cyan-400/30 rounded-xl text-cyan-100 placeholder-cyan-400/30 focus:border-cyan-400 transition-all"
                      placeholder="Brief description..."
                    />
                  </div>

                  <div>
                    <label className="block text-cyan-300/70 text-sm mb-2 font-semibold">
                      AVATAR IMAGE (OPTIONAL)
                    </label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setSelectedImage(e.target.files?.[0] || null)}
                      className="w-full px-4 py-3 bg-black/50 border-2 border-cyan-400/30 rounded-xl text-cyan-100 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-cyan-400/20 file:text-cyan-400 hover:file:bg-cyan-400/30 focus:border-cyan-400 transition-all"
                    />
                    {selectedImage && (
                      <p className="text-cyan-400/60 text-xs mt-2">
                        Selected: {selectedImage.name}
                      </p>
                    )}
                  </div>
                </div>

                {/* Merchant Products */}
                {agentType === "merchant" && (
                  <div className="border-2 border-cyan-400/20 rounded-2xl p-6 bg-black/50 mb-6">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-cyan-300/80 font-bold text-sm">
                        PRODUCTS
                      </h3>
                      <button
                        onClick={addProduct}
                        className="px-4 py-2 border border-cyan-400/50 rounded-lg text-cyan-400 hover:border-cyan-400 transition-all text-sm font-semibold"
                      >
                        + ADD
                      </button>
                    </div>

                    <div className="space-y-4 max-h-96 overflow-y-auto">
                      {products.map((product, idx) => (
                        <div
                          key={product.id}
                          className="border border-cyan-400/20 rounded-xl p-4 bg-black/30"
                        >
                          <div className="flex justify-between items-center mb-3">
                            <span className="text-cyan-400/60 text-xs font-bold">
                              PRODUCT {idx + 1}
                            </span>
                            <button
                              onClick={() => removeProduct(product.id)}
                              className="text-cyan-400/50 hover:text-cyan-400 text-xs"
                            >
                              ✕
                            </button>
                          </div>

                          <div className="grid grid-cols-2 gap-3">
                            <div className="col-span-2">
                              <label className="block text-cyan-300/60 text-xs mb-1">
                                NAME
                              </label>
                              <input
                                type="text"
                                value={product.name}
                                onChange={(e) =>
                                  updateProduct(
                                    product.id,
                                    "name",
                                    e.target.value
                                  )
                                }
                                className="w-full px-3 py-2 bg-black/50 border border-cyan-400/30 rounded-lg text-cyan-100 text-sm focus:border-cyan-400 transition-all"
                                placeholder="MacBook Pro"
                              />
                            </div>
                            <div>
                              <label className="block text-cyan-300/60 text-xs mb-1">
                                PRICE ($)
                              </label>
                              <input
                                type="number"
                                value={product.price}
                                onChange={(e) =>
                                  updateProduct(
                                    product.id,
                                    "price",
                                    Number(e.target.value)
                                  )
                                }
                                className="w-full px-3 py-2 bg-black/50 border border-cyan-400/30 rounded-lg text-cyan-100 text-sm focus:border-cyan-400 transition-all"
                              />
                            </div>
                            <div>
                              <label className="block text-cyan-300/60 text-xs mb-1">
                                STOCK
                              </label>
                              <input
                                type="number"
                                value={product.stock}
                                onChange={(e) =>
                                  updateProduct(
                                    product.id,
                                    "stock",
                                    Number(e.target.value)
                                  )
                                }
                                className="w-full px-3 py-2 bg-black/50 border border-cyan-400/30 rounded-lg text-cyan-100 text-sm focus:border-cyan-400 transition-all"
                              />
                            </div>
                            <div>
                              <label className="block text-cyan-300/60 text-xs mb-1">
                                MAX DISCOUNT (%)
                              </label>
                              <input
                                type="number"
                                value={product.maxDiscount}
                                onChange={(e) =>
                                  updateProduct(
                                    product.id,
                                    "maxDiscount",
                                    Number(e.target.value)
                                  )
                                }
                                className="w-full px-3 py-2 bg-black/50 border border-cyan-400/30 rounded-lg text-cyan-100 text-sm focus:border-cyan-400 transition-all"
                                max="100"
                                min="0"
                              />
                            </div>
                            <div>
                              <label className="block text-cyan-300/60 text-xs mb-1">
                                IMAGE URL (OPT)
                              </label>
                              <input
                                type="text"
                                value={product.imageUrl || ""}
                                onChange={(e) =>
                                  updateProduct(
                                    product.id,
                                    "imageUrl",
                                    e.target.value
                                  )
                                }
                                className="w-full px-3 py-2 bg-black/50 border border-cyan-400/30 rounded-lg text-cyan-100 text-sm focus:border-cyan-400 transition-all"
                                placeholder="https://..."
                              />
                            </div>
                          </div>
                        </div>
                      ))}

                      {products.length === 0 && (
                        <div className="text-center py-8 text-cyan-400/40 text-sm">
                          Click + ADD to create your first product
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Client Search Items */}
                {agentType === "client" && (
                  <div className="border-2 border-cyan-400/20 rounded-2xl p-6 bg-black/50 mb-6">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-cyan-300/80 font-bold text-sm">
                        WHAT ARE YOU LOOKING FOR?
                      </h3>
                      <button
                        onClick={addSearchItem}
                        className="px-4 py-2 border border-cyan-400/50 rounded-lg text-cyan-400 hover:border-cyan-400 transition-all text-sm font-semibold"
                      >
                        + ADD
                      </button>
                    </div>

                    <div className="space-y-4 max-h-96 overflow-y-auto">
                      {searchItems.map((item, idx) => (
                        <div
                          key={item.id}
                          className="border border-cyan-400/20 rounded-xl p-4 bg-black/30"
                        >
                          <div className="flex justify-between items-center mb-3">
                            <span className="text-cyan-400/60 text-xs font-bold">
                              ITEM {idx + 1}
                            </span>
                            <button
                              onClick={() => removeSearchItem(item.id)}
                              className="text-cyan-400/50 hover:text-cyan-400 text-xs"
                            >
                              ✕
                            </button>
                          </div>

                          <div className="grid grid-cols-2 gap-3">
                            <div className="col-span-2">
                              <label className="block text-cyan-300/60 text-xs mb-1">
                                PRODUCT NAME
                              </label>
                              <input
                                type="text"
                                value={item.productName}
                                onChange={(e) =>
                                  updateSearchItem(
                                    item.id,
                                    "productName",
                                    e.target.value
                                  )
                                }
                                className="w-full px-3 py-2 bg-black/50 border border-cyan-400/30 rounded-lg text-cyan-100 text-sm focus:border-cyan-400 transition-all"
                                placeholder="MacBook Pro"
                              />
                            </div>
                            <div>
                              <label className="block text-cyan-300/60 text-xs mb-1">
                                TARGET PRICE ($)
                              </label>
                              <input
                                type="number"
                                value={item.targetPrice}
                                onChange={(e) =>
                                  updateSearchItem(
                                    item.id,
                                    "targetPrice",
                                    Number(e.target.value)
                                  )
                                }
                                className="w-full px-3 py-2 bg-black/50 border border-cyan-400/30 rounded-lg text-cyan-100 text-sm focus:border-cyan-400 transition-all"
                              />
                            </div>
                            <div>
                              <label className="block text-cyan-300/60 text-xs mb-1">
                                MAX BUDGET ($)
                              </label>
                              <input
                                type="number"
                                value={item.maxBudget}
                                onChange={(e) =>
                                  updateSearchItem(
                                    item.id,
                                    "maxBudget",
                                    Number(e.target.value)
                                  )
                                }
                                className="w-full px-3 py-2 bg-black/50 border border-cyan-400/30 rounded-lg text-cyan-100 text-sm focus:border-cyan-400 transition-all"
                              />
                            </div>
                            <div className="col-span-2">
                              <label className="block text-cyan-300/60 text-xs mb-1">
                                QUANTITY
                              </label>
                              <input
                                type="number"
                                value={item.quantity}
                                onChange={(e) =>
                                  updateSearchItem(
                                    item.id,
                                    "quantity",
                                    Number(e.target.value)
                                  )
                                }
                                className="w-full px-3 py-2 bg-black/50 border border-cyan-400/30 rounded-lg text-cyan-100 text-sm focus:border-cyan-400 transition-all"
                                min="1"
                              />
                            </div>
                          </div>
                        </div>
                      ))}

                      {searchItems.length === 0 && (
                        <div className="text-center py-8 text-cyan-400/40 text-sm">
                          Click + ADD to specify what you're looking for
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Deploy Button */}
                <button
                  onClick={handleDeploy}
                  disabled={loading || !agentName.trim()}
                  className="w-full py-4 border-2 border-cyan-400 rounded-full text-cyan-400 font-bold hover:border-cyan-300 transition-all disabled:opacity-30 disabled:cursor-not-allowed neon-button text-lg"
                >
                  {loading ? "DEPLOYING..." : "DEPLOY AGENT"}
                </button>
              </>
            )}
            </div>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
