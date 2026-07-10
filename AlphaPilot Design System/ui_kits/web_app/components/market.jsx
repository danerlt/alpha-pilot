// Market / 行情 page — watchlist · candlestick chart · order book · trades · stats
// Self-contained; uses atoms from shell.jsx

// ---------- deterministic data gen ----------
function seededRand(seed){ let s=seed; return ()=>{ s=(s*1103515245+12345)&0x7fffffff; return s/0x7fffffff; }; }

function genCandles(n, start, vol, seed){
  const rnd = seededRand(seed); const out=[]; let p=start;
  for(let i=0;i<n;i++){
    const drift=(rnd()-0.46)*vol;
    const o=p, c=o+drift+(rnd()-0.5)*vol*0.6;
    const hi=Math.max(o,c)+rnd()*vol*0.5, lo=Math.min(o,c)-rnd()*vol*0.5;
    out.push({o,c,hi,lo,v:0.3+rnd()*0.7}); p=c;
  }
  return out;
}

const MARKET = {
  BTCUSDT: {price:68863.92, chg:2.14, base:67000, vol:260, seed:7, high:69240, low:66980, vol24:'2.84B', funding:0.0089, oi:'$8.2B', held:true, sl:64210, tp:68900, entry:67420.5},
  ETHUSDT: {price:3219.92, chg:-0.62, base:3260, vol:18, seed:13, high:3288, low:3201, vol24:'1.42B', funding:0.0051, oi:'$4.1B', held:true, sl:3120, tp:3380, entry:3240},
  SOLUSDT: {price:151.42, chg:1.08, base:149, vol:1.4, seed:21, high:153.8, low:148.2, vol24:'612M', funding:0.0123, oi:'$1.1B', held:false},
  BNBUSDT: {price:604.30, chg:0.42, base:600, vol:3.2, seed:29, high:611, low:598, vol24:'287M', funding:0.0067, oi:'$820M', held:false},
};
const REGIME_OF = {BTCUSDT:'trending_up', ETHUSDT:'ranging', SOLUSDT:'trending_up', BNBUSDT:'ranging'};

// ---------- interactive candlestick chart ----------
const MarketChart = ({sym, tf}) => {
  const m = MARKET[sym];
  const n = 64;
  const candles = React.useMemo(()=>genCandles(n, m.base, m.vol, m.seed + tf.length*7), [sym, tf]);
  const wrapRef = React.useRef(null);
  const [w, setW] = React.useState(760);
  const [hover, setHover] = React.useState(null);
  const h = 380, pad = 16, volH = 56, chartH = h - volH - 24;

  React.useEffect(()=>{
    const ro = new ResizeObserver(es=>{ for(const e of es) setW(e.contentRect.width); });
    if(wrapRef.current) ro.observe(wrapRef.current);
    return ()=>ro.disconnect();
  },[]);

  const allP = candles.flatMap(c=>[c.hi,c.lo]);
  const min=Math.min(...allP), max=Math.max(...allP), r=(max-min)||1;
  const y = p => pad + (1-(p-min)/r)*(chartH-pad);
  // clamp far-away levels (e.g. deep SL) to chart edge instead of squashing candles
  const yLvl = p => Math.max(pad+6, Math.min(chartH-6, y(p)));
  const cw = (w-pad*2)/candles.length;
  const cx = i => pad + i*cw + cw/2;

  const onMove = e => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX-rect.left;
    const i = Math.max(0,Math.min(candles.length-1, Math.floor((x-pad)/cw)));
    setHover({i, c:candles[i], x:cx(i)});
  };

  const levels = m.held ? [
    {p:m.tp, c:'var(--ap-mint)', l:'TP '+wfmt(m.tp,0)},
    {p:m.entry, c:'var(--ap-fg-3)', l:'入场 '+wfmt(m.entry,0), dash:true},
    {p:m.sl, c:'var(--ap-rose)', l:'SL '+wfmt(m.sl,0)},
  ] : [];

  return (
    <div ref={wrapRef} style={{position:'relative',width:'100%'}}>
      <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} style={{display:'block'}} onMouseMove={onMove} onMouseLeave={()=>setHover(null)}>
        {/* grid */}
        {[0,0.25,0.5,0.75,1].map((t,i)=>(<line key={i} x1={pad} x2={w-pad} y1={pad+t*(chartH-pad)} y2={pad+t*(chartH-pad)} stroke="var(--ap-line-soft)"/>))}
        {/* price axis labels */}
        {[0,0.5,1].map((t,i)=>(<text key={i} x={w-pad} y={pad+t*(chartH-pad)+ (i===0?10:i===2?-2:4)} textAnchor="end" fontSize="9.5" fill="var(--ap-fg-4)" fontFamily="var(--ap-font-mono)">{wfmt(max-t*r,0)}</text>))}
        {/* held levels */}
        {levels.map((lv,i)=>{
          const clamped = y(lv.p)!==yLvl(lv.p);
          const lw = clamped?64:52;
          return (
          <g key={i}>
            <line x1={pad} x2={w-pad-lw} y1={yLvl(lv.p)} y2={yLvl(lv.p)} stroke={lv.c} strokeWidth="1" strokeDasharray={lv.dash||clamped?'3 3':'5 0'} opacity={clamped?0.5:0.75}/>
            <rect x={w-pad-lw} y={yLvl(lv.p)-8} width={lw} height={16} rx={3} fill={lv.c} opacity=".18"/>
            <text x={w-pad-4} y={yLvl(lv.p)+4} textAnchor="end" fontSize="9" fill={lv.c} fontFamily="var(--ap-font-mono)" fontWeight="600">{lv.l}{clamped?' ↓':''}</text>
          </g>
        );})}
        {/* candles */}
        {candles.map((c,i)=>{
          const up=c.c>=c.o, col=up?'var(--ap-mint)':'var(--ap-rose)';
          const bw=Math.max(1.5,cw*0.62);
          return (
            <g key={i}>
              <line x1={cx(i)} x2={cx(i)} y1={y(c.hi)} y2={y(c.lo)} stroke={col} strokeWidth="1"/>
              <rect x={cx(i)-bw/2} y={y(Math.max(c.o,c.c))} width={bw} height={Math.max(1,Math.abs(y(c.o)-y(c.c)))} fill={col} opacity={up?0.95:0.9}/>
            </g>
          );
        })}
        {/* current price line */}
        <line x1={pad} x2={w-pad-52} y1={y(m.price)} y2={y(m.price)} stroke="var(--ap-cyan)" strokeWidth="1" strokeDasharray="1 3"/>
        <rect x={w-pad-52} y={y(m.price)-8} width={52} height={16} rx={3} fill="var(--ap-cyan)"/>
        <text x={w-pad-4} y={y(m.price)+4} textAnchor="end" fontSize="9.5" fill="var(--ap-bg-0)" fontFamily="var(--ap-font-mono)" fontWeight="700">{wfmt(m.price,0)}</text>
        {/* volume */}
        <g transform={`translate(0,${h-volH})`}>
          {candles.map((c,i)=>{const up=c.c>=c.o,bw=Math.max(1.5,cw*0.62);return <rect key={i} x={cx(i)-bw/2} y={volH-c.v*(volH-8)} width={bw} height={c.v*(volH-8)} fill={up?'var(--ap-mint)':'var(--ap-rose)'} opacity=".35"/>;})}
        </g>
        {/* crosshair */}
        {hover && (<>
          <line x1={hover.x} x2={hover.x} y1={pad} y2={chartH} stroke="var(--ap-fg-3)" strokeWidth="1" strokeDasharray="3 3"/>
          <circle cx={hover.x} cy={y(hover.c.c)} r="3.5" fill="var(--ap-cyan)" stroke="var(--ap-bg-1)" strokeWidth="2"/>
        </>)}
      </svg>
      {hover && (
        <div style={{position:'absolute',top:8,left:Math.max(8,Math.min(hover.x/w*100,72))+'%',transform:'translateX(-50%)',background:'var(--ap-bg-4)',border:'1px solid var(--ap-line)',borderRadius:8,padding:'7px 11px',pointerEvents:'none',boxShadow:'var(--ap-shadow-2)',whiteSpace:'nowrap',zIndex:2,fontFamily:'var(--ap-font-mono)',fontSize:11}}>
          <div style={{display:'flex',gap:12}}>
            <span style={{color:'var(--ap-fg-3)'}}>O</span><span>{wfmt(hover.c.o,0)}</span>
            <span style={{color:'var(--ap-fg-3)'}}>H</span><span style={{color:'var(--ap-mint)'}}>{wfmt(hover.c.hi,0)}</span>
          </div>
          <div style={{display:'flex',gap:12,marginTop:2}}>
            <span style={{color:'var(--ap-fg-3)'}}>C</span><span style={{color:hover.c.c>=hover.c.o?'var(--ap-mint)':'var(--ap-rose)'}}>{wfmt(hover.c.c,0)}</span>
            <span style={{color:'var(--ap-fg-3)'}}>L</span><span style={{color:'var(--ap-rose)'}}>{wfmt(hover.c.lo,0)}</span>
          </div>
        </div>
      )}
    </div>
  );
};

// ---------- order book ----------
const OrderBook = ({sym}) => {
  const m = MARKET[sym];
  const rnd = seededRand(m.seed*3);
  const step = m.price*0.0004;
  const asks = Array.from({length:8},(_,i)=>({p:m.price+step*(8-i), sz:(rnd()*4+0.2)}));
  const bids = Array.from({length:8},(_,i)=>({p:m.price-step*(i+1), sz:(rnd()*4+0.2)}));
  const maxSz = Math.max(...asks.map(a=>a.sz),...bids.map(b=>b.sz));
  const Row = ({r, side}) => (
    <div style={{position:'relative',display:'flex',justifyContent:'space-between',padding:'3px 10px',fontFamily:'var(--ap-font-mono)',fontSize:11}}>
      <div style={{position:'absolute',right:0,top:0,bottom:0,width:(r.sz/maxSz*100)+'%',background:side==='ask'?'var(--ap-rose-soft)':'var(--ap-mint-soft)'}}/>
      <span style={{position:'relative',color:side==='ask'?'var(--ap-rose)':'var(--ap-mint)'}}>{wfmt(r.p, m.price>1000?1:2)}</span>
      <span style={{position:'relative',color:'var(--ap-fg-3)'}}>{r.sz.toFixed(3)}</span>
    </div>
  );
  return (
    <div>
      <div style={{display:'flex',justifyContent:'space-between',padding:'0 10px 6px',fontSize:9.5,color:'var(--ap-fg-4)',letterSpacing:'.06em',textTransform:'uppercase'}}><span>价格</span><span>数量</span></div>
      {asks.map((a,i)=><Row key={i} r={a} side="ask"/>)}
      <div style={{padding:'7px 10px',fontFamily:'var(--ap-font-mono)',fontSize:14,fontWeight:700,color: m.chg>=0?'var(--ap-mint)':'var(--ap-rose)',display:'flex',alignItems:'center',gap:8,borderTop:'1px solid var(--ap-line-soft)',borderBottom:'1px solid var(--ap-line-soft)',margin:'3px 0'}}>
        {wfmt(m.price, m.price>1000?1:2)} <Icon name={m.chg>=0?'arrow_up':'arrow_down'} size={13} color={m.chg>=0?'var(--ap-mint)':'var(--ap-rose)'}/>
      </div>
      {bids.map((b,i)=><Row key={i} r={b} side="bid"/>)}
    </div>
  );
};

// ---------- recent trades ----------
const RecentTrades = ({sym}) => {
  const m = MARKET[sym]; const rnd = seededRand(m.seed*5);
  const trades = Array.from({length:14},(_,i)=>{
    const buy=rnd()>0.45; const step=m.price*0.0003;
    return {p:m.price+(rnd()-0.5)*step*6, sz:(rnd()*2+0.05), buy, t:`14:2${(3-Math.floor(i/5))}:${(59-i*3).toString().padStart(2,'0')}`};
  });
  return (
    <div>
      <div style={{display:'flex',justifyContent:'space-between',padding:'0 10px 6px',fontSize:9.5,color:'var(--ap-fg-4)',letterSpacing:'.06em',textTransform:'uppercase'}}><span>价格</span><span>数量</span><span>时间</span></div>
      {trades.map((t,i)=>(
        <div key={i} style={{display:'flex',justifyContent:'space-between',padding:'3px 10px',fontFamily:'var(--ap-font-mono)',fontSize:11}}>
          <span style={{color:t.buy?'var(--ap-mint)':'var(--ap-rose)'}}>{wfmt(t.p, m.price>1000?1:2)}</span>
          <span style={{color:'var(--ap-fg-2)'}}>{t.sz.toFixed(3)}</span>
          <span style={{color:'var(--ap-fg-4)'}}>{t.t}</span>
        </div>
      ))}
    </div>
  );
};

// ---------- main page ----------
const WMarketPage = () => {
  const [sym, setSym] = React.useState('BTCUSDT');
  const [tf, setTf] = React.useState('15m');
  const [obTab, setObTab] = React.useState('book');
  const m = MARKET[sym];
  const regime = REGIME_OF[sym];
  const regimeTone = regime==='trending_up'?'mint':regime==='trending_down'?'rose':regime==='chaotic'?'amber':'cyan';

  return (
    <div style={{display:'grid',gridTemplateColumns:'220px minmax(0,1fr) 260px',gap:16,height:'100%'}}>
      {/* watchlist */}
      <WCard title="自选" style={{height:'fit-content'}} right={<Icon name="search" size={13} color="var(--ap-fg-4)"/>}>
        <div style={{margin:'-16px -18px'}}>
          {Object.keys(MARKET).map(s=>{
            const d=MARKET[s]; const up=d.chg>=0; const sel=s===sym;
            return (
              <div key={s} onClick={()=>setSym(s)} style={{display:'flex',alignItems:'center',gap:10,padding:'11px 14px',cursor:'pointer',borderLeft:'2px solid '+(sel?'var(--ap-mint)':'transparent'),background:sel?'var(--ap-bg-3)':'transparent',borderBottom:'1px solid var(--ap-line-soft)'}}>
                <div style={{flex:1,minWidth:0}}>
                  <div style={{display:'flex',alignItems:'center',gap:6}}>
                    <span style={{fontFamily:'var(--ap-font-mono)',fontSize:12.5,fontWeight:600}}>{s.replace('USDT','')}</span>
                    {d.held && <span title="持仓中" style={{width:5,height:5,borderRadius:'50%',background:'var(--ap-violet)',boxShadow:'0 0 5px var(--ap-violet)'}}/>}
                  </div>
                  <div style={{fontFamily:'var(--ap-font-mono)',fontSize:10,color:'var(--ap-fg-4)'}}>USDT 永续</div>
                </div>
                <div style={{textAlign:'right'}}>
                  <div style={{fontFamily:'var(--ap-font-mono)',fontSize:12,fontWeight:600}}>{wfmt(d.price, d.price>1000?0:2)}</div>
                  <div style={{fontFamily:'var(--ap-font-mono)',fontSize:10.5,color:up?'var(--ap-mint)':'var(--ap-rose)'}}>{up?'▲':'▼'} {Math.abs(d.chg).toFixed(2)}%</div>
                </div>
              </div>
            );
          })}
        </div>
      </WCard>

      {/* center: header + chart + AI strip */}
      <div style={{display:'flex',flexDirection:'column',gap:16,minWidth:0}}>
        <WCard>
          {/* symbol header */}
          <div style={{display:'flex',alignItems:'center',gap:16,marginBottom:14,flexWrap:'wrap'}}>
            <div style={{display:'flex',alignItems:'center',gap:10}}>
              <div style={{width:32,height:32,borderRadius:'50%',background:sym.startsWith('BTC')?'linear-gradient(135deg,#F7931A,#8B4E0D)':sym.startsWith('ETH')?'linear-gradient(135deg,#627EEA,#3C54BD)':'linear-gradient(135deg,#9945FF,#14F195)',display:'flex',alignItems:'center',justifyContent:'center',color:'#fff',fontWeight:700}}>{sym[0]}</div>
              <div>
                <div style={{fontSize:16,fontWeight:700,fontFamily:'var(--ap-font-mono)'}}>{sym}</div>
                <div style={{fontSize:10.5,color:'var(--ap-fg-3)'}}>永续合约 · Binance</div>
              </div>
            </div>
            <div style={{display:'flex',alignItems:'baseline',gap:10}}>
              <AnimatedNumber value={m.price} prefix="$" format={v=>wfmt(v, m.price>1000?2:3)} style={{fontSize:26,fontWeight:700,color:'var(--ap-fg-1)'}}/>
              <span style={{fontFamily:'var(--ap-font-mono)',fontSize:14,fontWeight:600,color:m.chg>=0?'var(--ap-mint)':'var(--ap-rose)'}}>{m.chg>=0?'+':''}{m.chg.toFixed(2)}%</span>
            </div>
            <div style={{marginLeft:'auto',display:'flex',gap:18}}>
              {[['24h 高',wfmt(m.high,0)],['24h 低',wfmt(m.low,0)],['24h 量',m.vol24]].map(([l,v],i)=>(
                <div key={i}><div style={{fontSize:9.5,color:'var(--ap-fg-4)',letterSpacing:'.06em',textTransform:'uppercase'}}>{l}</div><div style={{fontFamily:'var(--ap-font-mono)',fontSize:12,fontWeight:600}}>{v}</div></div>
              ))}
            </div>
          </div>
          {/* tf selector */}
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:8,flexWrap:'wrap',rowGap:6}}>
            <div style={{display:'inline-flex',background:'var(--ap-bg-3)',borderRadius:8,padding:3,border:'1px solid var(--ap-line)'}}>
              {['1m','5m','15m','1h','4h','1d'].map(t=>(
                <div key={t} onClick={()=>setTf(t)} style={{fontSize:11,padding:'5px 11px',borderRadius:5,fontFamily:'var(--ap-font-mono)',cursor:'pointer',background:tf===t?'var(--ap-bg-4)':'transparent',color:tf===t?'var(--ap-fg-1)':'var(--ap-fg-3)',fontWeight:500}}>{t}</div>
              ))}
            </div>
            <WPill tone={regimeTone}>AI regime · {regime}</WPill>
            {m.held && <WPill tone="violet">持仓中</WPill>}
            <span style={{marginLeft:'auto',fontSize:10.5,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)',whiteSpace:'nowrap'}}>含 SL/TP 标线</span>
          </div>
          {/* chart */}
          <div style={{margin:'0 -18px -16px'}}><MarketChart sym={sym} tf={tf}/></div>
        </WCard>

        {/* AI read strip */}
        <WCard>
          <div style={{display:'flex',alignItems:'flex-start',gap:12}}>
            <div style={{width:32,height:32,borderRadius:8,background:'var(--ap-violet-soft)',display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0}}><Icon name="brain" size={16} color="var(--ap-violet)"/></div>
            <div style={{flex:1}}>
              <div style={{fontSize:10.5,color:'var(--ap-violet)',letterSpacing:'.08em',fontWeight:700,marginBottom:4}}>AI 市场解读 · {sym}</div>
              <div style={{fontSize:13,color:'var(--ap-fg-2)',lineHeight:1.6}}>
                {regime==='trending_up'
                  ? <>当前判定 <b style={{color:'var(--ap-mint)'}}>trending_up</b>：EMA 多头排列，{tf} 级别量能温和放大。{m.held?'持仓盈利中，止盈位上移空间充足。':'符合「趋势跟随」策略入场条件，等待回踩确认。'}</>
                  : <>当前判定 <b style={{color:'var(--ap-cyan)'}}>ranging</b>：价格在区间内震荡，方向性不足。AI 倾向 <b>观望</b>，仅在突破区间边界且放量时考虑入场。</>}
              </div>
              <div style={{display:'flex',gap:8,marginTop:10}}>
                <WPill tone="cyan">资金费率 {(m.funding).toFixed(4)}%</WPill>
                <WPill tone="default">持仓量 {m.oi}</WPill>
                <WPill tone="default">8h 倒计时 02:14:30</WPill>
              </div>
            </div>
          </div>
        </WCard>
      </div>

      {/* right: order ticket + order book / trades + stats */}
      <div style={{display:'flex',flexDirection:'column',gap:16,minWidth:0}}>
        <OrderTicket sym={sym}/>
        <WCard title={
          <div style={{display:'flex',gap:12}}>
            <span onClick={()=>setObTab('book')} style={{cursor:'pointer',color:obTab==='book'?'var(--ap-fg-1)':'var(--ap-fg-4)'}}>盘口</span>
            <span onClick={()=>setObTab('trades')} style={{cursor:'pointer',color:obTab==='trades'?'var(--ap-fg-1)':'var(--ap-fg-4)'}}>成交</span>
          </div>
        } style={{height:'fit-content'}}>
          <div style={{margin:'-16px -18px'}}>
            {obTab==='book' ? <OrderBook sym={sym}/> : <RecentTrades sym={sym}/>}
          </div>
        </WCard>

        <WCard title="合约信息" style={{height:'fit-content'}}>
          {[
            ['资金费率', (m.funding).toFixed(4)+'%', m.funding>=0?'pos':'neg'],
            ['下次结算', '02:14:30', ''],
            ['持仓量 OI', m.oi, ''],
            ['24h 成交额', m.vol24, ''],
            ['标记价格', wfmt(m.price, m.price>1000?1:3), ''],
            ['指数价格', wfmt(m.price*0.9998, m.price>1000?1:3), ''],
          ].map(([l,v,tone],i,a)=>(
            <div key={i} style={{display:'flex',justifyContent:'space-between',padding:'8px 0',borderBottom:i<a.length-1?'1px solid var(--ap-line-soft)':'none',fontSize:12}}>
              <span style={{color:'var(--ap-fg-3)'}}>{l}</span>
              <span style={{fontFamily:'var(--ap-font-mono)',fontWeight:600,color:tone==='pos'?'var(--ap-mint)':tone==='neg'?'var(--ap-rose)':'var(--ap-fg-1)'}}>{v}</span>
            </div>
          ))}
        </WCard>
      </div>
    </div>
  );
};

Object.assign(window, { WMarketPage, MARKET });
