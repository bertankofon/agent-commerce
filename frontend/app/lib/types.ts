export interface Agent {
  id: string;
  name: string;
  type: 'client' | 'merchant';
  config: {
    // Merchant
    product_name?: string;
    initial_price?: number;
    minimum_price?: number;
    stock?: number;
    // Client
    product_type?: string;
    target_price?: number;
    max_price?: number;
    quantity?: number;
  };
  created_at: string;
}

export interface Negotiation {
  id: string;
  client_id: string;
  merchant_id: string;
  client_name?: string;
  merchant_name?: string;
  status: 'in_progress' | 'completed' | 'failed';
  rounds?: Round[];
  final_price?: number;
  quantity?: number;
}

export interface Round {
  round: number;
  speaker: 'client' | 'merchant';
  message: string;
  price?: number;
}

