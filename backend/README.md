# Agent Commerce Backend

FastAPI backend for agent deployment and management with blockchain integration.

## Prerequisites

- Python 3.11+ (or 3.13+ as specified in pyproject.toml)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

### Installing uv

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Or via pip:**
```bash
pip install uv
```

## Installation

### Using uv

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies using uv:
```bash
uv sync
```

This will:
- Create a virtual environment (if it doesn't exist)
- Install all dependencies from `pyproject.toml`
- Set up the project environment

## Running the Server

### Development Mode

Run the server using uv:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Or using the Python module directly:

```bash
uv run python main.py
```

The server will start on `http://localhost:8000` by default.

### Production Mode

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Using Environment Variables

You can set the port via environment variable:

```bash
PORT=8000 uv run uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── middleware/             # Custom middleware
│   ├── __init__.py
│   ├── logging.py          # Request logging middleware
│   └── auth.py             # Dummy authentication middleware
├── routes/                 # API routes
│   ├── __init__.py
│   └── agent/
│       ├── __init__.py
│       ├── models.py       # Pydantic models
│       └── routes.py       # Agent deployment endpoints
├── pyproject.toml          # Project dependencies
├── requirements.txt        # Alternative requirements file
├── Dockerfile              # Docker configuration
└── docker-compose.yml      # Docker Compose setup
```

## API Endpoints

### Health Check
- `GET /health` - Health check endpoint

### Root
- `GET /` - API information

### Agent Management
- `POST /agent/deploy-agent` - Deploy a new agent
  - Request body:
    ```json
    {
      "agent_type": "client" | "merchant",
      "config": {
        "name": "agent-name",
        "domain": "agent-name.agent.com"
      }
    }
    ```
  - Response:
    ```json
    {
      "agent_id": "agent-id",
      "status": "deployed"
    }
    ```

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker

### Build and Run with Docker

```bash
# Build the image
docker build -f Dockerfile -t agent-commerce-backend ..

# Run the container
docker run -p 8000:8000 agent-commerce-backend
```

### Using Docker Compose

```bash
# From the backend directory
docker-compose up

# Or in detached mode
docker-compose up -d
```

## Development

### Adding Dependencies

Using uv to add a new dependency:

```bash
uv add package-name
```

This will automatically update `pyproject.toml` and install the package.

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black .
uv run isort .
```

## Environment Variables

- `PORT` - Server port (default: 8000)

## Middleware

The application includes the following middleware:

1. **CORS Middleware** - Handles cross-origin requests
2. **Request Logging Middleware** - Logs all incoming requests and responses
3. **Dummy Auth Middleware** - Optional API key validation (dummy implementation)

## Notes

- The backend requires access to the `agents/` directory to execute agent deployment scripts
- Make sure the agents directory is available when running the server
- For Docker, the agents directory is mounted as a volume

## Troubleshooting

### Port Already in Use

If port 8000 is already in use, change it:

```bash
PORT=8001 uv run uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Virtual Environment Issues

If you encounter issues with the virtual environment:

```bash
# Remove existing environment
rm -rf .venv

# Recreate it
uv sync
```

### Import Errors

Make sure you're running commands from the `backend/` directory or using `uv run` which handles the virtual environment automatically.

