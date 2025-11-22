# Agent Commerce 🤖💰

An autonomous AI agent-based trading and negotiation system built with blockchain technology.

## Overview

Agent Commerce enables AI agents to autonomously negotiate and conduct transactions on behalf of buyers and sellers. The system combines the Eliza AI framework with ChaosChain SDK for blockchain-based agent management and payments.

## Architecture

The project consists of three main components:

### 1. Frontend (Next.js)
- Modern React application with TypeScript
- Agent deployment interface
- Real-time negotiation monitoring

### 2. Backend (Express.js)
- REST API server
- Agent orchestration
- Python agent lifecycle management

### 3. AI Agents (Python)
- **Eliza AI Framework**: Provides personality and decision-making
- **ChaosChain SDK**: Blockchain integration on BASE Sepolia testnet
- **Agent Types**:
  - **Seller Agent**: Maximizes profit while remaining reasonable
  - **Buyer Agent**: Negotiates for best possible price

## Features

- 🤖 **Autonomous Negotiation**: AI agents negotiate directly with each other
- 💳 **Blockchain Payments**: Secure payments via ChaosChain SDK
- 📦 **Inventory Management**: Real-time stock checking
- 🔐 **Process Integrity**: AP2 protocol for secure agent communication
- 💬 **Natural Language**: Agents communicate in natural language with structured JSON outputs

## Tech Stack

**Frontend:**
- Next.js 16
- React 19
- TypeScript
- TailwindCSS

**Backend:**
- Express.js 5
- TypeScript
- CORS

**AI/Blockchain:**
- Python 3.11
- Eliza AI Framework
- ChaosChain SDK
- BASE Sepolia Testnet
- GPT-4.1-mini

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

3. Install backend dependencies:
```bash
cd ../backend
npm install
```

4. Set up Python virtual environment:
```bash
cd ../agents
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
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

## License

ISC

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

