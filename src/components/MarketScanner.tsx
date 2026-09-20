import React from 'react';
import { ScannerRow } from '../types';
import { CheckCircle2, XCircle, ArrowUpRight, ArrowDownRight, Eye } from 'lucide-react';

interface MarketScannerProps {
  rows: ScannerRow[];
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
}

export const MarketScanner: React.FC<MarketScannerProps> = ({
  rows,
  selectedSymbol,
  onSelectSymbol,
}) => {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-neutral-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-bold text-neutral-100 uppercase tracking-wide font-mono">
            Multi-Timeframe Market Scanner
          </h2>
          <span className="text-[10px] px-2 py-0.5 rounded bg-neutral-800 text-neutral-400 font-mono">
            HTF: 4H • Structure: 15M • Entry: 5M
          </span>
        </div>
        <div className="text-xs text-neutral-400 font-mono">
          Scanning Universe: <span className="text-neutral-200">BTC, ETH, SOL</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-neutral-950/80 border-b border-neutral-800 text-neutral-400 uppercase text-[10px] tracking-wider">
            <tr>
              <th className="px-4 py-2.5">Symbol</th>
              <th className="px-3 py-2.5 text-right">Price</th>
              <th className="px-3 py-2.5">HTF Bias</th>
              <th className="px-3 py-2.5">Structure</th>
              <th className="px-3 py-2.5">Liquidity Event</th>
              <th className="px-2 py-2.5 text-center">FVG</th>
              <th className="px-2 py-2.5 text-center">OB</th>
              <th className="px-3 py-2.5">Dealing Zone</th>
              <th className="px-3 py-2.5">Session</th>
              <th className="px-3 py-2.5 text-right">R:R</th>
              <th className="px-3 py-2.5 text-center">Score</th>
              <th className="px-3 py-2.5 text-center">Status</th>
              <th className="px-3 py-2.5 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-800/60">
            {rows.map((row) => {
              const isSelected = row.symbol === selectedSymbol;
              return (
                <tr
                  key={row.symbol}
                  onClick={() => onSelectSymbol(row.symbol)}
                  className={`cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-neutral-800/80 border-l-2 border-l-emerald-400'
                      : 'hover:bg-neutral-850/60'
                  }`}
                >
                  <td className="px-4 py-3 font-bold text-neutral-100 flex items-center gap-1.5">
                    {row.symbol}
                    {row.change24h >= 0 ? (
                      <span className="text-emerald-400 text-[10px] flex items-center">
                        <ArrowUpRight className="w-3 h-3" />+{row.change24h}%
                      </span>
                    ) : (
                      <span className="text-red-400 text-[10px] flex items-center">
                        <ArrowDownRight className="w-3 h-3" />
                        {row.change24h}%
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-3 text-right font-semibold text-neutral-200">
                    ${row.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-3 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        row.htfBias === 'BULLISH'
                          ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/30'
                          : row.htfBias === 'BEARISH'
                          ? 'bg-red-950/60 text-red-400 border border-red-500/30'
                          : 'bg-neutral-800 text-neutral-400'
                      }`}
                    >
                      {row.htfBias}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-neutral-200 font-semibold">{row.structure}</td>
                  <td className="px-3 py-3 text-neutral-300">{row.liquidity}</td>
                  <td className="px-2 py-3 text-center">
                    {row.fvg ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto" />
                    ) : (
                      <XCircle className="w-4 h-4 text-neutral-600 mx-auto" />
                    )}
                  </td>
                  <td className="px-2 py-3 text-center">
                    {row.orderBlock ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto" />
                    ) : (
                      <XCircle className="w-4 h-4 text-neutral-600 mx-auto" />
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] ${
                        row.pdZone === 'DISCOUNT'
                          ? 'bg-emerald-950/70 text-emerald-300 border border-emerald-500/40'
                          : row.pdZone === 'PREMIUM'
                          ? 'bg-red-950/70 text-red-300 border border-red-500/40'
                          : 'bg-neutral-800 text-neutral-300'
                      }`}
                    >
                      {row.pdZone}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-neutral-400">{row.session}</td>
                  <td className="px-3 py-3 text-right font-bold text-neutral-100">
                    {row.rr.toFixed(2)}R
                  </td>
                  <td className="px-3 py-3 text-center">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        row.score >= 8.5
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/50'
                          : row.score >= 7.0
                          ? 'bg-amber-950 text-amber-300 border border-amber-500/50'
                          : 'bg-neutral-800 text-neutral-400'
                      }`}
                    >
                      {row.score.toFixed(1)}/10
                    </span>
                  </td>
                  <td className="px-3 py-3 text-center">
                    <span
                      className={`px-2.5 py-1 rounded text-[10px] font-bold tracking-wider uppercase ${
                        row.status === 'ARMED'
                          ? 'bg-emerald-600 text-white animate-pulse'
                          : row.status === 'WATCHING'
                          ? 'bg-neutral-800 text-neutral-300'
                          : 'bg-red-900/60 text-red-300'
                      }`}
                    >
                      {row.status}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectSymbol(row.symbol);
                      }}
                      className="p-1 rounded bg-neutral-800 hover:bg-neutral-700 text-neutral-300 hover:text-white transition-colors"
                      title="Inspect Structure & Setup"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
