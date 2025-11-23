# Agent0 Service API Documentation

This document provides comprehensive API documentation for integrating with the Agent0 Service from other microservices or backend APIs.

## Base URL

```
http://localhost:8000  # Development
https://your-domain.com  # Production
```

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## Content Type

All requests must include the header:
```
Content-Type: application/json
```

---

## Endpoints

### 1. Health Check

#### `GET /health`

Check if the service is running and healthy.

**Request:**
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

---

### 2. Create and Register Agent

#### `POST /agents/create-and-register`

Create a new agent and optionally register it on-chain.

**Request:**
```http
POST /agents/create-and-register
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **YES** | Agent name (min length: 1) |
| `description` | string | **YES** | Agent description (min length: 1) |
| `image` | string | No | Agent image: local file path, Supabase S3 URL, HTTP URL, or IPFS URL |
| `skills` | string[] | No | List of OASF skills (e.g., `["data_engineering/data_transformation_pipeline"]`) |
| `domains` | string[] | No | List of OASF domains (e.g., `["technology/data_science"]`) |
| `active` | boolean | No | Set agent as active (visible in searches). Default: `true` |
| `x402support` | boolean | No | Enable x402 payment support. Default: `false` |
| `mcpEndpoint` | string | No | MCP (Model Context Protocol) endpoint URL |
| `a2aEndpoint` | string | No | A2A (Agent-to-Agent) endpoint URL |
| `ensName` | string | No | ENS name (e.g., `"myagent.eth"`) |
| `walletAddress` | string | No | Agent wallet address (Ethereum address) |
| `walletChainId` | integer | No | Chain ID for agent wallet (e.g., `11155111` for Sepolia) |
| `trustModels` | object | No | Trust models configuration (see below) |
| `metadata` | object | No | Custom metadata key-value pairs |
| `validateOasf` | boolean | No | Validate skills/domains against OASF taxonomy. Default: `false` |
| `register` | boolean | No | Register agent on-chain after creation. Default: `true` |

**Trust Models Object:**
```json
{
  "reputation": true,
  "cryptoEconomic": true,
  "teeAttestation": false
}
```

**Minimal Request Example:**
```json
{
  "name": "My AI Agent",
  "description": "An intelligent assistant that helps with various tasks"
}
```

**Full Request Example:**
```json
{
  "name": "My AI Agent",
  "description": "An intelligent assistant that helps with various tasks",
  "image": "https://supabase.co/storage/v1/object/public/bucket/image.png",
  "skills": [
    "data_engineering/data_transformation_pipeline",
    "advanced_reasoning_planning/strategic_planning"
  ],
  "domains": [
    "technology/data_science"
  ],
  "active": true,
  "x402support": false,
  "mcpEndpoint": "https://mcp.example.com/",
  "a2aEndpoint": "https://a2a.example.com/agent.json",
  "ensName": "myagent.eth",
  "walletAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "walletChainId": 11155111,
  "trustModels": {
    "reputation": true,
    "cryptoEconomic": true,
    "teeAttestation": false
  },
  "metadata": {
    "version": "1.0.0",
    "category": "developer-tools",
    "pricing": "free"
  },
  "validateOasf": false,
  "register": true
}
```

**Response (201 Created):**

All agent fields are returned in the response. Fields that are not set will be `null` or empty arrays/objects.

```json
{
  "agentId": "11155111:123",
  "agentURI": "ipfs://QmExampleHash",
  "name": "My AI Agent",
  "description": "An intelligent assistant that helps with various tasks",
  "image": "https://gateway.pinata.cloud/ipfs/QmImageHash",
  "active": true,
  "x402support": false,
  "walletAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "walletChainId": 11155111,
  "mcpEndpoint": "https://mcp.example.com/",
  "a2aEndpoint": "https://a2a.example.com/agent.json",
  "ensEndpoint": "myagent.eth",
  "endpoints": [
    {
      "type": "mcp",
      "value": "https://mcp.example.com/"
    }
  ],
  "trustModels": ["reputation", "crypto-economic"],
  "metadata": {
    "version": "1.0.0",
    "category": "developer-tools",
    "pricing": "free"
  },
  "skills": [
    "data_engineering/data_transformation_pipeline",
    "advanced_reasoning_planning/strategic_planning"
  ],
  "domains": [
    "technology/data_science"
  ],
  "mcpTools": ["tool1", "tool2"],
  "mcpPrompts": ["prompt1"],
  "mcpResources": ["resource1"],
  "a2aSkills": ["skill1"],
  "owners": ["0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"],
  "operators": [],
  "updatedAt": 1234567890
}
```

**Error Responses:**

- **400 Bad Request:** Invalid request body or validation error
  ```json
  {
    "detail": "Validation error message"
  }
  ```

- **404 Not Found:** Image file not found (if using local file path)
  ```json
  {
    "detail": "File not found: /path/to/image.png"
  }
  ```

- **500 Internal Server Error:** Server error during agent creation
  ```json
  {
    "detail": "Failed to create and register agent: error message"
  }
  ```

---

### 3. Get Agent

#### `GET /agents/{agent_id}`

Retrieve agent details by ID.

**Request:**
```http
GET /agents/{agent_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | string | **YES** | Agent ID in format `chainId:tokenId` or `tokenId` |

**Example:**
```http
GET /agents/11155111:123
GET /agents/123
```

**Response (200 OK):**

All agent fields are returned in the response. Fields that are not set will be `null` or empty arrays/objects.

```json
{
  "agentId": "11155111:123",
  "agentURI": "ipfs://QmExampleHash",
  "name": "My AI Agent",
  "description": "An intelligent assistant that helps with various tasks",
  "image": "https://gateway.pinata.cloud/ipfs/QmImageHash",
  "active": true,
  "x402support": false,
  "walletAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "walletChainId": 11155111,
  "mcpEndpoint": "https://mcp.example.com/",
  "a2aEndpoint": "https://a2a.example.com/agent.json",
  "ensEndpoint": "myagent.eth",
  "endpoints": [
    {
      "type": "mcp",
      "value": "https://mcp.example.com/"
    }
  ],
  "trustModels": ["reputation"],
  "metadata": {
    "version": "1.0.0"
  },
  "skills": ["data_engineering/data_transformation_pipeline"],
  "domains": ["technology/data_science"],
  "mcpTools": ["tool1"],
  "mcpPrompts": [],
  "mcpResources": [],
  "a2aSkills": [],
  "owners": ["0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"],
  "operators": [],
  "updatedAt": 1234567890
}
```

**Error Responses:**

- **400 Bad Request:** Invalid agent ID format
  ```json
  {
    "detail": "Invalid agent ID format"
  }
  ```

- **500 Internal Server Error:** Failed to retrieve agent
  ```json
  {
    "detail": "Failed to get agent: error message"
  }
  ```

---

### 4. Update Agent

#### `PUT /agents/{agent_id}`

Update an existing agent. All fields in the request body are optional - only provided fields will be updated.

**Request:**
```http
PUT /agents/{agent_id}
Content-Type: application/json
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | string | **YES** | Agent ID in format `chainId:tokenId` or `tokenId` |

**Request Body:**

All fields are **optional**. Only include fields you want to update.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Agent name |
| `description` | string | No | Agent description |
| `image` | string | No | Agent image: local file path, Supabase S3 URL, HTTP URL, or IPFS URL |
| `skills` | string[] | No | List of OASF skills to add |
| `domains` | string[] | No | List of OASF domains to add |
| `active` | boolean | No | Set agent as active (visible in searches) |
| `x402support` | boolean | No | Enable x402 payment support |
| `mcpEndpoint` | string | No | MCP endpoint URL |
| `a2aEndpoint` | string | No | A2A endpoint URL |
| `ensName` | string | No | ENS name (e.g., `"myagent.eth"`) |
| `walletAddress` | string | No | Agent wallet address |
| `walletChainId` | integer | No | Chain ID for agent wallet |
| `trustModels` | object | No | Trust models configuration |
| `metadata` | object | No | Custom metadata key-value pairs |
| `validateOasf` | boolean | No | Validate skills/domains against OASF taxonomy. Default: `false` |
| `removeEndpoints` | string[] | No | List of endpoint types to remove: `["mcp", "a2a", "ens"]` |

**Minimal Request Example (update only name):**
```json
{
  "name": "Updated Agent Name"
}
```

**Full Request Example:**
```json
{
  "name": "Updated Agent Name",
  "description": "Updated description",
  "image": "/path/to/local/image.png",
  "skills": ["new_skill/category"],
  "domains": ["new_domain/category"],
  "active": false,
  "x402support": true,
  "mcpEndpoint": "https://new-mcp.example.com/",
  "a2aEndpoint": "https://new-a2a.example.com/agent.json",
  "ensName": "newagent.eth",
  "walletAddress": "0xNewWalletAddress",
  "walletChainId": 11155111,
  "trustModels": {
    "reputation": true,
    "cryptoEconomic": false,
    "teeAttestation": true
  },
  "metadata": {
    "version": "2.0.0",
    "updated": true
  },
  "validateOasf": true,
  "removeEndpoints": ["mcp", "a2a"]
}
```

**Response (200 OK):**
```json
{
  "agentId": "11155111:123",
  "agentURI": "ipfs://QmExampleHash",
  "name": "Updated Agent Name",
  "description": "Updated description",
  "image": "https://gateway.pinata.cloud/ipfs/QmNewImageHash",
  "active": false,
  "x402support": true,
  "walletAddress": "0xNewWalletAddress",
  "walletChainId": 11155111,
  "mcpEndpoint": null,
  "a2aEndpoint": null,
  "ensEndpoint": "newagent.eth",
  "endpoints": [],
  "trustModels": [],
  "metadata": {
    "version": "2.0.0",
    "updated": true
  },
  "skills": ["new_skill/category"],
  "domains": ["new_domain/category"],
  "mcpTools": [],
  "mcpPrompts": [],
  "mcpResources": [],
  "a2aSkills": [],
  "owners": [],
  "operators": [],
  "updatedAt": null
}
```

**Error Responses:**

- **400 Bad Request:** Invalid request body or validation error
  ```json
  {
    "detail": "Validation error message"
  }
  ```

- **404 Not Found:** Agent not found or image file not found
  ```json
  {
    "detail": "Agent not found" or "File not found: /path/to/image.png"
  }
  ```

- **500 Internal Server Error:** Failed to update agent
  ```json
  {
    "detail": "Failed to update agent: error message"
  }
  ```

---

### 5. Deactivate Agent

#### `DELETE /agents/{agent_id}`

Deactivate an agent by setting `active=false`. This makes the agent hidden from searches.

**Request:**
```http
DELETE /agents/{agent_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | string | **YES** | Agent ID in format `chainId:tokenId` or `tokenId` |

**Example:**
```http
DELETE /agents/11155111:123
```

**Response (200 OK):**
```json
{
  "agentId": "11155111:123",
  "agentURI": "ipfs://QmExampleHash",
  "name": "My AI Agent",
  "description": "An intelligent assistant that helps with various tasks",
  "image": "https://gateway.pinata.cloud/ipfs/QmImageHash",
  "active": false,
  "x402support": false,
  "walletAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "walletChainId": 11155111,
  "mcpEndpoint": "https://mcp.example.com/",
  "a2aEndpoint": "https://a2a.example.com/agent.json",
  "ensEndpoint": "myagent.eth",
  "endpoints": [],
  "trustModels": [],
  "metadata": {},
  "skills": [],
  "domains": [],
  "mcpTools": [],
  "mcpPrompts": [],
  "mcpResources": [],
  "a2aSkills": [],
  "owners": [],
  "operators": [],
  "updatedAt": null
}
```

**Error Responses:**

- **400 Bad Request:** Invalid agent ID format
  ```json
  {
    "detail": "Invalid agent ID format"
  }
  ```

- **500 Internal Server Error:** Failed to deactivate agent
  ```json
  {
    "detail": "Failed to deactivate agent: error message"
  }
  ```

---

## Image Handling

The `image` field supports multiple formats:

1. **Local File Path:** `/path/to/image.png` (will be uploaded to IPFS)
2. **Supabase S3 URL:** `https://supabase.co/storage/v1/object/public/bucket/image.png` (will be downloaded and uploaded to IPFS)
3. **HTTP/HTTPS URL:** `https://example.com/image.png` (used as-is)
4. **IPFS URL:** `ipfs://QmExampleHash` or `https://gateway.pinata.cloud/ipfs/QmExampleHash` (used as-is)

---

## Field Reference

### Required Fields Summary

#### POST /agents/create-and-register
- ✅ `name` (string, min length: 1)
- ✅ `description` (string, min length: 1)
- ❌ All other fields are optional

#### PUT /agents/{agent_id}
- ❌ All fields are optional (only include fields to update)

### Optional Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `image` | string | `null` | Supports local paths, Supabase URLs, HTTP URLs, IPFS URLs |
| `skills` | string[] | `[]` | OASF skill identifiers |
| `domains` | string[] | `[]` | OASF domain identifiers |
| `active` | boolean | `true` | Visibility in searches |
| `x402support` | boolean | `false` | Payment support |
| `mcpEndpoint` | string | `null` | MCP endpoint URL |
| `a2aEndpoint` | string | `null` | A2A endpoint URL |
| `ensName` | string | `null` | ENS name (e.g., "myagent.eth") |
| `walletAddress` | string | `null` | Ethereum wallet address |
| `walletChainId` | integer | `null` | Blockchain chain ID |
| `trustModels` | object | `null` | Trust model configuration |
| `metadata` | object | `{}` | Custom key-value pairs |
| `validateOasf` | boolean | `false` | Validate skills/domains |
| `register` | boolean | `true` | Register on-chain (POST only) |
| `removeEndpoints` | string[] | `null` | Remove endpoints (PUT only) |

---

## Example Integration Code

### JavaScript/TypeScript (Fetch API)

```javascript
// Create and register an agent
async function createAgent(agentData) {
  const response = await fetch('http://localhost:8000/agents/create-and-register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: agentData.name,
      description: agentData.description,
      image: agentData.image,
      active: true,
      register: true
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// Get agent
async function getAgent(agentId) {
  const response = await fetch(`http://localhost:8000/agents/${agentId}`);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// Update agent
async function updateAgent(agentId, updates) {
  const response = await fetch(`http://localhost:8000/agents/${agentId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// Deactivate agent
async function deactivateAgent(agentId) {
  const response = await fetch(`http://localhost:8000/agents/${agentId}`, {
    method: 'DELETE'
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}
```

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

def create_agent(agent_data):
    """Create and register an agent"""
    response = requests.post(
        f"{BASE_URL}/agents/create-and-register",
        json={
            "name": agent_data["name"],
            "description": agent_data["description"],
            "image": agent_data.get("image"),
            "active": agent_data.get("active", True),
            "register": agent_data.get("register", True)
        }
    )
    response.raise_for_status()
    return response.json()

def get_agent(agent_id):
    """Get agent by ID"""
    response = requests.get(f"{BASE_URL}/agents/{agent_id}")
    response.raise_for_status()
    return response.json()

def update_agent(agent_id, updates):
    """Update an agent"""
    response = requests.put(
        f"{BASE_URL}/agents/{agent_id}",
        json=updates
    )
    response.raise_for_status()
    return response.json()

def deactivate_agent(agent_id):
    """Deactivate an agent"""
    response = requests.delete(f"{BASE_URL}/agents/{agent_id}")
    response.raise_for_status()
    return response.json()
```

### cURL Examples

```bash
# Create and register agent
curl -X POST "http://localhost:8000/agents/create-and-register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My AI Agent",
    "description": "An intelligent assistant",
      "active": true,
      "register": true
  }'

# Get agent
curl "http://localhost:8000/agents/11155111:123"

# Update agent
curl -X PUT "http://localhost:8000/agents/11155111:123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "active": false
  }'

# Deactivate agent
curl -X DELETE "http://localhost:8000/agents/11155111:123"
```

---

## Response Schema

### AgentResponse

All agent endpoints return an `AgentResponse` object with the following structure:

```typescript
interface AgentResponse {
  agentId: string | null;           // Format: "chainId:tokenId"
  agentURI: string | null;          // IPFS URI
  name: string;                     // Agent name
  description: string;              // Agent description
  image: string | null;             // Image URL
  active: boolean;                   // Visibility status
  x402support: boolean;             // Payment support
  walletAddress: string | null;     // Wallet address
  walletChainId: number | null;     // Chain ID
  mcpEndpoint: string | null;       // MCP endpoint
  a2aEndpoint: string | null;       // A2A endpoint
  ensEndpoint: string | null;       // ENS endpoint
  endpoints: Endpoint[];            // Endpoint list (currently empty)
  trustModels: string[];            // Trust models (currently empty)
  metadata: Record<string, any>;    // Custom metadata
  skills: string[];                 // OASF skills
  domains: string[];                // OASF domains
  mcpTools: string[];               // MCP tools (currently empty)
  mcpPrompts: string[];             // MCP prompts (currently empty)
  mcpResources: string[];           // MCP resources (currently empty)
  a2aSkills: string[];              // A2A skills (currently empty)
  owners: string[];                 // Owners (currently empty)
  operators: string[];              // Operators (currently empty)
  updatedAt: number | null;         // Timestamp
}
```

---

## Error Handling

All endpoints follow consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**HTTP Status Codes:**
- `200 OK` - Successful GET, PUT, DELETE requests
- `201 Created` - Successful POST request (agent created)
- `400 Bad Request` - Invalid request body or parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

**Best Practices:**
1. Always check the HTTP status code before processing response
2. Handle `400` errors for validation issues
3. Handle `404` errors for missing resources
4. Implement retry logic for `500` errors
5. Log error details for debugging

---

## Rate Limiting

Currently, there are no rate limits implemented. However, it's recommended to:
- Implement client-side rate limiting
- Use exponential backoff for retries
- Batch operations when possible

---

## Versioning

Current API version: `1.0.0`

The API version is included in the FastAPI app metadata and can be accessed via the OpenAPI schema at `/openapi.json`.

---

## Additional Resources

- **Interactive API Documentation (Swagger):** `http://localhost:8000/docs`
- **ReDoc Documentation:** `http://localhost:8000/redoc`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`

---

## Support

For issues or questions:
1. Check the interactive API documentation at `/docs`
2. Review the main README.md for service setup
3. Check error responses for detailed error messages

