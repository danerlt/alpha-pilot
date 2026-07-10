// Admin console — 用户管理 · 角色权限 · 管理操作日志

const ADMIN_USERS = [
  {name:'Daner Li', email:'daner@alphapilot.io', role:'owner', status:'active', last:'刚刚', twofa:true, self:true},
  {name:'Wei Zhang', email:'wei.z@alphapilot.io', role:'admin', status:'active', last:'2 小时前', twofa:true},
  {name:'Ming Chen', email:'ming.c@alphapilot.io', role:'trader', status:'active', last:'昨天 22:41', twofa:true},
  {name:'Lu Wang', email:'lu.w@alphapilot.io', role:'viewer', status:'active', last:'3 天前', twofa:false},
  {name:'Hao Sun', email:'hao.s@gmail.com', role:'viewer', status:'pending', last:'—', twofa:false},
  {name:'Jing Liu', email:'jing.l@alphapilot.io', role:'trader', status:'disabled', last:'06-12', twofa:true},
];

const ROLES = {
  owner:  {l:'Owner',  tone:'violet', desc:'所有权限 + 转让所有权'},
  admin:  {l:'Admin',  tone:'rose',   desc:'用户/权限/系统配置管理'},
  trader: {l:'Trader', tone:'mint',   desc:'交易操作与策略管理'},
  viewer: {l:'Viewer', tone:'cyan',   desc:'只读访问'},
};

const PERMS = [
  {group:'交易', items:[
    {k:'查看持仓与行情', owner:1,admin:1,trader:1,viewer:1},
    {k:'手动下单 / 平仓', owner:1,admin:1,trader:1,viewer:0},
    {k:'启停自动交易', owner:1,admin:1,trader:1,viewer:0},
    {k:'修改硬风控阈值', owner:1,admin:1,trader:0,viewer:0},
  ]},
  {group:'策略', items:[
    {k:'查看策略与实验室', owner:1,admin:1,trader:1,viewer:1},
    {k:'提交策略候选', owner:1,admin:1,trader:1,viewer:0},
    {k:'批准灰度 / 上线', owner:1,admin:1,trader:0,viewer:0},
  ]},
  {group:'系统', items:[
    {k:'交易所 API 配置', owner:1,admin:1,trader:0,viewer:0},
    {k:'LLM 模型配置', owner:1,admin:1,trader:0,viewer:0},
    {k:'用户与权限管理', owner:1,admin:1,trader:0,viewer:0},
    {k:'紧急停止引擎', owner:1,admin:1,trader:1,viewer:0},
  ]},
];

const ADMIN_LOG = [
  {t:'07-03 09:12', who:'Daner Li', act:'修改硬风控 · 日亏损熔断 −2.00% → −1.50%', kind:'risk'},
  {t:'07-02 18:40', who:'Wei Zhang', act:'批准策略上线 · 趋势跟随 v2.0', kind:'strategy'},
  {t:'07-02 15:03', who:'Daner Li', act:'邀请用户 hao.s@gmail.com（Viewer）', kind:'user'},
  {t:'07-01 11:27', who:'Wei Zhang', act:'停用账户 Jing Liu', kind:'user'},
  {t:'06-30 20:15', who:'Daner Li', act:'更换 Binance API Key（主网）', kind:'system'},
  {t:'06-30 09:00', who:'system', act:'自动回滚 · 均值回归 v0.4 灰度回撤超限', kind:'strategy'},
];

const StatusPill = ({s}) => (
  <WPill tone={s==='active'?'mint':s==='pending'?'amber':'default'}>{s==='active'?'活跃':s==='pending'?'待批准':'已停用'}</WPill>
);

const Avatar = ({name, size=30}) => {
  const hue = (name.charCodeAt(0)*37)%360;
  return (
    <div style={{width:size,height:size,borderRadius:'50%',flexShrink:0,display:'flex',alignItems:'center',justifyContent:'center',
      background:`oklch(0.45 0.09 ${hue})`,color:'#fff',fontSize:size*0.38,fontWeight:700}}>
      {name.split(' ').map(w=>w[0]).join('')}
    </div>
  );
};

// ---------- 用户管理 ----------
const UsersTab = () => {
  const [users, setUsers] = React.useState(ADMIN_USERS);
  const approve = (email)=> setUsers(us=>us.map(u=>u.email===email?{...u,status:'active'}:u));
  return (
    <>
      <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12}}>
        <WCard dense><WStat label="总用户" value={users.length} size="sm"/></WCard>
        <WCard dense><WStat label="活跃" value={users.filter(u=>u.status==='active').length} size="sm" tone="pos"/></WCard>
        <WCard dense><WStat label="待批准" value={users.filter(u=>u.status==='pending').length} size="sm"/></WCard>
        <WCard dense><WStat label="2FA 覆盖" value={Math.round(users.filter(u=>u.twofa).length/users.length*100)+'%'} size="sm"/></WCard>
      </div>
      <WCard title="用户" right={
        <button style={{display:'flex',alignItems:'center',gap:6,padding:'6px 13px',borderRadius:8,border:'none',background:'var(--ap-mint)',color:'var(--ap-bg-0)',fontSize:12,fontWeight:700,cursor:'pointer',fontFamily:'inherit'}}>
          + 邀请用户
        </button>
      }>
        <div style={{margin:'-16px -18px'}}>
          <table style={{width:'100%',borderCollapse:'collapse',fontSize:12.5}}>
            <thead>
              <tr style={{borderBottom:'1px solid var(--ap-line)'}}>
                {['用户','角色','状态','2FA','最近活跃','操作'].map(h=>(
                  <th key={h} style={{padding:'10px 14px',textAlign:'left',fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.06em',textTransform:'uppercase',fontWeight:500}}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u,i)=>(
                <tr key={i} style={{borderBottom:'1px solid var(--ap-line-soft)',opacity:u.status==='disabled'?0.55:1}}>
                  <td style={{padding:'11px 14px'}}>
                    <div style={{display:'flex',alignItems:'center',gap:10}}>
                      <Avatar name={u.name}/>
                      <div>
                        <div style={{fontWeight:600,display:'flex',alignItems:'center',gap:6}}>{u.name}{u.self && <span style={{fontSize:10,color:'var(--ap-fg-4)'}}>（你）</span>}</div>
                        <div style={{fontSize:11,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)'}}>{u.email}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{padding:'11px 14px'}}><WPill tone={ROLES[u.role].tone}>{ROLES[u.role].l}</WPill></td>
                  <td style={{padding:'11px 14px'}}><StatusPill s={u.status}/></td>
                  <td style={{padding:'11px 14px'}}>
                    {u.twofa
                      ? <Icon name="check" size={14} color="var(--ap-mint)" strokeWidth={2.4}/>
                      : <Icon name="x" size={14} color="var(--ap-fg-4)" strokeWidth={2.4}/>}
                  </td>
                  <td style={{padding:'11px 14px',fontFamily:'var(--ap-font-mono)',fontSize:11,color:'var(--ap-fg-3)'}}>{u.last}</td>
                  <td style={{padding:'11px 14px'}}>
                    <div style={{display:'flex',gap:6}}>
                      {u.status==='pending' ? (
                        <>
                          <button onClick={()=>approve(u.email)} style={{padding:'4px 11px',borderRadius:6,border:'none',background:'var(--ap-mint)',color:'var(--ap-bg-0)',fontSize:11,fontWeight:700,cursor:'pointer',fontFamily:'inherit'}}>批准</button>
                          <button style={{padding:'4px 11px',borderRadius:6,border:'1px solid var(--ap-line)',background:'transparent',color:'var(--ap-fg-3)',fontSize:11,cursor:'pointer',fontFamily:'inherit'}}>拒绝</button>
                        </>
                      ) : !u.self && (
                        <>
                          <button style={{padding:'4px 11px',borderRadius:6,border:'1px solid var(--ap-line)',background:'var(--ap-bg-3)',color:'var(--ap-fg-2)',fontSize:11,cursor:'pointer',fontFamily:'inherit'}}>编辑</button>
                          <button style={{padding:'4px 11px',borderRadius:6,border:'1px solid rgba(255,77,109,.35)',background:'transparent',color:'var(--ap-rose)',fontSize:11,cursor:'pointer',fontFamily:'inherit'}}>{u.status==='disabled'?'启用':'停用'}</button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </WCard>
    </>
  );
};

// ---------- 角色权限 ----------
const RolesTab = () => (
  <>
    <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12}}>
      {Object.entries(ROLES).map(([k,r])=>(
        <WCard key={k} dense>
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:6}}>
            <WPill tone={r.tone}>{r.l}</WPill>
            <span style={{fontSize:11,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)'}}>{ADMIN_USERS.filter(u=>u.role===k).length} 人</span>
          </div>
          <div style={{fontSize:11.5,color:'var(--ap-fg-3)',lineHeight:1.5}}>{r.desc}</div>
        </WCard>
      ))}
    </div>
    <WCard title="权限矩阵" right={<span style={{fontSize:10.5,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)'}}>Owner 权限不可修改</span>}>
      <div style={{margin:'-16px -18px'}}>
        <table style={{width:'100%',borderCollapse:'collapse',fontSize:12.5}}>
          <thead>
            <tr style={{borderBottom:'1px solid var(--ap-line)'}}>
              <th style={{padding:'10px 14px',textAlign:'left',fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.06em',textTransform:'uppercase',fontWeight:500}}>权限</th>
              {Object.values(ROLES).map(r=>(
                <th key={r.l} style={{padding:'10px 14px',textAlign:'center',fontSize:10,letterSpacing:'.06em',textTransform:'uppercase',fontWeight:600,color:'var(--ap-fg-2)'}}>{r.l}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PERMS.map(g=>(
              <React.Fragment key={g.group}>
                <tr style={{background:'var(--ap-bg-3)'}}>
                  <td colSpan={5} style={{padding:'7px 14px',fontSize:10,color:'var(--ap-fg-3)',letterSpacing:'.08em',fontWeight:700}}>{g.group}</td>
                </tr>
                {g.items.map((p,i)=>(
                  <tr key={i} style={{borderBottom:'1px solid var(--ap-line-soft)'}}>
                    <td style={{padding:'9px 14px',color:'var(--ap-fg-2)'}}>{p.k}</td>
                    {['owner','admin','trader','viewer'].map(role=>(
                      <td key={role} style={{padding:'9px 14px',textAlign:'center'}}>
                        <div style={{display:'inline-flex',width:18,height:18,borderRadius:5,alignItems:'center',justifyContent:'center',
                          cursor: role==='owner'?'not-allowed':'pointer',
                          background: p[role]?'var(--ap-mint-soft)':'var(--ap-bg-3)',
                          border:'1px solid '+(p[role]?'rgba(0,211,149,.4)':'var(--ap-line)')}}>
                          {p[role]?<Icon name="check" size={11} color="var(--ap-mint)" strokeWidth={2.8}/>:null}
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </WCard>
  </>
);

// ---------- 管理日志 ----------
const AdminLogTab = () => (
  <WCard title="管理操作日志" right={
    <div style={{display:'flex',gap:6}}>
      {['全部','用户','风控','策略','系统'].map((t,i)=>(
        <span key={t} style={{padding:'4px 10px',fontSize:11,background:i===0?'var(--ap-bg-4)':'var(--ap-bg-3)',border:'1px solid var(--ap-line-soft)',borderRadius:6,cursor:'pointer',color:i===0?'var(--ap-fg-1)':'var(--ap-fg-3)'}}>{t}</span>
      ))}
    </div>
  }>
    {ADMIN_LOG.map((l,i)=>(
      <div key={i} style={{display:'flex',gap:12,padding:'11px 0',borderBottom:i<ADMIN_LOG.length-1?'1px solid var(--ap-line-soft)':'none'}}>
        {l.who==='system'
          ? <div style={{width:28,height:28,borderRadius:'50%',background:'var(--ap-bg-3)',display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0}}><Icon name="settings" size={13} color="var(--ap-fg-4)"/></div>
          : <Avatar name={l.who} size={28}/>}
        <div style={{flex:1,minWidth:0}}>
          <div style={{fontSize:12.5,color:'var(--ap-fg-1)',lineHeight:1.5}}>
            <b>{l.who==='system'?'系统':l.who}</b> · {l.act}
          </div>
          <div style={{fontSize:10.5,color:'var(--ap-fg-4)',fontFamily:'var(--ap-font-mono)',marginTop:2}}>{l.t}</div>
        </div>
        <WPill tone={l.kind==='risk'?'rose':l.kind==='strategy'?'violet':l.kind==='user'?'cyan':'default'}>{l.kind}</WPill>
      </div>
    ))}
  </WCard>
);

// ---------- page ----------
const WAdminPage = () => {
  const [tab, setTab] = React.useState('users');
  const tabs = [
    {id:'users', label:'用户管理', icon:'users'},
    {id:'roles', label:'角色权限', icon:'key'},
    {id:'log', label:'管理日志', icon:'list'},
  ];
  return (
    <div style={{display:'flex',gap:24,maxWidth:1100}}>
      <div style={{width:180,flexShrink:0,display:'flex',flexDirection:'column',gap:2}}>
        {tabs.map(t=>(
          <div key={t.id} onClick={()=>setTab(t.id)} style={{display:'flex',alignItems:'center',gap:10,padding:'10px 12px',borderRadius:9,cursor:'pointer',
            background:tab===t.id?'var(--ap-bg-2)':'transparent',color:tab===t.id?'var(--ap-fg-1)':'var(--ap-fg-3)',fontSize:13,fontWeight:500,border:'1px solid '+(tab===t.id?'var(--ap-line-soft)':'transparent')}}>
            <Icon name={t.icon} size={15} color={tab===t.id?'var(--ap-mint)':'currentColor'}/>{t.label}
          </div>
        ))}
        <div style={{marginTop:14,padding:'10px 12px',background:'var(--ap-amber-soft)',borderRadius:9,border:'1px solid rgba(240,185,11,.2)'}}>
          <div style={{fontSize:10.5,color:'var(--ap-fg-2)',lineHeight:1.5}}>所有管理操作均记录审计日志，不可删除。</div>
        </div>
      </div>
      <div style={{flex:1,minWidth:0,display:'flex',flexDirection:'column',gap:16}}>
        {tab==='users' && <UsersTab/>}
        {tab==='roles' && <RolesTab/>}
        {tab==='log' && <AdminLogTab/>}
      </div>
    </div>
  );
};

Object.assign(window, { WAdminPage });
