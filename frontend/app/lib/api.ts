// Get backend URL from environment variable
// Supports multiple possible variable names
const API_BASE = 
  process.env.NEXT_PUBLIC_NEXT_BACKEND_URL || 
  process.env.NEXT_PUBLIC_next_backend_url ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  'http://localhost:8000';

// Debug: Log the API base URL (only in development)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  console.log('API_BASE:', API_BASE);
  console.log('NEXT_PUBLIC_NEXT_BACKEND_URL:', process.env.NEXT_PUBLIC_NEXT_BACKEND_URL);
  console.log('NEXT_PUBLIC_next_backend_url:', process.env.NEXT_PUBLIC_next_backend_url);
  console.log('NEXT_PUBLIC_BACKEND_URL:', process.env.NEXT_PUBLIC_BACKEND_URL);
}

export async function createAgent(formData: FormData) {
  const res = await fetch(`${API_BASE}/agent/deploy-agent`, {
    method: 'POST',
    body: formData,
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  
  return res.json();
}

export async function getMyAgents(owner: string) {
  const res = await fetch(`${API_BASE}/agent/my-agents?owner=${encodeURIComponent(owner)}`);
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  
  return res.json();
}

export async function getLiveAgents() {
  const res = await fetch(`${API_BASE}/agent/list`);
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  
  return res.json();
}

export async function getAgent(agentId: string) {
  const res = await fetch(`${API_BASE}/agent/${agentId}`);
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  
  return res.json();
}

export async function getAgentProducts(agentId: string) {
  const res = await fetch(`${API_BASE}/agent/${agentId}/products`);
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  
  return res.json();
}

export async function updateAgentStatus(agentId: string, status: string) {
  const res = await fetch(`${API_BASE}/agent/${agentId}/status?status=${status}`, {
    method: 'PATCH',
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  
  return res.json();
}

// Market / Pixel API
export async function getAllPixelClaims() {
  const res = await fetch(`${API_BASE}/market/pixels`);
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  
  return res.json();
}

export async function claimPixels(agentId: string, pixels: Array<{x: number, y: number}>) {
  const res = await fetch(`${API_BASE}/market/pixels/claim`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: agentId, pixels })
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  
  return res.json();
}

export async function getMarketplaceStats() {
  const res = await fetch(`${API_BASE}/market/stats`);
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  
  return res.json();
}

// Future endpoints (not implemented yet in backend)
export async function getAgents() {
  const res = await fetch(`${API_BASE}/api/agents`);
  return res.json();
}

export async function startNegotiation(clientId: string, merchantId: string) {
  const res = await fetch(`${API_BASE}/api/negotiations/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id: clientId, merchant_id: merchantId })
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

export async function getUserNegotiations(userId: string) {
  const res = await fetch(`${API_BASE}/negotiation/list/user/negotiations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId })
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  
  return res.json();
}
