import { DBRecordsResponse, ScannerRow, SignalItem, CandleData, FVGOverlay, OrderBlockOverlay, LiquidityPoolData } from '../types';

export interface ScanApiResponse {
  timestamp: string;
  scanner: ScannerRow[];
  signals: SignalItem[];
  charts: Record<
    string,
    {
      candles: CandleData[];
      fvgs: FVGOverlay[];
      orderBlocks: OrderBlockOverlay[];
    }
  >;
  liquidity: Record<string, LiquidityPoolData[]>;
  cached?: boolean;
}

export interface ExecuteOrderPayload {
  symbol: string;
  side: 'BUY' | 'SELL';
  price: number;
  stop: number;
}

export interface ExecuteOrderResponse {
  success: boolean;
  orderId?: string;
  symbol?: string;
  side?: string;
  price?: number;
  quantity?: number;
  notional?: number;
  riskAmount?: number;
  status?: string;
  error?: string;
}

export interface TestResultResponse {
  success: boolean;
  testCount: number;
  timeTaken: string;
  output: string;
}

export const api = {
  async getScan(refresh = false): Promise<ScanApiResponse> {
    const res = await fetch(`/api/scan${refresh ? '?refresh=true' : ''}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch market scan: ${res.statusText}`);
    }
    return res.json();
  },

  async getRecords(): Promise<DBRecordsResponse> {
    const res = await fetch('/api/records');
    if (!res.ok) {
      throw new Error(`Failed to fetch DB records: ${res.statusText}`);
    }
    return res.json();
  },

  async executeOrder(payload: ExecuteOrderPayload): Promise<ExecuteOrderResponse> {
    const res = await fetch('/api/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(err.error || 'Execution failed');
    }
    return res.json();
  },

  async toggleKillSwitch(engage: boolean): Promise<{ killSwitchEngaged: boolean; status: string }> {
    const res = await fetch('/api/kill-switch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ engage }),
    });
    if (!res.ok) {
      throw new Error(`Failed to toggle kill switch: ${res.statusText}`);
    }
    return res.json();
  },

  async runTests(): Promise<TestResultResponse> {
    const res = await fetch('/api/run-tests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Failed to run test suite: ${res.statusText}`);
    }
    return res.json();
  },

  async getSystemStatus(): Promise<any> {
    const res = await fetch('/api/system-status');
    if (!res.ok) {
      throw new Error(`Failed to fetch system status: ${res.statusText}`);
    }
    return res.json();
  },
};
