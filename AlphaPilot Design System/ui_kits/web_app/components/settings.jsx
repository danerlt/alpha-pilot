// Settings — Exchange (mainnet/testnet + API keys) · LLM · Notifications · Account
// Uses W_MOCK atoms (WCard, WPill, WDot, Icon, wfmt...) from shell.jsx

// ---------- form atoms ----------
const SField = ({label, hint, children, htmlFor}) => (
  <div style={{display:'flex',flexDirection:'column',gap:6,marginBottom:14}}>
    <label htmlFor={htmlFor} style={{fontSize:11,color:'var(--ap-fg-3)',letterSpacing:'.04em',fontWeight:600,display:'flex',alignItems:'center',gap:8,flexWrap:'wrap',lineHeight:1.5}}>
      {label}{hint && <span style={{fontWeight:400,color:'var(--ap-fg-4)',letterSpacing:0}}>{hint}</span>}
    </label>
    {children}
  </div>
);

const SInput = ({value, onChange, placeholder, mono=true, type='text', id, right}) => {
  const [focus, setFocus] = React.useState(false);
  return (
    <div style={{position:'relative',display:'flex',alignItems:'center'}}>
      <input id={id} type={type} value={value} onChange={e=>onChange?.(e.target.value)} placeholder={placeholder}
        onFocus={()=>setFocus(true)} onBlur={()=>setFocus(false)}
        style={{width:'100%',boxSizing:'border-box',background:'var(--ap-bg-3)',border:'1px solid '+(focus?'var(--ap-mint)':'var(--ap-line)'),
          boxShadow: focus?'0 0 0 3px rgba(0,211,149,.12)':'none',borderRadius:10,padding:'11px 13px',paddingRight: right?78:13,
          color:'var(--ap-fg-1)',fontSize:13,fontFamily: mono?'var(--ap-font-mono)':'inherit',outline:'none',transition:'.12s'}}/>
      {right && <div style={{position:'absolute',right:8}}>{right}</div>}
    </div>
  );
};

const SMasked = ({value, onChange, placeholder, id}) => {
  const [show, setShow] = React.useState(false);
  return (
    <SInput id={id} value={value} onChange={onChange} placeholder={placeholder} type={show?'text':'password'}
      right={<button onClick={()=>setShow(s=>!s)} style={{background:'var(--ap-bg-4)',border:'1px solid var(--ap-line)',borderRadius:6,padding:'4px 8px',color:'var(--ap-fg-3)',fontSize:10,cursor:'pointer',fontFamily:'var(--ap-font-mono)'}}>{show?'隐藏':'显示'}</button>}/>
  );
};

const SSwitch = ({on, onToggle}) => (
  <div onClick={onToggle} role="switch" aria-checked={on} tabIndex={0}
    style={{width:42,height:24,borderRadius:999,background:on?'var(--ap-mint)':'var(--ap-bg-4)',position:'relative',cursor:'pointer',flexShrink:0,transition:'.15s'}}>
    <div style={{position:'absolute',top:3,left:on?21:3,width:18,height:18,background:'#fff',borderRadius:'50%',transition:'.15s'}}/>
  </div>
);

const SSeg = ({options, value, onChange}) => (
  <div style={{display:'inline-flex',background:'var(--ap-bg-3)',borderRadius:9,padding:3,border:'1px solid var(--ap-line)'}}>
    {options.map(o=>(
      <div key={o.v} onClick={()=>onChange(o.v)} style={{display:'flex',alignItems:'center',gap:6,fontSize:12,padding:'6px 14px',borderRadius:6,cursor:'pointer',fontWeight:500,
        background:value===o.v?'var(--ap-bg-4)':'transparent',color:value===o.v?'var(--ap-fg-1)':'var(--ap-fg-3)',transition:'.12s'}}>
        {o.dot && <WDot c={o.dot} glow={value===o.v}/>}{o.l}
      </div>
    ))}
  </div>
);

const SSelect = ({value, onChange, options, id}) => (
  <div style={{position:'relative'}}>
    <select id={id} value={value} onChange={e=>onChange(e.target.value)}
      style={{width:'100%',appearance:'none',background:'var(--ap-bg-3)',border:'1px solid var(--ap-line)',borderRadius:10,padding:'11px 36px 11px 13px',color:'var(--ap-fg-1)',fontSize:13,fontFamily:'inherit',outline:'none',cursor:'pointer'}}>
      {options.map(o=><option key={o.v} value={o.v} style={{background:'var(--ap-bg-2)'}}>{o.l}</option>)}
    </select>
    <div style={{position:'absolute',right:12,top:'50%',transform:'translateY(-50%)',pointerEvents:'none'}}><Icon name="chevron_down" size={14} color="var(--ap-fg-3)"/></div>
  </div>
);

const STestBtn = ({onTest, state}) => {
  // state: idle | testing | ok | fail
  const cfg = {
    idle:{l:'测试连接',bg:'var(--ap-bg-4)',c:'var(--ap-fg-1)',bd:'var(--ap-line)'},
    testing:{l:'测试中…',bg:'var(--ap-bg-4)',c:'var(--ap-fg-3)',bd:'var(--ap-line)'},
    ok:{l:'连接成功',bg:'var(--ap-mint-soft)',c:'var(--ap-mint)',bd:'var(--ap-mint)'},
    fail:{l:'连接失败',bg:'var(--ap-rose-soft)',c:'var(--ap-rose)',bd:'var(--ap-rose)'},
  }[state];
  return (
    <button onClick={onTest} disabled={state==='testing'} style={{display:'flex',alignItems:'center',gap:6,padding:'9px 16px',borderRadius:9,border:`1px solid ${cfg.bd}`,background:cfg.bg,color:cfg.c,fontSize:12,fontWeight:600,cursor:state==='testing'?'default':'pointer',fontFamily:'inherit'}}>
      {state==='ok' && <Icon name="check" size={13} strokeWidth={2.4}/>}
      {state==='fail' && <Icon name="x" size={13} strokeWidth={2.4}/>}
      {state==='testing' && <span style={{width:6,height:6,borderRadius:'50%',background:'currentColor',animation:'apblink 1s infinite'}}/>}
      {cfg.l}
    </button>
  );
};

// ---------- main page ----------
const WSettingsPage = () => {
  const [tab, setTab] = React.useState('exchange');
  const tabs = [
    {id:'exchange', label:'交易所连接', icon:'layers'},
    {id:'llm', label:'AI 模型', icon:'brain'},
    {id:'notify', label:'通知', icon:'bell'},
    {id:'account', label:'账户偏好', icon:'settings'},
  ];
  return (
    <div style={{display:'flex',gap:24,maxWidth:1000}}>
      {/* sub-nav */}
      <div style={{width:200,flexShrink:0,display:'flex',flexDirection:'column',gap:2}}>
        {tabs.map(t=>(
          <div key={t.id} onClick={()=>setTab(t.id)} style={{display:'flex',alignItems:'center',gap:10,padding:'10px 12px',borderRadius:9,cursor:'pointer',
            background:tab===t.id?'var(--ap-bg-2)':'transparent',color:tab===t.id?'var(--ap-fg-1)':'var(--ap-fg-3)',fontSize:13,fontWeight:500,border:'1px solid '+(tab===t.id?'var(--ap-line-soft)':'transparent')}}>
            <Icon name={t.icon} size={15} color={tab===t.id?'var(--ap-mint)':'currentColor'}/>{t.label}
          </div>
        ))}
      </div>
      {/* content */}
      <div style={{flex:1,minWidth:0,display:'flex',flexDirection:'column',gap:20}}>
        {tab==='exchange' && <ExchangeSettings/>}
        {tab==='llm' && <LLMSettings/>}
        {tab==='notify' && <NotifySettings/>}
        {tab==='account' && <AccountSettings/>}
      </div>
    </div>
  );
};

// ---------- Exchange ----------
const ExchangeSettings = () => {
  const [net, setNet] = React.useState('mainnet');
  const [test, setTest] = React.useState('ok');
  const [key, setKey] = React.useState('bnx_live_8a3f2c91d4e7');
  const [secret, setSecret] = React.useState('••••••••••••••••3f2a');
  const runTest = ()=>{ setTest('testing'); setTimeout(()=>setTest('ok'), 1200); };
  const isTestnet = net==='testnet';
  return (
    <>
      {/* exchange selector */}
      <WCard title="交易所">
        <div style={{display:'flex',gap:12}}>
          {[
            {id:'binance', name:'Binance', logo:'../../assets/binance_logo.svg', sub:'USDT-M 永续 · MVP 首选', active:true},
            {id:'hyperliquid', name:'Hyperliquid', logo:'../../assets/hyperliquid_logo.svg', sub:'去中心化 · 钱包授权', active:false},
          ].map(ex=>(
            <div key={ex.id} style={{flex:1,padding:16,borderRadius:12,background:'var(--ap-bg-3)',border:'1px solid '+(ex.active?'var(--ap-mint)':'var(--ap-line-soft)'),position:'relative',cursor:'pointer'}}>
              {ex.active && <div style={{position:'absolute',top:12,right:12}}><WPill tone="mint">已连接</WPill></div>}
              <img src={ex.logo} style={{width:28,height:28,marginBottom:10}}/>
              <div style={{fontSize:14,fontWeight:600,marginBottom:2}}>{ex.name}</div>
              <div style={{fontSize:11,color:'var(--ap-fg-3)'}}>{ex.sub}</div>
            </div>
          ))}
        </div>
      </WCard>

      {/* network + API */}
      <WCard title="Binance · 网络与 API" right={<STestBtn onTest={runTest} state={test}/>}>
        {/* mainnet/testnet */}
        <SField label="运行网络" hint={isTestnet?'· 测试盘使用模拟资金，安全演练':'· 主网为真实资金交易，请谨慎'}>
          <SSeg value={net} onChange={(v)=>{setNet(v);setTest('idle');}} options={[
            {v:'mainnet', l:'主网 Mainnet', dot:'var(--ap-rose)'},
            {v:'testnet', l:'测试网 Testnet', dot:'var(--ap-cyan)'},
          ]}/>
        </SField>

        {isTestnet && (
          <div style={{display:'flex',gap:8,alignItems:'flex-start',padding:'10px 12px',background:'var(--ap-cyan-soft)',borderRadius:8,marginBottom:14,border:'1px solid rgba(34,211,238,.2)'}}>
            <Icon name="alert" size={14} color="var(--ap-cyan)"/>
            <span style={{fontSize:11,color:'var(--ap-fg-2)',lineHeight:1.5}}>当前为 <b style={{color:'var(--ap-cyan)'}}>测试网</b>。所有成交为模拟，不涉及真实资金。建议先在测试网验证策略，再切主网。</span>
          </div>
        )}
        {!isTestnet && (
          <div style={{display:'flex',gap:8,alignItems:'flex-start',padding:'10px 12px',background:'var(--ap-rose-soft)',borderRadius:8,marginBottom:14,border:'1px solid rgba(255,77,109,.2)'}}>
            <Icon name="alert" size={14} color="var(--ap-rose)"/>
            <span style={{fontSize:11,color:'var(--ap-fg-2)',lineHeight:1.5}}>当前为 <b style={{color:'var(--ap-rose)'}}>主网</b>，AI 将使用真实资金下单。请确认 API 仅开启「合约交易」权限，<b>切勿</b>开启「提现」权限。</span>
          </div>
        )}

        <SField label="API Key" htmlFor="bn-key"><SInput id="bn-key" value={key} onChange={setKey} placeholder="输入 Binance API Key"/></SField>
        <SField label="API Secret" htmlFor="bn-sec"><SMasked id="bn-sec" value={secret} onChange={setSecret} placeholder="输入 Binance API Secret"/></SField>

        {/* permissions checklist */}
        <SField label="权限校验" hint="· 自动检测 API 权限范围">
          <div style={{display:'flex',flexDirection:'column',gap:6}}>
            {[
              {l:'读取账户与持仓', ok:true},
              {l:'合约交易（下单/撤单）', ok:true},
              {l:'提现权限', ok:false, want:false},
            ].map((p,i)=>(
              <div key={i} style={{display:'flex',alignItems:'center',gap:8,padding:'8px 12px',background:'var(--ap-bg-3)',borderRadius:8,fontSize:12}}>
                {p.want===false
                  ? <span style={{width:16,height:16,borderRadius:4,background:p.ok?'var(--ap-rose-soft)':'var(--ap-mint-soft)',display:'flex',alignItems:'center',justifyContent:'center'}}><Icon name={p.ok?'alert':'check'} size={11} color={p.ok?'var(--ap-rose)':'var(--ap-mint)'} strokeWidth={2.6}/></span>
                  : <span style={{width:16,height:16,borderRadius:4,background:p.ok?'var(--ap-mint-soft)':'var(--ap-bg-4)',display:'flex',alignItems:'center',justifyContent:'center'}}><Icon name="check" size={11} color={p.ok?'var(--ap-mint)':'var(--ap-fg-4)'} strokeWidth={2.6}/></span>}
                <span style={{flex:1,color: p.want===false&&p.ok?'var(--ap-rose)':'var(--ap-fg-2)'}}>{p.l}</span>
                {p.want===false && p.ok && <span style={{fontSize:10,color:'var(--ap-rose)',fontFamily:'var(--ap-font-mono)'}}>建议关闭</span>}
                {p.want===false && !p.ok && <span style={{fontSize:10,color:'var(--ap-mint)',fontFamily:'var(--ap-font-mono)'}}>已关闭 ✓</span>}
              </div>
            ))}
          </div>
        </SField>

        <div style={{display:'flex',gap:8,marginTop:6}}>
          <button style={{padding:'10px 18px',borderRadius:10,border:'none',background:'var(--ap-mint)',color:'var(--ap-bg-0)',fontSize:13,fontWeight:700,cursor:'pointer',fontFamily:'inherit'}}>保存配置</button>
          <button style={{padding:'10px 18px',borderRadius:10,border:'1px solid var(--ap-line)',background:'var(--ap-bg-3)',color:'var(--ap-fg-2)',fontSize:13,fontWeight:500,cursor:'pointer',fontFamily:'inherit'}}>断开连接</button>
        </div>
      </WCard>
    </>
  );
};

// ---------- LLM ----------
const LLMSettings = () => {
  const [provider, setProvider] = React.useState('deepseek');
  const [test, setTest] = React.useState('idle');
  const [temp, setTemp] = React.useState(0.3);
  const [key, setKey] = React.useState('sk-••••••••••••••••a1b2');
  const runTest = ()=>{ setTest('testing'); setTimeout(()=>setTest('ok'), 1100); };

  const providers = {
    deepseek:  {models:['deepseek-chat','deepseek-reasoner'], base:'https://api.deepseek.com/v1', rec:true},
    openai:    {models:['gpt-5','o1','gpt-4o','gpt-4-turbo'], base:'https://api.openai.com/v1'},
    anthropic: {models:['claude-sonnet-4.5','claude-opus-4.1'], base:'https://api.anthropic.com/v1'},
    custom:    {models:['custom-model'], base:'https://your-endpoint/v1'},
  };
  const [model, setModel] = React.useState('deepseek-chat');
  const cur = providers[provider];

  return (
    <>
      <WCard title="模型提供方">
        <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:10,marginBottom:4}}>
          {[
            {id:'deepseek', l:'Deepseek', sub:'性价比首选'},
            {id:'openai', l:'OpenAI', sub:'GPT-5 / o1'},
            {id:'anthropic', l:'Anthropic', sub:'Claude'},
            {id:'custom', l:'自定义', sub:'兼容 OpenAI'},
          ].map(p=>(
            <div key={p.id} onClick={()=>{setProvider(p.id);setModel(providers[p.id].models[0]);setTest('idle');}}
              style={{padding:'12px 14px',borderRadius:10,background:'var(--ap-bg-3)',border:'1px solid '+(provider===p.id?'var(--ap-violet)':'var(--ap-line-soft)'),cursor:'pointer',position:'relative'}}>
              {providers[p.id].rec && <div style={{position:'absolute',top:8,right:8}}><WPill tone="violet">推荐</WPill></div>}
              <div style={{fontSize:13,fontWeight:600,marginBottom:2}}>{p.l}</div>
              <div style={{fontSize:10.5,color:'var(--ap-fg-3)'}}>{p.sub}</div>
            </div>
          ))}
        </div>
      </WCard>

      <WCard title="模型配置" right={<STestBtn onTest={runTest} state={test}/>}>
        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14}}>
          <SField label="模型"><SSelect value={model} onChange={setModel} options={cur.models.map(m=>({v:m,l:m}))}/></SField>
          <SField label="API Base URL"><SInput value={cur.base} onChange={()=>{}} mono/></SField>
        </div>
        <SField label="API Key" htmlFor="llm-key"><SMasked id="llm-key" value={key} onChange={setKey} placeholder="sk-..."/></SField>

        <SField label={`温度 · ${temp.toFixed(2)}`} hint="· 越低越确定，交易决策建议 0.2–0.4">
          <div style={{display:'flex',alignItems:'center',gap:14}}>
            <input type="range" min="0" max="1" step="0.05" value={temp} onChange={e=>setTemp(parseFloat(e.target.value))}
              style={{flex:1,accentColor:'var(--ap-violet)'}}/>
            <span style={{fontFamily:'var(--ap-font-mono)',fontSize:13,color:'var(--ap-violet)',fontWeight:600,width:40,textAlign:'right'}}>{temp.toFixed(2)}</span>
          </div>
        </SField>

        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14}}>
          <SField label="最大 Token" hint=""><SInput value="4096" onChange={()=>{}} mono/></SField>
          <SField label="超时 (秒)" hint=""><SInput value="30" onChange={()=>{}} mono/></SField>
        </div>

        <div style={{display:'flex',gap:8,marginTop:6}}>
          <button style={{padding:'10px 18px',borderRadius:10,border:'none',background:'var(--ap-violet)',color:'#fff',fontSize:13,fontWeight:700,cursor:'pointer',fontFamily:'inherit'}}>保存模型配置</button>
        </div>
      </WCard>

      <WCard title="Agent 模型分工" right={<span style={{fontSize:11,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>可分别指定</span>}>
        {[
          {a:'决策 Agent', m:'deepseek-reasoner', desc:'交易决策推理'},
          {a:'信号 Agent', m:'deepseek-chat', desc:'市场信号识别'},
          {a:'复盘 Agent', m:'deepseek-chat', desc:'归因与诊断'},
        ].map((r,i,arr)=>(
          <div key={i} style={{display:'flex',alignItems:'center',gap:12,padding:'11px 0',borderBottom:i<arr.length-1?'1px solid var(--ap-line-soft)':'none'}}>
            <div style={{width:30,height:30,borderRadius:8,background:'var(--ap-violet-soft)',display:'flex',alignItems:'center',justifyContent:'center'}}><Icon name="brain" size={15} color="var(--ap-violet)"/></div>
            <div style={{flex:1}}>
              <div style={{fontSize:13,fontWeight:600}}>{r.a}</div>
              <div style={{fontSize:11,color:'var(--ap-fg-3)'}}>{r.desc}</div>
            </div>
            <WPill tone="default">{r.m}</WPill>
          </div>
        ))}
      </WCard>
    </>
  );
};

// ---------- Notifications ----------
const NotifySettings = () => {
  const [tg, setTg] = React.useState(true);
  const [dc, setDc] = React.useState(false);
  const [events, setEvents] = React.useState({open:true, close:true, halt:true, reject:false, daily:true});
  const toggle = k => setEvents(e=>({...e,[k]:!e[k]}));
  return (
    <>
      <WCard title="推送渠道">
        <div style={{display:'flex',alignItems:'center',gap:12,padding:'11px 0',borderBottom:'1px solid var(--ap-line-soft)'}}>
          <div style={{width:32,height:32,borderRadius:8,background:'var(--ap-cyan-soft)',display:'flex',alignItems:'center',justifyContent:'center'}}><Icon name="bell" size={16} color="var(--ap-cyan)"/></div>
          <div style={{flex:1}}><div style={{fontSize:13,fontWeight:600}}>Telegram</div><div style={{fontSize:11,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>@alphapilot_bot · 已绑定</div></div>
          <SSwitch on={tg} onToggle={()=>setTg(!tg)}/>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:12,padding:'11px 0'}}>
          <div style={{width:32,height:32,borderRadius:8,background:'var(--ap-violet-soft)',display:'flex',alignItems:'center',justifyContent:'center'}}><Icon name="bell" size={16} color="var(--ap-violet)"/></div>
          <div style={{flex:1}}><div style={{fontSize:13,fontWeight:600}}>Discord</div><div style={{fontSize:11,color:'var(--ap-fg-3)'}}>未绑定</div></div>
          <SSwitch on={dc} onToggle={()=>setDc(!dc)}/>
        </div>
      </WCard>

      <WCard title="推送事件">
        {[
          {k:'open', l:'开仓成交', d:'AI 开仓并成交时'},
          {k:'close', l:'平仓成交', d:'止盈/止损/手动平仓'},
          {k:'halt', l:'熔断触发', d:'日亏/连亏触发熔断（强烈建议开启）', warn:true},
          {k:'reject', l:'守卫拦截', d:'决策被守卫拒绝时'},
          {k:'daily', l:'每日报告', d:'每日收盘 AI 日报'},
        ].map((e,i,arr)=>(
          <div key={e.k} style={{display:'flex',alignItems:'center',gap:12,padding:'11px 0',borderBottom:i<arr.length-1?'1px solid var(--ap-line-soft)':'none'}}>
            <div style={{flex:1}}>
              <div style={{fontSize:13,fontWeight:500,display:'flex',alignItems:'center',gap:8}}>{e.l}{e.warn && <WPill tone="rose">关键</WPill>}</div>
              <div style={{fontSize:11,color:'var(--ap-fg-3)',marginTop:2}}>{e.d}</div>
            </div>
            <SSwitch on={events[e.k]} onToggle={()=>toggle(e.k)}/>
          </div>
        ))}
      </WCard>
    </>
  );
};

// ---------- Account ----------
const AccountSettings = () => {
  const [lang, setLang] = React.useState('zh');
  const [tz, setTz] = React.useState('utc8');
  const [twofa, setTwofa] = React.useState(true);
  return (
    <>
      <WCard title="偏好">
        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14}}>
          <SField label="界面语言"><SSeg value={lang} onChange={setLang} options={[{v:'zh',l:'中文'},{v:'en',l:'English'}]}/></SField>
          <SField label="时区"><SSelect value={tz} onChange={setTz} options={[{v:'utc8',l:'UTC+8 北京'},{v:'utc0',l:'UTC 世界时'},{v:'utc-5',l:'UTC-5 纽约'}]}/></SField>
        </div>
      </WCard>
      <WCard title="安全">
        <div style={{display:'flex',alignItems:'center',gap:12,padding:'11px 0',borderBottom:'1px solid var(--ap-line-soft)'}}>
          <div style={{flex:1}}><div style={{fontSize:13,fontWeight:500}}>双重验证 2FA</div><div style={{fontSize:11,color:'var(--ap-fg-3)'}}>登录与提现操作需二次验证</div></div>
          <WPill tone="mint">已启用</WPill><SSwitch on={twofa} onToggle={()=>setTwofa(!twofa)}/>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:12,padding:'11px 0'}}>
          <div style={{flex:1}}><div style={{fontSize:13,fontWeight:500}}>会话与设备</div><div style={{fontSize:11,color:'var(--ap-fg-3)',fontFamily:'var(--ap-font-mono)'}}>2 个活跃会话</div></div>
          <button style={{padding:'7px 14px',borderRadius:8,border:'1px solid var(--ap-line)',background:'var(--ap-bg-3)',color:'var(--ap-fg-2)',fontSize:12,cursor:'pointer',fontFamily:'inherit'}}>管理</button>
        </div>
      </WCard>
      <WCard title="危险区" style={{borderColor:'rgba(255,77,109,.25)'}}>
        <div style={{display:'flex',alignItems:'center',gap:12}}>
          <div style={{flex:1}}><div style={{fontSize:13,fontWeight:500,color:'var(--ap-rose)'}}>清空所有持仓并停止引擎</div><div style={{fontSize:11,color:'var(--ap-fg-3)'}}>立即市价平掉所有仓位并暂停自动交易</div></div>
          <button style={{padding:'9px 16px',borderRadius:9,border:'1px solid var(--ap-rose)',background:'var(--ap-rose-soft)',color:'var(--ap-rose)',fontSize:12,fontWeight:600,cursor:'pointer',fontFamily:'inherit'}}>紧急停止</button>
        </div>
      </WCard>
    </>
  );
};

Object.assign(window, { WSettingsPage });
