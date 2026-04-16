# Morpheye Platform

🔮 **AI-Powered Prediction Market Terminal**

A complete trading platform for Polymarket with Python FastAPI backend.

## 🚀 Quick Start

### Local Development

```bash
# Clone
git clone https://github.com/Hackergut/morpheye-platform.git
cd morpheye-platform

# Install dependencies
pip install fastapi uvicorn httpx pydantic

# Run API
cd api
python main.py
```

**API will be available at:** http://localhost:8000

**API Docs (Swagger):** http://localhost:8000/docs

### Test the Frontend

Open `frontend/index.html` in your browser. It will automatically connect to the local API.

## 📊 Features

### Backend API (Python FastAPI)

- **GET /** - Root status
- **GET /api/health** - Health check
- **GET /api/markets** - Live Polymarket data
- **GET /api/user/{address}** - User portfolio
- **POST /api/trade/open** - Open position
- **POST /api/trade/close** - Close position

### Frontend

- 📊 Market Scanner with live Polymarket data
- 💼 Portfolio tracking
- 💸 Demo trading ($10,000 fake balance)
- 📊 Position management
- 📜 Trade history

### Database

- SQLite for persistence (no external DB needed)
- Auto-initialized on first run
- Data stored in `~/morpheye-data/` locally

## 🐳 Docker Deployment

**Using Docker Compose:**

```bash
docker-compose up -d
```

This starts:
- API on port 8000
- Frontend on port 80

## 🚀 Deploy with Coolify

### 1. Setup Coolify

Install Coolify on your VPS:

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

### 2. Connect Repository

1. Open Coolify dashboard (usually `https://your-server:3000`)
2. Create new resource → Docker Compose
3. Git Repository: `https://github.com/Hackergut/morpheye-platform`
4. Branch: `main`
5. Click **Deploy**

### 3. Access Your Platform

Your platform will be available at your server's URL!

## 🧪 API Examples

**Get markets:**

```bash
curl http://localhost:8000/api/markets?limit=5
```

**Open trade:**

```bash
curl -X POST http://localhost:8000/api/trade/open \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "test_user",
    "market_id": "market_123",
    "market_question": "BTC above 100K?",
    "side": "Yes",
    "price": 0.42,
    "size": 100
  }'
```

**Get user portfolio:**

```bash
curl http://localhost:8000/api/user/test_user
```

## 📁 Project Structure

```
morpheye-platform/
├── api/
│   ├── main.py           # FastAPI backend
│   └── requirements.txt  # Python dependencies
├── frontend/
│   └── index.html        # Web UI
├── Dockerfile            # API container
├── docker-compose.yml    # Full stack
└── README.md
```

## 🔧 Environment Variables

- `DB_PATH` - Database path (default: `/app/data/morpheye.db` in Docker, `~/morpheye-data/` locally)

## 📦 Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLite
- **Frontend:** HTML/CSS/JS (Vanilla)
- **Deployment:** Docker, Coolify

## 🔗 Links

- **Repository:** https://github.com/Hackergut/morpheye-platform
- **Polymarket API:** https://gamma-api.polymarket.com
- **Coolify:** https://coolify.io

## 📝 License

MIT
