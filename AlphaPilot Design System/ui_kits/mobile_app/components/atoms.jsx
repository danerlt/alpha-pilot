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
  riskState: 'OK', // OK | WARN | HALTED
  tradesToday: 7,
  winRate: 57,
  regime: 'trending_up',
  positions: [
    { sym:'BTCUSDT', qty:0.048, entry:67420.50, mark:68863.92, pnl:69.29, pnlPct:2.14 },
    { sym:'ETHUSDT', qty:0.82, entry:3240.00, mark:3219.92, pnl:-16.47, pnlPct:-0.62 },
  ],
  decisions: [
    { t:'14:23:08', sym:'BTCUSDT', tf:'15m', action:'OPEN_LONG', conf:0.78, strat:'趋势跟随', sl:64210, tp:68900, size:'2.5%', guard:'PASS', reason:'EMA20>EMA50>EMA200 金叉排列，1h 成交量较均值放大 1.4x，回踩 EMA20 未破，确认突破有效。', entry:67420.50 },
    { t:'13:45:00', sym:'ETHUSDT', tf:'15m', action:'HOLD', conf:0.42, strat:'观望模式', guard:'DEGRADE', reason:'波动率进入高位，regime 由 trending_up 切换为 chaotic，降级为观望。' },
    { t:'12:30:00', sym:'BTCUSDT', tf:'15m', action:'OPEN_LONG', conf:0.71, strat:'突破确认', guard:'REJECT', reason:'触发风险收益比 <1.5 检查，守卫拒绝，回退 HOLD。' },
    { t:'10:15:00', sym:'BTCUSDT', tf:'15m', action:'CLOSE_LONG', conf:0.85, strat:'止盈执行', guard:'PASS', reason:'达到 TP 价位，执行平仓，本笔 +1.82%。', entry:66100 },
  ],
  logs: [
    { t:'14:23:09', type:'fill', msg:'BTCUSDT 市价成交 0.048 @ 67,420.50', color:'mint' },
    { t:'14:23:09', type:'order', msg:'止损挂单 64,210.00 · 止盈 68,900.00', color:'fg' },
    { t:'14:23:08', type:'guard', msg:'守卫通过 PASS · 检查 8/8', color:'mint' },
    { t:'14:23:08', type:'ai', msg:'AI 决策 OPEN_LONG · 置信度 0.78', color:'violet' },
    { t:'13:45:05', type:'guard', msg:'守卫降级 DEGRADE · regime 异常', color:'amber' },
    { t:'12:30:12', type:'guard', msg:'守卫拒绝 REJECT · RR<1.5 · 回退 HOLD', color:'rose' },
    { t:'10:15:30', type:'fill', msg:'BTCUSDT 平仓 @ 68,903.20 · +1.82%', color:'mint' },
  ],
};

// --- atoms ---
const Pill = ({ children, tone='default', mono=true }) => {
  const tones = {
    mint:{bg:'var(--ap-mint-soft)', c:'var(--ap-mint)'},
    rose:{bg:'var(--ap-rose-soft)', c:'var(--ap-rose)'},
    amber:{bg:'var(--ap-amber-soft)', c:'var(--ap-amber)'},
    violet:{bg:'var(--ap-violet-soft)', c:'var(--ap-violet)'},
    cyan:{bg:'var(--ap-cyan-soft)', c:'var(--ap-cyan)'},
    default:{bg:'var(--ap-bg-3)', c:'var(--ap-fg-2)'},
  };
  const s = tones[tone]||tones.default;
  return <span style={{display:'inline-flex',alignItems:'center',gap:4,fontSize:10,padding:'2px 8px',borderRadius:999,background:s.bg,color:s.c,fontWeight:600,fontFamily: mono?'var(--ap-font-mono)':'inherit',letterSpacing:'.02em'}}>{children}</span>;
};

const Dot = ({c, glow}) => <span style={{width:6,height:6,borderRadius:'50%',background:c,boxShadow:glow?`0 0 6px ${c}`:'none',display:'inline-block'}}/>;

const Card = ({children, style, glow}) => (
  <div style={{background:'var(--ap-bg-2)',borderRadius:16,padding:16,border:'1px solid var(--ap-line-soft)',...(glow?{borderColor:'var(--ap-violet)',boxShadow:'0 0 24px rgba(124,92,255,.15)'}:{}),...style}}>{children}</div>
);

const Num = ({v, prefix='', suffix='', positive, negative, size=14, weight=600}) => {
  const c = positive?'var(--ap-mint)':negative?'var(--ap-rose)':'var(--ap-fg-1)';
  return <span style={{fontFamily:'var(--ap-font-mono)',fontVariantNumeric:'tabular-nums',fontSize:size,fontWeight:weight,color:c,letterSpacing:'-.01em'}}>{prefix}{v}{suffix}</span>;
};

const fmt = (n, d=2) => n.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const fmtPct = n => (n>=0?'+':'')+n.toFixed(2)+'%';
const fmtSigned = n => (n>=0?'+':'−')+'$'+Math.abs(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});

// --- Top bar: risk status (always-present) ---
const TopRiskBar = ({state='OK', regime, loss, positions}) => {
  const cfg = {
    OK:{c:'var(--ap-mint)',bg:'rgba(0,211,149,.08)',label:'风控正常'},
    WARN:{c:'var(--ap-amber)',bg:'rgba(240,185,11,.10)',label:'接近阈值'},
    HALTED:{c:'var(--ap-rose)',bg:'rgba(255,77,109,.12)',label:'已熔断'},
  }[state];
  return (
    <div style={{background:cfg.bg,backdropFilter:'blur(20px)',padding:'8px 16px',display:'flex',alignItems:'center',gap:8,borderBottom:'1px solid var(--ap-line-soft)'}}>
      <Dot c={cfg.c} glow/>
      <span style={{fontSize:12,fontWeight:600,color:cfg.c}}>{cfg.label}</span>
      <span style={{fontSize:11,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>· 仓位 {positions}% · 日损 {fmtPct(loss)}</span>
      <span style={{marginLeft:'auto',fontSize:10,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>{regime}</span>
    </div>
  );
};

// --- Header ---
const AppHeader = ({title, right, sub}) => (
  <div style={{padding:'16px 16px 10px',display:'flex',alignItems:'flex-end',justifyContent:'space-between'}}>
    <div>
      <div style={{fontSize:11,color:'var(--ap-fg-3)',letterSpacing:'.08em',textTransform:'uppercase',marginBottom:2}}>{sub}</div>
      <div style={{fontSize:26,fontWeight:700,letterSpacing:'-.02em'}}>{title}</div>
    </div>
    {right}
  </div>
);

// --- Stat tile ---
const StatTile = ({label, value, sub, tone}) => (
  <div style={{background:'var(--ap-bg-2)',borderRadius:14,padding:'12px 14px',display:'flex',flexDirection:'column',gap:3,border:'1px solid var(--ap-line-soft)'}}>
    <div style={{fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.05em',textTransform:'uppercase'}}>{label}</div>
    <div style={{fontFamily:'var(--ap-font-mono)',fontSize:19,fontWeight:700,letterSpacing:'-.02em',color: tone==='pos'?'var(--ap-mint)':tone==='neg'?'var(--ap-rose)':'var(--ap-fg-1)'}}>{value}</div>
    {sub && <div style={{fontSize:11,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>{sub}</div>}
  </div>
);

// --- PnL sparkline (inline SVG) ---
const Sparkline = ({data, w=348, h=88, color='var(--ap-mint)'}) => {
  const min = Math.min(...data), max=Math.max(...data), r=(max-min)||1;
  const pts = data.map((v,i)=>[i/(data.length-1)*w, h - ((v-min)/r)*(h-8) - 4]);
  const path = pts.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' ');
  const area = path+` L ${w} ${h} L 0 ${h} Z`;
  return (
    <svg width={w} height={h} style={{display:'block'}}>
      <defs>
        <linearGradient id="spark-grad" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity=".3"/>
          <stop offset="1" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <path d={area} fill="url(#spark-grad)"/>
      <path d={path} stroke={color} strokeWidth="1.8" fill="none" strokeLinejoin="round"/>
    </svg>
  );
};

// --- Decision pipeline (horizontal stepper) ---
const DecisionStepper = ({ai='done', guard='done', exec='done', guardState='PASS'}) => {
  const step = (label, state, idx) => {
    const colors = state==='done'?{dot:'var(--ap-mint)',txt:'var(--ap-fg-1)'}:state==='active'?{dot:'var(--ap-violet)',txt:'var(--ap-violet)'}:{dot:'var(--ap-bg-4)',txt:'var(--ap-fg-4)'};
    return <div key={idx} style={{display:'flex',flexDirection:'column',alignItems:'center',gap:6,flexShrink:0,width:54}}>
      <div style={{width:22,height:22,borderRadius:'50%',background:colors.dot,display:'flex',alignItems:'center',justifyContent:'center',fontSize:11,color:'var(--ap-bg-0)',fontWeight:700,lineHeight:1}}>{state==='done'?'✓':idx+1}</div>
      <div style={{fontSize:11,color:colors.txt,fontWeight:600,whiteSpace:'nowrap'}}>{label}</div>
    </div>;
  };
  return (
    <div style={{display:'flex',alignItems:'flex-start',gap:0,padding:'8px 0'}}>
      {step('AI', ai, 0)}
      <div style={{flex:1,height:2,background:'var(--ap-mint)',marginTop:10}}/>
      {step('守卫', guard, 1)}
      <div style={{flex:1,height:2,background:'var(--ap-mint)',marginTop:10}}/>
      {step('执行', exec, 2)}
    </div>
  );
};

// --- AI Decision Card (hero) ---
const AIDecisionCard = ({d}) => {
  const actionColor = d.action==='OPEN_LONG'?'var(--ap-mint)':d.action==='CLOSE_LONG'?'var(--ap-rose)':'var(--ap-fg-2)';
  const guardTone = d.guard==='PASS'?'mint':d.guard==='REJECT'?'rose':'amber';
  return (
    <Card glow>
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:10}}>
        <div style={{display:'inline-flex',alignItems:'center',gap:6,fontSize:10,color:'var(--ap-violet)',fontWeight:700,letterSpacing:'.08em'}}>
          <Dot c="var(--ap-violet)" glow/> AI DECISION
        </div>
        <div style={{fontSize:11,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>{d.sym} · {d.tf} · {d.t}</div>
      </div>
      <div style={{display:'flex',alignItems:'baseline',gap:10,marginBottom:4}}>
        <span style={{fontFamily:'var(--ap-font-mono)',fontSize:24,fontWeight:700,color:actionColor,letterSpacing:'.02em'}}>{d.action}</span>
        <span style={{fontSize:12,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>confidence {d.conf?.toFixed(2)}</span>
      </div>
      <div style={{fontSize:12,color:'var(--ap-fg-2)',marginBottom:12}}>{d.strat}</div>
      {d.sl && (
        <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:8,fontFamily:'var(--ap-font-mono)',fontSize:11,padding:'10px 0',borderTop:'1px solid var(--ap-line-soft)',borderBottom:'1px solid var(--ap-line-soft)',marginBottom:12}}>
          <div><div style={{color:'var(--ap-fg-3)',fontSize:9,letterSpacing:'.05em'}}>ENTRY</div><div>{fmt(d.entry)}</div></div>
          <div><div style={{color:'var(--ap-fg-3)',fontSize:9,letterSpacing:'.05em'}}>SIZE</div><div>{d.size}</div></div>
          <div><div style={{color:'var(--ap-fg-3)',fontSize:9,letterSpacing:'.05em'}}>SL</div><div style={{color:'var(--ap-rose)'}}>{fmt(d.sl)}</div></div>
          <div><div style={{color:'var(--ap-fg-3)',fontSize:9,letterSpacing:'.05em'}}>TP</div><div style={{color:'var(--ap-mint)'}}>{fmt(d.tp)}</div></div>
        </div>
      )}
      <DecisionStepper/>
      <div style={{fontSize:12,color:'var(--ap-fg-2)',lineHeight:1.55,marginTop:10,padding:'10px 12px',background:'var(--ap-bg-3)',borderRadius:10}}>
        <div style={{fontSize:10,color:'var(--ap-fg-3)',marginBottom:4,letterSpacing:'.05em'}}>REASONING</div>
        {d.reason}
      </div>
      <div style={{marginTop:10,display:'flex',gap:8,alignItems:'center'}}>
        <Pill tone={guardTone}>守卫 {d.guard}</Pill>
        <span style={{marginLeft:'auto',fontSize:11,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)'}}>trace · 7f3a9b2c</span>
      </div>
    </Card>
  );
};

// --- Position Row ---
const PositionRow = ({p, onClick}) => {
  const isUp = p.pnlPct>=0;
  const coinBg = p.sym.startsWith('BTC')?'linear-gradient(135deg,#F7931A,#8B4E0D)':p.sym.startsWith('ETH')?'linear-gradient(135deg,#627EEA,#3C54BD)':'linear-gradient(135deg,#9945FF,#14F195)';
  const glyph = p.sym.startsWith('BTC')?'₿':p.sym.startsWith('ETH')?'Ξ':'◎';
  return (
    <div onClick={onClick} style={{display:'flex',alignItems:'center',gap:12,padding:'12px 14px',background:'var(--ap-bg-2)',borderRadius:14,border:'1px solid var(--ap-line-soft)',cursor:'pointer'}}>
      <div style={{width:36,height:36,borderRadius:'50%',background:coinBg,display:'flex',alignItems:'center',justifyContent:'center',color:'#fff',fontSize:16,fontWeight:700,flexShrink:0}}>{glyph}</div>
      <div style={{flex:1,minWidth:0}}>
        <div style={{fontSize:14,fontWeight:600}}>{p.sym}</div>
        <div style={{fontSize:11,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>{p.qty} · entry {fmt(p.entry)}</div>
      </div>
      <div style={{textAlign:'right'}}>
        <div style={{fontFamily:'var(--ap-font-mono)',fontSize:14,fontWeight:600}}>${fmt(p.mark)}</div>
        <div style={{fontFamily:'var(--ap-font-mono)',fontSize:11,color:isUp?'var(--ap-mint)':'var(--ap-rose)'}}>{fmtPct(p.pnlPct)} · {fmtSigned(p.pnl)}</div>
      </div>
    </div>
  );
};

// --- Log Row ---
const LogRow = ({l}) => {
  const colorMap = {mint:'var(--ap-mint)',rose:'var(--ap-rose)',amber:'var(--ap-amber)',violet:'var(--ap-violet)',fg:'var(--ap-fg-2)'};
  const c = colorMap[l.color];
  return (
    <div style={{display:'flex',gap:10,padding:'10px 0',borderBottom:'1px solid var(--ap-line-soft)'}}>
      <span style={{fontFamily:'var(--ap-font-mono)',fontSize:10,color:'var(--ap-fg-3)',minWidth:58,flexShrink:0,paddingTop:2}}>{l.t}</span>
      <Dot c={c} glow={l.color==='violet'||l.color==='rose'}/>
      <span style={{fontSize:12,color:'var(--ap-fg-1)',flex:1,lineHeight:1.5}}>{l.msg}</span>
    </div>
  );
};

// --- Tab Bar ---
const TabBar = ({active, onChange}) => {
  const tabs = [
    {id:'home', label:'仪表盘', icon:'◎'},
    {id:'ai', label:'AI 决策', icon:'✦'},
    {id:'pos', label:'持仓', icon:'◈'},
    {id:'log', label:'日志', icon:'≡'},
    {id:'cfg', label:'配置', icon:'⚙'},
  ];
  return (
    <div style={{position:'absolute',bottom:0,left:0,right:0,background:'rgba(11,14,21,.85)',backdropFilter:'blur(24px)',borderTop:'1px solid var(--ap-line-soft)',padding:'8px 8px 28px',display:'flex',justifyContent:'space-around',zIndex:50}}>
      {tabs.map(t=>(
        <div key={t.id} onClick={()=>onChange(t.id)} style={{display:'flex',flexDirection:'column',alignItems:'center',gap:4,padding:'4px 10px',cursor:'pointer',color:active===t.id?'var(--ap-mint)':'var(--ap-fg-3)',transition:'color .15s'}}>
          <span style={{fontSize:18,fontFamily:'var(--ap-font-mono)'}}>{t.icon}</span>
          <span style={{fontSize:10,fontWeight:500}}>{t.label}</span>
        </div>
      ))}
    </div>
  );
};

Object.assign(window, {
  MOCK, Pill, Dot, Card, Num, fmt, fmtPct, fmtSigned,
  TopRiskBar, AppHeader, StatTile, Sparkline, DecisionStepper,
  AIDecisionCard, PositionRow, LogRow, TabBar
});
