/* MTP standalone render functions — used by talent-widget.js */

function _MTP_RENDER(data) {
  var d = data, av = d.avatar || '/widget/avatars/avatar-f-001.png';
  function s(v, def) { return (v != null && v !== "") ? String(v) : (def || "—"); }
  var h = d.history || {};

  function tbl(headers, rows, empty) {
    if (!rows || !rows.length)
      return '<table class="mt-tbl"><tbody><tr class="mt-empty"><td colspan="' + headers.length + '">' + (empty || "暂无数据") + '</td></tr></tbody></table>';
    var hh = '<thead><tr>' + headers.map(function(h) { return '<th>' + h + '</th>'; }).join("") + '</tr></thead>';
    var bb = '<tbody>' + rows.slice(0, 10).map(function(r) {
      return '<tr>' + headers.map(function(k) { return '<td>' + _esc(s(r[k], "")) + '</td>'; }).join("") + '</tr>';
    }).join("") + '</tbody>';
    return '<table class="mt-tbl">' + hh + bb + '</table>';
  }

  var tgColors = { tgR: "#FEE2E2", txR: "#991B1B", tgO: "#FFEDD5", txO: "#9A3412", tgB: "#DBEAFE", txB: "#1E40AF", tgG: "#DCFCE7", txG: "#166534", tgY: "#F3F4F6", txY: "#6B7280", tgT: "#CCFBF1", txT: "#134E4A", tgU: "#EDE9FE", txU: "#5B21B6", tgP: "#FCE7F3", txP: "#9D174D" };
  var pillData = [
    ["人才标签", ["tgR txR:高管理潜力", "tgR txR:绩效优秀", "tgR txR:双一流", "tgR txR:关键人才", "tgO txO:反躬", "tgO txO:高级职称", "tgO txO:演讲达人", "tgO txO:投资拓展", "tgP txP:洞察分析"]],
    ["能力标签", ["tgB txB:英语", "tgB txB:高潜", "tgB txB:项目管理", "tgB txB:法语", "tgB txB:测试B", "tgB txB:海外储备", "tgG txG:条理清晰", "tgG txG:沟通强", "tgG txG:沟通协调", "tgG txG:日语", "tgG txG:计划执行"]],
    ["系统标签", ["tgY txY:不稳定", "tgY txY:预警", "tgY txY:一般", "tgT txT:维保休", "tgU txU:团队建设"]]
  ];
  var pillsHtml = "";
  pillData.forEach(function(g) {
    pillsHtml += '<div class="mt-ts">' + g[0] + '</div>';
    g[1].forEach(function(p) {
      var x = p.split(":"), c = x[0].split(" ");
      pillsHtml += '<span class="mt-tg" style="background:' + tgColors[c[0]] + ';color:' + tgColors[c[1]] + '">' + x[1] + '</span>';
    });
  });

  var badges = [];
  function bdg(v, cls) { badges.push('<span class="mt-bd' + (cls ? " " + cls : "") + '">' + v + '</span>'); }
  if (d["关键人才"] == "是") bdg("关键人才", "key");
  if (d["国际化人才"] == "是") bdg("国际化人才");
  if (d["海外战略储备"] == "是") bdg("海外战略储备");
  if (d["XPM领域"] && d["XPM领域"] !== "否") bdg(_esc(d["XPM领域"]));
  if (d["内部拓展师等级"]) bdg(_esc(d["内部拓展师等级"]));
  if (d["综合等级"]) bdg(_esc(d["综合等级"]));
  if (d["是否工艺师"] == "是") bdg("工艺师", "hot");
  if (d["海外工作"] == "是") bdg("海外工作");
  if (d["精英MBA班"] == "是") bdg("精英MBA", "hot");

  var gx = parseInt(d["人才盘点_九宫格X"]) || 2, gy = parseInt(d["人才盘点_九宫格Y"]) || 2;
  var gl = [["明日之星", "明星骨干", "超级明星"], ["中坚力量", "优秀骨干", "高潜人才"], ["发展乏力", "稳定贡献", "需要辅导"]];
  var gh = "";
  for (var yr = 0; yr < 3; yr++)
    for (var xc = 0; xc < 3; xc++) {
      var gdY = 3 - yr, gdX = xc + 1;
      gh += '<div class="mt-gc' + (gdY === gy && gdX === gx ? " mt-ga" : "") + '">' + gl[yr][xc] + '</div>';
    }

  var mgmtSum = (parseFloat(d["管理技能_计划"]) || 0) + (parseFloat(d["管理技能_组织"]) || 0) + (parseFloat(d["管理技能_领导"]) || 0) + (parseFloat(d["管理技能_控制"]) || 0);
  var mgmtAvg = (mgmtSum / 4).toFixed(1);

  var langRows = d["语言能力_语种"] ? [{ 语种: d["语言能力_语种"], 熟练程度: d["语言能力_熟练程度"], 证书: d["语言能力_证书"], 分数: d["语言能力_分数"] }] : [];

  var H = [];

  H.push(
    '<div class="mt-topbar">MTP人才画像</div>',
    '<div class="mt-main">',
    '<div class="mt-sec"><div class="mt-sh">👤 基本信息</div>',
    '<div class="mt-ph"><img class="mt-av" src="' + av + '" onerror="this.style.display=\'none\'"><div class="mt-pi">',
    '<div class="mt-nm">' + _esc(s(d["姓名"])) + ' / ' + _esc(s(d.id || d["员工编码"])) + '</div>',
    '<div class="mt-dp"><strong>' + _esc(s(d["所在职位"])) + '</strong> ｜ ' + _esc(s(d["职级"])) + ' ｜ ' + _esc(s(d["职等"])) + '等 ｜ 任职' + _esc(s(d["担任当前职位时长"])) + '年</div>',
    '<div class="mt-mm">' + _esc(s(d["性别"])) + ' ｜ ' + _esc(s(d["年龄"])) + '岁 ｜ ' + _esc(s(d["民族"])) + ' ｜ ' + _esc(s(d["国籍"])) + ' ｜ ' + _esc(s(d["政治面貌"])) + ' ｜ ' + _esc(s(d["婚姻状况"])) + '</div>',
    '<div class="mt-mm">📍 ' + _esc(s(d["家庭住址"])) + ' ｜ 🏠 ' + _esc(s(d["籍贯"])) + (d["特长爱好"] ? ' ｜ ❤️ ' + _esc(d["特长爱好"]) : '') + '</div>',
    '<div class="mt-mm">岗龄' + _esc(s(d["担任当前职位时长"])) + '年 ｜ 任期' + _esc(s(d["当前任期"])) + '年 ｜ 司龄' + _esc(s(d["司龄"])) + '年 ｜ 上级：' + _esc(s(d["工作上级"])) + '</div>',
    '<div class="mt-br">' + badges.join(" ") + '</div></div>',
    '<div class="mt-tc">' + pillsHtml + '</div></div>',
    '<div class="mt-ed"><div class="mt-eh">📚 教育经历</div>',
    '<div class="mt-ec"><div class="mt-en">' + _esc(s(d["最高学历毕业院校"])) + '</div><div class="mt-edt">' + _esc(s(d["最高学历专业"])) + ' ｜ ' + _esc(s(d["最高学历"])) + ' ｜ ' + _esc(s(d["最高学历毕业时间"])) + '</div></div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">📊 人才盘点 &amp; 绩效 &amp; 综合考评 &amp; 日常过程评价</div><div class="mt-r4">',
    '<div class="mt-cl"><div class="mt-ch">人才盘点</div><div class="mt-gw"><div style="font-size:11px;color:#9CA3AF;margin-bottom:5px">' + s(d["人才盘点_年度"]) + '</div>',
    '<div class="mt-go"><div class="mt-gy"><span>▲ 高</span><span>潜力</span><span>▼ 低</span></div><div class="mt-g9">' + gh + '</div></div>',
    '<div class="mt-gx"><span>← 绩效 低</span><span>绩效 高 →</span></div></div></div>',
    '<div class="mt-cl"><div class="mt-ch">绩效</div>' + tbl(["年度", "绩效等级", "绩效分数"], h["工作业绩"], "暂无") + '</div>',
    '<div class="mt-cl"><div class="mt-ch">综合考评</div>' + tbl(["年度", "考评结果", "评价记录"], h["干部年度考评"], "暂无") + '</div>',
    '<div class="mt-cl"><div class="mt-ch">日常过程评价</div>' + tbl(["评价日期", "评价场景", "评语"], h["日常过程评价"], "暂无") + '</div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">💼 外部/内部工作履历 &amp; 外派经历</div><div class="mt-r3">',
    '<div class="mt-cl"><div class="mt-ch">外部工作履历</div>' + tbl(["开始日期", "结束日期", "单位", "职位"], h["外部工作履历"], "暂无外部工作经历") + '</div>',
    '<div class="mt-cl"><div class="mt-ch">内部工作履历</div>' + tbl(["主兼岗", "开始日期", "部门", "岗位"], h["内部工作履历"], "暂无内部调动记录") + '</div>',
    '<div class="mt-cl"><div class="mt-ch">外派经历</div>' + tbl(["日期", "外派部门", "外派岗位", "外派地"], h["外派经历"], "暂无外派经历") + '</div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">🎓 培训经历 &amp; 职级职等经历 &amp; 荣誉称号&amp;奖项 &amp; 负面信息</div><div class="mt-r2">',
    '<div class="mt-cl"><div class="mt-ch">培训经历</div>' + tbl(["开始日期", "结束日期", "培训项目名称", "培训机构", "结业状态"], h["培训经历"], "暂无培训记录") + '</div>',
    '<div class="mt-cl"><div class="mt-ch">职级职等经历</div>' + tbl(["晋升日期", "原职级", "原职等", "新职级", "新职等", "停等时间(年)"], h["晋升履历"], "暂无晋升记录") + '<div class="mt-cw" style="max-width:440px;margin:10px auto 0"><canvas id="mtp-promo-ch" height="200"></canvas></div></div>',
    '</div><div class="mt-r2" style="padding-top:0">',
    '<div class="mt-cl"><div class="mt-ch">荣誉称号&amp;奖项</div>' + tbl(["日期", "奖项类型", "奖项名称"], h["荣誉称号"], "暂无") + '</div>',
    '<div class="mt-cl"><div class="mt-ch">负面信息</div>' + tbl(["日期", "处罚类型", "处罚原因", "备注"], h["奖惩信息"], "暂无") + '</div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">👨‍👩‍👧 亲属关系</div><div class="mt-sb">',
    tbl(["亲属关系", "亲属关系类型", "亲属工号", "亲属姓名", "所在公司", "业务类型", "担任角色"], h["亲属关系"], "无亲属在公司任职"),
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">📋 项目经验 &amp; 领域经验</div><div class="mt-r2">',
    '<div class="mt-cl"><div class="mt-ch">项目经验</div>' + tbl(["项目类别", "关联领域", "项目等级", "项目名称", "项目角色"], h["项目经验"], "暂无") + '</div>',
    '<div class="mt-cl"><div class="mt-ch">领域经验</div><div class="mt-cw" style="max-width:340px;margin:0 auto"><canvas id="mtp-domain-ch" height="200"></canvas></div></div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">🌏 海外经验 &amp; 服务客户经验 &amp; 整机or零件经验</div><div class="mt-r3">',
    '<div class="mt-cl"><div class="mt-ch">海外经验</div><div class="mt-cw" style="max-width:260px;margin:0 auto"><canvas id="mtp-os-ch" height="170"></canvas></div></div>',
    '<div class="mt-cl"><div class="mt-ch">服务客户经验</div><div class="mt-cw" style="max-width:260px;margin:0 auto"><canvas id="mtp-cl-ch" height="170"></canvas></div></div>',
    '<div class="mt-cl"><div class="mt-ch">整机or零件经验</div><div class="mt-cw" style="max-width:260px;margin:0 auto"><canvas id="mtp-mc-ch" height="170"></canvas></div></div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">🎯 干部通用能力 &amp; MTP专业能力</div><div class="mt-r2">',
    '<div class="mt-cl" style="text-align:center"><div class="mt-ch">干部通用能力</div><div class="mt-cw" style="max-width:320px;margin:0 auto"><canvas id="mtp-ca-rd" height="280"></canvas></div></div>',
    '<div class="mt-cl" style="text-align:center"><div class="mt-ch">MTP专业能力</div><div class="mt-cw" style="max-width:400px;margin:0 auto"><canvas id="mtp-mt-ln" height="220"></canvas></div></div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">🛡️ 企业精神 &amp; 价值观 &amp; 干部精神品格</div><div class="mt-r3">',
    '<div class="mt-cl" style="text-align:center"><div class="mt-ch">企业精神</div><div class="mt-cw" style="max-width:240px;margin:0 auto"><canvas id="mtp-sp-rd" height="220"></canvas></div></div>',
    '<div class="mt-cl" style="text-align:center"><div class="mt-ch">价值观</div><div class="mt-cw" style="max-width:240px;margin:0 auto"><canvas id="mtp-vl-rd" height="220"></canvas></div></div>',
    '<div class="mt-cl" style="text-align:center"><div class="mt-ch">干部精神品格</div><div class="mt-cw" style="max-width:240px;margin:0 auto"><canvas id="mtp-cr-rd" height="220"></canvas></div></div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">📈 管理技能</div><div class="mt-flex2" style="padding:12px 16px">',
    '<div class="mt-cl" style="flex:1"><div class="mt-sh2"><div class="mt-sb2">' + mgmtAvg + '</div><div class="mt-sl2">总分</div></div><div style="font-size:12px;color:#86868B;line-height:1.8">整体表现中等偏高。计划、控制方面发展成熟度高。</div></div>',
    '<div class="mt-cl" style="flex:2"><div class="mt-cw" style="max-width:500px;margin:0 auto"><canvas id="mtp-mg-ln" height="190"></canvas></div></div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">🗣️ 语言能力 &amp; 行业头衔</div><div class="mt-r2">',
    '<div class="mt-cl"><div class="mt-ch">语言能力</div>' + tbl(["语种", "熟练程度", "证书", "分数"], langRows, "暂无") + '</div>',
    '<div class="mt-cl"><div class="mt-ch">行业头衔</div>' + tbl(["头衔"], [], "暂无行业头衔") + '</div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">🏆 专利 &amp; 论文 &amp; 专著 &amp; 技术标准</div><div class="mt-r4">',
    '<div class="mt-cl"><div class="mt-ch">专利</div>' + tbl(["获得日期", "专利类型", "专利名称", "专利号"], h["专利"], "暂无专利") + '</div>',
    '<div class="mt-cl"><div class="mt-ch">论文</div>' + tbl(["发表日期", "论文名称", "排名", "出版社刊物名称"], h["论文"], "暂无论文") + '</div>',
    '<div class="mt-cl"><div class="mt-ch">专著</div>' + tbl(["发表时间", "专著名称", "出版社名称"], h["专著"], "暂无专著") + '</div>',
    '<div class="mt-cl"><div class="mt-ch">技术标准</div>' + tbl(["发布时间", "标准类型", "标准名称", "名次"], [], "暂无") + '</div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">🧠 管理个性</div><div class="mt-flex2" style="padding:12px 16px">',
    '<div class="mt-cl" style="flex:1"><div class="mt-sh2"><div class="mt-sb2">' + _esc(s(d["管理个性类型"])) + '</div><div class="mt-sl2">管理个性类型</div></div></div>',
    '<div class="mt-cl" style="flex:2"><div class="mt-cw" style="max-width:520px;margin:0 auto"><canvas id="mtp-ps-ch" height="200"></canvas></div></div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">💡 潜力 &amp; 商业综合推理能力</div><div class="mt-r2">',
    '<div class="mt-cl"><div class="mt-ch">潜力</div><div class="mt-sh2"><div class="mt-sb2">' + _esc(s(d["潜力等级"])) + '</div></div><div class="mt-cw" style="max-width:280px;margin:0 auto"><canvas id="mtp-pt-ch" height="170"></canvas></div></div>',
    '<div class="mt-cl"><div class="mt-ch">商业综合推理能力</div><div class="mt-sh2"><div class="mt-sb2">' + _esc(s(d["商业综合推理能力"])) + '<span style="font-size:15px;color:#86868B;font-weight:400"> 分</span></div></div><div class="mt-cw" style="max-width:280px;margin:0 auto"><canvas id="mtp-bz-ch" height="170"></canvas></div></div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">📝 个人评价 &amp; 职业规划</div><div class="mt-r2">',
    '<div class="mt-cl"><div class="mt-ch">个人评价</div><div class="mt-tx">' + _esc(s(d["个人评价"])) + '</div></div>',
    '<div class="mt-cl"><div class="mt-ch">职业规划</div><div class="mt-tx">' + _esc(s(d["职业规划"])) + '</div></div>',
    '</div></div>'
  );

  H.push(
    '<div class="mt-sec"><div class="mt-sh">🚀 个人发展任用计划</div><div class="mt-sb"><div class="mt-tx">' + _esc(s(d["发展任用计划"])) + '</div></div></div>',
    '</div>'
  );

  return H.join("");
}

function _MTP_CHARTS(data, fp, chartInstances) {
  if (!window.Chart || !data || !fp) return;
  var d = data, h = d.history || {};

  function h2r(hex, a) { var r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16); return "rgba(" + r + "," + g + "," + b + "," + a + ")"; }
  function g(k) { return parseFloat(d[k]) || 0; }

  function radar(id, labels, values, color, max) {
    var c = fp.querySelector("#mtp-" + id); if (!c) return; max = max || 5;
    var ch = new Chart(c, { type: "radar", data: { labels: labels, datasets: [{ data: values, backgroundColor: h2r(color, 0.06), borderColor: color, borderWidth: 1.2, pointRadius: 3.5, pointBackgroundColor: color, pointBorderColor: "#FFF", pointBorderWidth: 1.5 }] }, options: { responsive: true, maintainAspectRatio: false, scales: { r: { beginAtZero: true, max: max, ticks: { stepSize: 1, font: { size: 10 }, backdropColor: "transparent", color: "#B0BEC5" }, pointLabels: { font: { size: 11 }, color: "#455A64" }, grid: { color: "#E8ECF0", lineWidth: 0.6 }, angleLines: { color: "#E8ECF0", lineWidth: 0.4 } } }, plugins: { legend: { display: false } } } });
    chartInstances.push(ch);
  }
  function barH(id, labels, values, color, max) {
    var c = fp.querySelector("#mtp-" + id); if (!c) return; max = max || 5;
    var ch = new Chart(c, { type: "bar", data: { labels: labels, datasets: [{ data: values, backgroundColor: color, borderRadius: 4, borderSkipped: false }] }, options: { responsive: true, maintainAspectRatio: false, indexAxis: "y", scales: { x: { beginAtZero: true, max: max, ticks: { font: { size: 9 } }, grid: { color: "#F3F4F6" } }, y: { ticks: { font: { size: 10 } }, grid: { display: false } } }, plugins: { legend: { display: false } } } });
    chartInstances.push(ch);
  }
  function line(id, labels, values, color, max) {
    var c = fp.querySelector("#mtp-" + id); if (!c) return; max = max || 10;
    var ch = new Chart(c, { type: "line", data: { labels: labels, datasets: [{ data: values, borderColor: color, borderWidth: 2.5, pointRadius: 4, pointBackgroundColor: color, tension: 0.3, fill: false }] }, options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: max, ticks: { font: { size: 9 } }, grid: { color: "#F3F4F6" } }, x: { ticks: { font: { size: 10 } }, grid: { display: false } } }, plugins: { legend: { display: false } } } });
    chartInstances.push(ch);
  }

  Chart.defaults.font.family = '-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif';
  Chart.defaults.font.size = 12;

  var pl = [], pv = [];
  (h["晋升履历"] || []).forEach(function(r) { pl.push(r["晋升日期"] || ""); pv.push(parseInt(r["新职等"] || "0")); });
  if (!pl.length) { pl = ["入职"]; pv = [parseInt(d["职等"]) || 1]; }
  line("promo-ch", pl, pv, "#8B5CF6", Math.max(5, Math.max.apply(null, pv) + 5));

  var dl = [], dv = [], ds = d["曾工作领域及年限"] || "";
  ds.split("),").forEach(function(p) { var m = p.match(/^(.+?)\((\d+)年\)/); if (m) { dl.push(m[1]); dv.push(parseInt(m[2])); } });
  if (!dl.length) { dl = ["管理经验"]; dv = [parseInt(d["曾工作领域个数"]) || 1]; }
  barH("domain-ch", dl, dv, "#22c55e", Math.max(5, Math.max.apply(null, dv) + 2));

  var ol = [], ov = [];
  (h["地域工作经历"] || []).forEach(function(r) { if (r["国家"] && r["国家"] !== "中国") { ol.push(r["国家"]); ov.push(2); } });
  if (!ol.length) { ol = ["暂无"]; ov = [0]; }
  barH("os-ch", ol, ov, "#3B82F6", Math.max(5, Math.max.apply(null, ov) + 2));

  var cl = [], cv = [], cs = d["服务客户经验"] || "";
  cs.split(",").forEach(function(p) { var m = p.match(/^(.+?)\((\d+)年\)/); if (m) { cl.push(m[1]); cv.push(parseInt(m[2])); } });
  if (!cl.length) { cl = ["暂无"]; cv = [0]; }
  barH("cl-ch", cl, cv, "#F97316", Math.max(5, Math.max.apply(null, cv) + 2));

  barH("mc-ch", ["零件", "整机"], [3, 3], "#14B8A6", 5);

  radar("ca-rd", ["变革创新力", "沟通影响力", "规划执行力", "组织发展力"], [g("干部通用能力_变革创新力"), g("干部通用能力_沟通影响力"), g("干部通用能力_规划执行力"), g("干部通用能力_组织发展力")], "#5470C6", 5);
  radar("sp-rd", ["艰苦奋斗", "追求卓越", "实事求是", "创新进取", "合作共赢"], [g("企业精神_艰苦奋斗"), g("企业精神_追求卓越"), g("企业精神_实事求是"), g("企业精神_创新进取"), g("企业精神_合作共赢")], "#3BA272", 5);
  radar("vl-rd", ["客户导向", "质量优先", "合规经营", "社会责任", "员工发展"], [g("价值观_客户导向"), g("价值观_质量优先"), g("价值观_合规经营"), g("价值观_社会责任"), g("价值观_员工发展")], "#FAC858", 5);
  radar("cr-rd", ["担当", "廉洁", "正直", "奉献", "公正"], [g("干部精神品格_担当"), g("干部精神品格_廉洁"), g("干部精神品格_正直"), g("干部精神品格_奉献"), g("干部精神品格_公正")], "#EE6666", 5);

  line("mt-ln", ["商务能力", "成本控制", "项目管理", "研发能力", "工程能力"], [g("MTP专业能力_商务能力"), g("MTP专业能力_成本控制能力"), g("MTP专业能力_项目管理能力"), g("MTP专业能力_研发能力"), g("MTP专业能力_工程能力")], "#73C0DE", 5);
  line("mg-ln", ["计划", "组织", "领导", "控制"], [g("管理技能_计划"), g("管理技能_组织"), g("管理技能_领导"), g("管理技能_控制")], "#91CC75", 10);

  barH("ps-ch", ["外向性", "亲和性", "尽责性", "情绪稳定性", "开放性"], [g("管理个性_外向性"), g("管理个性_亲和性"), g("管理个性_尽责性"), g("管理个性_情绪稳定性"), g("管理个性_开放性")], "#FC8452", 10);
  barH("pt-ch", ["战略思维", "学习敏锐度", "结果导向", "人际影响力"], [g("潜力_战略思维"), g("潜力_学习敏锐度"), g("潜力_结果导向"), g("潜力_人际影响力")], "#EE6666", 10);
  barH("bz-ch", ["分析判断", "决策力", "市场洞察"], [g("商业综合推理_分析判断"), g("商业综合推理_决策力"), g("商业综合推理_市场洞察")], "#5470C6", 10);
}
