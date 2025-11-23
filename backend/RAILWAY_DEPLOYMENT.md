# Railway Deployment Guide

## 🚂 Deploying to Railway

This guide covers deploying the Agent Commerce backend to Railway.

---

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Environment Variables**: Prepare all required environment variables

---

## 🚀 Quick Deploy

### Option 1: Deploy from GitHub (Recommended)

1. **Connect Repository**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

2. **Configure Service**
   - Railway will auto-detect the `railway.toml` in the root
   - **IMPORTANT**: Set **Root Directory** to empty or `/` (uses repository root)
   - The Dockerfile path is `backend/Dockerfile` (relative to repo root)
   - **Build Command**: (auto-detected from Dockerfile)
   - ⚠️ **Do NOT** set Root Directory to `backend/` - the Dockerfile expects repo root as build context

3. **Set Environment Variables**
   - Go to your service → Variables tab
   - Add all required variables (see below)

4. **Deploy**
   - Railway will automatically build and deploy
   - Check the Deployments tab for logs

### Option 2: Deploy via Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project (run from repository ROOT, not backend/)
cd /path/to/agent-commerce
railway init

# Link to existing project (or create new)
railway link

# IMPORTANT: Always run railway commands from repository root
# The Dockerfile expects build context to be repo root

# Set environment variables
railway variables set SUPABASE_URL=your_url
railway variables set SUPABASE_SERVICE_ROLE_KEY=your_key
railway variables set OPENAI_API_KEY=your_key
railway variables set USER_SECRET_KEY=your_key

# Deploy
railway up
```

---

## 🔐 Required Environment Variables

Set these in Railway Dashboard → Your Service → Variables:

### Required

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
OPENAI_API_KEY=sk-...
USER_SECRET_KEY=your-32-byte-hex-encryption-key
```

### Optional

```env
CHAOSCHAIN_NETWORK=BASE_SEPOLIA
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
PORT=8000  # Railway sets this automatically
```

---

## 📁 Project Structure

Railway expects this structure:

```
agent-commerce/
├── railway.toml          # Railway config (root)
├── backend/
│   ├── Dockerfile        # Docker build file
│   ├── pyproject.toml    # Python dependencies
│   ├── uv.lock          # Lock file
│   ├── main.py          # FastAPI app entry point
│   └── ...              # Rest of backend code
└── agents/              # Parent agents directory (if needed)
```

---

## 🐳 Docker Build Process

The Dockerfile:
1. Installs system dependencies (git, build tools)
2. Installs `uv` package manager
3. Copies `pyproject.toml` and `uv.lock`
4. Runs `uv sync` to install dependencies
5. Copies backend code
6. Runs `uvicorn` on port from `$PORT` env var

**Build Context**: Repository root (so Dockerfile can copy from `backend/`)

---

## 🔍 Health Checks

Railway automatically checks:
- **Path**: `/health`
- **Timeout**: 100 seconds
- **Interval**: Every 30 seconds (from Dockerfile HEALTHCHECK)

Your FastAPI app should have a `/health` endpoint:

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## 📊 Monitoring

### View Logs

```bash
# Via Railway Dashboard
# Go to your service → Deployments → Click on deployment → Logs

# Via CLI
railway logs
railway logs --follow  # Follow logs in real-time
```

### Check Status

```bash
railway status
```

### View Metrics

- Go to Railway Dashboard → Your Service → Metrics
- View CPU, Memory, Network usage

---

## 🔄 Updating Deployment

### Automatic Deploys

Railway automatically deploys when you push to:
- `main` branch (production)
- Or configured branch

### Manual Deploy

```bash
# Via CLI
railway up

# Via Dashboard
# Go to Deployments → Redeploy
```

### Rollback

```bash
# Via Dashboard
# Go to Deployments → Select previous deployment → Redeploy

# Via CLI
railway rollback
```

---

## 🐛 Troubleshooting

### Build Fails: "Git executable not found"

✅ **Fixed**: The Dockerfile now installs Git and build tools.

### Build Fails: "Dockerfile `backend/Dockerfile` does not exist"

**Cause**: Railway is using the wrong root directory or you're running `railway up` from the wrong directory.

**Solution**:
1. **If using Railway Dashboard**:
   - Go to your service → Settings
   - Check "Root Directory" - it should be **empty** or `/` (not `backend/`)
   - The Dockerfile path should be `backend/Dockerfile` (relative to repo root)

2. **If using Railway CLI**:
   ```bash
   # Make sure you're in the repository ROOT directory
   cd /path/to/agent-commerce  # NOT backend/
   
   # Verify railway.toml exists in root
   ls railway.toml
   
   # Now run railway up
   railway up
   ```

3. **Verify railway.toml location**:
   - `railway.toml` should be in repository root: `/agent-commerce/railway.toml`
   - NOT in: `/agent-commerce/backend/railway.toml`

### Build Fails: "Module not found"

- Check that `uv.lock` is committed to repository
- Verify `pyproject.toml` has all dependencies
- Check build logs for specific missing package

### Application Won't Start

1. **Check Logs**:
   ```bash
   railway logs
   ```

2. **Verify Environment Variables**:
   ```bash
   railway variables
   ```

3. **Test Locally**:
   ```bash
   docker build -f backend/Dockerfile -t test .
   docker run -p 8000:8000 test
   ```

### Health Check Failing

- Verify `/health` endpoint exists and returns 200
- Check application is listening on `0.0.0.0:$PORT`
- Review health check logs

### Port Issues

Railway sets `PORT` automatically. The Dockerfile uses:
```dockerfile
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

This uses `$PORT` if set, otherwise defaults to 8000.

---

## 💰 Railway Pricing

- **Hobby Plan**: Free tier available
- **Pro Plan**: $20/month for production use
- See [Railway Pricing](https://railway.app/pricing) for details

---

## 🔗 Useful Links

- [Railway Documentation](https://docs.railway.app)
- [Railway Dashboard](https://railway.app/dashboard)
- [Railway CLI Reference](https://docs.railway.app/develop/cli)

---

## ✅ Deployment Checklist

Before deploying:

- [ ] All environment variables set in Railway
- [ ] `railway.toml` configured correctly
- [ ] `Dockerfile` uses `$PORT` environment variable
- [ ] `/health` endpoint implemented
- [ ] `uv.lock` committed to repository
- [ ] Git and build tools in Dockerfile
- [ ] Tested locally with Docker
- [ ] Database connection strings verified
- [ ] API keys are valid

---

## 🎯 Next Steps After Deployment

1. **Get Your URL**:
   - Railway provides: `https://your-app.railway.app`
   - Or use custom domain

2. **Test Endpoints**:
   ```bash
   curl https://your-app.railway.app/health
   ```

3. **Update Frontend**:
   - Update API base URL to Railway URL
   - Test all endpoints

4. **Monitor**:
   - Set up alerts in Railway
   - Monitor logs for errors
   - Check metrics regularly

---

**Last Updated**: November 23, 2025  
**Status**: ✅ Production Ready

