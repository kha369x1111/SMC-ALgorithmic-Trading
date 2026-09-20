# SMC / ICT Algorithmic Trading Terminal — Windows Desktop Edition

An institutional-grade algorithmic trading terminal for cryptocurrencies based on formal, programmable **Smart Money Concepts (SMC)** and **Inner Circle Trader (ICT)** market mechanics.

> **Crucial Disclaimer**: SMC/ICT concepts are modeled strictly as algorithmic rule-sets and quantitative hypotheses. No market-structure methodology guarantees profitability. Live trading is strictly gated behind multi-layer safety confirmations.

---

## 1. Quantitative Pipeline Architecture

The terminal enforces a deterministic, multi-stage state transition pipeline:

```
DATA ENGINE
  ↓ (Validation, Chronology, Staleness Guard)
MARKET STATE & MTF CONTEXT (HTF 4H Bias)
  ↓
LIQUIDITY MAP (BSL, SSL, EQH, EQL, PDH/PDL, Session Extremes)
  ↓
STRUCTURE (Fractal Swings, HH/HL, LL/LH, BOS, MSS/CHoCH)
  ↓
DISPLACEMENT ENGINE (Body/ATR ratio, volume confirmation)
  ↓
PD ARRAY (50% Fair Value Gaps, Order Blocks with 0-100 score)
  ↓
DEALING RANGE (Premium / Discount valuation filter)
  ↓
SESSION & NEWS GATING (London / NY Killzones, High-impact news locks)
  ↓
SETUP DETECTION (Armed setups with explainable rationale)
  ↓
SIGNAL SCORE (0–10 score with transparent weighting)
  ↓
RISK GATING (Daily Loss Guard, Consecutive Loss Limit, R:R >= 2.0)
  ↓
EXECUTION ENGINE (Tick/Step size precision, Min Notional, Idempotency)
  ↓
ORDER RECONCILIATION & POSITION MANAGEMENT
```

---

## 2. Installation & Prerequisites

- **OS**: Windows 10/11 (or Linux/macOS for backtesting/headless execution)
- **Python Version**: Python 3.10 or Python 3.11+

### Virtual Environment Setup

```bash
# Clone or navigate to the project directory
cd smc_terminal

# Create dedicated virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Or on Linux / macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 3. Configuration & API Safety

Configuration is controlled via `config.yaml`. Sensitive API keys must **NEVER** be committed to Git or stored in plaintext:

```bash
cp .env.example .env
```

Set your credentials in `.env` or use the in-app Windows Credential Store manager:
```env
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
TELEGRAM_BOT_TOKEN=optional_token
TELEGRAM_CHAT_ID=optional_chat_id
```

### Safety Rules:
1. **Default Mode**: Always boots in `environment: demo` and `trading_mode: paper`.
2. **Live Gating**: Live trading requires changing `config.yaml`, confirming within GUI with prominent red banner, and explicitly verifying order parameters.
3. **Withdrawal Permissions**: The exchange adapter strictly prohibits and rejects API keys with withdrawal permissions.

---

## 4. Running the Terminal

### Interactive GUI Mode (PySide6)
```bash
python main.py
```

### Paper Trading CLI Mode
```bash
python main.py --mode paper --symbol ETHUSDT
```

### Backtest Mode
```bash
python main.py --mode backtest --config config.yaml
```

---

## 5. Running the Unit Test Suite

Execute the deterministic unit tests:

```bash
# Run all tests
python -m unittest discover tests

# Or run specific test suites
python tests/test_market_structure.py
python tests/test_liquidity.py
python tests/test_fvg_and_ob.py
python tests/test_risk_and_sizing.py
python tests/test_no_lookahead.py
```

---

## 6. Windows Standalone Packaging (.EXE)

Build a self-contained Windows executable via PyInstaller:

```cmd
build_windows.bat
```

The output standalone binary is generated at:
`dist\SMC-Trading-Terminal\SMC-Trading-Terminal.exe`

Credentials and sensitive `.env` files are never bundled into the binary.
