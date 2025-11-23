/**
 * Marketplace Categories
 * Used for merchant categorization and pixel coloring
 */

export interface Category {
  id: string;
  name: string;
  color: string;
  emoji: string;
  description: string;
}

export const CATEGORIES: Record<string, Category> = {
  TECH: {
    id: "TECH",
    name: "Electronics & Tech",
    color: "#00D9FF", // Cyan
    emoji: "💻",
    description: "Computers, phones, gadgets, and tech accessories"
  },
  FASHION: {
    id: "FASHION",
    name: "Fashion & Apparel",
    color: "#FF00FF", // Magenta
    emoji: "👗",
    description: "Clothing, shoes, accessories, and fashion items"
  },
  HOME: {
    id: "HOME",
    name: "Home & Living",
    color: "#00FF88", // Green
    emoji: "🏠",
    description: "Furniture, decor, kitchenware, and home essentials"
  },
  FOOD: {
    id: "FOOD",
    name: "Food & Beverage",
    color: "#FFD700", // Gold
    emoji: "🍔",
    description: "Food, drinks, snacks, and culinary products"
  },
  HEALTH: {
    id: "HEALTH",
    name: "Health & Beauty",
    color: "#FF6B9D", // Pink
    emoji: "💊",
    description: "Healthcare, cosmetics, wellness, and beauty products"
  }
};

export const CATEGORY_LIST = Object.values(CATEGORIES);

export const getCategoryById = (id: string): Category | undefined => {
  return CATEGORIES[id];
};

export const getCategoryColor = (id: string): string => {
  return CATEGORIES[id]?.color || "#666666";
};

