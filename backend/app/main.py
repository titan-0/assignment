from __future__ import annotations

import asyncio
import json
from datetime import datetime
from random import choice, random, uniform
from typing import Dict, List

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import DB_PATH, engine, get_db, session_scope
from .models import Base, Order, TradeRecord, Ticker
from . import crud, schemas

app = FastAPI(title="Trading Engine UI Dashboard API")

# CORS for Vite dev server
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables once
Base.metadata.create_all(bind=engine)

# Seed data if empty
with session_scope() as db:
    crud.seed_if_empty(db)


@app.get("/orders/open", response_model=schemas.OrdersResponse)
def get_orders_open(db: Session = Depends(get_db)):
    orders = crud.get_open_orders(db)
    return {"orders": orders}


@app.get("/trades/recent", response_model=schemas.TradesResponse)
def get_trades_recent(limit: int = 100, db: Session = Depends(get_db)):
    # Clamp limit to a reasonable range
    limit = max(1, min(100, limit))
    trades = crud.get_recent_trades(db, limit=limit)
    return {"trades": trades}


@app.get("/tickers", response_model=schemas.TickersResponse)
def get_tickers(db: Session = Depends(get_db)):
    tickers = crud.get_tickers(db)
    return {"tickers": tickers}


# ---- Extra REST endpoints ----
@app.post("/orders", response_model=schemas.OrderBase)
def create_order(order: schemas.OrderCreate, background: BackgroundTasks, db: Session = Depends(get_db)):
    created = crud.create_order(db, ticker=order.ticker, action=order.action, quantity=order.quantity, price=order.price)
    # Broadcast new/updated order
    background.add_task(
        manager.broadcast,
        {
            "type": "order_update",
            "order_id": created.order_id,
            "status": created.entry_status,
            "last_updated": created.last_updated.isoformat(),
        },
    )
    return created


@app.patch("/orders/{order_id}", response_model=schemas.OrderBase)
def patch_order(order_id: int, payload: schemas.OrderUpdate, background: BackgroundTasks, db: Session = Depends(get_db)):
    updated = crud.update_order_status(db, order_id=order_id, entry_status=payload.entry_status, exit_status=payload.exit_status)
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")
    background.add_task(
        manager.broadcast,
        {
            "type": "order_update",
            "order_id": updated.order_id,
            "status": updated.entry_status,
            "last_updated": updated.last_updated.isoformat(),
        },
    )
    return updated


@app.get("/orders/{order_id}", response_model=schemas.OrderBase)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.get_order_by_id(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/trades/by-order/{order_id}", response_model=schemas.TradesResponse)
def get_trades_by_order(order_id: int, db: Session = Depends(get_db)):
    trades = crud.get_trades_by_order(db, order_id=order_id)
    return {"trades": trades}


@app.get("/prices/{symbol}", response_model=schemas.PriceHistoryResponse)
def get_price_history(symbol: str, limit: int = 10, db: Session = Depends(get_db)):
    limit = max(1, min(200, limit))
    ticks = crud.get_price_history(db, symbol=symbol, limit=limit)
    return {"symbol": symbol, "ticks": list(reversed(ticks))}


class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()

CURRENT_PRICES: Dict[str, float] = {}
DAY_OPEN: Dict[str, float] = {}
_price_events_task: asyncio.Task | None = None


async def init_prices_once():
    if CURRENT_PRICES:
        return
    # Initialize from tickers
    with session_scope() as db:
        tickers = crud.get_tickers(db)
        for t in tickers:
            base = 22000.0 if "NIFTY" in t.symbol else 2500.0
            if t.symbol in ("GOLD", "SILVER"):
                base = 70000.0 if t.symbol == "GOLD" else 85000.0
            price = round(base + uniform(-100, 100), 2)
            CURRENT_PRICES[t.symbol] = price
            if t.symbol not in DAY_OPEN:
                DAY_OPEN[t.symbol] = price


async def _price_and_events_loop():
    await init_prices_once()
    tick = 0
    while True:
        tick += 1
        # Price updates: random walk and broadcast + persist
        for sym in list(CURRENT_PRICES.keys()):
            # Make movements more significant: up to ±10 points per tick
            delta = uniform(-10.0, 10.0)
            CURRENT_PRICES[sym] = round(max(0.01, CURRENT_PRICES[sym] + delta), 2)
            price_val = CURRENT_PRICES[sym]
            await manager.broadcast({
                "type": "price_update",
                "ticker": sym,
                "price": price_val,
                "open": DAY_OPEN.get(sym, price_val),
            })
            # Persist tick
            def do_add_tick(symbol: str, price: float):
                with session_scope() as db:
                    crud.add_price_tick(db, symbol=symbol, price=price)
            await asyncio.to_thread(do_add_tick, sym, price_val)

        # Occasionally update an order or insert a trade
        if tick % 3 == 0:
            def do_order_update_dict():
                with session_scope() as db:
                    o = crud.random_order_update(db)
                    if not o:
                        return None
                    return {
                        "order_id": o.order_id,
                        "status": o.entry_status,
                        "last_updated": o.last_updated.isoformat(),
                    }
            upd = await asyncio.to_thread(do_order_update_dict)
            if upd:
                await manager.broadcast({"type": "order_update", **upd})

        if tick % 5 == 0:
            def do_insert_trade_dict():
                with session_scope() as db:
                    tr = crud.insert_random_trade_for_order(db)
                    if not tr:
                        return None
                    return {
                        "trade_id": tr.trade_id,
                        "order_id": tr.order_id,
                        "price": tr.average_price,
                        "quantity": tr.quantity,
                        "tradingsymbol": tr.tradingsymbol,
                        "transaction_type": tr.transaction_type,
                        "fill_timestamp": tr.fill_timestamp.isoformat(),
                    }
            tr_msg = await asyncio.to_thread(do_insert_trade_dict)
            if tr_msg:
                await manager.broadcast({"type": "new_trade", **tr_msg})

        await asyncio.sleep(1)


@app.on_event("startup")
async def _start_background_loop():
    global _price_events_task
    if _price_events_task is None or _price_events_task.done():
        _price_events_task = asyncio.create_task(_price_and_events_loop())


@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await manager.connect(websocket)
    await init_prices_once()
    try:
        # Send initial snapshot ONLY to this websocket
        for sym, price in CURRENT_PRICES.items():
            await websocket.send_text(json.dumps({
                "type": "price_update",
                "ticker": sym,
                "price": price,
                "open": DAY_OPEN.get(sym, price),
            }))

        # Keep the connection open; ignore incoming messages
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
        raise
