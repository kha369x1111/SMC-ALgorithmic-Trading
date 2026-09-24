# Authentication and credentials

This document describes the implementation visible in this repository's `main` branch. It does not claim that the web UI has a user login system.

## Components and request flow

1. The React UI sends requests to the Express server in `server.ts`.
2. Express exposes `GET /api/scan`, `GET /api/records`, `POST /api/execute`, `POST /api/kill-switch`, `POST /api/run-tests`, and `GET /api/system-status`. The inspected routes have no authentication middleware or per-user authorization check.
3. For scan, records, execution, and kill-switch operations, Express starts `smc_terminal/src/api_bridge.py` as a subprocess and inherits its process environment.
4. The bridge's `execute_order` currently creates a `PaperTradingAdapter` and records the result in SQLite. This web request path does not call Binance or use Binance API credentials.
5. Separately, `smc_terminal/src/exchange/binance.py` implements Binance Spot/Testnet API authentication for code paths that instantiate `BinanceSpotAdapter`. Its public requests need no key. Signed requests require an API key and secret: it puts the key in `X-MBX-APIKEY`, adds a timestamp and 5000 ms receive window, computes an HMAC-SHA256 signature over URL-encoded parameters, and sends the signature with the request. It calibrates its clock against Binance server time. This is exchange API authentication, not user login to the web UI.

## Credential and token handling

- `smc_terminal/.env.example` names `BINANCE_API_KEY`, `BINANCE_API_SECRET`, optional `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID` without actual values. The root `.env.example` also documents `GEMINI_API_KEY` and `APP_URL`. Git ignores `.env*` except `.env.example`.
- The adapter receives `api_key` and `api_secret` constructor arguments and retains them in process memory. A caller must supply them; the inspected adapter does not load the `.env` file itself.
- The adapter checks the account response's `enableWithdrawals` field during `connect()` and rejects a credential when that field is true. Confirm the exchange response semantics and permissions independently before relying on this as a complete withdrawal safeguard.
- No session cookie, JWT issuance, refresh-token flow, password handling, or browser token storage was found in the inspected Express request path. Do not assume the server protects its endpoints.
- The README describes an in-app Windows Credential Store manager and live-trading confirmation, but these statements are documentation claims; they should be verified against the actual desktop startup and credential-loading path before being treated as active controls.

## Operational implications

The Express server listens on `0.0.0.0:3000`. Its execution and kill-switch endpoints accept requests without a user identity check. Restrict network access to trusted local environments until server-side authentication and authorization are implemented. `/api/run-tests` also starts a subprocess on request. The web execution bridge currently uses paper trading; avoid describing it as live exchange execution.

Never commit real API credentials or paste them into issues, logs, or screenshots. Use narrowly scoped exchange keys and rotate any key exposed in Git history.
