// Web pages: Dashboard, AI list, Positions, Backtest, Risk config, Audit log

// generate sparkline
const genData = (n=60, base=120000, vol=700) => {
  const out=[]; let v=base;
  for(let i=0;i<n;i++){ v += (Math.sin(i/5)*vol) + (Math.random()-0.4)*vol*0.7; out.push(v); }
  out[n-1] = base + 2291;
  return out;
};
const EQUITY_DATA = genData();
const PNL_DATA = genData(30, 0, 400).map((v,i)=>v*(i>15?1:-0.3));

// =========================================================
// Dashboard
// =========================================================
const WDashboard = ({ aiVariant, onNav }) => {
  const {equity, equityChange, equityChangePct, todayPnl, todayPnlPct, weekPnl, weekPnlPct, mtdPnl, mtdPnlPct, positions, tradesToday, winRate, sharpe, maxDD, avgHold, decisions, events} = W_MOCK;

  return (
    <div style={{display:'grid',gridTemplateColumns:'minmax(0,1fr) 360px',gap:20}}>
      {/* LEFT: main column */}
      <div style={{display:'flex',flexDirection:'column',gap:20,minWidth:0}}>
        {/* AI-first hero */}
        <AIDecisionCard d={decisions[0]} variant={aiVariant}/>

        {/* equity row */}
        <WCard title="账户权益" right={
          <div style={{display:'flex',gap:4,padding:3,background:'var(--ap-bg-3)',borderRadius:8}}>
            {['1D','1W','1M','3M','ALL'].map((r,i)=>(
              <span key={r} style={{padding:'4px 10px',fontSize:11,fontFamily:'var(--ap-font-mono)',borderRadius:5,background:i===2?'var(--ap-bg-4)':'transparent',color:i===2?'var(--ap-fg-1)':'var(--ap-fg-3)',cursor:'pointer'}}>{r}</span>
            ))}
          </div>
        }>
          <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:24,marginBottom:16}}>
            <WStat label="当前权益" value={`$${wfmt(equity)}`} sub={`+${wfmt(equityChange)} 今日`} size="lg"/>
            <WStat label="今日" value={wfmtPct(todayPnlPct)} sub={wfmtSigned(todayPnl)} tone="pos"/>
            <WStat label="本周" value={wfmtPct(weekPnlPct)} sub={wfmtSigned(weekPnl)} tone="pos"/>
            <WStat label="本月" value={wfmtPct(mtdPnlPct)} sub={wfmtSigned(mtdPnl)} tone="pos"/>
          </div>
          <div style={{margin:'0 -18px -16px',position:'relative'}}>
            <WSpark data={EQUITY_DATA} w={700} h={160} gridId="spd1"/>
          </div>
        </WCard>

        {/* key metrics grid */}
        <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12}}>
          <WCard dense><WStat label="今日交易" value={tradesToday} sub={`胜率 ${winRate}%`}/></WCard>
          <WCard dense><WStat label="Sharpe 30d" value={sharpe.toFixed(2)} sub="risk-adjusted"/></WCard>
          <WCard dense><WStat label="最大回撤" value={wfmtPct(maxDD)} sub="阈值 −8%" tone="neg"/></WCard>
          <WCard dense><WStat label="平均持仓时长" value={avgHold} sub="中短线"/></WCard>
        </div>

        {/* positions table */}
        <WCard title="当前持仓" right={<span onClick={()=>onNav('positions')} style={{fontSize:11,color:'var(--ap-mint)',cursor:'pointer',fontFamily:'var(--ap-font-mono)'}}>查看全部 →</span>}>
          <WPositionsTable positions={positions}/>
        </WCard>
      </div>

      {/* RIGHT: event stream */}
      <WCard title="事件流 · 实时" right={<WPill tone="mint">LIVE</WPill>} style={{height:'fit-content',position:'sticky',top:0}}>
        <div style={{display:'flex',flexDirection:'column',maxHeight:780,overflow:'auto'}}>
          {events.map((e,i)=>(
            <WEventRow key={i} e={e}/>
          ))}
        </div>
      </WCard>
    </div>
  );
};

const WEventRow = ({e}) => {
  const colors = {mint:'var(--ap-mint)',rose:'var(--ap-rose)',amber:'var(--ap-amber)',violet:'var(--ap-violet)',fg:'var(--ap-fg-2)'};
  const iconMap = {fill:'check', order:'clock', guard:'shield', ai:'brain'};
  return (
    <div style={{display:'flex',gap:10,padding:'10px 2px',borderBottom:'1px solid var(--ap-line-soft)'}}>
      <div style={{width:24,height:24,borderRadius:6,background:'var(--ap-bg-3)',display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0}}>
        <Icon name={iconMap[e.kind]||'circle'} size={12} color={colors[e.color]}/>
      </div>
      <div style={{flex:1,minWidth:0}}>
        <div style={{fontSize:12,color:'var(--ap-fg-1)',lineHeight:1.5}}>{e.msg}</div>
        <div style={{fontSize:10,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)',marginTop:2,letterSpacing:'.02em'}}>{e.t}</div>
      </div>
    </div>
  );
};

const WPositionsTable = ({positions, detail}) => (
  <div style={{margin:'-16px -18px'}}>
    <table style={{width:'100%',borderCollapse:'collapse',fontSize:12}}>
      <thead>
        <tr style={{borderBottom:'1px solid var(--ap-line)'}}>
          {['交易对','方向','数量','入场','标记','浮盈','收益率','止损','止盈','持仓时长','策略','操作'].slice(0, detail?12:9).map(h=>(
            <th key={h} style={{padding:'10px 12px',textAlign:'left',fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.06em',textTransform:'uppercase',fontWeight:500}}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {positions.map((p,i)=>{
          const isUp = p.pnl>=0;
          return (
            <tr key={i} style={{borderBottom:'1px solid var(--ap-line-soft)',cursor:'pointer'}}>
              <td style={{padding:'12px'}}>
                <div style={{display:'flex',alignItems:'center',gap:8}}>
                  <div style={{width:22,height:22,borderRadius:'50%',background:p.sym.startsWith('BTC')?'linear-gradient(135deg,#F7931A,#8B4E0D)':'linear-gradient(135deg,#627EEA,#3C54BD)',display:'flex',alignItems:'center',justifyContent:'center',color:'#fff',fontWeight:700,fontSize:10}}>{p.sym.startsWith('BTC')?'₿':'Ξ'}</div>
                  <span style={{fontFamily:'var(--ap-font-mono)',fontWeight:600}}>{p.sym}</span>
                </div>
              </td>
              <td style={{padding:'12px'}}><WPill tone={p.side==='LONG'?'mint':'rose'}>{p.side}</WPill></td>
              <td style={{padding:'12px',fontFamily:'var(--ap-font-mono)'}}>{p.qty}</td>
              <td style={{padding:'12px',fontFamily:'var(--ap-font-mono)'}}>{wfmt(p.entry)}</td>
              <td style={{padding:'12px',fontFamily:'var(--ap-font-mono)'}}>{wfmt(p.mark)}</td>
              <td style={{padding:'12px',fontFamily:'var(--ap-font-mono)',color:isUp?'var(--ap-mint)':'var(--ap-rose)'}}>{wfmtSigned(p.pnl)}</td>
              <td style={{padding:'12px',fontFamily:'var(--ap-font-mono)',color:isUp?'var(--ap-mint)':'var(--ap-rose)'}}>{wfmtPct(p.pnlPct)}</td>
              {detail && <td style={{padding:'12px',fontFamily:'var(--ap-font-mono)',color:'var(--ap-rose)'}}>{wfmt(p.sl)}</td>}
              {detail && <td style={{padding:'12px',fontFamily:'var(--ap-font-mono)',color:'var(--ap-mint)'}}>{wfmt(p.tp)}</td>}
              <td style={{padding:'12px',fontFamily:'var(--ap-font-mono)',color:'var(--ap-fg-3)'}}>{p.age}</td>
              {detail && <td style={{padding:'12px',color:'var(--ap-fg-2)'}}>{p.strat}</td>}
              {detail && <td style={{padding:'12px'}}>
                <button style={{padding:'4px 10px',background:'var(--ap-bg-3)',border:'1px solid var(--ap-line)',borderRadius:6,color:'var(--ap-fg-2)',fontSize:11,cursor:'pointer',marginRight:4}}>编辑</button>
                <button style={{padding:'4px 10px',background:'var(--ap-rose-soft)',border:'1px solid var(--ap-rose)',borderRadius:6,color:'var(--ap-rose)',fontSize:11,cursor:'pointer'}}>平仓</button>
              </td>}
            </tr>
          );
        })}
      </tbody>
    </table>
  </div>
);

// =========================================================
// AI decisions list
// =========================================================
const WAIPage = ({aiVariant}) => {
  const [filter, setFilter] = React.useState('all');
  const filtered = W_MOCK.decisions.filter(d=>filter==='all'||(filter==='exec'&&d.guard==='PASS')||(filter==='blocked'&&d.guard!=='PASS'));
  return (
    <div style={{display:'flex',flexDirection:'column',gap:16,maxWidth:1100}}>
      <div style={{display:'flex',alignItems:'center',gap:8}}>
        {[{k:'all',l:'全部',n:W_MOCK.decisions.length},{k:'exec',l:'已执行',n:W_MOCK.decisions.filter(d=>d.guard==='PASS').length},{k:'blocked',l:'已拦截',n:W_MOCK.decisions.filter(d=>d.guard!=='PASS').length}].map(t=>(
          <div key={t.k} onClick={()=>setFilter(t.k)} style={{padding:'6px 14px',borderRadius:8,fontSize:12,fontWeight:500,background:filter===t.k?'var(--ap-bg-3)':'var(--ap-bg-2)',color:filter===t.k?'var(--ap-fg-1)':'var(--ap-fg-3)',border:'1px solid '+(filter===t.k?'var(--ap-line)':'var(--ap-line-soft)'),cursor:'pointer',display:'inline-flex',alignItems:'center',gap:6,whiteSpace:'nowrap',flexShrink:0}}>
            {t.l} <span style={{fontFamily:'var(--ap-font-mono)',fontSize:10,opacity:.7}}>{t.n}</span>
          </div>
        ))}
        <div style={{marginLeft:'auto',fontSize:11,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>样式: <b style={{color:'var(--ap-violet)'}}>{aiVariant}</b></div>
      </div>
      {filtered.map(d=><AIDecisionCard key={d.id} d={d} variant={aiVariant}/>)}
    </div>
  );
};

// =========================================================
// Positions page
// =========================================================
const WPositionsPage = () => (
  <div style={{display:'flex',flexDirection:'column',gap:20}}>
    <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12}}>
      <WCard dense><WStat label="总持仓" value={W_MOCK.positions.length} sub={`占比 ${W_MOCK.positionsPct}%`}/></WCard>
      <WCard dense><WStat label="多头" value="2" sub="BTC · ETH"/></WCard>
      <WCard dense><WStat label="浮盈总计" value={wfmtSigned(W_MOCK.positions.reduce((s,p)=>s+p.pnl,0))} tone="pos"/></WCard>
      <WCard dense><WStat label="活跃挂单" value="4" sub="SL×2 · TP×2"/></WCard>
    </div>

    <WCard title="持仓">
      <WPositionsTable positions={W_MOCK.positions} detail/>
    </WCard>

    <WCard title="订单簿">
      <div style={{margin:'-16px -18px'}}>
        <table style={{width:'100%',borderCollapse:'collapse',fontSize:12}}>
          <thead>
            <tr style={{borderBottom:'1px solid var(--ap-line)'}}>
              {['时间','交易对','方向','类型','数量','价格','状态'].map(h=>(
                <th key={h} style={{padding:'10px 12px',textAlign:'left',fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.06em',textTransform:'uppercase',fontWeight:500}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {W_MOCK.orders.map((o,i)=>(
              <tr key={i} style={{borderBottom:'1px solid var(--ap-line-soft)'}}>
                <td style={{padding:'10px 12px',fontFamily:'var(--ap-font-mono)',color:'var(--ap-fg-3)'}}>{o.t}</td>
                <td style={{padding:'10px 12px',fontFamily:'var(--ap-font-mono)',fontWeight:600}}>{o.sym}</td>
                <td style={{padding:'10px 12px'}}><WPill tone={o.side==='BUY'?'mint':'rose'}>{o.side}</WPill></td>
                <td style={{padding:'10px 12px',fontFamily:'var(--ap-font-mono)',fontSize:11,color:'var(--ap-fg-2)'}}>{o.type}</td>
                <td style={{padding:'10px 12px',fontFamily:'var(--ap-font-mono)'}}>{o.qty}</td>
                <td style={{padding:'10px 12px',fontFamily:'var(--ap-font-mono)'}}>{wfmt(o.price)}</td>
                <td style={{padding:'10px 12px'}}><WPill tone={o.status==='FILLED'?'mint':o.status==='WORKING'?'cyan':'default'}>{o.status}</WPill></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </WCard>
  </div>
);

// =========================================================
// Backtest / performance
// =========================================================
const WBacktestPage = () => (
  <div style={{display:'flex',flexDirection:'column',gap:20}}>
    <div style={{display:'grid',gridTemplateColumns:'repeat(6,1fr)',gap:12}}>
      <WCard dense><WStat label="净收益" value="+24.8%" tone="pos" sub="vs +9.2% HODL"/></WCard>
      <WCard dense><WStat label="Sharpe" value="1.84" sub="risk-adjusted"/></WCard>
      <WCard dense><WStat label="Sortino" value="2.47" sub="下行风险"/></WCard>
      <WCard dense><WStat label="最大回撤" value="−4.23%" tone="neg"/></WCard>
      <WCard dense><WStat label="胜率" value="57%" sub="142/248"/></WCard>
      <WCard dense><WStat label="盈亏比" value="2.3:1" sub="avg R:R"/></WCard>
    </div>

    <WCard title="策略收益对比 (90 天)" right={
      <div style={{display:'flex',gap:12,fontSize:11,fontFamily:'var(--ap-font-mono)'}}>
        <span><WDot c="var(--ap-mint)" glow/> <span style={{marginLeft:6}}>AlphaPilot</span></span>
        <span><WDot c="var(--ap-fg-4)"/> <span style={{marginLeft:6,color:'var(--ap-fg-3)'}}>BTC HODL</span></span>
        <span><WDot c="var(--ap-violet)"/> <span style={{marginLeft:6,color:'var(--ap-fg-3)'}}>ETH HODL</span></span>
      </div>
    }>
      <div style={{margin:'0 -18px -16px',position:'relative'}}>
        <svg width="100%" height="240" viewBox="0 0 1000 240" preserveAspectRatio="none" style={{display:'block'}}>
          <defs>
            <linearGradient id="bt-mint" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="var(--ap-mint)" stopOpacity=".3"/><stop offset="1" stopColor="var(--ap-mint)" stopOpacity="0"/></linearGradient>
          </defs>
          {/* grid */}
          {[0,1,2,3,4].map(i=>(<line key={i} x1="0" x2="1000" y1={i*60} y2={i*60} stroke="var(--ap-line)" strokeOpacity=".4"/>))}
          {/* strategy */}
          <path d="M 0 200 C 100 195, 200 180, 300 160 S 500 130, 600 100 S 800 70, 1000 40" stroke="var(--ap-mint)" strokeWidth="2" fill="none"/>
          <path d="M 0 200 C 100 195, 200 180, 300 160 S 500 130, 600 100 S 800 70, 1000 40 L 1000 240 L 0 240 Z" fill="url(#bt-mint)"/>
          {/* BTC */}
          <path d="M 0 200 C 100 210, 200 205, 300 190 S 500 180, 600 170 S 800 160, 1000 140" stroke="var(--ap-fg-4)" strokeWidth="1.5" fill="none" strokeDasharray="4,3"/>
          {/* ETH */}
          <path d="M 0 200 C 100 215, 200 220, 300 210 S 500 215, 600 195 S 800 175, 1000 165" stroke="var(--ap-violet)" strokeWidth="1.5" fill="none" strokeDasharray="4,3"/>
        </svg>
      </div>
    </WCard>

    <div style={{display:'grid',gridTemplateColumns:'2fr 1fr',gap:20}}>
      <WCard title="月度 PnL 分布">
        <div style={{display:'flex',alignItems:'flex-end',gap:8,height:160,padding:'10px 0'}}>
          {[3.2,-1.4,5.1,2.8,-0.9,4.7,6.1,-2.3,3.8,1.9,4.2,2.5].map((v,i)=>(
            <div key={i} style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',gap:4}}>
              <div style={{fontSize:10,fontFamily:'var(--ap-font-mono)',color: v>=0?'var(--ap-mint)':'var(--ap-rose)'}}>{v>=0?'+':''}{v.toFixed(1)}</div>
              <div style={{width:'100%',height:Math.abs(v)*16+4,background: v>=0?'var(--ap-mint)':'var(--ap-rose)',borderRadius:'3px 3px 0 0',opacity:.85}}/>
              <div style={{fontSize:9,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)'}}>{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][i]}</div>
            </div>
          ))}
        </div>
      </WCard>

      <WCard title="交易统计">
        {[
          ['总交易数', '248'],
          ['盈利笔数', '142'],
          ['亏损笔数', '106'],
          ['平均盈利', '+$124.80'],
          ['平均亏损', '−$54.30'],
          ['最大连续盈利', '8 笔'],
          ['最大连续亏损', '3 笔'],
          ['平均持仓', '2h 14m'],
        ].map(([l,v],i)=>(
          <div key={i} style={{display:'flex',justifyContent:'space-between',padding:'8px 0',borderBottom: i<7?'1px solid var(--ap-line-soft)':'none',fontSize:12}}>
            <span style={{color:'var(--ap-fg-3)'}}>{l}</span>
            <span style={{fontFamily:'var(--ap-font-mono)',fontWeight:600,color:'var(--ap-fg-1)'}}>{v}</span>
          </div>
        ))}
      </WCard>
    </div>
  </div>
);

// =========================================================
// Strategy & Risk config
// =========================================================
const WRiskPage = () => (
  <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:20}}>
    <WCard title="策略框架 · 受限集">
      <div style={{display:'flex',flexDirection:'column',gap:12}}>
        {[
          {name:'趋势跟随', desc:'EMA 20/50/200 排列 + ATR 确认', active:true, regimes:['trending_up','trending_down']},
          {name:'突破确认', desc:'阻力位突破 + 成交量 1.4x+', active:false, regimes:['trending_up','ranging']},
          {name:'观望模式', desc:'chaotic regime 自动降级', active:false, regimes:['chaotic']},
        ].map((s,i)=>(
          <div key={i} style={{padding:14,background:'var(--ap-bg-3)',borderRadius:10,border:'1px solid '+(s.active?'var(--ap-mint)':'var(--ap-line-soft)')}}>
            <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:6}}>
              <WDot c={s.active?'var(--ap-mint)':'var(--ap-fg-4)'} glow={s.active}/>
              <span style={{fontSize:13,fontWeight:600}}>{s.name}</span>
              {s.active && <WPill tone="mint">ACTIVE</WPill>}
              <div style={{marginLeft:'auto',width:36,height:20,borderRadius:999,background:s.active?'var(--ap-mint)':'var(--ap-bg-4)',position:'relative',cursor:'pointer'}}>
                <div style={{position:'absolute',top:2,left:s.active?18:2,width:16,height:16,background:'#fff',borderRadius:'50%'}}/>
              </div>
            </div>
            <div style={{fontSize:12,color:'var(--ap-fg-3)',marginBottom:8}}>{s.desc}</div>
            <div style={{display:'flex',gap:6}}>
              {s.regimes.map(r=><WPill key={r} tone="default">{r}</WPill>)}
            </div>
          </div>
        ))}
      </div>
    </WCard>

    <WCard title="硬风控 · 不可 AI 学习">
      <div style={{padding:'8px 12px',background:'var(--ap-amber-soft)',borderRadius:8,marginBottom:14,display:'flex',gap:8,alignItems:'flex-start',border:'1px solid rgba(240,185,11,.2)'}}>
        <Icon name="alert" size={14} color="var(--ap-amber)"/>
        <span style={{fontSize:11,color:'var(--ap-fg-2)',lineHeight:1.5}}>硬风控阈值为系统级保护，AI 不可绕过或自我修改，所有决策必须通过守卫检查。</span>
      </div>
      {[
        {l:'单笔最大风险', v:'1.00%', max:'2.00%'},
        {l:'最大单币持仓', v:'15%', max:'25%'},
        {l:'日亏损熔断', v:'−2.00%', max:'−5.00%', tone:'neg'},
        {l:'周亏损熔断', v:'−5.00%', max:'−10.00%', tone:'neg'},
        {l:'连续亏损熔断', v:'3 笔', max:'5 笔'},
        {l:'最大相关度', v:'0.85', max:'1.00'},
        {l:'最小 R:R 比', v:'1.5', max:'1.0'},
        {l:'价差上限', v:'5bps', max:'10bps'},
      ].map((r,i,a)=>(
        <div key={i} style={{padding:'10px 0',borderBottom: i<a.length-1?'1px solid var(--ap-line-soft)':'none',display:'flex',alignItems:'center'}}>
          <span style={{flex:1,fontSize:13,color:'var(--ap-fg-2)'}}>{r.l}</span>
          <span style={{fontFamily:'var(--ap-font-mono)',fontSize:13,fontWeight:600,color:r.tone==='neg'?'var(--ap-rose)':'var(--ap-fg-1)',marginRight:8}}>{r.v}</span>
          <span style={{fontFamily:'var(--ap-font-mono)',fontSize:10,color:'var(--ap-fg-4)'}}>max {r.max}</span>
        </div>
      ))}
    </WCard>

    <WCard title="交易对" style={{gridColumn:'1 / 3'}}>
      <div style={{display:'flex',flexWrap:'wrap',gap:10}}>
        {[
          {s:'BTCUSDT',tf:'15m',active:true},
          {s:'ETHUSDT',tf:'15m',active:true},
          {s:'SOLUSDT',tf:'15m',active:false},
          {s:'BNBUSDT',tf:'15m',active:false},
        ].map((p,i)=>(
          <div key={i} style={{padding:'10px 14px',background:'var(--ap-bg-3)',borderRadius:10,border:'1px solid '+(p.active?'var(--ap-mint)':'var(--ap-line-soft)'),display:'flex',alignItems:'center',gap:10,minWidth:160}}>
            <div style={{width:28,height:28,borderRadius:'50%',background:'linear-gradient(135deg,#F7931A,#8B4E0D)',display:'flex',alignItems:'center',justifyContent:'center',color:'#fff',fontWeight:700,fontSize:12}}>{p.s[0]}</div>
            <div style={{flex:1}}>
              <div style={{fontFamily:'var(--ap-font-mono)',fontSize:12,fontWeight:600}}>{p.s}</div>
              <div style={{fontFamily:'var(--ap-font-mono)',fontSize:10,color:'var(--ap-fg-3)'}}>tf {p.tf}</div>
            </div>
            <WPill tone={p.active?'mint':'default'}>{p.active?'ON':'OFF'}</WPill>
          </div>
        ))}
        <div style={{padding:'10px 14px',background:'transparent',borderRadius:10,border:'1.5px dashed var(--ap-line)',display:'flex',alignItems:'center',gap:8,cursor:'pointer',color:'var(--ap-fg-3)',fontSize:12}}>+ 添加交易对</div>
      </div>
    </WCard>
  </div>
);

// =========================================================
// Audit log
// =========================================================
const WAuditPage = () => (
  <div style={{display:'flex',flexDirection:'column',gap:16,maxWidth:1100}}>
    <WCard title="审计日志 · 今日" right={
      <div style={{display:'flex',gap:6}}>
        {['全部','AI','守卫','成交','熔断'].map((t,i)=>(
          <span key={t} style={{padding:'4px 10px',fontSize:11,background:i===0?'var(--ap-bg-4)':'var(--ap-bg-3)',border:'1px solid var(--ap-line-soft)',borderRadius:6,cursor:'pointer',color:i===0?'var(--ap-fg-1)':'var(--ap-fg-3)'}}>{t}</span>
        ))}
      </div>
    }>
      <div style={{display:'flex',flexDirection:'column',gap:0}}>
        {W_MOCK.events.map((e,i)=><WEventRow key={i} e={e}/>)}
      </div>
    </WCard>

    <WCard title="AI 日报">
      <div style={{fontSize:14,color:'var(--ap-fg-2)',lineHeight:1.7}}>
        本日 <b style={{color:'var(--ap-fg-1)'}}>7 笔</b>交易 · 胜率 <b style={{color:'var(--ap-mint)',fontFamily:'var(--ap-font-mono)'}}>57%</b> · 净收益 <b style={{color:'var(--ap-mint)',fontFamily:'var(--ap-font-mono)'}}>+1.82%</b>。
        BTCUSDT 主导盈利贡献（<span style={{color:'var(--ap-mint)',fontFamily:'var(--ap-font-mono)'}}>+$1,890</span>），ETHUSDT 受 chaotic regime 拖累（<span style={{color:'var(--ap-rose)',fontFamily:'var(--ap-font-mono)'}}>−$642</span>）。
        守卫共拦截 <b style={{color:'var(--ap-amber)',fontFamily:'var(--ap-font-mono)'}}>2 次</b>，均因 RR &lt; 1.5。引擎延迟 <span style={{fontFamily:'var(--ap-font-mono)'}}>p50 42ms / p99 118ms</span>，健康。
      </div>
    </WCard>
  </div>
);

Object.assign(window, { WDashboard, WAIPage, WPositionsPage, WBacktestPage, WRiskPage, WAuditPage });
