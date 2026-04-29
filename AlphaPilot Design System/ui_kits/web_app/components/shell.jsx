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
  positions: [
    { sym:'BTCUSDT', side:'LONG', qty:0.048, entry:67420.50, mark:68863.92, pnl:69.29, pnlPct:2.14, margin:2.5, sl:64210, tp:68900, age:'2h 13m', strat:'趋势跟随' },
    { sym:'ETHUSDT', side:'LONG', qty:0.82, entry:3240.00, mark:3219.92, pnl:-16.47, pnlPct:-0.62, margin:1.8, sl:3120, tp:3380, age:'45m', strat:'突破确认' },
  ],
  orders: [
    { t:'14:23:09', sym:'BTCUSDT', side:'BUY', type:'MARKET', qty:0.048, price:67420.50, status:'FILLED' },
    { t:'14:23:09', sym:'BTCUSDT', side:'SELL', type:'STOP', qty:0.048, price:64210, status:'WORKING' },
    { t:'14:23:09', sym:'BTCUSDT', side:'SELL', type:'TAKE_PROFIT', qty:0.048, price:68900, status:'WORKING' },
    { t:'13:45:12', sym:'ETHUSDT', side:'BUY', type:'LIMIT', qty:0.82, price:3240, status:'FILLED' },
    { t:'10:15:30', sym:'BTCUSDT', side:'SELL', type:'MARKET', qty:0.062, price:68903.20, status:'FILLED' },
  ],
  decisions: [
    { id:'d_7f3a9b', t:'14:23:08', sym:'BTCUSDT', tf:'15m', action:'OPEN_LONG', conf:0.78, strat:'趋势跟随', sl:64210, tp:68900, size:'2.5%', guard:'PASS', entry:67420.50,
      reason:'EMA20>EMA50>EMA200 金叉排列，1h 成交量较均值放大 1.4x，回踩 EMA20 未破，确认突破有效。',
      features: [
        {k:'regime', v:'trending_up', ok:true},
        {k:'EMA_align', v:'20>50>200', ok:true},
        {k:'vol_mult', v:'1.4x', ok:true},
        {k:'ATR_14', v:'1.82%', ok:true},
        {k:'RSI_14', v:'58', ok:true},
        {k:'BB_width', v:'0.043', ok:true},
      ],
      guards: [
        {k:'regime_match', ok:true, note:'trending_up ∈ strategy.allowed'},
        {k:'max_per_trade_risk', ok:true, note:'0.8% < 1.0%'},
        {k:'max_position_size', ok:true, note:'2.5% < 15%'},
        {k:'daily_loss_limit', ok:true, note:'-0.48% > -2.0%'},
        {k:'RR_ratio', ok:true, note:'2.3 > 1.5'},
        {k:'correlation_cap', ok:true, note:'BTC-ETH corr 0.68 < 0.85'},
        {k:'spread_check', ok:true, note:'1.2bps < 5bps'},
        {k:'cooldown', ok:true, note:'last trade 3h ago'},
      ],
    },
    { id:'d_7f3a9a', t:'13:45:00', sym:'ETHUSDT', tf:'15m', action:'HOLD', conf:0.42, strat:'观望模式', guard:'DEGRADE', reason:'波动率进入高位，regime 由 trending_up 切换为 chaotic，降级为观望。' },
    { id:'d_7f3a99', t:'12:30:00', sym:'BTCUSDT', tf:'15m', action:'OPEN_LONG', conf:0.71, strat:'突破确认', guard:'REJECT', reason:'触发风险收益比 <1.5 检查，守卫拒绝，回退 HOLD。' },
    { id:'d_7f3a98', t:'10:15:00', sym:'BTCUSDT', tf:'15m', action:'CLOSE_LONG', conf:0.85, strat:'止盈执行', guard:'PASS', reason:'达到 TP 价位，执行平仓，本笔 +1.82%。', entry:66100 },
    { id:'d_7f3a97', t:'09:02:00', sym:'ETHUSDT', tf:'15m', action:'OPEN_LONG', conf:0.66, strat:'突破确认', guard:'PASS', reason:'突破前高 3240，成交量放大，进场。' },
  ],
  events: [
    {t:'14:23:09', kind:'fill', msg:'BTCUSDT 市价成交 0.048 @ 67,420.50', color:'mint'},
    {t:'14:23:09', kind:'order', msg:'止损挂单 64,210 · 止盈 68,900', color:'fg'},
    {t:'14:23:08', kind:'guard', msg:'守卫通过 PASS · 检查 8/8', color:'mint'},
    {t:'14:23:08', kind:'ai', msg:'AI OPEN_LONG BTCUSDT · 置信度 0.78', color:'violet'},
    {t:'13:45:05', kind:'guard', msg:'守卫降级 DEGRADE · regime 异常', color:'amber'},
    {t:'13:45:00', kind:'ai', msg:'AI HOLD ETHUSDT · 置信度 0.42', color:'violet'},
    {t:'12:30:12', kind:'guard', msg:'守卫拒绝 REJECT · RR<1.5 · 回退 HOLD', color:'rose'},
    {t:'12:30:08', kind:'ai', msg:'AI OPEN_LONG BTCUSDT · 置信度 0.71', color:'violet'},
    {t:'10:15:30', kind:'fill', msg:'BTCUSDT 平仓 @ 68,903 · +1.82%', color:'mint'},
    {t:'10:15:29', kind:'ai', msg:'AI CLOSE_LONG BTCUSDT · 置信度 0.85', color:'violet'},
    {t:'09:02:14', kind:'fill', msg:'ETHUSDT 市价成交 0.82 @ 3,240.00', color:'mint'},
    {t:'09:02:10', kind:'ai', msg:'AI OPEN_LONG ETHUSDT · 置信度 0.66', color:'violet'},
  ],
};

// =========== atoms (web-scale) ===========
const WPill = ({ children, tone='default' }) => {
  const tones = {
    mint:{bg:'var(--ap-mint-soft)', c:'var(--ap-mint)'},
    rose:{bg:'var(--ap-rose-soft)', c:'var(--ap-rose)'},
    amber:{bg:'var(--ap-amber-soft)', c:'var(--ap-amber)'},
    violet:{bg:'var(--ap-violet-soft)', c:'var(--ap-violet)'},
    cyan:{bg:'var(--ap-cyan-soft)', c:'var(--ap-cyan)'},
    default:{bg:'var(--ap-bg-3)', c:'var(--ap-fg-2)'},
  };
  const s = tones[tone]||tones.default;
  return <span style={{display:'inline-flex',alignItems:'center',gap:4,fontSize:10.5,padding:'2px 8px',borderRadius:999,background:s.bg,color:s.c,fontWeight:600,fontFamily:'var(--ap-font-mono)',letterSpacing:'.04em'}}>{children}</span>;
};

const WDot = ({c, glow, size=6}) => <span style={{width:size,height:size,borderRadius:'50%',background:c,boxShadow:glow?`0 0 6px ${c}`:'none',display:'inline-block',flexShrink:0}}/>;

const WCard = ({children, style, title, right, dense, glow}) => (
  <div style={{
    background:'var(--ap-bg-2)',borderRadius:'var(--ap-r-md)',
    border:'1px solid var(--ap-line-soft)',overflow:'hidden',
    ...(glow?{boxShadow:'0 0 0 1px var(--ap-violet), 0 0 40px rgba(124,92,255,.12)'}:{}),
    ...style
  }}>
    {title && (
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:dense?'10px 14px':'14px 18px',borderBottom:'1px solid var(--ap-line-soft)'}}>
        <div style={{fontSize:11,color:'var(--ap-fg-3)',letterSpacing:'.08em',textTransform:'uppercase',fontWeight:600}}>{title}</div>
        {right}
      </div>
    )}
    <div style={{padding:dense?'12px 14px':'16px 18px'}}>{children}</div>
  </div>
);

const WStat = ({label, value, sub, tone, size='md'}) => {
  const fs = size==='lg' ? 28 : size==='sm' ? 16 : 22;
  return (
    <div style={{display:'flex',flexDirection:'column',gap:4}}>
      <div style={{fontSize:10.5,color:'var(--ap-fg-3)',letterSpacing:'.08em',textTransform:'uppercase',fontWeight:500}}>{label}</div>
      <div style={{fontFamily:'var(--ap-font-mono)',fontSize:fs,fontWeight:700,letterSpacing:'-.02em',color: tone==='pos'?'var(--ap-mint)':tone==='neg'?'var(--ap-rose)':tone==='ai'?'var(--ap-violet)':'var(--ap-fg-1)',lineHeight:1.1}}>{value}</div>
      {sub && <div style={{fontSize:11.5,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>{sub}</div>}
    </div>
  );
};

const wfmt = (n, d=2) => n.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const wfmtPct = n => (n>=0?'+':'')+n.toFixed(2)+'%';
const wfmtSigned = n => (n>=0?'+':'−')+'$'+Math.abs(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});

// icons (inline SVG, Lucide-ish)
const Icon = ({name, size=16, color='currentColor', strokeWidth=1.8}) => {
  const s = size, sw = strokeWidth;
  const paths = {
    dashboard: <><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></>,
    brain: <><path d="M12 5a3 3 0 0 0-5.99.14A3 3 0 0 0 4 10.5v0a3 3 0 0 0 .14 4A3 3 0 0 0 6 19.99 3 3 0 0 0 12 19V5Z"/><path d="M12 5a3 3 0 0 1 5.99.14A3 3 0 0 1 20 10.5v0a3 3 0 0 1-.14 4A3 3 0 0 1 18 19.99 3 3 0 0 1 12 19V5Z"/></>,
    layers: <><path d="m12 2 8 5-8 5-8-5 8-5Z"/><path d="m4 12 8 5 8-5"/><path d="m4 17 8 5 8-5"/></>,
    chart: <><path d="M3 3v18h18"/><path d="m7 16 4-7 4 3 5-9"/></>,
    shield: <><path d="M12 2 4 6v6c0 5 3.5 9 8 10 4.5-1 8-5 8-10V6l-8-4Z"/></>,
    list: <><line x1="8" x2="21" y1="6" y2="6"/><line x1="8" x2="21" y1="12" y2="12"/><line x1="8" x2="21" y1="18" y2="18"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/></>,
    settings: <><path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"/></>,
    search: <><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></>,
    bell: <><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></>,
    play: <polygon points="6 3 20 12 6 21 6 3"/>,
    pause: <><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></>,
    check: <path d="M20 6 9 17l-5-5"/>,
    x: <><path d="M18 6 6 18"/><path d="m6 6 12 12"/></>,
    arrow_up: <><path d="m5 12 7-7 7 7"/><path d="M12 19V5"/></>,
    arrow_down: <><path d="M12 5v14"/><path d="m19 12-7 7-7-7"/></>,
    alert: <><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/></>,
    bolt: <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z"/>,
    clock: <><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></>,
    book: <><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></>,
    chevron_right: <path d="m9 18 6-6-6-6"/>,
    chevron_down: <path d="m6 9 6 6 6-6"/>,
    circle: <circle cx="12" cy="12" r="10"/>,
  };
  return <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" style={{flexShrink:0}}>{paths[name]}</svg>;
};

// =========== Sidebar ===========
const Sidebar = ({active, onNav}) => {
  const nav = [
    {id:'dashboard', label:'主控制台', icon:'dashboard'},
    {id:'ai', label:'AI 决策', icon:'brain', badge:5},
    {id:'positions', label:'持仓与订单', icon:'layers'},
    {id:'backtest', label:'回测与绩效', icon:'chart'},
    {id:'risk', label:'策略与风控', icon:'shield'},
    {id:'audit', label:'审计日志', icon:'list'},
    {id:'settings', label:'设置', icon:'settings'},
  ];
  return (
    <aside style={{width:240,flexShrink:0,background:'var(--ap-bg-1)',borderRight:'1px solid var(--ap-line)',display:'flex',flexDirection:'column',height:'100%'}}>
      {/* brand */}
      <div style={{padding:'20px 20px 24px',display:'flex',alignItems:'center',gap:10,borderBottom:'1px solid var(--ap-line-soft)'}}>
        <div style={{width:32,height:32,borderRadius:8,background:'linear-gradient(135deg,var(--ap-mint) 0%,var(--ap-violet) 100%)',display:'flex',alignItems:'center',justifyContent:'center',color:'var(--ap-bg-0)',fontWeight:800,fontSize:15}}>α</div>
        <div>
          <div style={{fontSize:15,fontWeight:700,letterSpacing:'-.01em'}}>Alpha<span style={{color:'var(--ap-mint)'}}>Pilot</span></div>
          <div style={{fontSize:10,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)',letterSpacing:'.05em'}}>v0.1 · mainnet</div>
        </div>
      </div>

      {/* account summary */}
      <div style={{padding:'16px 20px',borderBottom:'1px solid var(--ap-line-soft)'}}>
        <div style={{fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.08em',textTransform:'uppercase',fontWeight:500,marginBottom:6}}>账户权益</div>
        <div style={{fontFamily:'var(--ap-font-mono)',fontSize:20,fontWeight:700,letterSpacing:'-.02em',lineHeight:1.1}}>${wfmt(W_MOCK.equity)}</div>
        <div style={{fontFamily:'var(--ap-font-mono)',fontSize:11,color:'var(--ap-mint)',marginTop:3}}>+{wfmtPct(W_MOCK.equityChangePct).slice(1)} 今日</div>
      </div>

      {/* nav */}
      <nav style={{flex:1,padding:'12px 12px',display:'flex',flexDirection:'column',gap:1,overflow:'auto'}}>
        {nav.map(n=>{
          const isActive = active===n.id;
          return (
            <div key={n.id} onClick={()=>onNav(n.id)}
              style={{display:'flex',alignItems:'center',gap:10,padding:'9px 10px',borderRadius:8,cursor:'pointer',
                color: isActive?'var(--ap-fg-1)':'var(--ap-fg-3)',
                background: isActive?'var(--ap-bg-3)':'transparent',
                fontSize:13,fontWeight:500,position:'relative',transition:'.12s'}}>
              {isActive && <div style={{position:'absolute',left:-12,top:8,bottom:8,width:3,borderRadius:2,background:'var(--ap-mint)'}}/>}
              <Icon name={n.icon} size={16} color={isActive?'var(--ap-mint)':'currentColor'}/>
              <span style={{flex:1}}>{n.label}</span>
              {n.badge && <span style={{fontSize:10,padding:'1px 6px',background:'var(--ap-violet-soft)',color:'var(--ap-violet)',borderRadius:999,fontFamily:'var(--ap-font-mono)',fontWeight:600}}>{n.badge}</span>}
            </div>
          );
        })}
      </nav>

      {/* footer status */}
      <div style={{padding:'14px 20px',borderTop:'1px solid var(--ap-line-soft)',display:'flex',flexDirection:'column',gap:8}}>
        <div style={{display:'flex',alignItems:'center',gap:8}}>
          <WDot c="var(--ap-mint)" glow/>
          <span style={{fontSize:11,color:'var(--ap-fg-2)',fontWeight:500}}>引擎运行中</span>
          <span style={{marginLeft:'auto',fontSize:10,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)'}}>48ms</span>
        </div>
        <div style={{fontSize:10,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)',letterSpacing:'.02em'}}>Binance · uptime 14h 22m</div>
      </div>
    </aside>
  );
};

// =========== Topbar ===========
const Topbar = ({pageTitle, pageSub, onCommand, riskState, regime, dayLossPct, positionsPct}) => {
  riskState = riskState || W_MOCK.riskState;
  regime = regime || W_MOCK.regime;
  dayLossPct = dayLossPct ?? W_MOCK.dayLossPct;
  positionsPct = positionsPct ?? W_MOCK.positionsPct;
  const riskCfg = {OK:{c:'var(--ap-mint)',label:'风控正常'}, WARN:{c:'var(--ap-amber)',label:'接近阈值'}, HALTED:{c:'var(--ap-rose)',label:'已熔断'}}[riskState];
  return (
    <header style={{display:'flex',alignItems:'center',gap:16,padding:'14px 24px',borderBottom:'1px solid var(--ap-line-soft)',background:'var(--ap-bg-1)',height:60,boxSizing:'border-box'}}>
      <div style={{flex:1,minWidth:0}}>
        <div style={{fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.08em',textTransform:'uppercase',fontWeight:500,marginBottom:1}}>{pageSub}</div>
        <div style={{fontSize:16,fontWeight:600,letterSpacing:'-.01em'}}>{pageTitle}</div>
      </div>

      {/* risk status chip */}
      <div style={{display:'flex',alignItems:'center',gap:10,padding:'6px 12px',background:'var(--ap-bg-2)',borderRadius:999,border:'1px solid var(--ap-line-soft)'}}>
        <WDot c={riskCfg.c} glow/>
        <span style={{fontSize:12,fontWeight:600,color:riskCfg.c}}>{riskCfg.label}</span>
        <span style={{fontSize:11,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>仓位 {positionsPct}% · 日损 {wfmtPct(dayLossPct)} · {regime}</span>
      </div>

      {/* command K */}
      <div onClick={onCommand} style={{display:'flex',alignItems:'center',gap:8,padding:'6px 10px 6px 12px',background:'var(--ap-bg-2)',borderRadius:8,border:'1px solid var(--ap-line-soft)',cursor:'pointer',width:260}}>
        <Icon name="search" size={14} color="var(--ap-fg-3)"/>
        <span style={{fontSize:12,color:'var(--ap-fg-4)',flex:1}}>搜索交易对、决策、策略…</span>
        <span style={{fontFamily:'var(--ap-font-mono)',fontSize:10,color:'var(--ap-fg-4)',background:'var(--ap-bg-3)',padding:'2px 6px',borderRadius:4,border:'1px solid var(--ap-line)'}}>⌘K</span>
      </div>

      {/* bell */}
      <button style={{width:34,height:34,borderRadius:8,background:'var(--ap-bg-2)',border:'1px solid var(--ap-line-soft)',display:'flex',alignItems:'center',justifyContent:'center',cursor:'pointer',color:'var(--ap-fg-2)',position:'relative'}}>
        <Icon name="bell" size={15}/>
        <span style={{position:'absolute',top:6,right:6,width:6,height:6,borderRadius:'50%',background:'var(--ap-rose)',boxShadow:'0 0 4px var(--ap-rose)'}}/>
      </button>

      {/* auto switch */}
      <div style={{display:'flex',alignItems:'center',gap:8,padding:'6px 12px',background:'var(--ap-mint-soft)',borderRadius:8,border:'1px solid rgba(0,211,149,.25)'}}>
        <WDot c="var(--ap-mint)" glow/>
        <span style={{fontSize:12,fontWeight:600,color:'var(--ap-mint)',fontFamily:'var(--ap-font-mono)'}}>AUTO</span>
      </div>
    </header>
  );
};

// =========== PageShell (sidebar + topbar) ===========
const PageShell = ({active, onNav, title, sub, children, riskState, regime, dayLossPct, positionsPct}) => (
  <div style={{display:'flex',width:'100%',height:'100%',background:'var(--ap-bg-0)'}}>
    <Sidebar active={active} onNav={onNav}/>
    <div style={{flex:1,display:'flex',flexDirection:'column',minWidth:0}}>
      <Topbar pageTitle={title} pageSub={sub} riskState={riskState} regime={regime} dayLossPct={dayLossPct} positionsPct={positionsPct}/>
      <div style={{flex:1,overflow:'auto',padding:'24px'}}>
        {children}
      </div>
    </div>
  </div>
);

// =========== Sparkline + mini price chart ===========
const WSpark = ({data, w=400, h=110, color='var(--ap-mint)', fill=true, gridId='wsg'}) => {
  const min = Math.min(...data), max=Math.max(...data), r=(max-min)||1;
  const pts = data.map((v,i)=>[i/(data.length-1)*w, h - ((v-min)/r)*(h-8) - 4]);
  const path = pts.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' ');
  const area = path+` L ${w} ${h} L 0 ${h} Z`;
  return (
    <svg width={w} height={h} style={{display:'block'}} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={gridId} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity=".35"/>
          <stop offset="1" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      {fill && <path d={area} fill={`url(#${gridId})`}/>}
      <path d={path} stroke={color} strokeWidth="1.8" fill="none" strokeLinejoin="round"/>
    </svg>
  );
};

Object.assign(window, {
  W_MOCK, WPill, WDot, WCard, WStat, Icon, Sidebar, Topbar, PageShell, WSpark,
  wfmt, wfmtPct, wfmtSigned
});
