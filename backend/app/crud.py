from __future__ import annotations

from datetime import datetime
from random import choice, randint, random, uniform
from typing import Iterable, List

from sqlalchemy import select, func
import time
import secrets
from threading import Lock
from sqlalchemy.orm import Session

from .models import Order, TradeRecord, Ticker, PriceTick


DEFAULT_TICKERS = [
    ("NIFTY", "NIFTY 50 Index"),
    ("BANKNIFTY", "NIFTY Bank Index"),
    ("RELIANCE", "Reliance Industries"),
    ("GOLD", "Gold Futures"),
    ("SILVER", "Silver Futures"),
]


def seed_if_empty(db: Session) -> None:
    # Create tickers
    if db.query(Ticker).count() == 0:
        for sym, desc in DEFAULT_TICKERS:
            db.add(Ticker(symbol=sym, description=desc, active=True))
        db.commit()

    # Create orders
    if db.query(Order).count() == 0:
        order_id = 10000
        for sym, _ in DEFAULT_TICKERS:
            for _ in range(5):
                order_id += 1
                db.add(
                    Order(
                        order_id=order_id,
                        ticker=sym,
                        action=choice(["BUY", "SELL"]),
                        quantity=choice([25, 50, 75, 100]),
                        price=round(uniform(100.0, 50000.0), 2),
                        entry_status=choice(["OPEN", "PENDING", "FILLED"]),
                        exit_status=None,
                        last_updated=datetime.utcnow(),
                    )
                )
        db.commit()

    # Create trades
    if db.query(TradeRecord).count() == 0:
        trade_id = 9000
        orders = db.query(Order).limit(30).all()
        for o in orders:
            if random() < 0.6:
                trade_id += 1
                db.add(
                    TradeRecord(
                        trade_id=trade_id,
                        order_id=o.order_id,
                        tradingsymbol=o.ticker,
                        product="MIS",
                        quantity=o.quantity,
                        average_price=o.price + uniform(-5, 5),
                        transaction_type=o.action,
                        fill_timestamp=datetime.utcnow(),
                    )
                )
        db.commit()


def get_open_orders(db: Session) -> List[Order]:
    return (
        db.query(Order)
        .filter(Order.entry_status.in_(["OPEN", "PENDING"]))
        .order_by(Order.last_updated.desc())
        .all()
    )


def get_recent_trades(db: Session, limit: int = 100) -> List[TradeRecord]:
    return (
        db.query(TradeRecord)
        .order_by(TradeRecord.fill_timestamp.desc())
        .limit(limit)
        .all()
    )


def get_tickers(db: Session) -> List[Ticker]:
    return db.query(Ticker).filter(Ticker.active == True).order_by(Ticker.symbol).all()


def random_order_update(db: Session) -> Order | None:
    order = db.query(Order).order_by(Order.last_updated.asc()).first()
    if not order:
        return None
    order.entry_status = choice(["OPEN", "PENDING", "FILLED", "CANCELLED"])
    order.last_updated = datetime.utcnow()
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


_id_lock = Lock()


def _unique_int_id() -> int:
    with _id_lock:
        base_ms = int(time.time() * 1000)
        rnd = secrets.randbits(10)
        return base_ms * 1024 + rnd


def insert_random_trade_for_order(db: Session, order: Order | None = None) -> TradeRecord | None:
    if order is None:
        order = db.query(Order).order_by(Order.last_updated.desc()).first()
    if not order:
        return None

    trade_id = _unique_int_id()
    tr = TradeRecord(
        trade_id=trade_id,
        order_id=order.order_id,
        tradingsymbol=order.ticker,
        product="MIS",
        quantity=order.quantity,
        average_price=order.price,
        transaction_type=order.action,
        fill_timestamp=datetime.utcnow(),
    )
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return tr


# ----- Extra CRUD -----
def create_order(db: Session, *, ticker: str, action: str, quantity: int, price: float) -> Order:
    # Unique ID to avoid collisions under concurrency
    next_id = _unique_int_id()
    order = Order(
        order_id=next_id,
        ticker=ticker,
        action=action,
        quantity=quantity,
        price=price,
        entry_status="OPEN",
        exit_status=None,
        last_updated=datetime.utcnow(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_order_by_id(db: Session, *, order_id: int) -> Order | None:
    return db.query(Order).filter(Order.order_id == order_id).first()


def update_order_status(db: Session, *, order_id: int, entry_status: str | None = None, exit_status: str | None = None) -> Order | None:
    order = get_order_by_id(db, order_id=order_id)
    if not order:
        return None
    if entry_status is not None:
        order.entry_status = entry_status
    if exit_status is not None:
        order.exit_status = exit_status
    order.last_updated = datetime.utcnow()
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_trades_by_order(db: Session, *, order_id: int) -> List[TradeRecord]:
    return (
        db.query(TradeRecord)
        .filter(TradeRecord.order_id == order_id)
        .order_by(TradeRecord.fill_timestamp.desc())
        .all()
    )


def add_price_tick(db: Session, *, symbol: str, price: float) -> PriceTick:
    pt = PriceTick(symbol=symbol, price=price, timestamp=datetime.utcnow())
    db.add(pt)
    db.commit()
    db.refresh(pt)
    return pt


def get_price_history(db: Session, *, symbol: str, limit: int = 10) -> List[PriceTick]:
    return (
        db.query(PriceTick)
        .filter(PriceTick.symbol == symbol)
        .order_by(PriceTick.timestamp.desc())
        .limit(limit)
        .all()
    )
