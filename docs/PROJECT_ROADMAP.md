# Agent Commerce - Project Roadmap & Implementation Plan

## 📊 Current State Analysis (Mevcut Durum)

### ✅ What We Have (Elimizde Ne Var?)

#### 1. **Frontend (Next.js)**
```
✅ Basic Next.js 16 setup
✅ Deploy page with simple form
✅ TailwindCSS configured
❌ No dashboard/monitoring UI
❌ No negotiation viewer
❌ No transaction history
❌ No real-time updates
```

**Files:**
- `frontend/app/deploy/page.tsx` - Basic deployment form
- `frontend/app/page.tsx` - Default landing page (needs customization)
- `frontend/app/layout.tsx` - Root layout

#### 2. **Backend (Express.js)**
```
✅ Basic Express server setup
✅ CORS configured
✅ /deploy-agent endpoint (spawns Python)
❌ No agent management endpoints
❌ No negotiation orchestration
❌ No discovery service
❌ No WebSocket for real-time updates
❌ No database integration
```

**Files:**
- `backend/index.ts` - Basic server with one endpoint

#### 3. **AI Agents (Python)**
```
✅ chaos_agent.py - ChaosChain SDK integration
✅ eliza_agent.py - Eliza AI wrapper
✅ prompts.py - Basic seller/buyer prompts
✅ tools.py - Mock inventory & payment tools
✅ negotiation.py - Basic negotiation loop
✅ run_agent.py - Agent orchestrator
❌ No real inventory management
❌ No discovery mechanism
❌ No persistent agent storage
❌ No learning/adaptation system
```

### ❌ What's Missing (Eksikler)

1. **Database** - No data persistence
2. **Discovery Service** - Agents can't find each other
3. **Negotiation Orchestration** - No system to connect agents
4. **Real-time Communication** - No WebSocket/live updates
5. **Agent Management** - No CRUD operations for agents
6. **Transaction System** - No actual blockchain integration
7. **UI Components** - Limited frontend interfaces
8. **Testing** - No tests whatsoever

---

## 🎯 Implementation Strategy (Uygulama Stratejisi)

### Phase 1: Foundation (Week 1-2) 🏗️
**Goal:** Get basic end-to-end flow working

#### 1.1 Database Setup
```
Priority: HIGH
Complexity: Medium
Time: 2-3 days
```

**Tasks:**
- [ ] Choose database (PostgreSQL recommended)
- [ ] Design schema:
  - `agents` table (id, name, type, config, status, blockchain_address)
  - `products` table (id, agent_id, name, stock, pricing)
  - `negotiations` table (id, buyer_id, seller_id, status, messages)
  - `transactions` table (id, negotiation_id, amount, status, blockchain_tx)
- [ ] Setup Prisma ORM
- [ ] Create migration scripts
- [ ] Add seed data for testing

**Files to Create:**
```
backend/prisma/schema.prisma
backend/prisma/migrations/
backend/src/db/client.ts
backend/src/db/seed.ts
```

**Example Schema:**
```prisma
// prisma/schema.prisma
model Agent {
  id                String   @id @default(uuid())
  name              String   @unique
  domain            String   @unique
  type              AgentType
  config            Json
  status            AgentStatus @default(ACTIVE)
  blockchain_address String?
  created_at        DateTime @default(now())
  updated_at        DateTime @updatedAt
  
  products          Product[]
  negotiations_as_buyer  Negotiation[] @relation("buyer")
  negotiations_as_seller Negotiation[] @relation("seller")
}

model Product {
  id          String   @id @default(uuid())
  agent_id    String
  sku         String   @unique
  name        String
  stock       Int
  pricing     Json
  attributes  Json
  
  agent       Agent    @relation(fields: [agent_id], references: [id])
}

model Negotiation {
  id          String   @id @default(uuid())
  buyer_id    String
  seller_id   String
  product_id  String
  status      NegotiationStatus @default(IN_PROGRESS)
  rounds      Json[]
  final_terms Json?
  created_at  DateTime @default(now())
  
  buyer       Agent    @relation("buyer", fields: [buyer_id], references: [id])
  seller      Agent    @relation("seller", fields: [seller_id], references: [id])
  transaction Transaction?
}

model Transaction {
  id              String   @id @default(uuid())
  negotiation_id  String   @unique
  amount          Decimal
  currency        String   @default("USD")
  blockchain_tx   String?
  status          TransactionStatus @default(PENDING)
  created_at      DateTime @default(now())
  
  negotiation     Negotiation @relation(fields: [negotiation_id], references: [id])
}

enum AgentType {
  SELLER
  BUYER
}

enum AgentStatus {
  ACTIVE
  PAUSED
  STOPPED
}

enum NegotiationStatus {
  DISCOVERING
  IN_PROGRESS
  AGREED
  REJECTED
  TIMEOUT
}

enum TransactionStatus {
  PENDING
  PROCESSING
  COMPLETED
  FAILED
}
```

#### 1.2 Backend API Expansion
```
Priority: HIGH
Complexity: Medium
Time: 3-4 days
```

**Tasks:**
- [ ] Restructure backend with proper architecture:
  - Controllers
  - Services
  - Routes
  - Middleware
- [ ] Implement core endpoints:
  - `POST /api/agents` - Create agent
  - `GET /api/agents` - List all agents
  - `GET /api/agents/:id` - Get agent details
  - `PATCH /api/agents/:id` - Update agent config
  - `DELETE /api/agents/:id` - Delete agent
  - `POST /api/agents/:id/pause` - Pause agent
  - `POST /api/agents/:id/resume` - Resume agent
- [ ] Add validation middleware
- [ ] Add error handling
- [ ] Add logging

**Directory Structure:**
```
backend/
├── src/
│   ├── controllers/
│   │   ├── agentController.ts
│   │   ├── negotiationController.ts
│   │   └── transactionController.ts
│   ├── services/
│   │   ├── agentService.ts
│   │   ├── discoveryService.ts
│   │   └── pythonBridge.ts
│   ├── routes/
│   │   ├── agents.ts
│   │   ├── negotiations.ts
│   │   └── transactions.ts
│   ├── middleware/
│   │   ├── validation.ts
│   │   ├── errorHandler.ts
│   │   └── logger.ts
│   ├── types/
│   │   └── index.ts
│   └── index.ts
├── package.json
└── tsconfig.json
```

#### 1.3 Agent Persistence
```
Priority: HIGH
Complexity: Low
Time: 1-2 days
```

**Tasks:**
- [ ] Modify `run_agent.py` to save agent to DB
- [ ] Create agent management CLI
- [ ] Add agent status tracking
- [ ] Implement agent lifecycle management

**Files to Modify:**
```python
# agents/run_agent.py
import sys, json
import requests
from chaos_agent import create_chaos_agent
from eliza_agent import create_eliza_agent
from prompts import SELLER_PROMPT, BUYER_PROMPT
from tools import build_tools
from chaoschain_sdk import AgentRole

def deploy_agent(agent_type, config):
    # Determine role and prompt
    if agent_type == "seller":
        role = AgentRole.SERVER
        prompt = SELLER_PROMPT
    else:
        role = AgentRole.CLIENT
        prompt = BUYER_PROMPT
    
    # Create agents
    sdk, agent_id = create_chaos_agent(config["name"], config["domain"], role)
    eliza = create_eliza_agent(prompt)
    eliza.tools = build_tools(sdk)
    
    # Save to database via backend API
    agent_data = {
        "id": agent_id,
        "name": config["name"],
        "domain": config["domain"],
        "type": agent_type,
        "config": config,
        "blockchain_address": sdk.get_address(),
        "status": "active"
    }
    
    # Register with backend
    response = requests.post(
        "http://localhost:3001/api/agents/register",
        json=agent_data
    )
    
    return {
        "agent_id": agent_id,
        "status": "deployed",
        "blockchain_address": sdk.get_address()
    }

if __name__ == "__main__":
    agent_type = sys.argv[1]
    config = json.loads(sys.argv[2])
    result = deploy_agent(agent_type, config)
    print(json.dumps(result))
```

---

### Phase 2: Discovery & Matching (Week 3) 🔍
**Goal:** Enable agents to find each other

#### 2.1 Discovery Service
```
Priority: HIGH
Complexity: Medium
Time: 3-4 days
```

**Tasks:**
- [ ] Implement matching algorithm
- [ ] Create discovery endpoints:
  - `POST /api/discovery/search` - Find compatible agents
  - `GET /api/discovery/matches/:agent_id` - Get matches for agent
- [ ] Build matching criteria logic:
  - Product compatibility
  - Price range overlap
  - Stock availability
  - Payment method compatibility
- [ ] Add caching for performance

**Implementation:**
```typescript
// backend/src/services/discoveryService.ts
export class DiscoveryService {
  async findMatches(agentId: string): Promise<Agent[]> {
    const agent = await db.agent.findUnique({
      where: { id: agentId },
      include: { products: true }
    });
    
    if (!agent) throw new Error('Agent not found');
    
    if (agent.type === 'BUYER') {
      return this.findSellersForBuyer(agent);
    } else {
      return this.findBuyersForSeller(agent);
    }
  }
  
  private async findSellersForBuyer(buyer: Agent): Promise<Agent[]> {
    const requirements = buyer.config.requirements;
    
    // Find sellers with matching products
    const sellers = await db.agent.findMany({
      where: {
        type: 'SELLER',
        status: 'ACTIVE',
        products: {
          some: {
            name: {
              contains: requirements.product_type,
              mode: 'insensitive'
            },
            stock: {
              gte: requirements.quantity
            }
          }
        }
      },
      include: { products: true }
    });
    
    // Filter by price compatibility
    return sellers.filter(seller => {
      const product = seller.products[0];
      const minPrice = product.pricing.minimum_price;
      const maxBudget = requirements.max_unit_price;
      
      return minPrice <= maxBudget;
    });
  }
  
  private async findBuyersForSeller(seller: Agent): Promise<Agent[]> {
    const products = seller.products;
    
    return db.agent.findMany({
      where: {
        type: 'BUYER',
        status: 'ACTIVE',
        // Match buyers looking for our products
      },
      include: { config: true }
    });
  }
}
```

#### 2.2 Python Discovery Integration
```
Priority: MEDIUM
Complexity: Low
Time: 1-2 days
```

**Tasks:**
- [ ] Create `agents/discovery.py`
- [ ] Add discovery client to agent loop
- [ ] Implement automatic matching trigger

---

### Phase 3: Negotiation System (Week 4-5) 🤝
**Goal:** Enable autonomous negotiation between agents

#### 3.1 Negotiation Orchestrator
```
Priority: HIGH
Complexity: HIGH
Time: 4-5 days
```

**Tasks:**
- [ ] Build negotiation room manager
- [ ] Implement message queue system
- [ ] Create negotiation state machine
- [ ] Add round tracking and timeout logic
- [ ] Implement agreement detection

**Implementation:**
```typescript
// backend/src/services/negotiationService.ts
export class NegotiationService {
  async startNegotiation(buyerId: string, sellerId: string, productId: string) {
    // Create negotiation record
    const negotiation = await db.negotiation.create({
      data: {
        buyer_id: buyerId,
        seller_id: sellerId,
        product_id: productId,
        status: 'IN_PROGRESS',
        rounds: []
      }
    });
    
    // Trigger Python agents to start negotiating
    await this.triggerPythonNegotiation(negotiation.id);
    
    return negotiation;
  }
  
  async addRound(negotiationId: string, round: NegotiationRound) {
    const negotiation = await db.negotiation.findUnique({
      where: { id: negotiationId }
    });
    
    const rounds = [...negotiation.rounds, round];
    
    // Check for agreement
    const agreed = this.checkAgreement(round);
    
    await db.negotiation.update({
      where: { id: negotiationId },
      data: {
        rounds,
        status: agreed ? 'AGREED' : 'IN_PROGRESS',
        final_terms: agreed ? round.terms : null
      }
    });
    
    // If agreed, trigger transaction
    if (agreed) {
      await this.transactionService.createTransaction(negotiationId, round.terms);
    }
    
    return rounds;
  }
  
  private checkAgreement(round: NegotiationRound): boolean {
    const message = round.message.toLowerCase();
    return message.includes('accept') || 
           message.includes('deal') || 
           message.includes('agreed');
  }
}
```

#### 3.2 Enhanced Python Negotiation
```
Priority: HIGH
Complexity: MEDIUM
Time: 3-4 days
```

**Tasks:**
- [ ] Rewrite `agents/negotiation.py` with proper logic
- [ ] Add strategy patterns for different agent types
- [ ] Implement learning mechanism
- [ ] Add negotiation analytics

**Enhanced Implementation:**
```python
# agents/negotiation.py
import asyncio
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import requests

@dataclass
class NegotiationRound:
    round_number: int
    speaker: str  # 'buyer' or 'seller'
    message: str
    offer: Dict
    timestamp: str

class NegotiationEngine:
    def __init__(self, buyer_agent, seller_agent, negotiation_id: str):
        self.buyer = buyer_agent
        self.seller = seller_agent
        self.negotiation_id = negotiation_id
        self.rounds: List[NegotiationRound] = []
        self.max_rounds = 10
        self.backend_url = "http://localhost:3001"
    
    async def run(self) -> Dict:
        """Main negotiation loop"""
        
        # Round 1: Seller makes initial offer
        seller_offer = await self.seller.run("Make your initial offer.")
        self.log_round(1, 'seller', seller_offer)
        
        for round_num in range(2, self.max_rounds + 1):
            # Buyer responds
            buyer_response = await self.buyer.run(
                f"Seller's offer: {seller_offer}. Make your counter-offer or accept."
            )
            self.log_round(round_num, 'buyer', buyer_response)
            
            # Check for acceptance
            if self.is_acceptance(buyer_response):
                return self.finalize_agreement(seller_offer)
            
            # Seller responds to counter-offer
            seller_response = await self.seller.run(
                f"Buyer's counter-offer: {buyer_response}. Respond or accept."
            )
            self.log_round(round_num, 'seller', seller_response)
            
            # Check for acceptance
            if self.is_acceptance(seller_response):
                return self.finalize_agreement(buyer_response)
            
            seller_offer = seller_response
        
        # Timeout - no agreement
        return {
            "status": "TIMEOUT",
            "rounds": len(self.rounds),
            "message": "No agreement reached after maximum rounds"
        }
    
    def log_round(self, round_num: int, speaker: str, message: str):
        """Log round to backend"""
        round_data = NegotiationRound(
            round_number=round_num,
            speaker=speaker,
            message=message,
            offer=self.extract_offer(message),
            timestamp=datetime.now().isoformat()
        )
        
        self.rounds.append(round_data)
        
        # Send to backend
        requests.post(
            f"{self.backend_url}/api/negotiations/{self.negotiation_id}/rounds",
            json=round_data.__dict__
        )
    
    def is_acceptance(self, message: str) -> bool:
        """Check if message indicates acceptance"""
        keywords = ['accept', 'deal', 'agreed', 'yes', 'ok']
        return any(keyword in message.lower() for keyword in keywords)
    
    def extract_offer(self, message: str) -> Dict:
        """Extract structured offer from message"""
        # Use LLM to extract JSON from natural language
        # For now, simple regex or keyword matching
        pass
    
    def finalize_agreement(self, final_offer: str) -> Dict:
        """Mark negotiation as complete"""
        return {
            "status": "AGREED",
            "final_offer": final_offer,
            "rounds": len(self.rounds),
            "terms": self.extract_offer(final_offer)
        }


async def negotiate(buyer_id: str, seller_id: str, product_id: str):
    """Main entry point for negotiation"""
    
    # Load agents from database
    buyer_agent = load_agent(buyer_id)
    seller_agent = load_agent(seller_id)
    
    # Create negotiation record
    response = requests.post(
        "http://localhost:3001/api/negotiations",
        json={
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "product_id": product_id
        }
    )
    negotiation_id = response.json()['id']
    
    # Run negotiation
    engine = NegotiationEngine(buyer_agent, seller_agent, negotiation_id)
    result = await engine.run()
    
    return result
```

---

### Phase 4: Real-time UI (Week 5-6) 📱
**Goal:** Beautiful, live-updating dashboard

#### 4.1 WebSocket Integration
```
Priority: MEDIUM
Complexity: MEDIUM
Time: 2-3 days
```

**Tasks:**
- [ ] Add Socket.IO to backend
- [ ] Create WebSocket events:
  - `agent:deployed`
  - `negotiation:started`
  - `negotiation:round`
  - `negotiation:completed`
  - `transaction:processing`
  - `transaction:completed`
- [ ] Add client-side socket connection

#### 4.2 Dashboard UI
```
Priority: HIGH
Complexity: MEDIUM-HIGH
Time: 4-5 days
```

**Tasks:**
- [ ] Create dashboard layout
- [ ] Build components:
  - Agent list with status
  - Active negotiations viewer
  - Transaction history
  - Real-time negotiation chat viewer
  - Analytics charts
- [ ] Add filtering and search
- [ ] Implement responsive design

**Pages to Create:**
```
frontend/app/dashboard/page.tsx          - Main dashboard
frontend/app/agents/page.tsx             - Agent management
frontend/app/agents/[id]/page.tsx        - Single agent view
frontend/app/negotiations/page.tsx       - Active negotiations
frontend/app/negotiations/[id]/page.tsx  - Single negotiation viewer
frontend/app/transactions/page.tsx       - Transaction history
```

---

### Phase 5: Blockchain Integration (Week 7) ⛓️
**Goal:** Real blockchain payments

#### 5.1 Smart Contract Development
```
Priority: HIGH
Complexity: HIGH
Time: 3-4 days
```

**Tasks:**
- [ ] Write Solidity smart contracts:
  - Agent Registry contract
  - Escrow contract
  - Payment contract
- [ ] Deploy to BASE Sepolia testnet
- [ ] Add contract interaction to Python SDK

#### 5.2 Payment Processing
```
Priority: HIGH
Complexity: MEDIUM
Time: 2-3 days
```

**Tasks:**
- [ ] Implement wallet connection (Web3)
- [ ] Add transaction signing
- [ ] Build escrow flow
- [ ] Add transaction verification

---

### Phase 6: Polish & Testing (Week 8) ✨
**Goal:** Production-ready system

#### 6.1 Testing
```
Priority: HIGH
Complexity: MEDIUM
Time: 3-4 days
```

**Tasks:**
- [ ] Unit tests for backend services
- [ ] Integration tests for API endpoints
- [ ] E2E tests for complete flows
- [ ] Test agent negotiation scenarios
- [ ] Load testing

#### 6.2 Documentation & Polish
```
Priority: MEDIUM
Complexity: LOW
Time: 2-3 days
```

**Tasks:**
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Update README with setup instructions
- [ ] Add inline code documentation
- [ ] Create video demo
- [ ] UI/UX improvements

---

## 🔄 Development Flow (Günlük İş Akışı)

### Daily Workflow
```
1. Morning: Review previous day's work
2. Pick highest priority task from current phase
3. Implement feature
4. Test locally
5. Commit with descriptive message
6. Push to GitHub
7. Update roadmap progress
8. Evening: Plan next day's tasks
```

### Git Workflow
```bash
# Feature branch workflow
git checkout -b feature/discovery-service
# ... work on feature ...
git add .
git commit -m "feat: implement discovery service with matching algorithm"
git push origin feature/discovery-service
# Create PR, review, merge
```

---

## 📦 Technology Decisions

### Database: PostgreSQL
**Why?**
- Reliable, mature
- Good JSON support (for flexible agent configs)
- Excellent with Prisma ORM
- Free tier on Railway/Supabase

### Real-time: Socket.IO
**Why?**
- Easy to use
- Works with Next.js
- Auto-reconnection
- Room-based broadcasting

### State Management: Zustand
**Why?**
- Lightweight
- Simple API
- Good TypeScript support
- No boilerplate

### Styling: TailwindCSS + shadcn/ui
**Why?**
- Already in project
- Fast development
- Beautiful components
- Consistent design

---

## 🎯 Success Metrics

### MVP Success (After Phase 3)
- [ ] Deploy 2 agents (1 buyer, 1 seller)
- [ ] Agents discover each other automatically
- [ ] Complete negotiation automatically
- [ ] Reach agreement and log final terms

### Full Success (After Phase 6)
- [ ] 10+ agents running simultaneously
- [ ] Multiple concurrent negotiations
- [ ] Real blockchain transactions
- [ ] <2s latency for negotiations
- [ ] Beautiful, intuitive UI

---

## 🚨 Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| ChaosChain SDK issues | HIGH | Mock/stub SDK initially |
| Eliza AI costs | MEDIUM | Use cheaper models for testing |
| Complex negotiation logic | HIGH | Start simple, iterate |
| Blockchain gas costs | MEDIUM | Use testnet, optimize contracts |
| Real-time scaling | MEDIUM | Use Redis for pub/sub if needed |

---

## 💰 Cost Estimate

### Development Phase (Testnet)
- Database: $0 (free tier)
- Blockchain: ~$50 (testnet faucet)
- AI API: ~$20-50 (development)
- Total: **~$70-100**

### Production
- Database: $25/month
- Server: $20/month
- Blockchain gas: Variable
- AI API: $200-500/month (depends on volume)
- Total: **~$245-545/month**

---

## 📈 Next Steps

### Immediate (This Week)
1. ✅ Setup database (PostgreSQL + Prisma)
2. ✅ Restructure backend with proper architecture
3. ✅ Implement agent CRUD endpoints
4. ✅ Update frontend deploy form to use new API

### Week 2
1. Build discovery service
2. Create negotiation orchestrator
3. Enhanced negotiation logic in Python

### Week 3-4
1. Real-time updates with WebSocket
2. Dashboard UI
3. Negotiation viewer

---

**Let's build this! 🚀**

