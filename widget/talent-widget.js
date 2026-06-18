/* Talent Discover Widget v3 - Clean rewrite */
class TalentWidget {
  constructor() {
    var s = document.currentScript;
    this.wsUrl = (s && s.dataset && s.dataset.ws) || 'wss://talent.atgoertek.xyz/ws/default';
    this.sessionId = 'sess_' + Math.random().toString(36).slice(2, 10);
    this.ws = null; this.isOpen = false; this.messages = []; this._wsConnected = false;
    this._inject(); this._connect();
  }
  _inject() {
    this.host = document.createElement('div'); this.host.id = 'talent-widget-root';
    document.body.appendChild(this.host);
    this.shadow = this.host.attachShadow({ mode: 'open' });
    this.shadow.appendChild(Object.assign(document.createElement('style'), { textContent: _CSS }));
    var w = document.createElement('div'); w.innerHTML = this._html();
    while (w.firstChild) this.shadow.appendChild(w.firstChild);
    this._bindEvents();
  }
  _html() {
    var av = '/widget/avatar.png';
    return '<div class="float-wrapper"><button class="floating-btn" id="float-btn" title="AI 人才助手"><img class="btn-icon-img" src="'+av+'" alt="AI"></button><div class="float-label">AI人才助手</div></div>' +
    '<div class="chat-panel floating" id="chat-panel">' +
    '<div class="resize-grip-top" id="grip-top" title="拖动调整高度"></div>' +
    '<div class="panel-header"><div class="header-left"><div class="avatar"><img class="btn-icon-img" src="'+av+'" alt="AI"></div><div><div class="title">AI人才发现助手</div><div class="subtitle">AI Talent Discovery</div></div></div>' +
    '<div class="header-actions"><button class="header-btn" id="btn-fullscreen" title="全屏">&#x26F6;</button><button class="header-btn" id="btn-minimize" title="最小化">&minus;</button></div></div>' +
    '<div class="chat-panel-body" id="panel-body">' +
    '<div class="chat-column" id="chat-column"><div class="reconnect-banner" id="reconnect-banner" style="display:none">连接已断开，正在重连...</div><div class="messages-container" id="messages"></div>' +
    '<div class="input-bar"><input type="text" id="msg-input" placeholder="输入需求，如：帮我找高级产品经理..."><button class="send-btn" id="send-btn">&uarr;</button></div></div>' +
    '<div class="resize-grip-right" id="grip-right" title="拖动调整宽度"></div>' +
    '<div class="fullscreen-panel" id="fullscreen-panel"></div></div></div>';
  }
  _bindEvents() {
    var self = this, $ = function(id) { return self.shadow.getElementById(id); };
    $('float-btn').addEventListener('click', function() { self.toggle(); });
    $('btn-minimize').addEventListener('click', function() { self.close(); });
    $('btn-fullscreen').addEventListener('click', function() { self.toggleFullscreen(); });
    $('send-btn').addEventListener('click', function() { self._send(); });
    $('msg-input').addEventListener('keydown', function(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); self._send(); } });
    $('messages').addEventListener('click', function(e) {
      var db = e.target.closest('.detail-btn'); if (db && db.dataset.id) { self._showLoading('正在生成候选人分析报告...'); self._wsSend({ type: 'action', action: 'report', ids: [db.dataset.id] }); return; }
      var ab = e.target.closest('.action-btn'); if (ab) { self._handleActionClick(ab.dataset.action); return; }
      var sc = e.target.closest('.suggestion-chip'); if (sc) { $('msg-input').value = sc.dataset.suggest; self._send(); }
    });
    $('fullscreen-panel').addEventListener('click', function(e) {
      var share = e.target.closest('.share-report-btn'); if (share) { self._shareReport(); return; }
      var dl = e.target.closest('.download-report-btn'); if (dl) { self._downloadReport(); return; }
      var prt = e.target.closest('.print-btn'); if (prt) { self._printReport(); return; }
    });
    var panel = $('chat-panel'), chatCol = $('chat-column'), dragging = false, startY = 0, startTop = 0, startX = 0, startW = 0;
    $('grip-top').addEventListener('mousedown', function(e) { if (panel.classList.contains('fullscreen')) return; e.preventDefault(); dragging = true; startY = e.clientY; startTop = panel.offsetTop; });
    $('grip-right').addEventListener('mousedown', function(e) { if (!panel.classList.contains('fullscreen')) return; e.preventDefault(); dragging = true; startX = e.clientX; startW = chatCol.offsetWidth; });
    document.addEventListener('mousemove', function(e) {
      if (!dragging) return;
      if (panel.classList.contains('fullscreen')) { var w = Math.max(200, Math.min(600, startW + (e.clientX - startX))); chatCol.style.flex = '0 0 ' + w + 'px'; chatCol.style.width = w + 'px'; chatCol.style.maxWidth = 'none'; }
      else { var newTop = Math.max(50, Math.min(window.innerHeight - 200, startTop + (e.clientY - startY))); panel.style.top = newTop + 'px'; }
    });
    document.addEventListener('mouseup', function() { dragging = false; });
  }
  _isFullscreen() { return this.shadow.getElementById('chat-panel').classList.contains('fullscreen'); }
  toggle() { this.isOpen ? this.close() : this.open(); }
  open() {
    this.isOpen = true; this.shadow.getElementById('chat-panel').classList.add('open');
    this.shadow.querySelector('.float-wrapper').style.display = 'none'; this.shadow.getElementById('msg-input').focus();
    if (this.messages.length === 0) {
      this._addBotMsg('\u{1F44B} 我是 AI 人才发现助手，可以帮你搜索匹配人才、推荐岗位、生成报告。请告诉我你的需求');
      this._addSuggestions(['帮我找高级产品经理', '按标签搜索人才', '找数字化转型人才']);
    }
  }
  close() { this.isOpen = false; if (this._isFullscreen()) this.toggleFullscreen(); this.shadow.getElementById('chat-panel').classList.remove('open'); this.shadow.querySelector('.float-wrapper').style.display = 'flex'; }
  toggleFullscreen() { var p = this.shadow.getElementById('chat-panel'), isFS = p.classList.contains('fullscreen'); p.classList.toggle('floating', isFS); p.classList.toggle('fullscreen', !isFS); p.style.top = ''; var cc = this.shadow.getElementById('chat-column'); cc.style.flex = ''; cc.style.width = ''; cc.style.maxWidth = ''; }
  _send() { var input = this.shadow.getElementById('msg-input'), text = input.value.trim(); if (!text || !this._wsConnected) return; this._addUserMsg(text); input.value = ''; this.shadow.getElementById('send-btn').disabled = true; this._addTyping(); this._wsSend({ type: 'message', text: text, session_id: this.sessionId }); }
  _addUserMsg(text) { this.messages.push({ role: 'user', text: text }); this._app('<div class="message user"><div class="msg-bubble">'+_esc(text)+'</div><div class="msg-avatar user">U</div></div>'); }
  _addBotMsg(text)  { this.messages.push({ role: 'bot', text: text }); this._app('<div class="message"><div class="msg-avatar bot"><img class="btn-icon-img" src="/widget/avatar.png" alt="AI"></div><div class="msg-bubble">'+_esc(text).replace(/\n/g,'<br>')+'</div></div>'); }

  _addCard(data) {
    var g = data.grade || 'B'; this.messages.push({ role: 'bot', cardData: data });
    this._app('<div class="message"><div class="msg-avatar bot"><img class="btn-icon-img" src="/widget/avatar.png" alt="AI"></div><div class="result-card" data-id="'+(data.id||'')+'"><div class="card-top"><div class="card-avatar-wrap"><img class="card-avatar" src="'+_avatarUrl(data.id,data.gender)+'" alt="" onerror="this.style.display=\'none\'"><span class="card-score">'+(data.score||'')+'</span><span class="card-score-label">匹配度</span></div><div class="card-body"><div class="card-info"><div class="badge-row"><input type="checkbox" class="card-checkbox" data-id="'+(data.id||'')+'"><span class="grade-badge grade-'+g+'">'+g+'</span><span class="card-name">'+_esc(data.name||'')+'</span></div><div class="card-meta">'+_esc(data.department||'')+' · '+_esc(data.position||'')+' · '+_esc(data.level||'')+' · '+_esc(data.education||'')+' · '+_esc(data.performance||'')+'</div><div class="card-chips">'+_chips(data.skills)+_chips(data.tags)+'</div></div><div class="card-actions"><button class="card-btn detail-btn" data-id="'+(data.id||'')+'">人才画像</button></div></div>'+(data.reason?'<div style="font-size:11px;color:var(--text-secondary);margin-top:6px;">'+_esc(data.reason)+'</div>':'')+'</div></div></div>');
  }

  _addActions(actions) {
    if (!actions || !actions.length) return;
    var btns = actions.map(function(a) { return '<button class="action-btn'+(a.indexOf('对比')>=0||a.indexOf('推荐')>=0?'':' secondary')+'" data-action="'+_esc(a)+'">'+_esc(a)+'</button>'; }).join('');
    this._app('<div class="message"><div class="msg-avatar bot"><img class="btn-icon-img" src="/widget/avatar.png" alt="AI"></div><div class="action-bar">'+btns+'</div></div>');
  }

  _handleActionClick(action) {
    if (action.indexOf('对比选中')>=0) { var checked=this.shadow.querySelectorAll('.card-checkbox:checked'); var ids=Array.from(checked).map(function(cb){return cb.dataset.id;}).filter(Boolean); if(ids.length>=2){this._showLoading('正在对比候选人...');this._wsSend({type:'action',action:'compare',ids:ids});} else this._addBotMsg('请至少勾选2位候选人'); }
    else if (action.indexOf('对比')>=0) { var n=parseInt((action.match(/\d+/)||['2'])[0])||2; var ids=this.messages.filter(function(m){return m.cardData;}).slice(0,n).map(function(m){return m.cardData.id;}).filter(Boolean); if(ids.length>=2){this._showLoading('正在对比候选人...');this._wsSend({type:'action',action:'compare',ids:ids});} }
    else if (action.indexOf('导出')>=0) this._triggerDownload();
    else if (action.indexOf('返回')>=0) this.close();
  }

  _showLoading(text) {
    if (!this._isFullscreen()) this.toggleFullscreen();
    this.shadow.getElementById('fullscreen-panel').innerHTML =
      '<div class="loading-container"><div class="loading-spinner"><div class="spinner-ring"></div></div><p class="loading-text">'+_esc(text||'正在加载...')+'</p><p class="loading-hint">AI 正在分析数据，请稍候</p></div>';
  }

  _addSuggestions(items) { this._app('<div class="action-bar" style="margin-left:34px;">'+items.map(function(a){return '<button class="chip suggestion-chip" data-suggest="'+_esc(a)+'">'+_esc(a)+'</button>';}).join('')+'</div>'); }
  _addTyping() { this._app('<div class="message typing-msg"><div class="msg-avatar bot"><img class="btn-icon-img" src="/widget/avatar.png" alt="AI"></div><div class="typing-indicator"><span></span><span></span><span></span></div></div>'); }
  _removeTyping() { var el=this.shadow.querySelector('.typing-msg'); if(el)el.remove(); }
  _wsSend(data) { if(this.ws&&this.ws.readyState===WebSocket.OPEN)this.ws.send(JSON.stringify(data)); }

  _handleMessage(msg) {
    var self=this, M={
      text: function(){self._addBotMsg(msg.content);},
      card: function(){self._addCard(msg.data);},
      report: function(){self._removeTyping();if(!self._isFullscreen())self.toggleFullscreen();self._renderReport(msg.data);},
      compare: function(){self._removeTyping();if(!self._isFullscreen())self.toggleFullscreen();self._renderCompare(msg.data);if(!(msg.data.per_person&&msg.data.per_person.length>0))self._showAiPending();},
      profile: function(){self._removeTyping();if(!self._isFullscreen())self.toggleFullscreen();self._renderProfile(msg.data);},
      actions: function(){self._addActions(msg.actions);},
      done: function(){self._removeTyping();self.shadow.getElementById('send-btn').disabled=false;self.shadow.getElementById('msg-input').focus();},
      error: function(){self._removeTyping();self._addBotMsg('⚠ '+msg.content);self.shadow.getElementById('send-btn').disabled=false;}
    };
    (M[msg.type]||function(){})();
  }

  _showReconnecting() { var b=this.shadow.getElementById('reconnect-banner'); if(b)b.style.display='block'; }
  _hideReconnecting() { var b=this.shadow.getElementById('reconnect-banner'); if(b)b.style.display='none'; }
  _showAiPending() { var fp=this.shadow.getElementById('fullscreen-panel'); var d=document.createElement('div'); d.className='ai-pending'; d.innerHTML='<div class="report-section" style="margin-top:20px"><p style="font-size:0.8125rem;color:var(--text-secondary);display:flex;align-items:center;gap:8px"><span class="spinner-ring" style="width:14px;height:14px;border-width:2px;display:inline-block"></span>AI 深度分析生成中，完成后自动刷新...</p></div>'; fp.appendChild(d); }

  _renderReport(data) {
    var g=data.grade||'B', hasDims=data.dimensions&&Object.keys(data.dimensions).length>0;
    // Info row helper
    function _info(label, val) { return val ? '<div class="info-row"><span class="info-label">'+_esc(label)+'</span><span class="info-val">'+_esc(String(val))+'</span></div>' : ''; }
    this.shadow.getElementById('fullscreen-panel').innerHTML =
      '<div class="report-header"><img class="report-avatar" src="'+_avatarUrl(data.id,data.gender)+'" alt="" onerror="this.style.display=\'none\'"><div class="report-grade"><span class="grade-badge grade-'+g+'" style="font-size:1rem;padding:6px 14px;">'+g+'</span><div class="report-score">'+(data.score||'')+'</div><div style="font-size:0.75rem;color:var(--text-secondary)">综合评分</div></div>'+
      '<div class="report-info"><div class="report-name">'+_esc(data.name||'')+'</div><div class="report-meta">'+_esc(data.department||'')+' · '+_esc(data.position||'')+' · '+_esc(data.level||'')+'</div>'+
      '<div class="report-meta">'+_esc(data.education||'')+' / '+_esc(data.major||'')+' · 司龄'+(data.tenure||'')+'年 · 绩效'+_esc(data.performance||'')+'</div></div></div>'+

      '<div class="detail-grid">'+
        '<div class="detail-col"><h4>基本信息</h4>'+
          _info('姓名',data.name)+_info('性别',data.gender)+_info('年龄',data.age)+_info('籍贯',data.native)+
          _info('工龄(年)',data.tenure)+_info('工作地点',data.workplace)+
        '</div>'+
        '<div class="detail-col"><h4>组织信息</h4>'+
          _info('部门',data.department)+_info('岗位',data.position)+_info('职级',data.level)+
          _info('职等',data.level_num)+_info('主管',data.supervisor_name)+_info('下属数',data.subordinates)+
        '</div>'+
        '<div class="detail-col"><h4>学历背景</h4>'+
          _info('学历',data.education)+_info('院校类型',data.school_type)+_info('专业',data.major)+
        '</div>'+
      '</div>'+

      '<div class="report-section"><h4>技能标签</h4><div class="card-chips">'+_chips(data.skills)+'</div></div>'+
      '<div class="report-section"><h4>人才标签</h4><div class="card-chips">'+_chips(data.tags)+'</div></div>'+

      '<div class="detail-grid" style="margin-top:16px">'+
        '<div class="detail-col"><h4>项目经验</h4>'+
          _info('NPI项目数',data.npi_projects)+_info('量产项目数',data.mass_projects)+_info('管理改善项目',data.mgmt_projects)+
          _info('工作领域',data.work_domain)+_info('跨部门经验',data.cross_dept)+
        '</div>'+
        '<div class="detail-col"><h4>证书与资质</h4>'+
          _info('证书',data.certificates)+_info('导师',data.is_mentor)+_info('带徒人数',data.mentees)+
          _info('GPS人员',data.is_gps)+_info('国际化人才',data.is_international)+_info('外派国家',data.overseas)+
        '</div>'+
        '<div class="detail-col"><h4>发展意愿</h4>'+
          _info('是否愿意调岗',data.willing_transfer)+_info('感兴趣岗位',data.interested_position)+
          _info('愿意跨部门',data.willing_cross_dept)+_info('愿意跨BU',data.willing_cross_bu)+
          _info('近三年晋升',data.promotions_3y)+_info('绩效分数',data.performance_score)+
        '</div>'+
      '</div>'+

      (hasDims?'<div class="report-section"><h4>匹配度各维度</h4><div id="report-chart" style="width:100%;max-width:500px;margin:0 auto;">'+_radarSVG(data.dimensions)+'</div></div>':_dimFallback(data.dimensions))+
      '<div class="report-section"><h4>综合评估</h4><p>'+_esc(data.explanation||'暂无')+'</p></div>'+
      '<div class="report-section" style="display:flex;gap:24px;"><div style="flex:1;"><h4>优势</h4><ul>'+_li(data.strengths)+'</ul></div><div style="flex:1;"><h4>待发展项</h4><ul>'+_li(data.weaknesses)+'</ul></div></div>'+
      '<div class="report-section"><h4>发展建议</h4><ul>'+_li(data.suggestions)+'</ul></div>'+
      '<div style="margin-top:20px;display:flex;gap:8px;"><button class="action-btn share-report-btn">分享报告</button><button class="action-btn download-report-btn">下载报告</button><button class="action-btn secondary print-btn">打印</button></div>';
  }

  _renderCompare(data) {
    var profiles=data.profiles||[], n=profiles.length;
    if (n < 2) return;
    var allDimKeys=[];
    profiles.forEach(function(p){var d=p.dimensions||{};Object.keys(d).forEach(function(k){if(allDimKeys.indexOf(k)<0)allDimKeys.push(k);});});
    var hasDims=allDimKeys.length>0;

    var hdr='<th class="cmp-label-th">属性</th>'+profiles.map(function(p){return'<th><img class="cmp-avatar" src="'+_avatarUrl(p.id,p.gender)+'" alt="" onerror="this.style.display=\'none\'"><div>'+_esc(p.name||'')+'</div></th>';}).join('');
    var gradeRow='<tr><td class="cmp-label">评级</td>'+profiles.map(function(p){return'<td><span class="grade-badge grade-'+(p.grade||'B')+'">'+(p.grade||'B')+'</span></td>';}).join('')+'</tr>';
    var scoreRow='<tr class="cmp-row-odd"><td class="cmp-label">综合评分</td>'+profiles.map(function(p){return'<td><span class="cmp-score-cell">'+_esc(p.score||'—')+'</span></td>';}).join('')+'</tr>';
    var radarRow='';
    if (hasDims) { radarRow='<tr><td class="cmp-label">能力雷达</td>'+profiles.map(function(p){var dims=p.dimensions||{};return'<td><div style="width:100%;max-width:200px;margin:0 auto;">'+_radarSVG(dims,200)+'</div></td>';}).join('')+'</tr>'; }
    var secHdr='<tr class="cmp-section-header"><td class="cmp-label">基本信息</td>'+profiles.map(function(){return'<td></td>';}).join('')+'</tr>';
    var attrs=[{k:'department',l:'部门'},{k:'position',l:'岗位'},{k:'level',l:'职级'},{k:'education',l:'学历'},{k:'major',l:'专业'},{k:'performance',l:'绩效'},{k:'tenure',l:'司龄(年)'}];
    var tRows=attrs.map(function(a,i){var cls=i%2===0?'cmp-row-even':'cmp-row-odd';return'<tr class="'+cls+'"><td class="cmp-label">'+a.l+'</td>'+profiles.map(function(p){return'<td>'+_esc(String(p[a.k]||'—'))+'</td>';}).join('')+'</tr>';}).join('');
    var sRow='<tr class="cmp-row-odd"><td class="cmp-label">技能标签</td>'+profiles.map(function(p){return'<td class="cmp-chips-cell">'+_chips((p.skills||[]).slice(0,8))+'</td>';}).join('')+'</tr>';
    var dRows='';
    if (hasDims) { dRows='<tr class="cmp-section-header"><td class="cmp-label">维度评分</td>'+profiles.map(function(){return'<td></td>';}).join('')+'</tr>'; dRows+=allDimKeys.map(function(k,i){var cls=i%2===0?'cmp-row-even':'cmp-row-odd';return'<tr class="'+cls+'"><td class="cmp-label">'+_esc(k)+'</td>'+profiles.map(function(p){var v=(p.dimensions||{})[k];return'<td><span style="font-weight:600;color:'+(v>=80?'var(--green)':v>=60?'#F59E0B':'#EF4444')+'">'+(v!=null?v:'—')+'</span></td>';}).join('')+'</tr>';}).join(''); }

    // ── AI Analysis: per-candidate structured columns ──
    var perPerson=data.per_person||[];
    var aiSection='';
    if (perPerson.length>0) {
      var aiHdr='<th class="cmp-label-th">AI 深度分析</th>'+profiles.map(function(p){return'<th>'+_esc(p.name||'')+'</th>';}).join('');
      var posRow='<tr class="cmp-row-odd"><td class="cmp-label">定位</td>'+perPerson.map(function(p){return'<td>'+_esc(p.positioning||'—')+'</td>';}).join('')+'</tr>';
      var compScoreRow='<tr><td class="cmp-label">综合得分</td>'+perPerson.map(function(p){var s=parseInt(p.comprehensive_score)||0;return'<td><span style="font-size:1.3rem;font-weight:300;color:'+(s>=80?'var(--green)':s>=65?'#F59E0B':'#EF4444')+'">'+s+'</span></td>';}).join('')+'</tr>';
      var strRow='<tr class="cmp-row-odd"><td class="cmp-label">优势</td>'+perPerson.map(function(p){return'<td><ul style="margin:0;padding:0 0 0 16px;font-size:0.75rem;color:var(--text);line-height:1.7">'+(p.strengths||[]).slice(0,4).map(function(s){return'<li>'+_esc(s)+'</li>';}).join('')+'</ul></td>';}).join('')+'</tr>';
      var weakRow='<tr><td class="cmp-label">待发展</td>'+perPerson.map(function(p){return'<td><ul style="margin:0;padding:0 0 0 16px;font-size:0.75rem;color:var(--text-secondary);line-height:1.7">'+(p.weaknesses||[]).slice(0,3).map(function(s){return'<li>'+_esc(s)+'</li>';}).join('')+'</ul></td>';}).join('')+'</tr>';
      var recRow='<tr class="cmp-row-odd"><td class="cmp-label">任用建议</td>'+perPerson.map(function(p){return'<td style="font-size:0.8125rem;color:var(--text);line-height:1.7">'+_esc(p.recommendation||'—')+'</td>';}).join('')+'</tr>';
      aiSection='<table class="cmp-table" style="margin-top:24px;"><thead><tr>'+aiHdr+'</tr></thead><tbody>'+posRow+compScoreRow+strRow+weakRow+recRow+'</tbody></table>';
    }

    this.shadow.getElementById('fullscreen-panel').innerHTML =
      '<h3 style="font-weight:600;font-size:1.25rem;color:var(--text);margin-bottom:20px;">候选人对比分析</h3>'+
      '<table class="cmp-table"><thead><tr>'+hdr+'</tr></thead><tbody>'+gradeRow+scoreRow+radarRow+secHdr+tRows+sRow+dRows+'</tbody></table>'+
      aiSection+
      '<div class="report-section" style="margin-top:24px;"><h4>综合对比结论</h4><p style="white-space:pre-wrap;line-height:1.8;">'+_esc(data.analysis||'暂无')+'</p></div>'+
      '<div style="margin-top:20px;display:flex;gap:8px;"><button class="action-btn share-report-btn">分享报告</button><button class="action-btn download-report-btn">下载报告</button><button class="action-btn secondary print-btn">打印</button></div>';
  }

  _renderProfile(data) {
    var iceberg=data.iceberg||{};
    this.shadow.getElementById('fullscreen-panel').innerHTML =
      '<h3 style="font-weight:600;font-size:1.25rem;color:var(--text);margin-bottom:16px;">'+_esc(data.name||'')+' — 人才全景画像</h3>'+
      '<div class="profile-grid"><div>'+_icebergSection('水上 — 可见信息',iceberg['水上_可见']||{})+'</div>'+
      '<div>'+_icebergSection('水面 — 核心能力',iceberg['水面_核心能力']||{})+'</div>'+
      '<div>'+_icebergSection('水下 — 隐性特质',iceberg['水下_隐性特质']||{})+'</div></div>';
  }

  _connect() {
    this._reconnectAttempts=0; var url=this.wsUrl.replace(/\/ws\/default/,'/ws/'+this.sessionId); this.ws=new WebSocket(url); var self=this;
    this.ws.onopen=function(){self._reconnectAttempts=0;self._wsConnected=true;self._hideReconnecting();};
    this.ws.onmessage=function(e){try{self._handleMessage(JSON.parse(e.data));}catch(err){}};
    this.ws.onclose=function(){self._wsConnected=false;self._showReconnecting();self._reconnectAttempts++;var d=Math.min(1000*Math.pow(2,self._reconnectAttempts),30000);setTimeout(function(){self._connect();},d);};
    this.ws.onerror=function(){self._wsConnected=false;};
  }

  _app(html) { this.shadow.getElementById('messages').insertAdjacentHTML('beforeend',html); var self=this; requestAnimationFrame(function(){var c=self.shadow.getElementById('messages');if(c)c.scrollTop=c.scrollHeight;}); }
  _triggerDownload() { var a=document.createElement('a'); a.href='/api/export/'+this.sessionId; a.download='candidates.xlsx'; a.style.display='none'; document.body.appendChild(a); a.click(); document.body.removeChild(a); this._addBotMsg('Excel 报告已开始下载'); }
  _shareReport() { var fp=this.shadow.getElementById('fullscreen-panel'); var title=document.title||'对比报告'; var url=window.location.href; var text=fp.innerText.substring(0,300); var shareData={title:title,text:text,url:url}; if(navigator.share){navigator.share(shareData).catch(function(){});}else{this._downloadReport();} }
  _downloadReport() { var fp=this.shadow.getElementById('fullscreen-panel'); var isDetail=!!fp.querySelector('.report-header')&&!fp.querySelector('.cmp-table'); var fname=isDetail?'人才全景履历':'人才对比报告'; var css=':root{--green:#22c55e;--green-dark:#16a34a;--green-ghost:rgba(34,197,94,0.08);--text:#1D1D1F;--text-secondary:#86868B;--bg:#FAFAFA;--border:#E5E5EA;--border-light:#F2F2F7;--white:#fff}*{box-sizing:border-box;margin:0;padding:0}body{font-family:Inter,-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;max-width:1100px;margin:32px auto;padding:0 20px;color:#1D1D1F;line-height:1.7;background:#fff}'+
    'h3{font-weight:600;font-size:1.15rem;margin-bottom:20px;color:#1D1D1F}'+
    '.cmp-table{width:100%;border-collapse:collapse;font-size:0.8125rem;table-layout:fixed;margin-bottom:16px}'+
    '.cmp-table thead th{background:#22c55e;color:#fff;padding:10px 12px;font-weight:500;font-size:12px;text-align:center;word-break:break-word}.cmp-table thead th:first-child{border-radius:6px 0 0 0}.cmp-table thead th:last-child{border-radius:0 6px 0 0}'+
    '.cmp-table tbody td{padding:10px 12px;text-align:center;vertical-align:middle;border-bottom:0.5px solid #E5E5EA}.cmp-table tbody td:first-child{text-align:left}'+
    '.cmp-label-th{padding:10px 12px!important;text-align:left!important}.cmp-label{font-weight:600;font-size:11px;color:#1D1D1F;text-align:left;white-space:nowrap;padding:10px 12px!important}'+
    '.cmp-row-even td{background:#fafafa}.cmp-row-odd td{background:#fff}'+
    '.cmp-section-header td{background:#f2f2f7!important;font-weight:600;font-size:10px;color:#86868B;text-transform:uppercase;letter-spacing:.05em;padding:8px 12px!important}'+
    '.cmp-score-cell{font-size:1.5rem;font-weight:300;color:#22c55e}.cmp-chips-cell{line-height:2}'+
    '.grade-badge{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;border-radius:50%;font-weight:700;font-size:10px;text-transform:uppercase;flex-shrink:0}.grade-badge.S{background:#22C55E;color:#FFF}.grade-badge.A{background:rgba(34,197,94,0.08);color:#16A34A;border:1px solid rgba(34,197,94,0.25)}.grade-badge.B{background:rgba(100,100,100,0.06);color:#666}.grade-badge.C{color:#86868B}'+
    '.card-chips{display:flex;gap:6px;flex-wrap:wrap}.chip{font-size:10px;border-radius:8px;padding:3px 8px;white-space:nowrap;border:none;font-weight:500}'+
    '.card-avatar-wrap{width:72px;flex-shrink:0;display:flex;flex-direction:column;align-items:center;padding:14px 0 12px;gap:4px;background:linear-gradient(180deg,rgba(34,197,94,0.03) 0%,rgba(255,255,255,0) 100%)}.card-avatar{width:52px;height:65px;border-radius:10px;object-fit:cover;box-shadow:0 2px 6px rgba(0,0,0,0.12)}.cmp-avatar{width:56px;height:70px;border-radius:10px;object-fit:cover;box-shadow:0 2px 6px rgba(0,0,0,0.12);display:block;margin:0 auto 6px}.card-body{flex:1;min-width:0;padding:14px 16px;display:flex;align-items:center;gap:14px}.card-info{flex:1;min-width:0;display:flex;flex-direction:column;gap:5px}.card-score{font-size:24px;font-weight:600;color:#22C55E;line-height:1}.card-score-label{font-size:10px;color:#86868B}'+
    '.report-section{margin-top:20px}.report-section h4{font-weight:500;font-size:.75rem;color:#86868B;text-transform:uppercase;margin-bottom:8px}.report-section p,.report-section li{font-size:.875rem;color:#1D1D1F;line-height:1.7}.report-section ul{padding-left:16px}.report-section li{margin-bottom:4px}'+
    '.report-header{display:flex;gap:20px;align-items:stretch;margin-bottom:20px}.report-avatar{width:130px;height:160px;border-radius:14px;object-fit:cover;object-position:center top}.report-grade{text-align:center;flex-shrink:0}.report-info{flex:1;display:flex;flex-direction:column;justify-content:center}.report-name{font-size:1.5rem;font-weight:600;color:#1D1D1F}.report-meta{font-size:.875rem;color:#86868B;margin-top:4px}.report-score{font-size:2.5rem;font-weight:300;color:#22c55e}'+
    '.detail-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}.detail-grid h4{font-weight:500;font-size:0.75rem;color:#86868B;text-transform:uppercase;margin-bottom:8px}.detail-col{background:#fafafa;border-radius:8px;padding:14px}'+
    '.info-row{font-size:0.8125rem;color:#1D1D1F;margin:2px 0;display:flex;justify-content:space-between;padding:3px 0;border-bottom:0.5px solid #f2f2f7}.info-label{color:#86868B;flex-shrink:0}.info-val{color:#1D1D1F;font-weight:500;text-align:right}'+
    '.action-btn{display:none!important}'+
    '@media print{@page{size:A4;margin:12mm}body{margin:0;padding:0;max-width:none}}';
  var html='<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>'+fname+'</title><style>'+css+'</style></head><body><div style="background:#fff;padding:24px">'+fp.innerHTML+'</div></body></html>';
  var self=this; self._addBotMsg('正在生成 PDF...');
  var pdfUrl=self.wsUrl.replace(/\/ws\/.*$/,'').replace('wss://','https://').replace('ws://','http://')+'/api/pdf';
  fetch(pdfUrl,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({html:html,filename:fname})})
    .then(function(r){if(!r.ok)return r.json().then(function(j){throw new Error(j.error||'PDF failed')});return r.blob();})
    .then(function(b){var u=URL.createObjectURL(b);var a=document.createElement('a');a.href=u;a.download=fname+'.pdf';document.body.appendChild(a);a.click();document.body.removeChild(a);setTimeout(function(){URL.revokeObjectURL(u)},3000);self._addBotMsg(fname+' PDF 已下载');})
    .catch(function(e){self._addBotMsg('PDF 生成失败: '+e.message);console.error(e);}); }
  _printReport(){var fp=this.shadow.getElementById('fullscreen-panel');var css=':root{--green:#22c55e;--green-dark:#16a34a;--green-ghost:rgba(34,197,94,0.08);--text:#1D1D1F;--text-secondary:#86868B;--bg:#FAFAFA;--border:#E5E5EA;--border-light:#F2F2F7;--white:#fff}*{box-sizing:border-box;margin:0;padding:0}body{font-family:Inter,-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;max-width:1100px;margin:32px auto;padding:0 20px;color:#1D1D1F;line-height:1.7;background:#fff}'+
    'h3{font-weight:600;font-size:1.15rem;margin-bottom:20px;color:#1D1D1F}'+
    '.cmp-table{width:100%;border-collapse:collapse;font-size:0.8125rem;table-layout:fixed;margin-bottom:16px}'+
    '.cmp-table thead th{background:#22c55e;color:#fff;padding:10px 12px;font-weight:500;font-size:12px;text-align:center;word-break:break-word}.cmp-table thead th:first-child{border-radius:6px 0 0 0}.cmp-table thead th:last-child{border-radius:0 6px 0 0}'+
    '.cmp-table tbody td{padding:10px 12px;text-align:center;vertical-align:middle;border-bottom:0.5px solid #E5E5EA}.cmp-table tbody td:first-child{text-align:left}'+
    '.cmp-label-th{padding:10px 12px!important;text-align:left!important}.cmp-label{font-weight:600;font-size:11px;color:#1D1D1F;text-align:left;white-space:nowrap;padding:10px 12px!important}'+
    '.cmp-row-even td{background:#fafafa}.cmp-row-odd td{background:#fff}'+
    '.cmp-section-header td{background:#f2f2f7!important;font-weight:600;font-size:10px;color:#86868B;text-transform:uppercase;letter-spacing:.05em;padding:8px 12px!important}'+
    '.cmp-score-cell{font-size:1.5rem;font-weight:300;color:#22c55e}.cmp-chips-cell{line-height:2}'+
    '.grade-badge{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;border-radius:50%;font-weight:700;font-size:10px;text-transform:uppercase;flex-shrink:0}.grade-badge.S{background:#22C55E;color:#FFF}.grade-badge.A{background:rgba(34,197,94,0.08);color:#16A34A;border:1px solid rgba(34,197,94,0.25)}.grade-badge.B{background:rgba(100,100,100,0.06);color:#666}.grade-badge.C{color:#86868B}'+
    '.card-chips{display:flex;gap:6px;flex-wrap:wrap}.chip{font-size:10px;border-radius:8px;padding:3px 8px;white-space:nowrap;border:none;font-weight:500}'+
    '.card-avatar-wrap{width:72px;flex-shrink:0;display:flex;flex-direction:column;align-items:center;padding:14px 0 12px;gap:4px;background:linear-gradient(180deg,rgba(34,197,94,0.03) 0%,rgba(255,255,255,0) 100%)}.card-avatar{width:52px;height:65px;border-radius:10px;object-fit:cover;box-shadow:0 2px 6px rgba(0,0,0,0.12)}.cmp-avatar{width:56px;height:70px;border-radius:10px;object-fit:cover;box-shadow:0 2px 6px rgba(0,0,0,0.12);display:block;margin:0 auto 6px}.card-body{flex:1;min-width:0;padding:14px 16px;display:flex;align-items:center;gap:14px}.card-info{flex:1;min-width:0;display:flex;flex-direction:column;gap:5px}.card-score{font-size:24px;font-weight:600;color:#22C55E;line-height:1}.card-score-label{font-size:10px;color:#86868B}'+
    '.report-section{margin-top:20px}.report-section h4{font-weight:500;font-size:.75rem;color:#86868B;text-transform:uppercase;margin-bottom:8px}.report-section p,.report-section li{font-size:.875rem;color:#1D1D1F;line-height:1.7}.report-section ul{padding-left:16px}.report-section li{margin-bottom:4px}'+
    '.report-header{display:flex;gap:20px;align-items:stretch;margin-bottom:20px}.report-avatar{width:130px;height:160px;border-radius:14px;object-fit:cover;object-position:center top}.report-grade{text-align:center;flex-shrink:0}.report-info{flex:1;display:flex;flex-direction:column;justify-content:center}.report-name{font-size:1.5rem;font-weight:600;color:#1D1D1F}.report-meta{font-size:.875rem;color:#86868B;margin-top:4px}.report-score{font-size:2.5rem;font-weight:300;color:#22c55e}'+
    '.action-btn{display:inline-block;padding:6px 14px;border-radius:8px;font-size:11px;color:#fff;background:#22c55e;border:none;margin:4px}'+
    '.detail-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}.detail-grid h4{font-weight:500;font-size:0.75rem;color:#86868B;text-transform:uppercase;margin-bottom:8px}.detail-col{background:#fafafa;border-radius:8px;padding:14px}.info-row{font-size:0.8125rem;color:#1D1D1F;margin:2px 0;display:flex;justify-content:space-between;padding:3px 0;border-bottom:0.5px solid #f2f2f7}.info-label{color:#86868B;flex-shrink:0}.info-val{color:#1D1D1F;font-weight:500;text-align:right}'+
    '@media print{body{margin:0;padding:0;max-width:none}.action-btn{display:none!important}}';
  var html='<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>人才报告</title><style>'+css+'</style></head><body><div style="background:#fff;padding:24px">'+fp.innerHTML+'</div></body></html>';
  var w=window.open('','_blank','width=900,height=700');w.document.write(html);w.document.close();
var self=this;setTimeout(function(){w.print();w.close();self._addBotMsg('报告已发送到打印机');},800); }
}

/* ── Helpers ── */
function _esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function _avatarUrl(id,gender){var pool=gender==='女'?'f':'m';var count=pool==='f'?20:25;var h=0;for(var i=0;i<(id||'').length;i++){h=((h<<5)-h)+(id||'').charCodeAt(i);h|=0;}var n=(Math.abs(h)%count)+1;var ns=n<10?'0'+n:''+n;return '/widget/avatars/avatar-'+pool+'-'+ns+'.png';}
/* 64-color palette — vivid pastel, each hue distinct. Same tag = same color (hash → index). */
var _TAG_PALETTE=(function(){
  var families=[
    {h:210, n:10}, // blue
    {h:175, n:10}, // teal
    {h:155, n:10}, // green
    {h: 48, n: 8}, // yellow
    {h: 25, n: 8}, // orange
    {h: 85, n: 6}, // lime
    {h:195, n: 6}, // cyan
    {h:  5, n: 3}, // red
    {h:270, n: 2}, // purple
    {h:335, n: 1}, // pink
  ];
  var p=[];
  for(var f=0;f<families.length;f++){
    var fam=families[f];
    for(var v=0;v<fam.n;v++){
      var hue=fam.h+(v-fam.n/2)*3;
      var bgSat=68+(v%3)*10;              // 68-88% — strong pastel bg
      var bgLight=87-(v%3)*3;            // 84-87% — bright but colored
      var fgSat=70+(v%3)*12;             // 70-94% — vivid text
      var fgLight=22+(v%2)*3;            // 22-25% — deep readable
      p.push({bg:'hsl('+hue+','+bgSat+'%,'+bgLight+'%)',fg:'hsl('+hue+','+fgSat+'%,'+fgLight+'%)'});
    }
  }
  return p;
})();
function _tagColor(tag){
  var h=0;for(var i=0;i<tag.length;i++){h=((h<<5)-h)+tag.charCodeAt(i);h|=0;}
  return _TAG_PALETTE[Math.abs(h)%64];
}
function _chips(a){return(a||[]).map(function(x){var c=_tagColor(x);return'<span class="chip" style="background:'+c.bg+';color:'+c.fg+'">'+_esc(x)+'</span>';}).join('');}
function _li(a){return(a||[]).map(function(s){return'<li>'+_esc(s)+'</li>';}).join('')||'<li>暂无数据</li>';}
function _dimFallback(d){if(!d||!Object.keys(d).length)return'';return'<div class="report-section"><h4>匹配度各维度</h4>'+Object.entries(d).map(function(e){return'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:0.5px solid var(--border-light);"><span style="font-size:0.8125rem;color:var(--text);">'+_esc(e[0])+'</span><span style="font-size:0.8125rem;font-weight:600;color:var(--green);">'+e[1]+'</span></div>';}).join('')+'</div>';}
function _radarSVG(d,Sz){
  var c=Object.keys(d),v=Object.values(d),N=c.length;if(N<3)return _dimFallback(d);
  var S=Sz||280,x=S/2,y=S/2,R=S*0.39,svg='<svg viewBox="0 0 '+S+' '+S+'" style="width:100%;max-width:'+S+'px;display:block;margin:0 auto;">';
  for(var li=0;li<4;li++){var lv=[25,50,75,100][li],rr=R*lv/100;svg+='<circle cx="'+x+'" cy="'+y+'" r="'+rr.toFixed(1)+'" fill="none" stroke="#E5E5EA" stroke-width="0.5"/><text x="'+(x+rr+4).toFixed(0)+'" y="'+(y+4)+'" fill="#86868B" font-size="9">'+lv+'</text>';}
  for(var i=0;i<N;i++){var a=Math.PI*2*i/N-Math.PI/2,px=x+R*Math.cos(a),py=y+R*Math.sin(a),lx=x+(R+22)*Math.cos(a),ly=y+(R+22)*Math.sin(a);svg+='<line x1="'+x+'" y1="'+y+'" x2="'+px.toFixed(1)+'" y2="'+py.toFixed(1)+'" stroke="#E5E5EA" stroke-width="0.5"/><text x="'+lx.toFixed(1)+'" y="'+ly.toFixed(1)+'" text-anchor="middle" dominant-baseline="central" fill="#1D1D1F" font-size="10">'+_esc(c[i])+'</text>';}
  var pts='';for(var i=0;i<N;i++){var a=Math.PI*2*i/N-Math.PI/2,r=R*(v[i]||0)/100;pts+=(x+r*Math.cos(a)).toFixed(1)+','+(y+r*Math.sin(a)).toFixed(1)+' ';}
  svg+='<polygon points="'+pts.trim()+'" fill="rgba(34,197,94,0.12)" stroke="#22c55e" stroke-width="2" stroke-linejoin="round"/>';
  for(var i=0;i<N;i++){var a=Math.PI*2*i/N-Math.PI/2,r=R*(v[i]||0)/100;svg+='<circle cx="'+(x+r*Math.cos(a)).toFixed(1)+'" cy="'+(y+r*Math.sin(a)).toFixed(1)+'" r="2.5" fill="#22c55e"/>';}
  return svg+'</svg>';
}
function _icebergSection(t,d){var h='<h4>'+t+'</h4>';for(var k in d){var v=d[k];if(Array.isArray(v))h+='<div style="margin-top:6px;"><div style="font-size:0.75rem;color:var(--text-secondary);">'+_esc(k)+'</div><div class="card-chips">'+_chips(v.map(String))+'</div></div>';else if(typeof v==='object'&&v!==null){h+='<div style="margin-top:6px;"><div style="font-size:0.75rem;color:var(--text-secondary);">'+_esc(k)+'</div>';for(var kk in v)h+='<div class="info-row">'+_esc(kk)+': '+(v[kk]||'—')+'</div>';h+='</div>';}else h+='<div class="info-row">'+_esc(k)+': '+(v||'—')+'</div>';}return h;}

/* ── Inline CSS ── */
const _CSS = ':host{--green:#22c55e;--green-dark:#16a34a;--green-light:#86efac;--green-ghost:rgba(34,197,94,0.08);--white:#FFFFFF;--bg:#FAFAFA;--text:#1D1D1F;--text-secondary:#86868B;--border:#E5E5EA;--border-light:#F2F2F7;--shadow-sm:0 1px 3px rgba(0,0,0,0.04);--shadow-md:0 4px 16px rgba(0,0,0,0.08);--shadow-lg:0 8px 32px rgba(0,0,0,0.12);--radius-sm:8px;--radius-md:12px;--radius-lg:16px;--radius-full:980px;--font:Inter,-apple-system,BlinkMacSystemFont,sans-serif;--transition:0.3s cubic-bezier(0.25,0.1,0.25,1);all:initial}*{box-sizing:border-box;margin:0;padding:0;font-family:var(--font)}'+
'.float-wrapper{position:fixed;bottom:24px;right:24px;z-index:99999;display:flex;flex-direction:column;align-items:center;gap:6px}'+
'.float-label{font-size:11px;color:var(--green);font-weight:500;white-space:nowrap;text-align:center;text-shadow:0 1px 3px rgba(255,255,255,0.8)}'+
'.floating-btn{width:52px;height:52px;background:transparent;border:2px solid var(--green);border-radius:50%;box-shadow:0 4px 16px rgba(34,197,94,0.3);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:transform 0.2s ease,box-shadow 0.2s ease;overflow:hidden;padding:0;animation:float-pulse 3s ease-in-out infinite}'+
'.floating-btn:hover{transform:scale(1.08);box-shadow:0 6px 24px rgba(34,197,94,0.5)}.floating-btn::after{content:"";position:absolute;inset:-3px;border-radius:50%;border:2px solid rgba(34,197,94,0.25);animation:ring-pulse 3s ease-in-out infinite}'+
'.floating-btn .btn-icon-img{width:100%;height:100%;border-radius:50%;object-fit:cover;object-position:center 25%}.panel-header .avatar img,.message .msg-avatar.bot img{width:100%;height:100%;border-radius:50%;object-fit:cover;object-position:center 25%}'+
'.chat-panel{position:fixed;z-index:99998;background:var(--white);border-radius:var(--radius-lg);box-shadow:var(--shadow-lg);display:flex;flex-direction:column;overflow:hidden;transition:all var(--transition);opacity:0;transform:scale(0.95);pointer-events:none}'+
'.chat-panel.open{opacity:1;transform:scale(1);pointer-events:all}.chat-panel.floating{top:96px;bottom:0;right:24px;width:420px;max-height:none}'+
'.chat-panel.fullscreen{top:0;left:0;width:100vw;height:100vh;border-radius:0}'+
'.panel-header{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;background:linear-gradient(135deg,var(--green),#4ade80);color:var(--white);flex-shrink:0}'+
'.panel-header .header-left{display:flex;align-items:center;gap:10px}.panel-header .avatar{width:30px;height:30px;background:rgba(255,255,255,0.3);border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:13px;overflow:hidden}'+
'.panel-header .title{font-weight:600;font-size:13px}.panel-header .subtitle{font-size:10px;opacity:0.85}.panel-header .header-actions{display:flex;gap:6px}'+
'.panel-header .header-btn{width:24px;height:24px;background:rgba(255,255,255,0.25);border:none;border-radius:5px;color:#FFF;font-size:12px;cursor:pointer;display:flex;align-items:center;justify-content:center}.panel-header .header-btn:hover{background:rgba(255,255,255,0.4)}'+
'.chat-panel-body{display:flex;flex:1;overflow:hidden}.floating .chat-panel-body{flex-direction:column}.fullscreen .chat-panel-body{flex-direction:row;align-items:stretch}.fullscreen .chat-panel-body>*{flex-shrink:0}'+
'.chat-column{display:flex;flex-direction:column;flex:1;min-width:0;overflow:hidden}.fullscreen .chat-column{flex:0 0 33.33%;min-width:280px;max-width:480px;border-right:0.5px solid var(--border)}'+
'.messages-container{flex:1;overflow-y:auto;padding:14px;background:var(--bg);display:flex;flex-direction:column;gap:10px}.message{display:flex;gap:8px;align-items:flex-start}.message.user{justify-content:flex-end}'+
'.message .msg-avatar{width:26px;height:26px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:600;color:#FFF;overflow:hidden}.message .msg-avatar.bot{background:var(--green)}.message .msg-avatar.user{background:#D1D1D6}'+
'.message .msg-bubble{padding:10px 12px;border-radius:10px 10px 10px 4px;font-size:12.5px;line-height:1.55;color:var(--text);background:var(--white);box-shadow:var(--shadow-sm);max-width:80%}.message.user .msg-bubble{background:var(--green);color:#FFF;border-radius:10px 10px 4px 10px}'+
'.result-card{background:var(--white);border-radius:10px;border:1px solid rgba(0,0,0,0.05);display:flex;overflow:hidden;transition:all 0.15s ease}.result-card:hover{border-color:rgba(34,197,94,0.12);box-shadow:0 2px 12px rgba(0,0,0,0.06)}.result-card .card-top{display:flex;flex:1;min-width:0}.result-card .card-body{flex:1;min-width:0;padding:14px 16px;display:flex;align-items:center;gap:14px}.result-card .card-info{flex:1;min-width:0;display:flex;flex-direction:column;gap:5px}.result-card .badge-row{display:flex;align-items:center;gap:8px;margin-bottom:0}'+
'.grade-badge{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;border-radius:50%;font-weight:700;font-size:10px;text-transform:uppercase;flex-shrink:0}.grade-badge.S{background:#22C55E;color:#FFF}.grade-badge.A{background:rgba(34,197,94,0.08);color:#16A34A;border:1px solid rgba(34,197,94,0.25)}.grade-badge.B{background:rgba(100,100,100,0.06);color:#666}.grade-badge.C{color:var(--text-secondary)}'+
'.card-name{font-size:14px;font-weight:600;color:var(--text)}.card-score{font-size:24px;font-weight:600;color:#22C55E;line-height:1}.card-score-label{font-size:10px;color:#86868B}.card-meta{font-size:11px;color:var(--text-secondary)}'+
'.card-chips{display:flex;gap:6px;flex-wrap:wrap}.chip{font-size:10px;border-radius:8px;padding:3px 8px;white-space:nowrap;border:none;font-weight:500}'+
'.card-actions{flex-shrink:0}.card-btn{font-size:11px;color:#22C55E;background:rgba(34,197,94,0.05);border:0.5px solid rgba(34,197,94,0.2);border-radius:6px;padding:5px 14px;cursor:pointer;white-space:nowrap;transition:all 0.15s ease}.card-btn:hover{background:#22C55E;color:#FFF}'+
'.action-bar{display:flex;gap:6px;margin-top:4px;flex-wrap:wrap}.action-btn{background:var(--green);border:none;border-radius:var(--radius-sm);padding:6px 14px;font-size:11px;color:#FFF;cursor:pointer;font-weight:500;transition:background 0.15s ease}.action-btn:hover{background:var(--green-dark)}.action-btn.secondary{background:transparent;border:0.5px solid var(--border);color:var(--text-secondary)}.action-btn.secondary:hover{border-color:var(--green);color:var(--green)}'+
'.input-bar{display:flex;gap:8px;padding:10px 14px;border-top:0.5px solid var(--border);background:var(--white);flex-shrink:0}.input-bar input{flex:1;padding:8px 12px;font-size:13px;border:1px solid var(--border);border-radius:20px;outline:none;background:var(--bg);transition:border-color 0.2s ease}.input-bar input:focus{border-color:var(--green)}.input-bar .send-btn{width:36px;height:36px;background:var(--green);border:none;border-radius:50%;color:#FFF;font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:background 0.15s ease}.input-bar .send-btn:hover{background:var(--green-dark)}.input-bar .send-btn:disabled{opacity:0.5;cursor:not-allowed}'+
'.fullscreen-panel{display:none;flex:1;background:var(--white);overflow-y:auto;padding:24px}.fullscreen .fullscreen-panel{display:block}'+
'.report-header{display:flex;gap:24px;align-items:stretch;margin-bottom:24px}.report-grade{text-align:center;flex-shrink:0}.report-info{flex:1}.report-name{font-size:1.75rem;font-weight:600;color:var(--text)}.report-meta{font-size:0.875rem;color:var(--text-secondary);margin-top:4px}.report-score{font-size:3rem;font-weight:300;color:var(--green)}'+
'.report-section{margin-top:20px}.report-section h4{font-weight:500;font-size:0.75rem;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px}.report-section p,.report-section li{font-size:0.875rem;color:var(--text);line-height:1.7}'+
'.compare-table{width:100%;border-collapse:collapse;font-size:0.8125rem;table-layout:fixed}.compare-table th,.compare-table td{padding:8px 12px;border-bottom:0.5px solid var(--border-light);vertical-align:top;word-break:break-word}.compare-table th{color:var(--text-secondary);font-weight:500;text-align:left;text-transform:uppercase;font-size:0.6875rem;letter-spacing:0.06em}.compare-table td{color:var(--text)}'+
'.cmp-score-cell{font-size:1.5rem;font-weight:300;color:var(--green)}.cmp-chips-cell{line-height:2}'+
'.cmp-table{width:100%;border-collapse:collapse;font-size:0.8125rem;table-layout:fixed}.cmp-table thead th{background:var(--green);color:#FFF;padding:10px 14px;font-weight:500;font-size:12px;text-align:center;word-break:break-word}.cmp-table thead th:first-child{border-radius:6px 0 0 0}.cmp-table thead th:last-child{border-radius:0 6px 0 0}'+
'.cmp-label-th{padding:10px 14px!important;text-align:left!important}.cmp-label{font-weight:600;font-size:11px;color:var(--text);text-align:left;white-space:nowrap}'+
'.cmp-table tbody td{padding:10px 14px;text-align:center;color:var(--text);vertical-align:middle}.cmp-table tbody td:first-child{text-align:left}'+
'.cmp-row-even td{background:var(--bg)}.cmp-row-odd td{background:var(--white)}.cmp-table tbody tr:hover td{background:var(--green-ghost)}'+
'.cmp-section-header td{background:var(--border-light)!important;font-weight:600;font-size:10px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.05em;padding:8px 14px!important}'+
'.profile-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}.detail-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}.detail-grid h4{font-weight:500;font-size:0.75rem;color:var(--text-secondary);text-transform:uppercase;margin-bottom:8px}.detail-col{background:var(--bg);border-radius:var(--radius-sm);padding:14px}.profile-grid h4{font-weight:500;font-size:0.75rem;color:var(--text-secondary);text-transform:uppercase;margin-bottom:8px}.info-row{font-size:0.8125rem;color:var(--text);margin:2px 0;display:flex;justify-content:space-between;padding:3px 0;border-bottom:0.5px solid var(--border-light)}.info-label{color:var(--text-secondary);flex-shrink:0}.info-val{color:var(--text);font-weight:500;text-align:right}'+
'.typing-indicator{display:flex;gap:4px;padding:8px 12px}.typing-indicator span{width:6px;height:6px;background:var(--border);border-radius:50%;animation:bounce 1.4s infinite ease-in-out both}.typing-indicator span:nth-child(1){animation-delay:-0.32s}.typing-indicator span:nth-child(2){animation-delay:-0.16s}@keyframes bounce{0%,80%,100%{transform:scale(0)}40%{transform:scale(1)}}'+
'.suggestion-chip{font-size:11px;color:var(--green);background:var(--green-ghost);border:0.5px solid rgba(34,197,94,0.2);border-radius:var(--radius-full);padding:4px 12px;cursor:pointer;transition:all 0.15s ease}.suggestion-chip:hover{background:rgba(34,197,94,0.15)}'+
'.reconnect-banner{background:#FEF3C7;color:#92400E;font-size:11px;text-align:center;padding:6px 10px;border-bottom:0.5px solid #FDE68A;flex-shrink:0}'+
'.messages-container::-webkit-scrollbar,.fullscreen-panel::-webkit-scrollbar{width:5px}.messages-container::-webkit-scrollbar-track,.fullscreen-panel::-webkit-scrollbar-track{background:transparent}.messages-container::-webkit-scrollbar-thumb,.fullscreen-panel::-webkit-scrollbar-thumb{background:#D1D1D6;border-radius:10px}.messages-container::-webkit-scrollbar-thumb:hover,.fullscreen-panel::-webkit-scrollbar-thumb:hover{background:var(--green)}'+
'.card-checkbox{accent-color:#22C55E;cursor:pointer;flex-shrink:0;width:16px;height:16px}.result-card:has(.card-checkbox:checked){border-color:rgba(34,197,94,0.3)!important;box-shadow:0 2px 12px rgba(34,197,94,0.1)}'+
'.card-avatar-wrap{width:72px;flex-shrink:0;display:flex;flex-direction:column;align-items:center;padding:14px 0 12px;gap:4px;background:linear-gradient(180deg,rgba(34,197,94,0.03) 0%,rgba(255,255,255,0) 100%)}.card-avatar{width:52px;height:65px;border-radius:10px;object-fit:cover;box-shadow:0 2px 6px rgba(0,0,0,0.12)}'+
'.report-avatar{width:130px;height:160px;border-radius:14px;object-fit:cover;object-position:center top;flex-shrink:0}.cmp-avatar{width:56px;height:70px;border-radius:10px;object-fit:cover;box-shadow:0 2px 6px rgba(0,0,0,0.12);display:block;margin:0 auto 6px}'+
'.resize-grip-top{display:none;height:6px;background:linear-gradient(135deg,var(--green),#4ade80);cursor:ns-resize;flex-shrink:0;transition:background 0.15s ease}.floating .resize-grip-top{display:block}.resize-grip-top:hover{background:var(--green-dark)}'+
'.resize-grip-right{display:none;width:6px;background:transparent;cursor:ew-resize;flex-shrink:0;transition:background 0.15s ease}.fullscreen .resize-grip-right{display:block}.resize-grip-right:hover{background:rgba(34,197,94,0.15)}'+
'@keyframes float-pulse{0%,100%{box-shadow:0 4px 16px rgba(34,197,94,0.4)}50%{box-shadow:0 4px 28px rgba(34,197,94,0.6)}}@keyframes ring-pulse{0%,100%{transform:scale(1);opacity:0.4}50%{transform:scale(1.12);opacity:0}}'+
'.loading-container{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;min-height:300px;gap:16px}.loading-spinner{width:48px;height:48px;position:relative}.spinner-ring{width:48px;height:48px;border:3px solid var(--border-light);border-top-color:var(--green);border-radius:50%;animation:spin 0.8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.loading-text{font-size:0.9375rem;font-weight:500;color:var(--text)}.loading-hint{font-size:0.75rem;color:var(--text-secondary)}';

(function() { if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function() { new TalentWidget(); }); else new TalentWidget(); })();
