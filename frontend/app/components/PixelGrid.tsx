"use client";

import React, { useState, useMemo } from "react";
import { getCategoryColor, getCategoryById } from "../lib/categories";

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

interface PixelGridProps {
  claims: PixelClaim[];
  gridSize?: number;
  pixelSize?: number;
  onPixelClick?: (claim: PixelClaim | null, x: number, y: number) => void;
  onPixelHover?: (claim: PixelClaim | null, x: number, y: number) => void;
}

export default function PixelGrid({
  claims,
  gridSize = 50,
  pixelSize = 12,
  onPixelClick,
  onPixelHover,
}: PixelGridProps) {
  const [hoveredPixel, setHoveredPixel] = useState<{ x: number; y: number } | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  // Create a map for fast lookup
  const claimsMap = useMemo(() => {
    const map = new Map<string, PixelClaim>();
    claims.forEach((claim) => {
      map.set(`${claim.x},${claim.y}`, claim);
    });
    return map;
  }, [claims]);

  // Group pixels by agent for highlighting
  const agentPixels = useMemo(() => {
    const map = new Map<string, PixelClaim[]>();
    claims.forEach((claim) => {
      if (!map.has(claim.agent_id)) {
        map.set(claim.agent_id, []);
      }
      map.get(claim.agent_id)!.push(claim);
    });
    return map;
  }, [claims]);

  const handlePixelClick = (x: number, y: number) => {
    const claim = claimsMap.get(`${x},${y}`);
    if (claim) {
      setSelectedAgentId(selectedAgentId === claim.agent_id ? null : claim.agent_id);
    }
    onPixelClick?.(claim || null, x, y);
  };

  const handlePixelHover = (x: number, y: number) => {
    setHoveredPixel({ x, y });
    const claim = claimsMap.get(`${x},${y}`);
    onPixelHover?.(claim || null, x, y);
  };

  const renderPixel = (x: number, y: number) => {
    const key = `${x},${y}`;
    const claim = claimsMap.get(key);
    const isHovered = hoveredPixel?.x === x && hoveredPixel?.y === y;
    const isSelectedAgent = claim && selectedAgentId === claim.agent_id;

    let backgroundColor = "#0a0a0a"; // Empty pixel
    let borderColor = "#1a1a1a";
    let opacity = 0.3;

    if (claim) {
      const category = claim.agents?.category || "TECH";
      backgroundColor = getCategoryColor(category);
      opacity = 0.7;
      borderColor = backgroundColor;

      if (isSelectedAgent) {
        opacity = 1;
      }

      if (isHovered) {
        opacity = 0.9;
      }
    }

    return (
      <div
        key={key}
        onClick={() => handlePixelClick(x, y)}
        onMouseEnter={() => handlePixelHover(x, y)}
        onMouseLeave={() => setHoveredPixel(null)}
        style={{
          width: `${pixelSize}px`,
          height: `${pixelSize}px`,
          backgroundColor,
          opacity,
          border: `1px solid ${borderColor}`,
          boxShadow: isHovered ? `0 0 8px ${backgroundColor}` : isSelectedAgent ? `0 0 4px ${backgroundColor}` : "none",
          transition: "all 0.15s ease",
          cursor: claim ? "pointer" : "default",
        }}
        className={`
          ${claim ? "hover:scale-110" : ""}
          ${isSelectedAgent ? "animate-pulse" : ""}
        `}
      />
    );
  };

  return (
    <div className="relative">
      {/* Grid Container */}
      <div
        className="grid gap-0 border-2 border-cyan-400/20 rounded-lg p-2 bg-black/50"
        style={{
          gridTemplateColumns: `repeat(${gridSize}, ${pixelSize}px)`,
          width: "fit-content",
        }}
      >
        {Array.from({ length: gridSize * gridSize }, (_, i) => {
          const x = i % gridSize;
          const y = Math.floor(i / gridSize);
          return renderPixel(x, y);
        })}
      </div>

      {/* Hover Tooltip */}
      {hoveredPixel && (() => {
        const claim = claimsMap.get(`${hoveredPixel.x},${hoveredPixel.y}`);
        if (!claim) return null;

        const category = getCategoryById(claim.agents?.category || "TECH");

        return (
          <div className="absolute top-2 right-2 bg-black/90 border-2 border-cyan-400/50 rounded-lg p-3 backdrop-blur-lg z-10 min-w-[200px]">
            <div className="flex items-center gap-2 mb-2">
              {claim.agents?.avatar_url && (
                <span className="text-2xl">{claim.agents.avatar_url}</span>
              )}
              <div>
                <h4 className="text-cyan-300 font-bold text-sm">
                  {claim.agents?.name || "Unknown Agent"}
                </h4>
                <p className="text-cyan-400/60 text-xs flex items-center gap-1">
                  {category?.emoji} {category?.name}
                </p>
              </div>
            </div>
            <div className="text-cyan-400/40 text-xs">
              Position: ({hoveredPixel.x}, {hoveredPixel.y})
            </div>
            <div className="text-cyan-400/70 text-xs mt-1">
              Click to view details
            </div>
          </div>
        );
      })()}
    </div>
  );
}

