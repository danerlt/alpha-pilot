// AlphaPilot Web — interaction & state enhancements
// HaltBanner · StreamingDecision · WSparkLive · CommandPalette · AnimatedNumber · EmptyState

// ============================================================
// AnimatedNumber — count-up + color flash on change
// ============================================================
const AnimatedNumber = ({ value, format=(v)=>v.toFixed(2), prefix='', suffix='', style={}, motion=true, duration=600 }) => {
  const [display, setDisplay] = React.useState(value);
  const [flash, setFlash] = React.useState(null); // 'up' | 'down'
  const prev = React.useRef(value);
  const raf = React.useRef(null);

  React.useEffect(()=>{
    if(prev.current === value) return;
    const from = prev.current, to = value, start = performance.now();
    setFlash(to>=from?'up':'down');
    if(!motion){ setDisplay(to); prev.current=to; const t=setTimeout(()=>setFlash(null),500); return ()=>clearTimeout(t); }
    const tick = (now)=>{
      const t = Math.min(1, (now-start)/duration);
      const eased = 1-Math.pow(1-t, 3);
      setDisplay(from + (to-from)*eased);
      if(t<1) raf.current = requestAnimationFrame(tick);
      else { prev.current = to; setTimeout(()=>setFlash(null), 400); }
    };
    raf.current = requestAnimationFrame(tick);
    return ()=>cancelAnimationFrame(raf.current);
  }, [value, motion, duration]);

  const flashColor = flash==='up'?'var(--ap-mint)':flash==='down'?'var(--ap-rose)':undefined;
  return (
    <span style={{fontFamily:'var(--ap-font-mono)',fontVariantNumeric:'tabular-nums',transition:'color .3s, transform .3s',color:flashColor||style.color,transform:flash&&motion?'scale(1.015)':'scale(1)',display:'inline-block',...style}}>
      {prefix}{format(display)}{suffix}
    </span>
  );
};

// ============================================================
// HaltBanner — global circuit-breaker / warning ribbon
// ============================================================
const HaltBanner = ({ riskState, regime, dayLossPct, onAck }) => {
  if(riskState==='OK') return null;
  const halted = riskState==='HALTED';
  const c = halted?'var(--ap-rose)':'var(--ap-amber)';
  const soft = halted?'var(--ap-rose-soft)':'var(--ap-amber-soft)';
  return (
    <div role="alert" style={{
      display:'flex',alignItems:'center',gap:14,padding:'14px 18px',borderRadius:12,
      background:soft,border:`1px solid ${c}`,marginBottom:20,position:'relative',overflow:'hidden',
      boxShadow: halted?'0 0 32px rgba(255,77,109,.18)':'none'
    }}>
      {halted && <div style={{position:'absolute',inset:0,background:`repeating-linear-gradient(45deg, transparent, transparent 12px, ${c}0a 12px, ${c}0a 24px)`,pointerEvents:'none'}}/>}
      <div style={{width:36,height:36,borderRadius:9,background:c,display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0,boxShadow:`0 0 16px ${c}66`}}>
        <Icon name={halted?'alert':'alert'} size={18} color="var(--ap-bg-0)" strokeWidth={2.4}/>
      </div>
      <div style={{flex:1,minWidth:0,position:'relative'}}>
        <div style={{fontSize:14,fontWeight:700,color:c,marginBottom:2}}>
          {halted ? '日亏损熔断已触发 · 新开仓已暂停' : '接近熔断阈值 · 风险升高'}
        </div>
        <div style={{fontSize:12,color:'var(--ap-fg-2)',fontFamily:'var(--ap-font-mono)'}}>
          {halted
            ? `日损 ${wfmtPct(dayLossPct)} ≥ 阈值 −2.00% · 仅允许平仓与风险管理 · regime ${regime}`
            : `日损 ${wfmtPct(dayLossPct)} · 距阈值 ${(Math.abs(-2.0-dayLossPct)).toFixed(2)}% · regime ${regime}`}
        </div>
      </div>
      <div style={{display:'flex',gap:8,position:'relative',flexShrink:0}}>
        {halted && <button style={{padding:'8px 14px',borderRadius:8,border:`1px solid ${c}`,background:'transparent',color:c,fontSize:12,fontWeight:600,cursor:'pointer',fontFamily:'inherit'}}>查看风控日志</button>}
        <button onClick={onAck} style={{padding:'8px 14px',borderRadius:8,border:'none',background:c,color:'var(--ap-bg-0)',fontSize:12,fontWeight:700,cursor:'pointer',fontFamily:'inherit'}}>{halted?'手动恢复':'我知道了'}</button>
      </div>
    </div>
  );
};

// ============================================================
// StreamingDecision — plays the decision pipeline live, then
// reveals the full card. Replayable.
// ============================================================
const STREAM_STAGES = [
  {k:'snapshot', label:'采集市场快照', detail:'regime · K线 · 特征因子', color:'var(--ap-cyan)', icon:'bolt', ms:700},
  {k:'reason',   label:'AI 推理中',    detail:'LLM + 规则引擎评估', color:'var(--ap-violet)', icon:'brain', ms:1100},
  {k:'guard',    label:'守卫检查',     detail:'8 项硬风控校验', color:'var(--ap-mint)', icon:'shield', ms:800},
  {k:'verdict',  label:'风险裁决',     detail:'允许 / 回退 HOLD', color:'var(--ap-mint)', icon:'check', ms:600},
  {k:'exec',     label:'执行下单',     detail:'Binance 市价 + SL/TP', color:'var(--ap-mint)', icon:'play', ms:700},
];

const StreamingDecision = ({ d, variant, motion=true, halted=false }) => {
  const [stage, setStage] = React.useState(motion ? -1 : 99);
  const [done, setDone] = React.useState(!motion);
  const timers = React.useRef([]);

  const play = React.useCallback(()=>{
    timers.current.forEach(clearTimeout); timers.current=[];
    setDone(false); setStage(0);
    let acc=0;
    STREAM_STAGES.forEach((s,i)=>{
      acc += s.ms;
      timers.current.push(setTimeout(()=>{
        if(i===STREAM_STAGES.length-1){ setStage(99); setDone(true); }
        else setStage(i+1);
      }, acc));
    });
  },[]);

  React.useEffect(()=>{
    if(motion){ play(); }
    else { setStage(99); setDone(true); }
    return ()=>timers.current.forEach(clearTimeout);
  // eslint-disable-next-line
  },[motion, d?.id]);

  if(done){
    return (
      <div style={{position:'relative'}}>
        {motion && (
          <button onClick={play} title="重放决策过程"
            style={{position:'absolute',top:14,right:16,zIndex:5,display:'flex',alignItems:'center',gap:6,padding:'5px 10px',borderRadius:7,background:'var(--ap-bg-3)',border:'1px solid var(--ap-line)',color:'var(--ap-fg-3)',fontSize:11,cursor:'pointer',fontFamily:'var(--ap-font-mono)'}}>
            <Icon name="play" size={11}/> 重放
          </button>
        )}
        <AIDecisionCard d={d} variant={variant}/>
      </div>
    );
  }

  // streaming view
  return (
    <WCard glow>
      <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:18}}>
        <div style={{width:28,height:28,borderRadius:8,background:'var(--ap-violet-soft)',display:'flex',alignItems:'center',justifyContent:'center'}}>
          <Icon name="brain" size={16} color="var(--ap-violet)"/>
        </div>
        <div style={{flex:1}}>
          <div style={{fontSize:10.5,color:'var(--ap-violet)',letterSpacing:'.1em',fontWeight:700,display:'flex',alignItems:'center',gap:8}}>
            AI DECISION
            <span style={{display:'inline-flex',gap:3}}>
              {[0,1,2].map(i=><span key={i} style={{width:4,height:4,borderRadius:'50%',background:'var(--ap-violet)',animation:`apblink 1s ${i*0.18}s infinite`}}/>)}
            </span>
          </div>
          <div style={{fontFamily:'var(--ap-font-mono)',fontSize:11,color:'var(--ap-fg-3)'}}>{d.sym} · {d.tf} · 实时推理中…</div>
        </div>
      </div>

      <div style={{display:'flex',flexDirection:'column',gap:2,position:'relative',paddingLeft:4}}>
        {STREAM_STAGES.map((s,i)=>{
          const active = i===stage;
          const complete = i<stage;
          const pending = i>stage;
          return (
            <div key={s.k} style={{display:'flex',gap:14,padding:'10px 0',opacity:pending?0.35:1,transition:'opacity .3s',position:'relative'}}>
              {i<STREAM_STAGES.length-1 && <div style={{position:'absolute',left:13,top:30,bottom:-4,width:1.5,background:complete?s.color:'var(--ap-line)',opacity:.5}}/>}
              <div style={{width:26,height:26,borderRadius:'50%',flexShrink:0,zIndex:1,display:'flex',alignItems:'center',justifyContent:'center',
                background: complete?s.color:active?'var(--ap-bg-3)':'var(--ap-bg-3)',
                border: active?`2px solid ${s.color}`:complete?'none':'1px solid var(--ap-line)',
                boxShadow: active?`0 0 14px ${s.color}66`:'none',
                animation: active?'appulse 1.2s infinite':'none'}}>
                {complete
                  ? <Icon name="check" size={13} color="var(--ap-bg-0)" strokeWidth={2.6}/>
                  : <Icon name={s.icon} size={12} color={active?s.color:'var(--ap-fg-4)'} strokeWidth={2}/>}
              </div>
              <div style={{flex:1,paddingTop:2}}>
                <div style={{fontSize:13,fontWeight:600,color: active?s.color:'var(--ap-fg-1)'}}>{s.label}{active && <span style={{fontFamily:'var(--ap-font-mono)',fontWeight:400}}> …</span>}</div>
                <div style={{fontSize:11.5,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)',marginTop:1}}>{s.detail}</div>
              </div>
            </div>
          );
        })}
      </div>
    </WCard>
  );
};

// ============================================================
// WSparkLive — interactive area chart w/ crosshair + tooltip
// ============================================================
const WSparkLive = ({ data, h=160, color='var(--ap-mint)', gridId='wsl', valuePrefix='$', baseTs=Date.now() }) => {
  const wrapRef = React.useRef(null);
  const [hover, setHover] = React.useState(null); // {i, x, y, value}
  const [w, setW] = React.useState(700);

  React.useEffect(()=>{
    const ro = new ResizeObserver(es=>{ for(const e of es) setW(e.contentRect.width); });
    if(wrapRef.current) ro.observe(wrapRef.current);
    return ()=>ro.disconnect();
  },[]);

  const min = Math.min(...data), max=Math.max(...data), r=(max-min)||1;
  const px = i => i/(data.length-1)*w;
  const py = v => h - ((v-min)/r)*(h-16) - 8;
  const pts = data.map((v,i)=>[px(i), py(v)]);
  const path = pts.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' ');
  const area = path+` L ${w} ${h} L 0 ${h} Z`;

  const onMove = (e)=>{
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const i = Math.max(0, Math.min(data.length-1, Math.round(x/w*(data.length-1))));
    setHover({ i, x:px(i), y:py(data[i]), value:data[i] });
  };

  const change = hover ? ((hover.value - data[0])/data[0]*100) : null;

  return (
    <div ref={wrapRef} style={{position:'relative',width:'100%',userSelect:'none'}}>
      <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{display:'block'}}
           onMouseMove={onMove} onMouseLeave={()=>setHover(null)}>
        <defs>
          <linearGradient id={gridId} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor={color} stopOpacity=".32"/>
            <stop offset="1" stopColor={color} stopOpacity="0"/>
          </linearGradient>
        </defs>
        {[0.25,0.5,0.75].map(t=>(<line key={t} x1="0" x2={w} y1={t*h} y2={t*h} stroke="var(--ap-line-soft)" strokeWidth="1"/>))}
        <path d={area} fill={`url(#${gridId})`}/>
        <path d={path} stroke={color} strokeWidth="1.8" fill="none" strokeLinejoin="round" vectorEffect="non-scaling-stroke"/>
        {hover && (
          <g>
            <line x1={hover.x} x2={hover.x} y1="0" y2={h} stroke="var(--ap-fg-3)" strokeWidth="1" strokeDasharray="3 3" vectorEffect="non-scaling-stroke"/>
            <circle cx={hover.x} cy={hover.y} r="4" fill={color} stroke="var(--ap-bg-1)" strokeWidth="2"/>
          </g>
        )}
      </svg>
      {hover && (
        <div style={{position:'absolute',top:6,left:Math.max(4, Math.min(hover.x/w*100, 78))+'%',transform:'translateX(-50%)',
          background:'var(--ap-bg-4)',border:'1px solid var(--ap-line)',borderRadius:8,padding:'6px 10px',pointerEvents:'none',
          boxShadow:'var(--ap-shadow-2)',whiteSpace:'nowrap',zIndex:2}}>
          <div style={{fontFamily:'var(--ap-font-mono)',fontSize:13,fontWeight:700,color:'var(--ap-fg-1)'}}>{valuePrefix}{wfmt(hover.value)}</div>
          <div style={{fontFamily:'var(--ap-font-mono)',fontSize:10,color: change>=0?'var(--ap-mint)':'var(--ap-rose)'}}>{change>=0?'▲':'▼'} {wfmtPct(change)} 自起点</div>
        </div>
      )}
    </div>
  );
};

// ============================================================
// CommandPalette — ⌘K
// ============================================================
const CommandPalette = ({ open, onClose, onNav, onSetVariant, onSetScene, onOpenChat }) => {
  const [q, setQ] = React.useState('');
  const inputRef = React.useRef(null);
  const [sel, setSel] = React.useState(0);

  const commands = React.useMemo(()=>[
    {group:'导航', label:'主控制台', hint:'Cockpit', icon:'dashboard', run:()=>onNav('dashboard')},
    {group:'导航', label:'行情', hint:'Market', icon:'chart', run:()=>onNav('market')},
    {group:'导航', label:'AI 决策流', hint:'Decisions', icon:'brain', run:()=>onNav('ai')},
    {group:'导航', label:'持仓与订单', hint:'Positions', icon:'layers', run:()=>onNav('positions')},
    {group:'导航', label:'回测与绩效', hint:'Performance', icon:'chart', run:()=>onNav('backtest')},
    {group:'导航', label:'策略与风控', hint:'Risk', icon:'shield', run:()=>onNav('risk')},
    {group:'导航', label:'策略实验室', hint:'Shadow Lab', icon:'book', run:()=>onNav('lab')},
    {group:'导航', label:'审计日志', hint:'Audit', icon:'list', run:()=>onNav('audit')},
    {group:'导航', label:'后台管理', hint:'Admin', icon:'users', run:()=>onNav('admin')},
    {group:'AI', label:'问 Pilot AI', hint:'⌘J', icon:'brain', run:()=>onOpenChat?.()},
    {group:'交易对', label:'BTCUSDT', hint:'持仓 +2.14%', icon:'circle', run:()=>onNav('positions')},
    {group:'交易对', label:'ETHUSDT', hint:'持仓 −0.62%', icon:'circle', run:()=>onNav('positions')},
    {group:'AI 卡片样式', label:'Stepper 流水线', hint:'variant', icon:'bolt', run:()=>onSetVariant('stepper')},
    {group:'AI 卡片样式', label:'Timeline 时间线', hint:'variant', icon:'clock', run:()=>onSetVariant('timeline')},
    {group:'AI 卡片样式', label:'Graph 节点图', hint:'variant', icon:'layers', run:()=>onSetVariant('graph')},
    {group:'场景模拟', label:'盈利 · 风控正常', hint:'scene', icon:'check', run:()=>onSetScene('profit')},
    {group:'场景模拟', label:'接近熔断阈值', hint:'scene', icon:'alert', run:()=>onSetScene('warn')},
    {group:'场景模拟', label:'日亏熔断已触发', hint:'scene', icon:'alert', run:()=>onSetScene('halted')},
  ],[onNav,onSetVariant,onSetScene,onOpenChat]);

  const filtered = commands.filter(c=> !q || (c.label+c.hint+c.group).toLowerCase().includes(q.toLowerCase()));

  React.useEffect(()=>{ if(open){ setQ(''); setSel(0); setTimeout(()=>inputRef.current?.focus(),30); } },[open]);
  React.useEffect(()=>{ setSel(0); },[q]);

  const onKey = (e)=>{
    if(e.key==='ArrowDown'){ e.preventDefault(); setSel(s=>Math.min(filtered.length-1,s+1)); }
    else if(e.key==='ArrowUp'){ e.preventDefault(); setSel(s=>Math.max(0,s-1)); }
    else if(e.key==='Enter'){ e.preventDefault(); filtered[sel]?.run(); onClose(); }
    else if(e.key==='Escape'){ onClose(); }
  };

  if(!open) return null;
  let lastGroup=null;
  return (
    <div onMouseDown={onClose} style={{position:'fixed',inset:0,background:'rgba(0,0,0,.6)',backdropFilter:'blur(4px)',zIndex:2000,display:'flex',justifyContent:'center',alignItems:'flex-start',paddingTop:'12vh'}}>
      <div onMouseDown={e=>e.stopPropagation()} style={{width:560,maxWidth:'90vw',background:'var(--ap-bg-2)',border:'1px solid var(--ap-line)',borderRadius:14,boxShadow:'var(--ap-shadow-3)',overflow:'hidden'}}>
        <div style={{display:'flex',alignItems:'center',gap:10,padding:'14px 16px',borderBottom:'1px solid var(--ap-line-soft)'}}>
          <Icon name="search" size={16} color="var(--ap-fg-3)"/>
          <input ref={inputRef} value={q} onChange={e=>setQ(e.target.value)} onKeyDown={onKey}
            placeholder="搜索页面、交易对、命令…"
            style={{flex:1,background:'transparent',border:'none',outline:'none',color:'var(--ap-fg-1)',fontSize:15,fontFamily:'inherit'}}/>
          <span style={{fontFamily:'var(--ap-font-mono)',fontSize:10,color:'var(--ap-fg-4)',background:'var(--ap-bg-3)',padding:'2px 6px',borderRadius:4,border:'1px solid var(--ap-line)'}}>ESC</span>
        </div>
        <div style={{maxHeight:360,overflow:'auto',padding:6}}>
          {filtered.length===0 && <div style={{padding:'24px',textAlign:'center',color:'var(--ap-fg-4)',fontSize:13}}>无匹配结果</div>}
          {filtered.map((c,i)=>{
            const showGroup = c.group!==lastGroup; lastGroup=c.group;
            const active = i===sel;
            return (
              <React.Fragment key={i}>
                {showGroup && <div style={{fontSize:10,color:'var(--ap-fg-4)',letterSpacing:'.08em',textTransform:'uppercase',padding:'10px 10px 4px',fontWeight:600}}>{c.group}</div>}
                <div onMouseEnter={()=>setSel(i)} onClick={()=>{c.run();onClose();}}
                  style={{display:'flex',alignItems:'center',gap:10,padding:'9px 10px',borderRadius:8,cursor:'pointer',background:active?'var(--ap-bg-3)':'transparent'}}>
                  <div style={{width:24,height:24,borderRadius:6,background:'var(--ap-bg-3)',display:'flex',alignItems:'center',justifyContent:'center'}}>
                    <Icon name={c.icon} size={13} color={active?'var(--ap-mint)':'var(--ap-fg-3)'}/>
                  </div>
                  <span style={{flex:1,fontSize:13,color:'var(--ap-fg-1)'}}>{c.label}</span>
                  <span style={{fontSize:11,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)'}}>{c.hint}</span>
                  {active && <Icon name="chevron_right" size={13} color="var(--ap-fg-3)"/>}
                </div>
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// ============================================================
// EmptyState
// ============================================================
const EmptyState = ({ icon='circle', title, sub }) => (
  <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',padding:'48px 24px',textAlign:'center',gap:10}}>
    <div style={{width:48,height:48,borderRadius:12,background:'var(--ap-bg-3)',display:'flex',alignItems:'center',justifyContent:'center'}}>
      <Icon name={icon} size={22} color="var(--ap-fg-4)"/>
    </div>
    <div style={{fontSize:14,fontWeight:600,color:'var(--ap-fg-2)'}}>{title}</div>
    {sub && <div style={{fontSize:12,color:'var(--ap-fg-4)',maxWidth:280}}>{sub}</div>}
  </div>
);

Object.assign(window, { AnimatedNumber, HaltBanner, StreamingDecision, WSparkLive, CommandPalette, EmptyState, STREAM_STAGES });
