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
}

export interface UserLoginData {
  privy_user_id: string;
  wallet_address: string;
  email?: string;
  name?: string;
}

export interface User {
  id: string;
  privy_user_id: string;
  wallet_address: string;
  email?: string;
  name?: string;
  created_at: string;
}

export async function loginOrRegisterUser(userData: UserLoginData): Promise<User> {
  const res = await fetch(`${API_BASE}/auth/login-or-register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  
  return res.json();
}

export async function getUserByPrivyId(privyUserId: string): Promise<User> {
  const res = await fetch(`${API_BASE}/auth/user/${privyUserId}`);
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  
  return res.json();
}

