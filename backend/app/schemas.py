from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class OrderBase(BaseModel):
    order_id: int
    ticker: str
    action: str
    quantity: int
    price: float
    entry_status: str
    exit_status: Optional[str] | None = None
    last_updated: datetime

    class Config:
        from_attributes = True


class TradeRecordBase(BaseModel):
    trade_id: int
    order_id: int
    tradingsymbol: str
    product: str
    quantity: int
    average_price: float
    transaction_type: str
    fill_timestamp: datetime

    class Config:
        from_attributes = True


class TickerBase(BaseModel):
    symbol: str
    description: str | None = None
    active: bool = True

    class Config:
        from_attributes = True


class OrdersResponse(BaseModel):
    orders: List[OrderBase]


class TradesResponse(BaseModel):
    trades: List[TradeRecordBase]


class TickersResponse(BaseModel):
    tickers: List[TickerBase]


# ---- Extra API Schemas ----
class OrderCreate(BaseModel):
    ticker: str
    action: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)


class OrderUpdate(BaseModel):
    entry_status: str | None = None
    exit_status: str | None = None


class PriceTickBase(BaseModel):
    symbol: str
    price: float
    timestamp: datetime

    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    symbol: str
    ticks: List[PriceTickBase]
