from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, unique=True, index=True)
    ticker = Column(String, index=True)
    action = Column(String)  # BUY / SELL
    quantity = Column(Integer)
    price = Column(Float)
    entry_status = Column(String, index=True)  # OPEN / FILLED / CANCELLED / PENDING
    exit_status = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, index=True)


class TradeRecord(Base):
    __tablename__ = "trade_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    trade_id = Column(Integer, unique=True, index=True)
    order_id = Column(Integer, index=True)
    tradingsymbol = Column(String, index=True)
    product = Column(String, default="MIS")
    quantity = Column(Integer)
    average_price = Column(Float)
    transaction_type = Column(String)  # BUY / SELL
    fill_timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class Ticker(Base):
    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    active = Column(Boolean, default=True)


class PriceTick(Base):
    __tablename__ = "price_ticks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String, index=True)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
