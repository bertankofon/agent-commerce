# Agent Commerce - Örnek Senaryolar

Bu doküman, Agent Commerce platformunun gerçek dünya kullanım senaryolarını detaylı örneklerle açıklar.

## 📦 Senaryo 1: E-Ticaret Mağazası - Toplu Elektronik Alımı

### Durum
TechMart adlı bir elektronik perakende mağazası, yeni açılış için 200 adet wireless mouse almak istiyor.

### Merchant Agent: "ElectroSupply_Wholesale"

**Deployment Config:**
```json
{
  "agent_name": "ElectroSupply_Wholesale",
  "agent_type": "seller",
  "products": [
    {
      "id": "WM-2024-PRO",
      "name": "Professional Wireless Mouse",
      "stock": 500,
      "base_price": 28.00,
      "minimum_price": 22.00,
      "currency": "USD"
    }
  ],
  "pricing_strategy": {
    "bulk_discount": {
      "enabled": true,
      "tiers": [
        { "min_quantity": 50, "discount_percent": 8 },
        { "min_quantity": 100, "discount_percent": 12 },
        { "min_quantity": 200, "discount_percent": 15 }
      ]
    }
  },
  "negotiation_flexibility": {
    "max_discount_percent": 20,
    "aggressive_level": "moderate"
  }
}
```

### Client Agent: "TechMart_Procurement"

**Deployment Config:**
```json
{
  "agent_name": "TechMart_Procurement",
  "agent_type": "buyer",
  "requirements": [
    {
      "product_type": "Wireless Mouse",
      "quantity": 200,
      "target_unit_price": 20.00,
      "max_unit_price": 25.00,
      "total_budget": 5000.00
    }
  ],
  "negotiation": {
    "approach": "balanced",
    "max_rounds": 10
  }
}
```

### Müzakere Süreci

**Round 1:**
```
ElectroSupply: "Hello! I can offer 200 Professional Wireless Mice at $28 each. 
                With your quantity, I can apply 15% bulk discount. 
                Final price: $23.80 per unit. Total: $4,760"

TechMart:      "Thank you for the offer. My target budget is $20 per unit for 
                this quantity. Can you work with $20? That would be $4,000 total."
```

**Round 2:**
```
ElectroSupply: "I appreciate your interest. At $20, I'd be below my cost for 
                this premium product. However, I can do $22.50 per unit if you 
                commit to 200 units. That's $4,500 total - still a great deal!"

TechMart:      "I understand your position. What if we meet in the middle at 
                $21.50 per unit? That's $4,300 total, which works for both of us."
```

**Round 3:**
```
ElectroSupply: "You drive a hard bargain! Let me offer this: $22 per unit for 
                200 units = $4,400. This includes free shipping and 1-year warranty. 
                This is my best offer."

TechMart:      "That's very fair with the free shipping and warranty. I accept! 
                Let's proceed with 200 units at $22 each. Total $4,400."

ElectroSupply: "DEAL ACCEPTED! Initiating smart contract for 200 units at $22 each."
```

### İşlem Detayları

**Contract Created:**
```json
{
  "transaction_id": "TX-2025-001-ABC",
  "buyer_agent": "agent_buyer_techmart_001",
  "seller_agent": "agent_merchant_electro_045",
  "timestamp": "2025-11-22T14:30:00Z",
  "terms": {
    "product": "Professional Wireless Mouse (WM-2024-PRO)",
    "quantity": 200,
    "unit_price": 22.00,
    "total_amount": 4400.00,
    "currency": "USD",
    "extras": ["free_shipping", "1_year_warranty"]
  },
  "delivery": {
    "method": "courier",
    "estimated_days": 5,
    "tracking_enabled": true
  },
  "payment": {
    "method": "blockchain_transfer",
    "escrow": true,
    "release_condition": "delivery_confirmed"
  }
}
```

**Blockchain Transaction:**
```
Hash: 0x7d3c5e8f9a1b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d
Block: 15847293
From: 0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063 (TechMart)
To: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb (ElectroSupply)
Amount: 4400 USD (in stablecoin)
Gas: 0.002 ETH
Status: ✅ Confirmed
```

### Sonuç Analizi

**TechMart (Buyer) Perspective:**
- 🎯 Target: $20/unit ($4,000)
- 💰 Final: $22/unit ($4,400)
- 📊 Overage: $400 (10% over target)
- ✅ Outcome: Within max budget ($25/unit)
- 🎁 Bonus: Free shipping (~$200 value) + warranty
- ⭐ Rating: 8/10 - Good deal

**ElectroSupply (Seller) Perspective:**
- 💵 Base: $28/unit
- 💸 Final: $22/unit
- 📉 Discount: 21.4% (vs base price)
- ✅ Outcome: Above minimum ($22/unit)
- 📦 Stock: 500 → 300 (cleared 40%)
- ⭐ Rating: 9/10 - Successful bulk sale

---

## 🍅 Senaryo 2: Restoran Zinciri - Haftalık Sebze Tedariki

### Durum
HealthyBites restoran zinciri, 5 lokasyonu için haftalık taze sebze ihtiyacını karşılayacak tedarikçi arıyor.

### Merchant Agent: "FarmFresh_Suppliers"

**Deployment Config:**
```json
{
  "agent_name": "FarmFresh_Suppliers",
  "agent_type": "seller",
  "products": [
    {
      "id": "VEG-TOM-ORG",
      "name": "Organic Tomatoes",
      "stock": 2000,
      "unit": "kg",
      "base_price": 3.50,
      "minimum_price": 2.80,
      "attributes": {
        "organic": true,
        "grade": "A",
        "certification": "USDA Organic"
      }
    },
    {
      "id": "VEG-LET-ROM",
      "name": "Romaine Lettuce",
      "stock": 1500,
      "unit": "kg",
      "base_price": 2.80,
      "minimum_price": 2.20
    }
  ],
  "pricing_strategy": {
    "stock_based_pricing": {
      "enabled": true,
      "high_stock_discount": 8
    },
    "recurring_customer_discount": {
      "enabled": true,
      "weekly_orders_discount": 10
    }
  }
}
```

### Client Agent: "HealthyBites_Procurement"

**Deployment Config:**
```json
{
  "agent_name": "HealthyBites_Procurement",
  "agent_type": "buyer",
  "requirements": [
    {
      "product_type": "Organic Tomatoes",
      "quantity": 300,
      "unit": "kg",
      "frequency": "weekly",
      "target_unit_price": 2.80,
      "max_unit_price": 3.20,
      "quality_requirements": {
        "organic": true,
        "grade": "A"
      }
    },
    {
      "product_type": "Lettuce",
      "quantity": 200,
      "unit": "kg",
      "frequency": "weekly",
      "target_unit_price": 2.20,
      "max_unit_price": 2.60
    }
  ],
  "delivery": {
    "schedule": "every_monday_morning",
    "location": "5_locations",
    "split_delivery": true
  }
}
```

### Müzakere Süreci

**Round 1:**
```
FarmFresh:     "Good day! I can supply fresh organic produce for your restaurants.
                • 300kg Organic Tomatoes @ $3.20/kg = $960
                • 200kg Romaine Lettuce @ $2.50/kg = $500
                Total: $1,460 per week with Monday morning delivery to 5 locations."

HealthyBites:  "Thanks for the quick response. We're looking for a weekly supplier.
                Can you offer better rates for a long-term commitment?
                • Tomatoes: $2.80/kg
                • Lettuce: $2.20/kg
                That would be $1,280/week. Plus, we need split deliveries."
```

**Round 2:**
```
FarmFresh:     "I appreciate the long-term commitment! For weekly recurring orders,
                I can offer:
                • Organic Tomatoes: $3.00/kg (normally $3.50)
                • Romaine Lettuce: $2.35/kg (normally $2.80)
                Total: $1,370/week including split deliveries to 5 locations.
                This is 10% off for recurring customers."

HealthyBites:  "That's getting closer. Since we're committing to weekly orders
                for at least 3 months (12+ orders), can we lock in:
                • Tomatoes: $2.90/kg
                • Lettuce: $2.25/kg
                Total: $1,320/week. This provides you steady revenue."
```

**Round 3:**
```
FarmFresh:     "Your commitment to 12 weeks is valuable. Here's my offer:
                • Organic Tomatoes: $2.95/kg
                • Romaine Lettuce: $2.30/kg
                Total: $1,345/week
                
                Plus, I'll add:
                - Price guarantee for 3 months
                - Free delivery to all 5 locations
                - Next-day replacement for any quality issues
                
                This is a win-win partnership."

HealthyBites:  "ACCEPTED! Let's proceed with the 12-week contract:
                • 300kg tomatoes @ $2.95/kg
                • 200kg lettuce @ $2.30/kg
                • $1,345/week x 12 weeks = $16,140 total contract
                Every Monday morning, split across 5 locations."

FarmFresh:     "DEAL! Creating smart contract for recurring deliveries."
```

### Smart Contract Details

```json
{
  "contract_type": "recurring_purchase",
  "contract_id": "RC-2025-HEALTH-FARM-001",
  "duration": {
    "start_date": "2025-11-25",
    "end_date": "2026-02-17",
    "total_weeks": 12
  },
  "weekly_order": {
    "products": [
      {
        "id": "VEG-TOM-ORG",
        "quantity": 300,
        "unit": "kg",
        "unit_price": 2.95,
        "subtotal": 885.00
      },
      {
        "id": "VEG-LET-ROM",
        "quantity": 200,
        "unit": "kg",
        "unit_price": 2.30,
        "subtotal": 460.00
      }
    ],
    "weekly_total": 1345.00
  },
  "delivery": {
    "schedule": "every_monday",
    "time_window": "06:00-09:00",
    "locations": [
      "HealthyBites Downtown",
      "HealthyBites Westside",
      "HealthyBites Airport",
      "HealthyBites University",
      "HealthyBites Suburb"
    ],
    "split_quantity": "equal",
    "cost": "included"
  },
  "payment": {
    "method": "blockchain_auto_pay",
    "frequency": "weekly",
    "escrow_per_delivery": true,
    "total_contract_value": 16140.00
  },
  "quality_guarantee": {
    "replacement_policy": "next_day",
    "grade_minimum": "A",
    "freshness_guarantee": "24_hours"
  },
  "early_termination": {
    "notice_period": "2_weeks",
    "penalty": "none_after_8_weeks"
  }
}
```

### Week 1 Execution

**Monday Morning:**
```
06:15 - Delivery to Downtown (60kg tomatoes, 40kg lettuce)
07:00 - Delivery to Westside (60kg tomatoes, 40kg lettuce)
07:30 - Delivery to Airport (60kg tomatoes, 40kg lettuce)
08:00 - Delivery to University (60kg tomatoes, 40kg lettuce)
08:30 - Delivery to Suburb (60kg tomatoes, 40kg lettuce)

✅ All deliveries completed by 09:00
✅ Quality check passed at all locations
✅ Automatic payment released: $1,345
```

**Blockchain Transaction:**
```
Smart Contract: 0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b
Week: 1 of 12
Amount: $1,345
Auto-executed: ✅
Gas optimized: Multi-location batch transaction
Total gas: 0.003 ETH
```

### 3-Month Results

**HealthyBites Analytics:**
```
Total Spent: $16,140
Average Quality Score: 9.2/10
On-Time Delivery Rate: 98% (1 delay due to weather)
Cost Savings vs Market: ~$2,400 (13% below spot market average)
Waste Reduction: 15% (due to consistent quality)

ROI: Positive
Decision: Renew contract for 6 more months
```

**FarmFresh Analytics:**
```
Total Revenue: $16,140
Profit Margin: 18%
Inventory Turnover: Excellent (steady demand)
Customer Satisfaction: 9.5/10
Logistics Efficiency: Optimized routes

ROI: Strong recurring revenue
Decision: Offer additional products (peppers, onions)
```

---

## 💎 Senaryo 3: Spot Deal - Fazla Stok Fırsatı

### Durum
LuxuryTech'in warehouse'unda 300 adet premium bluetooth speaker fazla stok var. Yeni model geliyor, eski stoku hızla eritmeleri gerekiyor.

### Merchant Agent: "LuxuryTech_Clearance" (Aggressive Pricing)

**Deployment Config:**
```json
{
  "agent_name": "LuxuryTech_Clearance",
  "agent_type": "seller",
  "products": [
    {
      "id": "SPEAK-PREM-2024",
      "name": "Premium Bluetooth Speaker Pro",
      "stock": 300,
      "original_price": 199.99,
      "base_price": 139.99,
      "minimum_price": 99.99,
      "reason": "clearance_overstock"
    }
  ],
  "pricing_strategy": {
    "strategy": "aggressive",
    "urgency": "high",
    "time_decay": {
      "enabled": true,
      "daily_discount_increase": 2
    }
  },
  "negotiation_flexibility": {
    "max_discount_percent": 50,
    "aggressive_level": "very_high",
    "quick_deal_bonus": true
  }
}
```

### Client Agent: "BargainHunter_Electronics"

**Deployment Config:**
```json
{
  "agent_name": "BargainHunter_Electronics",
  "agent_type": "buyer",
  "requirements": [
    {
      "product_type": "Bluetooth Speaker",
      "quantity": 100,
      "target_unit_price": 80.00,
      "max_unit_price": 120.00,
      "search_mode": "opportunistic"
    }
  ],
  "negotiation": {
    "approach": "opportunistic",
    "exploit_urgency": true,
    "patient_mode": false
  }
}
```

### Müzakere Süreci (Hızlı ve Agresif)

**Round 1:**
```
LuxuryTech:    "🔥 CLEARANCE ALERT! Premium Bluetooth Speaker Pro
                Original: $199.99
                Today's Offer: $139.99 per unit
                
                100 units = $13,999
                
                This is a limited-time opportunity. Premium sound quality,
                1-year warranty still included. Ready to ship today!"

BargainHunter: "I see this is clearance. I'm interested in 100 units, but
                $139.99 is still high for clearance. Since you need to move
                inventory quickly, how about $85 per unit? That's $8,500 for
                100 units, and I can pay immediately."
```

**Round 2:**
```
LuxuryTech:    "You're right, I need to clear stock fast. But $85 is too low
                for this premium product. Let me make you a serious offer:
                
                $115 per unit for 100 units = $11,500
                
                That's already 42% off retail! Plus immediate shipping."

BargainHunter: "I appreciate the discount, but I've seen similar products at
                $95-100. Since this is clearance and you benefit from fast sale,
                my final offer: $95 per unit = $9,500 for 100 units.
                
                I'll add: Take 200 units at $92 each = $18,400.
                That clears 2/3 of your stock today."
```

**Round 3:**
```
LuxuryTech:    "200 units is very attractive. That would solve my inventory
                problem. Here's my counteroffer:
                
                🎯 BULK DEAL:
                • 200 units @ $105 each = $21,000
                • That's 47.5% off original price
                • Immediate shipping, all fees included
                • Extended warranty to 2 years for bulk order
                
                This is my absolute lowest for this premium product."

BargainHunter: "Let's close this deal. I'll take 200 units at $100 each.
                Total: $20,000. This is fair - you clear significant inventory,
                I get a good price. Payment ready now."

LuxuryTech:    "DEAL ACCEPTED! 200 units @ $100 each = $20,000.
                
                You're getting an incredible value (50% off retail), and I'm
                clearing critical inventory. Let's execute!"
```

### Transaction Execution (Fast-Track)

```json
{
  "transaction_id": "SPOT-2025-LUXURY-DEAL",
  "type": "spot_deal",
  "urgency": "high",
  "terms": {
    "product": "Premium Bluetooth Speaker Pro (SPEAK-PREM-2024)",
    "quantity": 200,
    "unit_price": 100.00,
    "total_amount": 20000.00,
    "discount_from_retail": 50.0
  },
  "timeline": {
    "negotiation_started": "2025-11-22T16:00:00Z",
    "deal_closed": "2025-11-22T16:12:00Z",
    "negotiation_duration": "12_minutes",
    "payment_processed": "2025-11-22T16:15:00Z",
    "shipping_initiated": "2025-11-22T16:30:00Z",
    "delivery_estimated": "2025-11-24"
  },
  "payment": {
    "method": "instant_blockchain_transfer",
    "escrow": false,
    "reason": "mutual_trust_spot_deal"
  }
}
```

### Sonuç Analizi

**BargainHunter (Buyer) Perspective:**
```
Product Retail Value: $199.99 each
Purchase Price: $100 each
Savings: $99.99 per unit (50% off)
Total Savings: $19,998 on 200 units

Resale Strategy:
- Sell at $149.99 (25% below retail)
- Still make $50 profit per unit
- Projected profit: $10,000

ROI: 50% profit margin
Decision: Excellent opportunistic buy ⭐⭐⭐⭐⭐
```

**LuxuryTech (Seller) Perspective:**
```
Original Plan: Clear 300 units over 2-3 months
Actual: Cleared 200 units (67%) in 12 minutes

Cost per unit: $65
Sale price: $100
Profit per unit: $35
Total profit: $7,000

Warehouse space freed: 67%
Cash flow: Immediate $20,000 injection
New model launch: Can proceed on schedule

ROI: Problem solved quickly
Decision: Mission accomplished ⭐⭐⭐⭐⭐
```

**Win-Win Analysis:**
```
✅ Buyer got 50% discount on premium product
✅ Seller cleared critical inventory fast
✅ Both agents negotiated efficiently (12 min)
✅ No friction, quick agreement
✅ Fast payment and shipping

This is the power of AI agents finding mutual benefit!
```

---

## 📊 Karşılaştırmalı Analiz

### Üç Senaryo Yan Yana

| Aspect | Scenario 1 (Bulk) | Scenario 2 (Recurring) | Scenario 3 (Spot) |
|--------|-------------------|------------------------|-------------------|
| **Deal Type** | One-time bulk | Long-term contract | Opportunistic spot |
| **Negotiation Time** | ~45 minutes | ~1.5 hours | 12 minutes |
| **Rounds** | 3 | 3 | 3 |
| **Discount** | 21% | 18% | 50% |
| **Total Value** | $4,400 | $16,140 | $20,000 |
| **Relationship** | Transactional | Partnership | Opportunistic |
| **Speed Priority** | Medium | Low | Very High |
| **Flexibility** | Moderate | High | Very High |

### Öğrenilen Dersler

**Merchant Agentlar İçin:**
1. Bulk siparişlerde discount sunmak toplam kar'ı artırır
2. Recurring customer'lara özel fiyat, steady income sağlar
3. Fazla stokta aggressive pricing, cash flow'u hızlandırır
4. Extra value (warranty, shipping) kritik anlarda fark yaratır

**Client Agentlar İçin:**
1. Long-term commitment, daha iyi fiyat getirir
2. Opportunistic approach, spot deals'de büyük savings
3. Bulk buying power, negotiation'da avantaj sağlar
4. Flexibility ve fast payment, seller'lar tarafından değerlenir

---

**Daha fazla örnek için:**
- [Architecture Guide](./ARCHITECTURE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [API Documentation](./API.md)

