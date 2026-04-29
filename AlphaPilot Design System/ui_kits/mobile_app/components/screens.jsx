// Screens — Dashboard / AI / Positions / Log / Config

// generate sparkline mock data
const genSpark = (n=48, base=120000, vol=800) => {
  const out=[]; let v=base;
  for(let i=0;i<n;i++){ v += (Math.sin(i/3)*vol) + (Math.random()-0.4)*vol*0.6; out.push(v); }
  out[n-1] = base + 2291;
  return out;
};
const SPARK = genSpark();

// =========================================================
// Dashboard (home)
// =========================================================
const DashboardScreen = ({ onOpenDecision }) => {
  const {equity, equityChangePct, equityChange, todayPnl, todayPnlPct, positions, tradesToday, winRate, regime, riskState, dayLossPct, positionsPct, decisions} = MOCK;
  const latest = decisions[0];
  return (
    <div style={{paddingTop:54,paddingBottom:100}}>
      <TopRiskBar state={riskState} regime={regime} loss={dayLossPct} positions={positionsPct}/>
      <AppHeader sub="AlphaPilot · AI 自主交易" title="仪表盘" right={
        <div style={{display:'flex',alignItems:'center',gap:6,padding:'6px 12px',background:'var(--ap-mint-soft)',borderRadius:999}}>
          <Dot c="var(--ap-mint)" glow/>
          <span style={{fontSize:11,color:'var(--ap-mint)',fontWeight:600}}>AUTO</span>
        </div>
      }/>

      {/* hero equity */}
      <div style={{padding:'0 16px',marginBottom:12}}>
        <Card>
          <div style={{fontSize:11,color:'var(--ap-fg-3)',letterSpacing:'.06em',textTransform:'uppercase',marginBottom:4}}>账户权益</div>
          <div style={{display:'flex',alignItems:'baseline',gap:10,marginBottom:2}}>
            <span style={{fontFamily:'var(--ap-font-mono)',fontSize:32,fontWeight:700,letterSpacing:'-.03em'}}>${fmt(equity)}</span>
          </div>
          <div style={{display:'flex',alignItems:'center',gap:6,marginBottom:10}}>
            <Num v={fmt(equityChange)} prefix="+$" positive size={13}/>
            <Num v={fmtPct(equityChangePct)} positive size={13}/>
            <span style={{fontSize:11,color:'var(--ap-fg-3)'}}>今日</span>
          </div>
          <div style={{margin:'0 -16px -16px'}}>
            <Sparkline data={SPARK} w={376} h={92}/>
          </div>
        </Card>
      </div>

      {/* quick stats */}
      <div style={{padding:'0 16px',display:'grid',gridTemplateColumns:'1fr 1fr',gap:10,marginBottom:12}}>
        <StatTile label="今日 PnL" value={fmtSigned(todayPnl)} sub={fmtPct(todayPnlPct)} tone="pos"/>
        <StatTile label="持仓数" value={positions.length} sub={`仓位 ${positionsPct}%`}/>
        <StatTile label="今日交易" value={tradesToday} sub={`胜率 ${winRate}%`}/>
        <StatTile label="最大回撤" value={fmtPct(dayLossPct)} sub="阈值 −2.00%" tone="neg"/>
      </div>

      {/* latest AI decision */}
      <div style={{padding:'0 16px',marginBottom:12}}>
        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'0 4px 8px'}}>
          <span style={{fontSize:12,color:'var(--ap-fg-3)',letterSpacing:'.05em',textTransform:'uppercase',fontWeight:600}}>最新 AI 决策</span>
          <span onClick={onOpenDecision} style={{fontSize:12,color:'var(--ap-mint)',cursor:'pointer'}}>查看全部 →</span>
        </div>
        <AIDecisionCard d={latest}/>
      </div>

      {/* positions compact */}
      <div style={{padding:'0 16px',marginBottom:12}}>
        <div style={{fontSize:12,color:'var(--ap-fg-3)',letterSpacing:'.05em',textTransform:'uppercase',fontWeight:600,padding:'0 4px 8px'}}>当前持仓</div>
        <div style={{display:'flex',flexDirection:'column',gap:8}}>
          {MOCK.positions.map(p=><PositionRow key={p.sym} p={p}/>)}
        </div>
      </div>
    </div>
  );
};

// =========================================================
// AI Decisions list
// =========================================================
const AIScreen = () => {
  const [filter, setFilter] = React.useState('all');
  const filtered = MOCK.decisions.filter(d=>filter==='all'||(filter==='exec'&&d.guard==='PASS')||(filter==='blocked'&&d.guard!=='PASS'));
  return (
    <div style={{paddingTop:54,paddingBottom:100}}>
      <TopRiskBar state={MOCK.riskState} regime={MOCK.regime} loss={MOCK.dayLossPct} positions={MOCK.positionsPct}/>
      <AppHeader sub="Decision stream" title="AI 决策流"/>
      <div style={{padding:'0 16px 10px',display:'flex',gap:6}}>
        {[{k:'all',l:'全部'},{k:'exec',l:'已执行'},{k:'blocked',l:'已拦截'}].map(t=>(
          <div key={t.k} onClick={()=>setFilter(t.k)} style={{padding:'6px 14px',borderRadius:999,fontSize:12,fontWeight:500,background:filter===t.k?'var(--ap-mint)':'var(--ap-bg-2)',color:filter===t.k?'var(--ap-bg-0)':'var(--ap-fg-2)',border:'1px solid '+(filter===t.k?'var(--ap-mint)':'var(--ap-line)'),cursor:'pointer'}}>{t.l}</div>
        ))}
      </div>
      <div style={{padding:'0 16px',display:'flex',flexDirection:'column',gap:12}}>
        {filtered.map((d,i)=><AIDecisionCard key={i} d={d}/>)}
      </div>
    </div>
  );
};

// =========================================================
// Positions detail
// =========================================================
const PositionsScreen = () => {
  const p = MOCK.positions[0];
  return (
    <div style={{paddingTop:54,paddingBottom:100}}>
      <TopRiskBar state={MOCK.riskState} regime={MOCK.regime} loss={MOCK.dayLossPct} positions={MOCK.positionsPct}/>
      <AppHeader sub="Positions · 2 active" title="持仓"/>

      <div style={{padding:'0 16px',marginBottom:12}}>
        <Card>
          <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:12}}>
            <div style={{width:40,height:40,borderRadius:'50%',background:'linear-gradient(135deg,#F7931A,#8B4E0D)',display:'flex',alignItems:'center',justifyContent:'center',color:'#fff',fontWeight:700}}>₿</div>
            <div style={{flex:1}}>
              <div style={{fontSize:16,fontWeight:700}}>BTCUSDT</div>
              <div style={{fontSize:11,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>趋势跟随 · 开仓 14:23</div>
            </div>
            <Pill tone="mint">LONG</Pill>
          </div>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10,marginBottom:12}}>
            <div><div style={{fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.05em',textTransform:'uppercase',marginBottom:2}}>浮动盈亏</div><Num v={fmtSigned(p.pnl)} positive size={22}/></div>
            <div><div style={{fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.05em',textTransform:'uppercase',marginBottom:2}}>收益率</div><Num v={fmtPct(p.pnlPct)} positive size={22}/></div>
          </div>
          <div style={{background:'var(--ap-bg-3)',borderRadius:10,padding:12,fontFamily:'var(--ap-font-mono)',fontSize:12,display:'grid',gridTemplateColumns:'1fr 1fr',gap:8}}>
            <div><span style={{color:'var(--ap-fg-3)'}}>数量 </span>{p.qty}</div>
            <div><span style={{color:'var(--ap-fg-3)'}}>标记 </span>{fmt(p.mark)}</div>
            <div><span style={{color:'var(--ap-fg-3)'}}>开仓 </span>{fmt(p.entry)}</div>
            <div><span style={{color:'var(--ap-fg-3)'}}>保证金 </span>2.5%</div>
            <div><span style={{color:'var(--ap-fg-3)'}}>SL </span><span style={{color:'var(--ap-rose)'}}>{fmt(64210)}</span></div>
            <div><span style={{color:'var(--ap-fg-3)'}}>TP </span><span style={{color:'var(--ap-mint)'}}>{fmt(68900)}</span></div>
          </div>
          {/* SL/TP bar */}
          <div style={{marginTop:12}}>
            <div style={{position:'relative',height:24,background:'var(--ap-bg-3)',borderRadius:6,overflow:'hidden'}}>
              <div style={{position:'absolute',left:'0%',top:0,bottom:0,width:'32%',background:'var(--ap-rose-soft)'}}/>
              <div style={{position:'absolute',right:'0%',top:0,bottom:0,width:'18%',background:'var(--ap-mint-soft)'}}/>
              <div style={{position:'absolute',left:'68%',top:0,bottom:0,width:2,background:'var(--ap-mint)',boxShadow:'0 0 8px var(--ap-mint)'}}/>
              <div style={{position:'absolute',left:'32%',top:0,bottom:0,width:1,background:'var(--ap-fg-3)'}}/>
            </div>
            <div style={{display:'flex',justifyContent:'space-between',marginTop:4,fontSize:10,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>
              <span>SL 64,210</span><span>开仓 67,420</span><span>当前 68,863</span><span>TP 68,900</span>
            </div>
          </div>
          <div style={{display:'flex',gap:8,marginTop:14}}>
            <button style={{flex:1,padding:'10px',borderRadius:10,border:'1px solid var(--ap-line)',background:'var(--ap-bg-3)',color:'var(--ap-fg-1)',fontSize:13,fontWeight:600,cursor:'pointer'}}>调整 SL/TP</button>
            <button style={{flex:1,padding:'10px',borderRadius:10,border:'none',background:'var(--ap-rose)',color:'#fff',fontSize:13,fontWeight:600,cursor:'pointer'}}>立即平仓</button>
          </div>
        </Card>
      </div>

      <div style={{padding:'0 16px'}}>
        <div style={{fontSize:12,color:'var(--ap-fg-3)',letterSpacing:'.05em',textTransform:'uppercase',fontWeight:600,padding:'0 4px 8px'}}>其他持仓</div>
        <PositionRow p={MOCK.positions[1]}/>
      </div>
    </div>
  );
};

// =========================================================
// Log / Activity
// =========================================================
const LogScreen = () => (
  <div style={{paddingTop:54,paddingBottom:100}}>
    <TopRiskBar state={MOCK.riskState} regime={MOCK.regime} loss={MOCK.dayLossPct} positions={MOCK.positionsPct}/>
    <AppHeader sub="Audit log · 实时" title="交易日志"/>
    <div style={{padding:'0 16px'}}>
      <Card>
        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:8}}>
          <span style={{fontSize:12,color:'var(--ap-fg-3)',letterSpacing:'.05em',textTransform:'uppercase',fontWeight:600}}>今日事件</span>
          <span style={{fontSize:11,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>{MOCK.logs.length} 条</span>
        </div>
        {MOCK.logs.map((l,i)=><LogRow key={i} l={l}/>)}
      </Card>
    </div>
    <div style={{padding:'12px 16px 0'}}>
      <div style={{fontSize:12,color:'var(--ap-fg-3)',letterSpacing:'.05em',textTransform:'uppercase',fontWeight:600,padding:'0 4px 8px'}}>日报摘要</div>
      <Card>
        <div style={{fontSize:13,color:'var(--ap-fg-2)',lineHeight:1.6}}>
          本日 <span style={{color:'var(--ap-fg-1)',fontWeight:600}}>7 笔</span>交易 · 胜率 <span style={{color:'var(--ap-mint)',fontFamily:'var(--ap-font-mono)'}}>57%</span> · 净收益 <span style={{color:'var(--ap-mint)',fontFamily:'var(--ap-font-mono)'}}>+1.82%</span>。
          BTCUSDT 主导盈利贡献（<span style={{color:'var(--ap-mint)',fontFamily:'var(--ap-font-mono)'}}>+$1,890</span>），ETHUSDT 受 chaotic regime 拖累（<span style={{color:'var(--ap-rose)',fontFamily:'var(--ap-font-mono)'}}>−$642</span>）。
          守卫共拦截 <span style={{color:'var(--ap-amber)',fontFamily:'var(--ap-font-mono)'}}>2 次</span>，均因 RR &lt; 1.5。
        </div>
      </Card>
    </div>
  </div>
);

// =========================================================
// Config
// =========================================================
const ConfigScreen = () => {
  const [auto, setAuto] = React.useState(true);
  const [testnet, setTestnet] = React.useState(false);
  const [tf, setTf] = React.useState('15m');
  return (
    <div style={{paddingTop:54,paddingBottom:100}}>
      <TopRiskBar state={MOCK.riskState} regime={MOCK.regime} loss={MOCK.dayLossPct} positions={MOCK.positionsPct}/>
      <AppHeader sub="Strategy · Risk · API" title="配置中心"/>

      <div style={{padding:'0 16px',display:'flex',flexDirection:'column',gap:12}}>
        <Card>
          <div style={{fontSize:11,color:'var(--ap-fg-3)',letterSpacing:'.06em',textTransform:'uppercase',marginBottom:10}}>运行开关</div>
          <Row label="自动交易" on={auto} onToggle={()=>setAuto(!auto)} sub="守卫通过后自动下单"/>
          <Row label="测试盘模式" on={testnet} onToggle={()=>setTestnet(!testnet)} sub="Binance Testnet · 无真实资金"/>
          <Row label="通知（Telegram）" on={true} onToggle={()=>{}} sub="开仓/平仓/熔断即时推送" last/>
        </Card>

        <Card>
          <div style={{fontSize:11,color:'var(--ap-fg-3)',letterSpacing:'.06em',textTransform:'uppercase',marginBottom:10}}>交易对 · 周期</div>
          <div style={{display:'flex',flexWrap:'wrap',gap:6,marginBottom:12}}>
            {['BTCUSDT','ETHUSDT'].map(s=><Pill key={s} tone="mint" mono>{s}</Pill>)}
            <Pill tone="default">+ 添加</Pill>
          </div>
          <div style={{fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.05em',textTransform:'uppercase',marginBottom:6}}>K线周期</div>
          <div style={{display:'inline-flex',background:'var(--ap-bg-3)',borderRadius:10,padding:3,border:'1px solid var(--ap-line)'}}>
            {['5m','15m','1h','4h','1d'].map(t=>(
              <div key={t} onClick={()=>setTf(t)} style={{fontSize:12,padding:'6px 12px',borderRadius:8,fontFamily:'var(--ap-font-mono)',cursor:'pointer',background:tf===t?'var(--ap-bg-4)':'transparent',color:tf===t?'var(--ap-fg-1)':'var(--ap-fg-3)'}}>{t}</div>
            ))}
          </div>
        </Card>

        <Card>
          <div style={{fontSize:11,color:'var(--ap-fg-3)',letterSpacing:'.06em',textTransform:'uppercase',marginBottom:10}}>受限策略框架</div>
          <StratRow name="趋势跟随" active enabled desc="EMA 排列 + ATR 确认"/>
          <StratRow name="突破确认" active={false} enabled desc="阻力位突破 + 成交量"/>
          <StratRow name="观望模式" active={false} enabled={true} desc="chaotic regime 默认" last/>
        </Card>

        <Card>
          <div style={{fontSize:11,color:'var(--ap-fg-3)',letterSpacing:'.06em',textTransform:'uppercase',marginBottom:10}}>硬风控（不可学习）</div>
          <RiskRow label="单笔最大风险" val="1.00%"/>
          <RiskRow label="最大单币持仓" val="15%"/>
          <RiskRow label="日亏损阈值" val="−2.00%" tone="neg"/>
          <RiskRow label="连续亏损熔断" val="3 笔" last/>
        </Card>

        <Card>
          <div style={{fontSize:11,color:'var(--ap-fg-3)',letterSpacing:'.06em',textTransform:'uppercase',marginBottom:10}}>Binance API</div>
          <div style={{display:'flex',alignItems:'center',gap:10,padding:'10px 0'}}>
            <img src="../../assets/binance_logo.svg" style={{width:24,height:24}}/>
            <div style={{flex:1}}>
              <div style={{fontSize:13,fontFamily:'var(--ap-font-mono)'}}>bnx_••••••••••3f2a</div>
              <div style={{fontSize:11,color:'var(--ap-mint)'}}>已连接 · 最后验证 14:20</div>
            </div>
            <Pill tone="mint">ACTIVE</Pill>
          </div>
        </Card>

        <div style={{padding:'10px 0 20px',textAlign:'center',fontSize:10,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)'}}>AlphaPilot v0.1 · build 2026.04.21</div>
      </div>
    </div>
  );
};

const Row = ({label, on, onToggle, sub, last}) => (
  <div style={{display:'flex',alignItems:'center',padding:'10px 0',borderBottom:last?'none':'1px solid var(--ap-line-soft)'}}>
    <div style={{flex:1}}>
      <div style={{fontSize:14,color:'var(--ap-fg-1)'}}>{label}</div>
      {sub && <div style={{fontSize:11,color:'var(--ap-fg-3)',marginTop:2}}>{sub}</div>}
    </div>
    <div onClick={onToggle} style={{width:44,height:26,borderRadius:999,background:on?'var(--ap-mint)':'var(--ap-bg-4)',position:'relative',cursor:'pointer',transition:'.15s'}}>
      <div style={{position:'absolute',top:3,left:on?21:3,width:20,height:20,background:'#fff',borderRadius:'50%',transition:'.15s'}}/>
    </div>
  </div>
);

const StratRow = ({name, active, enabled, desc, last}) => (
  <div style={{display:'flex',alignItems:'center',padding:'10px 0',borderBottom:last?'none':'1px solid var(--ap-line-soft)'}}>
    <Dot c={active?'var(--ap-mint)':'var(--ap-fg-4)'} glow={active}/>
    <div style={{flex:1,marginLeft:10}}>
      <div style={{fontSize:14,color:'var(--ap-fg-1)'}}>{name} {active && <Pill tone="mint">ACTIVE</Pill>}</div>
      <div style={{fontSize:11,color:'var(--ap-fg-3)',marginTop:2}}>{desc}</div>
    </div>
    <Pill tone={enabled?'mint':'default'}>{enabled?'启用':'停用'}</Pill>
  </div>
);

const RiskRow = ({label, val, tone, last}) => (
  <div style={{display:'flex',alignItems:'center',padding:'10px 0',borderBottom:last?'none':'1px solid var(--ap-line-soft)'}}>
    <div style={{fontSize:13,color:'var(--ap-fg-2)',flex:1}}>{label}</div>
    <span style={{fontFamily:'var(--ap-font-mono)',fontSize:14,fontWeight:600,color:tone==='neg'?'var(--ap-rose)':'var(--ap-fg-1)'}}>{val}</span>
  </div>
);

Object.assign(window, { DashboardScreen, AIScreen, PositionsScreen, LogScreen, ConfigScreen });
