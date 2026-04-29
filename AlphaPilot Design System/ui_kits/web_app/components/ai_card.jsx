// AI Decision card — 3 visual variants: stepper / timeline / graph

// ============ VARIANT A: Stepper (horizontal pipeline) ============
const AIDecisionStepper = ({d}) => {
  const actionColor = d.action==='OPEN_LONG'?'var(--ap-mint)':d.action==='CLOSE_LONG'?'var(--ap-rose)':'var(--ap-fg-2)';
  const guardTone = d.guard==='PASS'?'mint':d.guard==='REJECT'?'rose':'amber';
  return (
    <WCard glow>
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:14}}>
        <div style={{display:'flex',alignItems:'center',gap:10}}>
          <div style={{width:28,height:28,borderRadius:8,background:'var(--ap-violet-soft)',display:'flex',alignItems:'center',justifyContent:'center'}}>
            <Icon name="brain" size={16} color="var(--ap-violet)"/>
          </div>
          <div>
            <div style={{fontSize:10.5,color:'var(--ap-violet)',letterSpacing:'.1em',fontWeight:700}}>AI DECISION</div>
            <div style={{fontFamily:'var(--ap-font-mono)',fontSize:11,color:'var(--ap-fg-3)',letterSpacing:'.02em'}}>{d.id} · {d.sym} · {d.tf} · {d.t}</div>
          </div>
        </div>
        <div style={{display:'flex',alignItems:'baseline',gap:10}}>
          <span style={{fontFamily:'var(--ap-font-mono)',fontSize:22,fontWeight:700,color:actionColor,letterSpacing:'.02em'}}>{d.action}</span>
          <span style={{fontSize:12,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>conf <b style={{color:'var(--ap-fg-1)'}}>{d.conf?.toFixed(2)}</b></span>
        </div>
      </div>

      {d.sl && (
        <div style={{display:'grid',gridTemplateColumns:'repeat(5,1fr)',gap:2,marginBottom:14,background:'var(--ap-bg-3)',borderRadius:10,overflow:'hidden'}}>
          {[
            ['策略', d.strat, 'var(--ap-fg-1)'],
            ['入场', wfmt(d.entry), 'var(--ap-fg-1)'],
            ['仓位', d.size, 'var(--ap-fg-1)'],
            ['止损', wfmt(d.sl), 'var(--ap-rose)'],
            ['止盈', wfmt(d.tp), 'var(--ap-mint)'],
          ].map(([l,v,c],i)=>(
            <div key={i} style={{padding:'10px 12px',background:'var(--ap-bg-2)'}}>
              <div style={{fontSize:9.5,color:'var(--ap-fg-3)',letterSpacing:'.08em',textTransform:'uppercase',marginBottom:3}}>{l}</div>
              <div style={{fontFamily:'var(--ap-font-mono)',fontSize:13,fontWeight:600,color:c}}>{v}</div>
            </div>
          ))}
        </div>
      )}

      {/* pipeline */}
      <div style={{display:'flex',alignItems:'center',padding:'6px 0 16px'}}>
        {[
          {label:'市场快照', sub:'regime · features', ok:true},
          {label:'AI 推理', sub:`conf ${d.conf?.toFixed(2)}`, ok:true},
          {label:'守卫检查', sub:d.guard, ok:d.guard!=='REJECT', degraded:d.guard==='DEGRADE'},
          {label:'风险裁决', sub:d.guard==='PASS'?'允许执行':'回退 HOLD', ok:d.guard==='PASS'},
          {label:'执行', sub:d.guard==='PASS'?'已下单':'未执行', ok:d.guard==='PASS'},
        ].map((step,i,arr)=>(
          <React.Fragment key={i}>
            <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:8,flexShrink:0,width:100}}>
              <div style={{width:32,height:32,borderRadius:'50%',background: step.ok?'var(--ap-mint)':step.degraded?'var(--ap-amber)':'var(--ap-rose)',display:'flex',alignItems:'center',justifyContent:'center',color:'var(--ap-bg-0)',fontWeight:700,boxShadow: step.ok?'0 0 12px rgba(0,211,149,.4)':step.degraded?'0 0 12px rgba(240,185,11,.4)':'0 0 12px rgba(255,77,109,.4)'}}>
                <Icon name={step.ok?'check':step.degraded?'alert':'x'} size={15} color="var(--ap-bg-0)" strokeWidth={2.4}/>
              </div>
              <div style={{textAlign:'center'}}>
                <div style={{fontSize:12,color:'var(--ap-fg-1)',fontWeight:600}}>{step.label}</div>
                <div style={{fontSize:10.5,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)',marginTop:2}}>{step.sub}</div>
              </div>
            </div>
            {i<arr.length-1 && <div style={{flex:1,height:2,background: step.ok?'var(--ap-mint)':step.degraded?'var(--ap-amber)':'var(--ap-rose)',marginTop:-30,opacity:.55}}/>}
          </React.Fragment>
        ))}
      </div>

      {/* reasoning */}
      <div style={{background:'var(--ap-bg-3)',borderRadius:10,padding:'12px 14px',fontSize:13,color:'var(--ap-fg-2)',lineHeight:1.6}}>
        <div style={{fontSize:10,color:'var(--ap-violet)',letterSpacing:'.08em',fontWeight:700,marginBottom:6}}>REASONING</div>
        {d.reason}
      </div>

      <div style={{display:'flex',alignItems:'center',gap:8,marginTop:14}}>
        <WPill tone={guardTone}>守卫 {d.guard}</WPill>
        {d.features && <WPill tone="violet">{d.features.length} features</WPill>}
        {d.guards && <WPill tone="default">{d.guards.filter(g=>g.ok).length}/{d.guards.length} checks</WPill>}
        <span style={{marginLeft:'auto',fontSize:11,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)'}}>trace · {d.id.replace('d_','')}</span>
      </div>
    </WCard>
  );
};

// ============ VARIANT B: Timeline (vertical stages) ============
const AIDecisionTimeline = ({d}) => {
  const actionColor = d.action==='OPEN_LONG'?'var(--ap-mint)':d.action==='CLOSE_LONG'?'var(--ap-rose)':'var(--ap-fg-2)';
  const stages = [
    {t:d.t, label:'信号感知', detail:'regime=trending_up · BTC 1h EMA 金叉', color:'var(--ap-cyan)', icon:'bolt'},
    {t:d.t, label:'AI 推理', detail:`${d.strat} · 置信度 ${d.conf?.toFixed(2)} · 输出 ${d.action}`, color:'var(--ap-violet)', icon:'brain'},
    {t:d.t, label:'守卫检查', detail:d.guards ? `${d.guards.filter(g=>g.ok).length}/${d.guards.length} 通过` : d.guard, color: d.guard==='PASS'?'var(--ap-mint)':d.guard==='DEGRADE'?'var(--ap-amber)':'var(--ap-rose)', icon:'shield'},
    {t:d.t, label:'风险裁决', detail: d.guard==='PASS'?'允许执行 · 下单 '+(d.size||''):'回退 HOLD · 不下单', color: d.guard==='PASS'?'var(--ap-mint)':'var(--ap-rose)', icon:'check'},
    {t:d.t, label:'执行', detail: d.guard==='PASS'?`Binance 市价成交 @ ${wfmt(d.entry||0)}`:'—', color: d.guard==='PASS'?'var(--ap-mint)':'var(--ap-fg-4)', icon:'play'},
  ];
  return (
    <WCard glow>
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:18}}>
        <div style={{display:'flex',alignItems:'center',gap:10}}>
          <div style={{width:28,height:28,borderRadius:8,background:'var(--ap-violet-soft)',display:'flex',alignItems:'center',justifyContent:'center'}}>
            <Icon name="brain" size={16} color="var(--ap-violet)"/>
          </div>
          <div>
            <div style={{fontSize:10.5,color:'var(--ap-violet)',letterSpacing:'.1em',fontWeight:700}}>AI DECISION · TIMELINE</div>
            <div style={{fontFamily:'var(--ap-font-mono)',fontSize:11,color:'var(--ap-fg-3)'}}>{d.id} · {d.sym} · {d.tf}</div>
          </div>
        </div>
        <span style={{fontFamily:'var(--ap-font-mono)',fontSize:22,fontWeight:700,color:actionColor}}>{d.action}</span>
      </div>

      <div style={{position:'relative',paddingLeft:4}}>
        {stages.map((s,i)=>(
          <div key={i} style={{display:'flex',gap:14,paddingBottom:i===stages.length-1?0:14,position:'relative'}}>
            {/* rail */}
            {i<stages.length-1 && <div style={{position:'absolute',left:11,top:26,bottom:-4,width:1.5,background:'linear-gradient(to bottom, '+s.color+' 0%, var(--ap-line) 100%)',opacity:.5}}/>}
            <div style={{width:24,height:24,borderRadius:'50%',background:s.color,display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0,boxShadow:`0 0 10px ${s.color}40`,zIndex:1}}>
              <Icon name={s.icon} size={12} color="var(--ap-bg-0)" strokeWidth={2.2}/>
            </div>
            <div style={{flex:1,paddingTop:2}}>
              <div style={{display:'flex',alignItems:'baseline',gap:8,marginBottom:2}}>
                <span style={{fontSize:13,fontWeight:600,color:'var(--ap-fg-1)'}}>{s.label}</span>
                <span style={{fontSize:10,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)',marginLeft:'auto'}}>{s.t}</span>
              </div>
              <div style={{fontSize:12,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>{s.detail}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{marginTop:18,padding:'12px 14px',background:'var(--ap-bg-3)',borderRadius:10,fontSize:13,color:'var(--ap-fg-2)',lineHeight:1.6}}>
        <div style={{fontSize:10,color:'var(--ap-violet)',letterSpacing:'.08em',fontWeight:700,marginBottom:6}}>REASONING</div>
        {d.reason}
      </div>
    </WCard>
  );
};

// ============ VARIANT C: Graph (node diagram) ============
const AIDecisionGraph = ({d}) => {
  const actionColor = d.action==='OPEN_LONG'?'var(--ap-mint)':d.action==='CLOSE_LONG'?'var(--ap-rose)':'var(--ap-fg-2)';
  const guardPass = d.guard==='PASS';
  const guardColor = guardPass?'var(--ap-mint)':d.guard==='DEGRADE'?'var(--ap-amber)':'var(--ap-rose)';

  return (
    <WCard glow>
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:16}}>
        <div style={{display:'flex',alignItems:'center',gap:10}}>
          <div style={{width:28,height:28,borderRadius:8,background:'var(--ap-violet-soft)',display:'flex',alignItems:'center',justifyContent:'center'}}>
            <Icon name="brain" size={16} color="var(--ap-violet)"/>
          </div>
          <div>
            <div style={{fontSize:10.5,color:'var(--ap-violet)',letterSpacing:'.1em',fontWeight:700}}>AI DECISION · GRAPH</div>
            <div style={{fontFamily:'var(--ap-font-mono)',fontSize:11,color:'var(--ap-fg-3)'}}>{d.id} · {d.sym} · {d.tf}</div>
          </div>
        </div>
        <span style={{fontFamily:'var(--ap-font-mono)',fontSize:22,fontWeight:700,color:actionColor}}>{d.action}</span>
      </div>

      {/* graph canvas */}
      <div style={{position:'relative',background:'var(--ap-bg-3)',borderRadius:12,padding:'20px 20px',minHeight:360,overflow:'hidden'}}>
        {/* faint grid */}
        <svg style={{position:'absolute',inset:0,width:'100%',height:'100%',opacity:.25,pointerEvents:'none'}}>
          <defs>
            <pattern id="gd" width="24" height="24" patternUnits="userSpaceOnUse">
              <path d="M 24 0 L 0 0 0 24" fill="none" stroke="var(--ap-line)" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#gd)"/>
        </svg>

        {/* edges */}
        <svg style={{position:'absolute',inset:0,width:'100%',height:'100%',pointerEvents:'none'}}>
          <defs>
            <marker id="arrow-mint" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ap-mint)"/>
            </marker>
            <marker id="arrow-v" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ap-violet)"/>
            </marker>
            <marker id="arrow-c" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ap-cyan)"/>
            </marker>
          </defs>
          {/* features → AI */}
          {[60,110,160,210,260,310].map((y,i)=>(
            <path key={i} d={`M 180 ${y} C 240 ${y}, 260 180, 310 180`} stroke="var(--ap-cyan)" strokeWidth="1" strokeOpacity=".55" fill="none"/>
          ))}
          {/* AI → guard */}
          <path d="M 480 180 L 560 180" stroke="var(--ap-violet)" strokeWidth="2" fill="none" markerEnd="url(#arrow-v)"/>
          {/* guard checks into guard hub */}
          {[60,100,140,180,220,260,300,340].map((y,i)=>(
            <path key={i} d={`M 680 ${y} C 640 ${y}, 620 180, 640 180`} stroke={guardColor} strokeWidth="1" strokeOpacity=".5" fill="none"/>
          ))}
          {/* guard → action */}
          <path d="M 740 180 L 820 180" stroke={guardColor} strokeWidth="2.5" fill="none" markerEnd={guardPass?'url(#arrow-mint)':undefined}/>
        </svg>

        {/* features column */}
        <div style={{position:'absolute',left:20,top:20,display:'flex',flexDirection:'column',gap:6,width:160}}>
          <div style={{fontSize:9.5,color:'var(--ap-fg-3)',letterSpacing:'.08em',textTransform:'uppercase',marginBottom:2}}>FEATURES</div>
          {(d.features || [
            {k:'regime', v:'trending_up', ok:true},
            {k:'EMA_align', v:'20>50>200', ok:true},
            {k:'vol_mult', v:'1.4x', ok:true},
            {k:'ATR_14', v:'1.82%', ok:true},
            {k:'RSI_14', v:'58', ok:true},
            {k:'BB_width', v:'0.043', ok:true},
          ]).slice(0,6).map((f,i)=>(
            <div key={i} style={{padding:'5px 8px',background:'var(--ap-bg-2)',borderRadius:6,border:'1px solid var(--ap-line-soft)',fontFamily:'var(--ap-font-mono)',fontSize:10.5,display:'flex',justifyContent:'space-between',gap:8}}>
              <span style={{color:'var(--ap-fg-3)'}}>{f.k}</span>
              <span style={{color:'var(--ap-cyan)'}}>{f.v}</span>
            </div>
          ))}
        </div>

        {/* AI hub */}
        <div style={{position:'absolute',left:310,top:140,width:170,padding:'14px',background:'var(--ap-violet-soft)',border:'1px solid var(--ap-violet)',borderRadius:12,boxShadow:'0 0 24px rgba(124,92,255,.3)'}}>
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:6}}>
            <Icon name="brain" size={16} color="var(--ap-violet)"/>
            <span style={{fontSize:12,fontWeight:700,color:'var(--ap-violet)',letterSpacing:'.05em'}}>LLM + RULES</span>
          </div>
          <div style={{fontSize:11,color:'var(--ap-fg-2)'}}>{d.strat}</div>
          <div style={{fontFamily:'var(--ap-font-mono)',fontSize:11,color:'var(--ap-fg-3)',marginTop:6}}>conf <b style={{color:'var(--ap-violet)'}}>{d.conf?.toFixed(2)}</b> · {d.action}</div>
        </div>

        {/* Guard hub */}
        <div style={{position:'absolute',left:560,top:155,width:80,padding:'12px',background:'var(--ap-bg-2)',border:`1px solid ${guardColor}`,borderRadius:12,boxShadow:`0 0 20px ${guardColor}30`,textAlign:'center'}}>
          <Icon name="shield" size={18} color={guardColor}/>
          <div style={{fontSize:10,fontFamily:'var(--ap-font-mono)',fontWeight:700,color:guardColor,marginTop:4,letterSpacing:'.05em'}}>{d.guard}</div>
        </div>

        {/* Guards column */}
        <div style={{position:'absolute',left:680,top:20,display:'flex',flexDirection:'column',gap:4,width:150}}>
          <div style={{fontSize:9.5,color:'var(--ap-fg-3)',letterSpacing:'.08em',textTransform:'uppercase',marginBottom:2}}>GUARDS · 8</div>
          {(d.guards || [
            {k:'regime_match',ok:true},{k:'max_per_trade_risk',ok:true},{k:'max_position_size',ok:true},{k:'daily_loss_limit',ok:true},
            {k:'RR_ratio',ok:true},{k:'correlation_cap',ok:true},{k:'spread_check',ok:true},{k:'cooldown',ok:true}
          ]).map((g,i)=>(
            <div key={i} style={{padding:'4px 8px',background:'var(--ap-bg-2)',borderRadius:6,border:'1px solid var(--ap-line-soft)',fontFamily:'var(--ap-font-mono)',fontSize:10,display:'flex',alignItems:'center',gap:6}}>
              <WDot c={g.ok?'var(--ap-mint)':'var(--ap-rose)'}/>
              <span style={{color:'var(--ap-fg-3)',flex:1,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{g.k}</span>
            </div>
          ))}
        </div>

        {/* Action output */}
        <div style={{position:'absolute',left:820,top:155,padding:'12px 14px',background:guardPass?'var(--ap-mint-soft)':'var(--ap-rose-soft)',border:`1px solid ${guardPass?'var(--ap-mint)':'var(--ap-rose)'}`,borderRadius:12,textAlign:'center'}}>
          <div style={{fontSize:9.5,color:guardPass?'var(--ap-mint)':'var(--ap-rose)',letterSpacing:'.08em',fontWeight:700}}>EXECUTE</div>
          <div style={{fontFamily:'var(--ap-font-mono)',fontSize:14,fontWeight:700,color:guardPass?'var(--ap-mint)':'var(--ap-rose)',marginTop:3}}>{guardPass?d.action:'HOLD'}</div>
        </div>
      </div>

      <div style={{marginTop:14,padding:'12px 14px',background:'var(--ap-bg-3)',borderRadius:10,fontSize:13,color:'var(--ap-fg-2)',lineHeight:1.6}}>
        <div style={{fontSize:10,color:'var(--ap-violet)',letterSpacing:'.08em',fontWeight:700,marginBottom:6}}>REASONING</div>
        {d.reason}
      </div>
    </WCard>
  );
};

// ============ Variant switcher ============
const AIDecisionCard = ({d, variant='stepper'}) => {
  if (variant==='timeline') return <AIDecisionTimeline d={d}/>;
  if (variant==='graph') return <AIDecisionGraph d={d}/>;
  return <AIDecisionStepper d={d}/>;
};

Object.assign(window, { AIDecisionCard, AIDecisionStepper, AIDecisionTimeline, AIDecisionGraph });
