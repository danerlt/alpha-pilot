// Order ticket — manual trading panel for the Market page
// Includes guard pre-check preview: manual orders also pass through hard risk checks.

const OrderTicket = ({sym}) => {
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

  React.useEffect(()=>{ setPrice(String(Math.round(m.price))); setSubmitted(false); }, [sym]);

  const notional = (parseFloat(qty)||0) * (type==='market'? m.price : (parseFloat(price)||0));
  const equity = W_MOCK.equity;
  const posPct = notional/equity*100;
  const rr = (()=>{
    const p = type==='market'? m.price : parseFloat(price), s=parseFloat(sl), t=parseFloat(tp);
    if(!p||!s||!t) return null;
    const risk = Math.abs(p-s), reward = Math.abs(t-p);
    return risk>0 ? reward/risk : null;
  })();

  // guard pre-checks (manual orders still guarded)
  const checks = [
    {k:'仓位上限', ok: posPct <= 15, note: posPct.toFixed(1)+'% / 15%'},
    {k:'止损设置', ok: reduceOnly || !!parseFloat(sl), note: parseFloat(sl)?'已设':'必填'},
    {k:'R:R ≥ 1.5', ok: reduceOnly || (rr!==null && rr>=1.5), note: rr?('1:'+rr.toFixed(1)):'—'},
    {k:'熔断状态', ok: W_MOCK.riskState!=='HALTED' || reduceOnly, note: W_MOCK.riskState==='HALTED'?(reduceOnly?'仅减仓':'已熔断'):'正常'},
  ];
  const allPass = checks.every(c=>c.ok);
  const buyC = side==='buy';

  const inputStyle = {width:'100%',boxSizing:'border-box',background:'var(--ap-bg-3)',border:'1px solid var(--ap-line)',borderRadius:8,padding:'8px 10px',color:'var(--ap-fg-1)',fontSize:12,fontFamily:'var(--ap-font-mono)',outline:'none'};
  const lbl = {fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.05em',marginBottom:4,display:'block'};

  return (
    <WCard title="手动下单" right={<WPill tone="amber">人工干预</WPill>} style={{height:'fit-content'}}>
      {/* side */}
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:6,marginBottom:10}}>
        {[['buy','买入 / 做多','var(--ap-mint)'],['sell','卖出 / 做空','var(--ap-rose)']].map(([v,l,c])=>(
          <div key={v} onClick={()=>setSide(v)} style={{padding:'9px 0',textAlign:'center',borderRadius:8,fontSize:12,fontWeight:700,cursor:'pointer',
            background: side===v?c:'var(--ap-bg-3)', color: side===v?'var(--ap-bg-0)':'var(--ap-fg-3)',border:'1px solid '+(side===v?c:'var(--ap-line)')}}>{l}</div>
        ))}
      </div>
      {/* type */}
      <div style={{display:'inline-flex',background:'var(--ap-bg-3)',borderRadius:8,padding:2,border:'1px solid var(--ap-line)',marginBottom:10}}>
        {[['limit','限价'],['market','市价'],['stop','止损单']].map(([v,l])=>(
          <div key={v} onClick={()=>setType(v)} style={{fontSize:11,padding:'5px 12px',borderRadius:6,cursor:'pointer',fontFamily:'var(--ap-font-mono)',
            background:type===v?'var(--ap-bg-4)':'transparent',color:type===v?'var(--ap-fg-1)':'var(--ap-fg-3)'}}>{l}</div>
        ))}
      </div>

      {type!=='market' && (
        <div style={{marginBottom:10}}>
          <span style={lbl}>价格 (USDT)</span>
          <input value={price} onChange={e=>setPrice(e.target.value)} style={inputStyle}/>
        </div>
      )}
      <div style={{marginBottom:10}}>
        <span style={lbl}>数量 ({sym.replace('USDT','')})</span>
        <input value={qty} onChange={e=>setQty(e.target.value)} style={inputStyle}/>
        <div style={{display:'flex',gap:4,marginTop:6}}>
          {[10,25,50,75,100].map(p=>(
            <div key={p} onClick={()=>{setPct(p); setQty((equity*p/100/m.price*0.1).toFixed(3));}}
              style={{flex:1,textAlign:'center',padding:'4px 0',fontSize:10,borderRadius:5,cursor:'pointer',fontFamily:'var(--ap-font-mono)',
              background:pct===p?'var(--ap-bg-4)':'var(--ap-bg-3)',color:pct===p?'var(--ap-fg-1)':'var(--ap-fg-4)',border:'1px solid var(--ap-line-soft)'}}>{p}%</div>
          ))}
        </div>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:8,marginBottom:10}}>
        <div><span style={lbl}>止损 SL</span><input value={sl} onChange={e=>setSl(e.target.value)} placeholder="必填" style={{...inputStyle,borderColor: sl?'var(--ap-line)':'rgba(255,77,109,.4)'}}/></div>
        <div><span style={lbl}>止盈 TP</span><input value={tp} onChange={e=>setTp(e.target.value)} placeholder="可选" style={inputStyle}/></div>
      </div>

      <div onClick={()=>setReduceOnly(!reduceOnly)} style={{display:'flex',alignItems:'center',gap:8,marginBottom:12,cursor:'pointer'}}>
        <div style={{width:14,height:14,borderRadius:4,border:'1px solid '+(reduceOnly?'var(--ap-mint)':'var(--ap-line)'),background:reduceOnly?'var(--ap-mint)':'transparent',display:'flex',alignItems:'center',justifyContent:'center'}}>
          {reduceOnly && <Icon name="check" size={10} color="var(--ap-bg-0)" strokeWidth={3}/>}
        </div>
        <span style={{fontSize:11,color:'var(--ap-fg-2)'}}>只减仓 Reduce-Only</span>
      </div>

      {/* summary */}
      <div style={{background:'var(--ap-bg-3)',borderRadius:8,padding:'8px 10px',marginBottom:10,fontFamily:'var(--ap-font-mono)',fontSize:10.5,display:'flex',flexDirection:'column',gap:4}}>
        <div style={{display:'flex',justifyContent:'space-between'}}><span style={{color:'var(--ap-fg-4)'}}>名义价值</span><span>${wfmt(notional)}</span></div>
        <div style={{display:'flex',justifyContent:'space-between'}}><span style={{color:'var(--ap-fg-4)'}}>占用仓位</span><span style={{color:posPct>15?'var(--ap-rose)':'var(--ap-fg-1)'}}>{posPct.toFixed(2)}%</span></div>
        {rr!==null && <div style={{display:'flex',justifyContent:'space-between'}}><span style={{color:'var(--ap-fg-4)'}}>盈亏比</span><span style={{color:rr>=1.5?'var(--ap-mint)':'var(--ap-rose)'}}>1:{rr.toFixed(2)}</span></div>}
      </div>

      {/* guard pre-check */}
      <div style={{marginBottom:12}}>
        <div style={{fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.06em',fontWeight:600,marginBottom:6,display:'flex',alignItems:'center',gap:6}}>
          <Icon name="shield" size={11} color="var(--ap-fg-3)"/> 守卫预检 · 人工单同样受硬风控约束
        </div>
        <div style={{display:'flex',flexDirection:'column',gap:3}}>
          {checks.map((c,i)=>(
            <div key={i} style={{display:'flex',alignItems:'center',gap:6,fontSize:10.5,fontFamily:'var(--ap-font-mono)'}}>
              <WDot c={c.ok?'var(--ap-mint)':'var(--ap-rose)'}/>
              <span style={{color:'var(--ap-fg-3)',flex:1}}>{c.k}</span>
              <span style={{color:c.ok?'var(--ap-fg-2)':'var(--ap-rose)'}}>{c.note}</span>
            </div>
          ))}
        </div>
      </div>

      <button onClick={()=>allPass&&setSubmitted(true)} disabled={!allPass}
        style={{width:'100%',padding:'11px 0',borderRadius:9,border:'none',fontSize:13,fontWeight:700,fontFamily:'inherit',cursor:allPass?'pointer':'not-allowed',
          background: submitted?'var(--ap-bg-4)':allPass?(buyC?'var(--ap-mint)':'var(--ap-rose)'):'var(--ap-bg-4)',
          color: submitted?'var(--ap-mint)':allPass?'var(--ap-bg-0)':'var(--ap-fg-4)'}}>
        {submitted?'✓ 已提交（模拟）': allPass?(buyC?'买入 '+sym.replace('USDT',''):'卖出 '+sym.replace('USDT','')):'守卫未通过'}
      </button>
      {W_MOCK.riskState==='HALTED' && !reduceOnly && (
        <div style={{marginTop:8,fontSize:10.5,color:'var(--ap-rose)',fontFamily:'var(--ap-font-mono)',textAlign:'center'}}>熔断中 · 仅允许 Reduce-Only</div>
      )}
    </WCard>
  );
};

Object.assign(window, { OrderTicket });
