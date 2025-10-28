from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field
from pydantic import field_validator


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
    ticker: str = Field(min_length=1, max_length=32)
    action: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0, le=1_000_000)
    price: float = Field(gt=0, le=1_000_000_000)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        v = (v or "").strip().upper()
        # Allow A-Z, 0-9, underscore
        for ch in v:
            if not ("A" <= ch <= "Z" or "0" <= ch <= "9" or ch == "_"):
                raise ValueError("ticker may only contain A-Z, 0-9, and underscore")
        return v


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
