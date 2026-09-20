import React, { useState } from 'react';
import { CandleData, FVGOverlay, OrderBlockOverlay } from '../types';
import { Layers } from 'lucide-react';

interface ChartViewProps {
  symbol: string;
  candles: CandleData[];
  fvgs: FVGOverlay[];
  orderBlocks: OrderBlockOverlay[];
}

export const ChartView: React.FC<ChartViewProps> = ({
  symbol,
  candles,
  fvgs,
  orderBlocks,
}) => {
  // Layer toggle states
  const [showSwings, setShowSwings] = useState(true);
  const [showBOS, setShowBOS] = useState(true);
  const [showFVG, setShowFVG] = useState(true);
  const [showOB, setShowOB] = useState(true);
  const [showEquilibrium, setShowEquilibrium] = useState(true);
  const [timeframe, setTimeframe] = useState<'15m' | '5m' | '4h'>('15m');
  const [hoveredCandle, setHoveredCandle] = useState<CandleData | null>(null);

  // Compute robust SVG scaling coordinates
  const prices = candles.flatMap((c) => [c.high, c.low]).filter((p) => typeof p === 'number' && !isNaN(p) && p > 0);
  const lastPrice = candles.length > 0 ? candles[candles.length - 1].close : 0;
  
  const rawMin = prices.length > 0 ? Math.min(...prices) : 100;
  const rawMax = prices.length > 0 ? Math.max(...prices) : 200;
  const priceSpread = rawMax - rawMin || 10;
  
  // Dynamic 15% top & bottom buffer proportional to price spread
  const buffer = Math.max(priceSpread * 0.15, rawMax * 0.001);
  const minPrice = rawMin - buffer;
  const maxPrice = rawMax + buffer;
  const priceRange = maxPrice - minPrice || 1;

  const chartHeight = 340;
  const chartWidth = 720;
  const candleSpacing = chartWidth / Math.max(candles.length, 1);
  const candleWidth = Math.max(Math.min(candleSpacing * 0.65, 28), 8);

  const getY = (price: number) => {
    const y = chartHeight - ((price - minPrice) / priceRange) * chartHeight;
    return Math.max(-20, Math.min(chartHeight + 20, y));
  };

  const equilibriumPrice = (minPrice + maxPrice) / 2.0;

  // Filter overlays to only those within a reasonable boundary of the current chart scale
  const visibleFVGs = fvgs.filter(
    (f) => f.top >= minPrice - buffer * 2 && f.bottom <= maxPrice + buffer * 2
  );
  const visibleOBs = orderBlocks.filter(
    (ob) => ob.top >= minPrice - buffer * 2 && ob.bottom <= maxPrice + buffer * 2
  );

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden flex flex-col shadow-sm">
      {/* Chart Top Bar & Controls */}
      <div className="px-4 py-2.5 border-b border-neutral-800 flex flex-wrap items-center justify-between gap-3 bg-neutral-950/80">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm text-neutral-100 font-mono tracking-tight">{symbol}</span>
            <span className="text-xs px-2 py-0.5 rounded bg-neutral-800/90 text-emerald-400 font-mono font-semibold border border-neutral-700/50">
              ${lastPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>

          <div className="flex items-center bg-neutral-900 border border-neutral-800 rounded text-xs font-mono p-0.5">
            {(['4h', '15m', '5m'] as const).map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-2.5 py-0.5 rounded uppercase font-medium transition-colors ${
                  timeframe === tf
                    ? 'bg-neutral-800 text-white font-bold shadow-xs'
                    : 'text-neutral-400 hover:text-neutral-200'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>

          {hoveredCandle && (
            <div className="hidden md:flex items-center gap-2 text-[10px] font-mono text-neutral-400 pl-2 border-l border-neutral-800">
              <span>O: <span className="text-neutral-200">{hoveredCandle.open.toFixed(2)}</span></span>
              <span>H: <span className="text-neutral-200">{hoveredCandle.high.toFixed(2)}</span></span>
              <span>L: <span className="text-neutral-200">{hoveredCandle.low.toFixed(2)}</span></span>
              <span>C: <span className={hoveredCandle.close >= hoveredCandle.open ? 'text-emerald-400' : 'text-red-400'}>{hoveredCandle.close.toFixed(2)}</span></span>
            </div>
          )}
        </div>

        {/* Layer Visibility Toggles */}
        <div className="flex items-center gap-1.5 text-xs font-mono">
          <span className="text-neutral-400 text-[11px] mr-1 flex items-center gap-1">
            <Layers className="w-3 h-3 text-neutral-400" /> Layers:
          </span>

          <button
            onClick={() => setShowSwings(!showSwings)}
            className={`px-2 py-0.5 rounded border text-[10px] transition-colors ${
              showSwings
                ? 'bg-amber-950/40 border-amber-500/40 text-amber-300'
                : 'bg-neutral-950 border-neutral-800 text-neutral-500'
            }`}
          >
            Swings (H/L)
          </button>

          <button
            onClick={() => setShowBOS(!showBOS)}
            className={`px-2 py-0.5 rounded border text-[10px] transition-colors ${
              showBOS
                ? 'bg-sky-950/40 border-sky-500/40 text-sky-300'
                : 'bg-neutral-950 border-neutral-800 text-neutral-500'
            }`}
          >
            MSS / BOS
          </button>

          <button
            onClick={() => setShowFVG(!showFVG)}
            className={`px-2 py-0.5 rounded border text-[10px] transition-colors ${
              showFVG
                ? 'bg-emerald-950/60 border-emerald-500/50 text-emerald-300'
                : 'bg-neutral-950 border-neutral-800 text-neutral-500'
            }`}
          >
            50% FVG
          </button>

          <button
            onClick={() => setShowOB(!showOB)}
            className={`px-2 py-0.5 rounded border text-[10px] transition-colors ${
              showOB
                ? 'bg-purple-950/60 border-purple-500/50 text-purple-300'
                : 'bg-neutral-950 border-neutral-800 text-neutral-500'
            }`}
          >
            Order Block
          </button>

          <button
            onClick={() => setShowEquilibrium(!showEquilibrium)}
            className={`px-2 py-0.5 rounded border text-[10px] transition-colors ${
              showEquilibrium
                ? 'bg-neutral-800 border-neutral-700 text-neutral-200'
                : 'bg-neutral-950 border-neutral-800 text-neutral-500'
            }`}
          >
            Equilibrium (50%)
          </button>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div className="relative p-3 bg-neutral-950 flex justify-center overflow-hidden">
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          className="w-full h-[340px] select-none"
        >
          <defs>
            {/* Viewport clip to prevent any overlay from overflowing */}
            <clipPath id="chart-viewport">
              <rect x="0" y="0" width={chartWidth} height={chartHeight} rx="4" />
            </clipPath>
          </defs>

          {/* Background Grid Lines & Y-axis Labels */}
          {[0.15, 0.35, 0.55, 0.75, 0.9].map((ratio) => {
            const y = chartHeight * ratio;
            const priceVal = maxPrice - (chartHeight * ratio * priceRange) / chartHeight;
            return (
              <g key={ratio}>
                <line
                  x1="0"
                  y1={y}
                  x2={chartWidth - 55}
                  y2={y}
                  stroke="#262626"
                  strokeWidth="1"
                  strokeDasharray="2 4"
                />
                <text
                  x={chartWidth - 50}
                  y={y + 3}
                  fill="#737373"
                  fontSize="9"
                  fontFamily="monospace"
                >
                  ${priceVal.toFixed(1)}
                </text>
              </g>
            );
          })}

          <g clipPath="url(#chart-viewport)">
            {/* Equilibrium 50% Line */}
            {showEquilibrium && (
              <g>
                <line
                  x1="0"
                  y1={getY(equilibriumPrice)}
                  x2={chartWidth}
                  y2={getY(equilibriumPrice)}
                  stroke="#525252"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                />
                <text
                  x="12"
                  y={getY(equilibriumPrice) - 5}
                  fill="#a3a3a3"
                  fontSize="9"
                  fontFamily="monospace"
                  fontWeight="bold"
                >
                  EQUILIBRIUM (50%) — ${equilibriumPrice.toFixed(1)}
                </text>
              </g>
            )}

            {/* Order Block Overlay Box */}
            {showOB &&
              visibleOBs.map((ob, idx) => {
                const startX = Math.max(0, ob.startIndex * candleSpacing);
                const endX = chartWidth;
                const y1 = getY(ob.top);
                const y2 = getY(ob.bottom);
                const topY = Math.min(y1, y2);
                const height = Math.max(Math.abs(y1 - y2), 4);

                return (
                  <g key={`ob-${idx}`}>
                    <rect
                      x={startX}
                      y={topY}
                      width={endX - startX}
                      height={height}
                      fill="#a855f7"
                      fillOpacity="0.18"
                      stroke="#a855f7"
                      strokeWidth="1"
                      strokeDasharray="3 3"
                    />
                    <text
                      x={startX + 6}
                      y={topY + 12}
                      fill="#d8b4fe"
                      fontSize="9"
                      fontFamily="monospace"
                      fontWeight="bold"
                    >
                      {timeframe.toUpperCase()} Bullish OB (Score: {ob.score.toFixed(1)})
                    </text>
                  </g>
                );
              })}

            {/* Fair Value Gap (FVG) Overlay Box */}
            {showFVG &&
              visibleFVGs.map((fvg, idx) => {
                const startX = Math.max(0, fvg.startIndex * candleSpacing);
                const endX = chartWidth;
                const y1 = getY(fvg.top);
                const y2 = getY(fvg.bottom);
                const topY = Math.min(y1, y2);
                const height = Math.max(Math.abs(y1 - y2), 4);
                const yMid = getY(fvg.midpoint);

                return (
                  <g key={`fvg-${idx}`}>
                    <rect
                      x={startX}
                      y={topY}
                      width={endX - startX}
                      height={height}
                      fill="#10b981"
                      fillOpacity="0.16"
                      stroke="#10b981"
                      strokeWidth="1.2"
                    />
                    {/* 50% Consequent Encroachment (CE) Midpoint line */}
                    <line
                      x1={startX}
                      y1={yMid}
                      x2={endX}
                      y2={yMid}
                      stroke="#34d399"
                      strokeWidth="1.5"
                      strokeDasharray="4 3"
                    />
                    <text
                      x={startX + 8}
                      y={yMid - 4}
                      fill="#6ee7b7"
                      fontSize="9"
                      fontFamily="monospace"
                      fontWeight="bold"
                    >
                      FVG CE 50% — ${fvg.midpoint.toFixed(1)}
                    </text>
                  </g>
                );
              })}

            {/* Candlesticks Rendering */}
            {candles.map((c, i) => {
              const x = i * candleSpacing + candleSpacing / 2;
              const yHigh = getY(c.high);
              const yLow = getY(c.low);
              const yOpen = getY(c.open);
              const yClose = getY(c.close);
              const isBullish = c.close >= c.open;
              const strokeColor = isBullish ? '#22c55e' : '#ef4444';
              const fillColor = isBullish ? '#15803d' : '#991b1b';
              const bodyTop = Math.min(yOpen, yClose);
              const bodyHeight = Math.max(Math.abs(yOpen - yClose), 2.5);

              return (
                <g
                  key={c.index ?? i}
                  className="cursor-pointer group"
                  onMouseEnter={() => setHoveredCandle(c)}
                  onMouseLeave={() => setHoveredCandle(null)}
                >
                  {/* Candlestick Wick */}
                  <line
                    x1={x}
                    y1={yHigh}
                    x2={x}
                    y2={yLow}
                    stroke={strokeColor}
                    strokeWidth="1.5"
                  />
                  {/* Candlestick Body */}
                  <rect
                    x={x - candleWidth / 2}
                    y={bodyTop}
                    width={candleWidth}
                    height={bodyHeight}
                    fill={fillColor}
                    stroke={strokeColor}
                    strokeWidth="1.2"
                    rx="1"
                  />

                  {/* Swing High Label */}
                  {showSwings && c.isSwingHigh && (
                    <g>
                      <polygon
                        points={`${x},${yHigh - 4} ${x - 4},${yHigh - 11} ${x + 4},${yHigh - 11}`}
                        fill="#f59e0b"
                      />
                      <text
                        x={x}
                        y={yHigh - 14}
                        textAnchor="middle"
                        fill="#fbbf24"
                        fontSize="9"
                        fontFamily="monospace"
                        fontWeight="bold"
                      >
                        SH ${c.high.toFixed(1)}
                      </text>
                    </g>
                  )}

                  {/* Swing Low / Sweep Label */}
                  {showSwings && c.isSwingLow && (
                    <g>
                      <polygon
                        points={`${x},${yLow + 4} ${x - 4},${yLow + 11} ${x + 4},${yLow + 11}`}
                        fill="#f59e0b"
                      />
                      <text
                        x={x}
                        y={yLow + 22}
                        textAnchor="middle"
                        fill="#fbbf24"
                        fontSize="9"
                        fontFamily="monospace"
                        fontWeight="bold"
                      >
                        SSL SWEEP ${c.low.toFixed(1)}
                      </text>
                    </g>
                  )}

                  {/* MSS Market Structure Shift Label */}
                  {showBOS && c.mss && (
                    <g>
                      <text
                        x={x}
                        y={Math.min(bodyTop - 8, yHigh - 8)}
                        textAnchor="middle"
                        fill="#38bdf8"
                        fontSize="9"
                        fontFamily="monospace"
                        fontWeight="bold"
                      >
                        MSS ↑
                      </text>
                    </g>
                  )}
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {/* Footer Info */}
      <div className="px-4 py-2 border-t border-neutral-800 bg-neutral-950/80 flex flex-wrap items-center justify-between text-[11px] font-mono text-neutral-400">
        <div>
          Dealing Range: <span className="text-emerald-400 font-semibold font-mono">DISCOUNT ZONE</span>{' '}
          (Optimal for Long Setups)
        </div>
        <div className="flex items-center gap-4">
          <span>Timeframe: <span className="text-neutral-200">{timeframe}</span></span>
          <span>Bars: <span className="text-neutral-200">{candles.length}</span></span>
          <span>Range: <span className="text-neutral-200">${rawMin.toFixed(1)} - ${rawMax.toFixed(1)}</span></span>
          {visibleFVGs.length > 0 && (
            <span className="text-emerald-400 font-bold">
              Key FVG 50% CE: ${visibleFVGs[0].midpoint.toFixed(2)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
