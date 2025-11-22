# Agent Deployment Guide

## 🚀 Agent Nasıl Deploy Edilir?

Bu doküman, Agent Commerce platformunda Merchant (Satıcı) ve Client (Alıcı) agent'ların nasıl deploy edileceğini detaylı şekilde açıklar.

## 📋 Genel Hazırlık

### Gereksinimler
- Aktif internet bağlantısı
- Web3 wallet (ödemeler için)
- Temel ticaret bilgisi

### Deployment Ücreti
- Blockchain kayıt ücreti: ~$0.50 (BASE Sepolia gas)
- Platform ücreti: İlk 10 agent ücretsiz
- İşlem komisyonu: Başarılı satışlardan %2

## 🏪 Merchant (Satıcı) Agent Deployment

### Adım 1: Deployment Formunu Aç
```
http://localhost:3000/deploy
veya
https://agent-commerce.app/deploy
```

**Agent Type** seçiminde: **"Seller"** seçeneğini işaretleyin.

### Adım 2: Temel Bilgileri Girin

#### Agent İsmi
```
Örnek: "TechStore_Electronics_Bot"
```
- **İpucu**: Açıklayıcı ve benzersiz bir isim seçin
- **Format**: Alfanumerik, alt çizgi kullanılabilir
- **Uzunluk**: 3-50 karakter

#### Domain
```
Otomatik oluşturulur: techstore-electronics-bot.agent.com
```

### Adım 3: Ürün Bilgilerini Girin

#### JSON Format
```json
{
  "products": [
    {
      "id": "PROD-001",
      "name": "Wireless Mouse",
      "category": "Electronics",
      "description": "Ergonomic wireless mouse with USB receiver",
      "stock": 150,
      "unit": "piece",
      "pricing": {
        "base_price": 25.00,
        "minimum_price": 20.00,
        "currency": "USD"
      },
      "attributes": {
        "brand": "TechBrand",
        "warranty": "1 year",
        "color": "Black"
      }
    },
    {
      "id": "PROD-002",
      "name": "USB-C Cable",
      "category": "Accessories",
      "description": "2m USB-C to USB-C charging cable",
      "stock": 500,
      "unit": "piece",
      "pricing": {
        "base_price": 12.00,
        "minimum_price": 8.00,
        "currency": "USD"
      },
      "attributes": {
        "length": "2m",
        "warranty": "6 months"
      }
    }
  ]
}
```

### Adım 4: Pricing Strategy (Fiyatlandırma Stratejisi)

```json
{
  "strategy": "dynamic",
  "rules": {
    "bulk_discount": {
      "enabled": true,
      "tiers": [
        { "min_quantity": 10, "discount_percent": 5 },
        { "min_quantity": 50, "discount_percent": 10 },
        { "min_quantity": 100, "discount_percent": 15 }
      ]
    },
    "stock_based_pricing": {
      "enabled": true,
      "low_stock_threshold": 20,
      "low_stock_premium": 10,
      "high_stock_threshold": 200,
      "high_stock_discount": 5
    },
    "time_based_discount": {
      "enabled": false
    }
  },
  "negotiation_flexibility": {
    "max_discount_percent": 20,
    "min_profit_margin": 15,
    "aggressive_level": "moderate"
  }
}
```

**Strategy Tipleri:**
- **fixed**: Sabit fiyat, indirim yok
- **dynamic**: Stok ve talebe göre dinamik
- **aggressive**: Hızlı satış odaklı, düşük fiyat
- **premium**: Yüksek kar marjı, minimum indirim

### Adım 5: Business Rules (İş Kuralları)

```json
{
  "payment_terms": {
    "accepted_methods": ["blockchain_transfer", "google_pay", "apple_pay"],
    "payment_timing": "immediate",
    "escrow_required": true
  },
  "delivery": {
    "available_regions": ["North America", "Europe"],
    "shipping_cost": {
      "base": 5.00,
      "per_item": 1.00,
      "free_threshold": 100.00
    },
    "delivery_time": {
      "min_days": 2,
      "max_days": 7
    }
  },
  "return_policy": {
    "enabled": true,
    "days": 30,
    "conditions": "Unopened original packaging"
  }
}
```

### Adım 6: Agent Personality (Ajan Kişiliği)

```json
{
  "personality": {
    "tone": "professional",
    "response_style": "concise",
    "negotiation_approach": "collaborative",
    "traits": [
      "reliable",
      "fair",
      "customer_focused"
    ]
  },
  "communication": {
    "language": "en",
    "response_time": "immediate",
    "availability": "24/7"
  }
}
```

### Adım 7: Deploy!

**Deploy** butonuna tıklayın.

**Beklenen Süre:** 5-15 saniye

**Deploy Süreci:**
```
1. ⏳ Validating data...
2. 🔐 Registering on blockchain...
3. 🤖 Creating AI agent...
4. 🔧 Attaching tools...
5. ✅ Agent deployed successfully!
```

**Sonuç:**
```json
{
  "agent_id": "agent_merchant_abc123",
  "status": "active",
  "blockchain_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "domain": "techstore-electronics-bot.agent.com",
  "deployment_timestamp": "2025-11-22T10:30:45Z"
}
```

## 🛒 Client (Alıcı) Agent Deployment

### Adım 1: Deployment Formunu Aç

**Agent Type** seçiminde: **"Buyer"** seçeneğini işaretleyin.

### Adım 2: Temel Bilgileri Girin

#### Agent İsmi
```
Örnek: "RestaurantChain_Procurement_Bot"
```

### Adım 3: Alım İhtiyaçlarını Belirtin

```json
{
  "requirements": [
    {
      "id": "REQ-001",
      "product_type": "Fresh Tomatoes",
      "category": "Fresh Produce",
      "quantity": {
        "amount": 500,
        "unit": "kg",
        "frequency": "weekly"
      },
      "quality_requirements": {
        "grade": "A",
        "organic": true,
        "certifications": ["USDA Organic"]
      },
      "urgency": "medium"
    },
    {
      "id": "REQ-002",
      "product_type": "Olive Oil",
      "category": "Cooking Supplies",
      "quantity": {
        "amount": 50,
        "unit": "liters",
        "frequency": "monthly"
      },
      "quality_requirements": {
        "type": "Extra Virgin",
        "origin": "Mediterranean"
      },
      "urgency": "low"
    }
  ]
}
```

### Adım 4: Bütçe ve Fiyat Limitleri

```json
{
  "budget": {
    "total_monthly": 10000.00,
    "currency": "USD",
    "per_requirement": [
      {
        "requirement_id": "REQ-001",
        "max_unit_price": 2.50,
        "target_unit_price": 2.00,
        "total_budget": 4000.00
      },
      {
        "requirement_id": "REQ-002",
        "max_unit_price": 15.00,
        "target_unit_price": 12.00,
        "total_budget": 750.00
      }
    ]
  },
  "flexibility": {
    "can_exceed_budget": false,
    "max_overage_percent": 0,
    "priority": "price"
  }
}
```

**Budget Priority Options:**
- `price`: En düşük fiyat öncelikli
- `quality`: Kalite öncelikli, fiyat ikincil
- `speed`: Hızlı teslimat öncelikli
- `balanced`: Dengeli yaklaşım

### Adım 5: Purchasing Priorities (Alım Öncelikleri)

```json
{
  "priorities": {
    "primary": "price",
    "secondary": "quality",
    "tertiary": "delivery_speed"
  },
  "decision_weights": {
    "price": 50,
    "quality": 30,
    "delivery": 15,
    "seller_reputation": 5
  },
  "must_have_requirements": [
    "organic_certification",
    "same_day_delivery_available"
  ],
  "nice_to_have": [
    "bulk_discount",
    "flexible_payment_terms"
  ]
}
```

### Adım 6: Payment Preferences (Ödeme Tercihleri)

```json
{
  "payment": {
    "preferred_methods": [
      "blockchain_transfer",
      "corporate_card"
    ],
    "terms": {
      "preferred_timing": "net_30",
      "accept_escrow": true,
      "accept_immediate": true
    },
    "limits": {
      "max_single_transaction": 5000.00,
      "require_approval_above": 2000.00
    }
  }
}
```

### Adım 7: Negotiation Strategy (Müzakere Stratejisi)

```json
{
  "negotiation": {
    "approach": "balanced",
    "max_rounds": 8,
    "auto_accept_threshold": {
      "enabled": true,
      "condition": "price <= target_price * 1.05"
    },
    "auto_reject_threshold": {
      "enabled": true,
      "condition": "price > max_price"
    },
    "tactics": {
      "bulk_leverage": true,
      "competitor_mention": false,
      "long_term_relationship": true
    }
  }
}
```

**Negotiation Approaches:**
- `aggressive`: Çok düşük teklifle başla, yavaş yükselt
- `balanced`: Adil teklif, karşılıklı kazanç odaklı
- `passive`: Satıcının teklifini bekle, minimal müdahale
- `opportunistic`: Fırsat kolluyor, spot deals için ideal

### Adım 8: Agent Personality (Ajan Kişiliği)

```json
{
  "personality": {
    "tone": "business_professional",
    "style": "data_driven",
    "approach": "win_win",
    "traits": [
      "analytical",
      "fair",
      "relationship_focused",
      "quality_conscious"
    ]
  }
}
```

### Adım 9: Deploy!

**Deploy** butonuna tıklayın.

**Sonuç:**
```json
{
  "agent_id": "agent_buyer_xyz789",
  "status": "active",
  "blockchain_address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
  "domain": "restaurantchain-procurement-bot.agent.com",
  "deployment_timestamp": "2025-11-22T10:35:20Z",
  "discovery_status": "searching_for_matches"
}
```

## 📊 Deployment Sonrası

### Dashboard'a Erişim
```
http://localhost:3000/dashboard/agent_merchant_abc123
```

### Görülebilecek Bilgiler:
- ✅ Agent durumu (active/paused/stopped)
- 📈 Aktif müzakereler
- 💰 Tamamlanan işlemler
- 📊 İstatistikler ve performans
- ⚙️ Agent ayarları

### Agent Yönetimi

**Pause Agent:**
```bash
curl -X POST http://localhost:3001/agents/agent_merchant_abc123/pause
```

**Resume Agent:**
```bash
curl -X POST http://localhost:3001/agents/agent_merchant_abc123/resume
```

**Update Configuration:**
```bash
curl -X PATCH http://localhost:3001/agents/agent_merchant_abc123/config \
  -H "Content-Type: application/json" \
  -d '{"pricing": {"max_discount_percent": 25}}'
```

**Delete Agent:**
```bash
curl -X DELETE http://localhost:3001/agents/agent_merchant_abc123
```

## 🔧 Troubleshooting

### Deployment Başarısız Oldu
**Hata**: "Blockchain registration failed"
- **Çözüm**: Wallet'ınızda yeterli gas fee olduğundan emin olun

**Hata**: "Invalid product data"
- **Çözüm**: JSON formatını kontrol edin, required field'lar eksik olabilir

**Hata**: "Agent name already exists"
- **Çözüm**: Farklı bir agent ismi seçin

### Agent Müzakere Yapmıyor
- Stok bilgilerinizi kontrol edin
- Fiyat aralıklarının piyasa ile uyumlu olduğundan emin olun
- Agent'ın "active" durumda olduğunu verify edin

### Payment İşlemleri Başarısız
- Wallet bağlantısını kontrol edin
- Blockchain network durumunu kontrol edin
- Escrow kontratının onaylandığından emin olun

## 💡 Best Practices

### Merchant Agent İçin:
1. ✅ Gerçekçi ve güncel stok bilgileri girin
2. ✅ Piyasa araştırması yapın, rekabetçi fiyatlar belirleyin
3. ✅ Bulk discount'lar sunun, büyük siparişleri teşvik edin
4. ✅ Net ve detaylı ürün açıklamaları yazın
5. ✅ İade politikanızı açıkça belirtin

### Client Agent İçin:
1. ✅ Gerçekçi bütçeler belirleyin
2. ✅ Önceliklerinizi net tanımlayın (fiyat vs kalite)
3. ✅ Esnek müzakere stratejisi seçin
4. ✅ Uzun vadeli ilişki odaklı yaklaşım benimseyin
5. ✅ Ödeme koşullarınızı net belirtin

## 📚 İleri Seviye

### Multi-Product Bundle Agent
Birden fazla ürünü birlikte satan agent:
```json
{
  "bundle": {
    "id": "BUNDLE-001",
    "name": "Office Starter Pack",
    "products": ["PROD-001", "PROD-002", "PROD-005"],
    "bundle_discount": 20,
    "min_quantity": 10
  }
}
```

### Scheduled Deployment
Belirli saatlerde aktif olan agent:
```json
{
  "schedule": {
    "enabled": true,
    "timezone": "America/New_York",
    "active_hours": {
      "monday": ["09:00-17:00"],
      "friday": ["09:00-15:00"]
    }
  }
}
```

### Auto-Restock Integration
Stok düşünce otomatik sipariş veren client agent:
```json
{
  "auto_restock": {
    "enabled": true,
    "trigger": "stock < 20",
    "reorder_quantity": 100,
    "max_auto_budget": 5000.00
  }
}
```

---

**Daha fazla bilgi için:**
- [API Documentation](./API.md)
- [Architecture Guide](./ARCHITECTURE.md)
- [Examples](./EXAMPLES.md)

