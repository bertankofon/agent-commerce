# Quick Start Guide - İlk Adımlar

## 🎯 Projenin Şu Anki Durumu

**Özet:** Temel yapı kurulu, ama sistemi çalıştırmak için birçok parça eksik.

### Çalışan Şeyler ✅
- Frontend deploy formu (ama backend'e bağlı değil)
- Backend deploy endpoint'i (ama DB yok, sadece Python spawn ediyor)
- Python agent'ları (ama bağımsız çalışıyor, birbirini bulamıyor)

### Çalışmayan Şeyler ❌
- Agent'lar deploy ediliyor ama veritabanına kaydedilmiyor
- Discovery yok - agentlar birbirini bulamıyor
- Negotiation manuel - otomatik başlamıyor
- UI'da sadece deploy formu var, başka bir şey yok
- Blockchain integration eksik

---

## 🚀 Hemen Başlamak İçin

### Seçenek 1: Minimum Viable Product (Hızlı Demo)
**Hedef:** 1 hafta içinde çalışan demo

**Yapılacaklar:**
1. **Database ekle** (1 gün)
   - PostgreSQL + Prisma
   - Agents tablosu
   
2. **Backend düzenle** (1 gün)
   - Agent CRUD endpoints
   - Agents'ı DB'ye kaydet
   
3. **Discovery servisi** (2 gün)
   - Basit matching algoritması
   - Agents birbirini bulsun
   
4. **Negotiation başlat** (2 gün)
   - Otomatik negotiation trigger
   - Console'da göster
   
5. **Frontend iyileştir** (1 gün)
   - Agent listesi
   - Basit dashboard

**Sonuç:** End-to-end demo working!

### Seçenek 2: Production-Ready (Tam Proje)
**Hedef:** 6-8 hafta içinde production-ready sistem

Roadmap'deki Phase 1-6'yı takip et.

---

## 📝 İlk 3 Gün İçin Detaylı Plan

### Gün 1: Database Setup ⚙️

#### Sabah (4 saat)
```bash
# 1. PostgreSQL kur (local veya cloud)
brew install postgresql  # Mac
# veya
# Docker: docker run -p 5432:5432 -e POSTGRES_PASSWORD=password postgres

# 2. Backend'e Prisma ekle
cd backend
npm install prisma @prisma/client
npx prisma init

# 3. Schema oluştur
# prisma/schema.prisma düzenle (roadmap'teki örnekteki gibi)

# 4. Migration çalıştır
npx prisma migrate dev --name init

# 5. Prisma Client generate et
npx prisma generate
```

**Dosyalar:**
- `backend/prisma/schema.prisma` - Database schema
- `backend/prisma/migrations/` - Migration files
- `backend/src/db/client.ts` - Prisma client instance

#### Öğleden Sonra (4 saat)
```bash
# 6. Seed data ekle
# prisma/seed.ts oluştur

# 7. Test et
npx prisma studio  # GUI'de DB'yi gör
```

**Sonuç:** Database hazır, test data var.

---

### Gün 2: Backend Restructure 🏗️

#### Sabah (4 saat)
```bash
# 1. Backend'i yeniden organize et
mkdir -p backend/src/{controllers,services,routes,types}

# 2. AgentService oluştur
# src/services/agentService.ts
```

**Kod:**
```typescript
// backend/src/services/agentService.ts
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export class AgentService {
  async createAgent(data: any) {
    return await prisma.agent.create({
      data: {
        name: data.name,
        domain: data.domain,
        type: data.type,
        config: data.config,
        status: 'ACTIVE'
      }
    });
  }
  
  async getAllAgents() {
    return await prisma.agent.findMany({
      include: { products: true }
    });
  }
  
  async getAgentById(id: string) {
    return await prisma.agent.findUnique({
      where: { id },
      include: { products: true }
    });
  }
}
```

#### Öğleden Sonra (4 saat)
```typescript
// 3. Routes ekle
// backend/src/routes/agents.ts
import express from 'express';
import { AgentService } from '../services/agentService';

const router = express.Router();
const agentService = new AgentService();

router.get('/', async (req, res) => {
  const agents = await agentService.getAllAgents();
  res.json(agents);
});

router.post('/', async (req, res) => {
  const agent = await agentService.createAgent(req.body);
  res.json(agent);
});

router.get('/:id', async (req, res) => {
  const agent = await agentService.getAgentById(req.params.id);
  res.json(agent);
});

export default router;
```

```typescript
// 4. Main index.ts'yi güncelle
// backend/src/index.ts
import express from 'express';
import cors from 'cors';
import agentRoutes from './routes/agents';

const app = express();
app.use(cors());
app.use(express.json());

app.use('/api/agents', agentRoutes);

app.listen(3001, () => console.log('Backend running on :3001'));
```

**Sonuç:** REST API çalışıyor, agents CRUD yapılabiliyor.

---

### Gün 3: Frontend Update & Discovery 🔍

#### Sabah (4 saat)
```typescript
// 1. Frontend deploy page'i güncelle
// frontend/app/deploy/page.tsx

"use client";
import { useState } from "react";

export default function DeployPage() {
  const [type, setType] = useState("seller");
  const [name, setName] = useState("");
  const [products, setProducts] = useState([]);

  async function deploy() {
    // Create agent in DB first
    const agentRes = await fetch("http://localhost:3001/api/agents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        domain: `${name.toLowerCase()}.agent.com`,
        type: type.toUpperCase(),
        config: { products }
      })
    });

    const agent = await agentRes.json();

    // Then deploy to blockchain
    const deployRes = await fetch("http://localhost:3001/deploy-agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agentType: type,
        config: { 
          name, 
          domain: agent.domain,
          agent_id: agent.id 
        }
      })
    });

    const deployment = await deployRes.json();
    alert(`Deployed! Agent ID: ${agent.id}\nBlockchain: ${deployment.agent_id}`);
  }

  return (
    <div style={{ padding: 40 }}>
      <h1>Deploy Agent</h1>
      {/* ... form ... */}
    </div>
  );
}
```

#### Öğleden Sonra (4 saat)
```typescript
// 2. Discovery service ekle
// backend/src/services/discoveryService.ts

export class DiscoveryService {
  async findMatches(agentId: string) {
    const agent = await prisma.agent.findUnique({
      where: { id: agentId },
      include: { products: true }
    });

    if (agent.type === 'BUYER') {
      // Find sellers
      return await prisma.agent.findMany({
        where: {
          type: 'SELLER',
          status: 'ACTIVE'
        },
        include: { products: true }
      });
    } else {
      // Find buyers
      return await prisma.agent.findMany({
        where: {
          type: 'BUYER',
          status: 'ACTIVE'
        }
      });
    }
  }
}
```

```typescript
// 3. Discovery route ekle
// backend/src/routes/discovery.ts
import express from 'express';
import { DiscoveryService } from '../services/discoveryService';

const router = express.Router();
const discoveryService = new DiscoveryService();

router.get('/matches/:agentId', async (req, res) => {
  const matches = await discoveryService.findMatches(req.params.agentId);
  res.json(matches);
});

export default router;
```

**Sonuç:** Agents deploy edilebiliyor, birbirini bulabiliyor!

---

## 🎬 Demo Akışı (3 Gün Sonra)

```bash
# 1. Start database
docker start postgres  # or brew services start postgresql

# 2. Start backend
cd backend
npm run dev  # port 3001

# 3. Start frontend
cd frontend
npm run dev  # port 3000

# 4. Open browser
# http://localhost:3000/deploy
```

### Demo Senaryosu:
```
1. Deploy Seller Agent
   - Name: "TechStore"
   - Products: [{"name": "Mouse", "stock": 100, "price": 25}]

2. Deploy Buyer Agent
   - Name: "RetailBuyer"
   - Needs: "Mouse", quantity: 50, budget: $30

3. Check discovery
   GET http://localhost:3001/api/discovery/matches/{buyer_id}
   # Should return TechStore

4. Manually trigger negotiation (for now)
   POST http://localhost:3001/api/negotiations
   {
     "buyer_id": "...",
     "seller_id": "..."
   }

5. Watch console for negotiation logs
```

---

## 🛠️ Setup Komutları (Tek Seferde)

```bash
# Clone & Install
git clone git@github.com:bertankofon/agent-commerce.git
cd agent-commerce

# Backend setup
cd backend
npm install
npm install prisma @prisma/client
npx prisma init
# Edit prisma/schema.prisma
npx prisma migrate dev --name init
npx prisma generate

# Frontend setup
cd ../frontend
npm install

# Python setup
cd ../agents
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start everything (3 terminals)
# Terminal 1: Backend
cd backend && npm run dev

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Database GUI (optional)
cd backend && npx prisma studio
```

---

## 📚 Sonraki Adımlar

3 gün sonra elimizde:
- ✅ Database çalışıyor
- ✅ Agents deploy edilebiliyor
- ✅ Agents birbirini bulabiliyor
- ✅ REST API hazır

Sonra:
1. **Week 2:** Automatic negotiation trigger
2. **Week 3:** Real-time dashboard
3. **Week 4:** Blockchain integration

---

## 💡 Pro Tips

1. **Incremental:** Her şeyi bir anda yapmaya çalışma
2. **Test:** Her feature'ı hemen test et
3. **Commit:** Her çalışan feature'ı commit et
4. **Mock:** Blockchain pahalı - başta mock et
5. **Simple:** Önce simple versiyonu yap, sonra optimize et

---

## 🆘 Yardım

Herhangi bir yerde takılırsan:
1. `docs/PROJECT_ROADMAP.md` - Detaylı plan
2. `docs/ARCHITECTURE.md` - System mimarisi
3. GitHub Issues - Soru sor
4. Discord/Slack - Topluluktan yardım al

**Let's start building! 🚀**

