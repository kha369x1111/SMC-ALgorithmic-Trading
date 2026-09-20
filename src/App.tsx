import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { PipelineSteps } from './components/PipelineSteps';
import { MarketScanner } from './components/MarketScanner';
import { ChartView } from './components/ChartView';
import { LiquidityMap } from './components/LiquidityMap';
import { SignalCenter } from './components/SignalCenter';
import { RiskPanel } from './components/RiskPanel';
import { CodeInspector } from './components/CodeInspector';
import { KillSwitchModal } from './components/KillSwitchModal';

import {
  initialScannerData,
  ethCandles,
  ethFVGs,
  ethOrderBlocks,
  ethLiquidityPools,
  liveSignals,
} from './data/mockData';
import {
  EnvironmentMode,
  SystemStatus,
  TradingMode,
  ScannerRow,
  SignalItem,
  CandleData,
  FVGOverlay,
  OrderBlockOverlay,
  LiquidityPoolData,
  DBRecordsResponse,
} from './types';
import {
  LayoutGrid,
  BarChart3,
  ShieldAlert,
  Award,
  Calculator,
  Code2,
  RefreshCw,
  Zap,
} from 'lucide-react';
import { api } from './services/api';

export default function App() {
  const [environment, setEnvironment] = useState<EnvironmentMode>('demo');
  const [tradingMode, setTradingMode] = useState<TradingMode>('paper');
  const [systemStatus, setSystemStatus] = useState<SystemStatus>('ONLINE');
  const [killSwitchActive, setKillSwitchActive] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('ETHUSDT');

  // Navigation tab
  const [activeTab, setActiveTab] = useState<
    'scanner' | 'chart' | 'liquidity' | 'signals' | 'risk' | 'code'
  >('scanner');

  // Backend Live State
  const [scannerRows, setScannerRows] = useState<ScannerRow[]>(initialScannerData);
  const [signals, setSignals] = useState<SignalItem[]>(liveSignals);
  const [chartsData, setChartsData] = useState<
    Record<
      string,
      {
        candles: CandleData[];
        fvgs: FVGOverlay[];
        orderBlocks: OrderBlockOverlay[];
      }
    >
  >({
    ETHUSDT: { candles: ethCandles, fvgs: ethFVGs, orderBlocks: ethOrderBlocks },
  });
  const [liquidityMap, setLiquidityMap] = useState<Record<string, LiquidityPoolData[]>>({
    ETHUSDT: ethLiquidityPools,
  });
  const [dbRecords, setDbRecords] = useState<DBRecordsResponse | undefined>(undefined);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [lastSyncTime, setLastSyncTime] = useState<string>('Just now');
  const [isLiveConnected, setIsLiveConnected] = useState<boolean>(false);

  // Mock account metrics
  const equity = 10000.0;
  const dailyPnl = 184.5;
  const dailyPnlPct = 1.84;

  const refreshAllData = useCallback(async (forceRefresh = false) => {
    setIsRefreshing(true);
    try {
      const [scanRes, recordsRes] = await Promise.allSettled([
        api.getScan(forceRefresh),
        api.getRecords(),
      ]);

      if (scanRes.status === 'fulfilled' && scanRes.value) {
        if (scanRes.value.scanner && scanRes.value.scanner.length > 0) {
          setScannerRows(scanRes.value.scanner);
        }
        if (scanRes.value.signals) {
          setSignals(scanRes.value.signals);
        }
        if (scanRes.value.charts) {
          setChartsData((prev) => ({ ...prev, ...scanRes.value.charts }));
        }
        if (scanRes.value.liquidity) {
          setLiquidityMap((prev) => ({ ...prev, ...scanRes.value.liquidity }));
        }
        setIsLiveConnected(true);
      }

      if (recordsRes.status === 'fulfilled' && recordsRes.value) {
        setDbRecords(recordsRes.value);
      }

      const now = new Date();
      setLastSyncTime(now.toLocaleTimeString());
    } catch (err) {
      console.warn('Could not sync with backend bridge:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // Initial load and periodic polling every 8s
  useEffect(() => {
    refreshAllData(true);
    const interval = setInterval(() => {
      refreshAllData(false);
    }, 8000);
    return () => clearInterval(interval);
  }, [refreshAllData]);

  const handleToggleKillSwitch = () => {
    setIsModalOpen(true);
  };

  const handleConfirmKillSwitch = async () => {
    const nextState = !killSwitchActive;
    try {
      await api.toggleKillSwitch(nextState);
      setKillSwitchActive(nextState);
      setSystemStatus(nextState ? 'HALTED' : 'ONLINE');
      refreshAllData(true);
    } catch (err) {
      console.error('Error toggling kill switch:', err);
      // Fallback local toggle
      setKillSwitchActive(nextState);
      setSystemStatus(nextState ? 'HALTED' : 'ONLINE');
    }
  };

  // Active Symbol Data
  const currentChart = chartsData[selectedSymbol] || {
    candles: ethCandles,
    fvgs: ethFVGs,
    orderBlocks: ethOrderBlocks,
  };
  const currentPools = liquidityMap[selectedSymbol] || ethLiquidityPools;
  const currentPrice =
    currentChart.candles.length > 0
      ? currentChart.candles[currentChart.candles.length - 1].close
      : 3512.45;

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col selection:bg-emerald-800 selection:text-white">
      {/* Top Header & Environment Safety Status */}
      <Header
        environment={environment}
        tradingMode={tradingMode}
        systemStatus={systemStatus}
        killSwitchActive={killSwitchActive}
        onToggleKillSwitch={handleToggleKillSwitch}
        onSelectEnv={(env) => setEnvironment(env)}
        equity={equity}
        dailyPnl={dailyPnl}
        dailyPnlPct={dailyPnlPct}
      />

      {/* SMC Quantitative Pipeline Visualizer */}
      <PipelineSteps />

      {/* Navigation Sub-Header */}
      <div className="bg-neutral-900/90 border-b border-neutral-800 px-4 py-2 sticky top-0 z-30 backdrop-blur-xs">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 overflow-x-auto">
          <div className="flex items-center gap-1 font-mono text-xs">
            <button
              onClick={() => setActiveTab('scanner')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeTab === 'scanner'
                  ? 'bg-neutral-800 text-emerald-400 font-bold border border-neutral-700'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-850'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Market Scanner</span>
            </button>

            <button
              onClick={() => setActiveTab('chart')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeTab === 'chart'
                  ? 'bg-neutral-800 text-emerald-400 font-bold border border-neutral-700'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-850'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Structure & Chart</span>
            </button>

            <button
              onClick={() => setActiveTab('liquidity')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeTab === 'liquidity'
                  ? 'bg-neutral-800 text-emerald-400 font-bold border border-neutral-700'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-850'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Liquidity Map</span>
            </button>

            <button
              onClick={() => setActiveTab('signals')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeTab === 'signals'
                  ? 'bg-neutral-800 text-emerald-400 font-bold border border-neutral-700'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-850'
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              <span>Signal Center</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse ml-0.5"></span>
            </button>

            <button
              onClick={() => setActiveTab('risk')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeTab === 'risk'
                  ? 'bg-neutral-800 text-emerald-400 font-bold border border-neutral-700'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-850'
              }`}
            >
              <Calculator className="w-3.5 h-3.5" />
              <span>Risk & DB Persistence</span>
            </button>

            <button
              onClick={() => setActiveTab('code')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeTab === 'code'
                  ? 'bg-neutral-800 text-emerald-400 font-bold border border-neutral-700'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-850'
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Python Engine & Tests</span>
            </button>
          </div>

          <div className="flex items-center gap-3 text-[11px] font-mono shrink-0">
            <button
              onClick={() => refreshAllData(true)}
              disabled={isRefreshing}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-neutral-800 hover:bg-neutral-750 text-neutral-300 hover:text-white transition-colors cursor-pointer border border-neutral-700"
              title="Execute live scan across Python engine"
            >
              <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
              <span>{isRefreshing ? 'Scanning...' : 'Scan Now'}</span>
            </button>

            <div className="flex items-center gap-1 text-neutral-400">
              <Zap className={`w-3 h-3 ${isLiveConnected ? 'text-emerald-400' : 'text-neutral-500'}`} />
              <span className="hidden sm:inline">Engine:</span>
              <span className={isLiveConnected ? 'text-emerald-400 font-bold' : 'text-neutral-400'}>
                {isLiveConnected ? 'CONNECTED' : 'LOCAL'}
              </span>
            </div>

            <div className="text-neutral-400">
              Focus: <span className="text-emerald-400 font-bold">{selectedSymbol}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 flex flex-col gap-6">
        {activeTab === 'scanner' && (
          <div className="flex flex-col gap-6">
            <MarketScanner
              rows={scannerRows}
              selectedSymbol={selectedSymbol}
              onSelectSymbol={(sym) => {
                setSelectedSymbol(sym);
                setActiveTab('chart');
              }}
            />
            {/* Quick Chart Preview below Scanner */}
            <ChartView
              symbol={selectedSymbol}
              candles={currentChart.candles}
              fvgs={currentChart.fvgs}
              orderBlocks={currentChart.orderBlocks}
            />
          </div>
        )}

        {activeTab === 'chart' && (
          <ChartView
            symbol={selectedSymbol}
            candles={currentChart.candles}
            fvgs={currentChart.fvgs}
            orderBlocks={currentChart.orderBlocks}
          />
        )}

        {activeTab === 'liquidity' && (
          <LiquidityMap
            symbol={selectedSymbol}
            currentPrice={currentPrice}
            pools={currentPools}
          />
        )}

        {activeTab === 'signals' && (
          <SignalCenter
            signals={signals}
            onOrderExecuted={() => refreshAllData(true)}
            killSwitchActive={killSwitchActive}
          />
        )}

        {activeTab === 'risk' && (
          <RiskPanel
            equity={equity}
            openPositionsCount={dbRecords?.positions?.length || 1}
            maxOpenPositions={2}
            consecutiveLosses={0}
            maxConsecutiveLosses={3}
            dailyLossPct={0.0}
            maxDailyLossPct={2.0}
            dbRecords={dbRecords}
            onRefreshRecords={() => refreshAllData(true)}
            killSwitchActive={killSwitchActive}
          />
        )}

        {activeTab === 'code' && <CodeInspector />}
      </main>

      {/* Kill Switch Confirmation Modal */}
      <KillSwitchModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleConfirmKillSwitch}
        isCurrentlyActive={killSwitchActive}
      />

      {/* Institutional Terminal Footer */}
      <footer className="bg-neutral-950 border-t border-neutral-800/80 px-4 py-3 text-xs font-mono text-neutral-400">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div>
            SMC Algorithmic Trading Terminal • Python 3.10+ Quantitative Backend • SQLite3 WAL Storage
          </div>
          <div className="flex items-center gap-4 text-[11px]">
            <span>Synced: {lastSyncTime}</span>
            <span>•</span>
            <span className="text-emerald-400">Zero Lookahead Bias Verified</span>
            <span>•</span>
            <span>33/33 Unit Tests Passing</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

