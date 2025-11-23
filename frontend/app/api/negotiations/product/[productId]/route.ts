import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/app/lib/supabase';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ productId: string }> }
) {
  try {
    const { productId } = await params;

    if (!productId) {
      return NextResponse.json(
        { success: false, error: 'Product ID is required' },
        { status: 400 }
      );
    }

    // Fetch all negotiations for this product
    const { data: negotiations, error: negotiationsError } = await supabase
      .from('negotiations')
      .select(`
        *,
        client_agent:agents!client_agent_id(id, name, agent_type, category),
        merchant_agent:agents!merchant_agent_id(id, name, agent_type, category)
      `)
      .eq('product_id', productId)
      .order('created_at', { ascending: false });

    if (negotiationsError) {
      console.error('Error fetching negotiations:', negotiationsError);
      return NextResponse.json(
        { success: false, error: negotiationsError.message },
        { status: 500 }
      );
    }

    // For each negotiation, fetch its chat history
    const negotiationsWithHistory = await Promise.all(
      (negotiations || []).map(async (negotiation) => {
        const { data: chatHistory, error: chatError } = await supabase
          .from('agent_chat_history')
          .select(`
            *,
            sender:agents!sender_agent_id(id, name, agent_type),
            receiver:agents!receiver_agent_id(id, name, agent_type)
          `)
          .eq('negotiation_id', negotiation.id)
          .order('round_number', { ascending: true });

        if (chatError) {
          console.error(`Error fetching chat history for negotiation ${negotiation.id}:`, chatError);
        }

        return {
          ...negotiation,
          chat_history: chatHistory || []
        };
      })
    );

    return NextResponse.json({
      success: true,
      negotiations: negotiationsWithHistory,
      count: negotiationsWithHistory.length
    });

  } catch (error: any) {
    console.error('Unexpected error in GET /api/negotiations/product:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

