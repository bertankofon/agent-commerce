const API_BASE = 'http://localhost:8000';

export async function createAgent(data: any) {
  const res = await fetch(`${API_BASE}/api/agents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function getAgents() {
  const res = await fetch(`${API_BASE}/api/agents`);
  return res.json();
}

export async function startNegotiation(buyerId: string, sellerId: string) {
  const res = await fetch(`${API_BASE}/api/negotiations/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ buyer_id: buyerId, seller_id: sellerId })
  });
  return res.json();
}

export async function getNegotiations() {
  const res = await fetch(`${API_BASE}/api/negotiations`);
  return res.json();
}

export async function getNegotiation(id: string) {
  const res = await fetch(`${API_BASE}/api/negotiations/${id}`);
  return res.json();
}

