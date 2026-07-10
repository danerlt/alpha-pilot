/* @ds-bundle: {"format":4,"namespace":"AlphaPilotDesignSystem_13e693","components":[],"sourceHashes":{"ui_kits/mobile_app/components/atoms.jsx":"58cfd15c0460","ui_kits/mobile_app/components/screens.jsx":"626ab4970e38","ui_kits/mobile_app/ios-frame.jsx":"d67eb3ffe562","ui_kits/web_app/components/admin.jsx":"deff30f38beb","ui_kits/web_app/components/ai_card.jsx":"7ab19847a62b","ui_kits/web_app/components/ai_chat.jsx":"5677a21b6571","ui_kits/web_app/components/auth.jsx":"a9d62e830013","ui_kits/web_app/components/enhancements.jsx":"b8f269f26ec0","ui_kits/web_app/components/lab.jsx":"b57a1f4a45b7","ui_kits/web_app/components/market.jsx":"a4940dd0e910","ui_kits/web_app/components/pages.jsx":"abf155872602","ui_kits/web_app/components/settings.jsx":"17289360f390","ui_kits/web_app/components/shell.jsx":"8fee449781b3","ui_kits/web_app/components/trade_panel.jsx":"1fedddddcaa7"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.AlphaPilotDesignSystem_13e693 = window.AlphaPilotDesignSystem_13e693 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// ui_kits/mobile_app/components/atoms.jsx
try { (() => {
// AlphaPilot mobile components — all screens built with AP design tokens
// Global state + mock data

const MOCK = {
  equity: 128450.73,
  equityChangePct: 1.82,
  equityChange: 2291.40,
  todayPnl: 1248.05,
  todayPnlPct: 0.98,
  positionsPct: 12,
  dayLossPct: -0.48,
  riskState: 'OK',
  // OK | WARN | HALTED
  tradesToday: 7,
  winRate: 57,
  regime: 'trending_up',
  positions: [{
    sym: 'BTCUSDT',
    qty: 0.048,
    entry: 67420.50,
    mark: 68863.92,
    pnl: 69.29,
    pnlPct: 2.14
  }, {
    sym: 'ETHUSDT',
    qty: 0.82,
    entry: 3240.00,
    mark: 3219.92,
    pnl: -16.47,
    pnlPct: -0.62
  }],
  decisions: [{
    t: '14:23:08',
    sym: 'BTCUSDT',
    tf: '15m',
    action: 'OPEN_LONG',
    conf: 0.78,
    strat: '趋势跟随',
    sl: 64210,
    tp: 68900,
    size: '2.5%',
    guard: 'PASS',
    reason: 'EMA20>EMA50>EMA200 金叉排列，1h 成交量较均值放大 1.4x，回踩 EMA20 未破，确认突破有效。',
    entry: 67420.50
  }, {
    t: '13:45:00',
    sym: 'ETHUSDT',
    tf: '15m',
    action: 'HOLD',
    conf: 0.42,
    strat: '观望模式',
    guard: 'DEGRADE',
    reason: '波动率进入高位，regime 由 trending_up 切换为 chaotic，降级为观望。'
  }, {
    t: '12:30:00',
    sym: 'BTCUSDT',
    tf: '15m',
    action: 'OPEN_LONG',
    conf: 0.71,
    strat: '突破确认',
    guard: 'REJECT',
    reason: '触发风险收益比 <1.5 检查，守卫拒绝，回退 HOLD。'
  }, {
    t: '10:15:00',
    sym: 'BTCUSDT',
    tf: '15m',
    action: 'CLOSE_LONG',
    conf: 0.85,
    strat: '止盈执行',
    guard: 'PASS',
    reason: '达到 TP 价位，执行平仓，本笔 +1.82%。',
    entry: 66100
  }],
  logs: [{
    t: '14:23:09',
    type: 'fill',
    msg: 'BTCUSDT 市价成交 0.048 @ 67,420.50',
    color: 'mint'
  }, {
    t: '14:23:09',
    type: 'order',
    msg: '止损挂单 64,210.00 · 止盈 68,900.00',
    color: 'fg'
  }, {
    t: '14:23:08',
    type: 'guard',
    msg: '守卫通过 PASS · 检查 8/8',
    color: 'mint'
  }, {
    t: '14:23:08',
    type: 'ai',
    msg: 'AI 决策 OPEN_LONG · 置信度 0.78',
    color: 'violet'
  }, {
    t: '13:45:05',
    type: 'guard',
    msg: '守卫降级 DEGRADE · regime 异常',
    color: 'amber'
  }, {
    t: '12:30:12',
    type: 'guard',
    msg: '守卫拒绝 REJECT · RR<1.5 · 回退 HOLD',
    color: 'rose'
  }, {
    t: '10:15:30',
    type: 'fill',
    msg: 'BTCUSDT 平仓 @ 68,903.20 · +1.82%',
    color: 'mint'
  }]
};

// --- atoms ---
const Pill = ({
  children,
  tone = 'default',
  mono = true
}) => {
  const tones = {
    mint: {
      bg: 'var(--ap-mint-soft)',
      c: 'var(--ap-mint)'
    },
    rose: {
      bg: 'var(--ap-rose-soft)',
      c: 'var(--ap-rose)'
    },
    amber: {
      bg: 'var(--ap-amber-soft)',
      c: 'var(--ap-amber)'
    },
    violet: {
      bg: 'var(--ap-violet-soft)',
      c: 'var(--ap-violet)'
    },
    cyan: {
      bg: 'var(--ap-cyan-soft)',
      c: 'var(--ap-cyan)'
    },
    default: {
      bg: 'var(--ap-bg-3)',
      c: 'var(--ap-fg-2)'
    }
  };
  const s = tones[tone] || tones.default;
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 4,
      fontSize: 10,
      padding: '2px 8px',
      borderRadius: 999,
      background: s.bg,
      color: s.c,
      fontWeight: 600,
      fontFamily: mono ? 'var(--ap-font-mono)' : 'inherit',
      letterSpacing: '.02em'
    }
  }, children);
};
const Dot = ({
  c,
  glow
}) => /*#__PURE__*/React.createElement("span", {
  style: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    background: c,
    boxShadow: glow ? `0 0 6px ${c}` : 'none',
    display: 'inline-block'
  }
});
const Card = ({
  children,
  style,
  glow
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    background: 'var(--ap-bg-2)',
    borderRadius: 16,
    padding: 16,
    border: '1px solid var(--ap-line-soft)',
    ...(glow ? {
      borderColor: 'var(--ap-violet)',
      boxShadow: '0 0 24px rgba(124,92,255,.15)'
    } : {}),
    ...style
  }
}, children);
const Num = ({
  v,
  prefix = '',
  suffix = '',
  positive,
  negative,
  size = 14,
  weight = 600
}) => {
  const c = positive ? 'var(--ap-mint)' : negative ? 'var(--ap-rose)' : 'var(--ap-fg-1)';
  return /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontVariantNumeric: 'tabular-nums',
      fontSize: size,
      fontWeight: weight,
      color: c,
      letterSpacing: '-.01em'
    }
  }, prefix, v, suffix);
};
const fmt = (n, d = 2) => n.toLocaleString('en-US', {
  minimumFractionDigits: d,
  maximumFractionDigits: d
});
const fmtPct = n => (n >= 0 ? '+' : '') + n.toFixed(2) + '%';
const fmtSigned = n => (n >= 0 ? '+' : '−') + '$' + Math.abs(n).toLocaleString('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});

// --- Top bar: risk status (always-present) ---
const TopRiskBar = ({
  state = 'OK',
  regime,
  loss,
  positions
}) => {
  const cfg = {
    OK: {
      c: 'var(--ap-mint)',
      bg: 'rgba(0,211,149,.08)',
      label: '风控正常'
    },
    WARN: {
      c: 'var(--ap-amber)',
      bg: 'rgba(240,185,11,.10)',
      label: '接近阈值'
    },
    HALTED: {
      c: 'var(--ap-rose)',
      bg: 'rgba(255,77,109,.12)',
      label: '已熔断'
    }
  }[state];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: cfg.bg,
      backdropFilter: 'blur(20px)',
      padding: '8px 16px',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      borderBottom: '1px solid var(--ap-line-soft)'
    }
  }, /*#__PURE__*/React.createElement(Dot, {
    c: cfg.c,
    glow: true
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: cfg.c
    }
  }, cfg.label), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "\xB7 \u4ED3\u4F4D ", positions, "% \xB7 \u65E5\u635F ", fmtPct(loss)), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      fontSize: 10,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, regime));
};

// --- Header ---
const AppHeader = ({
  title,
  right,
  sub
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    padding: '16px 16px 10px',
    display: 'flex',
    alignItems: 'flex-end',
    justifyContent: 'space-between'
  }
}, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 11,
    color: 'var(--ap-fg-3)',
    letterSpacing: '.08em',
    textTransform: 'uppercase',
    marginBottom: 2
  }
}, sub), /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 26,
    fontWeight: 700,
    letterSpacing: '-.02em'
  }
}, title)), right);

// --- Stat tile ---
const StatTile = ({
  label,
  value,
  sub,
  tone
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    background: 'var(--ap-bg-2)',
    borderRadius: 14,
    padding: '12px 14px',
    display: 'flex',
    flexDirection: 'column',
    gap: 3,
    border: '1px solid var(--ap-line-soft)'
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 10,
    color: 'var(--ap-fg-3)',
    letterSpacing: '.05em',
    textTransform: 'uppercase'
  }
}, label), /*#__PURE__*/React.createElement("div", {
  style: {
    fontFamily: 'var(--ap-font-mono)',
    fontSize: 19,
    fontWeight: 700,
    letterSpacing: '-.02em',
    color: tone === 'pos' ? 'var(--ap-mint)' : tone === 'neg' ? 'var(--ap-rose)' : 'var(--ap-fg-1)'
  }
}, value), sub && /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 11,
    color: 'var(--ap-fg-3)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, sub));

// --- PnL sparkline (inline SVG) ---
const Sparkline = ({
  data,
  w = 348,
  h = 88,
  color = 'var(--ap-mint)'
}) => {
  const min = Math.min(...data),
    max = Math.max(...data),
    r = max - min || 1;
  const pts = data.map((v, i) => [i / (data.length - 1) * w, h - (v - min) / r * (h - 8) - 4]);
  const path = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
  const area = path + ` L ${w} ${h} L 0 ${h} Z`;
  return /*#__PURE__*/React.createElement("svg", {
    width: w,
    height: h,
    style: {
      display: 'block'
    }
  }, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("linearGradient", {
    id: "spark-grad",
    x1: "0",
    x2: "0",
    y1: "0",
    y2: "1"
  }, /*#__PURE__*/React.createElement("stop", {
    offset: "0",
    stopColor: color,
    stopOpacity: ".3"
  }), /*#__PURE__*/React.createElement("stop", {
    offset: "1",
    stopColor: color,
    stopOpacity: "0"
  }))), /*#__PURE__*/React.createElement("path", {
    d: area,
    fill: "url(#spark-grad)"
  }), /*#__PURE__*/React.createElement("path", {
    d: path,
    stroke: color,
    strokeWidth: "1.8",
    fill: "none",
    strokeLinejoin: "round"
  }));
};

// --- Decision pipeline (horizontal stepper) ---
const DecisionStepper = ({
  ai = 'done',
  guard = 'done',
  exec = 'done',
  guardState = 'PASS'
}) => {
  const step = (label, state, idx) => {
    const colors = state === 'done' ? {
      dot: 'var(--ap-mint)',
      txt: 'var(--ap-fg-1)'
    } : state === 'active' ? {
      dot: 'var(--ap-violet)',
      txt: 'var(--ap-violet)'
    } : {
      dot: 'var(--ap-bg-4)',
      txt: 'var(--ap-fg-4)'
    };
    return /*#__PURE__*/React.createElement("div", {
      key: idx,
      style: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 6,
        flexShrink: 0,
        width: 54
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        width: 22,
        height: 22,
        borderRadius: '50%',
        background: colors.dot,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 11,
        color: 'var(--ap-bg-0)',
        fontWeight: 700,
        lineHeight: 1
      }
    }, state === 'done' ? '✓' : idx + 1), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        color: colors.txt,
        fontWeight: 600,
        whiteSpace: 'nowrap'
      }
    }, label));
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-start',
      gap: 0,
      padding: '8px 0'
    }
  }, step('AI', ai, 0), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      height: 2,
      background: 'var(--ap-mint)',
      marginTop: 10
    }
  }), step('守卫', guard, 1), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      height: 2,
      background: 'var(--ap-mint)',
      marginTop: 10
    }
  }), step('执行', exec, 2));
};

// --- AI Decision Card (hero) ---
const AIDecisionCard = ({
  d
}) => {
  const actionColor = d.action === 'OPEN_LONG' ? 'var(--ap-mint)' : d.action === 'CLOSE_LONG' ? 'var(--ap-rose)' : 'var(--ap-fg-2)';
  const guardTone = d.guard === 'PASS' ? 'mint' : d.guard === 'REJECT' ? 'rose' : 'amber';
  return /*#__PURE__*/React.createElement(Card, {
    glow: true
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 10,
      color: 'var(--ap-violet)',
      fontWeight: 700,
      letterSpacing: '.08em'
    }
  }, /*#__PURE__*/React.createElement(Dot, {
    c: "var(--ap-violet)",
    glow: true
  }), " AI DECISION"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, d.sym, " \xB7 ", d.tf, " \xB7 ", d.t)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 10,
      marginBottom: 4
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 24,
      fontWeight: 700,
      color: actionColor,
      letterSpacing: '.02em'
    }
  }, d.action), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "confidence ", d.conf?.toFixed(2))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-2)',
      marginBottom: 12
    }
  }, d.strat), d.sl && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(4,1fr)',
      gap: 8,
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11,
      padding: '10px 0',
      borderTop: '1px solid var(--ap-line-soft)',
      borderBottom: '1px solid var(--ap-line-soft)',
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      color: 'var(--ap-fg-3)',
      fontSize: 9,
      letterSpacing: '.05em'
    }
  }, "ENTRY"), /*#__PURE__*/React.createElement("div", null, fmt(d.entry))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      color: 'var(--ap-fg-3)',
      fontSize: 9,
      letterSpacing: '.05em'
    }
  }, "SIZE"), /*#__PURE__*/React.createElement("div", null, d.size)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      color: 'var(--ap-fg-3)',
      fontSize: 9,
      letterSpacing: '.05em'
    }
  }, "SL"), /*#__PURE__*/React.createElement("div", {
    style: {
      color: 'var(--ap-rose)'
    }
  }, fmt(d.sl))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      color: 'var(--ap-fg-3)',
      fontSize: 9,
      letterSpacing: '.05em'
    }
  }, "TP"), /*#__PURE__*/React.createElement("div", {
    style: {
      color: 'var(--ap-mint)'
    }
  }, fmt(d.tp)))), /*#__PURE__*/React.createElement(DecisionStepper, null), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-2)',
      lineHeight: 1.55,
      marginTop: 10,
      padding: '10px 12px',
      background: 'var(--ap-bg-3)',
      borderRadius: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-3)',
      marginBottom: 4,
      letterSpacing: '.05em'
    }
  }, "REASONING"), d.reason), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 10,
      display: 'flex',
      gap: 8,
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement(Pill, {
    tone: guardTone
  }, "\u5B88\u536B ", d.guard), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      fontSize: 11,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "trace \xB7 7f3a9b2c")));
};

// --- Position Row ---
const PositionRow = ({
  p,
  onClick
}) => {
  const isUp = p.pnlPct >= 0;
  const coinBg = p.sym.startsWith('BTC') ? 'linear-gradient(135deg,#F7931A,#8B4E0D)' : p.sym.startsWith('ETH') ? 'linear-gradient(135deg,#627EEA,#3C54BD)' : 'linear-gradient(135deg,#9945FF,#14F195)';
  const glyph = p.sym.startsWith('BTC') ? '₿' : p.sym.startsWith('ETH') ? 'Ξ' : '◎';
  return /*#__PURE__*/React.createElement("div", {
    onClick: onClick,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '12px 14px',
      background: 'var(--ap-bg-2)',
      borderRadius: 14,
      border: '1px solid var(--ap-line-soft)',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 36,
      height: 36,
      borderRadius: '50%',
      background: coinBg,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#fff',
      fontSize: 16,
      fontWeight: 700,
      flexShrink: 0
    }
  }, glyph), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 600
    }
  }, p.sym), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, p.qty, " \xB7 entry ", fmt(p.entry))), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'right'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 14,
      fontWeight: 600
    }
  }, "$", fmt(p.mark)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11,
      color: isUp ? 'var(--ap-mint)' : 'var(--ap-rose)'
    }
  }, fmtPct(p.pnlPct), " \xB7 ", fmtSigned(p.pnl))));
};

// --- Log Row ---
const LogRow = ({
  l
}) => {
  const colorMap = {
    mint: 'var(--ap-mint)',
    rose: 'var(--ap-rose)',
    amber: 'var(--ap-amber)',
    violet: 'var(--ap-violet)',
    fg: 'var(--ap-fg-2)'
  };
  const c = colorMap[l.color];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 10,
      padding: '10px 0',
      borderBottom: '1px solid var(--ap-line-soft)'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 10,
      color: 'var(--ap-fg-3)',
      minWidth: 58,
      flexShrink: 0,
      paddingTop: 2
    }
  }, l.t), /*#__PURE__*/React.createElement(Dot, {
    c: c,
    glow: l.color === 'violet' || l.color === 'rose'
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-1)',
      flex: 1,
      lineHeight: 1.5
    }
  }, l.msg));
};

// --- Tab Bar ---
const TabBar = ({
  active,
  onChange
}) => {
  const tabs = [{
    id: 'home',
    label: '仪表盘',
    icon: '◎'
  }, {
    id: 'ai',
    label: 'AI 决策',
    icon: '✦'
  }, {
    id: 'pos',
    label: '持仓',
    icon: '◈'
  }, {
    id: 'log',
    label: '日志',
    icon: '≡'
  }, {
    id: 'cfg',
    label: '配置',
    icon: '⚙'
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      bottom: 0,
      left: 0,
      right: 0,
      background: 'rgba(11,14,21,.85)',
      backdropFilter: 'blur(24px)',
      borderTop: '1px solid var(--ap-line-soft)',
      padding: '8px 8px 28px',
      display: 'flex',
      justifyContent: 'space-around',
      zIndex: 50
    }
  }, tabs.map(t => /*#__PURE__*/React.createElement("div", {
    key: t.id,
    onClick: () => onChange(t.id),
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 4,
      padding: '4px 10px',
      cursor: 'pointer',
      color: active === t.id ? 'var(--ap-mint)' : 'var(--ap-fg-3)',
      transition: 'color .15s'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 18,
      fontFamily: 'var(--ap-font-mono)'
    }
  }, t.icon), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      fontWeight: 500
    }
  }, t.label))));
};
Object.assign(window, {
  MOCK,
  Pill,
  Dot,
  Card,
  Num,
  fmt,
  fmtPct,
  fmtSigned,
  TopRiskBar,
  AppHeader,
  StatTile,
  Sparkline,
  DecisionStepper,
  AIDecisionCard,
  PositionRow,
  LogRow,
  TabBar
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/mobile_app/components/atoms.jsx", error: String((e && e.message) || e) }); }

// ui_kits/mobile_app/components/screens.jsx
try { (() => {
// Screens — Dashboard / AI / Positions / Log / Config

// generate sparkline mock data
const genSpark = (n = 48, base = 120000, vol = 800) => {
  const out = [];
  let v = base;
  for (let i = 0; i < n; i++) {
    v += Math.sin(i / 3) * vol + (Math.random() - 0.4) * vol * 0.6;
    out.push(v);
  }
  out[n - 1] = base + 2291;
  return out;
};
const SPARK = genSpark();

// =========================================================
// Dashboard (home)
// =========================================================
const DashboardScreen = ({
  onOpenDecision
}) => {
  const {
    equity,
    equityChangePct,
    equityChange,
    todayPnl,
    todayPnlPct,
    positions,
    tradesToday,
    winRate,
    regime,
    riskState,
    dayLossPct,
    positionsPct,
    decisions
  } = MOCK;
  const latest = decisions[0];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      paddingTop: 54,
      paddingBottom: 100
    }
  }, /*#__PURE__*/React.createElement(TopRiskBar, {
    state: riskState,
    regime: regime,
    loss: dayLossPct,
    positions: positionsPct
  }), /*#__PURE__*/React.createElement(AppHeader, {
    sub: "AlphaPilot \xB7 AI \u81EA\u4E3B\u4EA4\u6613",
    title: "\u4EEA\u8868\u76D8",
    right: /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '6px 12px',
        background: 'var(--ap-mint-soft)',
        borderRadius: 999
      }
    }, /*#__PURE__*/React.createElement(Dot, {
      c: "var(--ap-mint)",
      glow: true
    }), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 11,
        color: 'var(--ap-mint)',
        fontWeight: 600
      }
    }, "AUTO"))
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px',
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.06em',
      textTransform: 'uppercase',
      marginBottom: 4
    }
  }, "\u8D26\u6237\u6743\u76CA"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 10,
      marginBottom: 2
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 32,
      fontWeight: 700,
      letterSpacing: '-.03em'
    }
  }, "$", fmt(equity))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement(Num, {
    v: fmt(equityChange),
    prefix: "+$",
    positive: true,
    size: 13
  }), /*#__PURE__*/React.createElement(Num, {
    v: fmtPct(equityChangePct),
    positive: true,
    size: 13
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)'
    }
  }, "\u4ECA\u65E5")), /*#__PURE__*/React.createElement("div", {
    style: {
      margin: '0 -16px -16px'
    }
  }, /*#__PURE__*/React.createElement(Sparkline, {
    data: SPARK,
    w: 376,
    h: 92
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px',
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 10,
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement(StatTile, {
    label: "\u4ECA\u65E5 PnL",
    value: fmtSigned(todayPnl),
    sub: fmtPct(todayPnlPct),
    tone: "pos"
  }), /*#__PURE__*/React.createElement(StatTile, {
    label: "\u6301\u4ED3\u6570",
    value: positions.length,
    sub: `仓位 ${positionsPct}%`
  }), /*#__PURE__*/React.createElement(StatTile, {
    label: "\u4ECA\u65E5\u4EA4\u6613",
    value: tradesToday,
    sub: `胜率 ${winRate}%`
  }), /*#__PURE__*/React.createElement(StatTile, {
    label: "\u6700\u5927\u56DE\u64A4",
    value: fmtPct(dayLossPct),
    sub: "\u9608\u503C \u22122.00%",
    tone: "neg"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px',
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 4px 8px'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.05em',
      textTransform: 'uppercase',
      fontWeight: 600
    }
  }, "\u6700\u65B0 AI \u51B3\u7B56"), /*#__PURE__*/React.createElement("span", {
    onClick: onOpenDecision,
    style: {
      fontSize: 12,
      color: 'var(--ap-mint)',
      cursor: 'pointer'
    }
  }, "\u67E5\u770B\u5168\u90E8 \u2192")), /*#__PURE__*/React.createElement(AIDecisionCard, {
    d: latest
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px',
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.05em',
      textTransform: 'uppercase',
      fontWeight: 600,
      padding: '0 4px 8px'
    }
  }, "\u5F53\u524D\u6301\u4ED3"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, MOCK.positions.map(p => /*#__PURE__*/React.createElement(PositionRow, {
    key: p.sym,
    p: p
  })))));
};

// =========================================================
// AI Decisions list
// =========================================================
const AIScreen = () => {
  const [filter, setFilter] = React.useState('all');
  const filtered = MOCK.decisions.filter(d => filter === 'all' || filter === 'exec' && d.guard === 'PASS' || filter === 'blocked' && d.guard !== 'PASS');
  return /*#__PURE__*/React.createElement("div", {
    style: {
      paddingTop: 54,
      paddingBottom: 100
    }
  }, /*#__PURE__*/React.createElement(TopRiskBar, {
    state: MOCK.riskState,
    regime: MOCK.regime,
    loss: MOCK.dayLossPct,
    positions: MOCK.positionsPct
  }), /*#__PURE__*/React.createElement(AppHeader, {
    sub: "Decision stream",
    title: "AI \u51B3\u7B56\u6D41"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px 10px',
      display: 'flex',
      gap: 6
    }
  }, [{
    k: 'all',
    l: '全部'
  }, {
    k: 'exec',
    l: '已执行'
  }, {
    k: 'blocked',
    l: '已拦截'
  }].map(t => /*#__PURE__*/React.createElement("div", {
    key: t.k,
    onClick: () => setFilter(t.k),
    style: {
      padding: '6px 14px',
      borderRadius: 999,
      fontSize: 12,
      fontWeight: 500,
      background: filter === t.k ? 'var(--ap-mint)' : 'var(--ap-bg-2)',
      color: filter === t.k ? 'var(--ap-bg-0)' : 'var(--ap-fg-2)',
      border: '1px solid ' + (filter === t.k ? 'var(--ap-mint)' : 'var(--ap-line)'),
      cursor: 'pointer'
    }
  }, t.l))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px',
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, filtered.map((d, i) => /*#__PURE__*/React.createElement(AIDecisionCard, {
    key: i,
    d: d
  }))));
};

// =========================================================
// Positions detail
// =========================================================
const PositionsScreen = () => {
  const p = MOCK.positions[0];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      paddingTop: 54,
      paddingBottom: 100
    }
  }, /*#__PURE__*/React.createElement(TopRiskBar, {
    state: MOCK.riskState,
    regime: MOCK.regime,
    loss: MOCK.dayLossPct,
    positions: MOCK.positionsPct
  }), /*#__PURE__*/React.createElement(AppHeader, {
    sub: "Positions \xB7 2 active",
    title: "\u6301\u4ED3"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px',
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 40,
      height: 40,
      borderRadius: '50%',
      background: 'linear-gradient(135deg,#F7931A,#8B4E0D)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#fff',
      fontWeight: 700
    }
  }, "\u20BF"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 16,
      fontWeight: 700
    }
  }, "BTCUSDT"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "\u8D8B\u52BF\u8DDF\u968F \xB7 \u5F00\u4ED3 14:23")), /*#__PURE__*/React.createElement(Pill, {
    tone: "mint"
  }, "LONG")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 10,
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.05em',
      textTransform: 'uppercase',
      marginBottom: 2
    }
  }, "\u6D6E\u52A8\u76C8\u4E8F"), /*#__PURE__*/React.createElement(Num, {
    v: fmtSigned(p.pnl),
    positive: true,
    size: 22
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.05em',
      textTransform: 'uppercase',
      marginBottom: 2
    }
  }, "\u6536\u76CA\u7387"), /*#__PURE__*/React.createElement(Num, {
    v: fmtPct(p.pnlPct),
    positive: true,
    size: 22
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--ap-bg-3)',
      borderRadius: 10,
      padding: 12,
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 12,
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)'
    }
  }, "\u6570\u91CF "), p.qty), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)'
    }
  }, "\u6807\u8BB0 "), fmt(p.mark)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)'
    }
  }, "\u5F00\u4ED3 "), fmt(p.entry)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)'
    }
  }, "\u4FDD\u8BC1\u91D1 "), "2.5%"), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)'
    }
  }, "SL "), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-rose)'
    }
  }, fmt(64210))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)'
    }
  }, "TP "), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-mint)'
    }
  }, fmt(68900)))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      height: 24,
      background: 'var(--ap-bg-3)',
      borderRadius: 6,
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: '0%',
      top: 0,
      bottom: 0,
      width: '32%',
      background: 'var(--ap-rose-soft)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      right: '0%',
      top: 0,
      bottom: 0,
      width: '18%',
      background: 'var(--ap-mint-soft)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: '68%',
      top: 0,
      bottom: 0,
      width: 2,
      background: 'var(--ap-mint)',
      boxShadow: '0 0 8px var(--ap-mint)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: '32%',
      top: 0,
      bottom: 0,
      width: 1,
      background: 'var(--ap-fg-3)'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      marginTop: 4,
      fontSize: 10,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, /*#__PURE__*/React.createElement("span", null, "SL 64,210"), /*#__PURE__*/React.createElement("span", null, "\u5F00\u4ED3 67,420"), /*#__PURE__*/React.createElement("span", null, "\u5F53\u524D 68,863"), /*#__PURE__*/React.createElement("span", null, "TP 68,900"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      marginTop: 14
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      flex: 1,
      padding: '10px',
      borderRadius: 10,
      border: '1px solid var(--ap-line)',
      background: 'var(--ap-bg-3)',
      color: 'var(--ap-fg-1)',
      fontSize: 13,
      fontWeight: 600,
      cursor: 'pointer'
    }
  }, "\u8C03\u6574 SL/TP"), /*#__PURE__*/React.createElement("button", {
    style: {
      flex: 1,
      padding: '10px',
      borderRadius: 10,
      border: 'none',
      background: 'var(--ap-rose)',
      color: '#fff',
      fontSize: 13,
      fontWeight: 600,
      cursor: 'pointer'
    }
  }, "\u7ACB\u5373\u5E73\u4ED3")))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.05em',
      textTransform: 'uppercase',
      fontWeight: 600,
      padding: '0 4px 8px'
    }
  }, "\u5176\u4ED6\u6301\u4ED3"), /*#__PURE__*/React.createElement(PositionRow, {
    p: MOCK.positions[1]
  })));
};

// =========================================================
// Log / Activity
// =========================================================
const LogScreen = () => /*#__PURE__*/React.createElement("div", {
  style: {
    paddingTop: 54,
    paddingBottom: 100
  }
}, /*#__PURE__*/React.createElement(TopRiskBar, {
  state: MOCK.riskState,
  regime: MOCK.regime,
  loss: MOCK.dayLossPct,
  positions: MOCK.positionsPct
}), /*#__PURE__*/React.createElement(AppHeader, {
  sub: "Audit log \xB7 \u5B9E\u65F6",
  title: "\u4EA4\u6613\u65E5\u5FD7"
}), /*#__PURE__*/React.createElement("div", {
  style: {
    padding: '0 16px'
  }
}, /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8
  }
}, /*#__PURE__*/React.createElement("span", {
  style: {
    fontSize: 12,
    color: 'var(--ap-fg-3)',
    letterSpacing: '.05em',
    textTransform: 'uppercase',
    fontWeight: 600
  }
}, "\u4ECA\u65E5\u4E8B\u4EF6"), /*#__PURE__*/React.createElement("span", {
  style: {
    fontSize: 11,
    color: 'var(--ap-fg-3)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, MOCK.logs.length, " \u6761")), MOCK.logs.map((l, i) => /*#__PURE__*/React.createElement(LogRow, {
  key: i,
  l: l
})))), /*#__PURE__*/React.createElement("div", {
  style: {
    padding: '12px 16px 0'
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 12,
    color: 'var(--ap-fg-3)',
    letterSpacing: '.05em',
    textTransform: 'uppercase',
    fontWeight: 600,
    padding: '0 4px 8px'
  }
}, "\u65E5\u62A5\u6458\u8981"), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 13,
    color: 'var(--ap-fg-2)',
    lineHeight: 1.6
  }
}, "\u672C\u65E5 ", /*#__PURE__*/React.createElement("span", {
  style: {
    color: 'var(--ap-fg-1)',
    fontWeight: 600
  }
}, "7 \u7B14"), "\u4EA4\u6613 \xB7 \u80DC\u7387 ", /*#__PURE__*/React.createElement("span", {
  style: {
    color: 'var(--ap-mint)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, "57%"), " \xB7 \u51C0\u6536\u76CA ", /*#__PURE__*/React.createElement("span", {
  style: {
    color: 'var(--ap-mint)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, "+1.82%"), "\u3002 BTCUSDT \u4E3B\u5BFC\u76C8\u5229\u8D21\u732E\uFF08", /*#__PURE__*/React.createElement("span", {
  style: {
    color: 'var(--ap-mint)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, "+$1,890"), "\uFF09\uFF0CETHUSDT \u53D7 chaotic regime \u62D6\u7D2F\uFF08", /*#__PURE__*/React.createElement("span", {
  style: {
    color: 'var(--ap-rose)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, "\u2212$642"), "\uFF09\u3002 \u5B88\u536B\u5171\u62E6\u622A ", /*#__PURE__*/React.createElement("span", {
  style: {
    color: 'var(--ap-amber)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, "2 \u6B21"), "\uFF0C\u5747\u56E0 RR < 1.5\u3002"))));

// =========================================================
// Config
// =========================================================
const ConfigScreen = () => {
  const [auto, setAuto] = React.useState(true);
  const [testnet, setTestnet] = React.useState(false);
  const [tf, setTf] = React.useState('15m');
  return /*#__PURE__*/React.createElement("div", {
    style: {
      paddingTop: 54,
      paddingBottom: 100
    }
  }, /*#__PURE__*/React.createElement(TopRiskBar, {
    state: MOCK.riskState,
    regime: MOCK.regime,
    loss: MOCK.dayLossPct,
    positions: MOCK.positionsPct
  }), /*#__PURE__*/React.createElement(AppHeader, {
    sub: "Strategy \xB7 Risk \xB7 API",
    title: "\u914D\u7F6E\u4E2D\u5FC3"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px',
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.06em',
      textTransform: 'uppercase',
      marginBottom: 10
    }
  }, "\u8FD0\u884C\u5F00\u5173"), /*#__PURE__*/React.createElement(Row, {
    label: "\u81EA\u52A8\u4EA4\u6613",
    on: auto,
    onToggle: () => setAuto(!auto),
    sub: "\u5B88\u536B\u901A\u8FC7\u540E\u81EA\u52A8\u4E0B\u5355"
  }), /*#__PURE__*/React.createElement(Row, {
    label: "\u6D4B\u8BD5\u76D8\u6A21\u5F0F",
    on: testnet,
    onToggle: () => setTestnet(!testnet),
    sub: "Binance Testnet \xB7 \u65E0\u771F\u5B9E\u8D44\u91D1"
  }), /*#__PURE__*/React.createElement(Row, {
    label: "\u901A\u77E5\uFF08Telegram\uFF09",
    on: true,
    onToggle: () => {},
    sub: "\u5F00\u4ED3/\u5E73\u4ED3/\u7194\u65AD\u5373\u65F6\u63A8\u9001",
    last: true
  })), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.06em',
      textTransform: 'uppercase',
      marginBottom: 10
    }
  }, "\u4EA4\u6613\u5BF9 \xB7 \u5468\u671F"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: 6,
      marginBottom: 12
    }
  }, ['BTCUSDT', 'ETHUSDT'].map(s => /*#__PURE__*/React.createElement(Pill, {
    key: s,
    tone: "mint",
    mono: true
  }, s)), /*#__PURE__*/React.createElement(Pill, {
    tone: "default"
  }, "+ \u6DFB\u52A0")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.05em',
      textTransform: 'uppercase',
      marginBottom: 6
    }
  }, "K\u7EBF\u5468\u671F"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-flex',
      background: 'var(--ap-bg-3)',
      borderRadius: 10,
      padding: 3,
      border: '1px solid var(--ap-line)'
    }
  }, ['5m', '15m', '1h', '4h', '1d'].map(t => /*#__PURE__*/React.createElement("div", {
    key: t,
    onClick: () => setTf(t),
    style: {
      fontSize: 12,
      padding: '6px 12px',
      borderRadius: 8,
      fontFamily: 'var(--ap-font-mono)',
      cursor: 'pointer',
      background: tf === t ? 'var(--ap-bg-4)' : 'transparent',
      color: tf === t ? 'var(--ap-fg-1)' : 'var(--ap-fg-3)'
    }
  }, t)))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.06em',
      textTransform: 'uppercase',
      marginBottom: 10
    }
  }, "\u53D7\u9650\u7B56\u7565\u6846\u67B6"), /*#__PURE__*/React.createElement(StratRow, {
    name: "\u8D8B\u52BF\u8DDF\u968F",
    active: true,
    enabled: true,
    desc: "EMA \u6392\u5217 + ATR \u786E\u8BA4"
  }), /*#__PURE__*/React.createElement(StratRow, {
    name: "\u7A81\u7834\u786E\u8BA4",
    active: false,
    enabled: true,
    desc: "\u963B\u529B\u4F4D\u7A81\u7834 + \u6210\u4EA4\u91CF"
  }), /*#__PURE__*/React.createElement(StratRow, {
    name: "\u89C2\u671B\u6A21\u5F0F",
    active: false,
    enabled: true,
    desc: "chaotic regime \u9ED8\u8BA4",
    last: true
  })), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.06em',
      textTransform: 'uppercase',
      marginBottom: 10
    }
  }, "\u786C\u98CE\u63A7\uFF08\u4E0D\u53EF\u5B66\u4E60\uFF09"), /*#__PURE__*/React.createElement(RiskRow, {
    label: "\u5355\u7B14\u6700\u5927\u98CE\u9669",
    val: "1.00%"
  }), /*#__PURE__*/React.createElement(RiskRow, {
    label: "\u6700\u5927\u5355\u5E01\u6301\u4ED3",
    val: "15%"
  }), /*#__PURE__*/React.createElement(RiskRow, {
    label: "\u65E5\u4E8F\u635F\u9608\u503C",
    val: "\u22122.00%",
    tone: "neg"
  }), /*#__PURE__*/React.createElement(RiskRow, {
    label: "\u8FDE\u7EED\u4E8F\u635F\u7194\u65AD",
    val: "3 \u7B14",
    last: true
  })), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.06em',
      textTransform: 'uppercase',
      marginBottom: 10
    }
  }, "Binance API"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '10px 0'
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/binance_logo.svg",
    style: {
      width: 24,
      height: 24
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "bnx_\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u20223f2a"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-mint)'
    }
  }, "\u5DF2\u8FDE\u63A5 \xB7 \u6700\u540E\u9A8C\u8BC1 14:20")), /*#__PURE__*/React.createElement(Pill, {
    tone: "mint"
  }, "ACTIVE"))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '10px 0 20px',
      textAlign: 'center',
      fontSize: 10,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "AlphaPilot v0.1 \xB7 build 2026.04.21")));
};
const Row = ({
  label,
  on,
  onToggle,
  sub,
  last
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px 0',
    borderBottom: last ? 'none' : '1px solid var(--ap-line-soft)'
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    flex: 1
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 14,
    color: 'var(--ap-fg-1)'
  }
}, label), sub && /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 11,
    color: 'var(--ap-fg-3)',
    marginTop: 2
  }
}, sub)), /*#__PURE__*/React.createElement("div", {
  onClick: onToggle,
  style: {
    width: 44,
    height: 26,
    borderRadius: 999,
    background: on ? 'var(--ap-mint)' : 'var(--ap-bg-4)',
    position: 'relative',
    cursor: 'pointer',
    transition: '.15s'
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    position: 'absolute',
    top: 3,
    left: on ? 21 : 3,
    width: 20,
    height: 20,
    background: '#fff',
    borderRadius: '50%',
    transition: '.15s'
  }
})));
const StratRow = ({
  name,
  active,
  enabled,
  desc,
  last
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px 0',
    borderBottom: last ? 'none' : '1px solid var(--ap-line-soft)'
  }
}, /*#__PURE__*/React.createElement(Dot, {
  c: active ? 'var(--ap-mint)' : 'var(--ap-fg-4)',
  glow: active
}), /*#__PURE__*/React.createElement("div", {
  style: {
    flex: 1,
    marginLeft: 10
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 14,
    color: 'var(--ap-fg-1)'
  }
}, name, " ", active && /*#__PURE__*/React.createElement(Pill, {
  tone: "mint"
}, "ACTIVE")), /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 11,
    color: 'var(--ap-fg-3)',
    marginTop: 2
  }
}, desc)), /*#__PURE__*/React.createElement(Pill, {
  tone: enabled ? 'mint' : 'default'
}, enabled ? '启用' : '停用'));
const RiskRow = ({
  label,
  val,
  tone,
  last
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px 0',
    borderBottom: last ? 'none' : '1px solid var(--ap-line-soft)'
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 13,
    color: 'var(--ap-fg-2)',
    flex: 1
  }
}, label), /*#__PURE__*/React.createElement("span", {
  style: {
    fontFamily: 'var(--ap-font-mono)',
    fontSize: 14,
    fontWeight: 600,
    color: tone === 'neg' ? 'var(--ap-rose)' : 'var(--ap-fg-1)'
  }
}, val));
Object.assign(window, {
  DashboardScreen,
  AIScreen,
  PositionsScreen,
  LogScreen,
  ConfigScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/mobile_app/components/screens.jsx", error: String((e && e.message) || e) }); }

// ui_kits/mobile_app/ios-frame.jsx
try { (() => {
// iOS.jsx — Simplified iOS 26 (Liquid Glass) device frame
// Based on the iOS 26 UI Kit + Figma status bar spec. No assets, no deps.
// Exports: IOSDevice, IOSStatusBar, IOSNavBar, IOSGlassPill, IOSList, IOSListRow, IOSKeyboard

// ─────────────────────────────────────────────────────────────
// Status bar
// ─────────────────────────────────────────────────────────────
function IOSStatusBar({
  dark = false,
  time = '9:41'
}) {
  const c = dark ? '#fff' : '#000';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 154,
      alignItems: 'center',
      justifyContent: 'center',
      padding: '21px 24px 19px',
      boxSizing: 'border-box',
      position: 'relative',
      zIndex: 20,
      width: '100%'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      height: 22,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      paddingTop: 1.5
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: '-apple-system, "SF Pro", system-ui',
      fontWeight: 590,
      fontSize: 17,
      lineHeight: '22px',
      color: c
    }
  }, time)), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      height: 22,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 7,
      paddingTop: 1,
      paddingRight: 1
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "19",
    height: "12",
    viewBox: "0 0 19 12"
  }, /*#__PURE__*/React.createElement("rect", {
    x: "0",
    y: "7.5",
    width: "3.2",
    height: "4.5",
    rx: "0.7",
    fill: c
  }), /*#__PURE__*/React.createElement("rect", {
    x: "4.8",
    y: "5",
    width: "3.2",
    height: "7",
    rx: "0.7",
    fill: c
  }), /*#__PURE__*/React.createElement("rect", {
    x: "9.6",
    y: "2.5",
    width: "3.2",
    height: "9.5",
    rx: "0.7",
    fill: c
  }), /*#__PURE__*/React.createElement("rect", {
    x: "14.4",
    y: "0",
    width: "3.2",
    height: "12",
    rx: "0.7",
    fill: c
  })), /*#__PURE__*/React.createElement("svg", {
    width: "17",
    height: "12",
    viewBox: "0 0 17 12"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M8.5 3.2C10.8 3.2 12.9 4.1 14.4 5.6L15.5 4.5C13.7 2.7 11.2 1.5 8.5 1.5C5.8 1.5 3.3 2.7 1.5 4.5L2.6 5.6C4.1 4.1 6.2 3.2 8.5 3.2Z",
    fill: c
  }), /*#__PURE__*/React.createElement("path", {
    d: "M8.5 6.8C9.9 6.8 11.1 7.3 12 8.2L13.1 7.1C11.8 5.9 10.2 5.1 8.5 5.1C6.8 5.1 5.2 5.9 3.9 7.1L5 8.2C5.9 7.3 7.1 6.8 8.5 6.8Z",
    fill: c
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "8.5",
    cy: "10.5",
    r: "1.5",
    fill: c
  })), /*#__PURE__*/React.createElement("svg", {
    width: "27",
    height: "13",
    viewBox: "0 0 27 13"
  }, /*#__PURE__*/React.createElement("rect", {
    x: "0.5",
    y: "0.5",
    width: "23",
    height: "12",
    rx: "3.5",
    stroke: c,
    strokeOpacity: "0.35",
    fill: "none"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "2",
    y: "2",
    width: "20",
    height: "9",
    rx: "2",
    fill: c
  }), /*#__PURE__*/React.createElement("path", {
    d: "M25 4.5V8.5C25.8 8.2 26.5 7.2 26.5 6.5C26.5 5.8 25.8 4.8 25 4.5Z",
    fill: c,
    fillOpacity: "0.4"
  }))));
}

// ─────────────────────────────────────────────────────────────
// Liquid glass pill — blur + tint + shine
// ─────────────────────────────────────────────────────────────
function IOSGlassPill({
  children,
  dark = false,
  style = {}
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      height: 44,
      minWidth: 44,
      borderRadius: 9999,
      position: 'relative',
      overflow: 'hidden',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: dark ? '0 2px 6px rgba(0,0,0,0.35), 0 6px 16px rgba(0,0,0,0.2)' : '0 1px 3px rgba(0,0,0,0.07), 0 3px 10px rgba(0,0,0,0.06)',
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      borderRadius: 9999,
      backdropFilter: 'blur(12px) saturate(180%)',
      WebkitBackdropFilter: 'blur(12px) saturate(180%)',
      background: dark ? 'rgba(120,120,128,0.28)' : 'rgba(255,255,255,0.5)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      borderRadius: 9999,
      boxShadow: dark ? 'inset 1.5px 1.5px 1px rgba(255,255,255,0.15), inset -1px -1px 1px rgba(255,255,255,0.08)' : 'inset 1.5px 1.5px 1px rgba(255,255,255,0.7), inset -1px -1px 1px rgba(255,255,255,0.4)',
      border: dark ? '0.5px solid rgba(255,255,255,0.15)' : '0.5px solid rgba(0,0,0,0.06)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      zIndex: 1,
      display: 'flex',
      alignItems: 'center',
      padding: '0 4px'
    }
  }, children));
}

// ─────────────────────────────────────────────────────────────
// Navigation bar — glass pills + large title
// ─────────────────────────────────────────────────────────────
function IOSNavBar({
  title = 'Title',
  dark = false,
  trailingIcon = true
}) {
  const muted = dark ? 'rgba(255,255,255,0.6)' : '#404040';
  const text = dark ? '#fff' : '#000';
  const pillIcon = content => /*#__PURE__*/React.createElement(IOSGlassPill, {
    dark: dark
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 36,
      height: 36,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, content));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
      paddingTop: 62,
      paddingBottom: 10,
      position: 'relative',
      zIndex: 5
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 16px'
    }
  }, pillIcon(/*#__PURE__*/React.createElement("svg", {
    width: "12",
    height: "20",
    viewBox: "0 0 12 20",
    fill: "none",
    style: {
      marginLeft: -1
    }
  }, /*#__PURE__*/React.createElement("path", {
    d: "M10 2L2 10l8 8",
    stroke: muted,
    strokeWidth: "2.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }))), trailingIcon && pillIcon(/*#__PURE__*/React.createElement("svg", {
    width: "22",
    height: "6",
    viewBox: "0 0 22 6"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "3",
    cy: "3",
    r: "2.5",
    fill: muted
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "11",
    cy: "3",
    r: "2.5",
    fill: muted
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "19",
    cy: "3",
    r: "2.5",
    fill: muted
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px',
      fontFamily: '-apple-system, system-ui',
      fontSize: 34,
      fontWeight: 700,
      lineHeight: '41px',
      color: text,
      letterSpacing: 0.4
    }
  }, title));
}

// ─────────────────────────────────────────────────────────────
// Grouped list (inset card, r:26) + row (52px)
// ─────────────────────────────────────────────────────────────
function IOSListRow({
  title,
  detail,
  icon,
  chevron = true,
  isLast = false,
  dark = false
}) {
  const text = dark ? '#fff' : '#000';
  const sec = dark ? 'rgba(235,235,245,0.6)' : 'rgba(60,60,67,0.6)';
  const ter = dark ? 'rgba(235,235,245,0.3)' : 'rgba(60,60,67,0.3)';
  const sep = dark ? 'rgba(84,84,88,0.65)' : 'rgba(60,60,67,0.12)';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      minHeight: 52,
      padding: '0 16px',
      position: 'relative',
      fontFamily: '-apple-system, system-ui',
      fontSize: 17,
      letterSpacing: -0.43
    }
  }, icon && /*#__PURE__*/React.createElement("div", {
    style: {
      width: 30,
      height: 30,
      borderRadius: 7,
      background: icon,
      marginRight: 12,
      flexShrink: 0
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      color: text
    }
  }, title), detail && /*#__PURE__*/React.createElement("span", {
    style: {
      color: sec,
      marginRight: 6
    }
  }, detail), chevron && /*#__PURE__*/React.createElement("svg", {
    width: "8",
    height: "14",
    viewBox: "0 0 8 14",
    style: {
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("path", {
    d: "M1 1l6 6-6 6",
    stroke: ter,
    strokeWidth: "2",
    fill: "none",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  })), !isLast && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      bottom: 0,
      right: 0,
      left: icon ? 58 : 16,
      height: 0.5,
      background: sep
    }
  }));
}
function IOSList({
  header,
  children,
  dark = false
}) {
  const hc = dark ? 'rgba(235,235,245,0.6)' : 'rgba(60,60,67,0.6)';
  const bg = dark ? '#1C1C1E' : '#fff';
  return /*#__PURE__*/React.createElement("div", null, header && /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: '-apple-system, system-ui',
      fontSize: 13,
      color: hc,
      textTransform: 'uppercase',
      padding: '8px 36px 6px',
      letterSpacing: -0.08
    }
  }, header), /*#__PURE__*/React.createElement("div", {
    style: {
      background: bg,
      borderRadius: 26,
      margin: '0 16px',
      overflow: 'hidden'
    }
  }, children));
}

// ─────────────────────────────────────────────────────────────
// Device frame
// ─────────────────────────────────────────────────────────────
function IOSDevice({
  children,
  width = 402,
  height = 874,
  dark = false,
  title,
  keyboard = false
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width,
      height,
      borderRadius: 48,
      overflow: 'hidden',
      position: 'relative',
      background: dark ? '#000' : '#F2F2F7',
      boxShadow: '0 40px 80px rgba(0,0,0,0.18), 0 0 0 1px rgba(0,0,0,0.12)',
      fontFamily: '-apple-system, system-ui, sans-serif',
      WebkitFontSmoothing: 'antialiased'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 11,
      left: '50%',
      transform: 'translateX(-50%)',
      width: 126,
      height: 37,
      borderRadius: 24,
      background: '#000',
      zIndex: 50
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      zIndex: 10
    }
  }, /*#__PURE__*/React.createElement(IOSStatusBar, {
    dark: dark
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }
  }, title !== undefined && /*#__PURE__*/React.createElement(IOSNavBar, {
    title: title,
    dark: dark
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflow: 'auto'
    }
  }, children), keyboard && /*#__PURE__*/React.createElement(IOSKeyboard, {
    dark: dark
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      bottom: 0,
      left: 0,
      right: 0,
      zIndex: 60,
      height: 34,
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'flex-end',
      paddingBottom: 8,
      pointerEvents: 'none'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 139,
      height: 5,
      borderRadius: 100,
      background: dark ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.25)'
    }
  })));
}

// ─────────────────────────────────────────────────────────────
// Keyboard — iOS 26 liquid glass
// ─────────────────────────────────────────────────────────────
function IOSKeyboard({
  dark = false
}) {
  const glyph = dark ? 'rgba(255,255,255,0.7)' : '#595959';
  const sugg = dark ? 'rgba(255,255,255,0.6)' : '#333';
  const keyBg = dark ? 'rgba(255,255,255,0.22)' : 'rgba(255,255,255,0.85)';

  // special-key icons
  const icons = {
    shift: /*#__PURE__*/React.createElement("svg", {
      width: "19",
      height: "17",
      viewBox: "0 0 19 17"
    }, /*#__PURE__*/React.createElement("path", {
      d: "M9.5 1L1 9.5h4.5V16h8V9.5H18L9.5 1z",
      fill: glyph
    })),
    del: /*#__PURE__*/React.createElement("svg", {
      width: "23",
      height: "17",
      viewBox: "0 0 23 17"
    }, /*#__PURE__*/React.createElement("path", {
      d: "M7 1h13a2 2 0 012 2v11a2 2 0 01-2 2H7l-6-7.5L7 1z",
      fill: "none",
      stroke: glyph,
      strokeWidth: "1.6",
      strokeLinejoin: "round"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M10 5l7 7M17 5l-7 7",
      stroke: glyph,
      strokeWidth: "1.6",
      strokeLinecap: "round"
    })),
    ret: /*#__PURE__*/React.createElement("svg", {
      width: "20",
      height: "14",
      viewBox: "0 0 20 14"
    }, /*#__PURE__*/React.createElement("path", {
      d: "M18 1v6H4m0 0l4-4M4 7l4 4",
      fill: "none",
      stroke: "#fff",
      strokeWidth: "1.8",
      strokeLinecap: "round",
      strokeLinejoin: "round"
    }))
  };
  const key = (content, {
    w,
    flex,
    ret,
    fs = 25,
    k
  } = {}) => /*#__PURE__*/React.createElement("div", {
    key: k,
    style: {
      height: 42,
      borderRadius: 8.5,
      flex: flex ? 1 : undefined,
      width: w,
      minWidth: 0,
      background: ret ? '#08f' : keyBg,
      boxShadow: '0 1px 0 rgba(0,0,0,0.075)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: '-apple-system, "SF Compact", system-ui',
      fontSize: fs,
      fontWeight: 458,
      color: ret ? '#fff' : glyph
    }
  }, content);
  const row = (keys, pad = 0) => /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6.5,
      justifyContent: 'center',
      padding: `0 ${pad}px`
    }
  }, keys.map(l => key(l, {
    flex: true,
    k: l
  })));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      zIndex: 15,
      borderRadius: 27,
      overflow: 'hidden',
      padding: '11px 0 2px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      boxShadow: dark ? '0 -2px 20px rgba(0,0,0,0.09)' : '0 -1px 6px rgba(0,0,0,0.018), 0 -3px 20px rgba(0,0,0,0.012)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      borderRadius: 27,
      backdropFilter: 'blur(12px) saturate(180%)',
      WebkitBackdropFilter: 'blur(12px) saturate(180%)',
      background: dark ? 'rgba(120,120,128,0.14)' : 'rgba(255,255,255,0.25)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      borderRadius: 27,
      boxShadow: dark ? 'inset 1.5px 1.5px 1px rgba(255,255,255,0.15)' : 'inset 1.5px 1.5px 1px rgba(255,255,255,0.7), inset -1px -1px 1px rgba(255,255,255,0.4)',
      border: dark ? '0.5px solid rgba(255,255,255,0.15)' : '0.5px solid rgba(0,0,0,0.06)',
      pointerEvents: 'none'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 20,
      alignItems: 'center',
      padding: '8px 22px 13px',
      width: '100%',
      boxSizing: 'border-box',
      position: 'relative'
    }
  }, ['"The"', 'the', 'to'].map((w, i) => /*#__PURE__*/React.createElement(React.Fragment, {
    key: i
  }, i > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      width: 1,
      height: 25,
      background: '#ccc',
      opacity: 0.3
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      textAlign: 'center',
      fontFamily: '-apple-system, system-ui',
      fontSize: 17,
      color: sugg,
      letterSpacing: -0.43,
      lineHeight: '22px'
    }
  }, w)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 13,
      padding: '0 6.5px',
      width: '100%',
      boxSizing: 'border-box',
      position: 'relative'
    }
  }, row(['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p']), row(['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'], 20), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 14.25,
      alignItems: 'center'
    }
  }, key(icons.shift, {
    w: 45,
    k: 'shift'
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6.5,
      flex: 1
    }
  }, ['z', 'x', 'c', 'v', 'b', 'n', 'm'].map(l => key(l, {
    flex: true,
    k: l
  }))), key(icons.del, {
    w: 45,
    k: 'del'
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6,
      alignItems: 'center'
    }
  }, key('ABC', {
    w: 92.25,
    fs: 18,
    k: 'abc'
  }), key('', {
    flex: true,
    k: 'space'
  }), key(icons.ret, {
    w: 92.25,
    ret: true,
    k: 'ret'
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 56,
      width: '100%',
      position: 'relative'
    }
  }));
}
Object.assign(window, {
  IOSDevice,
  IOSStatusBar,
  IOSNavBar,
  IOSGlassPill,
  IOSList,
  IOSListRow,
  IOSKeyboard
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/mobile_app/ios-frame.jsx", error: String((e && e.message) || e) }); }

// ui_kits/web_app/components/admin.jsx
try { (() => {
// Admin console — 用户管理 · 角色权限 · 管理操作日志

const ADMIN_USERS = [{
  name: 'Daner Li',
  email: 'daner@alphapilot.io',
  role: 'owner',
  status: 'active',
  last: '刚刚',
  twofa: true,
  self: true
}, {
  name: 'Wei Zhang',
  email: 'wei.z@alphapilot.io',
  role: 'admin',
  status: 'active',
  last: '2 小时前',
  twofa: true
}, {
  name: 'Ming Chen',
  email: 'ming.c@alphapilot.io',
  role: 'trader',
  status: 'active',
  last: '昨天 22:41',
  twofa: true
}, {
  name: 'Lu Wang',
  email: 'lu.w@alphapilot.io',
  role: 'viewer',
  status: 'active',
  last: '3 天前',
  twofa: false
}, {
  name: 'Hao Sun',
  email: 'hao.s@gmail.com',
  role: 'viewer',
  status: 'pending',
  last: '—',
  twofa: false
}, {
  name: 'Jing Liu',
  email: 'jing.l@alphapilot.io',
  role: 'trader',
  status: 'disabled',
  last: '06-12',
  twofa: true
}];
const ROLES = {
  owner: {
    l: 'Owner',
    tone: 'violet',
    desc: '所有权限 + 转让所有权'
  },
  admin: {
    l: 'Admin',
    tone: 'rose',
    desc: '用户/权限/系统配置管理'
  },
  trader: {
    l: 'Trader',
    tone: 'mint',
    desc: '交易操作与策略管理'
  },
  viewer: {
    l: 'Viewer',
    tone: 'cyan',
    desc: '只读访问'
  }
};
const PERMS = [{
  group: '交易',
  items: [{
    k: '查看持仓与行情',
    owner: 1,
    admin: 1,
    trader: 1,
    viewer: 1
  }, {
    k: '手动下单 / 平仓',
    owner: 1,
    admin: 1,
    trader: 1,
    viewer: 0
  }, {
    k: '启停自动交易',
    owner: 1,
    admin: 1,
    trader: 1,
    viewer: 0
  }, {
    k: '修改硬风控阈值',
    owner: 1,
    admin: 1,
    trader: 0,
    viewer: 0
  }]
}, {
  group: '策略',
  items: [{
    k: '查看策略与实验室',
    owner: 1,
    admin: 1,
    trader: 1,
    viewer: 1
  }, {
    k: '提交策略候选',
    owner: 1,
    admin: 1,
    trader: 1,
    viewer: 0
  }, {
    k: '批准灰度 / 上线',
    owner: 1,
    admin: 1,
    trader: 0,
    viewer: 0
  }]
}, {
  group: '系统',
  items: [{
    k: '交易所 API 配置',
    owner: 1,
    admin: 1,
    trader: 0,
    viewer: 0
  }, {
    k: 'LLM 模型配置',
    owner: 1,
    admin: 1,
    trader: 0,
    viewer: 0
  }, {
    k: '用户与权限管理',
    owner: 1,
    admin: 1,
    trader: 0,
    viewer: 0
  }, {
    k: '紧急停止引擎',
    owner: 1,
    admin: 1,
    trader: 1,
    viewer: 0
  }]
}];
const ADMIN_LOG = [{
  t: '07-03 09:12',
  who: 'Daner Li',
  act: '修改硬风控 · 日亏损熔断 −2.00% → −1.50%',
  kind: 'risk'
}, {
  t: '07-02 18:40',
  who: 'Wei Zhang',
  act: '批准策略上线 · 趋势跟随 v2.0',
  kind: 'strategy'
}, {
  t: '07-02 15:03',
  who: 'Daner Li',
  act: '邀请用户 hao.s@gmail.com（Viewer）',
  kind: 'user'
}, {
  t: '07-01 11:27',
  who: 'Wei Zhang',
  act: '停用账户 Jing Liu',
  kind: 'user'
}, {
  t: '06-30 20:15',
  who: 'Daner Li',
  act: '更换 Binance API Key（主网）',
  kind: 'system'
}, {
  t: '06-30 09:00',
  who: 'system',
  act: '自动回滚 · 均值回归 v0.4 灰度回撤超限',
  kind: 'strategy'
}];
const StatusPill = ({
  s
}) => /*#__PURE__*/React.createElement(WPill, {
  tone: s === 'active' ? 'mint' : s === 'pending' ? 'amber' : 'default'
}, s === 'active' ? '活跃' : s === 'pending' ? '待批准' : '已停用');
const Avatar = ({
  name,
  size = 30
}) => {
  const hue = name.charCodeAt(0) * 37 % 360;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: size,
      height: size,
      borderRadius: '50%',
      flexShrink: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: `oklch(0.45 0.09 ${hue})`,
      color: '#fff',
      fontSize: size * 0.38,
      fontWeight: 700
    }
  }, name.split(' ').map(w => w[0]).join(''));
};

// ---------- 用户管理 ----------
const UsersTab = () => {
  const [users, setUsers] = React.useState(ADMIN_USERS);
  const approve = email => setUsers(us => us.map(u => u.email === email ? {
    ...u,
    status: 'active'
  } : u));
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(4,1fr)',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(WCard, {
    dense: true
  }, /*#__PURE__*/React.createElement(WStat, {
    label: "\u603B\u7528\u6237",
    value: users.length,
    size: "sm"
  })), /*#__PURE__*/React.createElement(WCard, {
    dense: true
  }, /*#__PURE__*/React.createElement(WStat, {
    label: "\u6D3B\u8DC3",
    value: users.filter(u => u.status === 'active').length,
    size: "sm",
    tone: "pos"
  })), /*#__PURE__*/React.createElement(WCard, {
    dense: true
  }, /*#__PURE__*/React.createElement(WStat, {
    label: "\u5F85\u6279\u51C6",
    value: users.filter(u => u.status === 'pending').length,
    size: "sm"
  })), /*#__PURE__*/React.createElement(WCard, {
    dense: true
  }, /*#__PURE__*/React.createElement(WStat, {
    label: "2FA \u8986\u76D6",
    value: Math.round(users.filter(u => u.twofa).length / users.length * 100) + '%',
    size: "sm"
  }))), /*#__PURE__*/React.createElement(WCard, {
    title: "\u7528\u6237",
    right: /*#__PURE__*/React.createElement("button", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '6px 13px',
        borderRadius: 8,
        border: 'none',
        background: 'var(--ap-mint)',
        color: 'var(--ap-bg-0)',
        fontSize: 12,
        fontWeight: 700,
        cursor: 'pointer',
        fontFamily: 'inherit'
      }
    }, "+ \u9080\u8BF7\u7528\u6237")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      margin: '-16px -18px'
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: '100%',
      borderCollapse: 'collapse',
      fontSize: 12.5
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", {
    style: {
      borderBottom: '1px solid var(--ap-line)'
    }
  }, ['用户', '角色', '状态', '2FA', '最近活跃', '操作'].map(h => /*#__PURE__*/React.createElement("th", {
    key: h,
    style: {
      padding: '10px 14px',
      textAlign: 'left',
      fontSize: 10,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.06em',
      textTransform: 'uppercase',
      fontWeight: 500
    }
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, users.map((u, i) => /*#__PURE__*/React.createElement("tr", {
    key: i,
    style: {
      borderBottom: '1px solid var(--ap-line-soft)',
      opacity: u.status === 'disabled' ? 0.55 : 1
    }
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '11px 14px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement(Avatar, {
    name: u.name
  }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 600,
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, u.name, u.self && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-4)'
    }
  }, "\uFF08\u4F60\uFF09")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, u.email)))), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '11px 14px'
    }
  }, /*#__PURE__*/React.createElement(WPill, {
    tone: ROLES[u.role].tone
  }, ROLES[u.role].l)), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '11px 14px'
    }
  }, /*#__PURE__*/React.createElement(StatusPill, {
    s: u.status
  })), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '11px 14px'
    }
  }, u.twofa ? /*#__PURE__*/React.createElement(Icon, {
    name: "check",
    size: 14,
    color: "var(--ap-mint)",
    strokeWidth: 2.4
  }) : /*#__PURE__*/React.createElement(Icon, {
    name: "x",
    size: 14,
    color: "var(--ap-fg-4)",
    strokeWidth: 2.4
  })), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '11px 14px',
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11,
      color: 'var(--ap-fg-3)'
    }
  }, u.last), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '11px 14px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6
    }
  }, u.status === 'pending' ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    onClick: () => approve(u.email),
    style: {
      padding: '4px 11px',
      borderRadius: 6,
      border: 'none',
      background: 'var(--ap-mint)',
      color: 'var(--ap-bg-0)',
      fontSize: 11,
      fontWeight: 700,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u6279\u51C6"), /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '4px 11px',
      borderRadius: 6,
      border: '1px solid var(--ap-line)',
      background: 'transparent',
      color: 'var(--ap-fg-3)',
      fontSize: 11,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u62D2\u7EDD")) : !u.self && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '4px 11px',
      borderRadius: 6,
      border: '1px solid var(--ap-line)',
      background: 'var(--ap-bg-3)',
      color: 'var(--ap-fg-2)',
      fontSize: 11,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u7F16\u8F91"), /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '4px 11px',
      borderRadius: 6,
      border: '1px solid rgba(255,77,109,.35)',
      background: 'transparent',
      color: 'var(--ap-rose)',
      fontSize: 11,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, u.status === 'disabled' ? '启用' : '停用')))))))))));
};

// ---------- 角色权限 ----------
const RolesTab = () => /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4,1fr)',
    gap: 12
  }
}, Object.entries(ROLES).map(([k, r]) => /*#__PURE__*/React.createElement(WCard, {
  key: k,
  dense: true
}, /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6
  }
}, /*#__PURE__*/React.createElement(WPill, {
  tone: r.tone
}, r.l), /*#__PURE__*/React.createElement("span", {
  style: {
    fontSize: 11,
    color: 'var(--ap-fg-4)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, ADMIN_USERS.filter(u => u.role === k).length, " \u4EBA")), /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 11.5,
    color: 'var(--ap-fg-3)',
    lineHeight: 1.5
  }
}, r.desc)))), /*#__PURE__*/React.createElement(WCard, {
  title: "\u6743\u9650\u77E9\u9635",
  right: /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "Owner \u6743\u9650\u4E0D\u53EF\u4FEE\u6539")
}, /*#__PURE__*/React.createElement("div", {
  style: {
    margin: '-16px -18px'
  }
}, /*#__PURE__*/React.createElement("table", {
  style: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 12.5
  }
}, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", {
  style: {
    borderBottom: '1px solid var(--ap-line)'
  }
}, /*#__PURE__*/React.createElement("th", {
  style: {
    padding: '10px 14px',
    textAlign: 'left',
    fontSize: 10,
    color: 'var(--ap-fg-3)',
    letterSpacing: '.06em',
    textTransform: 'uppercase',
    fontWeight: 500
  }
}, "\u6743\u9650"), Object.values(ROLES).map(r => /*#__PURE__*/React.createElement("th", {
  key: r.l,
  style: {
    padding: '10px 14px',
    textAlign: 'center',
    fontSize: 10,
    letterSpacing: '.06em',
    textTransform: 'uppercase',
    fontWeight: 600,
    color: 'var(--ap-fg-2)'
  }
}, r.l)))), /*#__PURE__*/React.createElement("tbody", null, PERMS.map(g => /*#__PURE__*/React.createElement(React.Fragment, {
  key: g.group
}, /*#__PURE__*/React.createElement("tr", {
  style: {
    background: 'var(--ap-bg-3)'
  }
}, /*#__PURE__*/React.createElement("td", {
  colSpan: 5,
  style: {
    padding: '7px 14px',
    fontSize: 10,
    color: 'var(--ap-fg-3)',
    letterSpacing: '.08em',
    fontWeight: 700
  }
}, g.group)), g.items.map((p, i) => /*#__PURE__*/React.createElement("tr", {
  key: i,
  style: {
    borderBottom: '1px solid var(--ap-line-soft)'
  }
}, /*#__PURE__*/React.createElement("td", {
  style: {
    padding: '9px 14px',
    color: 'var(--ap-fg-2)'
  }
}, p.k), ['owner', 'admin', 'trader', 'viewer'].map(role => /*#__PURE__*/React.createElement("td", {
  key: role,
  style: {
    padding: '9px 14px',
    textAlign: 'center'
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'inline-flex',
    width: 18,
    height: 18,
    borderRadius: 5,
    alignItems: 'center',
    justifyContent: 'center',
    cursor: role === 'owner' ? 'not-allowed' : 'pointer',
    background: p[role] ? 'var(--ap-mint-soft)' : 'var(--ap-bg-3)',
    border: '1px solid ' + (p[role] ? 'rgba(0,211,149,.4)' : 'var(--ap-line)')
  }
}, p[role] ? /*#__PURE__*/React.createElement(Icon, {
  name: "check",
  size: 11,
  color: "var(--ap-mint)",
  strokeWidth: 2.8
}) : null))))))))))));

// ---------- 管理日志 ----------
const AdminLogTab = () => /*#__PURE__*/React.createElement(WCard, {
  title: "\u7BA1\u7406\u64CD\u4F5C\u65E5\u5FD7",
  right: /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6
    }
  }, ['全部', '用户', '风控', '策略', '系统'].map((t, i) => /*#__PURE__*/React.createElement("span", {
    key: t,
    style: {
      padding: '4px 10px',
      fontSize: 11,
      background: i === 0 ? 'var(--ap-bg-4)' : 'var(--ap-bg-3)',
      border: '1px solid var(--ap-line-soft)',
      borderRadius: 6,
      cursor: 'pointer',
      color: i === 0 ? 'var(--ap-fg-1)' : 'var(--ap-fg-3)'
    }
  }, t)))
}, ADMIN_LOG.map((l, i) => /*#__PURE__*/React.createElement("div", {
  key: i,
  style: {
    display: 'flex',
    gap: 12,
    padding: '11px 0',
    borderBottom: i < ADMIN_LOG.length - 1 ? '1px solid var(--ap-line-soft)' : 'none'
  }
}, l.who === 'system' ? /*#__PURE__*/React.createElement("div", {
  style: {
    width: 28,
    height: 28,
    borderRadius: '50%',
    background: 'var(--ap-bg-3)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0
  }
}, /*#__PURE__*/React.createElement(Icon, {
  name: "settings",
  size: 13,
  color: "var(--ap-fg-4)"
})) : /*#__PURE__*/React.createElement(Avatar, {
  name: l.who,
  size: 28
}), /*#__PURE__*/React.createElement("div", {
  style: {
    flex: 1,
    minWidth: 0
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 12.5,
    color: 'var(--ap-fg-1)',
    lineHeight: 1.5
  }
}, /*#__PURE__*/React.createElement("b", null, l.who === 'system' ? '系统' : l.who), " \xB7 ", l.act), /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 10.5,
    color: 'var(--ap-fg-4)',
    fontFamily: 'var(--ap-font-mono)',
    marginTop: 2
  }
}, l.t)), /*#__PURE__*/React.createElement(WPill, {
  tone: l.kind === 'risk' ? 'rose' : l.kind === 'strategy' ? 'violet' : l.kind === 'user' ? 'cyan' : 'default'
}, l.kind))));

// ---------- page ----------
const WAdminPage = () => {
  const [tab, setTab] = React.useState('users');
  const tabs = [{
    id: 'users',
    label: '用户管理',
    icon: 'users'
  }, {
    id: 'roles',
    label: '角色权限',
    icon: 'key'
  }, {
    id: 'log',
    label: '管理日志',
    icon: 'list'
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 24,
      maxWidth: 1100
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 180,
      flexShrink: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: 2
    }
  }, tabs.map(t => /*#__PURE__*/React.createElement("div", {
    key: t.id,
    onClick: () => setTab(t.id),
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '10px 12px',
      borderRadius: 9,
      cursor: 'pointer',
      background: tab === t.id ? 'var(--ap-bg-2)' : 'transparent',
      color: tab === t.id ? 'var(--ap-fg-1)' : 'var(--ap-fg-3)',
      fontSize: 13,
      fontWeight: 500,
      border: '1px solid ' + (tab === t.id ? 'var(--ap-line-soft)' : 'transparent')
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: t.icon,
    size: 15,
    color: tab === t.id ? 'var(--ap-mint)' : 'currentColor'
  }), t.label)), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 14,
      padding: '10px 12px',
      background: 'var(--ap-amber-soft)',
      borderRadius: 9,
      border: '1px solid rgba(240,185,11,.2)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-fg-2)',
      lineHeight: 1.5
    }
  }, "\u6240\u6709\u7BA1\u7406\u64CD\u4F5C\u5747\u8BB0\u5F55\u5BA1\u8BA1\u65E5\u5FD7\uFF0C\u4E0D\u53EF\u5220\u9664\u3002"))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: 16
    }
  }, tab === 'users' && /*#__PURE__*/React.createElement(UsersTab, null), tab === 'roles' && /*#__PURE__*/React.createElement(RolesTab, null), tab === 'log' && /*#__PURE__*/React.createElement(AdminLogTab, null)));
};
Object.assign(window, {
  WAdminPage
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/web_app/components/admin.jsx", error: String((e && e.message) || e) }); }

// ui_kits/web_app/components/ai_card.jsx
try { (() => {
// AI Decision card — 3 visual variants: stepper / timeline / graph

// ============ VARIANT A: Stepper (horizontal pipeline) ============
const AIDecisionStepper = ({
  d
}) => {
  const actionColor = d.action === 'OPEN_LONG' ? 'var(--ap-mint)' : d.action === 'CLOSE_LONG' ? 'var(--ap-rose)' : 'var(--ap-fg-2)';
  const guardTone = d.guard === 'PASS' ? 'mint' : d.guard === 'REJECT' ? 'rose' : 'amber';
  return /*#__PURE__*/React.createElement(WCard, {
    glow: true
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 28,
      height: 28,
      borderRadius: 8,
      background: 'var(--ap-violet-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "brain",
    size: 16,
    color: "var(--ap-violet)"
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-violet)',
      letterSpacing: '.1em',
      fontWeight: 700
    }
  }, "AI DECISION"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.02em'
    }
  }, d.id, " \xB7 ", d.sym, " \xB7 ", d.tf, " \xB7 ", d.t))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 22,
      fontWeight: 700,
      color: actionColor,
      letterSpacing: '.02em'
    }
  }, d.action), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "conf ", /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--ap-fg-1)'
    }
  }, d.conf?.toFixed(2))))), d.sl && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(5,1fr)',
      gap: 2,
      marginBottom: 14,
      background: 'var(--ap-bg-3)',
      borderRadius: 10,
      overflow: 'hidden'
    }
  }, [['策略', d.strat, 'var(--ap-fg-1)'], ['入场', wfmt(d.entry), 'var(--ap-fg-1)'], ['仓位', d.size, 'var(--ap-fg-1)'], ['止损', wfmt(d.sl), 'var(--ap-rose)'], ['止盈', wfmt(d.tp), 'var(--ap-mint)']].map(([l, v, c], i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      padding: '10px 12px',
      background: 'var(--ap-bg-2)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9.5,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.08em',
      textTransform: 'uppercase',
      marginBottom: 3
    }
  }, l), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 13,
      fontWeight: 600,
      color: c
    }
  }, v)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      padding: '6px 0 16px'
    }
  }, [{
    label: '市场快照',
    sub: 'regime · features',
    ok: true
  }, {
    label: 'AI 推理',
    sub: `conf ${d.conf?.toFixed(2)}`,
    ok: true
  }, {
    label: '守卫检查',
    sub: d.guard,
    ok: d.guard !== 'REJECT',
    degraded: d.guard === 'DEGRADE'
  }, {
    label: '风险裁决',
    sub: d.guard === 'PASS' ? '允许执行' : '回退 HOLD',
    ok: d.guard === 'PASS'
  }, {
    label: '执行',
    sub: d.guard === 'PASS' ? '已下单' : '未执行',
    ok: d.guard === 'PASS'
  }].map((step, i, arr) => /*#__PURE__*/React.createElement(React.Fragment, {
    key: i
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 8,
      flexShrink: 0,
      width: 100
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      borderRadius: '50%',
      background: step.ok ? 'var(--ap-mint)' : step.degraded ? 'var(--ap-amber)' : 'var(--ap-rose)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'var(--ap-bg-0)',
      fontWeight: 700,
      boxShadow: step.ok ? '0 0 12px rgba(0,211,149,.4)' : step.degraded ? '0 0 12px rgba(240,185,11,.4)' : '0 0 12px rgba(255,77,109,.4)'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: step.ok ? 'check' : step.degraded ? 'alert' : 'x',
    size: 15,
    color: "var(--ap-bg-0)",
    strokeWidth: 2.4
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-1)',
      fontWeight: 600
    }
  }, step.label), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)',
      marginTop: 2
    }
  }, step.sub))), i < arr.length - 1 && /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      height: 2,
      background: step.ok ? 'var(--ap-mint)' : step.degraded ? 'var(--ap-amber)' : 'var(--ap-rose)',
      marginTop: -30,
      opacity: .55
    }
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--ap-bg-3)',
      borderRadius: 10,
      padding: '12px 14px',
      fontSize: 13,
      color: 'var(--ap-fg-2)',
      lineHeight: 1.6
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-violet)',
      letterSpacing: '.08em',
      fontWeight: 700,
      marginBottom: 6
    }
  }, "REASONING"), d.reason), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginTop: 14
    }
  }, /*#__PURE__*/React.createElement(WPill, {
    tone: guardTone
  }, "\u5B88\u536B ", d.guard), d.features && /*#__PURE__*/React.createElement(WPill, {
    tone: "violet"
  }, d.features.length, " features"), d.guards && /*#__PURE__*/React.createElement(WPill, {
    tone: "default"
  }, d.guards.filter(g => g.ok).length, "/", d.guards.length, " checks"), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      fontSize: 11,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "trace \xB7 ", d.id.replace('d_', ''))));
};

// ============ VARIANT B: Timeline (vertical stages) ============
const AIDecisionTimeline = ({
  d
}) => {
  const actionColor = d.action === 'OPEN_LONG' ? 'var(--ap-mint)' : d.action === 'CLOSE_LONG' ? 'var(--ap-rose)' : 'var(--ap-fg-2)';
  const stages = [{
    t: d.t,
    label: '信号感知',
    detail: 'regime=trending_up · BTC 1h EMA 金叉',
    color: 'var(--ap-cyan)',
    icon: 'bolt'
  }, {
    t: d.t,
    label: 'AI 推理',
    detail: `${d.strat} · 置信度 ${d.conf?.toFixed(2)} · 输出 ${d.action}`,
    color: 'var(--ap-violet)',
    icon: 'brain'
  }, {
    t: d.t,
    label: '守卫检查',
    detail: d.guards ? `${d.guards.filter(g => g.ok).length}/${d.guards.length} 通过` : d.guard,
    color: d.guard === 'PASS' ? 'var(--ap-mint)' : d.guard === 'DEGRADE' ? 'var(--ap-amber)' : 'var(--ap-rose)',
    icon: 'shield'
  }, {
    t: d.t,
    label: '风险裁决',
    detail: d.guard === 'PASS' ? '允许执行 · 下单 ' + (d.size || '') : '回退 HOLD · 不下单',
    color: d.guard === 'PASS' ? 'var(--ap-mint)' : 'var(--ap-rose)',
    icon: 'check'
  }, {
    t: d.t,
    label: '执行',
    detail: d.guard === 'PASS' ? `Binance 市价成交 @ ${wfmt(d.entry || 0)}` : '—',
    color: d.guard === 'PASS' ? 'var(--ap-mint)' : 'var(--ap-fg-4)',
    icon: 'play'
  }];
  return /*#__PURE__*/React.createElement(WCard, {
    glow: true
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 18
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 28,
      height: 28,
      borderRadius: 8,
      background: 'var(--ap-violet-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "brain",
    size: 16,
    color: "var(--ap-violet)"
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-violet)',
      letterSpacing: '.1em',
      fontWeight: 700
    }
  }, "AI DECISION \xB7 TIMELINE"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11,
      color: 'var(--ap-fg-3)'
    }
  }, d.id, " \xB7 ", d.sym, " \xB7 ", d.tf))), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 22,
      fontWeight: 700,
      color: actionColor
    }
  }, d.action)), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      paddingLeft: 4
    }
  }, stages.map((s, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      gap: 14,
      paddingBottom: i === stages.length - 1 ? 0 : 14,
      position: 'relative'
    }
  }, i < stages.length - 1 && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 11,
      top: 26,
      bottom: -4,
      width: 1.5,
      background: 'linear-gradient(to bottom, ' + s.color + ' 0%, var(--ap-line) 100%)',
      opacity: .5
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 24,
      height: 24,
      borderRadius: '50%',
      background: s.color,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
      boxShadow: `0 0 10px ${s.color}40`,
      zIndex: 1
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: s.icon,
    size: 12,
    color: "var(--ap-bg-0)",
    strokeWidth: 2.2
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      paddingTop: 2
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 8,
      marginBottom: 2
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      fontWeight: 600,
      color: 'var(--ap-fg-1)'
    }
  }, s.label), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)',
      marginLeft: 'auto'
    }
  }, s.t)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, s.detail))))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 18,
      padding: '12px 14px',
      background: 'var(--ap-bg-3)',
      borderRadius: 10,
      fontSize: 13,
      color: 'var(--ap-fg-2)',
      lineHeight: 1.6
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-violet)',
      letterSpacing: '.08em',
      fontWeight: 700,
      marginBottom: 6
    }
  }, "REASONING"), d.reason));
};

// ============ VARIANT C: Graph (node diagram) ============
const AIDecisionGraph = ({
  d
}) => {
  const actionColor = d.action === 'OPEN_LONG' ? 'var(--ap-mint)' : d.action === 'CLOSE_LONG' ? 'var(--ap-rose)' : 'var(--ap-fg-2)';
  const guardPass = d.guard === 'PASS';
  const guardColor = guardPass ? 'var(--ap-mint)' : d.guard === 'DEGRADE' ? 'var(--ap-amber)' : 'var(--ap-rose)';
  return /*#__PURE__*/React.createElement(WCard, {
    glow: true
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 28,
      height: 28,
      borderRadius: 8,
      background: 'var(--ap-violet-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "brain",
    size: 16,
    color: "var(--ap-violet)"
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-violet)',
      letterSpacing: '.1em',
      fontWeight: 700
    }
  }, "AI DECISION \xB7 GRAPH"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11,
      color: 'var(--ap-fg-3)'
    }
  }, d.id, " \xB7 ", d.sym, " \xB7 ", d.tf))), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 22,
      fontWeight: 700,
      color: actionColor
    }
  }, d.action)), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      background: 'var(--ap-bg-3)',
      borderRadius: 12,
      padding: '20px 20px',
      minHeight: 360,
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    style: {
      position: 'absolute',
      inset: 0,
      width: '100%',
      height: '100%',
      opacity: .25,
      pointerEvents: 'none'
    }
  }, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("pattern", {
    id: "gd",
    width: "24",
    height: "24",
    patternUnits: "userSpaceOnUse"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M 24 0 L 0 0 0 24",
    fill: "none",
    stroke: "var(--ap-line)",
    strokeWidth: "1"
  }))), /*#__PURE__*/React.createElement("rect", {
    width: "100%",
    height: "100%",
    fill: "url(#gd)"
  })), /*#__PURE__*/React.createElement("svg", {
    style: {
      position: 'absolute',
      inset: 0,
      width: '100%',
      height: '100%',
      pointerEvents: 'none'
    }
  }, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("marker", {
    id: "arrow-mint",
    viewBox: "0 0 10 10",
    refX: "8",
    refY: "5",
    markerWidth: "6",
    markerHeight: "6",
    orient: "auto"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M 0 0 L 10 5 L 0 10 z",
    fill: "var(--ap-mint)"
  })), /*#__PURE__*/React.createElement("marker", {
    id: "arrow-v",
    viewBox: "0 0 10 10",
    refX: "8",
    refY: "5",
    markerWidth: "6",
    markerHeight: "6",
    orient: "auto"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M 0 0 L 10 5 L 0 10 z",
    fill: "var(--ap-violet)"
  })), /*#__PURE__*/React.createElement("marker", {
    id: "arrow-c",
    viewBox: "0 0 10 10",
    refX: "8",
    refY: "5",
    markerWidth: "6",
    markerHeight: "6",
    orient: "auto"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M 0 0 L 10 5 L 0 10 z",
    fill: "var(--ap-cyan)"
  }))), [60, 110, 160, 210, 260, 310].map((y, i) => /*#__PURE__*/React.createElement("path", {
    key: i,
    d: `M 180 ${y} C 240 ${y}, 260 180, 310 180`,
    stroke: "var(--ap-cyan)",
    strokeWidth: "1",
    strokeOpacity: ".55",
    fill: "none"
  })), /*#__PURE__*/React.createElement("path", {
    d: "M 480 180 L 560 180",
    stroke: "var(--ap-violet)",
    strokeWidth: "2",
    fill: "none",
    markerEnd: "url(#arrow-v)"
  }), [60, 100, 140, 180, 220, 260, 300, 340].map((y, i) => /*#__PURE__*/React.createElement("path", {
    key: i,
    d: `M 680 ${y} C 640 ${y}, 620 180, 640 180`,
    stroke: guardColor,
    strokeWidth: "1",
    strokeOpacity: ".5",
    fill: "none"
  })), /*#__PURE__*/React.createElement("path", {
    d: "M 740 180 L 820 180",
    stroke: guardColor,
    strokeWidth: "2.5",
    fill: "none",
    markerEnd: guardPass ? 'url(#arrow-mint)' : undefined
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 20,
      top: 20,
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      width: 160
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9.5,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.08em',
      textTransform: 'uppercase',
      marginBottom: 2
    }
  }, "FEATURES"), (d.features || [{
    k: 'regime',
    v: 'trending_up',
    ok: true
  }, {
    k: 'EMA_align',
    v: '20>50>200',
    ok: true
  }, {
    k: 'vol_mult',
    v: '1.4x',
    ok: true
  }, {
    k: 'ATR_14',
    v: '1.82%',
    ok: true
  }, {
    k: 'RSI_14',
    v: '58',
    ok: true
  }, {
    k: 'BB_width',
    v: '0.043',
    ok: true
  }]).slice(0, 6).map((f, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      padding: '5px 8px',
      background: 'var(--ap-bg-2)',
      borderRadius: 6,
      border: '1px solid var(--ap-line-soft)',
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 10.5,
      display: 'flex',
      justifyContent: 'space-between',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)'
    }
  }, f.k), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-cyan)'
    }
  }, f.v)))), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 310,
      top: 140,
      width: 170,
      padding: '14px',
      background: 'var(--ap-violet-soft)',
      border: '1px solid var(--ap-violet)',
      borderRadius: 12,
      boxShadow: '0 0 24px rgba(124,92,255,.3)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 6
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "brain",
    size: 16,
    color: "var(--ap-violet)"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: 'var(--ap-violet)',
      letterSpacing: '.05em'
    }
  }, "LLM + RULES")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-2)'
    }
  }, d.strat), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      marginTop: 6
    }
  }, "conf ", /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--ap-violet)'
    }
  }, d.conf?.toFixed(2)), " \xB7 ", d.action)), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 560,
      top: 155,
      width: 80,
      padding: '12px',
      background: 'var(--ap-bg-2)',
      border: `1px solid ${guardColor}`,
      borderRadius: 12,
      boxShadow: `0 0 20px ${guardColor}30`,
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "shield",
    size: 18,
    color: guardColor
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      fontFamily: 'var(--ap-font-mono)',
      fontWeight: 700,
      color: guardColor,
      marginTop: 4,
      letterSpacing: '.05em'
    }
  }, d.guard)), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 680,
      top: 20,
      display: 'flex',
      flexDirection: 'column',
      gap: 4,
      width: 150
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9.5,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.08em',
      textTransform: 'uppercase',
      marginBottom: 2
    }
  }, "GUARDS \xB7 8"), (d.guards || [{
    k: 'regime_match',
    ok: true
  }, {
    k: 'max_per_trade_risk',
    ok: true
  }, {
    k: 'max_position_size',
    ok: true
  }, {
    k: 'daily_loss_limit',
    ok: true
  }, {
    k: 'RR_ratio',
    ok: true
  }, {
    k: 'correlation_cap',
    ok: true
  }, {
    k: 'spread_check',
    ok: true
  }, {
    k: 'cooldown',
    ok: true
  }]).map((g, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      padding: '4px 8px',
      background: 'var(--ap-bg-2)',
      borderRadius: 6,
      border: '1px solid var(--ap-line-soft)',
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 10,
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(WDot, {
    c: g.ok ? 'var(--ap-mint)' : 'var(--ap-rose)'
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)',
      flex: 1,
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    }
  }, g.k)))), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 820,
      top: 155,
      padding: '12px 14px',
      background: guardPass ? 'var(--ap-mint-soft)' : 'var(--ap-rose-soft)',
      border: `1px solid ${guardPass ? 'var(--ap-mint)' : 'var(--ap-rose)'}`,
      borderRadius: 12,
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9.5,
      color: guardPass ? 'var(--ap-mint)' : 'var(--ap-rose)',
      letterSpacing: '.08em',
      fontWeight: 700
    }
  }, "EXECUTE"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 14,
      fontWeight: 700,
      color: guardPass ? 'var(--ap-mint)' : 'var(--ap-rose)',
      marginTop: 3
    }
  }, guardPass ? d.action : 'HOLD'))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 14,
      padding: '12px 14px',
      background: 'var(--ap-bg-3)',
      borderRadius: 10,
      fontSize: 13,
      color: 'var(--ap-fg-2)',
      lineHeight: 1.6
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-violet)',
      letterSpacing: '.08em',
      fontWeight: 700,
      marginBottom: 6
    }
  }, "REASONING"), d.reason));
};

// ============ Variant switcher ============
const AIDecisionCard = ({
  d,
  variant = 'stepper'
}) => {
  if (variant === 'timeline') return /*#__PURE__*/React.createElement(AIDecisionTimeline, {
    d: d
  });
  if (variant === 'graph') return /*#__PURE__*/React.createElement(AIDecisionGraph, {
    d: d
  });
  return /*#__PURE__*/React.createElement(AIDecisionStepper, {
    d: d
  });
};
Object.assign(window, {
  AIDecisionCard,
  AIDecisionStepper,
  AIDecisionTimeline,
  AIDecisionGraph
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/web_app/components/ai_card.jsx", error: String((e && e.message) || e) }); }

// ui_kits/web_app/components/ai_chat.jsx
try { (() => {
// Pilot AI — conversational assistant drawer
// Mock conversation with tool-use traces, quick prompts, streaming reply.

const CANNED = {
  '为什么 ETHUSDT 没有开仓？': {
    tools: ['查询决策记录 d_7f3a9a', '读取 regime 状态'],
    reply: '13:45 的决策周期中，ETHUSDT 的市场状态从 trending_up 切换为 chaotic（ATR 波动率进入前 10% 分位），触发策略降级规则。AI 输出 HOLD（置信度 0.42），守卫标记 DEGRADE。\n\n按照受限策略框架，chaotic regime 下仅允许「观望模式」，这是为了避免在无方向高波动期入场。若后续 1h 内 regime 恢复且量能配合，会重新评估。'
  },
  '当前风险敞口如何？': {
    tools: ['读取持仓', '计算组合风险'],
    reply: '当前 2 个持仓，总仓位 12%（上限 15%）：\n\n· BTCUSDT 多 0.048，浮盈 +2.14%，距止损 −6.8%\n· ETHUSDT 多 0.82，浮亏 −0.62%，距止损 −3.1%\n\n组合层面：BTC-ETH 相关度 0.68（上限 0.85），日损 −0.48%（熔断线 −2.00%）。整体风险健康，但 ETH 接近入场价，若跌破 3,180 建议关注。'
  },
  '帮我收紧风控': {
    tools: ['读取当前风控配置'],
    reply: '可以，这是我的建议（需你确认后生效）：\n\n1. 单笔最大风险 1.00% → 0.75%\n2. 日亏损熔断 −2.00% → −1.50%\n3. 连续亏损熔断 3 笔 → 2 笔\n\n注意：硬风控修改走人工确认流程，AI 无权自行变更。是否应用？',
    action: '应用修改（模拟）'
  },
  '今天表现怎么样？': {
    tools: ['读取今日交易', '生成归因'],
    reply: '今日 7 笔交易，胜率 57%，净收益 +1.82%（+$1,248）。\n\n亮点：趋势跟随策略在 BTC 上贡献 +$1,890，两次守卫拦截（RR<1.5）事后看均正确避损。\n\n短板：ETHUSDT 在 regime 切换前 45 分钟入场，时机偏早，−$642。经验库已记录该案例：「chaotic 前兆期的 ranging 误判」。'
  }
};
const QUICK_PROMPTS = Object.keys(CANNED);
const AIChatDrawer = ({
  open,
  onClose
}) => {
  const [messages, setMessages] = React.useState([{
    role: 'ai',
    text: '你好，我是 Pilot AI。可以问我任何关于持仓、决策、风控的问题——我能读取系统实时状态并解释每一笔决策。',
    tools: []
  }]);
  const [typing, setTyping] = React.useState(false);
  const [input, setInput] = React.useState('');
  const bodyRef = React.useRef(null);
  const timers = React.useRef([]);
  React.useEffect(() => () => timers.current.forEach(clearTimeout), []);
  React.useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [messages, typing]);
  const ask = q => {
    if (!q.trim()) return;
    setMessages(ms => [...ms, {
      role: 'user',
      text: q
    }]);
    setInput('');
    setTyping(true);
    const c = CANNED[q] || {
      tools: ['检索经验库'],
      reply: '这是原型演示——该问题的完整回答需要接入真实引擎。试试预设的快捷问题，能看到带工具调用轨迹的完整对话效果。'
    };
    timers.current.push(setTimeout(() => {
      setTyping(false);
      setMessages(ms => [...ms, {
        role: 'ai',
        text: c.reply,
        tools: c.tools,
        action: c.action
      }]);
    }, 900 + Math.random() * 500));
  };
  if (!open) return null;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'fixed',
      top: 0,
      right: 0,
      bottom: 0,
      width: 400,
      maxWidth: '92vw',
      zIndex: 1500,
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--ap-bg-1)',
      borderLeft: '1px solid var(--ap-line)',
      boxShadow: '-16px 0 48px rgba(0,0,0,.5)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '14px 16px',
      borderBottom: '1px solid var(--ap-line-soft)',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 30,
      height: 30,
      borderRadius: 8,
      background: 'var(--ap-violet-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "brain",
    size: 16,
    color: "var(--ap-violet)"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'absolute',
      bottom: -1,
      right: -1,
      width: 8,
      height: 8,
      borderRadius: '50%',
      background: 'var(--ap-mint)',
      border: '2px solid var(--ap-bg-1)'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 700
    }
  }, "Pilot AI"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "\u53EF\u8BFB\u53D6\u5B9E\u65F6\u72B6\u6001 \xB7 \u65E0\u6743\u7ED5\u8FC7\u98CE\u63A7")), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    style: {
      width: 28,
      height: 28,
      borderRadius: 7,
      background: 'var(--ap-bg-3)',
      border: '1px solid var(--ap-line-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      color: 'var(--ap-fg-3)'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "x",
    size: 13
  }))), /*#__PURE__*/React.createElement("div", {
    ref: bodyRef,
    style: {
      flex: 1,
      overflow: 'auto',
      padding: '16px 16px',
      display: 'flex',
      flexDirection: 'column',
      gap: 14
    }
  }, messages.map((m, i) => m.role === 'user' ? /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      alignSelf: 'flex-end',
      maxWidth: '85%',
      background: 'var(--ap-bg-4)',
      borderRadius: '12px 12px 4px 12px',
      padding: '10px 13px',
      fontSize: 13,
      lineHeight: 1.55
    }
  }, m.text) : /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      alignSelf: 'flex-start',
      maxWidth: '92%',
      display: 'flex',
      flexDirection: 'column',
      gap: 6
    }
  }, m.tools?.length > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 3
    }
  }, m.tools.map((t, j) => /*#__PURE__*/React.createElement("div", {
    key: j,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 10.5,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "check",
    size: 10,
    color: "var(--ap-mint)",
    strokeWidth: 2.5
  }), " ", t))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--ap-bg-2)',
      border: '1px solid var(--ap-line-soft)',
      borderRadius: '12px 12px 12px 4px',
      padding: '11px 14px',
      fontSize: 13,
      lineHeight: 1.6,
      color: 'var(--ap-fg-1)',
      whiteSpace: 'pre-line'
    }
  }, m.text), m.action && /*#__PURE__*/React.createElement("button", {
    style: {
      alignSelf: 'flex-start',
      padding: '7px 14px',
      borderRadius: 8,
      border: '1px solid var(--ap-violet)',
      background: 'var(--ap-violet-soft)',
      color: 'var(--ap-violet)',
      fontSize: 12,
      fontWeight: 600,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, m.action))), typing && /*#__PURE__*/React.createElement("div", {
    style: {
      alignSelf: 'flex-start',
      background: 'var(--ap-bg-2)',
      border: '1px solid var(--ap-line-soft)',
      borderRadius: '12px 12px 12px 4px',
      padding: '12px 16px',
      display: 'flex',
      gap: 4
    }
  }, [0, 1, 2].map(i => /*#__PURE__*/React.createElement("span", {
    key: i,
    style: {
      width: 5,
      height: 5,
      borderRadius: '50%',
      background: 'var(--ap-violet)',
      animation: `apblink 1s ${i * 0.18}s infinite`
    }
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 16px 10px',
      display: 'flex',
      flexWrap: 'wrap',
      gap: 6,
      flexShrink: 0
    }
  }, QUICK_PROMPTS.map(q => /*#__PURE__*/React.createElement("div", {
    key: q,
    onClick: () => ask(q),
    style: {
      fontSize: 11,
      padding: '6px 11px',
      borderRadius: 999,
      background: 'var(--ap-bg-2)',
      border: '1px solid var(--ap-line-soft)',
      color: 'var(--ap-fg-3)',
      cursor: 'pointer'
    }
  }, q))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 16px 16px',
      borderTop: '1px solid var(--ap-line-soft)',
      display: 'flex',
      gap: 8,
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("input", {
    value: input,
    onChange: e => setInput(e.target.value),
    onKeyDown: e => e.key === 'Enter' && ask(input),
    placeholder: "\u95EE Pilot AI\u2026",
    style: {
      flex: 1,
      background: 'var(--ap-bg-2)',
      border: '1px solid var(--ap-line)',
      borderRadius: 10,
      padding: '10px 13px',
      color: 'var(--ap-fg-1)',
      fontSize: 13,
      outline: 'none',
      fontFamily: 'inherit'
    }
  }), /*#__PURE__*/React.createElement("button", {
    onClick: () => ask(input),
    style: {
      width: 40,
      borderRadius: 10,
      border: 'none',
      background: 'var(--ap-violet)',
      color: '#fff',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "arrow_up",
    size: 15,
    strokeWidth: 2.2
  }))));
};
Object.assign(window, {
  AIChatDrawer
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/web_app/components/ai_chat.jsx", error: String((e && e.message) || e) }); }

// ui_kits/web_app/components/auth.jsx
try { (() => {
// Auth — login / register / 2FA screens (pre-shell, full page)

const AuthInput = ({
  icon,
  type = 'text',
  value,
  onChange,
  placeholder,
  autoFocus
}) => {
  const [focus, setFocus] = React.useState(false);
  const [show, setShow] = React.useState(false);
  const isPw = type === 'password';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      display: 'flex',
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 13
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: icon,
    size: 15,
    color: focus ? 'var(--ap-mint)' : 'var(--ap-fg-4)'
  })), /*#__PURE__*/React.createElement("input", {
    type: isPw && show ? 'text' : type,
    value: value,
    onChange: e => onChange(e.target.value),
    placeholder: placeholder,
    autoFocus: autoFocus,
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      width: '100%',
      boxSizing: 'border-box',
      background: 'var(--ap-bg-2)',
      border: '1px solid ' + (focus ? 'var(--ap-mint)' : 'var(--ap-line)'),
      boxShadow: focus ? '0 0 0 3px rgba(0,211,149,.1)' : 'none',
      borderRadius: 11,
      padding: '13px 14px 13px 40px',
      paddingRight: isPw ? 44 : 14,
      color: 'var(--ap-fg-1)',
      fontSize: 14,
      outline: 'none',
      fontFamily: 'inherit',
      transition: '.12s'
    }
  }), isPw && /*#__PURE__*/React.createElement("div", {
    onClick: () => setShow(s => !s),
    style: {
      position: 'absolute',
      right: 13,
      cursor: 'pointer',
      display: 'flex'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "eye",
    size: 15,
    color: show ? 'var(--ap-mint)' : 'var(--ap-fg-4)'
  })));
};
const AuthScreen = ({
  onLogin
}) => {
  const [mode, setMode] = React.useState('login'); // login | register | twofa
  const [email, setEmail] = React.useState('');
  const [pw, setPw] = React.useState('');
  const [pw2, setPw2] = React.useState('');
  const [code, setCode] = React.useState(['', '', '', '', '', '']);
  const codeRefs = React.useRef([]);
  const submit = () => {
    if (mode === 'login') {
      setMode('twofa');
    } else if (mode === 'register') {
      setMode('twofa');
    }
  };
  const onCode = (i, v) => {
    if (!/^[0-9]?$/.test(v)) return;
    const next = [...code];
    next[i] = v;
    setCode(next);
    if (v && i < 5) codeRefs.current[i + 1]?.focus();
    if (next.every(c => c !== '')) setTimeout(onLogin, 350);
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'fixed',
      inset: 0,
      display: 'flex',
      background: 'var(--ap-bg-0)',
      zIndex: 100
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      padding: '48px 56px',
      position: 'relative',
      overflow: 'hidden',
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("svg", {
    style: {
      position: 'absolute',
      inset: 0,
      width: '100%',
      height: '100%',
      opacity: .35
    }
  }, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("pattern", {
    id: "authgrid",
    width: "40",
    height: "40",
    patternUnits: "userSpaceOnUse"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M 40 0 L 0 0 0 40",
    fill: "none",
    stroke: "var(--ap-line-soft)",
    strokeWidth: "1"
  }))), /*#__PURE__*/React.createElement("rect", {
    width: "100%",
    height: "100%",
    fill: "url(#authgrid)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 36,
      height: 36,
      borderRadius: 9,
      background: 'linear-gradient(135deg,var(--ap-mint),var(--ap-violet))',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'var(--ap-bg-0)',
      fontWeight: 800,
      fontSize: 17
    }
  }, "\u03B1"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 17,
      fontWeight: 700
    }
  }, "Alpha", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-mint)'
    }
  }, "Pilot"))), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      maxWidth: 440
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 34,
      fontWeight: 700,
      letterSpacing: '-.03em',
      lineHeight: 1.25,
      marginBottom: 16
    }
  }, "AI \u81EA\u4E3B\u4EA4\u6613", /*#__PURE__*/React.createElement("br", null), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-mint)'
    }
  }, "\u5728\u8FB9\u754C\u5185"), "\u8FD0\u884C"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      color: 'var(--ap-fg-3)',
      lineHeight: 1.7
    }
  }, "\u7ED3\u6784\u5316\u51B3\u7B56 \xB7 \u786C\u98CE\u63A7\u5B88\u536B \xB7 \u6267\u884C\u95ED\u73AF \xB7 \u53D7\u63A7\u8FDB\u5316\u3002", /*#__PURE__*/React.createElement("br", null), "\u4E0D\u662F\u53C8\u4E00\u4E2A\u53D1\u4FE1\u53F7\u7684\u52A9\u624B\uFF0C\u800C\u662F\u53EF\u6258\u4ED8\u7684\u4EA4\u6613\u7CFB\u7EDF\u3002"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 16,
      marginTop: 28
    }
  }, [['248', '累计交易'], ['57%', '胜率'], ['1.84', 'Sharpe'], ['−4.2%', '最大回撤']].map(([v, l]) => /*#__PURE__*/React.createElement("div", {
    key: l
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 20,
      fontWeight: 700,
      color: 'var(--ap-fg-1)'
    }
  }, v), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-fg-4)',
      marginTop: 2
    }
  }, l))))), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      fontSize: 11,
      color: 'var(--ap-fg-5)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "Binance USDT-M \xB7 Testnet & Mainnet \xB7 v0.1")), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 460,
      flexShrink: 0,
      background: 'var(--ap-bg-1)',
      borderLeft: '1px solid var(--ap-line)',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      padding: '0 56px'
    }
  }, mode !== 'twofa' ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 22,
      fontWeight: 700,
      marginBottom: 6
    }
  }, mode === 'login' ? '欢迎回来' : '创建账户'), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: 'var(--ap-fg-3)',
      marginBottom: 28
    }
  }, mode === 'login' ? '登录以进入你的交易控制台' : '注册后需管理员批准并分配角色'), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(AuthInput, {
    icon: "mail",
    value: email,
    onChange: setEmail,
    placeholder: "\u90AE\u7BB1",
    autoFocus: true
  }), /*#__PURE__*/React.createElement(AuthInput, {
    icon: "lock",
    type: "password",
    value: pw,
    onChange: setPw,
    placeholder: "\u5BC6\u7801"
  }), mode === 'register' && /*#__PURE__*/React.createElement(AuthInput, {
    icon: "lock",
    type: "password",
    value: pw2,
    onChange: setPw2,
    placeholder: "\u786E\u8BA4\u5BC6\u7801"
  })), mode === 'login' && /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'right',
      marginTop: 10
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-4)',
      cursor: 'pointer'
    }
  }, "\u5FD8\u8BB0\u5BC6\u7801\uFF1F")), /*#__PURE__*/React.createElement("button", {
    onClick: submit,
    style: {
      marginTop: 22,
      width: '100%',
      padding: '13px 0',
      borderRadius: 11,
      border: 'none',
      background: 'var(--ap-mint)',
      color: 'var(--ap-bg-0)',
      fontSize: 14,
      fontWeight: 700,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, mode === 'login' ? '登录' : '注册'), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      margin: '22px 0'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      height: 1,
      background: 'var(--ap-line-soft)'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-5)'
    }
  }, "\u6216"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      height: 1,
      background: 'var(--ap-line-soft)'
    }
  })), /*#__PURE__*/React.createElement("button", {
    onClick: onLogin,
    style: {
      width: '100%',
      padding: '12px 0',
      borderRadius: 11,
      border: '1px solid var(--ap-line)',
      background: 'var(--ap-bg-2)',
      color: 'var(--ap-fg-2)',
      fontSize: 13,
      fontWeight: 600,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u4EE5\u6F14\u793A\u8D26\u6237\u8FDB\u5165 \u2192"), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'center',
      marginTop: 24,
      fontSize: 12.5,
      color: 'var(--ap-fg-4)'
    }
  }, mode === 'login' ? '还没有账户？' : '已有账户？', /*#__PURE__*/React.createElement("span", {
    onClick: () => setMode(mode === 'login' ? 'register' : 'login'),
    style: {
      color: 'var(--ap-mint)',
      cursor: 'pointer',
      fontWeight: 600,
      marginLeft: 6
    }
  }, mode === 'login' ? '注册' : '登录'))) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    onClick: () => setMode('login'),
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      color: 'var(--ap-fg-4)',
      fontSize: 12,
      cursor: 'pointer',
      marginBottom: 26
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      transform: 'rotate(180deg)'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "chevron_right",
    size: 12
  })), " \u8FD4\u56DE"), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 44,
      height: 44,
      borderRadius: 11,
      background: 'var(--ap-mint-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      marginBottom: 18
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "shield",
    size: 20,
    color: "var(--ap-mint)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 22,
      fontWeight: 700,
      marginBottom: 6
    }
  }, "\u53CC\u91CD\u9A8C\u8BC1"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: 'var(--ap-fg-3)',
      marginBottom: 26
    }
  }, "\u8F93\u5165\u9A8C\u8BC1\u5668 App \u4E2D\u7684 6 \u4F4D\u52A8\u6001\u7801", /*#__PURE__*/React.createElement("br", null), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11,
      color: 'var(--ap-fg-4)'
    }
  }, "\u6F14\u793A\u63D0\u793A\uFF1A\u8F93\u5165\u4EFB\u610F 6 \u4F4D\u6570\u5B57")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 10,
      marginBottom: 24
    }
  }, code.map((c, i) => /*#__PURE__*/React.createElement("input", {
    key: i,
    ref: el => codeRefs.current[i] = el,
    value: c,
    onChange: e => onCode(i, e.target.value),
    autoFocus: i === 0,
    maxLength: 1,
    inputMode: "numeric",
    style: {
      width: 48,
      height: 56,
      textAlign: 'center',
      fontSize: 22,
      fontWeight: 700,
      fontFamily: 'var(--ap-font-mono)',
      background: 'var(--ap-bg-2)',
      border: '1px solid ' + (c ? 'var(--ap-mint)' : 'var(--ap-line)'),
      borderRadius: 11,
      color: 'var(--ap-fg-1)',
      outline: 'none'
    }
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-4)'
    }
  }, "\u6536\u4E0D\u5230\u9A8C\u8BC1\u7801\uFF1F", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-mint)',
      cursor: 'pointer',
      fontWeight: 600
    }
  }, "\u4F7F\u7528\u6062\u590D\u7801")))));
};
Object.assign(window, {
  AuthScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/web_app/components/auth.jsx", error: String((e && e.message) || e) }); }

// ui_kits/web_app/components/enhancements.jsx
try { (() => {
// AlphaPilot Web — interaction & state enhancements
// HaltBanner · StreamingDecision · WSparkLive · CommandPalette · AnimatedNumber · EmptyState

// ============================================================
// AnimatedNumber — count-up + color flash on change
// ============================================================
const AnimatedNumber = ({
  value,
  format = v => v.toFixed(2),
  prefix = '',
  suffix = '',
  style = {},
  motion = true,
  duration = 600
}) => {
  const [display, setDisplay] = React.useState(value);
  const [flash, setFlash] = React.useState(null); // 'up' | 'down'
  const prev = React.useRef(value);
  const raf = React.useRef(null);
  React.useEffect(() => {
    if (prev.current === value) return;
    const from = prev.current,
      to = value,
      start = performance.now();
    setFlash(to >= from ? 'up' : 'down');
    if (!motion) {
      setDisplay(to);
      prev.current = to;
      const t = setTimeout(() => setFlash(null), 500);
      return () => clearTimeout(t);
    }
    const tick = now => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + (to - from) * eased);
      if (t < 1) raf.current = requestAnimationFrame(tick);else {
        prev.current = to;
        setTimeout(() => setFlash(null), 400);
      }
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [value, motion, duration]);
  const flashColor = flash === 'up' ? 'var(--ap-mint)' : flash === 'down' ? 'var(--ap-rose)' : undefined;
  return /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontVariantNumeric: 'tabular-nums',
      transition: 'color .3s, transform .3s',
      color: flashColor || style.color,
      transform: flash && motion ? 'scale(1.015)' : 'scale(1)',
      display: 'inline-block',
      ...style
    }
  }, prefix, format(display), suffix);
};

// ============================================================
// HaltBanner — global circuit-breaker / warning ribbon
// ============================================================
const HaltBanner = ({
  riskState,
  regime,
  dayLossPct,
  onAck
}) => {
  if (riskState === 'OK') return null;
  const halted = riskState === 'HALTED';
  const c = halted ? 'var(--ap-rose)' : 'var(--ap-amber)';
  const soft = halted ? 'var(--ap-rose-soft)' : 'var(--ap-amber-soft)';
  return /*#__PURE__*/React.createElement("div", {
    role: "alert",
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 14,
      padding: '14px 18px',
      borderRadius: 12,
      background: soft,
      border: `1px solid ${c}`,
      marginBottom: 20,
      position: 'relative',
      overflow: 'hidden',
      boxShadow: halted ? '0 0 32px rgba(255,77,109,.18)' : 'none'
    }
  }, halted && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      background: `repeating-linear-gradient(45deg, transparent, transparent 12px, ${c}0a 12px, ${c}0a 24px)`,
      pointerEvents: 'none'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 36,
      height: 36,
      borderRadius: 9,
      background: c,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
      boxShadow: `0 0 16px ${c}66`
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: halted ? 'alert' : 'alert',
    size: 18,
    color: "var(--ap-bg-0)",
    strokeWidth: 2.4
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0,
      position: 'relative'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      color: c,
      marginBottom: 2
    }
  }, halted ? '日亏损熔断已触发 · 新开仓已暂停' : '接近熔断阈值 · 风险升高'), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-2)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, halted ? `日损 ${wfmtPct(dayLossPct)} ≥ 阈值 −2.00% · 仅允许平仓与风险管理 · regime ${regime}` : `日损 ${wfmtPct(dayLossPct)} · 距阈值 ${Math.abs(-2.0 - dayLossPct).toFixed(2)}% · regime ${regime}`)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      position: 'relative',
      flexShrink: 0
    }
  }, halted && /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '8px 14px',
      borderRadius: 8,
      border: `1px solid ${c}`,
      background: 'transparent',
      color: c,
      fontSize: 12,
      fontWeight: 600,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u67E5\u770B\u98CE\u63A7\u65E5\u5FD7"), /*#__PURE__*/React.createElement("button", {
    onClick: onAck,
    style: {
      padding: '8px 14px',
      borderRadius: 8,
      border: 'none',
      background: c,
      color: 'var(--ap-bg-0)',
      fontSize: 12,
      fontWeight: 700,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, halted ? '手动恢复' : '我知道了')));
};

// ============================================================
// StreamingDecision — plays the decision pipeline live, then
// reveals the full card. Replayable.
// ============================================================
const STREAM_STAGES = [{
  k: 'snapshot',
  label: '采集市场快照',
  detail: 'regime · K线 · 特征因子',
  color: 'var(--ap-cyan)',
  icon: 'bolt',
  ms: 700
}, {
  k: 'reason',
  label: 'AI 推理中',
  detail: 'LLM + 规则引擎评估',
  color: 'var(--ap-violet)',
  icon: 'brain',
  ms: 1100
}, {
  k: 'guard',
  label: '守卫检查',
  detail: '8 项硬风控校验',
  color: 'var(--ap-mint)',
  icon: 'shield',
  ms: 800
}, {
  k: 'verdict',
  label: '风险裁决',
  detail: '允许 / 回退 HOLD',
  color: 'var(--ap-mint)',
  icon: 'check',
  ms: 600
}, {
  k: 'exec',
  label: '执行下单',
  detail: 'Binance 市价 + SL/TP',
  color: 'var(--ap-mint)',
  icon: 'play',
  ms: 700
}];
const StreamingDecision = ({
  d,
  variant,
  motion = true,
  halted = false
}) => {
  const [stage, setStage] = React.useState(motion ? -1 : 99);
  const [done, setDone] = React.useState(!motion);
  const timers = React.useRef([]);
  const play = React.useCallback(() => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setDone(false);
    setStage(0);
    let acc = 0;
    STREAM_STAGES.forEach((s, i) => {
      acc += s.ms;
      timers.current.push(setTimeout(() => {
        if (i === STREAM_STAGES.length - 1) {
          setStage(99);
          setDone(true);
        } else setStage(i + 1);
      }, acc));
    });
  }, []);
  React.useEffect(() => {
    if (motion) {
      play();
    } else {
      setStage(99);
      setDone(true);
    }
    return () => timers.current.forEach(clearTimeout);
    // eslint-disable-next-line
  }, [motion, d?.id]);
  if (done) {
    return /*#__PURE__*/React.createElement("div", {
      style: {
        position: 'relative'
      }
    }, motion && /*#__PURE__*/React.createElement("button", {
      onClick: play,
      title: "\u91CD\u653E\u51B3\u7B56\u8FC7\u7A0B",
      style: {
        position: 'absolute',
        top: 14,
        right: 16,
        zIndex: 5,
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '5px 10px',
        borderRadius: 7,
        background: 'var(--ap-bg-3)',
        border: '1px solid var(--ap-line)',
        color: 'var(--ap-fg-3)',
        fontSize: 11,
        cursor: 'pointer',
        fontFamily: 'var(--ap-font-mono)'
      }
    }, /*#__PURE__*/React.createElement(Icon, {
      name: "play",
      size: 11
    }), " \u91CD\u653E"), /*#__PURE__*/React.createElement(AIDecisionCard, {
      d: d,
      variant: variant
    }));
  }

  // streaming view
  return /*#__PURE__*/React.createElement(WCard, {
    glow: true
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      marginBottom: 18
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 28,
      height: 28,
      borderRadius: 8,
      background: 'var(--ap-violet-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "brain",
    size: 16,
    color: "var(--ap-violet)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-violet)',
      letterSpacing: '.1em',
      fontWeight: 700,
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, "AI DECISION", /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      gap: 3
    }
  }, [0, 1, 2].map(i => /*#__PURE__*/React.createElement("span", {
    key: i,
    style: {
      width: 4,
      height: 4,
      borderRadius: '50%',
      background: 'var(--ap-violet)',
      animation: `apblink 1s ${i * 0.18}s infinite`
    }
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11,
      color: 'var(--ap-fg-3)'
    }
  }, d.sym, " \xB7 ", d.tf, " \xB7 \u5B9E\u65F6\u63A8\u7406\u4E2D\u2026"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 2,
      position: 'relative',
      paddingLeft: 4
    }
  }, STREAM_STAGES.map((s, i) => {
    const active = i === stage;
    const complete = i < stage;
    const pending = i > stage;
    return /*#__PURE__*/React.createElement("div", {
      key: s.k,
      style: {
        display: 'flex',
        gap: 14,
        padding: '10px 0',
        opacity: pending ? 0.35 : 1,
        transition: 'opacity .3s',
        position: 'relative'
      }
    }, i < STREAM_STAGES.length - 1 && /*#__PURE__*/React.createElement("div", {
      style: {
        position: 'absolute',
        left: 13,
        top: 30,
        bottom: -4,
        width: 1.5,
        background: complete ? s.color : 'var(--ap-line)',
        opacity: .5
      }
    }), /*#__PURE__*/React.createElement("div", {
      style: {
        width: 26,
        height: 26,
        borderRadius: '50%',
        flexShrink: 0,
        zIndex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: complete ? s.color : active ? 'var(--ap-bg-3)' : 'var(--ap-bg-3)',
        border: active ? `2px solid ${s.color}` : complete ? 'none' : '1px solid var(--ap-line)',
        boxShadow: active ? `0 0 14px ${s.color}66` : 'none',
        animation: active ? 'appulse 1.2s infinite' : 'none'
      }
    }, complete ? /*#__PURE__*/React.createElement(Icon, {
      name: "check",
      size: 13,
      color: "var(--ap-bg-0)",
      strokeWidth: 2.6
    }) : /*#__PURE__*/React.createElement(Icon, {
      name: s.icon,
      size: 12,
      color: active ? s.color : 'var(--ap-fg-4)',
      strokeWidth: 2
    })), /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 1,
        paddingTop: 2
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 13,
        fontWeight: 600,
        color: active ? s.color : 'var(--ap-fg-1)'
      }
    }, s.label, active && /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: 'var(--ap-font-mono)',
        fontWeight: 400
      }
    }, " \u2026")), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11.5,
        color: 'var(--ap-fg-3)',
        fontFamily: 'var(--ap-font-mono)',
        marginTop: 1
      }
    }, s.detail)));
  })));
};

// ============================================================
// WSparkLive — interactive area chart w/ crosshair + tooltip
// ============================================================
const WSparkLive = ({
  data,
  h = 160,
  color = 'var(--ap-mint)',
  gridId = 'wsl',
  valuePrefix = '$',
  baseTs = Date.now()
}) => {
  const wrapRef = React.useRef(null);
  const [hover, setHover] = React.useState(null); // {i, x, y, value}
  const [w, setW] = React.useState(700);
  React.useEffect(() => {
    const ro = new ResizeObserver(es => {
      for (const e of es) setW(e.contentRect.width);
    });
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);
  const min = Math.min(...data),
    max = Math.max(...data),
    r = max - min || 1;
  const px = i => i / (data.length - 1) * w;
  const py = v => h - (v - min) / r * (h - 16) - 8;
  const pts = data.map((v, i) => [px(i), py(v)]);
  const path = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
  const area = path + ` L ${w} ${h} L 0 ${h} Z`;
  const onMove = e => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const i = Math.max(0, Math.min(data.length - 1, Math.round(x / w * (data.length - 1))));
    setHover({
      i,
      x: px(i),
      y: py(data[i]),
      value: data[i]
    });
  };
  const change = hover ? (hover.value - data[0]) / data[0] * 100 : null;
  return /*#__PURE__*/React.createElement("div", {
    ref: wrapRef,
    style: {
      position: 'relative',
      width: '100%',
      userSelect: 'none'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "100%",
    height: h,
    viewBox: `0 0 ${w} ${h}`,
    preserveAspectRatio: "none",
    style: {
      display: 'block'
    },
    onMouseMove: onMove,
    onMouseLeave: () => setHover(null)
  }, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("linearGradient", {
    id: gridId,
    x1: "0",
    x2: "0",
    y1: "0",
    y2: "1"
  }, /*#__PURE__*/React.createElement("stop", {
    offset: "0",
    stopColor: color,
    stopOpacity: ".32"
  }), /*#__PURE__*/React.createElement("stop", {
    offset: "1",
    stopColor: color,
    stopOpacity: "0"
  }))), [0.25, 0.5, 0.75].map(t => /*#__PURE__*/React.createElement("line", {
    key: t,
    x1: "0",
    x2: w,
    y1: t * h,
    y2: t * h,
    stroke: "var(--ap-line-soft)",
    strokeWidth: "1"
  })), /*#__PURE__*/React.createElement("path", {
    d: area,
    fill: `url(#${gridId})`
  }), /*#__PURE__*/React.createElement("path", {
    d: path,
    stroke: color,
    strokeWidth: "1.8",
    fill: "none",
    strokeLinejoin: "round",
    vectorEffect: "non-scaling-stroke"
  }), hover && /*#__PURE__*/React.createElement("g", null, /*#__PURE__*/React.createElement("line", {
    x1: hover.x,
    x2: hover.x,
    y1: "0",
    y2: h,
    stroke: "var(--ap-fg-3)",
    strokeWidth: "1",
    strokeDasharray: "3 3",
    vectorEffect: "non-scaling-stroke"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: hover.x,
    cy: hover.y,
    r: "4",
    fill: color,
    stroke: "var(--ap-bg-1)",
    strokeWidth: "2"
  }))), hover && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 6,
      left: Math.max(4, Math.min(hover.x / w * 100, 78)) + '%',
      transform: 'translateX(-50%)',
      background: 'var(--ap-bg-4)',
      border: '1px solid var(--ap-line)',
      borderRadius: 8,
      padding: '6px 10px',
      pointerEvents: 'none',
      boxShadow: 'var(--ap-shadow-2)',
      whiteSpace: 'nowrap',
      zIndex: 2
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 13,
      fontWeight: 700,
      color: 'var(--ap-fg-1)'
    }
  }, valuePrefix, wfmt(hover.value)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 10,
      color: change >= 0 ? 'var(--ap-mint)' : 'var(--ap-rose)'
    }
  }, change >= 0 ? '▲' : '▼', " ", wfmtPct(change), " \u81EA\u8D77\u70B9")));
};

// ============================================================
// CommandPalette — ⌘K
// ============================================================
const CommandPalette = ({
  open,
  onClose,
  onNav,
  onSetVariant,
  onSetScene,
  onOpenChat
}) => {
  const [q, setQ] = React.useState('');
  const inputRef = React.useRef(null);
  const [sel, setSel] = React.useState(0);
  const commands = React.useMemo(() => [{
    group: '导航',
    label: '主控制台',
    hint: 'Cockpit',
    icon: 'dashboard',
    run: () => onNav('dashboard')
  }, {
    group: '导航',
    label: '行情',
    hint: 'Market',
    icon: 'chart',
    run: () => onNav('market')
  }, {
    group: '导航',
    label: 'AI 决策流',
    hint: 'Decisions',
    icon: 'brain',
    run: () => onNav('ai')
  }, {
    group: '导航',
    label: '持仓与订单',
    hint: 'Positions',
    icon: 'layers',
    run: () => onNav('positions')
  }, {
    group: '导航',
    label: '回测与绩效',
    hint: 'Performance',
    icon: 'chart',
    run: () => onNav('backtest')
  }, {
    group: '导航',
    label: '策略与风控',
    hint: 'Risk',
    icon: 'shield',
    run: () => onNav('risk')
  }, {
    group: '导航',
    label: '策略实验室',
    hint: 'Shadow Lab',
    icon: 'book',
    run: () => onNav('lab')
  }, {
    group: '导航',
    label: '审计日志',
    hint: 'Audit',
    icon: 'list',
    run: () => onNav('audit')
  }, {
    group: '导航',
    label: '后台管理',
    hint: 'Admin',
    icon: 'users',
    run: () => onNav('admin')
  }, {
    group: 'AI',
    label: '问 Pilot AI',
    hint: '⌘J',
    icon: 'brain',
    run: () => onOpenChat?.()
  }, {
    group: '交易对',
    label: 'BTCUSDT',
    hint: '持仓 +2.14%',
    icon: 'circle',
    run: () => onNav('positions')
  }, {
    group: '交易对',
    label: 'ETHUSDT',
    hint: '持仓 −0.62%',
    icon: 'circle',
    run: () => onNav('positions')
  }, {
    group: 'AI 卡片样式',
    label: 'Stepper 流水线',
    hint: 'variant',
    icon: 'bolt',
    run: () => onSetVariant('stepper')
  }, {
    group: 'AI 卡片样式',
    label: 'Timeline 时间线',
    hint: 'variant',
    icon: 'clock',
    run: () => onSetVariant('timeline')
  }, {
    group: 'AI 卡片样式',
    label: 'Graph 节点图',
    hint: 'variant',
    icon: 'layers',
    run: () => onSetVariant('graph')
  }, {
    group: '场景模拟',
    label: '盈利 · 风控正常',
    hint: 'scene',
    icon: 'check',
    run: () => onSetScene('profit')
  }, {
    group: '场景模拟',
    label: '接近熔断阈值',
    hint: 'scene',
    icon: 'alert',
    run: () => onSetScene('warn')
  }, {
    group: '场景模拟',
    label: '日亏熔断已触发',
    hint: 'scene',
    icon: 'alert',
    run: () => onSetScene('halted')
  }], [onNav, onSetVariant, onSetScene, onOpenChat]);
  const filtered = commands.filter(c => !q || (c.label + c.hint + c.group).toLowerCase().includes(q.toLowerCase()));
  React.useEffect(() => {
    if (open) {
      setQ('');
      setSel(0);
      setTimeout(() => inputRef.current?.focus(), 30);
    }
  }, [open]);
  React.useEffect(() => {
    setSel(0);
  }, [q]);
  const onKey = e => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSel(s => Math.min(filtered.length - 1, s + 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSel(s => Math.max(0, s - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      filtered[sel]?.run();
      onClose();
    } else if (e.key === 'Escape') {
      onClose();
    }
  };
  if (!open) return null;
  let lastGroup = null;
  return /*#__PURE__*/React.createElement("div", {
    onMouseDown: onClose,
    style: {
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,.6)',
      backdropFilter: 'blur(4px)',
      zIndex: 2000,
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'flex-start',
      paddingTop: '12vh'
    }
  }, /*#__PURE__*/React.createElement("div", {
    onMouseDown: e => e.stopPropagation(),
    style: {
      width: 560,
      maxWidth: '90vw',
      background: 'var(--ap-bg-2)',
      border: '1px solid var(--ap-line)',
      borderRadius: 14,
      boxShadow: 'var(--ap-shadow-3)',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '14px 16px',
      borderBottom: '1px solid var(--ap-line-soft)'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "search",
    size: 16,
    color: "var(--ap-fg-3)"
  }), /*#__PURE__*/React.createElement("input", {
    ref: inputRef,
    value: q,
    onChange: e => setQ(e.target.value),
    onKeyDown: onKey,
    placeholder: "\u641C\u7D22\u9875\u9762\u3001\u4EA4\u6613\u5BF9\u3001\u547D\u4EE4\u2026",
    style: {
      flex: 1,
      background: 'transparent',
      border: 'none',
      outline: 'none',
      color: 'var(--ap-fg-1)',
      fontSize: 15,
      fontFamily: 'inherit'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 10,
      color: 'var(--ap-fg-4)',
      background: 'var(--ap-bg-3)',
      padding: '2px 6px',
      borderRadius: 4,
      border: '1px solid var(--ap-line)'
    }
  }, "ESC")), /*#__PURE__*/React.createElement("div", {
    style: {
      maxHeight: 360,
      overflow: 'auto',
      padding: 6
    }
  }, filtered.length === 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '24px',
      textAlign: 'center',
      color: 'var(--ap-fg-4)',
      fontSize: 13
    }
  }, "\u65E0\u5339\u914D\u7ED3\u679C"), filtered.map((c, i) => {
    const showGroup = c.group !== lastGroup;
    lastGroup = c.group;
    const active = i === sel;
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: i
    }, showGroup && /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 10,
        color: 'var(--ap-fg-4)',
        letterSpacing: '.08em',
        textTransform: 'uppercase',
        padding: '10px 10px 4px',
        fontWeight: 600
      }
    }, c.group), /*#__PURE__*/React.createElement("div", {
      onMouseEnter: () => setSel(i),
      onClick: () => {
        c.run();
        onClose();
      },
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '9px 10px',
        borderRadius: 8,
        cursor: 'pointer',
        background: active ? 'var(--ap-bg-3)' : 'transparent'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        width: 24,
        height: 24,
        borderRadius: 6,
        background: 'var(--ap-bg-3)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }
    }, /*#__PURE__*/React.createElement(Icon, {
      name: c.icon,
      size: 13,
      color: active ? 'var(--ap-mint)' : 'var(--ap-fg-3)'
    })), /*#__PURE__*/React.createElement("span", {
      style: {
        flex: 1,
        fontSize: 13,
        color: 'var(--ap-fg-1)'
      }
    }, c.label), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 11,
        color: 'var(--ap-fg-4)',
        fontFamily: 'var(--ap-font-mono)'
      }
    }, c.hint), active && /*#__PURE__*/React.createElement(Icon, {
      name: "chevron_right",
      size: 13,
      color: "var(--ap-fg-3)"
    })));
  }))));
};

// ============================================================
// EmptyState
// ============================================================
const EmptyState = ({
  icon = 'circle',
  title,
  sub
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '48px 24px',
    textAlign: 'center',
    gap: 10
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    width: 48,
    height: 48,
    borderRadius: 12,
    background: 'var(--ap-bg-3)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  }
}, /*#__PURE__*/React.createElement(Icon, {
  name: icon,
  size: 22,
  color: "var(--ap-fg-4)"
})), /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 14,
    fontWeight: 600,
    color: 'var(--ap-fg-2)'
  }
}, title), sub && /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 12,
    color: 'var(--ap-fg-4)',
    maxWidth: 280
  }
}, sub));
Object.assign(window, {
  AnimatedNumber,
  HaltBanner,
  StreamingDecision,
  WSparkLive,
  CommandPalette,
  EmptyState,
  STREAM_STAGES
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/web_app/components/enhancements.jsx", error: String((e && e.message) || e) }); }

// ui_kits/web_app/components/lab.jsx
try { (() => {
// Strategy Lab — Shadow Mode (受控进化): candidates run in shadow, compare, promote/rollback

const LAB_CANDIDATES = [{
  id: 'cand_a3f2',
  name: '趋势跟随 v2.1',
  base: '趋势跟随 v2.0（当前线上）',
  change: '入场增加 4h 级别趋势过滤；ATR 止损从 2.0x 收紧到 1.6x',
  origin: '经验库归因 · 12 个亏损案例聚类',
  stage: 'shadow',
  day: 9,
  total: 14,
  shadow: {
    trades: 31,
    win: 64,
    pnl: 4.21,
    sharpe: 2.08,
    dd: -1.8
  },
  live: {
    trades: 29,
    win: 55,
    pnl: 2.87,
    sharpe: 1.84,
    dd: -3.1
  },
  verdict: 'better'
}, {
  id: 'cand_b7c1',
  name: '突破确认 v1.3',
  base: '突破确认 v1.2（当前停用）',
  change: '突破量能阈值 1.4x → 1.8x；增加假突破回撤检测',
  origin: 'AI 自主提案 · 周复盘',
  stage: 'shadow',
  day: 3,
  total: 14,
  shadow: {
    trades: 8,
    win: 50,
    pnl: -0.42,
    sharpe: 0.61,
    dd: -1.2
  },
  live: {
    trades: 8,
    win: 50,
    pnl: -0.38,
    sharpe: 0.66,
    dd: -1.1
  },
  verdict: 'neutral'
}, {
  id: 'cand_c9d4',
  name: '资金费率套利 v0.1',
  base: '新策略（无基线）',
  change: '资金费率极值时反向持仓收取费率；严格 delta 中性',
  origin: '用户提案 · 待验证',
  stage: 'queued',
  day: 0,
  total: 14,
  shadow: null,
  live: null,
  verdict: null
}];
const HISTORY = [{
  t: '06-28 14:00',
  name: '趋势跟随 v2.0',
  event: 'promote',
  note: '影子期 14 天 · Sharpe 1.62→1.84 · 人工批准上线'
}, {
  t: '06-15 09:30',
  name: '均值回归 v0.4',
  event: 'rollback',
  note: '灰度期回撤 −3.4% 触发自动回滚 · 已归档'
}, {
  t: '06-02 11:00',
  name: '趋势跟随 v1.9',
  event: 'retire',
  note: '被 v2.0 替代 · 保留 90 天可回退'
}];
const StageBadge = ({
  stage
}) => {
  const cfg = {
    shadow: {
      l: 'SHADOW 影子运行',
      tone: 'violet'
    },
    queued: {
      l: 'QUEUED 排队中',
      tone: 'default'
    },
    canary: {
      l: 'CANARY 灰度',
      tone: 'amber'
    },
    live: {
      l: 'LIVE 线上',
      tone: 'mint'
    }
  }[stage];
  return /*#__PURE__*/React.createElement(WPill, {
    tone: cfg.tone
  }, cfg.l);
};
const CompareRow = ({
  label,
  shadow,
  live,
  better,
  fmt = v => v,
  suffix = ''
}) => {
  const sBetter = better === 'higher' ? shadow > live : shadow < live;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '90px 1fr 1fr',
      gap: 8,
      padding: '7px 0',
      borderBottom: '1px solid var(--ap-line-soft)',
      fontSize: 11.5,
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-4)'
    }
  }, label), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontWeight: 600,
      color: sBetter ? 'var(--ap-mint)' : 'var(--ap-fg-1)'
    }
  }, fmt(shadow), suffix, sBetter && ' ▲'), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      color: 'var(--ap-fg-3)'
    }
  }, fmt(live), suffix));
};
const CandidateCard = ({
  c
}) => {
  const isQueued = c.stage === 'queued';
  return /*#__PURE__*/React.createElement(WCard, {
    style: {
      borderColor: c.verdict === 'better' ? 'rgba(124,92,255,.4)' : 'var(--ap-line-soft)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-start',
      gap: 12,
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 34,
      height: 34,
      borderRadius: 9,
      background: 'var(--ap-violet-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "layers",
    size: 16,
    color: "var(--ap-violet)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      fontWeight: 700
    }
  }, c.name), /*#__PURE__*/React.createElement(StageBadge, {
    stage: c.stage
  }), c.verdict === 'better' && /*#__PURE__*/React.createElement(WPill, {
    tone: "mint"
  }, "\u4F18\u4E8E\u7EBF\u4E0A")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)',
      marginTop: 2
    }
  }, c.id, " \xB7 \u57FA\u7EBF: ", c.base))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--ap-bg-3)',
      borderRadius: 8,
      padding: '10px 12px',
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-violet)',
      letterSpacing: '.06em',
      fontWeight: 700,
      marginBottom: 4
    }
  }, "\u53D8\u66F4\u5185\u5BB9"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12.5,
      color: 'var(--ap-fg-2)',
      lineHeight: 1.55
    }
  }, c.change), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-fg-4)',
      marginTop: 6,
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "\u6765\u6E90 \xB7 ", c.origin)), isQueued ? /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      fontSize: 12,
      color: 'var(--ap-fg-3)'
    }
  }, "\u7B49\u5F85\u5F71\u5B50\u69FD\u4F4D \xB7 \u9884\u8BA1\u660E\u65E5\u5F00\u59CB 14 \u5929\u5F71\u5B50\u8FD0\u884C"), /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '8px 14px',
      borderRadius: 8,
      border: '1px solid var(--ap-violet)',
      background: 'var(--ap-violet-soft)',
      color: 'var(--ap-violet)',
      fontSize: 12,
      fontWeight: 600,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u7ACB\u5373\u5F00\u59CB")) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      fontSize: 10.5,
      fontFamily: 'var(--ap-font-mono)',
      color: 'var(--ap-fg-3)',
      marginBottom: 5
    }
  }, /*#__PURE__*/React.createElement("span", null, "\u5F71\u5B50\u8FD0\u884C \u7B2C ", c.day, "/", c.total, " \u5929"), /*#__PURE__*/React.createElement("span", null, Math.round(c.day / c.total * 100), "%")), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 5,
      background: 'var(--ap-bg-3)',
      borderRadius: 3,
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: c.day / c.total * 100 + '%',
      height: '100%',
      background: 'var(--ap-violet)',
      borderRadius: 3,
      boxShadow: '0 0 8px var(--ap-violet-glow)'
    }
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '90px 1fr 1fr',
      gap: 8,
      padding: '4px 0 6px',
      fontSize: 10,
      color: 'var(--ap-fg-4)',
      letterSpacing: '.06em',
      textTransform: 'uppercase'
    }
  }, /*#__PURE__*/React.createElement("span", null), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-violet)'
    }
  }, "\u5F71\u5B50 (\u6A21\u62DF)"), /*#__PURE__*/React.createElement("span", null, "\u7EBF\u4E0A (\u771F\u5B9E)")), /*#__PURE__*/React.createElement(CompareRow, {
    label: "\u4EA4\u6613\u6570",
    shadow: c.shadow.trades,
    live: c.live.trades,
    better: "higher"
  }), /*#__PURE__*/React.createElement(CompareRow, {
    label: "\u80DC\u7387",
    shadow: c.shadow.win,
    live: c.live.win,
    better: "higher",
    suffix: "%"
  }), /*#__PURE__*/React.createElement(CompareRow, {
    label: "\u51C0\u6536\u76CA",
    shadow: c.shadow.pnl,
    live: c.live.pnl,
    better: "higher",
    fmt: v => (v >= 0 ? '+' : '') + v.toFixed(2),
    suffix: "%"
  }), /*#__PURE__*/React.createElement(CompareRow, {
    label: "Sharpe",
    shadow: c.shadow.sharpe,
    live: c.live.sharpe,
    better: "higher",
    fmt: v => v.toFixed(2)
  }), /*#__PURE__*/React.createElement(CompareRow, {
    label: "\u6700\u5927\u56DE\u64A4",
    shadow: c.shadow.dd,
    live: c.live.dd,
    better: "lower",
    fmt: v => v.toFixed(1),
    suffix: "%"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      marginTop: 14,
      alignItems: 'center'
    }
  }, c.verdict === 'better' && c.day >= c.total * 0.6 ? /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '9px 16px',
      borderRadius: 9,
      border: 'none',
      background: 'var(--ap-mint)',
      color: 'var(--ap-bg-0)',
      fontSize: 12,
      fontWeight: 700,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u7533\u8BF7\u7070\u5EA6\u4E0A\u7EBF \u2192") : /*#__PURE__*/React.createElement("button", {
    disabled: true,
    style: {
      padding: '9px 16px',
      borderRadius: 9,
      border: '1px solid var(--ap-line)',
      background: 'var(--ap-bg-3)',
      color: 'var(--ap-fg-4)',
      fontSize: 12,
      fontWeight: 600,
      cursor: 'not-allowed',
      fontFamily: 'inherit'
    }
  }, c.verdict === 'better' ? '影子期未满 60%' : '表现未达标'), /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '9px 14px',
      borderRadius: 9,
      border: '1px solid var(--ap-line)',
      background: 'transparent',
      color: 'var(--ap-fg-3)',
      fontSize: 12,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u7EC8\u6B62"), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      fontSize: 10,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "\u4E0A\u7EBF\u9700\u4EBA\u5DE5\u6279\u51C6"))));
};
const WLabPage = () => /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    flexDirection: 'column',
    gap: 20,
    maxWidth: 1100
  }
}, /*#__PURE__*/React.createElement(WCard, null, /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    gap: 14,
    alignItems: 'flex-start'
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    width: 34,
    height: 34,
    borderRadius: 9,
    background: 'var(--ap-violet-soft)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0
  }
}, /*#__PURE__*/React.createElement(Icon, {
  name: "book",
  size: 17,
  color: "var(--ap-violet)"
})), /*#__PURE__*/React.createElement("div", {
  style: {
    flex: 1
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 14,
    fontWeight: 700,
    marginBottom: 4
  }
}, "\u53D7\u63A7\u8FDB\u5316 \xB7 Shadow Mode"), /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 12.5,
    color: 'var(--ap-fg-3)',
    lineHeight: 1.6
  }
}, "AI \u6216\u4EBA\u5DE5\u63D0\u51FA\u7684\u7B56\u7565\u6539\u8FDB\u4E0D\u4F1A\u76F4\u63A5\u4E0A\u7EBF\u3002\u5019\u9009\u7248\u672C\u5148\u4EE5", /*#__PURE__*/React.createElement("b", {
  style: {
    color: 'var(--ap-violet)'
  }
}, "\u5F71\u5B50\u6A21\u5F0F"), "\u5E76\u884C\u8FD0\u884C\uFF08\u6536\u5230\u540C\u6837\u7684\u5E02\u573A\u6570\u636E\u3001\u4EA7\u751F\u6A21\u62DF\u51B3\u7B56\u4F46\u4E0D\u4E0B\u5355\uFF09\uFF0C \u4E0E\u7EBF\u4E0A\u7248\u672C\u9010\u7B14\u5BF9\u6BD4\u3002\u5F71\u5B50\u671F \u226514 \u5929\u4E14\u5173\u952E\u6307\u6807\u4F18\u4E8E\u57FA\u7EBF\uFF0C\u65B9\u53EF\u7533\u8BF7", /*#__PURE__*/React.createElement("b", {
  style: {
    color: 'var(--ap-amber)'
  }
}, "\u7070\u5EA6"), "\uFF08\u5C0F\u4ED3\u4F4D\u771F\u5B9E\u8FD0\u884C\uFF09\uFF0C \u6700\u7EC8", /*#__PURE__*/React.createElement("b", {
  style: {
    color: 'var(--ap-mint)'
  }
}, "\u4EBA\u5DE5\u6279\u51C6"), "\u4E0A\u7EBF\u3002\u7070\u5EA6\u671F\u56DE\u64A4\u8D85\u9650\u81EA\u52A8\u56DE\u6EDA\u3002"), /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    alignItems: 'center',
    gap: 0,
    marginTop: 12,
    maxWidth: 560
  }
}, [['提案', 'var(--ap-fg-3)'], ['SHADOW 14d', 'var(--ap-violet)'], ['CANARY 灰度', 'var(--ap-amber)'], ['人工批准', 'var(--ap-fg-2)'], ['LIVE', 'var(--ap-mint)']].map(([l, c], i, arr) => /*#__PURE__*/React.createElement(React.Fragment, {
  key: i
}, /*#__PURE__*/React.createElement("div", {
  style: {
    padding: '5px 12px',
    borderRadius: 999,
    border: `1px solid ${c}`,
    color: c,
    fontSize: 10.5,
    fontFamily: 'var(--ap-font-mono)',
    fontWeight: 600,
    whiteSpace: 'nowrap'
  }
}, l), i < arr.length - 1 && /*#__PURE__*/React.createElement("div", {
  style: {
    flex: 1,
    height: 1.5,
    background: 'var(--ap-line)',
    minWidth: 12
  }
}))))))), /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 20,
    alignItems: 'start'
  }
}, LAB_CANDIDATES.slice(0, 2).map(c => /*#__PURE__*/React.createElement(CandidateCard, {
  key: c.id,
  c: c
}))), /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 20,
    alignItems: 'start'
  }
}, /*#__PURE__*/React.createElement(CandidateCard, {
  c: LAB_CANDIDATES[2]
}), /*#__PURE__*/React.createElement(WCard, {
  title: "\u8FDB\u5316\u5386\u53F2"
}, HISTORY.map((h, i) => /*#__PURE__*/React.createElement("div", {
  key: i,
  style: {
    display: 'flex',
    gap: 12,
    padding: '10px 0',
    borderBottom: i < HISTORY.length - 1 ? '1px solid var(--ap-line-soft)' : 'none'
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    width: 26,
    height: 26,
    borderRadius: '50%',
    flexShrink: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: h.event === 'promote' ? 'var(--ap-mint-soft)' : h.event === 'rollback' ? 'var(--ap-rose-soft)' : 'var(--ap-bg-3)'
  }
}, /*#__PURE__*/React.createElement(Icon, {
  name: h.event === 'promote' ? 'arrow_up' : h.event === 'rollback' ? 'arrow_down' : 'pause',
  size: 12,
  color: h.event === 'promote' ? 'var(--ap-mint)' : h.event === 'rollback' ? 'var(--ap-rose)' : 'var(--ap-fg-4)',
  strokeWidth: 2.2
})), /*#__PURE__*/React.createElement("div", {
  style: {
    flex: 1,
    minWidth: 0
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    alignItems: 'center',
    gap: 8
  }
}, /*#__PURE__*/React.createElement("span", {
  style: {
    fontSize: 12.5,
    fontWeight: 600
  }
}, h.name), /*#__PURE__*/React.createElement(WPill, {
  tone: h.event === 'promote' ? 'mint' : h.event === 'rollback' ? 'rose' : 'default'
}, h.event === 'promote' ? '上线' : h.event === 'rollback' ? '自动回滚' : '退役')), /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 11,
    color: 'var(--ap-fg-4)',
    marginTop: 2,
    fontFamily: 'var(--ap-font-mono)'
  }
}, h.t, " \xB7 ", h.note)))))));
Object.assign(window, {
  WLabPage
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/web_app/components/lab.jsx", error: String((e && e.message) || e) }); }

// ui_kits/web_app/components/market.jsx
try { (() => {
// Market / 行情 page — watchlist · candlestick chart · order book · trades · stats
// Self-contained; uses atoms from shell.jsx

// ---------- deterministic data gen ----------
function seededRand(seed) {
  let s = seed;
  return () => {
    s = s * 1103515245 + 12345 & 0x7fffffff;
    return s / 0x7fffffff;
  };
}
function genCandles(n, start, vol, seed) {
  const rnd = seededRand(seed);
  const out = [];
  let p = start;
  for (let i = 0; i < n; i++) {
    const drift = (rnd() - 0.46) * vol;
    const o = p,
      c = o + drift + (rnd() - 0.5) * vol * 0.6;
    const hi = Math.max(o, c) + rnd() * vol * 0.5,
      lo = Math.min(o, c) - rnd() * vol * 0.5;
    out.push({
      o,
      c,
      hi,
      lo,
      v: 0.3 + rnd() * 0.7
    });
    p = c;
  }
  return out;
}
const MARKET = {
  BTCUSDT: {
    price: 68863.92,
    chg: 2.14,
    base: 67000,
    vol: 260,
    seed: 7,
    high: 69240,
    low: 66980,
    vol24: '2.84B',
    funding: 0.0089,
    oi: '$8.2B',
    held: true,
    sl: 64210,
    tp: 68900,
    entry: 67420.5
  },
  ETHUSDT: {
    price: 3219.92,
    chg: -0.62,
    base: 3260,
    vol: 18,
    seed: 13,
    high: 3288,
    low: 3201,
    vol24: '1.42B',
    funding: 0.0051,
    oi: '$4.1B',
    held: true,
    sl: 3120,
    tp: 3380,
    entry: 3240
  },
  SOLUSDT: {
    price: 151.42,
    chg: 1.08,
    base: 149,
    vol: 1.4,
    seed: 21,
    high: 153.8,
    low: 148.2,
    vol24: '612M',
    funding: 0.0123,
    oi: '$1.1B',
    held: false
  },
  BNBUSDT: {
    price: 604.30,
    chg: 0.42,
    base: 600,
    vol: 3.2,
    seed: 29,
    high: 611,
    low: 598,
    vol24: '287M',
    funding: 0.0067,
    oi: '$820M',
    held: false
  }
};
const REGIME_OF = {
  BTCUSDT: 'trending_up',
  ETHUSDT: 'ranging',
  SOLUSDT: 'trending_up',
  BNBUSDT: 'ranging'
};

// ---------- interactive candlestick chart ----------
const MarketChart = ({
  sym,
  tf
}) => {
  const m = MARKET[sym];
  const n = 64;
  const candles = React.useMemo(() => genCandles(n, m.base, m.vol, m.seed + tf.length * 7), [sym, tf]);
  const wrapRef = React.useRef(null);
  const [w, setW] = React.useState(760);
  const [hover, setHover] = React.useState(null);
  const h = 380,
    pad = 16,
    volH = 56,
    chartH = h - volH - 24;
  React.useEffect(() => {
    const ro = new ResizeObserver(es => {
      for (const e of es) setW(e.contentRect.width);
    });
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);
  const allP = candles.flatMap(c => [c.hi, c.lo]);
  const min = Math.min(...allP),
    max = Math.max(...allP),
    r = max - min || 1;
  const y = p => pad + (1 - (p - min) / r) * (chartH - pad);
  // clamp far-away levels (e.g. deep SL) to chart edge instead of squashing candles
  const yLvl = p => Math.max(pad + 6, Math.min(chartH - 6, y(p)));
  const cw = (w - pad * 2) / candles.length;
  const cx = i => pad + i * cw + cw / 2;
  const onMove = e => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const i = Math.max(0, Math.min(candles.length - 1, Math.floor((x - pad) / cw)));
    setHover({
      i,
      c: candles[i],
      x: cx(i)
    });
  };
  const levels = m.held ? [{
    p: m.tp,
    c: 'var(--ap-mint)',
    l: 'TP ' + wfmt(m.tp, 0)
  }, {
    p: m.entry,
    c: 'var(--ap-fg-3)',
    l: '入场 ' + wfmt(m.entry, 0),
    dash: true
  }, {
    p: m.sl,
    c: 'var(--ap-rose)',
    l: 'SL ' + wfmt(m.sl, 0)
  }] : [];
  return /*#__PURE__*/React.createElement("div", {
    ref: wrapRef,
    style: {
      position: 'relative',
      width: '100%'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "100%",
    height: h,
    viewBox: `0 0 ${w} ${h}`,
    style: {
      display: 'block'
    },
    onMouseMove: onMove,
    onMouseLeave: () => setHover(null)
  }, [0, 0.25, 0.5, 0.75, 1].map((t, i) => /*#__PURE__*/React.createElement("line", {
    key: i,
    x1: pad,
    x2: w - pad,
    y1: pad + t * (chartH - pad),
    y2: pad + t * (chartH - pad),
    stroke: "var(--ap-line-soft)"
  })), [0, 0.5, 1].map((t, i) => /*#__PURE__*/React.createElement("text", {
    key: i,
    x: w - pad,
    y: pad + t * (chartH - pad) + (i === 0 ? 10 : i === 2 ? -2 : 4),
    textAnchor: "end",
    fontSize: "9.5",
    fill: "var(--ap-fg-4)",
    fontFamily: "var(--ap-font-mono)"
  }, wfmt(max - t * r, 0))), levels.map((lv, i) => {
    const clamped = y(lv.p) !== yLvl(lv.p);
    const lw = clamped ? 64 : 52;
    return /*#__PURE__*/React.createElement("g", {
      key: i
    }, /*#__PURE__*/React.createElement("line", {
      x1: pad,
      x2: w - pad - lw,
      y1: yLvl(lv.p),
      y2: yLvl(lv.p),
      stroke: lv.c,
      strokeWidth: "1",
      strokeDasharray: lv.dash || clamped ? '3 3' : '5 0',
      opacity: clamped ? 0.5 : 0.75
    }), /*#__PURE__*/React.createElement("rect", {
      x: w - pad - lw,
      y: yLvl(lv.p) - 8,
      width: lw,
      height: 16,
      rx: 3,
      fill: lv.c,
      opacity: ".18"
    }), /*#__PURE__*/React.createElement("text", {
      x: w - pad - 4,
      y: yLvl(lv.p) + 4,
      textAnchor: "end",
      fontSize: "9",
      fill: lv.c,
      fontFamily: "var(--ap-font-mono)",
      fontWeight: "600"
    }, lv.l, clamped ? ' ↓' : ''));
  }), candles.map((c, i) => {
    const up = c.c >= c.o,
      col = up ? 'var(--ap-mint)' : 'var(--ap-rose)';
    const bw = Math.max(1.5, cw * 0.62);
    return /*#__PURE__*/React.createElement("g", {
      key: i
    }, /*#__PURE__*/React.createElement("line", {
      x1: cx(i),
      x2: cx(i),
      y1: y(c.hi),
      y2: y(c.lo),
      stroke: col,
      strokeWidth: "1"
    }), /*#__PURE__*/React.createElement("rect", {
      x: cx(i) - bw / 2,
      y: y(Math.max(c.o, c.c)),
      width: bw,
      height: Math.max(1, Math.abs(y(c.o) - y(c.c))),
      fill: col,
      opacity: up ? 0.95 : 0.9
    }));
  }), /*#__PURE__*/React.createElement("line", {
    x1: pad,
    x2: w - pad - 52,
    y1: y(m.price),
    y2: y(m.price),
    stroke: "var(--ap-cyan)",
    strokeWidth: "1",
    strokeDasharray: "1 3"
  }), /*#__PURE__*/React.createElement("rect", {
    x: w - pad - 52,
    y: y(m.price) - 8,
    width: 52,
    height: 16,
    rx: 3,
    fill: "var(--ap-cyan)"
  }), /*#__PURE__*/React.createElement("text", {
    x: w - pad - 4,
    y: y(m.price) + 4,
    textAnchor: "end",
    fontSize: "9.5",
    fill: "var(--ap-bg-0)",
    fontFamily: "var(--ap-font-mono)",
    fontWeight: "700"
  }, wfmt(m.price, 0)), /*#__PURE__*/React.createElement("g", {
    transform: `translate(0,${h - volH})`
  }, candles.map((c, i) => {
    const up = c.c >= c.o,
      bw = Math.max(1.5, cw * 0.62);
    return /*#__PURE__*/React.createElement("rect", {
      key: i,
      x: cx(i) - bw / 2,
      y: volH - c.v * (volH - 8),
      width: bw,
      height: c.v * (volH - 8),
      fill: up ? 'var(--ap-mint)' : 'var(--ap-rose)',
      opacity: ".35"
    });
  })), hover && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("line", {
    x1: hover.x,
    x2: hover.x,
    y1: pad,
    y2: chartH,
    stroke: "var(--ap-fg-3)",
    strokeWidth: "1",
    strokeDasharray: "3 3"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: hover.x,
    cy: y(hover.c.c),
    r: "3.5",
    fill: "var(--ap-cyan)",
    stroke: "var(--ap-bg-1)",
    strokeWidth: "2"
  }))), hover && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 8,
      left: Math.max(8, Math.min(hover.x / w * 100, 72)) + '%',
      transform: 'translateX(-50%)',
      background: 'var(--ap-bg-4)',
      border: '1px solid var(--ap-line)',
      borderRadius: 8,
      padding: '7px 11px',
      pointerEvents: 'none',
      boxShadow: 'var(--ap-shadow-2)',
      whiteSpace: 'nowrap',
      zIndex: 2,
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)'
    }
  }, "O"), /*#__PURE__*/React.createElement("span", null, wfmt(hover.c.o, 0)), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)'
    }
  }, "H"), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-mint)'
    }
  }, wfmt(hover.c.hi, 0))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 12,
      marginTop: 2
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)'
    }
  }, "C"), /*#__PURE__*/React.createElement("span", {
    style: {
      color: hover.c.c >= hover.c.o ? 'var(--ap-mint)' : 'var(--ap-rose)'
    }
  }, wfmt(hover.c.c, 0)), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)'
    }
  }, "L"), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-rose)'
    }
  }, wfmt(hover.c.lo, 0)))));
};

// ---------- order book ----------
const OrderBook = ({
  sym
}) => {
  const m = MARKET[sym];
  const rnd = seededRand(m.seed * 3);
  const step = m.price * 0.0004;
  const asks = Array.from({
    length: 8
  }, (_, i) => ({
    p: m.price + step * (8 - i),
    sz: rnd() * 4 + 0.2
  }));
  const bids = Array.from({
    length: 8
  }, (_, i) => ({
    p: m.price - step * (i + 1),
    sz: rnd() * 4 + 0.2
  }));
  const maxSz = Math.max(...asks.map(a => a.sz), ...bids.map(b => b.sz));
  const Row = ({
    r,
    side
  }) => /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      display: 'flex',
      justifyContent: 'space-between',
      padding: '3px 10px',
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      right: 0,
      top: 0,
      bottom: 0,
      width: r.sz / maxSz * 100 + '%',
      background: side === 'ask' ? 'var(--ap-rose-soft)' : 'var(--ap-mint-soft)'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'relative',
      color: side === 'ask' ? 'var(--ap-rose)' : 'var(--ap-mint)'
    }
  }, wfmt(r.p, m.price > 1000 ? 1 : 2)), /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'relative',
      color: 'var(--ap-fg-3)'
    }
  }, r.sz.toFixed(3)));
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      padding: '0 10px 6px',
      fontSize: 9.5,
      color: 'var(--ap-fg-4)',
      letterSpacing: '.06em',
      textTransform: 'uppercase'
    }
  }, /*#__PURE__*/React.createElement("span", null, "\u4EF7\u683C"), /*#__PURE__*/React.createElement("span", null, "\u6570\u91CF")), asks.map((a, i) => /*#__PURE__*/React.createElement(Row, {
    key: i,
    r: a,
    side: "ask"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '7px 10px',
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 14,
      fontWeight: 700,
      color: m.chg >= 0 ? 'var(--ap-mint)' : 'var(--ap-rose)',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      borderTop: '1px solid var(--ap-line-soft)',
      borderBottom: '1px solid var(--ap-line-soft)',
      margin: '3px 0'
    }
  }, wfmt(m.price, m.price > 1000 ? 1 : 2), " ", /*#__PURE__*/React.createElement(Icon, {
    name: m.chg >= 0 ? 'arrow_up' : 'arrow_down',
    size: 13,
    color: m.chg >= 0 ? 'var(--ap-mint)' : 'var(--ap-rose)'
  })), bids.map((b, i) => /*#__PURE__*/React.createElement(Row, {
    key: i,
    r: b,
    side: "bid"
  })));
};

// ---------- recent trades ----------
const RecentTrades = ({
  sym
}) => {
  const m = MARKET[sym];
  const rnd = seededRand(m.seed * 5);
  const trades = Array.from({
    length: 14
  }, (_, i) => {
    const buy = rnd() > 0.45;
    const step = m.price * 0.0003;
    return {
      p: m.price + (rnd() - 0.5) * step * 6,
      sz: rnd() * 2 + 0.05,
      buy,
      t: `14:2${3 - Math.floor(i / 5)}:${(59 - i * 3).toString().padStart(2, '0')}`
    };
  });
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      padding: '0 10px 6px',
      fontSize: 9.5,
      color: 'var(--ap-fg-4)',
      letterSpacing: '.06em',
      textTransform: 'uppercase'
    }
  }, /*#__PURE__*/React.createElement("span", null, "\u4EF7\u683C"), /*#__PURE__*/React.createElement("span", null, "\u6570\u91CF"), /*#__PURE__*/React.createElement("span", null, "\u65F6\u95F4")), trades.map((t, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      padding: '3px 10px',
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: t.buy ? 'var(--ap-mint)' : 'var(--ap-rose)'
    }
  }, wfmt(t.p, m.price > 1000 ? 1 : 2)), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-2)'
    }
  }, t.sz.toFixed(3)), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-4)'
    }
  }, t.t))));
};

// ---------- main page ----------
const WMarketPage = () => {
  const [sym, setSym] = React.useState('BTCUSDT');
  const [tf, setTf] = React.useState('15m');
  const [obTab, setObTab] = React.useState('book');
  const m = MARKET[sym];
  const regime = REGIME_OF[sym];
  const regimeTone = regime === 'trending_up' ? 'mint' : regime === 'trending_down' ? 'rose' : regime === 'chaotic' ? 'amber' : 'cyan';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '220px minmax(0,1fr) 260px',
      gap: 16,
      height: '100%'
    }
  }, /*#__PURE__*/React.createElement(WCard, {
    title: "\u81EA\u9009",
    style: {
      height: 'fit-content'
    },
    right: /*#__PURE__*/React.createElement(Icon, {
      name: "search",
      size: 13,
      color: "var(--ap-fg-4)"
    })
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      margin: '-16px -18px'
    }
  }, Object.keys(MARKET).map(s => {
    const d = MARKET[s];
    const up = d.chg >= 0;
    const sel = s === sym;
    return /*#__PURE__*/React.createElement("div", {
      key: s,
      onClick: () => setSym(s),
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '11px 14px',
        cursor: 'pointer',
        borderLeft: '2px solid ' + (sel ? 'var(--ap-mint)' : 'transparent'),
        background: sel ? 'var(--ap-bg-3)' : 'transparent',
        borderBottom: '1px solid var(--ap-line-soft)'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 1,
        minWidth: 0
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 6
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: 'var(--ap-font-mono)',
        fontSize: 12.5,
        fontWeight: 600
      }
    }, s.replace('USDT', '')), d.held && /*#__PURE__*/React.createElement("span", {
      title: "\u6301\u4ED3\u4E2D",
      style: {
        width: 5,
        height: 5,
        borderRadius: '50%',
        background: 'var(--ap-violet)',
        boxShadow: '0 0 5px var(--ap-violet)'
      }
    })), /*#__PURE__*/React.createElement("div", {
      style: {
        fontFamily: 'var(--ap-font-mono)',
        fontSize: 10,
        color: 'var(--ap-fg-4)'
      }
    }, "USDT \u6C38\u7EED")), /*#__PURE__*/React.createElement("div", {
      style: {
        textAlign: 'right'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontFamily: 'var(--ap-font-mono)',
        fontSize: 12,
        fontWeight: 600
      }
    }, wfmt(d.price, d.price > 1000 ? 0 : 2)), /*#__PURE__*/React.createElement("div", {
      style: {
        fontFamily: 'var(--ap-font-mono)',
        fontSize: 10.5,
        color: up ? 'var(--ap-mint)' : 'var(--ap-rose)'
      }
    }, up ? '▲' : '▼', " ", Math.abs(d.chg).toFixed(2), "%")));
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 16,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(WCard, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 16,
      marginBottom: 14,
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      borderRadius: '50%',
      background: sym.startsWith('BTC') ? 'linear-gradient(135deg,#F7931A,#8B4E0D)' : sym.startsWith('ETH') ? 'linear-gradient(135deg,#627EEA,#3C54BD)' : 'linear-gradient(135deg,#9945FF,#14F195)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#fff',
      fontWeight: 700
    }
  }, sym[0]), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 16,
      fontWeight: 700,
      fontFamily: 'var(--ap-font-mono)'
    }
  }, sym), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-fg-3)'
    }
  }, "\u6C38\u7EED\u5408\u7EA6 \xB7 Binance"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement(AnimatedNumber, {
    value: m.price,
    prefix: "$",
    format: v => wfmt(v, m.price > 1000 ? 2 : 3),
    style: {
      fontSize: 26,
      fontWeight: 700,
      color: 'var(--ap-fg-1)'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 14,
      fontWeight: 600,
      color: m.chg >= 0 ? 'var(--ap-mint)' : 'var(--ap-rose)'
    }
  }, m.chg >= 0 ? '+' : '', m.chg.toFixed(2), "%")), /*#__PURE__*/React.createElement("div", {
    style: {
      marginLeft: 'auto',
      display: 'flex',
      gap: 18
    }
  }, [['24h 高', wfmt(m.high, 0)], ['24h 低', wfmt(m.low, 0)], ['24h 量', m.vol24]].map(([l, v], i) => /*#__PURE__*/React.createElement("div", {
    key: i
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9.5,
      color: 'var(--ap-fg-4)',
      letterSpacing: '.06em',
      textTransform: 'uppercase'
    }
  }, l), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 12,
      fontWeight: 600
    }
  }, v))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 8,
      flexWrap: 'wrap',
      rowGap: 6
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-flex',
      background: 'var(--ap-bg-3)',
      borderRadius: 8,
      padding: 3,
      border: '1px solid var(--ap-line)'
    }
  }, ['1m', '5m', '15m', '1h', '4h', '1d'].map(t => /*#__PURE__*/React.createElement("div", {
    key: t,
    onClick: () => setTf(t),
    style: {
      fontSize: 11,
      padding: '5px 11px',
      borderRadius: 5,
      fontFamily: 'var(--ap-font-mono)',
      cursor: 'pointer',
      background: tf === t ? 'var(--ap-bg-4)' : 'transparent',
      color: tf === t ? 'var(--ap-fg-1)' : 'var(--ap-fg-3)',
      fontWeight: 500
    }
  }, t))), /*#__PURE__*/React.createElement(WPill, {
    tone: regimeTone
  }, "AI regime \xB7 ", regime), m.held && /*#__PURE__*/React.createElement(WPill, {
    tone: "violet"
  }, "\u6301\u4ED3\u4E2D"), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      fontSize: 10.5,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)',
      whiteSpace: 'nowrap'
    }
  }, "\u542B SL/TP \u6807\u7EBF")), /*#__PURE__*/React.createElement("div", {
    style: {
      margin: '0 -18px -16px'
    }
  }, /*#__PURE__*/React.createElement(MarketChart, {
    sym: sym,
    tf: tf
  }))), /*#__PURE__*/React.createElement(WCard, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-start',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      borderRadius: 8,
      background: 'var(--ap-violet-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "brain",
    size: 16,
    color: "var(--ap-violet)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-violet)',
      letterSpacing: '.08em',
      fontWeight: 700,
      marginBottom: 4
    }
  }, "AI \u5E02\u573A\u89E3\u8BFB \xB7 ", sym), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: 'var(--ap-fg-2)',
      lineHeight: 1.6
    }
  }, regime === 'trending_up' ? /*#__PURE__*/React.createElement(React.Fragment, null, "\u5F53\u524D\u5224\u5B9A ", /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--ap-mint)'
    }
  }, "trending_up"), "\uFF1AEMA \u591A\u5934\u6392\u5217\uFF0C", tf, " \u7EA7\u522B\u91CF\u80FD\u6E29\u548C\u653E\u5927\u3002", m.held ? '持仓盈利中，止盈位上移空间充足。' : '符合「趋势跟随」策略入场条件，等待回踩确认。') : /*#__PURE__*/React.createElement(React.Fragment, null, "\u5F53\u524D\u5224\u5B9A ", /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--ap-cyan)'
    }
  }, "ranging"), "\uFF1A\u4EF7\u683C\u5728\u533A\u95F4\u5185\u9707\u8361\uFF0C\u65B9\u5411\u6027\u4E0D\u8DB3\u3002AI \u503E\u5411 ", /*#__PURE__*/React.createElement("b", null, "\u89C2\u671B"), "\uFF0C\u4EC5\u5728\u7A81\u7834\u533A\u95F4\u8FB9\u754C\u4E14\u653E\u91CF\u65F6\u8003\u8651\u5165\u573A\u3002")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      marginTop: 10
    }
  }, /*#__PURE__*/React.createElement(WPill, {
    tone: "cyan"
  }, "\u8D44\u91D1\u8D39\u7387 ", m.funding.toFixed(4), "%"), /*#__PURE__*/React.createElement(WPill, {
    tone: "default"
  }, "\u6301\u4ED3\u91CF ", m.oi), /*#__PURE__*/React.createElement(WPill, {
    tone: "default"
  }, "8h \u5012\u8BA1\u65F6 02:14:30")))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 16,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(OrderTicket, {
    sym: sym
  }), /*#__PURE__*/React.createElement(WCard, {
    title: /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        gap: 12
      }
    }, /*#__PURE__*/React.createElement("span", {
      onClick: () => setObTab('book'),
      style: {
        cursor: 'pointer',
        color: obTab === 'book' ? 'var(--ap-fg-1)' : 'var(--ap-fg-4)'
      }
    }, "\u76D8\u53E3"), /*#__PURE__*/React.createElement("span", {
      onClick: () => setObTab('trades'),
      style: {
        cursor: 'pointer',
        color: obTab === 'trades' ? 'var(--ap-fg-1)' : 'var(--ap-fg-4)'
      }
    }, "\u6210\u4EA4")),
    style: {
      height: 'fit-content'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      margin: '-16px -18px'
    }
  }, obTab === 'book' ? /*#__PURE__*/React.createElement(OrderBook, {
    sym: sym
  }) : /*#__PURE__*/React.createElement(RecentTrades, {
    sym: sym
  }))), /*#__PURE__*/React.createElement(WCard, {
    title: "\u5408\u7EA6\u4FE1\u606F",
    style: {
      height: 'fit-content'
    }
  }, [['资金费率', m.funding.toFixed(4) + '%', m.funding >= 0 ? 'pos' : 'neg'], ['下次结算', '02:14:30', ''], ['持仓量 OI', m.oi, ''], ['24h 成交额', m.vol24, ''], ['标记价格', wfmt(m.price, m.price > 1000 ? 1 : 3), ''], ['指数价格', wfmt(m.price * 0.9998, m.price > 1000 ? 1 : 3), '']].map(([l, v, tone], i, a) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      padding: '8px 0',
      borderBottom: i < a.length - 1 ? '1px solid var(--ap-line-soft)' : 'none',
      fontSize: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)'
    }
  }, l), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontWeight: 600,
      color: tone === 'pos' ? 'var(--ap-mint)' : tone === 'neg' ? 'var(--ap-rose)' : 'var(--ap-fg-1)'
    }
  }, v))))));
};
Object.assign(window, {
  WMarketPage,
  MARKET
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/web_app/components/market.jsx", error: String((e && e.message) || e) }); }

// ui_kits/web_app/components/pages.jsx
try { (() => {
// Web pages: Dashboard, AI list, Positions, Backtest, Risk config, Audit log

// session-level dismissals for halt banners (per surface)
const ackHaltSession = {
  ai: false,
  pos: false
};

// generate sparkline
const genData = (n = 60, base = 120000, vol = 700) => {
  const out = [];
  let v = base;
  for (let i = 0; i < n; i++) {
    v += Math.sin(i / 5) * vol + (Math.random() - 0.4) * vol * 0.7;
    out.push(v);
  }
  out[n - 1] = base + 2291;
  return out;
};
const EQUITY_DATA = genData();
const PNL_DATA = genData(30, 0, 400).map((v, i) => v * (i > 15 ? 1 : -0.3));

// =========================================================
// Dashboard
// =========================================================
const WDashboard = ({
  aiVariant,
  onNav,
  motion = true,
  narrow = false
}) => {
  const {
    equity,
    equityChange,
    equityChangePct,
    todayPnl,
    todayPnlPct,
    weekPnl,
    weekPnlPct,
    mtdPnl,
    mtdPnlPct,
    positions,
    tradesToday,
    winRate,
    sharpe,
    maxDD,
    avgHold,
    decisions,
    events,
    riskState,
    regime,
    dayLossPct
  } = W_MOCK;
  const [ackHalt, setAckHalt] = React.useState(false);
  // when halted, the first decision is a CLOSE-only / blocked open
  const heroDecision = riskState === 'HALTED' ? {
    ...decisions[0],
    action: 'HOLD',
    guard: 'REJECT',
    conf: 0.31,
    strat: '熔断保护',
    reason: '日亏损达到熔断阈值，守卫拒绝所有新开仓，仅允许平仓与风险管理操作。',
    sl: undefined
  } : decisions[0];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column'
    }
  }, !ackHalt && /*#__PURE__*/React.createElement(HaltBanner, {
    riskState: riskState,
    regime: regime,
    dayLossPct: dayLossPct,
    onAck: () => setAckHalt(true)
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: narrow ? '1fr' : 'minmax(0,1fr) 360px',
      gap: 20
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 20,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(StreamingDecision, {
    d: heroDecision,
    variant: aiVariant,
    motion: motion,
    halted: riskState === 'HALTED'
  }), /*#__PURE__*/React.createElement(WCard, {
    title: "\u8D26\u6237\u6743\u76CA",
    right: /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        gap: 4,
        padding: 3,
        background: 'var(--ap-bg-3)',
        borderRadius: 8
      }
    }, ['1D', '1W', '1M', '3M', 'ALL'].map((r, i) => /*#__PURE__*/React.createElement("span", {
      key: r,
      style: {
        padding: '4px 10px',
        fontSize: 11,
        fontFamily: 'var(--ap-font-mono)',
        borderRadius: 5,
        background: i === 2 ? 'var(--ap-bg-4)' : 'transparent',
        color: i === 2 ? 'var(--ap-fg-1)' : 'var(--ap-fg-3)',
        cursor: 'pointer'
      }
    }, r)))
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(4,1fr)',
      gap: 24,
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.08em',
      textTransform: 'uppercase',
      fontWeight: 500
    }
  }, "\u5F53\u524D\u6743\u76CA"), /*#__PURE__*/React.createElement(AnimatedNumber, {
    value: equity,
    prefix: "$",
    format: v => wfmt(v),
    motion: motion,
    style: {
      fontSize: 28,
      fontWeight: 700,
      letterSpacing: '-.02em',
      color: 'var(--ap-fg-1)',
      lineHeight: 1.1
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11.5,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "+", wfmt(equityChange), " \u4ECA\u65E5")), /*#__PURE__*/React.createElement(WStat, {
    label: "\u4ECA\u65E5",
    value: wfmtPct(todayPnlPct),
    sub: wfmtSigned(todayPnl),
    tone: "pos"
  }), /*#__PURE__*/React.createElement(WStat, {
    label: "\u672C\u5468",
    value: wfmtPct(weekPnlPct),
    sub: wfmtSigned(weekPnl),
    tone: "pos"
  }), /*#__PURE__*/React.createElement(WStat, {
    label: "\u672C\u6708",
    value: wfmtPct(mtdPnlPct),
    sub: wfmtSigned(mtdPnl),
    tone: "pos"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      margin: '0 -18px -16px',
      position: 'relative'
    }
  }, /*#__PURE__*/React.createElement(WSparkLive, {
    data: EQUITY_DATA,
    h: 160,
    gridId: "spd1",
    color: riskState === 'HALTED' ? 'var(--ap-rose)' : 'var(--ap-mint)'
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(4,1fr)',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(WCard, {
    dense: true
  }, /*#__PURE__*/React.createElement(WStat, {
    label: "\u4ECA\u65E5\u4EA4\u6613",
    value: tradesToday,
    sub: `胜率 ${winRate}%`
  })), /*#__PURE__*/React.createElement(WCard, {
    dense: true
  }, /*#__PURE__*/React.createElement(WStat, {
    label: "Sharpe 30d",
    value: sharpe.toFixed(2),
    sub: "risk-adjusted"
  })), /*#__PURE__*/React.createElement(WCard, {
    dense: true
  }, /*#__PURE__*/React.createElement(WStat, {
    label: "\u6700\u5927\u56DE\u64A4",
    value: wfmtPct(maxDD),
    sub: "\u9608\u503C \u22128%",
    tone: "neg"
  })), /*#__PURE__*/React.createElement(WCard, {
    dense: true
  }, /*#__PURE__*/React.createElement(WStat, {
    label: "\u5E73\u5747\u6301\u4ED3\u65F6\u957F",
    value: avgHold,
    sub: "\u4E2D\u77ED\u7EBF"
  }))), /*#__PURE__*/React.createElement(WCard, {
    title: "\u5F53\u524D\u6301\u4ED3",
    right: /*#__PURE__*/React.createElement("span", {
      onClick: () => onNav('positions'),
      style: {
        fontSize: 11,
        color: 'var(--ap-mint)',
        cursor: 'pointer',
        fontFamily: 'var(--ap-font-mono)'
      }
    }, "\u67E5\u770B\u5168\u90E8 \u2192")
  }, /*#__PURE__*/React.createElement(WPositionsTable, {
    positions: positions
  }))), /*#__PURE__*/React.createElement(WCard, {
    title: "\u4E8B\u4EF6\u6D41 \xB7 \u5B9E\u65F6",
    right: /*#__PURE__*/React.createElement(WPill, {
      tone: motion ? 'mint' : 'default'
    }, motion ? 'LIVE' : 'PAUSED'),
    style: {
      height: 'fit-content',
      position: narrow ? 'static' : 'sticky',
      top: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      maxHeight: narrow ? 420 : 780,
      overflow: 'auto'
    }
  }, riskState === 'HALTED' && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 10,
      padding: '10px 2px',
      borderBottom: '1px solid var(--ap-line-soft)',
      background: 'var(--ap-rose-soft)',
      margin: '0 -4px',
      paddingLeft: 6,
      paddingRight: 6,
      borderRadius: 6
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 24,
      height: 24,
      borderRadius: 6,
      background: 'var(--ap-rose)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "alert",
    size: 12,
    color: "var(--ap-bg-0)",
    strokeWidth: 2.4
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--ap-rose)',
      fontWeight: 600,
      lineHeight: 1.5
    }
  }, "\u7194\u65AD\u89E6\u53D1 \xB7 \u65B0\u5F00\u4ED3\u5DF2\u6682\u505C"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)',
      marginTop: 2
    }
  }, new Date().toTimeString().slice(0, 8)))), events.map((e, i) => /*#__PURE__*/React.createElement(WEventRow, {
    key: i,
    e: e
  }))))));
};
const WEventRow = ({
  e
}) => {
  const colors = {
    mint: 'var(--ap-mint)',
    rose: 'var(--ap-rose)',
    amber: 'var(--ap-amber)',
    violet: 'var(--ap-violet)',
    fg: 'var(--ap-fg-2)'
  };
  const iconMap = {
    fill: 'check',
    order: 'clock',
    guard: 'shield',
    ai: 'brain'
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 10,
      padding: '10px 2px',
      borderBottom: '1px solid var(--ap-line-soft)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 24,
      height: 24,
      borderRadius: 6,
      background: 'var(--ap-bg-3)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: iconMap[e.kind] || 'circle',
    size: 12,
    color: colors[e.color]
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-1)',
      lineHeight: 1.5
    }
  }, e.msg), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)',
      marginTop: 2,
      letterSpacing: '.02em'
    }
  }, e.t)));
};
const WPositionsTable = ({
  positions,
  detail
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    margin: '-16px -18px'
  }
}, /*#__PURE__*/React.createElement("table", {
  style: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 12
  }
}, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", {
  style: {
    borderBottom: '1px solid var(--ap-line)'
  }
}, ['交易对', '方向', '数量', '入场', '标记', '浮盈', '收益率', '止损', '止盈', '持仓时长', '策略', '操作'].slice(0, detail ? 12 : 9).map(h => /*#__PURE__*/React.createElement("th", {
  key: h,
  style: {
    padding: '10px 12px',
    textAlign: 'left',
    fontSize: 10,
    color: 'var(--ap-fg-3)',
    letterSpacing: '.06em',
    textTransform: 'uppercase',
    fontWeight: 500
  }
}, h)))), /*#__PURE__*/React.createElement("tbody", null, positions.map((p, i) => {
  const isUp = p.pnl >= 0;
  return /*#__PURE__*/React.createElement("tr", {
    key: i,
    style: {
      borderBottom: '1px solid var(--ap-line-soft)',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '12px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 22,
      height: 22,
      borderRadius: '50%',
      background: p.sym.startsWith('BTC') ? 'linear-gradient(135deg,#F7931A,#8B4E0D)' : 'linear-gradient(135deg,#627EEA,#3C54BD)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#fff',
      fontWeight: 700,
      fontSize: 10
    }
  }, p.sym.startsWith('BTC') ? '₿' : 'Ξ'), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontWeight: 600
    }
  }, p.sym))), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '12px'
    }
  }, /*#__PURE__*/React.createElement(WPill, {
    tone: p.side === 'LONG' ? 'mint' : 'rose'
  }, p.side)), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '12px',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, p.qty), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '12px',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, wfmt(p.entry)), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '12px',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, wfmt(p.mark)), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '12px',
      fontFamily: 'var(--ap-font-mono)',
      color: isUp ? 'var(--ap-mint)' : 'var(--ap-rose)'
    }
  }, wfmtSigned(p.pnl)), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '12px',
      fontFamily: 'var(--ap-font-mono)',
      color: isUp ? 'var(--ap-mint)' : 'var(--ap-rose)'
    }
  }, wfmtPct(p.pnlPct)), detail && /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '12px',
      fontFamily: 'var(--ap-font-mono)',
      color: 'var(--ap-rose)'
    }
  }, wfmt(p.sl)), detail && /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '12px',
      fontFamily: 'var(--ap-font-mono)',
      color: 'var(--ap-mint)'
    }
  }, wfmt(p.tp)), /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '12px',
      fontFamily: 'var(--ap-font-mono)',
      color: 'var(--ap-fg-3)'
    }
  }, p.age), detail && /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '12px',
      color: 'var(--ap-fg-2)'
    }
  }, p.strat), detail && /*#__PURE__*/React.createElement("td", {
    style: {
      padding: '12px'
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '4px 10px',
      background: 'var(--ap-bg-3)',
      border: '1px solid var(--ap-line)',
      borderRadius: 6,
      color: 'var(--ap-fg-2)',
      fontSize: 11,
      cursor: 'pointer',
      marginRight: 4
    }
  }, "\u7F16\u8F91"), /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '4px 10px',
      background: 'var(--ap-rose-soft)',
      border: '1px solid var(--ap-rose)',
      borderRadius: 6,
      color: 'var(--ap-rose)',
      fontSize: 11,
      cursor: 'pointer'
    }
  }, "\u5E73\u4ED3")));
}))));

// =========================================================
// AI decisions list
// =========================================================
const WAIPage = ({
  aiVariant,
  motion = true
}) => {
  const [filter, setFilter] = React.useState('all');
  const filtered = W_MOCK.decisions.filter(d => filter === 'all' || filter === 'exec' && d.guard === 'PASS' || filter === 'blocked' && d.guard !== 'PASS');
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 16,
      maxWidth: 1100
    }
  }, !ackHaltSession.ai && /*#__PURE__*/React.createElement(HaltBanner, {
    riskState: W_MOCK.riskState,
    regime: W_MOCK.regime,
    dayLossPct: W_MOCK.dayLossPct,
    onAck: () => {
      ackHaltSession.ai = true;
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, [{
    k: 'all',
    l: '全部',
    n: W_MOCK.decisions.length
  }, {
    k: 'exec',
    l: '已执行',
    n: W_MOCK.decisions.filter(d => d.guard === 'PASS').length
  }, {
    k: 'blocked',
    l: '已拦截',
    n: W_MOCK.decisions.filter(d => d.guard !== 'PASS').length
  }].map(t => /*#__PURE__*/React.createElement("div", {
    key: t.k,
    onClick: () => setFilter(t.k),
    style: {
      padding: '6px 14px',
      borderRadius: 8,
      fontSize: 12,
      fontWeight: 500,
      background: filter === t.k ? 'var(--ap-bg-3)' : 'var(--ap-bg-2)',
      color: filter === t.k ? 'var(--ap-fg-1)' : 'var(--ap-fg-3)',
      border: '1px solid ' + (filter === t.k ? 'var(--ap-line)' : 'var(--ap-line-soft)'),
      cursor: 'pointer',
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      whiteSpace: 'nowrap',
      flexShrink: 0
    }
  }, t.l, " ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 10,
      opacity: .7
    }
  }, t.n))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginLeft: 'auto',
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "\u6837\u5F0F: ", /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--ap-violet)'
    }
  }, aiVariant))), filtered.map((d, i) => i === 0 && motion ? /*#__PURE__*/React.createElement(StreamingDecision, {
    key: d.id,
    d: d,
    variant: aiVariant,
    motion: motion
  }) : /*#__PURE__*/React.createElement(AIDecisionCard, {
    key: d.id,
    d: d,
    variant: aiVariant
  })));
};

// =========================================================
// Positions page
// =========================================================
const WPositionsPage = () => /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    flexDirection: 'column',
    gap: 20
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4,1fr)',
    gap: 12
  }
}, /*#__PURE__*/React.createElement(WCard, {
  dense: true
}, /*#__PURE__*/React.createElement(WStat, {
  label: "\u603B\u6301\u4ED3",
  value: W_MOCK.positions.length,
  sub: `占比 ${W_MOCK.positionsPct}%`
})), /*#__PURE__*/React.createElement(WCard, {
  dense: true
}, /*#__PURE__*/React.createElement(WStat, {
  label: "\u591A\u5934",
  value: "2",
  sub: "BTC \xB7 ETH"
})), /*#__PURE__*/React.createElement(WCard, {
  dense: true
}, /*#__PURE__*/React.createElement(WStat, {
  label: "\u6D6E\u76C8\u603B\u8BA1",
  value: wfmtSigned(W_MOCK.positions.reduce((s, p) => s + p.pnl, 0)),
  tone: "pos"
})), /*#__PURE__*/React.createElement(WCard, {
  dense: true
}, /*#__PURE__*/React.createElement(WStat, {
  label: "\u6D3B\u8DC3\u6302\u5355",
  value: "4",
  sub: "SL\xD72 \xB7 TP\xD72"
}))), /*#__PURE__*/React.createElement(WCard, {
  title: "\u6301\u4ED3"
}, /*#__PURE__*/React.createElement(WPositionsTable, {
  positions: W_MOCK.positions,
  detail: true
})), /*#__PURE__*/React.createElement(WCard, {
  title: "\u8BA2\u5355\u7C3F"
}, /*#__PURE__*/React.createElement("div", {
  style: {
    margin: '-16px -18px'
  }
}, /*#__PURE__*/React.createElement("table", {
  style: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 12
  }
}, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", {
  style: {
    borderBottom: '1px solid var(--ap-line)'
  }
}, ['时间', '交易对', '方向', '类型', '数量', '价格', '状态'].map(h => /*#__PURE__*/React.createElement("th", {
  key: h,
  style: {
    padding: '10px 12px',
    textAlign: 'left',
    fontSize: 10,
    color: 'var(--ap-fg-3)',
    letterSpacing: '.06em',
    textTransform: 'uppercase',
    fontWeight: 500
  }
}, h)))), /*#__PURE__*/React.createElement("tbody", null, W_MOCK.orders.map((o, i) => /*#__PURE__*/React.createElement("tr", {
  key: i,
  style: {
    borderBottom: '1px solid var(--ap-line-soft)'
  }
}, /*#__PURE__*/React.createElement("td", {
  style: {
    padding: '10px 12px',
    fontFamily: 'var(--ap-font-mono)',
    color: 'var(--ap-fg-3)'
  }
}, o.t), /*#__PURE__*/React.createElement("td", {
  style: {
    padding: '10px 12px',
    fontFamily: 'var(--ap-font-mono)',
    fontWeight: 600
  }
}, o.sym), /*#__PURE__*/React.createElement("td", {
  style: {
    padding: '10px 12px'
  }
}, /*#__PURE__*/React.createElement(WPill, {
  tone: o.side === 'BUY' ? 'mint' : 'rose'
}, o.side)), /*#__PURE__*/React.createElement("td", {
  style: {
    padding: '10px 12px',
    fontFamily: 'var(--ap-font-mono)',
    fontSize: 11,
    color: 'var(--ap-fg-2)'
  }
}, o.type), /*#__PURE__*/React.createElement("td", {
  style: {
    padding: '10px 12px',
    fontFamily: 'var(--ap-font-mono)'
  }
}, o.qty), /*#__PURE__*/React.createElement("td", {
  style: {
    padding: '10px 12px',
    fontFamily: 'var(--ap-font-mono)'
  }
}, wfmt(o.price)), /*#__PURE__*/React.createElement("td", {
  style: {
    padding: '10px 12px'
  }
}, /*#__PURE__*/React.createElement(WPill, {
  tone: o.status === 'FILLED' ? 'mint' : o.status === 'WORKING' ? 'cyan' : 'default'
}, o.status)))))))));

// =========================================================
// Backtest / performance
// =========================================================
const WBacktestPage = () => /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    flexDirection: 'column',
    gap: 20
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'grid',
    gridTemplateColumns: 'repeat(6,1fr)',
    gap: 12
  }
}, /*#__PURE__*/React.createElement(WCard, {
  dense: true
}, /*#__PURE__*/React.createElement(WStat, {
  label: "\u51C0\u6536\u76CA",
  value: "+24.8%",
  tone: "pos",
  sub: "vs +9.2% HODL"
})), /*#__PURE__*/React.createElement(WCard, {
  dense: true
}, /*#__PURE__*/React.createElement(WStat, {
  label: "Sharpe",
  value: "1.84",
  sub: "risk-adjusted"
})), /*#__PURE__*/React.createElement(WCard, {
  dense: true
}, /*#__PURE__*/React.createElement(WStat, {
  label: "Sortino",
  value: "2.47",
  sub: "\u4E0B\u884C\u98CE\u9669"
})), /*#__PURE__*/React.createElement(WCard, {
  dense: true
}, /*#__PURE__*/React.createElement(WStat, {
  label: "\u6700\u5927\u56DE\u64A4",
  value: "\u22124.23%",
  tone: "neg"
})), /*#__PURE__*/React.createElement(WCard, {
  dense: true
}, /*#__PURE__*/React.createElement(WStat, {
  label: "\u80DC\u7387",
  value: "57%",
  sub: "142/248"
})), /*#__PURE__*/React.createElement(WCard, {
  dense: true
}, /*#__PURE__*/React.createElement(WStat, {
  label: "\u76C8\u4E8F\u6BD4",
  value: "2.3:1",
  sub: "avg R:R"
}))), /*#__PURE__*/React.createElement(WCard, {
  title: "\u7B56\u7565\u6536\u76CA\u5BF9\u6BD4 (90 \u5929)",
  right: /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 12,
      fontSize: 11,
      fontFamily: 'var(--ap-font-mono)'
    }
  }, /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement(WDot, {
    c: "var(--ap-mint)",
    glow: true
  }), " ", /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 6
    }
  }, "AlphaPilot")), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement(WDot, {
    c: "var(--ap-fg-4)"
  }), " ", /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 6,
      color: 'var(--ap-fg-3)'
    }
  }, "BTC HODL")), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement(WDot, {
    c: "var(--ap-violet)"
  }), " ", /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 6,
      color: 'var(--ap-fg-3)'
    }
  }, "ETH HODL")))
}, /*#__PURE__*/React.createElement("div", {
  style: {
    margin: '0 -18px -16px',
    position: 'relative'
  }
}, /*#__PURE__*/React.createElement("svg", {
  width: "100%",
  height: "240",
  viewBox: "0 0 1000 240",
  preserveAspectRatio: "none",
  style: {
    display: 'block'
  }
}, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("linearGradient", {
  id: "bt-mint",
  x1: "0",
  x2: "0",
  y1: "0",
  y2: "1"
}, /*#__PURE__*/React.createElement("stop", {
  offset: "0",
  stopColor: "var(--ap-mint)",
  stopOpacity: ".3"
}), /*#__PURE__*/React.createElement("stop", {
  offset: "1",
  stopColor: "var(--ap-mint)",
  stopOpacity: "0"
}))), [0, 1, 2, 3, 4].map(i => /*#__PURE__*/React.createElement("line", {
  key: i,
  x1: "0",
  x2: "1000",
  y1: i * 60,
  y2: i * 60,
  stroke: "var(--ap-line)",
  strokeOpacity: ".4"
})), /*#__PURE__*/React.createElement("path", {
  d: "M 0 200 C 100 195, 200 180, 300 160 S 500 130, 600 100 S 800 70, 1000 40",
  stroke: "var(--ap-mint)",
  strokeWidth: "2",
  fill: "none"
}), /*#__PURE__*/React.createElement("path", {
  d: "M 0 200 C 100 195, 200 180, 300 160 S 500 130, 600 100 S 800 70, 1000 40 L 1000 240 L 0 240 Z",
  fill: "url(#bt-mint)"
}), /*#__PURE__*/React.createElement("path", {
  d: "M 0 200 C 100 210, 200 205, 300 190 S 500 180, 600 170 S 800 160, 1000 140",
  stroke: "var(--ap-fg-4)",
  strokeWidth: "1.5",
  fill: "none",
  strokeDasharray: "4,3"
}), /*#__PURE__*/React.createElement("path", {
  d: "M 0 200 C 100 215, 200 220, 300 210 S 500 215, 600 195 S 800 175, 1000 165",
  stroke: "var(--ap-violet)",
  strokeWidth: "1.5",
  fill: "none",
  strokeDasharray: "4,3"
})))), /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr',
    gap: 20
  }
}, /*#__PURE__*/React.createElement(WCard, {
  title: "\u6708\u5EA6 PnL \u5206\u5E03"
}, (() => {
  const vals = [3.2, -1.4, 5.1, 2.8, -0.9, 4.7, 6.1, -2.3, 3.8, 1.9, 4.2, 2.5];
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const maxV = Math.max(...vals.map(Math.abs));
  const H = 170,
    zero = 100,
    scale = (zero - 30) / maxV; // positives above zero-line, negatives below
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'stretch',
      gap: 8,
      height: H,
      padding: '6px 0'
    }
  }, vals.map((v, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      flex: 1,
      position: 'relative'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 0,
      right: 0,
      top: zero,
      height: 1,
      background: 'var(--ap-line)',
      opacity: .6
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: '8%',
      right: '8%',
      borderRadius: 3,
      background: v >= 0 ? 'var(--ap-mint)' : 'var(--ap-rose)',
      opacity: .88,
      top: v >= 0 ? zero - v * scale : zero + 1,
      height: Math.max(3, Math.abs(v) * scale)
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 0,
      right: 0,
      textAlign: 'center',
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 10,
      color: v >= 0 ? 'var(--ap-mint)' : 'var(--ap-rose)',
      top: v >= 0 ? zero - v * scale - 16 : zero + Math.abs(v) * scale + 4
    }
  }, v >= 0 ? '+' : '', v.toFixed(1)), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 0,
      right: 0,
      bottom: 0,
      textAlign: 'center',
      fontSize: 9,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, months[i]))));
})()), /*#__PURE__*/React.createElement(WCard, {
  title: "\u4EA4\u6613\u7EDF\u8BA1"
}, [['总交易数', '248'], ['盈利笔数', '142'], ['亏损笔数', '106'], ['平均盈利', '+$124.80'], ['平均亏损', '−$54.30'], ['最大连续盈利', '8 笔'], ['最大连续亏损', '3 笔'], ['平均持仓', '2h 14m']].map(([l, v], i) => /*#__PURE__*/React.createElement("div", {
  key: i,
  style: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px 0',
    borderBottom: i < 7 ? '1px solid var(--ap-line-soft)' : 'none',
    fontSize: 12
  }
}, /*#__PURE__*/React.createElement("span", {
  style: {
    color: 'var(--ap-fg-3)'
  }
}, l), /*#__PURE__*/React.createElement("span", {
  style: {
    fontFamily: 'var(--ap-font-mono)',
    fontWeight: 600,
    color: 'var(--ap-fg-1)'
  }
}, v))))));

// =========================================================
// Strategy & Risk config
// =========================================================
const WRiskPage = () => /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 20
  }
}, /*#__PURE__*/React.createElement(WCard, {
  title: "\u7B56\u7565\u6846\u67B6 \xB7 \u53D7\u9650\u96C6"
}, /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12
  }
}, [{
  name: '趋势跟随',
  desc: 'EMA 20/50/200 排列 + ATR 确认',
  active: true,
  regimes: ['trending_up', 'trending_down']
}, {
  name: '突破确认',
  desc: '阻力位突破 + 成交量 1.4x+',
  active: false,
  regimes: ['trending_up', 'ranging']
}, {
  name: '观望模式',
  desc: 'chaotic regime 自动降级',
  active: false,
  regimes: ['chaotic']
}].map((s, i) => /*#__PURE__*/React.createElement("div", {
  key: i,
  style: {
    padding: 14,
    background: 'var(--ap-bg-3)',
    borderRadius: 10,
    border: '1px solid ' + (s.active ? 'var(--ap-mint)' : 'var(--ap-line-soft)')
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    marginBottom: 6
  }
}, /*#__PURE__*/React.createElement(WDot, {
  c: s.active ? 'var(--ap-mint)' : 'var(--ap-fg-4)',
  glow: s.active
}), /*#__PURE__*/React.createElement("span", {
  style: {
    fontSize: 13,
    fontWeight: 600
  }
}, s.name), s.active && /*#__PURE__*/React.createElement(WPill, {
  tone: "mint"
}, "ACTIVE"), /*#__PURE__*/React.createElement("div", {
  style: {
    marginLeft: 'auto',
    width: 36,
    height: 20,
    borderRadius: 999,
    background: s.active ? 'var(--ap-mint)' : 'var(--ap-bg-4)',
    position: 'relative',
    cursor: 'pointer'
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    position: 'absolute',
    top: 2,
    left: s.active ? 18 : 2,
    width: 16,
    height: 16,
    background: '#fff',
    borderRadius: '50%'
  }
}))), /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 12,
    color: 'var(--ap-fg-3)',
    marginBottom: 8
  }
}, s.desc), /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    gap: 6
  }
}, s.regimes.map(r => /*#__PURE__*/React.createElement(WPill, {
  key: r,
  tone: "default"
}, r))))))), /*#__PURE__*/React.createElement(WCard, {
  title: "\u786C\u98CE\u63A7 \xB7 \u4E0D\u53EF AI \u5B66\u4E60"
}, /*#__PURE__*/React.createElement("div", {
  style: {
    padding: '8px 12px',
    background: 'var(--ap-amber-soft)',
    borderRadius: 8,
    marginBottom: 14,
    display: 'flex',
    gap: 8,
    alignItems: 'flex-start',
    border: '1px solid rgba(240,185,11,.2)'
  }
}, /*#__PURE__*/React.createElement(Icon, {
  name: "alert",
  size: 14,
  color: "var(--ap-amber)"
}), /*#__PURE__*/React.createElement("span", {
  style: {
    fontSize: 11,
    color: 'var(--ap-fg-2)',
    lineHeight: 1.5
  }
}, "\u786C\u98CE\u63A7\u9608\u503C\u4E3A\u7CFB\u7EDF\u7EA7\u4FDD\u62A4\uFF0CAI \u4E0D\u53EF\u7ED5\u8FC7\u6216\u81EA\u6211\u4FEE\u6539\uFF0C\u6240\u6709\u51B3\u7B56\u5FC5\u987B\u901A\u8FC7\u5B88\u536B\u68C0\u67E5\u3002")), [{
  l: '单笔最大风险',
  v: '1.00%',
  max: '2.00%'
}, {
  l: '最大单币持仓',
  v: '15%',
  max: '25%'
}, {
  l: '日亏损熔断',
  v: '−2.00%',
  max: '−5.00%',
  tone: 'neg'
}, {
  l: '周亏损熔断',
  v: '−5.00%',
  max: '−10.00%',
  tone: 'neg'
}, {
  l: '连续亏损熔断',
  v: '3 笔',
  max: '5 笔'
}, {
  l: '最大相关度',
  v: '0.85',
  max: '1.00'
}, {
  l: '最小 R:R 比',
  v: '1.5',
  max: '1.0'
}, {
  l: '价差上限',
  v: '5bps',
  max: '10bps'
}].map((r, i, a) => /*#__PURE__*/React.createElement("div", {
  key: i,
  style: {
    padding: '10px 0',
    borderBottom: i < a.length - 1 ? '1px solid var(--ap-line-soft)' : 'none',
    display: 'flex',
    alignItems: 'center'
  }
}, /*#__PURE__*/React.createElement("span", {
  style: {
    flex: 1,
    fontSize: 13,
    color: 'var(--ap-fg-2)'
  }
}, r.l), /*#__PURE__*/React.createElement("span", {
  style: {
    fontFamily: 'var(--ap-font-mono)',
    fontSize: 13,
    fontWeight: 600,
    color: r.tone === 'neg' ? 'var(--ap-rose)' : 'var(--ap-fg-1)',
    marginRight: 8
  }
}, r.v), /*#__PURE__*/React.createElement("span", {
  style: {
    fontFamily: 'var(--ap-font-mono)',
    fontSize: 10,
    color: 'var(--ap-fg-4)'
  }
}, "max ", r.max)))), /*#__PURE__*/React.createElement(WCard, {
  title: "\u4EA4\u6613\u5BF9",
  style: {
    gridColumn: '1 / 3'
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 10
  }
}, [{
  s: 'BTCUSDT',
  tf: '15m',
  active: true
}, {
  s: 'ETHUSDT',
  tf: '15m',
  active: true
}, {
  s: 'SOLUSDT',
  tf: '15m',
  active: false
}, {
  s: 'BNBUSDT',
  tf: '15m',
  active: false
}].map((p, i) => /*#__PURE__*/React.createElement("div", {
  key: i,
  style: {
    padding: '10px 14px',
    background: 'var(--ap-bg-3)',
    borderRadius: 10,
    border: '1px solid ' + (p.active ? 'var(--ap-mint)' : 'var(--ap-line-soft)'),
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    minWidth: 160
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    width: 28,
    height: 28,
    borderRadius: '50%',
    background: 'linear-gradient(135deg,#F7931A,#8B4E0D)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
    fontWeight: 700,
    fontSize: 12
  }
}, p.s[0]), /*#__PURE__*/React.createElement("div", {
  style: {
    flex: 1
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    fontFamily: 'var(--ap-font-mono)',
    fontSize: 12,
    fontWeight: 600
  }
}, p.s), /*#__PURE__*/React.createElement("div", {
  style: {
    fontFamily: 'var(--ap-font-mono)',
    fontSize: 10,
    color: 'var(--ap-fg-3)'
  }
}, "tf ", p.tf)), /*#__PURE__*/React.createElement(WPill, {
  tone: p.active ? 'mint' : 'default'
}, p.active ? 'ON' : 'OFF'))), /*#__PURE__*/React.createElement("div", {
  style: {
    padding: '10px 14px',
    background: 'transparent',
    borderRadius: 10,
    border: '1.5px dashed var(--ap-line)',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    cursor: 'pointer',
    color: 'var(--ap-fg-3)',
    fontSize: 12
  }
}, "+ \u6DFB\u52A0\u4EA4\u6613\u5BF9"))));

// =========================================================
// Audit log
// =========================================================
const WAuditPage = () => /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    maxWidth: 1100
  }
}, /*#__PURE__*/React.createElement(WCard, {
  title: "\u5BA1\u8BA1\u65E5\u5FD7 \xB7 \u4ECA\u65E5",
  right: /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6
    }
  }, ['全部', 'AI', '守卫', '成交', '熔断'].map((t, i) => /*#__PURE__*/React.createElement("span", {
    key: t,
    style: {
      padding: '4px 10px',
      fontSize: 11,
      background: i === 0 ? 'var(--ap-bg-4)' : 'var(--ap-bg-3)',
      border: '1px solid var(--ap-line-soft)',
      borderRadius: 6,
      cursor: 'pointer',
      color: i === 0 ? 'var(--ap-fg-1)' : 'var(--ap-fg-3)'
    }
  }, t)))
}, /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    flexDirection: 'column',
    gap: 0
  }
}, W_MOCK.events.map((e, i) => /*#__PURE__*/React.createElement(WEventRow, {
  key: i,
  e: e
})))), /*#__PURE__*/React.createElement(WCard, {
  title: "AI \u65E5\u62A5"
}, /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 14,
    color: 'var(--ap-fg-2)',
    lineHeight: 1.7
  }
}, "\u672C\u65E5 ", /*#__PURE__*/React.createElement("b", {
  style: {
    color: 'var(--ap-fg-1)'
  }
}, "7 \u7B14"), "\u4EA4\u6613 \xB7 \u80DC\u7387 ", /*#__PURE__*/React.createElement("b", {
  style: {
    color: 'var(--ap-mint)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, "57%"), " \xB7 \u51C0\u6536\u76CA ", /*#__PURE__*/React.createElement("b", {
  style: {
    color: 'var(--ap-mint)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, "+1.82%"), "\u3002 BTCUSDT \u4E3B\u5BFC\u76C8\u5229\u8D21\u732E\uFF08", /*#__PURE__*/React.createElement("span", {
  style: {
    color: 'var(--ap-mint)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, "+$1,890"), "\uFF09\uFF0CETHUSDT \u53D7 chaotic regime \u62D6\u7D2F\uFF08", /*#__PURE__*/React.createElement("span", {
  style: {
    color: 'var(--ap-rose)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, "\u2212$642"), "\uFF09\u3002 \u5B88\u536B\u5171\u62E6\u622A ", /*#__PURE__*/React.createElement("b", {
  style: {
    color: 'var(--ap-amber)',
    fontFamily: 'var(--ap-font-mono)'
  }
}, "2 \u6B21"), "\uFF0C\u5747\u56E0 RR < 1.5\u3002\u5F15\u64CE\u5EF6\u8FDF ", /*#__PURE__*/React.createElement("span", {
  style: {
    fontFamily: 'var(--ap-font-mono)'
  }
}, "p50 42ms / p99 118ms"), "\uFF0C\u5065\u5EB7\u3002")));
Object.assign(window, {
  WDashboard,
  WAIPage,
  WPositionsPage,
  WBacktestPage,
  WRiskPage,
  WAuditPage
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/web_app/components/pages.jsx", error: String((e && e.message) || e) }); }

// ui_kits/web_app/components/settings.jsx
try { (() => {
// Settings — Exchange (mainnet/testnet + API keys) · LLM · Notifications · Account
// Uses W_MOCK atoms (WCard, WPill, WDot, Icon, wfmt...) from shell.jsx

// ---------- form atoms ----------
const SField = ({
  label,
  hint,
  children,
  htmlFor
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    marginBottom: 14
  }
}, /*#__PURE__*/React.createElement("label", {
  htmlFor: htmlFor,
  style: {
    fontSize: 11,
    color: 'var(--ap-fg-3)',
    letterSpacing: '.04em',
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
    lineHeight: 1.5
  }
}, label, hint && /*#__PURE__*/React.createElement("span", {
  style: {
    fontWeight: 400,
    color: 'var(--ap-fg-4)',
    letterSpacing: 0
  }
}, hint)), children);
const SInput = ({
  value,
  onChange,
  placeholder,
  mono = true,
  type = 'text',
  id,
  right
}) => {
  const [focus, setFocus] = React.useState(false);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      display: 'flex',
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("input", {
    id: id,
    type: type,
    value: value,
    onChange: e => onChange?.(e.target.value),
    placeholder: placeholder,
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      width: '100%',
      boxSizing: 'border-box',
      background: 'var(--ap-bg-3)',
      border: '1px solid ' + (focus ? 'var(--ap-mint)' : 'var(--ap-line)'),
      boxShadow: focus ? '0 0 0 3px rgba(0,211,149,.12)' : 'none',
      borderRadius: 10,
      padding: '11px 13px',
      paddingRight: right ? 78 : 13,
      color: 'var(--ap-fg-1)',
      fontSize: 13,
      fontFamily: mono ? 'var(--ap-font-mono)' : 'inherit',
      outline: 'none',
      transition: '.12s'
    }
  }), right && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      right: 8
    }
  }, right));
};
const SMasked = ({
  value,
  onChange,
  placeholder,
  id
}) => {
  const [show, setShow] = React.useState(false);
  return /*#__PURE__*/React.createElement(SInput, {
    id: id,
    value: value,
    onChange: onChange,
    placeholder: placeholder,
    type: show ? 'text' : 'password',
    right: /*#__PURE__*/React.createElement("button", {
      onClick: () => setShow(s => !s),
      style: {
        background: 'var(--ap-bg-4)',
        border: '1px solid var(--ap-line)',
        borderRadius: 6,
        padding: '4px 8px',
        color: 'var(--ap-fg-3)',
        fontSize: 10,
        cursor: 'pointer',
        fontFamily: 'var(--ap-font-mono)'
      }
    }, show ? '隐藏' : '显示')
  });
};
const SSwitch = ({
  on,
  onToggle
}) => /*#__PURE__*/React.createElement("div", {
  onClick: onToggle,
  role: "switch",
  "aria-checked": on,
  tabIndex: 0,
  style: {
    width: 42,
    height: 24,
    borderRadius: 999,
    background: on ? 'var(--ap-mint)' : 'var(--ap-bg-4)',
    position: 'relative',
    cursor: 'pointer',
    flexShrink: 0,
    transition: '.15s'
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    position: 'absolute',
    top: 3,
    left: on ? 21 : 3,
    width: 18,
    height: 18,
    background: '#fff',
    borderRadius: '50%',
    transition: '.15s'
  }
}));
const SSeg = ({
  options,
  value,
  onChange
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'inline-flex',
    background: 'var(--ap-bg-3)',
    borderRadius: 9,
    padding: 3,
    border: '1px solid var(--ap-line)'
  }
}, options.map(o => /*#__PURE__*/React.createElement("div", {
  key: o.v,
  onClick: () => onChange(o.v),
  style: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 12,
    padding: '6px 14px',
    borderRadius: 6,
    cursor: 'pointer',
    fontWeight: 500,
    background: value === o.v ? 'var(--ap-bg-4)' : 'transparent',
    color: value === o.v ? 'var(--ap-fg-1)' : 'var(--ap-fg-3)',
    transition: '.12s'
  }
}, o.dot && /*#__PURE__*/React.createElement(WDot, {
  c: o.dot,
  glow: value === o.v
}), o.l)));
const SSelect = ({
  value,
  onChange,
  options,
  id
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    position: 'relative'
  }
}, /*#__PURE__*/React.createElement("select", {
  id: id,
  value: value,
  onChange: e => onChange(e.target.value),
  style: {
    width: '100%',
    appearance: 'none',
    background: 'var(--ap-bg-3)',
    border: '1px solid var(--ap-line)',
    borderRadius: 10,
    padding: '11px 36px 11px 13px',
    color: 'var(--ap-fg-1)',
    fontSize: 13,
    fontFamily: 'inherit',
    outline: 'none',
    cursor: 'pointer'
  }
}, options.map(o => /*#__PURE__*/React.createElement("option", {
  key: o.v,
  value: o.v,
  style: {
    background: 'var(--ap-bg-2)'
  }
}, o.l))), /*#__PURE__*/React.createElement("div", {
  style: {
    position: 'absolute',
    right: 12,
    top: '50%',
    transform: 'translateY(-50%)',
    pointerEvents: 'none'
  }
}, /*#__PURE__*/React.createElement(Icon, {
  name: "chevron_down",
  size: 14,
  color: "var(--ap-fg-3)"
})));
const STestBtn = ({
  onTest,
  state
}) => {
  // state: idle | testing | ok | fail
  const cfg = {
    idle: {
      l: '测试连接',
      bg: 'var(--ap-bg-4)',
      c: 'var(--ap-fg-1)',
      bd: 'var(--ap-line)'
    },
    testing: {
      l: '测试中…',
      bg: 'var(--ap-bg-4)',
      c: 'var(--ap-fg-3)',
      bd: 'var(--ap-line)'
    },
    ok: {
      l: '连接成功',
      bg: 'var(--ap-mint-soft)',
      c: 'var(--ap-mint)',
      bd: 'var(--ap-mint)'
    },
    fail: {
      l: '连接失败',
      bg: 'var(--ap-rose-soft)',
      c: 'var(--ap-rose)',
      bd: 'var(--ap-rose)'
    }
  }[state];
  return /*#__PURE__*/React.createElement("button", {
    onClick: onTest,
    disabled: state === 'testing',
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      padding: '9px 16px',
      borderRadius: 9,
      border: `1px solid ${cfg.bd}`,
      background: cfg.bg,
      color: cfg.c,
      fontSize: 12,
      fontWeight: 600,
      cursor: state === 'testing' ? 'default' : 'pointer',
      fontFamily: 'inherit'
    }
  }, state === 'ok' && /*#__PURE__*/React.createElement(Icon, {
    name: "check",
    size: 13,
    strokeWidth: 2.4
  }), state === 'fail' && /*#__PURE__*/React.createElement(Icon, {
    name: "x",
    size: 13,
    strokeWidth: 2.4
  }), state === 'testing' && /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: 'currentColor',
      animation: 'apblink 1s infinite'
    }
  }), cfg.l);
};

// ---------- main page ----------
const WSettingsPage = () => {
  const [tab, setTab] = React.useState('exchange');
  const tabs = [{
    id: 'exchange',
    label: '交易所连接',
    icon: 'layers'
  }, {
    id: 'llm',
    label: 'AI 模型',
    icon: 'brain'
  }, {
    id: 'notify',
    label: '通知',
    icon: 'bell'
  }, {
    id: 'account',
    label: '账户偏好',
    icon: 'settings'
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 24,
      maxWidth: 1000
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 200,
      flexShrink: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: 2
    }
  }, tabs.map(t => /*#__PURE__*/React.createElement("div", {
    key: t.id,
    onClick: () => setTab(t.id),
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '10px 12px',
      borderRadius: 9,
      cursor: 'pointer',
      background: tab === t.id ? 'var(--ap-bg-2)' : 'transparent',
      color: tab === t.id ? 'var(--ap-fg-1)' : 'var(--ap-fg-3)',
      fontSize: 13,
      fontWeight: 500,
      border: '1px solid ' + (tab === t.id ? 'var(--ap-line-soft)' : 'transparent')
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: t.icon,
    size: 15,
    color: tab === t.id ? 'var(--ap-mint)' : 'currentColor'
  }), t.label))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: 20
    }
  }, tab === 'exchange' && /*#__PURE__*/React.createElement(ExchangeSettings, null), tab === 'llm' && /*#__PURE__*/React.createElement(LLMSettings, null), tab === 'notify' && /*#__PURE__*/React.createElement(NotifySettings, null), tab === 'account' && /*#__PURE__*/React.createElement(AccountSettings, null)));
};

// ---------- Exchange ----------
const ExchangeSettings = () => {
  const [net, setNet] = React.useState('mainnet');
  const [test, setTest] = React.useState('ok');
  const [key, setKey] = React.useState('bnx_live_8a3f2c91d4e7');
  const [secret, setSecret] = React.useState('••••••••••••••••3f2a');
  const runTest = () => {
    setTest('testing');
    setTimeout(() => setTest('ok'), 1200);
  };
  const isTestnet = net === 'testnet';
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(WCard, {
    title: "\u4EA4\u6613\u6240"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 12
    }
  }, [{
    id: 'binance',
    name: 'Binance',
    logo: '../../assets/binance_logo.svg',
    sub: 'USDT-M 永续 · MVP 首选',
    active: true
  }, {
    id: 'hyperliquid',
    name: 'Hyperliquid',
    logo: '../../assets/hyperliquid_logo.svg',
    sub: '去中心化 · 钱包授权',
    active: false
  }].map(ex => /*#__PURE__*/React.createElement("div", {
    key: ex.id,
    style: {
      flex: 1,
      padding: 16,
      borderRadius: 12,
      background: 'var(--ap-bg-3)',
      border: '1px solid ' + (ex.active ? 'var(--ap-mint)' : 'var(--ap-line-soft)'),
      position: 'relative',
      cursor: 'pointer'
    }
  }, ex.active && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 12,
      right: 12
    }
  }, /*#__PURE__*/React.createElement(WPill, {
    tone: "mint"
  }, "\u5DF2\u8FDE\u63A5")), /*#__PURE__*/React.createElement("img", {
    src: ex.logo,
    style: {
      width: 28,
      height: 28,
      marginBottom: 10
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 600,
      marginBottom: 2
    }
  }, ex.name), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)'
    }
  }, ex.sub))))), /*#__PURE__*/React.createElement(WCard, {
    title: "Binance \xB7 \u7F51\u7EDC\u4E0E API",
    right: /*#__PURE__*/React.createElement(STestBtn, {
      onTest: runTest,
      state: test
    })
  }, /*#__PURE__*/React.createElement(SField, {
    label: "\u8FD0\u884C\u7F51\u7EDC",
    hint: isTestnet ? '· 测试盘使用模拟资金，安全演练' : '· 主网为真实资金交易，请谨慎'
  }, /*#__PURE__*/React.createElement(SSeg, {
    value: net,
    onChange: v => {
      setNet(v);
      setTest('idle');
    },
    options: [{
      v: 'mainnet',
      l: '主网 Mainnet',
      dot: 'var(--ap-rose)'
    }, {
      v: 'testnet',
      l: '测试网 Testnet',
      dot: 'var(--ap-cyan)'
    }]
  })), isTestnet && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      alignItems: 'flex-start',
      padding: '10px 12px',
      background: 'var(--ap-cyan-soft)',
      borderRadius: 8,
      marginBottom: 14,
      border: '1px solid rgba(34,211,238,.2)'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "alert",
    size: 14,
    color: "var(--ap-cyan)"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-2)',
      lineHeight: 1.5
    }
  }, "\u5F53\u524D\u4E3A ", /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--ap-cyan)'
    }
  }, "\u6D4B\u8BD5\u7F51"), "\u3002\u6240\u6709\u6210\u4EA4\u4E3A\u6A21\u62DF\uFF0C\u4E0D\u6D89\u53CA\u771F\u5B9E\u8D44\u91D1\u3002\u5EFA\u8BAE\u5148\u5728\u6D4B\u8BD5\u7F51\u9A8C\u8BC1\u7B56\u7565\uFF0C\u518D\u5207\u4E3B\u7F51\u3002")), !isTestnet && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      alignItems: 'flex-start',
      padding: '10px 12px',
      background: 'var(--ap-rose-soft)',
      borderRadius: 8,
      marginBottom: 14,
      border: '1px solid rgba(255,77,109,.2)'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "alert",
    size: 14,
    color: "var(--ap-rose)"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-2)',
      lineHeight: 1.5
    }
  }, "\u5F53\u524D\u4E3A ", /*#__PURE__*/React.createElement("b", {
    style: {
      color: 'var(--ap-rose)'
    }
  }, "\u4E3B\u7F51"), "\uFF0CAI \u5C06\u4F7F\u7528\u771F\u5B9E\u8D44\u91D1\u4E0B\u5355\u3002\u8BF7\u786E\u8BA4 API \u4EC5\u5F00\u542F\u300C\u5408\u7EA6\u4EA4\u6613\u300D\u6743\u9650\uFF0C", /*#__PURE__*/React.createElement("b", null, "\u5207\u52FF"), "\u5F00\u542F\u300C\u63D0\u73B0\u300D\u6743\u9650\u3002")), /*#__PURE__*/React.createElement(SField, {
    label: "API Key",
    htmlFor: "bn-key"
  }, /*#__PURE__*/React.createElement(SInput, {
    id: "bn-key",
    value: key,
    onChange: setKey,
    placeholder: "\u8F93\u5165 Binance API Key"
  })), /*#__PURE__*/React.createElement(SField, {
    label: "API Secret",
    htmlFor: "bn-sec"
  }, /*#__PURE__*/React.createElement(SMasked, {
    id: "bn-sec",
    value: secret,
    onChange: setSecret,
    placeholder: "\u8F93\u5165 Binance API Secret"
  })), /*#__PURE__*/React.createElement(SField, {
    label: "\u6743\u9650\u6821\u9A8C",
    hint: "\xB7 \u81EA\u52A8\u68C0\u6D4B API \u6743\u9650\u8303\u56F4"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 6
    }
  }, [{
    l: '读取账户与持仓',
    ok: true
  }, {
    l: '合约交易（下单/撤单）',
    ok: true
  }, {
    l: '提现权限',
    ok: false,
    want: false
  }].map((p, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '8px 12px',
      background: 'var(--ap-bg-3)',
      borderRadius: 8,
      fontSize: 12
    }
  }, p.want === false ? /*#__PURE__*/React.createElement("span", {
    style: {
      width: 16,
      height: 16,
      borderRadius: 4,
      background: p.ok ? 'var(--ap-rose-soft)' : 'var(--ap-mint-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: p.ok ? 'alert' : 'check',
    size: 11,
    color: p.ok ? 'var(--ap-rose)' : 'var(--ap-mint)',
    strokeWidth: 2.6
  })) : /*#__PURE__*/React.createElement("span", {
    style: {
      width: 16,
      height: 16,
      borderRadius: 4,
      background: p.ok ? 'var(--ap-mint-soft)' : 'var(--ap-bg-4)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "check",
    size: 11,
    color: p.ok ? 'var(--ap-mint)' : 'var(--ap-fg-4)',
    strokeWidth: 2.6
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      color: p.want === false && p.ok ? 'var(--ap-rose)' : 'var(--ap-fg-2)'
    }
  }, p.l), p.want === false && p.ok && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: 'var(--ap-rose)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "\u5EFA\u8BAE\u5173\u95ED"), p.want === false && !p.ok && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: 'var(--ap-mint)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "\u5DF2\u5173\u95ED \u2713"))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      marginTop: 6
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '10px 18px',
      borderRadius: 10,
      border: 'none',
      background: 'var(--ap-mint)',
      color: 'var(--ap-bg-0)',
      fontSize: 13,
      fontWeight: 700,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u4FDD\u5B58\u914D\u7F6E"), /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '10px 18px',
      borderRadius: 10,
      border: '1px solid var(--ap-line)',
      background: 'var(--ap-bg-3)',
      color: 'var(--ap-fg-2)',
      fontSize: 13,
      fontWeight: 500,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u65AD\u5F00\u8FDE\u63A5"))));
};

// ---------- LLM ----------
const LLMSettings = () => {
  const [provider, setProvider] = React.useState('deepseek');
  const [test, setTest] = React.useState('idle');
  const [temp, setTemp] = React.useState(0.3);
  const [key, setKey] = React.useState('sk-••••••••••••••••a1b2');
  const runTest = () => {
    setTest('testing');
    setTimeout(() => setTest('ok'), 1100);
  };
  const providers = {
    deepseek: {
      models: ['deepseek-chat', 'deepseek-reasoner'],
      base: 'https://api.deepseek.com/v1',
      rec: true
    },
    openai: {
      models: ['gpt-5', 'o1', 'gpt-4o', 'gpt-4-turbo'],
      base: 'https://api.openai.com/v1'
    },
    anthropic: {
      models: ['claude-sonnet-4.5', 'claude-opus-4.1'],
      base: 'https://api.anthropic.com/v1'
    },
    custom: {
      models: ['custom-model'],
      base: 'https://your-endpoint/v1'
    }
  };
  const [model, setModel] = React.useState('deepseek-chat');
  const cur = providers[provider];
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(WCard, {
    title: "\u6A21\u578B\u63D0\u4F9B\u65B9"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(4,1fr)',
      gap: 10,
      marginBottom: 4
    }
  }, [{
    id: 'deepseek',
    l: 'Deepseek',
    sub: '性价比首选'
  }, {
    id: 'openai',
    l: 'OpenAI',
    sub: 'GPT-5 / o1'
  }, {
    id: 'anthropic',
    l: 'Anthropic',
    sub: 'Claude'
  }, {
    id: 'custom',
    l: '自定义',
    sub: '兼容 OpenAI'
  }].map(p => /*#__PURE__*/React.createElement("div", {
    key: p.id,
    onClick: () => {
      setProvider(p.id);
      setModel(providers[p.id].models[0]);
      setTest('idle');
    },
    style: {
      padding: '12px 14px',
      borderRadius: 10,
      background: 'var(--ap-bg-3)',
      border: '1px solid ' + (provider === p.id ? 'var(--ap-violet)' : 'var(--ap-line-soft)'),
      cursor: 'pointer',
      position: 'relative'
    }
  }, providers[p.id].rec && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 8,
      right: 8
    }
  }, /*#__PURE__*/React.createElement(WPill, {
    tone: "violet"
  }, "\u63A8\u8350")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600,
      marginBottom: 2
    }
  }, p.l), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-fg-3)'
    }
  }, p.sub))))), /*#__PURE__*/React.createElement(WCard, {
    title: "\u6A21\u578B\u914D\u7F6E",
    right: /*#__PURE__*/React.createElement(STestBtn, {
      onTest: runTest,
      state: test
    })
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 14
    }
  }, /*#__PURE__*/React.createElement(SField, {
    label: "\u6A21\u578B"
  }, /*#__PURE__*/React.createElement(SSelect, {
    value: model,
    onChange: setModel,
    options: cur.models.map(m => ({
      v: m,
      l: m
    }))
  })), /*#__PURE__*/React.createElement(SField, {
    label: "API Base URL"
  }, /*#__PURE__*/React.createElement(SInput, {
    value: cur.base,
    onChange: () => {},
    mono: true
  }))), /*#__PURE__*/React.createElement(SField, {
    label: "API Key",
    htmlFor: "llm-key"
  }, /*#__PURE__*/React.createElement(SMasked, {
    id: "llm-key",
    value: key,
    onChange: setKey,
    placeholder: "sk-..."
  })), /*#__PURE__*/React.createElement(SField, {
    label: `温度 · ${temp.toFixed(2)}`,
    hint: "\xB7 \u8D8A\u4F4E\u8D8A\u786E\u5B9A\uFF0C\u4EA4\u6613\u51B3\u7B56\u5EFA\u8BAE 0.2\u20130.4"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 14
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "range",
    min: "0",
    max: "1",
    step: "0.05",
    value: temp,
    onChange: e => setTemp(parseFloat(e.target.value)),
    style: {
      flex: 1,
      accentColor: 'var(--ap-violet)'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 13,
      color: 'var(--ap-violet)',
      fontWeight: 600,
      width: 40,
      textAlign: 'right'
    }
  }, temp.toFixed(2)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 14
    }
  }, /*#__PURE__*/React.createElement(SField, {
    label: "\u6700\u5927 Token",
    hint: ""
  }, /*#__PURE__*/React.createElement(SInput, {
    value: "4096",
    onChange: () => {},
    mono: true
  })), /*#__PURE__*/React.createElement(SField, {
    label: "\u8D85\u65F6 (\u79D2)",
    hint: ""
  }, /*#__PURE__*/React.createElement(SInput, {
    value: "30",
    onChange: () => {},
    mono: true
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      marginTop: 6
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '10px 18px',
      borderRadius: 10,
      border: 'none',
      background: 'var(--ap-violet)',
      color: '#fff',
      fontSize: 13,
      fontWeight: 700,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u4FDD\u5B58\u6A21\u578B\u914D\u7F6E"))), /*#__PURE__*/React.createElement(WCard, {
    title: "Agent \u6A21\u578B\u5206\u5DE5",
    right: /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 11,
        color: 'var(--ap-fg-3)',
        fontFamily: 'var(--ap-font-mono)'
      }
    }, "\u53EF\u5206\u522B\u6307\u5B9A")
  }, [{
    a: '决策 Agent',
    m: 'deepseek-reasoner',
    desc: '交易决策推理'
  }, {
    a: '信号 Agent',
    m: 'deepseek-chat',
    desc: '市场信号识别'
  }, {
    a: '复盘 Agent',
    m: 'deepseek-chat',
    desc: '归因与诊断'
  }].map((r, i, arr) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '11px 0',
      borderBottom: i < arr.length - 1 ? '1px solid var(--ap-line-soft)' : 'none'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 30,
      height: 30,
      borderRadius: 8,
      background: 'var(--ap-violet-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "brain",
    size: 15,
    color: "var(--ap-violet)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600
    }
  }, r.a), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)'
    }
  }, r.desc)), /*#__PURE__*/React.createElement(WPill, {
    tone: "default"
  }, r.m)))));
};

// ---------- Notifications ----------
const NotifySettings = () => {
  const [tg, setTg] = React.useState(true);
  const [dc, setDc] = React.useState(false);
  const [events, setEvents] = React.useState({
    open: true,
    close: true,
    halt: true,
    reject: false,
    daily: true
  });
  const toggle = k => setEvents(e => ({
    ...e,
    [k]: !e[k]
  }));
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(WCard, {
    title: "\u63A8\u9001\u6E20\u9053"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '11px 0',
      borderBottom: '1px solid var(--ap-line-soft)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      borderRadius: 8,
      background: 'var(--ap-cyan-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "bell",
    size: 16,
    color: "var(--ap-cyan)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600
    }
  }, "Telegram"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "@alphapilot_bot \xB7 \u5DF2\u7ED1\u5B9A")), /*#__PURE__*/React.createElement(SSwitch, {
    on: tg,
    onToggle: () => setTg(!tg)
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '11px 0'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      borderRadius: 8,
      background: 'var(--ap-violet-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "bell",
    size: 16,
    color: "var(--ap-violet)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600
    }
  }, "Discord"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)'
    }
  }, "\u672A\u7ED1\u5B9A")), /*#__PURE__*/React.createElement(SSwitch, {
    on: dc,
    onToggle: () => setDc(!dc)
  }))), /*#__PURE__*/React.createElement(WCard, {
    title: "\u63A8\u9001\u4E8B\u4EF6"
  }, [{
    k: 'open',
    l: '开仓成交',
    d: 'AI 开仓并成交时'
  }, {
    k: 'close',
    l: '平仓成交',
    d: '止盈/止损/手动平仓'
  }, {
    k: 'halt',
    l: '熔断触发',
    d: '日亏/连亏触发熔断（强烈建议开启）',
    warn: true
  }, {
    k: 'reject',
    l: '守卫拦截',
    d: '决策被守卫拒绝时'
  }, {
    k: 'daily',
    l: '每日报告',
    d: '每日收盘 AI 日报'
  }].map((e, i, arr) => /*#__PURE__*/React.createElement("div", {
    key: e.k,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '11px 0',
      borderBottom: i < arr.length - 1 ? '1px solid var(--ap-line-soft)' : 'none'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, e.l, e.warn && /*#__PURE__*/React.createElement(WPill, {
    tone: "rose"
  }, "\u5173\u952E")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      marginTop: 2
    }
  }, e.d)), /*#__PURE__*/React.createElement(SSwitch, {
    on: events[e.k],
    onToggle: () => toggle(e.k)
  })))));
};

// ---------- Account ----------
const AccountSettings = () => {
  const [lang, setLang] = React.useState('zh');
  const [tz, setTz] = React.useState('utc8');
  const [twofa, setTwofa] = React.useState(true);
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(WCard, {
    title: "\u504F\u597D"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 14
    }
  }, /*#__PURE__*/React.createElement(SField, {
    label: "\u754C\u9762\u8BED\u8A00"
  }, /*#__PURE__*/React.createElement(SSeg, {
    value: lang,
    onChange: setLang,
    options: [{
      v: 'zh',
      l: '中文'
    }, {
      v: 'en',
      l: 'English'
    }]
  })), /*#__PURE__*/React.createElement(SField, {
    label: "\u65F6\u533A"
  }, /*#__PURE__*/React.createElement(SSelect, {
    value: tz,
    onChange: setTz,
    options: [{
      v: 'utc8',
      l: 'UTC+8 北京'
    }, {
      v: 'utc0',
      l: 'UTC 世界时'
    }, {
      v: 'utc-5',
      l: 'UTC-5 纽约'
    }]
  })))), /*#__PURE__*/React.createElement(WCard, {
    title: "\u5B89\u5168"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '11px 0',
      borderBottom: '1px solid var(--ap-line-soft)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 500
    }
  }, "\u53CC\u91CD\u9A8C\u8BC1 2FA"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)'
    }
  }, "\u767B\u5F55\u4E0E\u63D0\u73B0\u64CD\u4F5C\u9700\u4E8C\u6B21\u9A8C\u8BC1")), /*#__PURE__*/React.createElement(WPill, {
    tone: "mint"
  }, "\u5DF2\u542F\u7528"), /*#__PURE__*/React.createElement(SSwitch, {
    on: twofa,
    onToggle: () => setTwofa(!twofa)
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '11px 0'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 500
    }
  }, "\u4F1A\u8BDD\u4E0E\u8BBE\u5907"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "2 \u4E2A\u6D3B\u8DC3\u4F1A\u8BDD")), /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '7px 14px',
      borderRadius: 8,
      border: '1px solid var(--ap-line)',
      background: 'var(--ap-bg-3)',
      color: 'var(--ap-fg-2)',
      fontSize: 12,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u7BA1\u7406"))), /*#__PURE__*/React.createElement(WCard, {
    title: "\u5371\u9669\u533A",
    style: {
      borderColor: 'rgba(255,77,109,.25)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: 'var(--ap-rose)'
    }
  }, "\u6E05\u7A7A\u6240\u6709\u6301\u4ED3\u5E76\u505C\u6B62\u5F15\u64CE"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)'
    }
  }, "\u7ACB\u5373\u5E02\u4EF7\u5E73\u6389\u6240\u6709\u4ED3\u4F4D\u5E76\u6682\u505C\u81EA\u52A8\u4EA4\u6613")), /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '9px 16px',
      borderRadius: 9,
      border: '1px solid var(--ap-rose)',
      background: 'var(--ap-rose-soft)',
      color: 'var(--ap-rose)',
      fontSize: 12,
      fontWeight: 600,
      cursor: 'pointer',
      fontFamily: 'inherit'
    }
  }, "\u7D27\u6025\u505C\u6B62"))));
};
Object.assign(window, {
  WSettingsPage
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/web_app/components/settings.jsx", error: String((e && e.message) || e) }); }

// ui_kits/web_app/components/shell.jsx
try { (() => {
// Web shell: sidebar, topbar, command palette hint, page scaffolding
// Also re-exports common atoms from the mobile kit (for same naming) with web-scale variants.

// =========== mock data ===========
const W_MOCK = {
  equity: 128450.73,
  equityChange: 2291.40,
  equityChangePct: 1.82,
  todayPnl: 1248.05,
  todayPnlPct: 0.98,
  weekPnl: 5420.11,
  weekPnlPct: 4.32,
  mtdPnl: 8934.50,
  mtdPnlPct: 7.45,
  positionsPct: 12,
  dayLossPct: -0.48,
  riskState: 'OK',
  tradesToday: 7,
  winRate: 57,
  regime: 'trending_up',
  sharpe: 1.84,
  maxDD: -4.23,
  avgHold: '2h 14m',
  positions: [{
    sym: 'BTCUSDT',
    side: 'LONG',
    qty: 0.048,
    entry: 67420.50,
    mark: 68863.92,
    pnl: 69.29,
    pnlPct: 2.14,
    margin: 2.5,
    sl: 64210,
    tp: 68900,
    age: '2h 13m',
    strat: '趋势跟随'
  }, {
    sym: 'ETHUSDT',
    side: 'LONG',
    qty: 0.82,
    entry: 3240.00,
    mark: 3219.92,
    pnl: -16.47,
    pnlPct: -0.62,
    margin: 1.8,
    sl: 3120,
    tp: 3380,
    age: '45m',
    strat: '突破确认'
  }],
  orders: [{
    t: '14:23:09',
    sym: 'BTCUSDT',
    side: 'BUY',
    type: 'MARKET',
    qty: 0.048,
    price: 67420.50,
    status: 'FILLED'
  }, {
    t: '14:23:09',
    sym: 'BTCUSDT',
    side: 'SELL',
    type: 'STOP',
    qty: 0.048,
    price: 64210,
    status: 'WORKING'
  }, {
    t: '14:23:09',
    sym: 'BTCUSDT',
    side: 'SELL',
    type: 'TAKE_PROFIT',
    qty: 0.048,
    price: 68900,
    status: 'WORKING'
  }, {
    t: '13:45:12',
    sym: 'ETHUSDT',
    side: 'BUY',
    type: 'LIMIT',
    qty: 0.82,
    price: 3240,
    status: 'FILLED'
  }, {
    t: '10:15:30',
    sym: 'BTCUSDT',
    side: 'SELL',
    type: 'MARKET',
    qty: 0.062,
    price: 68903.20,
    status: 'FILLED'
  }],
  decisions: [{
    id: 'd_7f3a9b',
    t: '14:23:08',
    sym: 'BTCUSDT',
    tf: '15m',
    action: 'OPEN_LONG',
    conf: 0.78,
    strat: '趋势跟随',
    sl: 64210,
    tp: 68900,
    size: '2.5%',
    guard: 'PASS',
    entry: 67420.50,
    reason: 'EMA20>EMA50>EMA200 金叉排列，1h 成交量较均值放大 1.4x，回踩 EMA20 未破，确认突破有效。',
    features: [{
      k: 'regime',
      v: 'trending_up',
      ok: true
    }, {
      k: 'EMA_align',
      v: '20>50>200',
      ok: true
    }, {
      k: 'vol_mult',
      v: '1.4x',
      ok: true
    }, {
      k: 'ATR_14',
      v: '1.82%',
      ok: true
    }, {
      k: 'RSI_14',
      v: '58',
      ok: true
    }, {
      k: 'BB_width',
      v: '0.043',
      ok: true
    }],
    guards: [{
      k: 'regime_match',
      ok: true,
      note: 'trending_up ∈ strategy.allowed'
    }, {
      k: 'max_per_trade_risk',
      ok: true,
      note: '0.8% < 1.0%'
    }, {
      k: 'max_position_size',
      ok: true,
      note: '2.5% < 15%'
    }, {
      k: 'daily_loss_limit',
      ok: true,
      note: '-0.48% > -2.0%'
    }, {
      k: 'RR_ratio',
      ok: true,
      note: '2.3 > 1.5'
    }, {
      k: 'correlation_cap',
      ok: true,
      note: 'BTC-ETH corr 0.68 < 0.85'
    }, {
      k: 'spread_check',
      ok: true,
      note: '1.2bps < 5bps'
    }, {
      k: 'cooldown',
      ok: true,
      note: 'last trade 3h ago'
    }]
  }, {
    id: 'd_7f3a9a',
    t: '13:45:00',
    sym: 'ETHUSDT',
    tf: '15m',
    action: 'HOLD',
    conf: 0.42,
    strat: '观望模式',
    guard: 'DEGRADE',
    reason: '波动率进入高位，regime 由 trending_up 切换为 chaotic，降级为观望。'
  }, {
    id: 'd_7f3a99',
    t: '12:30:00',
    sym: 'BTCUSDT',
    tf: '15m',
    action: 'OPEN_LONG',
    conf: 0.71,
    strat: '突破确认',
    guard: 'REJECT',
    reason: '触发风险收益比 <1.5 检查，守卫拒绝，回退 HOLD。'
  }, {
    id: 'd_7f3a98',
    t: '10:15:00',
    sym: 'BTCUSDT',
    tf: '15m',
    action: 'CLOSE_LONG',
    conf: 0.85,
    strat: '止盈执行',
    guard: 'PASS',
    reason: '达到 TP 价位，执行平仓，本笔 +1.82%。',
    entry: 66100
  }, {
    id: 'd_7f3a97',
    t: '09:02:00',
    sym: 'ETHUSDT',
    tf: '15m',
    action: 'OPEN_LONG',
    conf: 0.66,
    strat: '突破确认',
    guard: 'PASS',
    reason: '突破前高 3240，成交量放大，进场。'
  }],
  events: [{
    t: '14:23:09',
    kind: 'fill',
    msg: 'BTCUSDT 市价成交 0.048 @ 67,420.50',
    color: 'mint'
  }, {
    t: '14:23:09',
    kind: 'order',
    msg: '止损挂单 64,210 · 止盈 68,900',
    color: 'fg'
  }, {
    t: '14:23:08',
    kind: 'guard',
    msg: '守卫通过 PASS · 检查 8/8',
    color: 'mint'
  }, {
    t: '14:23:08',
    kind: 'ai',
    msg: 'AI OPEN_LONG BTCUSDT · 置信度 0.78',
    color: 'violet'
  }, {
    t: '13:45:05',
    kind: 'guard',
    msg: '守卫降级 DEGRADE · regime 异常',
    color: 'amber'
  }, {
    t: '13:45:00',
    kind: 'ai',
    msg: 'AI HOLD ETHUSDT · 置信度 0.42',
    color: 'violet'
  }, {
    t: '12:30:12',
    kind: 'guard',
    msg: '守卫拒绝 REJECT · RR<1.5 · 回退 HOLD',
    color: 'rose'
  }, {
    t: '12:30:08',
    kind: 'ai',
    msg: 'AI OPEN_LONG BTCUSDT · 置信度 0.71',
    color: 'violet'
  }, {
    t: '10:15:30',
    kind: 'fill',
    msg: 'BTCUSDT 平仓 @ 68,903 · +1.82%',
    color: 'mint'
  }, {
    t: '10:15:29',
    kind: 'ai',
    msg: 'AI CLOSE_LONG BTCUSDT · 置信度 0.85',
    color: 'violet'
  }, {
    t: '09:02:14',
    kind: 'fill',
    msg: 'ETHUSDT 市价成交 0.82 @ 3,240.00',
    color: 'mint'
  }, {
    t: '09:02:10',
    kind: 'ai',
    msg: 'AI OPEN_LONG ETHUSDT · 置信度 0.66',
    color: 'violet'
  }]
};

// =========== atoms (web-scale) ===========
const WPill = ({
  children,
  tone = 'default'
}) => {
  const tones = {
    mint: {
      bg: 'var(--ap-mint-soft)',
      c: 'var(--ap-mint)'
    },
    rose: {
      bg: 'var(--ap-rose-soft)',
      c: 'var(--ap-rose)'
    },
    amber: {
      bg: 'var(--ap-amber-soft)',
      c: 'var(--ap-amber)'
    },
    violet: {
      bg: 'var(--ap-violet-soft)',
      c: 'var(--ap-violet)'
    },
    cyan: {
      bg: 'var(--ap-cyan-soft)',
      c: 'var(--ap-cyan)'
    },
    default: {
      bg: 'var(--ap-bg-3)',
      c: 'var(--ap-fg-2)'
    }
  };
  const s = tones[tone] || tones.default;
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 4,
      fontSize: 10.5,
      padding: '2px 8px',
      borderRadius: 999,
      background: s.bg,
      color: s.c,
      fontWeight: 600,
      fontFamily: 'var(--ap-font-mono)',
      letterSpacing: '.04em',
      whiteSpace: 'nowrap'
    }
  }, children);
};
const WDot = ({
  c,
  glow,
  size = 6
}) => /*#__PURE__*/React.createElement("span", {
  style: {
    width: size,
    height: size,
    borderRadius: '50%',
    background: c,
    boxShadow: glow ? `0 0 6px ${c}` : 'none',
    display: 'inline-block',
    flexShrink: 0
  }
});
const WCard = ({
  children,
  style,
  title,
  right,
  dense,
  glow
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    background: 'var(--ap-bg-2)',
    borderRadius: 'var(--ap-r-md)',
    border: '1px solid var(--ap-line-soft)',
    overflow: 'hidden',
    ...(glow ? {
      boxShadow: '0 0 0 1px var(--ap-violet), 0 0 40px rgba(124,92,255,.12)'
    } : {}),
    ...style
  }
}, title && /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: dense ? '10px 14px' : '14px 18px',
    borderBottom: '1px solid var(--ap-line-soft)'
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    fontSize: 11,
    color: 'var(--ap-fg-3)',
    letterSpacing: '.08em',
    textTransform: 'uppercase',
    fontWeight: 600,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis'
  }
}, title), right), /*#__PURE__*/React.createElement("div", {
  style: {
    padding: dense ? '12px 14px' : '16px 18px'
  }
}, children));
const WStat = ({
  label,
  value,
  sub,
  tone,
  size = 'md'
}) => {
  const fs = size === 'lg' ? 28 : size === 'sm' ? 16 : 22;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10.5,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.08em',
      textTransform: 'uppercase',
      fontWeight: 500
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: fs,
      fontWeight: 700,
      letterSpacing: '-.02em',
      color: tone === 'pos' ? 'var(--ap-mint)' : tone === 'neg' ? 'var(--ap-rose)' : tone === 'ai' ? 'var(--ap-violet)' : 'var(--ap-fg-1)',
      lineHeight: 1.1
    }
  }, value), sub && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11.5,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, sub));
};
const wfmt = (n, d = 2) => n.toLocaleString('en-US', {
  minimumFractionDigits: d,
  maximumFractionDigits: d
});
const wfmtPct = n => (n >= 0 ? '+' : '') + n.toFixed(2) + '%';
const wfmtSigned = n => (n >= 0 ? '+' : '−') + '$' + Math.abs(n).toLocaleString('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});

// icons (inline SVG, Lucide-ish)
const Icon = ({
  name,
  size = 16,
  color = 'currentColor',
  strokeWidth = 1.8
}) => {
  const s = size,
    sw = strokeWidth;
  const paths = {
    dashboard: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("rect", {
      x: "3",
      y: "3",
      width: "7",
      height: "9",
      rx: "1"
    }), /*#__PURE__*/React.createElement("rect", {
      x: "14",
      y: "3",
      width: "7",
      height: "5",
      rx: "1"
    }), /*#__PURE__*/React.createElement("rect", {
      x: "14",
      y: "12",
      width: "7",
      height: "9",
      rx: "1"
    }), /*#__PURE__*/React.createElement("rect", {
      x: "3",
      y: "16",
      width: "7",
      height: "5",
      rx: "1"
    })),
    brain: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M12 5a3 3 0 0 0-5.99.14A3 3 0 0 0 4 10.5v0a3 3 0 0 0 .14 4A3 3 0 0 0 6 19.99 3 3 0 0 0 12 19V5Z"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M12 5a3 3 0 0 1 5.99.14A3 3 0 0 1 20 10.5v0a3 3 0 0 1-.14 4A3 3 0 0 1 18 19.99 3 3 0 0 1 12 19V5Z"
    })),
    layers: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "m12 2 8 5-8 5-8-5 8-5Z"
    }), /*#__PURE__*/React.createElement("path", {
      d: "m4 12 8 5 8-5"
    }), /*#__PURE__*/React.createElement("path", {
      d: "m4 17 8 5 8-5"
    })),
    chart: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M3 3v18h18"
    }), /*#__PURE__*/React.createElement("path", {
      d: "m7 16 4-7 4 3 5-9"
    })),
    shield: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M12 2 4 6v6c0 5 3.5 9 8 10 4.5-1 8-5 8-10V6l-8-4Z"
    })),
    list: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("line", {
      x1: "8",
      x2: "21",
      y1: "6",
      y2: "6"
    }), /*#__PURE__*/React.createElement("line", {
      x1: "8",
      x2: "21",
      y1: "12",
      y2: "12"
    }), /*#__PURE__*/React.createElement("line", {
      x1: "8",
      x2: "21",
      y1: "18",
      y2: "18"
    }), /*#__PURE__*/React.createElement("circle", {
      cx: "4",
      cy: "6",
      r: "1"
    }), /*#__PURE__*/React.createElement("circle", {
      cx: "4",
      cy: "12",
      r: "1"
    }), /*#__PURE__*/React.createElement("circle", {
      cx: "4",
      cy: "18",
      r: "1"
    })),
    settings: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"
    })),
    search: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("circle", {
      cx: "11",
      cy: "11",
      r: "8"
    }), /*#__PURE__*/React.createElement("path", {
      d: "m21 21-4.3-4.3"
    })),
    bell: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M10.3 21a1.94 1.94 0 0 0 3.4 0"
    })),
    play: /*#__PURE__*/React.createElement("polygon", {
      points: "6 3 20 12 6 21 6 3"
    }),
    pause: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("rect", {
      x: "6",
      y: "4",
      width: "4",
      height: "16"
    }), /*#__PURE__*/React.createElement("rect", {
      x: "14",
      y: "4",
      width: "4",
      height: "16"
    })),
    check: /*#__PURE__*/React.createElement("path", {
      d: "M20 6 9 17l-5-5"
    }),
    x: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M18 6 6 18"
    }), /*#__PURE__*/React.createElement("path", {
      d: "m6 6 12 12"
    })),
    arrow_up: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "m5 12 7-7 7 7"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M12 19V5"
    })),
    arrow_down: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M12 5v14"
    }), /*#__PURE__*/React.createElement("path", {
      d: "m19 12-7 7-7-7"
    })),
    alert: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M12 9v4"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M12 17h.01"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"
    })),
    bolt: /*#__PURE__*/React.createElement("path", {
      d: "M13 2 3 14h9l-1 8 10-12h-9l1-8Z"
    }),
    clock: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("circle", {
      cx: "12",
      cy: "12",
      r: "10"
    }), /*#__PURE__*/React.createElement("polyline", {
      points: "12 6 12 12 16 14"
    })),
    book: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"
    })),
    chevron_right: /*#__PURE__*/React.createElement("path", {
      d: "m9 18 6-6-6-6"
    }),
    chevron_down: /*#__PURE__*/React.createElement("path", {
      d: "m6 9 6 6 6-6"
    }),
    circle: /*#__PURE__*/React.createElement("circle", {
      cx: "12",
      cy: "12",
      r: "10"
    }),
    user: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"
    }), /*#__PURE__*/React.createElement("circle", {
      cx: "12",
      cy: "7",
      r: "4"
    })),
    users: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"
    }), /*#__PURE__*/React.createElement("circle", {
      cx: "9",
      cy: "7",
      r: "4"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M22 21v-2a4 4 0 0 0-3-3.87"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M16 3.13a4 4 0 0 1 0 7.75"
    })),
    lock: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("rect", {
      x: "3",
      y: "11",
      width: "18",
      height: "11",
      rx: "2"
    }), /*#__PURE__*/React.createElement("path", {
      d: "M7 11V7a5 5 0 0 1 10 0v4"
    })),
    key: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("circle", {
      cx: "7.5",
      cy: "15.5",
      r: "5.5"
    }), /*#__PURE__*/React.createElement("path", {
      d: "m21 2-9.6 9.6"
    }), /*#__PURE__*/React.createElement("path", {
      d: "m15.5 7.5 3 3L22 7l-3-3"
    })),
    mail: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("rect", {
      x: "2",
      y: "4",
      width: "20",
      height: "16",
      rx: "2"
    }), /*#__PURE__*/React.createElement("path", {
      d: "m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"
    })),
    logout: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"
    }), /*#__PURE__*/React.createElement("polyline", {
      points: "16 17 21 12 16 7"
    }), /*#__PURE__*/React.createElement("line", {
      x1: "21",
      x2: "9",
      y1: "12",
      y2: "12"
    })),
    eye: /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("path", {
      d: "M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"
    }), /*#__PURE__*/React.createElement("circle", {
      cx: "12",
      cy: "12",
      r: "3"
    }))
  };
  return /*#__PURE__*/React.createElement("svg", {
    width: s,
    height: s,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: color,
    strokeWidth: sw,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    style: {
      flexShrink: 0
    }
  }, paths[name]);
};

// =========== Sidebar ===========
const Sidebar = ({
  active,
  onNav,
  onLogout
}) => {
  const nav = [{
    id: 'dashboard',
    label: '主控制台',
    icon: 'dashboard'
  }, {
    id: 'market',
    label: '行情',
    icon: 'chart'
  }, {
    id: 'ai',
    label: 'AI 决策',
    icon: 'brain',
    badge: 5
  }, {
    id: 'positions',
    label: '持仓与订单',
    icon: 'layers'
  }, {
    id: 'backtest',
    label: '回测与绩效',
    icon: 'chart'
  }, {
    id: 'risk',
    label: '策略与风控',
    icon: 'shield'
  }, {
    id: 'lab',
    label: '策略实验室',
    icon: 'book',
    badge: 2
  }, {
    id: 'audit',
    label: '审计日志',
    icon: 'list'
  }, {
    id: 'admin',
    label: '后台管理',
    icon: 'users'
  }, {
    id: 'settings',
    label: '设置',
    icon: 'settings'
  }];
  return /*#__PURE__*/React.createElement("aside", {
    style: {
      width: 240,
      flexShrink: 0,
      background: 'var(--ap-bg-1)',
      borderRight: '1px solid var(--ap-line)',
      display: 'flex',
      flexDirection: 'column',
      height: '100%'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '20px 20px 24px',
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      borderBottom: '1px solid var(--ap-line-soft)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      borderRadius: 8,
      background: 'linear-gradient(135deg,var(--ap-mint) 0%,var(--ap-violet) 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'var(--ap-bg-0)',
      fontWeight: 800,
      fontSize: 15
    }
  }, "\u03B1"), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 15,
      fontWeight: 700,
      letterSpacing: '-.01em'
    }
  }, "Alpha", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-mint)'
    }
  }, "Pilot")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)',
      letterSpacing: '.05em'
    }
  }, "v0.1 \xB7 mainnet"))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '16px 20px',
      borderBottom: '1px solid var(--ap-line-soft)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.08em',
      textTransform: 'uppercase',
      fontWeight: 500,
      marginBottom: 6
    }
  }, "\u8D26\u6237\u6743\u76CA"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 20,
      fontWeight: 700,
      letterSpacing: '-.02em',
      lineHeight: 1.1
    }
  }, "$", wfmt(W_MOCK.equity)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 11,
      color: 'var(--ap-mint)',
      marginTop: 3
    }
  }, "+", wfmtPct(W_MOCK.equityChangePct).slice(1), " \u4ECA\u65E5")), /*#__PURE__*/React.createElement("nav", {
    style: {
      flex: 1,
      padding: '12px 12px',
      display: 'flex',
      flexDirection: 'column',
      gap: 1,
      overflow: 'auto'
    }
  }, nav.map(n => {
    const isActive = active === n.id;
    return /*#__PURE__*/React.createElement("div", {
      key: n.id,
      onClick: () => onNav(n.id),
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '9px 10px',
        borderRadius: 8,
        cursor: 'pointer',
        color: isActive ? 'var(--ap-fg-1)' : 'var(--ap-fg-3)',
        background: isActive ? 'var(--ap-bg-3)' : 'transparent',
        fontSize: 13,
        fontWeight: 500,
        position: 'relative',
        transition: '.12s'
      }
    }, isActive && /*#__PURE__*/React.createElement("div", {
      style: {
        position: 'absolute',
        left: -12,
        top: 8,
        bottom: 8,
        width: 3,
        borderRadius: 2,
        background: 'var(--ap-mint)'
      }
    }), /*#__PURE__*/React.createElement(Icon, {
      name: n.icon,
      size: 16,
      color: isActive ? 'var(--ap-mint)' : 'currentColor'
    }), /*#__PURE__*/React.createElement("span", {
      style: {
        flex: 1
      }
    }, n.label), n.badge && /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10,
        padding: '1px 6px',
        background: 'var(--ap-violet-soft)',
        color: 'var(--ap-violet)',
        borderRadius: 999,
        fontFamily: 'var(--ap-font-mono)',
        fontWeight: 600
      }
    }, n.badge));
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 14px',
      borderTop: '1px solid var(--ap-line-soft)',
      display: 'flex',
      flexDirection: 'column',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(WDot, {
    c: "var(--ap-mint)",
    glow: true
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-2)',
      fontWeight: 500
    }
  }, "\u5F15\u64CE\u8FD0\u884C\u4E2D"), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      fontSize: 10,
      color: 'var(--ap-fg-4)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "48ms")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 9,
      padding: '8px 8px',
      background: 'var(--ap-bg-2)',
      borderRadius: 9,
      border: '1px solid var(--ap-line-soft)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 28,
      height: 28,
      borderRadius: '50%',
      background: 'oklch(0.45 0.09 148)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#fff',
      fontSize: 11,
      fontWeight: 700,
      flexShrink: 0
    }
  }, "DL"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    }
  }, "Daner Li"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9.5,
      color: 'var(--ap-violet)',
      fontFamily: 'var(--ap-font-mono)',
      fontWeight: 600
    }
  }, "OWNER")), /*#__PURE__*/React.createElement("button", {
    onClick: onLogout,
    title: "\u9000\u51FA\u767B\u5F55",
    style: {
      width: 26,
      height: 26,
      borderRadius: 7,
      background: 'transparent',
      border: '1px solid var(--ap-line-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      color: 'var(--ap-fg-4)',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "logout",
    size: 12
  })))));
};

// =========== Topbar ===========
const Topbar = ({
  pageTitle,
  pageSub,
  onCommand,
  onChat,
  riskState,
  regime,
  dayLossPct,
  positionsPct
}) => {
  riskState = riskState || W_MOCK.riskState;
  regime = regime || W_MOCK.regime;
  dayLossPct = dayLossPct ?? W_MOCK.dayLossPct;
  positionsPct = positionsPct ?? W_MOCK.positionsPct;
  const riskCfg = {
    OK: {
      c: 'var(--ap-mint)',
      label: '风控正常'
    },
    WARN: {
      c: 'var(--ap-amber)',
      label: '接近阈值'
    },
    HALTED: {
      c: 'var(--ap-rose)',
      label: '已熔断'
    }
  }[riskState];
  return /*#__PURE__*/React.createElement("header", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 16,
      padding: '14px 24px',
      borderBottom: '1px solid var(--ap-line-soft)',
      background: 'var(--ap-bg-1)',
      height: 60,
      boxSizing: 'border-box'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.08em',
      textTransform: 'uppercase',
      fontWeight: 500,
      marginBottom: 1
    }
  }, pageSub), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 16,
      fontWeight: 600,
      letterSpacing: '-.01em'
    }
  }, pageTitle)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '6px 12px',
      background: 'var(--ap-bg-2)',
      borderRadius: 999,
      border: '1px solid var(--ap-line-soft)'
    }
  }, /*#__PURE__*/React.createElement(WDot, {
    c: riskCfg.c,
    glow: true
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: riskCfg.c
    }
  }, riskCfg.label), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-3)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "\u4ED3\u4F4D ", positionsPct, "% \xB7 \u65E5\u635F ", wfmtPct(dayLossPct), " \xB7 ", regime)), /*#__PURE__*/React.createElement("div", {
    onClick: onCommand,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '6px 10px 6px 12px',
      background: 'var(--ap-bg-2)',
      borderRadius: 8,
      border: '1px solid var(--ap-line-soft)',
      cursor: 'pointer',
      width: 260
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "search",
    size: 14,
    color: "var(--ap-fg-3)"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--ap-fg-4)',
      flex: 1
    }
  }, "\u641C\u7D22\u4EA4\u6613\u5BF9\u3001\u51B3\u7B56\u3001\u7B56\u7565\u2026"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 10,
      color: 'var(--ap-fg-4)',
      background: 'var(--ap-bg-3)',
      padding: '2px 6px',
      borderRadius: 4,
      border: '1px solid var(--ap-line)'
    }
  }, "\u2318K")), /*#__PURE__*/React.createElement("button", {
    onClick: onChat,
    title: "Pilot AI",
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 7,
      padding: '7px 13px',
      borderRadius: 8,
      background: 'var(--ap-violet-soft)',
      border: '1px solid rgba(124,92,255,.35)',
      cursor: 'pointer',
      color: 'var(--ap-violet)'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "brain",
    size: 14
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 600
    }
  }, "Pilot AI")), /*#__PURE__*/React.createElement("button", {
    style: {
      width: 34,
      height: 34,
      borderRadius: 8,
      background: 'var(--ap-bg-2)',
      border: '1px solid var(--ap-line-soft)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      color: 'var(--ap-fg-2)',
      position: 'relative'
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "bell",
    size: 15
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'absolute',
      top: 6,
      right: 6,
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: 'var(--ap-rose)',
      boxShadow: '0 0 4px var(--ap-rose)'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '6px 12px',
      background: 'var(--ap-mint-soft)',
      borderRadius: 8,
      border: '1px solid rgba(0,211,149,.25)'
    }
  }, /*#__PURE__*/React.createElement(WDot, {
    c: "var(--ap-mint)",
    glow: true
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: 'var(--ap-mint)',
      fontFamily: 'var(--ap-font-mono)'
    }
  }, "AUTO")));
};

// =========== PageShell (sidebar + topbar) ===========
const PageShell = ({
  active,
  onNav,
  title,
  sub,
  children,
  riskState,
  regime,
  dayLossPct,
  positionsPct,
  onCommand,
  onChat,
  onLogout
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    width: '100%',
    height: '100%',
    background: 'var(--ap-bg-0)'
  }
}, /*#__PURE__*/React.createElement(Sidebar, {
  active: active,
  onNav: onNav,
  onLogout: onLogout
}), /*#__PURE__*/React.createElement("div", {
  style: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    minWidth: 0
  }
}, /*#__PURE__*/React.createElement(Topbar, {
  pageTitle: title,
  pageSub: sub,
  onCommand: onCommand,
  onChat: onChat,
  riskState: riskState,
  regime: regime,
  dayLossPct: dayLossPct,
  positionsPct: positionsPct
}), /*#__PURE__*/React.createElement("div", {
  style: {
    flex: 1,
    overflow: 'auto',
    padding: '24px'
  }
}, children)));

// =========== Sparkline + mini price chart ===========
const WSpark = ({
  data,
  w = 400,
  h = 110,
  color = 'var(--ap-mint)',
  fill = true,
  gridId = 'wsg'
}) => {
  const min = Math.min(...data),
    max = Math.max(...data),
    r = max - min || 1;
  const pts = data.map((v, i) => [i / (data.length - 1) * w, h - (v - min) / r * (h - 8) - 4]);
  const path = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
  const area = path + ` L ${w} ${h} L 0 ${h} Z`;
  return /*#__PURE__*/React.createElement("svg", {
    width: w,
    height: h,
    style: {
      display: 'block'
    },
    viewBox: `0 0 ${w} ${h}`,
    preserveAspectRatio: "none"
  }, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("linearGradient", {
    id: gridId,
    x1: "0",
    x2: "0",
    y1: "0",
    y2: "1"
  }, /*#__PURE__*/React.createElement("stop", {
    offset: "0",
    stopColor: color,
    stopOpacity: ".35"
  }), /*#__PURE__*/React.createElement("stop", {
    offset: "1",
    stopColor: color,
    stopOpacity: "0"
  }))), fill && /*#__PURE__*/React.createElement("path", {
    d: area,
    fill: `url(#${gridId})`
  }), /*#__PURE__*/React.createElement("path", {
    d: path,
    stroke: color,
    strokeWidth: "1.8",
    fill: "none",
    strokeLinejoin: "round"
  }));
};
Object.assign(window, {
  W_MOCK,
  WPill,
  WDot,
  WCard,
  WStat,
  Icon,
  Sidebar,
  Topbar,
  PageShell,
  WSpark,
  wfmt,
  wfmtPct,
  wfmtSigned
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/web_app/components/shell.jsx", error: String((e && e.message) || e) }); }

// ui_kits/web_app/components/trade_panel.jsx
try { (() => {
// Order ticket — manual trading panel for the Market page
// Includes guard pre-check preview: manual orders also pass through hard risk checks.

const OrderTicket = ({
  sym
}) => {
  const m = MARKET[sym];
  const [side, setSide] = React.useState('buy');
  const [type, setType] = React.useState('limit');
  const [price, setPrice] = React.useState(String(Math.round(m.price)));
  const [qty, setQty] = React.useState('0.01');
  const [pct, setPct] = React.useState(25);
  const [sl, setSl] = React.useState('');
  const [tp, setTp] = React.useState('');
  const [reduceOnly, setReduceOnly] = React.useState(false);
  const [submitted, setSubmitted] = React.useState(false);
  React.useEffect(() => {
    setPrice(String(Math.round(m.price)));
    setSubmitted(false);
  }, [sym]);
  const notional = (parseFloat(qty) || 0) * (type === 'market' ? m.price : parseFloat(price) || 0);
  const equity = W_MOCK.equity;
  const posPct = notional / equity * 100;
  const rr = (() => {
    const p = type === 'market' ? m.price : parseFloat(price),
      s = parseFloat(sl),
      t = parseFloat(tp);
    if (!p || !s || !t) return null;
    const risk = Math.abs(p - s),
      reward = Math.abs(t - p);
    return risk > 0 ? reward / risk : null;
  })();

  // guard pre-checks (manual orders still guarded)
  const checks = [{
    k: '仓位上限',
    ok: posPct <= 15,
    note: posPct.toFixed(1) + '% / 15%'
  }, {
    k: '止损设置',
    ok: reduceOnly || !!parseFloat(sl),
    note: parseFloat(sl) ? '已设' : '必填'
  }, {
    k: 'R:R ≥ 1.5',
    ok: reduceOnly || rr !== null && rr >= 1.5,
    note: rr ? '1:' + rr.toFixed(1) : '—'
  }, {
    k: '熔断状态',
    ok: W_MOCK.riskState !== 'HALTED' || reduceOnly,
    note: W_MOCK.riskState === 'HALTED' ? reduceOnly ? '仅减仓' : '已熔断' : '正常'
  }];
  const allPass = checks.every(c => c.ok);
  const buyC = side === 'buy';
  const inputStyle = {
    width: '100%',
    boxSizing: 'border-box',
    background: 'var(--ap-bg-3)',
    border: '1px solid var(--ap-line)',
    borderRadius: 8,
    padding: '8px 10px',
    color: 'var(--ap-fg-1)',
    fontSize: 12,
    fontFamily: 'var(--ap-font-mono)',
    outline: 'none'
  };
  const lbl = {
    fontSize: 10,
    color: 'var(--ap-fg-3)',
    letterSpacing: '.05em',
    marginBottom: 4,
    display: 'block'
  };
  return /*#__PURE__*/React.createElement(WCard, {
    title: "\u624B\u52A8\u4E0B\u5355",
    right: /*#__PURE__*/React.createElement(WPill, {
      tone: "amber"
    }, "\u4EBA\u5DE5\u5E72\u9884"),
    style: {
      height: 'fit-content'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 6,
      marginBottom: 10
    }
  }, [['buy', '买入 / 做多', 'var(--ap-mint)'], ['sell', '卖出 / 做空', 'var(--ap-rose)']].map(([v, l, c]) => /*#__PURE__*/React.createElement("div", {
    key: v,
    onClick: () => setSide(v),
    style: {
      padding: '9px 0',
      textAlign: 'center',
      borderRadius: 8,
      fontSize: 12,
      fontWeight: 700,
      cursor: 'pointer',
      background: side === v ? c : 'var(--ap-bg-3)',
      color: side === v ? 'var(--ap-bg-0)' : 'var(--ap-fg-3)',
      border: '1px solid ' + (side === v ? c : 'var(--ap-line)')
    }
  }, l))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-flex',
      background: 'var(--ap-bg-3)',
      borderRadius: 8,
      padding: 2,
      border: '1px solid var(--ap-line)',
      marginBottom: 10
    }
  }, [['limit', '限价'], ['market', '市价'], ['stop', '止损单']].map(([v, l]) => /*#__PURE__*/React.createElement("div", {
    key: v,
    onClick: () => setType(v),
    style: {
      fontSize: 11,
      padding: '5px 12px',
      borderRadius: 6,
      cursor: 'pointer',
      fontFamily: 'var(--ap-font-mono)',
      background: type === v ? 'var(--ap-bg-4)' : 'transparent',
      color: type === v ? 'var(--ap-fg-1)' : 'var(--ap-fg-3)'
    }
  }, l))), type !== 'market' && /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: lbl
  }, "\u4EF7\u683C (USDT)"), /*#__PURE__*/React.createElement("input", {
    value: price,
    onChange: e => setPrice(e.target.value),
    style: inputStyle
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: lbl
  }, "\u6570\u91CF (", sym.replace('USDT', ''), ")"), /*#__PURE__*/React.createElement("input", {
    value: qty,
    onChange: e => setQty(e.target.value),
    style: inputStyle
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 4,
      marginTop: 6
    }
  }, [10, 25, 50, 75, 100].map(p => /*#__PURE__*/React.createElement("div", {
    key: p,
    onClick: () => {
      setPct(p);
      setQty((equity * p / 100 / m.price * 0.1).toFixed(3));
    },
    style: {
      flex: 1,
      textAlign: 'center',
      padding: '4px 0',
      fontSize: 10,
      borderRadius: 5,
      cursor: 'pointer',
      fontFamily: 'var(--ap-font-mono)',
      background: pct === p ? 'var(--ap-bg-4)' : 'var(--ap-bg-3)',
      color: pct === p ? 'var(--ap-fg-1)' : 'var(--ap-fg-4)',
      border: '1px solid var(--ap-line-soft)'
    }
  }, p, "%")))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 8,
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("span", {
    style: lbl
  }, "\u6B62\u635F SL"), /*#__PURE__*/React.createElement("input", {
    value: sl,
    onChange: e => setSl(e.target.value),
    placeholder: "\u5FC5\u586B",
    style: {
      ...inputStyle,
      borderColor: sl ? 'var(--ap-line)' : 'rgba(255,77,109,.4)'
    }
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("span", {
    style: lbl
  }, "\u6B62\u76C8 TP"), /*#__PURE__*/React.createElement("input", {
    value: tp,
    onChange: e => setTp(e.target.value),
    placeholder: "\u53EF\u9009",
    style: inputStyle
  }))), /*#__PURE__*/React.createElement("div", {
    onClick: () => setReduceOnly(!reduceOnly),
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 12,
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 14,
      height: 14,
      borderRadius: 4,
      border: '1px solid ' + (reduceOnly ? 'var(--ap-mint)' : 'var(--ap-line)'),
      background: reduceOnly ? 'var(--ap-mint)' : 'transparent',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, reduceOnly && /*#__PURE__*/React.createElement(Icon, {
    name: "check",
    size: 10,
    color: "var(--ap-bg-0)",
    strokeWidth: 3
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--ap-fg-2)'
    }
  }, "\u53EA\u51CF\u4ED3 Reduce-Only")), /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--ap-bg-3)',
      borderRadius: 8,
      padding: '8px 10px',
      marginBottom: 10,
      fontFamily: 'var(--ap-font-mono)',
      fontSize: 10.5,
      display: 'flex',
      flexDirection: 'column',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-4)'
    }
  }, "\u540D\u4E49\u4EF7\u503C"), /*#__PURE__*/React.createElement("span", null, "$", wfmt(notional))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-4)'
    }
  }, "\u5360\u7528\u4ED3\u4F4D"), /*#__PURE__*/React.createElement("span", {
    style: {
      color: posPct > 15 ? 'var(--ap-rose)' : 'var(--ap-fg-1)'
    }
  }, posPct.toFixed(2), "%")), rr !== null && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-4)'
    }
  }, "\u76C8\u4E8F\u6BD4"), /*#__PURE__*/React.createElement("span", {
    style: {
      color: rr >= 1.5 ? 'var(--ap-mint)' : 'var(--ap-rose)'
    }
  }, "1:", rr.toFixed(2)))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--ap-fg-3)',
      letterSpacing: '.06em',
      fontWeight: 600,
      marginBottom: 6,
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "shield",
    size: 11,
    color: "var(--ap-fg-3)"
  }), " \u5B88\u536B\u9884\u68C0 \xB7 \u4EBA\u5DE5\u5355\u540C\u6837\u53D7\u786C\u98CE\u63A7\u7EA6\u675F"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 3
    }
  }, checks.map((c, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      fontSize: 10.5,
      fontFamily: 'var(--ap-font-mono)'
    }
  }, /*#__PURE__*/React.createElement(WDot, {
    c: c.ok ? 'var(--ap-mint)' : 'var(--ap-rose)'
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--ap-fg-3)',
      flex: 1
    }
  }, c.k), /*#__PURE__*/React.createElement("span", {
    style: {
      color: c.ok ? 'var(--ap-fg-2)' : 'var(--ap-rose)'
    }
  }, c.note))))), /*#__PURE__*/React.createElement("button", {
    onClick: () => allPass && setSubmitted(true),
    disabled: !allPass,
    style: {
      width: '100%',
      padding: '11px 0',
      borderRadius: 9,
      border: 'none',
      fontSize: 13,
      fontWeight: 700,
      fontFamily: 'inherit',
      cursor: allPass ? 'pointer' : 'not-allowed',
      background: submitted ? 'var(--ap-bg-4)' : allPass ? buyC ? 'var(--ap-mint)' : 'var(--ap-rose)' : 'var(--ap-bg-4)',
      color: submitted ? 'var(--ap-mint)' : allPass ? 'var(--ap-bg-0)' : 'var(--ap-fg-4)'
    }
  }, submitted ? '✓ 已提交（模拟）' : allPass ? buyC ? '买入 ' + sym.replace('USDT', '') : '卖出 ' + sym.replace('USDT', '') : '守卫未通过'), W_MOCK.riskState === 'HALTED' && !reduceOnly && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 8,
      fontSize: 10.5,
      color: 'var(--ap-rose)',
      fontFamily: 'var(--ap-font-mono)',
      textAlign: 'center'
    }
  }, "\u7194\u65AD\u4E2D \xB7 \u4EC5\u5141\u8BB8 Reduce-Only"));
};
Object.assign(window, {
  OrderTicket
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/web_app/components/trade_panel.jsx", error: String((e && e.message) || e) }); }

})();
