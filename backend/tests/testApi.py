"""
Comprehensive test suite for Trading Dashboard API
Run with: pytest backend/tests/ -v
"""
import pytest
import json
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db
from app.models import Base, Order, TradeRecord, Ticker, PriceTick
from app.database import DB_PATH


# ============================================================================
# FIXTURES & SETUP
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test"""
    # Use in-memory SQLite for testing
    # Use a shared in-memory SQLite DB across connections
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal()
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(scope="function")
def seed_data(test_db):
    """Seed test database with sample data"""
    # Create tickers
    tickers = [
        Ticker(symbol="NIFTY", description="NIFTY 50 Index", active=True),
        Ticker(symbol="BANKNIFTY", description="NIFTY Bank Index", active=True),
        Ticker(symbol="RELIANCE", description="Reliance Industries", active=True),
    ]
    test_db.add_all(tickers)
    test_db.commit()
    
    # Create orders
    orders = [
        Order(order_id=10001, ticker="NIFTY", action="BUY", quantity=50, 
              price=18500.0, entry_status="OPEN", last_updated=datetime.utcnow()),
        Order(order_id=10002, ticker="NIFTY", action="SELL", quantity=100, 
              price=18550.0, entry_status="FILLED", last_updated=datetime.utcnow()),
        Order(order_id=10003, ticker="BANKNIFTY", action="BUY", quantity=25, 
              price=42000.0, entry_status="PENDING", last_updated=datetime.utcnow()),
    ]
    test_db.add_all(orders)
    test_db.commit()
    
    # Create trades
    trades = [
        TradeRecord(trade_id=9001, order_id=10001, tradingsymbol="NIFTY", 
                   product="MIS", quantity=50, average_price=18502.0, 
                   transaction_type="BUY", fill_timestamp=datetime.utcnow()),
        TradeRecord(trade_id=9002, order_id=10002, tradingsymbol="NIFTY", 
                   product="MIS", quantity=100, average_price=18548.0, 
                   transaction_type="SELL", fill_timestamp=datetime.utcnow()),
    ]
    test_db.add_all(trades)
    test_db.commit()
    
    return {"tickers": tickers, "orders": orders, "trades": trades}


# ============================================================================
# TEST: GET /orders/open
# ============================================================================

class TestGetOrdersOpen:
    """Test suite for GET /orders/open endpoint"""
    
    def test_get_orders_open_success(self, client, seed_data):
        """Should return list of open and pending orders"""
        response = client.get("/orders/open")
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert len(data["orders"]) >= 2  # At least OPEN and PENDING orders
    
    def test_get_orders_open_returns_correct_statuses(self, client, seed_data):
        """Should only return OPEN and PENDING status orders"""
        response = client.get("/orders/open")
        data = response.json()
        statuses = [order["entry_status"] for order in data["orders"]]
        assert all(status in ["OPEN", "PENDING"] for status in statuses)
    
    def test_get_orders_open_empty_database(self, client, test_db):
        """Should return empty list when no orders exist"""
        response = client.get("/orders/open")
        assert response.status_code == 200
        data = response.json()
        assert data["orders"] == []
    
    def test_get_orders_open_ordering(self, client, seed_data):
        """Should return orders ordered by last_updated descending"""
        response = client.get("/orders/open")
        data = response.json()
        if len(data["orders"]) > 1:
            timestamps = [order["last_updated"] for order in data["orders"]]
            # Verify descending order
            assert timestamps == sorted(timestamps, reverse=True)


# ============================================================================
# TEST: GET /trades/recent
# ============================================================================

class TestGetTradesRecent:
    """Test suite for GET /trades/recent endpoint"""
    
    def test_get_trades_recent_success(self, client, seed_data):
        """Should return list of recent trades"""
        response = client.get("/trades/recent")
        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert isinstance(data["trades"], list)
    
    def test_get_trades_recent_limit(self, client, seed_data):
        """Should respect limit parameter"""
        response = client.get("/trades/recent?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) <= 1
    
    def test_get_trades_recent_ordering(self, client, seed_data):
        """Should return trades ordered by fill_timestamp descending"""
        response = client.get("/trades/recent")
        data = response.json()
        if len(data["trades"]) > 1:
            timestamps = [trade["fill_timestamp"] for trade in data["trades"]]
            assert timestamps == sorted(timestamps, reverse=True)
    
    def test_get_trades_recent_empty_database(self, client, test_db):
        """Should return empty list when no trades exist"""
        response = client.get("/trades/recent")
        assert response.status_code == 200
        data = response.json()
        assert data["trades"] == []


# ============================================================================
# TEST: GET /tickers
# ============================================================================

class TestGetTickers:
    """Test suite for GET /tickers endpoint"""
    
    def test_get_tickers_success(self, client, seed_data):
        """Should return list of active tickers"""
        response = client.get("/tickers")
        assert response.status_code == 200
        data = response.json()
        assert "tickers" in data
        assert len(data["tickers"]) == 3
    
    def test_get_tickers_only_active(self, client, test_db):
        """Should only return active tickers"""
        # Add inactive ticker
        test_db.add(Ticker(symbol="GOLD", description="Gold Futures", active=False))
        test_db.add(Ticker(symbol="SILVER", description="Silver Futures", active=True))
        test_db.commit()
        
        response = client.get("/tickers")
        data = response.json()
        symbols = [t["symbol"] for t in data["tickers"]]
        assert "GOLD" not in symbols
        assert "SILVER" in symbols
    
    def test_get_tickers_ordering(self, client, seed_data):
        """Should return tickers ordered by symbol"""
        response = client.get("/tickers")
        data = response.json()
        symbols = [t["symbol"] for t in data["tickers"]]
        assert symbols == sorted(symbols)


# ============================================================================
# TEST: POST /orders
# ============================================================================

class TestCreateOrder:
    """Test suite for POST /orders endpoint"""
    
    def test_create_order_success(self, client, seed_data):
        """Should create a new order"""
        payload = {
            "ticker": "NIFTY",
            "action": "BUY",
            "quantity": 50,
            "price": 18600.0
        }
        response = client.post("/orders", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "NIFTY"
        assert data["action"] == "BUY"
        assert data["quantity"] == 50
        assert data["price"] == 18600.0
        assert data["entry_status"] == "OPEN"
    
    def test_create_order_invalid_quantity(self, client, seed_data):
        """Should reject negative quantity"""
        payload = {
            "ticker": "NIFTY",
            "action": "BUY",
            "quantity": -50,
            "price": 18600.0
        }
        response = client.post("/orders", json=payload)
        # Should fail validation or be rejected
        assert response.status_code in [400, 422]
    
    def test_create_order_invalid_price(self, client, seed_data):
        """Should reject negative price"""
        payload = {
            "ticker": "NIFTY",
            "action": "BUY",
            "quantity": 50,
            "price": -18600.0
        }
        response = client.post("/orders", json=payload)
        assert response.status_code in [400, 422]
    
    def test_create_order_invalid_action(self, client, seed_data):
        """Should reject invalid action"""
        payload = {
            "ticker": "NIFTY",
            "action": "INVALID",
            "quantity": 50,
            "price": 18600.0
        }
        response = client.post("/orders", json=payload)
        assert response.status_code in [400, 422]
    
    def test_create_order_missing_fields(self, client, seed_data):
        """Should reject request with missing fields"""
        payload = {"ticker": "NIFTY", "action": "BUY"}  # Missing quantity and price
        response = client.post("/orders", json=payload)
        assert response.status_code == 422


# ============================================================================
# TEST: GET /orders/{order_id}
# ============================================================================

class TestGetOrderById:
    """Test suite for GET /orders/{order_id} endpoint"""
    
    def test_get_order_by_id_success(self, client, seed_data):
        """Should return order by ID"""
        response = client.get("/orders/10001")
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == 10001
        assert data["ticker"] == "NIFTY"
    
    def test_get_order_by_id_not_found(self, client, seed_data):
        """Should return 404 for non-existent order"""
        response = client.get("/orders/99999")
        assert response.status_code == 404
    
    def test_get_order_by_id_invalid_id(self, client, seed_data):
        """Should handle invalid order ID format"""
        response = client.get("/orders/invalid")
        assert response.status_code in [400, 404, 422]


# ============================================================================
# TEST: PATCH /orders/{order_id}
# ============================================================================

class TestUpdateOrder:
    """Test suite for PATCH /orders/{order_id} endpoint"""
    
    def test_update_order_entry_status(self, client, seed_data):
        """Should update order entry status"""
        payload = {"entry_status": "FILLED"}
        response = client.patch("/orders/10001", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["entry_status"] == "FILLED"
    
    def test_update_order_exit_status(self, client, seed_data):
        """Should update order exit status"""
        payload = {"exit_status": "COMPLETED"}
        response = client.patch("/orders/10001", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["exit_status"] == "COMPLETED"
    
    def test_update_order_both_statuses(self, client, seed_data):
        """Should update both entry and exit status"""
        payload = {"entry_status": "FILLED", "exit_status": "COMPLETED"}
        response = client.patch("/orders/10001", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["entry_status"] == "FILLED"
        assert data["exit_status"] == "COMPLETED"
    
    def test_update_order_not_found(self, client, seed_data):
        """Should return 404 for non-existent order"""
        payload = {"entry_status": "FILLED"}
        response = client.patch("/orders/99999", json=payload)
        assert response.status_code == 404


# ============================================================================
# TEST: GET /trades/by-order/{order_id}
# ============================================================================

class TestGetTradesByOrder:
    """Test suite for GET /trades/by-order/{order_id} endpoint"""
    
    def test_get_trades_by_order_success(self, client, seed_data):
        """Should return trades for specific order"""
        response = client.get("/trades/by-order/10001")
        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert all(trade["order_id"] == 10001 for trade in data["trades"])
    
    def test_get_trades_by_order_empty(self, client, seed_data):
        """Should return empty list if no trades for order"""
        response = client.get("/trades/by-order/10003")
        assert response.status_code == 200
        data = response.json()
        assert data["trades"] == []
    
    def test_get_trades_by_order_not_found(self, client, seed_data):
        """Should handle non-existent order"""
        response = client.get("/trades/by-order/99999")
        assert response.status_code in [200, 404]


# ============================================================================
# TEST: GET /prices/{symbol}
# ============================================================================

class TestGetPriceHistory:
    """Test suite for GET /prices/{symbol} endpoint"""
    
    def test_get_price_history_success(self, client, test_db):
        """Should return price history for symbol"""
        # Add price ticks
        ticks = [
            PriceTick(symbol="NIFTY", price=18500.0, timestamp=datetime.utcnow()),
            PriceTick(symbol="NIFTY", price=18510.0, timestamp=datetime.utcnow()),
            PriceTick(symbol="NIFTY", price=18520.0, timestamp=datetime.utcnow()),
        ]
        test_db.add_all(ticks)
        test_db.commit()
        
        response = client.get("/prices/NIFTY")
        assert response.status_code == 200
        data = response.json()
        assert "ticks" in data
        assert len(data["ticks"]) == 3
    
    def test_get_price_history_limit(self, client, test_db):
        """Should respect limit parameter"""
        # Add many price ticks
        for i in range(20):
            test_db.add(PriceTick(symbol="NIFTY", price=18500.0 + i, 
                                 timestamp=datetime.utcnow()))
        test_db.commit()
        
        response = client.get("/prices/NIFTY?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ticks"]) <= 5
    
    def test_get_price_history_empty(self, client, test_db):
        """Should return empty list if no history"""
        response = client.get("/prices/UNKNOWN")
        assert response.status_code == 200
        data = response.json()
        assert data["ticks"] == []


# ============================================================================
# TEST: DATA VALIDATION
# ============================================================================

class TestDataValidation:
    """Test suite for data validation"""
    
    def test_order_quantity_constraints(self, client, seed_data):
        """Should validate order quantity constraints"""
        payload = {
            "ticker": "NIFTY",
            "action": "BUY",
            "quantity": 0,  # Invalid: zero quantity
            "price": 18600.0
        }
        response = client.post("/orders", json=payload)
        assert response.status_code in [400, 422]
    
    def test_order_price_precision(self, client, seed_data):
        """Should handle price precision correctly"""
        payload = {
            "ticker": "NIFTY",
            "action": "BUY",
            "quantity": 50,
            "price": 18600.99
        }
        response = client.post("/orders", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 18600.99


# ============================================================================
# TEST: ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Test suite for error handling"""
    
    def test_malformed_json(self, client):
        """Should handle malformed JSON gracefully"""
        response = client.post("/orders", data="invalid json", 
                              headers={"Content-Type": "application/json"})
        assert response.status_code in [400, 422]
    
    def test_http_methods_not_allowed(self, client):
        """Should reject unsupported HTTP methods"""
        response = client.delete("/tickers")
        assert response.status_code == 405


# ============================================================================
# TEST: RESPONSE SCHEMAS
# ============================================================================

class TestResponseSchemas:
    """Test suite for response schema validation"""
    
    def test_order_response_schema(self, client, seed_data):
        """Should return correct order schema"""
        response = client.get("/orders/10001")
        data = response.json()
        required_fields = ["order_id", "ticker", "action", "quantity", 
                          "price", "entry_status", "last_updated"]
        assert all(field in data for field in required_fields)
    
    def test_trade_response_schema(self, client, seed_data):
        """Should return correct trade schema"""
        response = client.get("/trades/recent")
        data = response.json()
        if data["trades"]:
            trade = data["trades"][0]
            required_fields = ["trade_id", "order_id", "tradingsymbol", 
                              "quantity", "average_price", "transaction_type"]
            assert all(field in trade for field in required_fields)
    
    def test_ticker_response_schema(self, client, seed_data):
        """Should return correct ticker schema"""
        response = client.get("/tickers")
        data = response.json()
        if data["tickers"]:
            ticker = data["tickers"][0]
            required_fields = ["symbol", "active"]
            assert all(field in ticker for field in required_fields)