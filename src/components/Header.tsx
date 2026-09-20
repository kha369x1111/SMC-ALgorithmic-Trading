import React from 'react';
import {
  ShieldAlert,
  Radio,
  Activity,
  Zap,
  TrendingUp,
  AlertTriangle,
  Lock,
  Layers,
} from 'lucide-react';
import { EnvironmentMode, SystemStatus, TradingMode } from '../types';

interface HeaderProps {
  environment: EnvironmentMode;
  tradingMode: TradingMode;
  systemStatus: SystemStatus;
  killSwitchActive: boolean;
  onToggleKillSwitch: () => void;
  onSelectEnv: (env: EnvironmentMode) => void;
  equity: number;
  dailyPnl: number;
  dailyPnlPct: number;
}

export const Header: React.FC<HeaderProps> = ({
  environment,
  tradingMode,
  systemStatus,
  killSwitchActive,
  onToggleKillSwitch,
  onSelectEnv,
  equity,
  dailyPnl,
  dailyPnlPct,
}) => {
  return (
    <header className="bg-neutral-950 border-b border-neutral-800 text-neutral-200">
      {/* Real Real-Money Warning if LIVE */}
      {environment === 'live' && (
        <div className="bg-red-950/80 border-b border-red-700/80 px-4 py-2 flex items-center justify-between text-xs font-semibold text-red-200 animate-pulse">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span>🔴 LIVE ENVIRONMENT ACTIVE — REAL CAPITAL AT RISK</span>
          </div>
          <span className="bg-red-800/80 px-2 py-0.5 rounded text-[10px] tracking-wider uppercase">
            Exchange Execution Engaged
          </span>
        </div>
      )}

      {/* Main Bar */}
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Title and Brand */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-950/70 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-sm">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-white">
                SMC ALGORITHMIC TRADING TERMINAL
              </h1>
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-neutral-800 border border-neutral-700 text-neutral-400">
                v1.0-STABLE
              </span>
            </div>
            <p className="text-xs text-neutral-400">
              Institutional Market-Structure & Liquidity Execution Engine
            </p>
          </div>
        </div>

        {/* Operating Environment Status Badges */}
        <div className="flex items-center gap-2">
          {/* Environment Selector */}
          <div className="flex items-center bg-neutral-900 border border-neutral-800 rounded-md p-0.5 text-xs font-mono">
            <button
              onClick={() => onSelectEnv('demo')}
              className={`px-2.5 py-1 rounded transition-colors ${
                environment === 'demo'
                  ? 'bg-neutral-800 text-emerald-400 font-semibold shadow-xs'
                  : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              DEMO
            </button>
            <button
              onClick={() => onSelectEnv('testnet')}
              className={`px-2.5 py-1 rounded transition-colors ${
                environment === 'testnet'
                  ? 'bg-amber-950/60 text-amber-300 font-semibold border border-amber-600/40'
                  : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              TESTNET
            </button>
            <button
              onClick={() => onSelectEnv('live')}
              className={`px-2.5 py-1 rounded transition-colors ${
                environment === 'live'
                  ? 'bg-red-950/80 text-red-300 font-bold border border-red-700'
                  : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              LIVE
            </button>
          </div>

          {/* Trading Mode Badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-neutral-900 border border-neutral-800 text-xs font-mono">
            <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span className="text-neutral-400 text-[10px]">MODE:</span>
            <span className="text-neutral-200 font-semibold uppercase">{tradingMode}</span>
          </div>

          {/* System Status Badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-neutral-900 border border-neutral-800 text-xs font-mono">
            <Activity
              className={`w-3.5 h-3.5 ${
                systemStatus === 'ONLINE' ? 'text-emerald-400' : 'text-red-400'
              }`}
            />
            <span className="text-neutral-400 text-[10px]">STATUS:</span>
            <span
              className={`font-semibold ${
                systemStatus === 'ONLINE' ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {systemStatus}
            </span>
          </div>

          {/* Emergency Kill Switch Button */}
          <button
            onClick={onToggleKillSwitch}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all border shadow-sm ${
              killSwitchActive
                ? 'bg-red-600 hover:bg-red-500 text-white border-red-400 animate-pulse'
                : 'bg-red-950/60 hover:bg-red-900/60 text-red-300 border-red-800/80 hover:border-red-600'
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            <span>{killSwitchActive ? 'HALT ENGAGED' : 'KILL SWITCH'}</span>
          </button>
        </div>
      </div>

      {/* Metrics Header Bar */}
      <div className="bg-neutral-900/90 border-t border-neutral-800/80 px-4 py-2">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-6 font-mono">
            <div className="flex items-center gap-2">
              <span className="text-neutral-400">Total Equity:</span>
              <span className="text-neutral-100 font-bold text-sm">
                ${equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-neutral-400">Daily P/L:</span>
              <span
                className={`font-semibold flex items-center gap-0.5 ${
                  dailyPnl >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                <TrendingUp className="w-3.5 h-3.5" />
                {dailyPnl >= 0 ? '+' : ''}${dailyPnl.toFixed(2)} ({dailyPnlPct >= 0 ? '+' : ''}
                {dailyPnlPct.toFixed(2)}%)
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-neutral-400">Risk Used:</span>
              <span className="text-neutral-300 font-medium">0.25% / 1.00% max</span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-neutral-400">Daily Loss Guard:</span>
              <span className="text-emerald-400 font-medium">0.00% / 2.00%</span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-neutral-400">Consecutive Losses:</span>
              <span className="text-neutral-300 font-medium">0 / 3</span>
            </div>
          </div>

          <div className="flex items-center gap-3 font-mono text-[11px] text-neutral-400">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              WebSocket Feed: OK (12ms)
            </span>
            <span>•</span>
            <span>REST Fallback: Ready</span>
            <span>•</span>
            <span className="text-neutral-300">Sessions: London Killzone Active</span>
          </div>
        </div>
      </div>
    </header>
  );
};
