import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || '';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_SERVICE_KEY || '';

if (!supabaseUrl || !supabaseKey) {
  console.warn('⚠️ Supabase credentials not found in environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
  }
});

// Database types
export interface Negotiation {
  id: string;
  session_id: string;
  client_agent_id: string;
  merchant_agent_id: string;
  product_id: string;
  initial_price: number;
  final_price: number | null;
  negotiation_percentage: number | null;
  budget: number | null;
  agreed: boolean;
  status: 'in_progress' | 'agreed' | 'rejected' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface ChatHistory {
  id: string;
  negotiation_id: string;
  round_number: number;
  sender_agent_id: string;
  receiver_agent_id: string;
  message: string;
  proposed_price: number;
  accept: boolean;
  reason: string | null;
  created_at: string;
}

export interface Agent {
  id: string;
  name: string;
  agent_type: string;
  category?: string;
  owner?: string;
}

export interface Product {
  id: string;
  name: string;
  price: number;
  image_url?: string;
}

