"""
SMC Algorithmic Trading Terminal - Binance Spot Exchange Adapter.
Implements real HTTP REST transport for Binance Testnet and Spot API.
Enforces pre-flight filter validation (minNotional, stepSize, tickSize),
HMAC-SHA256 signature generation, clock synchronization, and withdrawal safety check.
"""

import hashlib
import hmac
import json
import logging
import math
import time
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.parse
import urllib.request

from src.data.models import Candle, OrderBook, Ticker, Timeframe
from src.exchange.base import ExchangeAdapter
from src.exchange.exceptions import AuthenticationError, ExchangeError, OrderError
from src.exchange.models import (
    BalanceModel,
    OrderRequest,
    OrderResponse,
    OrderSide,
    OrderStatus,
    OrderType,
    PositionModel,
    SymbolConstraints,
)

logger = logging.getLogger("SMC_TERMINAL.BINANCE")


class BinanceSpotAdapter(ExchangeAdapter):
    """
    Production-grade Binance Spot and Testnet API adapter.
    Handles clock calibration, rate limits, symbol constraints caching,
    HMAC-SHA256 signature signing, and strict withdrawal lockout.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        testnet: bool = True,
        timeout: float = 10.0,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.timeout = timeout
        self._connected = False
        self.base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"

        # Millisecond clock offset: server_time - local_time
        self._time_offset: int = 0

        # In-memory cached symbol exchange info rules
        self._constraints_cache: Dict[str, SymbolConstraints] = {}

    def get_name(self) -> str:
        return "binance_spot_testnet" if self.testnet else "binance_spot_live"

    def _http_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Any:
        """Execute raw HTTP request against Binance REST API."""
        params = params.copy() if params else {}

        headers = {
            "User-Agent": "SMCTerminal/1.0",
            "Accept": "application/json",
        }

        if signed:
            if not self.api_key or not self.api_secret:
                raise AuthenticationError("API Key and API Secret are required for signed Binance endpoints.")
            headers["X-MBX-APIKEY"] = self.api_key

            # Synchronize timestamp with calibrated server time
            current_ms = int(time.time() * 1000) + self._time_offset
            params["timestamp"] = current_ms
            params["recvWindow"] = 5000

            # Compute HMAC-SHA256 signature
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            query_string += f"&signature={signature}"
        else:
            query_string = urllib.parse.urlencode(params) if params else ""

        url = f"{self.base_url}{path}"
        data = None

        if method.upper() == "GET" and query_string:
            url = f"{url}?{query_string}"
        elif method.upper() in ("POST", "DELETE"):
            if query_string:
                data = query_string.encode("utf-8")
                headers["Content-Type"] = "application/x-www-form-urlencoded"

        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_body = resp.read().decode("utf-8")
                return json.loads(resp_body) if resp_body else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            error_json = {}
            try:
                error_json = json.loads(error_body)
            except Exception:
                pass

            msg = error_json.get("msg", error_body)
            code = error_json.get("code", e.code)

            if e.code == 429:
                logger.error("Binance Rate Limit Exceeded (HTTP 429)")
                raise ExchangeError(f"Binance Rate Limit Exceeded (HTTP 429): {msg}")
            elif e.code == 418:
                logger.critical("Binance IP Banned (HTTP 418)")
                raise ExchangeError(f"Binance IP Banned (HTTP 418): {msg}")
            elif e.code == 401:
                raise AuthenticationError(f"Binance Authentication Failed (HTTP 401): {msg}")
            elif -1013 <= code <= -1010 or code in (-2010, -2011, -1111):
                raise OrderError(f"Binance Order Filter Rejection ({code}): {msg}")
            else:
                raise ExchangeError(f"Binance HTTP {e.code} Error ({code}): {msg}")
        except urllib.error.URLError as e:
            raise ExchangeError(f"Network error connecting to Binance: {str(e.reason)}")
        except Exception as e:
            raise ExchangeError(f"Unexpected error in Binance request: {str(e)}")

    def ping(self) -> bool:
        """Test public connectivity to Binance API."""
        res = self._http_request("GET", "/api/v3/ping")
        return res == {}

    def get_server_time(self) -> int:
        """Fetch exchange server time and calibrate clock offset."""
        local_before = int(time.time() * 1000)
        res = self._http_request("GET", "/api/v3/time")
        local_after = int(time.time() * 1000)
        server_time = int(res["serverTime"])
        local_midpoint = (local_before + local_after) // 2
        self._time_offset = server_time - local_midpoint
        logger.info("Binance server time calibrated. Offset: %d ms", self._time_offset)
        return server_time

    def connect(self) -> bool:
        """
        Establish connection, sync clock drift, and perform security verification.
        Crucial: Rejects API key if withdrawal permission is detected!
        """
        try:
            self.ping()
            self.get_server_time()

            # If API credentials provided, verify account and withdrawal lockout
            if self.api_key and self.api_secret:
                account_info = self._http_request("GET", "/api/v3/account", signed=True)
                
                # SECURITY RULE: Withdrawals MUST NOT be enabled
                if account_info.get("enableWithdrawals", False):
                    self._connected = False
                    raise AuthenticationError(
                        "CRITICAL SECURITY RISK: Provided Binance API Key has WITHDRAWALS ENABLED! "
                        "The SMC Trading Terminal strictly refuses to run with withdrawal-capable keys. "
                        "Please regenerate an API key with Read-Only and Spot Trading permissions only."
                    )
                logger.info("Binance account verified. Spot trading enabled: %s", account_info.get("canTrade", False))

            self._connected = True
            logger.info("BinanceSpotAdapter connected successfully to %s", self.base_url)
            return True
        except Exception as e:
            self._connected = False
            logger.error("Binance connection failed: %s", str(e))
            raise

    def disconnect(self) -> None:
        self._connected = False
        logger.info("BinanceSpotAdapter disconnected.")

    def is_connected(self) -> bool:
        return self._connected

    def fetch_exchange_info(self, symbols: Optional[List[str]] = None) -> Dict[str, SymbolConstraints]:
        """Fetch and cache exchange filters (tickSize, stepSize, minNotional)."""
        params = {}
        if symbols and len(symbols) == 1:
            params["symbol"] = symbols[0]

        res = self._http_request("GET", "/api/v3/exchangeInfo", params=params)
        symbols_data = res.get("symbols", [])

        target_set = set(symbols) if symbols else None
        for s in symbols_data:
            sym = s.get("symbol", "")
            if target_set and sym not in target_set:
                continue

            tick_size = 0.01
            price_precision = s.get("quoteAssetPrecision", 2)
            step_size = 0.0001
            min_qty = 0.0001
            max_qty = 100000.0
            qty_precision = s.get("baseAssetPrecision", 4)
            min_notional = 5.0
            is_active = (s.get("status") == "TRADING")

            for f in s.get("filters", []):
                filter_type = f.get("filterType")
                if filter_type == "PRICE_FILTER":
                    tick_size = float(f.get("tickSize", 0.01))
                    if tick_size > 0:
                        price_precision = max(0, int(round(-math.log10(tick_size))))
                elif filter_type == "LOT_SIZE":
                    step_size = float(f.get("stepSize", 0.0001))
                    min_qty = float(f.get("minQty", 0.0001))
                    max_qty = float(f.get("maxQty", 100000.0))
                    if step_size > 0:
                        qty_precision = max(0, int(round(-math.log10(step_size))))
                elif filter_type in ("NOTIONAL", "MIN_NOTIONAL"):
                    min_notional = float(f.get("minNotional", f.get("notional", 5.0)))

            constraints = SymbolConstraints(
                symbol=sym,
                tick_size=tick_size,
                step_size=step_size,
                min_qty=min_qty,
                max_qty=max_qty,
                min_notional=min_notional,
                price_precision=price_precision,
                qty_precision=qty_precision,
                is_trading_active=is_active,
            )
            self._constraints_cache[sym] = constraints

        return self._constraints_cache

    def register_constraints(self, constraints: SymbolConstraints) -> None:
        """Register exchange filter constraints directly."""
        self._constraints_cache[constraints.symbol] = constraints

    def get_symbol_constraints(self, symbol: str) -> SymbolConstraints:
        """Fetch cached constraints, or pull live from exchangeInfo, or safe fallback."""
        if symbol in self._constraints_cache:
            return self._constraints_cache[symbol]

        try:
            self.fetch_exchange_info([symbol])
            if symbol in self._constraints_cache:
                return self._constraints_cache[symbol]
        except Exception as e:
            logger.warning("Could not fetch exchangeInfo for %s: %s. Using standard defaults.", symbol, e)

        # Standard safe defaults
        if "BTC" in symbol:
            c = SymbolConstraints(symbol, tick_size=0.01, step_size=0.00001, min_qty=0.00001, max_qty=1000.0, min_notional=5.0, price_precision=2, qty_precision=5)
        elif "ETH" in symbol:
            c = SymbolConstraints(symbol, tick_size=0.01, step_size=0.0001, min_qty=0.0001, max_qty=10000.0, min_notional=5.0, price_precision=2, qty_precision=4)
        else:
            c = SymbolConstraints(symbol, tick_size=0.001, step_size=0.01, min_qty=0.01, max_qty=100000.0, min_notional=5.0, price_precision=3, qty_precision=2)
        self._constraints_cache[symbol] = c
        return c

    def get_ticker(self, symbol: str) -> Ticker:
        """Fetch 24h ticker and book depth benchmark."""
        res = self._http_request("GET", "/api/v3/ticker/24hr", params={"symbol": symbol})
        return Ticker(
            symbol=symbol,
            bid=float(res.get("bidPrice", res.get("lastPrice", 0.0))),
            ask=float(res.get("askPrice", res.get("lastPrice", 0.0))),
            last_price=float(res.get("lastPrice", 0.0)),
            volume_24h=float(res.get("volume", 0.0)),
            timestamp=int(res.get("closeTime", int(time.time() * 1000))),
        )

    def get_candles(self, symbol: str, timeframe: Timeframe, limit: int = 200) -> List[Candle]:
        """Fetch verified OHLCV candlestick sequence from Binance."""
        params = {
            "symbol": symbol,
            "interval": timeframe.value,
            "limit": min(limit, 1000),
        }
        res = self._http_request("GET", "/api/v3/klines", params=params)

        candles: List[Candle] = []
        for row in res:
            # Format: [open_time, open, high, low, close, volume, close_time, ...]
            candles.append(Candle(
                timestamp=int(row[0]),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
                is_closed=True,
            ))
        return candles

    def get_order_book(self, symbol: str, depth: int = 20) -> OrderBook:
        """Fetch order book bids and asks."""
        params = {"symbol": symbol, "limit": min(depth, 100)}
        res = self._http_request("GET", "/api/v3/depth", params=params)

        bids = [(float(b[0]), float(b[1])) for b in res.get("bids", [])]
        asks = [(float(a[0]), float(a[1])) for a in res.get("asks", [])]

        return OrderBook(
            symbol=symbol,
            bids=bids,
            asks=asks,
            timestamp=int(time.time() * 1000),
        )

    def create_order(self, request: OrderRequest) -> OrderResponse:
        """
        Validate constraints and dispatch order to Binance Spot API.
        Enforces idempotency using request.client_order_id.
        """
        constraints = self.get_symbol_constraints(request.symbol)
        price = request.price or 0.0
        rounded_qty = constraints.round_qty(request.quantity)
        rounded_price = constraints.round_price(price) if price > 0 else None

        # Pre-flight filter validation
        test_price = rounded_price if (rounded_price and rounded_price > 0) else self.get_ticker(request.symbol).last_price
        constraints.validate_order(test_price, rounded_qty)

        # Build order payload
        params: Dict[str, Any] = {
            "symbol": request.symbol,
            "side": request.side.value,
            "type": request.order_type.value,
            "quantity": rounded_qty,
            "newClientOrderId": request.client_order_id,
            "newOrderRespType": "FULL",
        }

        if request.order_type == OrderType.LIMIT:
            if not rounded_price or rounded_price <= 0:
                raise OrderError("Price is required for LIMIT order")
            params["price"] = rounded_price
            params["timeInForce"] = "GTC"

        if request.stop_price and request.stop_price > 0:
            params["stopPrice"] = constraints.round_price(request.stop_price)

        res = self._http_request("POST", "/api/v3/order", params=params, signed=True)

        status_mapping = {
            "NEW": OrderStatus.NEW,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "FILLED": OrderStatus.FILLED,
            "CANCELED": OrderStatus.CANCELED,
            "REJECTED": OrderStatus.REJECTED,
            "EXPIRED": OrderStatus.EXPIRED,
        }

        # Calculate executed quantity and average price
        executed_qty = float(res.get("executedQty", 0.0))
        cummulative_quote = float(res.get("cummulativeQuoteQty", 0.0))
        avg_price = (cummulative_quote / executed_qty) if executed_qty > 0 else (rounded_price or test_price)

        fee_paid = 0.0
        for fill in res.get("fills", []):
            fee_paid += float(fill.get("commission", 0.0))

        return OrderResponse(
            client_order_id=res.get("clientOrderId", request.client_order_id),
            exchange_order_id=str(res.get("orderId", "")),
            symbol=request.symbol,
            status=status_mapping.get(res.get("status", "NEW"), OrderStatus.NEW),
            side=request.side,
            order_type=request.order_type,
            orig_qty=float(res.get("origQty", rounded_qty)),
            executed_qty=executed_qty,
            avg_price=avg_price,
            fee_paid=fee_paid,
            timestamp=int(res.get("transactTime", int(time.time() * 1000))),
        )

    def cancel_order(self, symbol: str, client_order_id: str) -> bool:
        """Cancel active order on Binance."""
        params = {
            "symbol": symbol,
            "origClientOrderId": client_order_id,
        }
        res = self._http_request("DELETE", "/api/v3/order", params=params, signed=True)
        return res.get("status") == "CANCELED"

    def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderResponse]:
        """Fetch all currently active limit orders."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        res = self._http_request("GET", "/api/v3/openOrders", params=params, signed=True)

        orders = []
        for o in res:
            side = OrderSide.BUY if o.get("side") == "BUY" else OrderSide.SELL
            otype = OrderType.LIMIT if o.get("type") == "LIMIT" else OrderType.MARKET
            orders.append(OrderResponse(
                client_order_id=o.get("clientOrderId", ""),
                exchange_order_id=str(o.get("orderId", "")),
                symbol=o.get("symbol", ""),
                status=OrderStatus.NEW,
                side=side,
                order_type=otype,
                orig_qty=float(o.get("origQty", 0.0)),
                executed_qty=float(o.get("executedQty", 0.0)),
                avg_price=float(o.get("price", 0.0)),
                fee_paid=0.0,
                timestamp=int(o.get("time", 0)),
            ))
        return orders

    def get_account_balances(self) -> Dict[str, BalanceModel]:
        """Fetch real free and locked spot balances."""
        res = self._http_request("GET", "/api/v3/account", signed=True)
        balances = {}
        for b in res.get("balances", []):
            asset = b.get("asset", "")
            free = float(b.get("free", 0.0))
            locked = float(b.get("locked", 0.0))
            if free > 0 or locked > 0:
                balances[asset] = BalanceModel(
                    asset=asset,
                    free=free,
                    locked=locked,
                    total=free + locked,
                )
        return balances

    def get_positions(self) -> List[PositionModel]:
        """Spot trading does not have margin positions natively, returns empty list."""
        return []
