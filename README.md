# Agent Commerce 🤖💰

An autonomous AI agent-based trading and negotiation system with pixel marketplace built on blockchain technology.

## Overview

Agent Commerce enables AI agents to autonomously negotiate and conduct transactions on behalf of buyers and sellers. The system combines the Eliza AI framework with ChaosChain SDK for blockchain-based agent management and payments.

## Architecture

The project consists of three main components:

### 1. Frontend (Next.js)
- Modern React application with TypeScript
- Agent deployment interface
- Real-time negotiation monitoring

### 2. Backend (FastAPI)
- REST API server with FastAPI
- Agent orchestration and negotiation engine
- Supabase PostgreSQL database integration
- LlamaIndex-based AI agents (ShoppingAgent & MerchantAgent)

### 3. AI Agents (Python)
- **Eliza AI Framework**: Provides personality and decision-making
- **ChaosChain SDK**: Blockchain integration on BASE Sepolia testnet
- **Agent Types**:
  - **Seller Agent**: Maximizes profit while remaining reasonable
  - **Buyer Agent**: Negotiates for best possible price

## Features

- 🤖 **Autonomous Negotiation**: AI agents negotiate directly with each other using LlamaIndex
- 💳 **Blockchain Payments**: Secure USDC payments via ChaosChain SDK (x402 protocol) on Base Sepolia
- 🗺️ **Pixel Marketplace**: 75x30 interactive grid where merchants claim territory
- 📦 **Product Management**: Merchants manage inventory with Supabase storage
- 💰 **Agent Funding**: Direct USDC transfers to client agents via MetaMask
- 📊 **Negotiation History**: Track all negotiations with detailed chat history
- 🔐 **Privy Authentication**: Secure wallet-based authentication
- 💬 **Natural Language**: Agents communicate in natural language with structured outputs

## Tech Stack

**Frontend:**
- Next.js 16
- React 19
- TypeScript
- TailwindCSS

**Backend:**
- FastAPI
- Python 3.11+
- LlamaIndex (ReActAgent)
- Supabase (PostgreSQL + Storage)
- OpenAI GPT-4o-mini

**Blockchain:**
- ChaosChain SDK
- Base Sepolia Testnet
- USDC Token (ERC-20)
- x402 Payment Protocol

**Authentication:**
- Privy (Wallet-based auth)
- MetaMask Integration

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agent-commerce
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. Set up backend Python environment:
```bash
cd ../backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
# Backend (.env)
cp .env.example .env
# Add: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY, BASE_SEPOLIA_RPC_URL

# Frontend (.env.local)
# Add: NEXT_PUBLIC_PRIVY_APP_ID, NEXT_PUBLIC_BACKEND_URL, NEXT_PUBLIC_SUPABASE_URL
```

### Running the Application

1. Start the backend server:
```bash
cd backend
npm start
# Server runs on http://localhost:3001
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
# App runs on http://localhost:3000
```

3. Visit `http://localhost:3000/deploy` to deploy agents

## Project Structure

```
agent-commerce/
├── frontend/          # Next.js frontend
│   ├── app/
│   │   ├── deploy/   # Agent deployment page
│   │   └── page.tsx  # Home page
│   └── package.json
├── backend/          # Express.js API server
│   ├── index.ts
│   └── package.json
└── agents/           # Python AI agents
    ├── chaos_agent.py      # ChaosChain SDK integration
    ├── eliza_agent.py      # Eliza AI agent creation
    ├── negotiation.py      # Negotiation logic
    ├── prompts.py          # Agent personalities
    ├── tools.py            # Agent tools (inventory, payment)
    └── run_agent.py        # Main orchestrator
```

## Usage Flow

1. User selects agent type (seller/buyer) in frontend
2. Enters agent name and clicks Deploy
3. Backend spawns Python script
4. Python script:
   - Registers agent on blockchain via ChaosChain SDK
   - Creates Eliza AI agent with personality
   - Attaches tools (inventory check, payment processing)
5. Agent ID is returned to frontend
6. Multiple agents can negotiate with each other autonomously

## Roadmap

- [ ] Real inventory database integration
- [ ] Frontend UI for monitoring active negotiations
- [ ] Authentication and authorization
- [ ] Multi-agent negotiation rooms
- [ ] Transaction history and analytics
- [ ] Advanced payment methods
- [ ] Error handling and retry logic

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

### 🚀 Getting Started
- **[Quick Start Guide](./docs/QUICK_START.md)** - Get up and running in 3 days
- **[Project Roadmap](./docs/PROJECT_ROADMAP.md)** - Complete implementation plan and timeline

### 📖 Technical Documentation
- **[Architecture Guide](./docs/ARCHITECTURE.md)** (Turkish) - Complete system architecture and workflow
- **[Architecture Guide](./docs/ARCHITECTURE_EN.md)** (English) - Complete system architecture and workflow
- **[Deployment Guide](./docs/DEPLOYMENT_GUIDE.md)** - Step-by-step agent deployment instructions
- **[Examples](./docs/EXAMPLES.md)** - Real-world use case scenarios with detailed walkthroughs

## License

ISC

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

