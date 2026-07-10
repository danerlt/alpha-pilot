// Pilot AI — conversational assistant drawer
// Mock conversation with tool-use traces, quick prompts, streaming reply.

const CANNED = {
  '为什么 ETHUSDT 没有开仓？': {
    tools: ['查询决策记录 d_7f3a9a', '读取 regime 状态'],
    reply: '13:45 的决策周期中，ETHUSDT 的市场状态从 trending_up 切换为 chaotic（ATR 波动率进入前 10% 分位），触发策略降级规则。AI 输出 HOLD（置信度 0.42），守卫标记 DEGRADE。\n\n按照受限策略框架，chaotic regime 下仅允许「观望模式」，这是为了避免在无方向高波动期入场。若后续 1h 内 regime 恢复且量能配合，会重新评估。',
  },
  '当前风险敞口如何？': {
    tools: ['读取持仓', '计算组合风险'],
    reply: '当前 2 个持仓，总仓位 12%（上限 15%）：\n\n· BTCUSDT 多 0.048，浮盈 +2.14%，距止损 −6.8%\n· ETHUSDT 多 0.82，浮亏 −0.62%，距止损 −3.1%\n\n组合层面：BTC-ETH 相关度 0.68（上限 0.85），日损 −0.48%（熔断线 −2.00%）。整体风险健康，但 ETH 接近入场价，若跌破 3,180 建议关注。',
  },
  '帮我收紧风控': {
    tools: ['读取当前风控配置'],
    reply: '可以，这是我的建议（需你确认后生效）：\n\n1. 单笔最大风险 1.00% → 0.75%\n2. 日亏损熔断 −2.00% → −1.50%\n3. 连续亏损熔断 3 笔 → 2 笔\n\n注意：硬风控修改走人工确认流程，AI 无权自行变更。是否应用？',
    action: '应用修改（模拟）',
  },
  '今天表现怎么样？': {
    tools: ['读取今日交易', '生成归因'],
    reply: '今日 7 笔交易，胜率 57%，净收益 +1.82%（+$1,248）。\n\n亮点：趋势跟随策略在 BTC 上贡献 +$1,890，两次守卫拦截（RR<1.5）事后看均正确避损。\n\n短板：ETHUSDT 在 regime 切换前 45 分钟入场，时机偏早，−$642。经验库已记录该案例：「chaotic 前兆期的 ranging 误判」。',
  },
};

const QUICK_PROMPTS = Object.keys(CANNED);

const AIChatDrawer = ({open, onClose}) => {
  const [messages, setMessages] = React.useState([
    {role:'ai', text:'你好，我是 Pilot AI。可以问我任何关于持仓、决策、风控的问题——我能读取系统实时状态并解释每一笔决策。', tools:[]},
  ]);
  const [typing, setTyping] = React.useState(false);
  const [input, setInput] = React.useState('');
  const bodyRef = React.useRef(null);
  const timers = React.useRef([]);

  React.useEffect(()=>()=>timers.current.forEach(clearTimeout),[]);
  React.useEffect(()=>{ if(bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight; },[messages,typing]);

  const ask = (q)=>{
    if(!q.trim()) return;
    setMessages(ms=>[...ms,{role:'user',text:q}]);
    setInput('');
    setTyping(true);
    const c = CANNED[q] || {tools:['检索经验库'], reply:'这是原型演示——该问题的完整回答需要接入真实引擎。试试预设的快捷问题，能看到带工具调用轨迹的完整对话效果。'};
    timers.current.push(setTimeout(()=>{
      setTyping(false);
      setMessages(ms=>[...ms,{role:'ai',text:c.reply,tools:c.tools,action:c.action}]);
    }, 900 + Math.random()*500));
  };

  if(!open) return null;
  return (
    <div style={{position:'fixed',top:0,right:0,bottom:0,width:400,maxWidth:'92vw',zIndex:1500,display:'flex',flexDirection:'column',
      background:'var(--ap-bg-1)',borderLeft:'1px solid var(--ap-line)',boxShadow:'-16px 0 48px rgba(0,0,0,.5)'}}>
      {/* header */}
      <div style={{display:'flex',alignItems:'center',gap:10,padding:'14px 16px',borderBottom:'1px solid var(--ap-line-soft)',flexShrink:0}}>
        <div style={{width:30,height:30,borderRadius:8,background:'var(--ap-violet-soft)',display:'flex',alignItems:'center',justifyContent:'center',position:'relative'}}>
          <Icon name="brain" size={16} color="var(--ap-violet)"/>
          <span style={{position:'absolute',bottom:-1,right:-1,width:8,height:8,borderRadius:'50%',background:'var(--ap-mint)',border:'2px solid var(--ap-bg-1)'}}/>
        </div>
        <div style={{flex:1}}>
          <div style={{fontSize:13,fontWeight:700}}>Pilot AI</div>
          <div style={{fontSize:10,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)'}}>可读取实时状态 · 无权绕过风控</div>
        </div>
        <button onClick={onClose} style={{width:28,height:28,borderRadius:7,background:'var(--ap-bg-3)',border:'1px solid var(--ap-line-soft)',display:'flex',alignItems:'center',justifyContent:'center',cursor:'pointer',color:'var(--ap-fg-3)'}}>
          <Icon name="x" size={13}/>
        </button>
      </div>

      {/* messages */}
      <div ref={bodyRef} style={{flex:1,overflow:'auto',padding:'16px 16px',display:'flex',flexDirection:'column',gap:14}}>
        {messages.map((m,i)=>(
          m.role==='user' ? (
            <div key={i} style={{alignSelf:'flex-end',maxWidth:'85%',background:'var(--ap-bg-4)',borderRadius:'12px 12px 4px 12px',padding:'10px 13px',fontSize:13,lineHeight:1.55}}>{m.text}</div>
          ) : (
            <div key={i} style={{alignSelf:'flex-start',maxWidth:'92%',display:'flex',flexDirection:'column',gap:6}}>
              {m.tools?.length>0 && (
                <div style={{display:'flex',flexDirection:'column',gap:3}}>
                  {m.tools.map((t,j)=>(
                    <div key={j} style={{display:'flex',alignItems:'center',gap:6,fontSize:10.5,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)'}}>
                      <Icon name="check" size={10} color="var(--ap-mint)" strokeWidth={2.5}/> {t}
                    </div>
                  ))}
                </div>
              )}
              <div style={{background:'var(--ap-bg-2)',border:'1px solid var(--ap-line-soft)',borderRadius:'12px 12px 12px 4px',padding:'11px 14px',fontSize:13,lineHeight:1.6,color:'var(--ap-fg-1)',whiteSpace:'pre-line'}}>
                {m.text}
              </div>
              {m.action && (
                <button style={{alignSelf:'flex-start',padding:'7px 14px',borderRadius:8,border:'1px solid var(--ap-violet)',background:'var(--ap-violet-soft)',color:'var(--ap-violet)',fontSize:12,fontWeight:600,cursor:'pointer',fontFamily:'inherit'}}>{m.action}</button>
              )}
            </div>
          )
        ))}
        {typing && (
          <div style={{alignSelf:'flex-start',background:'var(--ap-bg-2)',border:'1px solid var(--ap-line-soft)',borderRadius:'12px 12px 12px 4px',padding:'12px 16px',display:'flex',gap:4}}>
            {[0,1,2].map(i=><span key={i} style={{width:5,height:5,borderRadius:'50%',background:'var(--ap-violet)',animation:`apblink 1s ${i*0.18}s infinite`}}/>)}
          </div>
        )}
      </div>

      {/* quick prompts */}
      <div style={{padding:'0 16px 10px',display:'flex',flexWrap:'wrap',gap:6,flexShrink:0}}>
        {QUICK_PROMPTS.map(q=>(
          <div key={q} onClick={()=>ask(q)} style={{fontSize:11,padding:'6px 11px',borderRadius:999,background:'var(--ap-bg-2)',border:'1px solid var(--ap-line-soft)',color:'var(--ap-fg-3)',cursor:'pointer'}}>{q}</div>
        ))}
      </div>

      {/* input */}
      <div style={{padding:'12px 16px 16px',borderTop:'1px solid var(--ap-line-soft)',display:'flex',gap:8,flexShrink:0}}>
        <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==='Enter'&&ask(input)}
          placeholder="问 Pilot AI…"
          style={{flex:1,background:'var(--ap-bg-2)',border:'1px solid var(--ap-line)',borderRadius:10,padding:'10px 13px',color:'var(--ap-fg-1)',fontSize:13,outline:'none',fontFamily:'inherit'}}/>
        <button onClick={()=>ask(input)} style={{width:40,borderRadius:10,border:'none',background:'var(--ap-violet)',color:'#fff',cursor:'pointer',display:'flex',alignItems:'center',justifyContent:'center'}}>
          <Icon name="arrow_up" size={15} strokeWidth={2.2}/>
        </button>
      </div>
    </div>
  );
};

Object.assign(window, { AIChatDrawer });
