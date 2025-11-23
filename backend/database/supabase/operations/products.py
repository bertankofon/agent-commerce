from typing import Optional, Dict, Any, List
from uuid import UUID
from database.supabase.client import get_supabase_client
import logging

logger = logging.getLogger(__name__)


class ProductsOperations:
    """Operations for the products table."""
    
    def __init__(self):
        self.client = get_supabase_client()
        self.table = "products"
    
    def create_product(
        self,
        agent_id: UUID,
        name: str,
        price: str,
        stock: int,
        negotiation_percentage: int,
        description: Optional[str] = None,
        currency: str = "USDC",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new product record in the products table.
        
        Args:
            agent_id: UUID of the merchant agent
            name: Product name
            price: Product price (as string for precision)
            stock: Available stock quantity
            negotiation_percentage: Max discount percentage for negotiation
            description: Product description
            currency: Currency code (default: USDC)
            metadata: Additional metadata (JSON)
        
        Returns:
            Created product record
        """
        try:
            data = {
                "agent_id": str(agent_id),
                "name": name,
                "price": price,
                "stock": stock,
                "negotiation_percentage": negotiation_percentage,
                "currency": currency
            }
            
            if description:
                data["description"] = description
            
            if metadata:
                data["metadata"] = metadata
            
            response = self.client.table(self.table).insert(data).execute()
            
            if not response.data:
                raise ValueError("Failed to create product: no data returned")
            
            logger.info(f"Created product with ID: {response.data[0]['id']}")
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            raise
    
    def create_products_batch(
        self,
        agent_id: UUID,
        products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create multiple products in one batch.
        
        Args:
            agent_id: UUID of the merchant agent
            products: List of product data dicts with keys:
                - name: str
                - price: str or float
                - stock: int
                - negotiation_percentage: int (maxDiscount from frontend)
                - description: Optional[str]
                - imageUrl: Optional[str] (stored in metadata)
        
        Returns:
            List of created product records
        """
        try:
            data_list = []
            
            for product in products:
                product_data = {
                    "agent_id": str(agent_id),
                    "name": product["name"],
                    "price": str(product["price"]),  # Convert to string for precision
                    "stock": product["stock"],
                    "negotiation_percentage": product.get("maxDiscount", product.get("negotiation_percentage", 0)),
                    "currency": "USDC",
                    "description": product.get("name", "")  # Use name as description if not provided
                }
                
                # Store imageUrl in metadata if provided
                if product.get("imageUrl"):
                    product_data["metadata"] = {"imageUrl": product["imageUrl"]}
                
                data_list.append(product_data)
            
            if not data_list:
                logger.warning(f"No products to insert for agent {agent_id}")
                return []
            
            response = self.client.table(self.table).insert(data_list).execute()
            
            if not response.data:
                raise ValueError("Failed to create products: no data returned")
            
            logger.info(f"Created {len(response.data)} products for agent {agent_id}")
            return response.data
            
        except Exception as e:
            logger.error(f"Error creating products batch: {str(e)}")
            raise
    
    def get_products_by_agent(self, agent_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all products for a specific agent.
        
        Args:
            agent_id: UUID of the merchant agent
        
        Returns:
            List of product records
        """
        try:
            response = self.client.table(self.table)\
                .select("*")\
                .eq("agent_id", str(agent_id))\
                .order("created_at", desc=False)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting products for agent {agent_id}: {str(e)}")
            raise
    
    def update_product_stock(
        self,
        product_id: UUID,
        new_stock: int
    ) -> Dict[str, Any]:
        """
        Update product stock quantity.
        
        Args:
            product_id: UUID of the product
            new_stock: New stock quantity
        
        Returns:
            Updated product record
        """
        try:
            response = self.client.table(self.table)\
                .update({"stock": new_stock})\
                .eq("id", str(product_id))\
                .execute()
            
            if not response.data:
                raise ValueError(f"Product {product_id} not found")
            
            logger.info(f"Updated product stock for ID: {product_id}")
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error updating product stock {product_id}: {str(e)}")
            raise

