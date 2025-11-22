# Agent Commerce - Sistem Mimarisi

## 🎯 Proje Özeti

Agent Commerce, yapay zeka destekli otonom ticaret agentlarının birbirleriyle müzakere edip, anlaşma sağlayıp, blockchain üzerinden güvenli ödeme yapabildiği devrim niteliğinde bir platformdur.

## 🔄 Sistemin Tam İş Akışı

### 1. Agent Deployment (Ajan Kurulumu)

#### Merchant (Satıcı) Agent Kurulumu
Kullanıcı bir merchant agent deploy etmek istediğinde:

**Gerekli Bilgiler:**
- **Agent İsmi**: Ajanın benzersiz adı
- **Ürün Bilgileri**: Satılacak ürün/ürünlerin listesi
- **Stok Durumu**: Her ürün için mevcut stok miktarı
- **Fiyatlandırma**: 
  - Minimum kabul edilebilir fiyat
  - Başlangıç teklif fiyatı
  - Maksimum indirim oranı
- **İş Kuralları**:
  - Toplu alımlarda indirim politikası
  - Ödeme şartları
  - Teslimat koşulları

**Deployment Süreci:**
```
User Input → Frontend Form → Backend API → Python Agent Manager
    ↓
ChaosChain SDK (Blockchain Kayıt)
    ↓
Eliza AI (Personality & Strategy)
    ↓
Agent Tools (Inventory, Pricing, Payment)
    ↓
Active Agent (Hazır & Dinlemede)
```

#### Client (Alıcı) Agent Kurulumu
Kullanıcı bir client agent deploy etmek istediğinde:

**Gerekli Bilgiler:**
- **Agent İsmi**: Ajanın benzersiz adı
- **Alım İhtiyacı**:
  - İhtiyaç duyulan ürün/ürünler
  - Miktar gereksinimleri
  - Kalite beklentileri
- **Bütçe Bilgileri**:
  - Maksimum ödeyebileceği fiyat
  - Hedef fiyat
  - Toplam bütçe limiti
- **Öncelikler**:
  - Fiyat öncelikli mi, kalite mi?
  - Hızlı teslimat önemli mi?
  - Tercih edilen ödeme yöntemleri

### 2. Agent Discovery (Ajan Keşfi)

Agentlar deploy edildikten sonra, birbirlerini bulmak için:

**Discovery Mekanizması:**
```
Client Agent                    Discovery Service                    Merchant Agent
     |                                 |                                    |
     |--- Search Request ------------->|                                    |
     |    (product, quantity, budget)  |                                    |
     |                                 |<--- Register Availability ---------|
     |                                 |    (products, stock, price range)  |
     |                                 |                                    |
     |<-- Matched Merchants -----------|                                    |
     |    (list of compatible sellers) |                                    |
```

**Eşleştirme Kriterleri:**
- Ürün uygunluğu (client'ın aradığı ürünü merchant'ın satması)
- Stok durumu (yeterli stok olması)
- Fiyat aralığı uyumu (bütçe ile fiyat aralığının kesişmesi)
- Ödeme yöntemi uyumluluğu
- Coğrafi konum (opsiyonel, teslimat için)

### 3. Negotiation (Müzakere Süreci)

İki uyumlu agent bulunduğunda, otonom müzakere başlar:

#### Müzakere Akışı

```
┌─────────────────────────────────────────────────────────────┐
│                    NEGOTIATION CYCLE                        │
└─────────────────────────────────────────────────────────────┘

Round 1:
  Merchant: "I offer 100 units at $50 each. Total: $5000"
          ↓
  Client:   "I need 100 units but my budget is $45 each. Can you do $4500?"
          ↓
  
Round 2:
  Merchant: "I can offer $48 each if you buy 100+ units. Total: $4800"
          ↓
  Client:   "How about $46 each? That's $4600 total - fair middle ground"
          ↓

Round 3:
  Merchant: "Deal! $47 each, 100 units. Total: $4700. Payment via blockchain"
          ↓
  Client:   "ACCEPTED. Initiating payment protocol."
          ↓
  
  ✅ AGREEMENT REACHED
```

#### Müzakere Stratejileri

**Merchant Agent Stratejisi:**
- Kar marjını maksimize etmeye çalışır
- Ancak makul ve rekabetçi kalır
- Toplu alımlarda indirim teklif edebilir
- Stok seviyesine göre agresiflik ayarlar (yüksek stok = daha esnek)

**Client Agent Stratejisi:**
- En iyi fiyatı almaya çalışır
- Bütçe limitini aşmaz
- Alternatif teklifler değerlendirir
- Kalite-fiyat dengesini optimize eder

#### Müzakere Kuralları

**Otomatik Kabul Koşulları:**
- Merchant için: Minimum fiyatın üzerinde teklif
- Client için: Maksimum bütçenin altında teklif
- Her iki taraf da "win-win" aralığında

**Otomatik Red Koşulları:**
- Bütçe/fiyat çok uzak
- Stok yetersiz
- Ödeme yöntemi uyumsuz
- 10 round sonra anlaşma sağlanamaması

**Deadlock Çözümü:**
- Küçük tavizlerle orta nokta arama
- Ek değer önerileri (hızlı teslimat, garanti, vs.)
- Eğer çözüm yoksa: "No deal" ve başka agentlara yönelme

### 4. Transaction Execution (İşlem Gerçekleştirme)

Anlaşma sağlandığında, otomatik işlem başlar:

#### Adım 1: Contract Preparation
```javascript
{
  "transaction_id": "tx_abc123",
  "buyer_agent_id": "agent_buyer_001",
  "seller_agent_id": "agent_merchant_045",
  "agreed_terms": {
    "product": "Widget Pro",
    "quantity": 100,
    "unit_price": 47,
    "total_amount": 4700,
    "currency": "USD",
    "payment_method": "blockchain_transfer"
  },
  "delivery_terms": {
    "address": "encrypted_address",
    "expected_date": "2025-11-30"
  },
  "status": "pending_payment"
}
```

#### Adım 2: Payment Processing
```
Client Agent                    ChaosChain SDK                    Merchant Agent
     |                                |                                  |
     |--- Initiate Payment ---------->|                                  |
     |    (amount: 4700)               |                                  |
     |                                 |                                  |
     |<-- Payment Request -------------|                                  |
     |    (wallet address, amount)     |                                  |
     |                                 |                                  |
     |--- Confirm & Sign ------------->|                                  |
     |    (digital signature)          |                                  |
     |                                 |                                  |
     |                                 |--- Transfer Funds -------------->|
     |                                 |    (blockchain transaction)      |
     |                                 |                                  |
     |<-- Transaction Hash ------------|                                  |
     |    (0xabc...def)                |                                  |
     |                                 |                                  |
     |                                 |<-- Confirm Receipt --------------|
     |                                 |                                  |
     ✅ Payment Complete              ✅ Funds Received                 ✅
```

#### Adım 3: Inventory Update
```python
# Merchant side
def complete_transaction(transaction):
    # Update inventory
    inventory.reduce_stock(
        product_id=transaction.product,
        quantity=transaction.quantity
    )
    
    # Record sale
    sales_history.add({
        "date": now(),
        "product": transaction.product,
        "quantity": transaction.quantity,
        "revenue": transaction.total_amount,
        "buyer": transaction.buyer_agent_id
    })
    
    # Update agent strategy
    pricing_strategy.update_based_on_sale()
```

#### Adım 4: Confirmation & Rating
```
Both Agents:
  ✅ Transaction Complete
  📝 Rate the experience (optional)
  💾 Store transaction in history
  🔄 Return to discovery mode for new deals
```

## 🏗️ Teknik Mimari

### Frontend Layer
```
┌─────────────────────────────────────────────┐
│           Next.js Frontend (Port 3000)      │
│                                             │
│  ┌─────────────┐      ┌─────────────────┐ │
│  │   Deploy    │      │   Dashboard     │ │
│  │   Agent     │      │   Monitor       │ │
│  │   Form      │      │   Negotiations  │ │
│  └─────────────┘      └─────────────────┘ │
└─────────────────────────────────────────────┘
                    │
                    │ REST API
                    ↓
```

### Backend Layer
```
┌─────────────────────────────────────────────┐
│       Express.js Backend (Port 3001)        │
│                                             │
│  POST /deploy-agent                         │
│  GET  /agents                               │
│  POST /start-negotiation                    │
│  GET  /transactions                         │
│  WebSocket /negotiations/live               │
└─────────────────────────────────────────────┘
                    │
                    │ Spawn Process
                    ↓
```

### Agent Layer
```
┌─────────────────────────────────────────────┐
│           Python Agent System               │
│                                             │
│  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Eliza AI       │  │  ChaosChain SDK │ │
│  │  (Decision)     │  │  (Blockchain)   │ │
│  └─────────────────┘  └─────────────────┘ │
│                                             │
│  ┌─────────────────────────────────────┐  │
│  │         Agent Tools                 │  │
│  │  • check_inventory()                │  │
│  │  • calculate_pricing()              │  │
│  │  • process_payment()                │  │
│  │  • verify_transaction()             │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    │
                    │ Blockchain Protocol
                    ↓
┌─────────────────────────────────────────────┐
│      BASE Sepolia Testnet (Blockchain)      │
│                                             │
│  • Agent Identity Registry                  │
│  • Payment Transactions                     │
│  • Smart Contracts                          │
│  • Transaction History                      │
└─────────────────────────────────────────────┘
```

## 📊 Data Flow

### Agent Deployment Flow
```
User → Form Data → Backend → Python Script → {
    ChaosChain: Register on blockchain
    Eliza: Create AI personality
    Tools: Attach capabilities
} → Agent ID → User
```

### Negotiation Flow
```
Discovery: Find Compatible Agents
    ↓
Initialize: Create negotiation room
    ↓
Loop: {
    Merchant → Offer
    Client → Counter-offer
    Evaluate: Agreement reached?
} Until: Agreement || Timeout
    ↓
Transaction: Execute payment & delivery
    ↓
Complete: Update records & ratings
```

## 🔐 Güvenlik ve Güven

### Blockchain Garantileri
- **Immutable Records**: Tüm işlemler blockchain'de kayıtlı
- **Smart Contracts**: Ödeme şartları otomatik execute
- **Escrow**: Fon önce emanet, teslimat sonrası serbest
- **Dispute Resolution**: Anlaşmazlık durumunda otomatik arbitraj

### Agent Integrity
- **Process Integrity**: ChaosChain'in process integrity özelliği
- **AP2 Protocol**: Agent-to-agent güvenli iletişim
- **Rate Limiting**: Spam ve abuse önleme
- **Reputation System**: Agent'ların geçmiş performans skorları

## 🚀 Gelecek Özellikler

### Phase 2
- [ ] Multi-product negotiations (birden fazla ürün)
- [ ] Bulk discount strategies (toplu indirim stratejileri)
- [ ] Quality tiers (kalite seviyeleri)
- [ ] Delivery options (teslimat seçenekleri)

### Phase 3
- [ ] Agent marketplace (agent pazarı)
- [ ] Agent templates (hazır agent şablonları)
- [ ] Advanced analytics (detaylı analizler)
- [ ] Multi-chain support (farklı blockchain'ler)

### Phase 4
- [ ] AI learning from past negotiations (geçmişten öğrenme)
- [ ] Predictive pricing (tahmine dayalı fiyatlandırma)
- [ ] Market trend analysis (pazar trend analizi)
- [ ] Autonomous inventory management (otonom stok yönetimi)

## 💡 Kullanım Senaryoları

### Senaryo 1: Toplu Alım
- **Durum**: Restaurant zinciri günlük sebze ihtiyacı
- **Client Agent**: 500kg domates, maksimum $2/kg
- **Merchant Agent**: 1000kg stok, $2.50/kg liste fiyatı
- **Müzakere**: Toplu alım indirimi ile $2.20/kg'da anlaşma
- **Sonuç**: Her iki taraf da kazançlı

### Senaryo 2: Spot Market
- **Durum**: Merchant'ın hızla satması gereken fazla stok
- **Merchant Agent**: Agresif pricing, hızlı satış öncelikli
- **Client Agent**: Fırsat kolluyor, düşük fiyat hedefli
- **Müzakere**: Normal fiyatın %30 altında anlaşma
- **Sonuç**: Merchant stoğu eritti, Client kazançlı alım yaptı

### Senaryo 3: Premium Ürün
- **Durum**: Yüksek kaliteli ürün, sınırlı stok
- **Merchant Agent**: Yüksek fiyat, minimum indirim
- **Client Agent**: Kalite öncelikli, bütçe esnek
- **Müzakere**: Premium fiyattan hızlı anlaşma
- **Sonuç**: Kalite beklentisi karşılandı

## 🎓 Öğrenme ve Adaptasyon

Agentlar her işlemden öğrenir:

**Merchant Agent Öğrenmesi:**
- Hangi fiyat aralıklarında satış gerçekleşiyor?
- Hangi indirim oranları kabul görüyor?
- Hangi müzakere taktikleri başarılı?
- Pazar trendleri nasıl değişiyor?

**Client Agent Öğrenmesi:**
- Hangi merchant'lar güvenilir?
- Ortalama pazar fiyatları nedir?
- Hangi zamanlarda daha iyi fiyat alınıyor?
- Hangi müzakere yaklaşımları etkili?

Bu öğrenme sistemi, zamanla agentları daha akıllı ve etkili hale getirir.

