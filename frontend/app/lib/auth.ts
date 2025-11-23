const API_BASE = 'http://localhost:8000';

export interface UserLoginData {
  privy_user_id: string;
  wallet_address: string;
  user_type: 'merchant' | 'client';
  email?: string;
  name?: string;
}

export interface User {
  id: string;
  privy_user_id: string;
  wallet_address: string;
  user_type: 'merchant' | 'client';
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

