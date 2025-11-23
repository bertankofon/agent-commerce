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
    color: "#0891B2", // Muted Cyan (cyan-600) - UI'a uyumlu
    emoji: "💻",
    description: "Computers, phones, gadgets, and tech accessories"
  },
  FASHION: {
    id: "FASHION",
    name: "Fashion & Apparel",
    color: "#9333EA", // Muted Purple (purple-600) - Daha soft magenta
    emoji: "👗",
    description: "Clothing, shoes, accessories, and fashion items"
  },
  HOME: {
    id: "HOME",
    name: "Home & Living",
    color: "#059669", // Muted Green (emerald-600) - Gölgeli yeşil
    emoji: "🏠",
    description: "Furniture, decor, kitchenware, and home essentials"
  },
  FOOD: {
    id: "FOOD",
    name: "Food & Beverage",
    color: "#D97706", // Muted Amber (amber-600) - Soft altın
    emoji: "🍔",
    description: "Food, drinks, snacks, and culinary products"
  },
  HEALTH: {
    id: "HEALTH",
    name: "Health & Beauty",
    color: "#DB2777", // Muted Pink (pink-600) - Dengeli pembe
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

