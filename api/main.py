"""
Morpheye Platform - FastAPI Backend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import sqlite3
import json
from datetime import datetime
import os

app = FastAPI(title="Morpheye API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path - use local if not in Docker
import platform
if os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER'):
    DB_PATH = "/app/data/morpheye.db"
else:
    # Local development
    DB_PATH = os.path.expanduser("~/morpheye-data/morpheye.db")

def init_db():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT UNIQUE,
            balance REAL DEFAULT 10000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            market_id TEXT,
            market_question TEXT,
            side TEXT,
            price REAL,
            size REAL,
            opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            market_id TEXT,
            market_question TEXT,
            side TEXT,
            entry_price REAL,
            exit_price REAL,
            size REAL,
            pnl REAL,
            closed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class TradeRequest(BaseModel):
    user_address: str
    market_id: str
    market_question: str
    side: str
    price: float
    size: float

class CloseRequest(BaseModel):
    user_address: str
    position_id: int
    exit_price: float

POLYMARKET_API = "https://gamma-api.polymarket.com/markets"

@app.get("/")
async def root():
    return {"status": "online", "service": "morpheye-api", "version": "1.0.0"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/markets")
async def get_markets(limit: int = 30):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{POLYMARKET_API}?limit={limit}&active=true", timeout=10.0)
            if not response.ok:
                raise HTTPException(status_code=502, detail="Polymarket API error")
            data = response.json()
            markets = []
            for m in data[:limit]:
                try:
                    outcome_prices = json.loads(m.get('outcomePrices', '[]'))
                    yes_price = (outcome_prices[0] if len(outcome_prices) > 0 else 0.5) * 100
                    no_price = (outcome_prices[1] if len(outcome_prices) > 1 else 0.5) * 100
                    markets.append({
                        "id": m.get('id'),
                        "question": m.get('question', 'Unknown'),
                        "category": (m.get('tags') or ['General'])[0],
                        "yes_price": round(yes_price, 1),
                        "no_price": round(no_price, 1),
                        "volume": m.get('volume24hr') or m.get('volume', 0),
                        "liquidity": m.get('liquidity', 0),
                        "image": m.get('image'),
                        "end_date": m.get('endDate'),
                        "active": m.get('active', True)
                    })
                except:
                    continue
            return {"markets": markets, "count": len(markets), "source": "polymarket"}
    except Exception as e:
        return {"markets": get_mock_markets(), "count": 5, "source": "fallback", "error": str(e)}

def get_mock_markets():
    return [
        {"id": "1", "question": "BTC above $100K by Dec 2025?", "category": "Crypto", "yes_price": 42, "no_price": 58, "volume": 3800000, "liquidity": 2100000},
        {"id": "2", "question": "Trump announces new tariffs?", "category": "Politics", "yes_price": 67, "no_price": 33, "volume": 1240000, "liquidity": 890000},
        {"id": "3", "question": "Fed cuts rates in Q2 2025?", "category": "Finance", "yes_price": 28, "no_price": 72, "volume": 2150000, "liquidity": 1540000},
        {"id": "4", "question": "Ethereum above $5K?", "category": "Crypto", "yes_price": 35, "no_price": 65, "volume": 980000, "liquidity": 720000},
        {"id": "5", "question": "Real Madrid wins Champions League?", "category": "Sports", "yes_price": 18, "no_price": 82, "volume": 450000, "liquidity": 320000}
    ]

@app.get("/api/user/{address}")
async def get_user(address: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE address = ?", (address,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (address) VALUES (?)", (address,))
        conn.commit()
        c.execute("SELECT * FROM users WHERE address = ?", (address,))
        user = c.fetchone()
    user_id = user[0]
    c.execute("SELECT * FROM positions WHERE user_id = ?", (user_id,))
    positions = c.fetchall()
    c.execute("SELECT SUM(pnl) FROM trades WHERE user_id = ?", (user_id,))
    total_pnl = c.fetchone()[0] or 0
    conn.close()
    return {
        "address": address,
        "balance": user[2],
        "positions": [{"id": p[0], "market_id": p[2], "market_question": p[3], "side": p[4], "price": p[5], "size": p[6]} for p in positions],
        "total_pnl": total_pnl
    }

@app.post("/api/trade/open")
async def open_trade(trade: TradeRequest):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE address = ?", (trade.user_address,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (address) VALUES (?)", (trade.user_address,))
        conn.commit()
        c.execute("SELECT * FROM users WHERE address = ?", (trade.user_address,))
        user = c.fetchone()
    user_id = user[0]
    balance = user[2]
    if trade.size > balance:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient balance")
    c.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (trade.size, user_id))
    c.execute('INSERT INTO positions (user_id, market_id, market_question, side, price, size) VALUES (?, ?, ?, ?, ?, ?)',
              (user_id, trade.market_id, trade.market_question, trade.side, trade.price, trade.size))
    conn.commit()
    position_id = c.lastrowid
    conn.close()
    return {"success": True, "position_id": position_id, "remaining_balance": balance - trade.size}

@app.post("/api/trade/close")
async def close_trade(close: CloseRequest):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM positions WHERE id = ?", (close.position_id,))
    position = c.fetchone()
    if not position:
        conn.close()
        raise HTTPException(status_code=404, detail="Position not found")
    pnl = (close.exit_price - position[5]) * position[6]
    c.execute("SELECT * FROM users WHERE address = ?", (close.user_address,))
    user = c.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    new_balance = user[2] + position[6] + pnl
    c.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user[0]))
    c.execute('INSERT INTO trades (user_id, market_id, market_question, side, entry_price, exit_price, size, pnl) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
              (user[0], position[2], position[3], position[4], position[5], close.exit_price, position[6], pnl))
    c.execute("DELETE FROM positions WHERE id = ?", (close.position_id,))
    conn.commit()
    conn.close()
    return {"success": True, "pnl": pnl, "new_balance": new_balance}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
