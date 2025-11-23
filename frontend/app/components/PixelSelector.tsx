"use client";

import React, { useState, useMemo, useEffect } from "react";
import { getCategoryColor } from "../lib/categories";

interface PixelSelectorProps {
  occupiedPixels: Array<{ x: number; y: number }>;
  selectedPixels: Array<{ x: number; y: number }>;
  onSelectionChange: (pixels: Array<{ x: number; y: number }>) => void;
  category: string;
  gridWidth?: number;
  gridHeight?: number;
  pixelSize?: number;
  maxPixels?: number;
}

export default function PixelSelector({
  occupiedPixels,
  selectedPixels,
  onSelectionChange,
  category,
  gridWidth = 75,
  gridHeight = 30,
  pixelSize = 10,
  maxPixels = 150,
}: PixelSelectorProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(null);
  const [dragEnd, setDragEnd] = useState<{ x: number; y: number } | null>(null);

  // Create set of occupied pixels for fast lookup
  const occupiedSet = useMemo(() => {
    const set = new Set<string>();
    occupiedPixels.forEach(({ x, y }) => set.add(`${x},${y}`));
    return set;
  }, [occupiedPixels]);

  // Create set of selected pixels
  const selectedSet = useMemo(() => {
    const set = new Set<string>();
    selectedPixels.forEach(({ x, y }) => set.add(`${x},${y}`));
    return set;
  }, [selectedPixels]);

  const handleMouseDown = (x: number, y: number) => {
    if (occupiedSet.has(`${x},${y}`)) return;
    setIsDragging(true);
    setDragStart({ x, y });
    setDragEnd({ x, y });
  };

  const handleMouseMove = (x: number, y: number) => {
    if (!isDragging || !dragStart) return;
    setDragEnd({ x, y });
  };

  const handleMouseUp = () => {
    if (!isDragging || !dragStart || !dragEnd) return;

    // Calculate rectangle bounds
    const minX = Math.min(dragStart.x, dragEnd.x);
    const maxX = Math.max(dragStart.x, dragEnd.x);
    const minY = Math.min(dragStart.y, dragEnd.y);
    const maxY = Math.max(dragStart.y, dragEnd.y);

    // Collect pixels in rectangle (excluding occupied ones)
    const newPixels: Array<{ x: number; y: number }> = [];
    for (let x = minX; x <= maxX; x++) {
      for (let y = minY; y <= maxY; y++) {
        if (!occupiedSet.has(`${x},${y}`)) {
          newPixels.push({ x, y });
        }
      }
    }

    // Check max limit
    if (newPixels.length > maxPixels) {
      alert(`Maximum ${maxPixels} pixels allowed. You selected ${newPixels.length}.`);
      setIsDragging(false);
      setDragStart(null);
      setDragEnd(null);
      return;
    }

    onSelectionChange(newPixels);
    setIsDragging(false);
    setDragStart(null);
    setDragEnd(null);
  };

  const handleClear = () => {
    onSelectionChange([]);
  };

  const isInDragArea = (x: number, y: number): boolean => {
    if (!isDragging || !dragStart || !dragEnd) return false;
    const minX = Math.min(dragStart.x, dragEnd.x);
    const maxX = Math.max(dragStart.x, dragEnd.x);
    const minY = Math.min(dragStart.y, dragEnd.y);
    const maxY = Math.max(dragStart.y, dragEnd.y);
    return x >= minX && x <= maxX && y >= minY && y <= maxY;
  };

  const renderPixel = (x: number, y: number) => {
    const key = `${x},${y}`;
    const isOccupied = occupiedSet.has(key);
    const isSelected = selectedSet.has(key);
    const isInDrag = isInDragArea(x, y);

    let backgroundColor = "#0a0a0a";
    let borderColor = "#1a1a1a";
    let opacity = 0.2;
    let cursor = "crosshair";

    if (isOccupied) {
      backgroundColor = "#666666";
      opacity = 0.4;
      cursor = "not-allowed";
    } else if (isSelected) {
      backgroundColor = getCategoryColor(category);
      opacity = 0.6; // Daha soft seçim
      borderColor = getCategoryColor(category);
    } else if (isInDrag && !isOccupied) {
      backgroundColor = getCategoryColor(category);
      opacity = 0.4; // Daha soft drag preview
      borderColor = getCategoryColor(category);
    }

    return (
      <div
        key={key}
        onMouseDown={() => handleMouseDown(x, y)}
        onMouseMove={() => handleMouseMove(x, y)}
        onMouseUp={handleMouseUp}
        style={{
          width: `${pixelSize}px`,
          height: `${pixelSize}px`,
          backgroundColor,
          opacity,
          border: `1px solid ${borderColor}`,
          cursor,
          transition: "all 0.1s ease",
        }}
        className={`
          ${!isOccupied && !isSelected ? "hover:bg-cyan-400/30" : ""}
          ${isSelected ? "shadow-sm" : ""}
        `}
      />
    );
  };

  const getDragDimensions = () => {
    if (!isDragging || !dragStart || !dragEnd) return { width: 0, height: 0, count: 0 };
    const width = Math.abs(dragEnd.x - dragStart.x) + 1;
    const height = Math.abs(dragEnd.y - dragStart.y) + 1;
    
    // Count only non-occupied pixels
    let count = 0;
    const minX = Math.min(dragStart.x, dragEnd.x);
    const maxX = Math.max(dragStart.x, dragEnd.x);
    const minY = Math.min(dragStart.y, dragEnd.y);
    const maxY = Math.max(dragStart.y, dragEnd.y);
    
    for (let x = minX; x <= maxX; x++) {
      for (let y = minY; y <= maxY; y++) {
        if (!occupiedSet.has(`${x},${y}`)) {
          count++;
        }
      }
    }
    
    return { width, height, count };
  };

  const dragDims = getDragDimensions();

  return (
    <div className="space-y-3">
      {/* Info Bar */}
      <div className="flex justify-between items-center text-sm">
        <div className="text-cyan-400/80">
          <span className="font-bold text-cyan-300">{selectedPixels.length}</span> / {maxPixels} pixels selected
          {selectedPixels.length > 0 && (
            <span className="text-cyan-400/60 ml-2">
              = Max {selectedPixels.length} products
            </span>
          )}
        </div>
        {selectedPixels.length > 0 && (
          <button
            onClick={handleClear}
            className="text-xs px-3 py-1 border border-red-400/50 text-red-400 rounded hover:bg-red-400/10 transition-all"
          >
            Clear Selection
          </button>
        )}
      </div>

      {/* Drag Info */}
      {isDragging && (
        <div className="text-xs text-cyan-400/60 animate-pulse">
          Selecting: {dragDims.width}×{dragDims.height} = {dragDims.count} pixels
          {dragDims.count > maxPixels && (
            <span className="text-red-400 ml-2">⚠ Exceeds max limit!</span>
          )}
        </div>
      )}

      {/* Grid */}
      <div
        className="grid gap-0 border-2 border-cyan-400/30 rounded-lg p-2 bg-black/30 select-none"
        style={{
          gridTemplateColumns: `repeat(${gridWidth}, ${pixelSize}px)`,
          width: "fit-content",
        }}
        onMouseLeave={() => {
          if (isDragging) {
            setIsDragging(false);
            setDragStart(null);
            setDragEnd(null);
          }
        }}
      >
        {Array.from({ length: gridWidth * gridHeight }, (_, i) => {
          const x = i % gridWidth;
          const y = Math.floor(i / gridWidth);
          return renderPixel(x, y);
        })}
      </div>

      {/* Legend */}
      <div className="flex gap-4 text-xs text-cyan-400/60">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-black/50 border border-cyan-400/30" />
          <span>Available</span>
        </div>
        <div className="flex items-center gap-1">
          <div
            className="w-3 h-3 border"
            style={{
              backgroundColor: getCategoryColor(category),
              borderColor: getCategoryColor(category),
              opacity: 0.6,
            }}
          />
          <span>Your Selection</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-gray-600" />
          <span>Occupied</span>
        </div>
      </div>

      {/* Instructions */}
      <div className="text-xs text-cyan-400/40 border border-cyan-400/20 rounded-lg p-2 bg-black/20">
        💡 <strong>Tip:</strong> Click and drag to select a rectangular area. Selected pixels = max products you can list.
      </div>
    </div>
  );
}

