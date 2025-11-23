"use client";
import { useEffect, useState } from "react";

interface Product {
  id: string;
  name: string;
  price: string;
  stock: number;
  negotiation_percentage: number;
  currency: string;
  description?: string;
  metadata?: any;
  images?: string[]; // Array of image URLs
}

interface ProductsModalProps {
  isOpen: boolean;
  onClose: () => void;
  agentName: string;
  products: Product[];
  loading?: boolean;
}

export default function ProductsModal({ isOpen, onClose, agentName, products, loading = false }: ProductsModalProps) {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 2;
      const y = (e.clientY / window.innerHeight - 0.5) * 2;
      setMousePos({ x, y });
    };

    if (isOpen) {
      window.addEventListener("mousemove", handleMouseMove);
      document.body.style.overflow = "hidden";
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-w-4xl w-full max-h-[80vh] overflow-hidden border-2 border-cyan-400/40 rounded-3xl backdrop-blur-md bg-black/90 shadow-2xl shadow-cyan-500/20"
        style={{
          transform: `perspective(1000px) rotateY(${mousePos.x * 1}deg) rotateX(${-mousePos.y * 1}deg)`,
          transition: "transform 0.3s ease-out",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-cyan-400/20">
          <div>
            <h2 className="text-2xl font-bold text-cyan-300">{agentName}</h2>
            <p className="text-cyan-400/60 text-sm mt-1">{products.length} Products</p>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center rounded-full border-2 border-cyan-400/40 text-cyan-400 hover:border-cyan-400 hover:bg-cyan-400/10 transition-all"
          >
            ✕
          </button>
        </div>

        {/* Products List */}
        <div className="overflow-y-auto max-h-[calc(80vh-100px)] p-6">
          {products.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-cyan-400/60 text-lg">No products available</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {products.map((product) => {
                // Debug: Log product to see images
                console.log("Product data:", product);
                console.log("Product images:", product.images);
                
                return (
                <div
                  key={product.id}
                  className="border-2 border-cyan-400/30 rounded-xl p-4 bg-black/40 hover:border-cyan-400/60 transition-all"
                >
                  {/* Product Image (if available) */}
                  {(product.images && product.images.length > 0) ? (
                    <div className="mb-3">
                      {/* Show first image as main */}
                      <img
                        src={product.images[0]}
                        alt={product.name}
                        className="w-full h-32 object-cover rounded-lg"
                        onError={(e) => {
                          console.error("Image load error:", product.images[0]);
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                      {/* Show thumbnails if more than 1 image */}
                      {product.images.length > 1 && (
                        <div className="flex gap-1 mt-1">
                          {product.images.slice(1).map((img, idx) => (
                            <img
                              key={idx}
                              src={img}
                              alt={`${product.name} - ${idx + 2}`}
                              className="w-10 h-10 object-cover rounded"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none';
                              }}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  ) : product.metadata?.imageUrl ? (
                    <img
                      src={product.metadata.imageUrl}
                      alt={product.name}
                      className="w-full h-32 object-cover rounded-lg mb-3"
                      onError={(e) => {
                        console.error("Metadata image load error:", product.metadata?.imageUrl);
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="w-full h-32 bg-gradient-to-br from-cyan-400/10 to-purple-400/10 rounded-lg mb-3 flex items-center justify-center">
                      <span className="text-cyan-400/40 text-4xl">📦</span>
                    </div>
                  )}

                  {/* Product Name */}
                  <h3 className="text-lg font-bold text-cyan-300 mb-2">
                    {product.name}
                  </h3>

                  {/* Product Description */}
                  {product.description && (
                    <p className="text-cyan-400/60 text-sm mb-3 line-clamp-2">
                      {product.description}
                    </p>
                  )}

                  {/* Product Details */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-cyan-400/60 text-sm">Price:</span>
                      <span className="text-cyan-300 font-bold">
                        ${parseFloat(product.price).toLocaleString()} {product.currency}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-cyan-400/60 text-sm">Stock:</span>
                      <span className={`font-semibold ${
                        product.stock > 10 ? 'text-cyan-300' : 
                        product.stock > 0 ? 'text-orange-400' : 
                        'text-red-400'
                      }`}>
                        {product.stock} units
                      </span>
                    </div>
                  </div>

                  {/* Action Button */}
                  <button className="w-full mt-4 py-2 border border-cyan-400/50 rounded-lg text-cyan-400 hover:border-cyan-400 hover:bg-cyan-400/10 transition-all text-sm font-semibold">
                    Negotiate
                  </button>
                </div>
              )})}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

