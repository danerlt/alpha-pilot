// Strategy Lab — Shadow Mode (受控进化): candidates run in shadow, compare, promote/rollback

const LAB_CANDIDATES = [
  {
    id:'cand_a3f2', name:'趋势跟随 v2.1', base:'趋势跟随 v2.0（当前线上）',
    change:'入场增加 4h 级别趋势过滤；ATR 止损从 2.0x 收紧到 1.6x',
    origin:'经验库归因 · 12 个亏损案例聚类',
    stage:'shadow', day:9, total:14,
    shadow:{trades:31, win:64, pnl:4.21, sharpe:2.08, dd:-1.8},
    live:{trades:29, win:55, pnl:2.87, sharpe:1.84, dd:-3.1},
    verdict:'better',
  },
  {
    id:'cand_b7c1', name:'突破确认 v1.3', base:'突破确认 v1.2（当前停用）',
    change:'突破量能阈值 1.4x → 1.8x；增加假突破回撤检测',
    origin:'AI 自主提案 · 周复盘',
    stage:'shadow', day:3, total:14,
    shadow:{trades:8, win:50, pnl:-0.42, sharpe:0.61, dd:-1.2},
    live:{trades:8, win:50, pnl:-0.38, sharpe:0.66, dd:-1.1},
    verdict:'neutral',
  },
  {
    id:'cand_c9d4', name:'资金费率套利 v0.1', base:'新策略（无基线）',
    change:'资金费率极值时反向持仓收取费率；严格 delta 中性',
    origin:'用户提案 · 待验证',
    stage:'queued', day:0, total:14,
    shadow:null, live:null, verdict:null,
  },
];

const HISTORY = [
  {t:'06-28 14:00', name:'趋势跟随 v2.0', event:'promote', note:'影子期 14 天 · Sharpe 1.62→1.84 · 人工批准上线'},
  {t:'06-15 09:30', name:'均值回归 v0.4', event:'rollback', note:'灰度期回撤 −3.4% 触发自动回滚 · 已归档'},
  {t:'06-02 11:00', name:'趋势跟随 v1.9', event:'retire', note:'被 v2.0 替代 · 保留 90 天可回退'},
];

const StageBadge = ({stage}) => {
  const cfg = {
    shadow:{l:'SHADOW 影子运行', tone:'violet'},
    queued:{l:'QUEUED 排队中', tone:'default'},
    canary:{l:'CANARY 灰度', tone:'amber'},
    live:{l:'LIVE 线上', tone:'mint'},
  }[stage];
  return <WPill tone={cfg.tone}>{cfg.l}</WPill>;
};

const CompareRow = ({label, shadow, live, better, fmt=(v)=>v, suffix=''}) => {
  const sBetter = better==='higher' ? shadow>live : shadow<live;
  return (
    <div style={{display:'grid',gridTemplateColumns:'90px 1fr 1fr',gap:8,padding:'7px 0',borderBottom:'1px solid var(--ap-line-soft)',fontSize:11.5,alignItems:'center'}}>
      <span style={{color:'var(--ap-fg-4)'}}>{label}</span>
      <span style={{fontFamily:'var(--ap-font-mono)',fontWeight:600,color: sBetter?'var(--ap-mint)':'var(--ap-fg-1)'}}>{fmt(shadow)}{suffix}{sBetter&&' ▲'}</span>
      <span style={{fontFamily:'var(--ap-font-mono)',color:'var(--ap-fg-3)'}}>{fmt(live)}{suffix}</span>
    </div>
  );
};

const CandidateCard = ({c}) => {
  const isQueued = c.stage==='queued';
  return (
    <WCard style={{borderColor: c.verdict==='better'?'rgba(124,92,255,.4)':'var(--ap-line-soft)'}}>
      {/* header */}
      <div style={{display:'flex',alignItems:'flex-start',gap:12,marginBottom:12}}>
        <div style={{width:34,height:34,borderRadius:9,background:'var(--ap-violet-soft)',display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0}}>
          <Icon name="layers" size={16} color="var(--ap-violet)"/>
        </div>
        <div style={{flex:1,minWidth:0}}>
          <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}>
            <span style={{fontSize:14,fontWeight:700}}>{c.name}</span>
            <StageBadge stage={c.stage}/>
            {c.verdict==='better' && <WPill tone="mint">优于线上</WPill>}
          </div>
          <div style={{fontSize:11,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)',marginTop:2}}>{c.id} · 基线: {c.base}</div>
        </div>
      </div>

      {/* change description */}
      <div style={{background:'var(--ap-bg-3)',borderRadius:8,padding:'10px 12px',marginBottom:12}}>
        <div style={{fontSize:10,color:'var(--ap-violet)',letterSpacing:'.06em',fontWeight:700,marginBottom:4}}>变更内容</div>
        <div style={{fontSize:12.5,color:'var(--ap-fg-2)',lineHeight:1.55}}>{c.change}</div>
        <div style={{fontSize:10.5,color:'var(--ap-fg-4)',marginTop:6,fontFamily:'var(--ap-font-mono)'}}>来源 · {c.origin}</div>
      </div>

      {isQueued ? (
        <div style={{display:'flex',alignItems:'center',gap:10}}>
          <div style={{flex:1,fontSize:12,color:'var(--ap-fg-3)'}}>等待影子槽位 · 预计明日开始 14 天影子运行</div>
          <button style={{padding:'8px 14px',borderRadius:8,border:'1px solid var(--ap-violet)',background:'var(--ap-violet-soft)',color:'var(--ap-violet)',fontSize:12,fontWeight:600,cursor:'pointer',fontFamily:'inherit'}}>立即开始</button>
        </div>
      ) : (
        <>
          {/* progress */}
          <div style={{marginBottom:12}}>
            <div style={{display:'flex',justifyContent:'space-between',fontSize:10.5,fontFamily:'var(--ap-font-mono)',color:'var(--ap-fg-3)',marginBottom:5}}>
              <span>影子运行 第 {c.day}/{c.total} 天</span><span>{Math.round(c.day/c.total*100)}%</span>
            </div>
            <div style={{height:5,background:'var(--ap-bg-3)',borderRadius:3,overflow:'hidden'}}>
              <div style={{width:(c.day/c.total*100)+'%',height:'100%',background:'var(--ap-violet)',borderRadius:3,boxShadow:'0 0 8px var(--ap-violet-glow)'}}/>
            </div>
          </div>

          {/* comparison */}
          <div style={{display:'grid',gridTemplateColumns:'90px 1fr 1fr',gap:8,padding:'4px 0 6px',fontSize:10,color:'var(--ap-fg-4)',letterSpacing:'.06em',textTransform:'uppercase'}}>
            <span></span><span style={{color:'var(--ap-violet)'}}>影子 (模拟)</span><span>线上 (真实)</span>
          </div>
          <CompareRow label="交易数" shadow={c.shadow.trades} live={c.live.trades} better="higher"/>
          <CompareRow label="胜率" shadow={c.shadow.win} live={c.live.win} better="higher" suffix="%"/>
          <CompareRow label="净收益" shadow={c.shadow.pnl} live={c.live.pnl} better="higher" fmt={v=>(v>=0?'+':'')+v.toFixed(2)} suffix="%"/>
          <CompareRow label="Sharpe" shadow={c.shadow.sharpe} live={c.live.sharpe} better="higher" fmt={v=>v.toFixed(2)}/>
          <CompareRow label="最大回撤" shadow={c.shadow.dd} live={c.live.dd} better="lower" fmt={v=>v.toFixed(1)} suffix="%"/>

          {/* actions */}
          <div style={{display:'flex',gap:8,marginTop:14,alignItems:'center'}}>
            {c.verdict==='better' && c.day>=c.total*0.6 ? (
              <button style={{padding:'9px 16px',borderRadius:9,border:'none',background:'var(--ap-mint)',color:'var(--ap-bg-0)',fontSize:12,fontWeight:700,cursor:'pointer',fontFamily:'inherit'}}>申请灰度上线 →</button>
            ) : (
              <button disabled style={{padding:'9px 16px',borderRadius:9,border:'1px solid var(--ap-line)',background:'var(--ap-bg-3)',color:'var(--ap-fg-4)',fontSize:12,fontWeight:600,cursor:'not-allowed',fontFamily:'inherit'}}>
                {c.verdict==='better'?'影子期未满 60%':'表现未达标'}
              </button>
            )}
            <button style={{padding:'9px 14px',borderRadius:9,border:'1px solid var(--ap-line)',background:'transparent',color:'var(--ap-fg-3)',fontSize:12,cursor:'pointer',fontFamily:'inherit'}}>终止</button>
            <span style={{marginLeft:'auto',fontSize:10,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)'}}>上线需人工批准</span>
          </div>
        </>
      )}
    </WCard>
  );
};

const WLabPage = () => (
  <div style={{display:'flex',flexDirection:'column',gap:20,maxWidth:1100}}>
    {/* explainer strip */}
    <WCard>
      <div style={{display:'flex',gap:14,alignItems:'flex-start'}}>
        <div style={{width:34,height:34,borderRadius:9,background:'var(--ap-violet-soft)',display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0}}>
          <Icon name="book" size={17} color="var(--ap-violet)"/>
        </div>
        <div style={{flex:1}}>
          <div style={{fontSize:14,fontWeight:700,marginBottom:4}}>受控进化 · Shadow Mode</div>
          <div style={{fontSize:12.5,color:'var(--ap-fg-3)',lineHeight:1.6}}>
            AI 或人工提出的策略改进不会直接上线。候选版本先以<b style={{color:'var(--ap-violet)'}}>影子模式</b>并行运行（收到同样的市场数据、产生模拟决策但不下单），
            与线上版本逐笔对比。影子期 ≥14 天且关键指标优于基线，方可申请<b style={{color:'var(--ap-amber)'}}>灰度</b>（小仓位真实运行），
            最终<b style={{color:'var(--ap-mint)'}}>人工批准</b>上线。灰度期回撤超限自动回滚。
          </div>
          {/* pipeline visual */}
          <div style={{display:'flex',alignItems:'center',gap:0,marginTop:12,maxWidth:560}}>
            {[['提案','var(--ap-fg-3)'],['SHADOW 14d','var(--ap-violet)'],['CANARY 灰度','var(--ap-amber)'],['人工批准','var(--ap-fg-2)'],['LIVE','var(--ap-mint)']].map(([l,c],i,arr)=>(
              <React.Fragment key={i}>
                <div style={{padding:'5px 12px',borderRadius:999,border:`1px solid ${c}`,color:c,fontSize:10.5,fontFamily:'var(--ap-font-mono)',fontWeight:600,whiteSpace:'nowrap'}}>{l}</div>
                {i<arr.length-1 && <div style={{flex:1,height:1.5,background:'var(--ap-line)',minWidth:12}}/>}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </WCard>

    {/* candidates */}
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:20,alignItems:'start'}}>
      {LAB_CANDIDATES.slice(0,2).map(c=><CandidateCard key={c.id} c={c}/>)}
    </div>
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:20,alignItems:'start'}}>
      <CandidateCard c={LAB_CANDIDATES[2]}/>
      {/* history */}
      <WCard title="进化历史">
        {HISTORY.map((h,i)=>(
          <div key={i} style={{display:'flex',gap:12,padding:'10px 0',borderBottom:i<HISTORY.length-1?'1px solid var(--ap-line-soft)':'none'}}>
            <div style={{width:26,height:26,borderRadius:'50%',flexShrink:0,display:'flex',alignItems:'center',justifyContent:'center',
              background: h.event==='promote'?'var(--ap-mint-soft)':h.event==='rollback'?'var(--ap-rose-soft)':'var(--ap-bg-3)'}}>
              <Icon name={h.event==='promote'?'arrow_up':h.event==='rollback'?'arrow_down':'pause'} size={12}
                color={h.event==='promote'?'var(--ap-mint)':h.event==='rollback'?'var(--ap-rose)':'var(--ap-fg-4)'} strokeWidth={2.2}/>
            </div>
            <div style={{flex:1,minWidth:0}}>
              <div style={{display:'flex',alignItems:'center',gap:8}}>
                <span style={{fontSize:12.5,fontWeight:600}}>{h.name}</span>
                <WPill tone={h.event==='promote'?'mint':h.event==='rollback'?'rose':'default'}>{h.event==='promote'?'上线':h.event==='rollback'?'自动回滚':'退役'}</WPill>
              </div>
              <div style={{fontSize:11,color:'var(--ap-fg-4)',marginTop:2,fontFamily:'var(--ap-font-mono)'}}>{h.t} · {h.note}</div>
            </div>
          </div>
        ))}
      </WCard>
    </div>
  </div>
);

Object.assign(window, { WLabPage });
