// Auth — login / register / 2FA screens (pre-shell, full page)

const AuthInput = ({icon, type='text', value, onChange, placeholder, autoFocus}) => {
  const [focus, setFocus] = React.useState(false);
  const [show, setShow] = React.useState(false);
  const isPw = type==='password';
  return (
    <div style={{position:'relative',display:'flex',alignItems:'center'}}>
      <div style={{position:'absolute',left:13}}><Icon name={icon} size={15} color={focus?'var(--ap-mint)':'var(--ap-fg-4)'}/></div>
      <input type={isPw&&show?'text':type} value={value} onChange={e=>onChange(e.target.value)} placeholder={placeholder} autoFocus={autoFocus}
        onFocus={()=>setFocus(true)} onBlur={()=>setFocus(false)}
        style={{width:'100%',boxSizing:'border-box',background:'var(--ap-bg-2)',border:'1px solid '+(focus?'var(--ap-mint)':'var(--ap-line)'),
          boxShadow:focus?'0 0 0 3px rgba(0,211,149,.1)':'none',borderRadius:11,padding:'13px 14px 13px 40px',paddingRight:isPw?44:14,
          color:'var(--ap-fg-1)',fontSize:14,outline:'none',fontFamily:'inherit',transition:'.12s'}}/>
      {isPw && (
        <div onClick={()=>setShow(s=>!s)} style={{position:'absolute',right:13,cursor:'pointer',display:'flex'}}>
          <Icon name="eye" size={15} color={show?'var(--ap-mint)':'var(--ap-fg-4)'}/>
        </div>
      )}
    </div>
  );
};

const AuthScreen = ({onLogin}) => {
  const [mode, setMode] = React.useState('login'); // login | register | twofa
  const [email, setEmail] = React.useState('');
  const [pw, setPw] = React.useState('');
  const [pw2, setPw2] = React.useState('');
  const [code, setCode] = React.useState(['','','','','','']);
  const codeRefs = React.useRef([]);

  const submit = ()=>{
    if(mode==='login'){ setMode('twofa'); }
    else if(mode==='register'){ setMode('twofa'); }
  };
  const onCode = (i,v)=>{
    if(!/^[0-9]?$/.test(v)) return;
    const next=[...code]; next[i]=v; setCode(next);
    if(v && i<5) codeRefs.current[i+1]?.focus();
    if(next.every(c=>c!=='')) setTimeout(onLogin, 350);
  };

  return (
    <div style={{position:'fixed',inset:0,display:'flex',background:'var(--ap-bg-0)',zIndex:100}}>
      {/* left brand panel */}
      <div style={{flex:1,display:'flex',flexDirection:'column',justifyContent:'space-between',padding:'48px 56px',position:'relative',overflow:'hidden',minWidth:0}}>
        {/* bg grid */}
        <svg style={{position:'absolute',inset:0,width:'100%',height:'100%',opacity:.35}}>
          <defs><pattern id="authgrid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="var(--ap-line-soft)" strokeWidth="1"/></pattern></defs>
          <rect width="100%" height="100%" fill="url(#authgrid)"/>
        </svg>
        <div style={{position:'relative',display:'flex',alignItems:'center',gap:10}}>
          <div style={{width:36,height:36,borderRadius:9,background:'linear-gradient(135deg,var(--ap-mint),var(--ap-violet))',display:'flex',alignItems:'center',justifyContent:'center',color:'var(--ap-bg-0)',fontWeight:800,fontSize:17}}>α</div>
          <span style={{fontSize:17,fontWeight:700}}>Alpha<span style={{color:'var(--ap-mint)'}}>Pilot</span></span>
        </div>
        <div style={{position:'relative',maxWidth:440}}>
          <div style={{fontSize:34,fontWeight:700,letterSpacing:'-.03em',lineHeight:1.25,marginBottom:16}}>AI 自主交易<br/><span style={{color:'var(--ap-mint)'}}>在边界内</span>运行</div>
          <div style={{fontSize:14,color:'var(--ap-fg-3)',lineHeight:1.7}}>结构化决策 · 硬风控守卫 · 执行闭环 · 受控进化。<br/>不是又一个发信号的助手，而是可托付的交易系统。</div>
          <div style={{display:'flex',gap:16,marginTop:28}}>
            {[['248','累计交易'],['57%','胜率'],['1.84','Sharpe'],['−4.2%','最大回撤']].map(([v,l])=>(
              <div key={l}>
                <div style={{fontFamily:'var(--ap-font-mono)',fontSize:20,fontWeight:700,color:'var(--ap-fg-1)'}}>{v}</div>
                <div style={{fontSize:10.5,color:'var(--ap-fg-4)',marginTop:2}}>{l}</div>
              </div>
            ))}
          </div>
        </div>
        <div style={{position:'relative',fontSize:11,color:'var(--ap-fg-5)',fontFamily:'var(--ap-font-mono)'}}>Binance USDT-M · Testnet & Mainnet · v0.1</div>
      </div>

      {/* right form panel */}
      <div style={{width:460,flexShrink:0,background:'var(--ap-bg-1)',borderLeft:'1px solid var(--ap-line)',display:'flex',flexDirection:'column',justifyContent:'center',padding:'0 56px'}}>
        {mode!=='twofa' ? (
          <>
            <div style={{fontSize:22,fontWeight:700,marginBottom:6}}>{mode==='login'?'欢迎回来':'创建账户'}</div>
            <div style={{fontSize:13,color:'var(--ap-fg-3)',marginBottom:28}}>{mode==='login'?'登录以进入你的交易控制台':'注册后需管理员批准并分配角色'}</div>
            <div style={{display:'flex',flexDirection:'column',gap:12}}>
              <AuthInput icon="mail" value={email} onChange={setEmail} placeholder="邮箱" autoFocus/>
              <AuthInput icon="lock" type="password" value={pw} onChange={setPw} placeholder="密码"/>
              {mode==='register' && <AuthInput icon="lock" type="password" value={pw2} onChange={setPw2} placeholder="确认密码"/>}
            </div>
            {mode==='login' && (
              <div style={{textAlign:'right',marginTop:10}}>
                <span style={{fontSize:12,color:'var(--ap-fg-4)',cursor:'pointer'}}>忘记密码？</span>
              </div>
            )}
            <button onClick={submit} style={{marginTop:22,width:'100%',padding:'13px 0',borderRadius:11,border:'none',background:'var(--ap-mint)',color:'var(--ap-bg-0)',fontSize:14,fontWeight:700,cursor:'pointer',fontFamily:'inherit'}}>
              {mode==='login'?'登录':'注册'}
            </button>
            <div style={{display:'flex',alignItems:'center',gap:12,margin:'22px 0'}}>
              <div style={{flex:1,height:1,background:'var(--ap-line-soft)'}}/>
              <span style={{fontSize:11,color:'var(--ap-fg-5)'}}>或</span>
              <div style={{flex:1,height:1,background:'var(--ap-line-soft)'}}/>
            </div>
            <button onClick={onLogin} style={{width:'100%',padding:'12px 0',borderRadius:11,border:'1px solid var(--ap-line)',background:'var(--ap-bg-2)',color:'var(--ap-fg-2)',fontSize:13,fontWeight:600,cursor:'pointer',fontFamily:'inherit'}}>
              以演示账户进入 →
            </button>
            <div style={{textAlign:'center',marginTop:24,fontSize:12.5,color:'var(--ap-fg-4)'}}>
              {mode==='login'?'还没有账户？':'已有账户？'}
              <span onClick={()=>setMode(mode==='login'?'register':'login')} style={{color:'var(--ap-mint)',cursor:'pointer',fontWeight:600,marginLeft:6}}>
                {mode==='login'?'注册':'登录'}
              </span>
            </div>
          </>
        ) : (
          <>
            <div onClick={()=>setMode('login')} style={{display:'flex',alignItems:'center',gap:6,color:'var(--ap-fg-4)',fontSize:12,cursor:'pointer',marginBottom:26}}>
              <span style={{display:'inline-flex',transform:'rotate(180deg)'}}><Icon name="chevron_right" size={12}/></span> 返回
            </div>
            <div style={{width:44,height:44,borderRadius:11,background:'var(--ap-mint-soft)',display:'flex',alignItems:'center',justifyContent:'center',marginBottom:18}}>
              <Icon name="shield" size={20} color="var(--ap-mint)"/>
            </div>
            <div style={{fontSize:22,fontWeight:700,marginBottom:6}}>双重验证</div>
            <div style={{fontSize:13,color:'var(--ap-fg-3)',marginBottom:26}}>输入验证器 App 中的 6 位动态码<br/><span style={{fontFamily:'var(--ap-font-mono)',fontSize:11,color:'var(--ap-fg-4)'}}>演示提示：输入任意 6 位数字</span></div>
            <div style={{display:'flex',gap:10,marginBottom:24}}>
              {code.map((c,i)=>(
                <input key={i} ref={el=>codeRefs.current[i]=el} value={c} onChange={e=>onCode(i,e.target.value)} autoFocus={i===0}
                  maxLength={1} inputMode="numeric"
                  style={{width:48,height:56,textAlign:'center',fontSize:22,fontWeight:700,fontFamily:'var(--ap-font-mono)',
                    background:'var(--ap-bg-2)',border:'1px solid '+(c?'var(--ap-mint)':'var(--ap-line)'),borderRadius:11,color:'var(--ap-fg-1)',outline:'none'}}/>
              ))}
            </div>
            <div style={{fontSize:12,color:'var(--ap-fg-4)'}}>收不到验证码？<span style={{color:'var(--ap-mint)',cursor:'pointer',fontWeight:600}}>使用恢复码</span></div>
          </>
        )}
      </div>
    </div>
  );
};

Object.assign(window, { AuthScreen });
