// 頭頂星空：天象行事曆。流星雨、日月食、行星、月相與節氣，全部用 Astronomy Engine 在手機上計算（不需要網路）。
// SkyEvents.list(A, lat, lon, from, days) 回傳事件陣列；SkyEvents.ics(events, loc) 產生 iCalendar；SkyEvents.google(ev) 產生 Google 日曆連結。
(function (root) {
'use strict';
const DEG = Math.PI / 180, RAD = 180 / Math.PI, DAY = 86400000;
const pad = (n) => String(n).padStart(2, '0');
const WEEK = '日一二三四五六';
const hhmm = (d) => pad(d.getHours()) + ':' + pad(d.getMinutes());
const md = (d) => (d.getMonth() + 1) + '/' + d.getDate() + '（' + WEEK[d.getDay()] + '）';
const mdhm = (d) => md(d) + ' ' + hhmm(d);
const fmtMag = (m) => (m < 0 ? '−' + Math.abs(m).toFixed(1) : m.toFixed(1)) + ' 等';
const DIR8 = ['北', '東北', '東', '東南', '南', '西南', '西', '西北'];
const dirName = (az) => DIR8[Math.round(((az % 360) + 360) % 360 / 45) % 8];

// IMO 流星雨工作表（極大的太陽黃經為 J2000.0 分點；ZHR 為理想暗空、輻射點在天頂時每小時流星數）
const SHOWERS = [
  { id: 'QUA', zh: '象限儀座流星雨', lon: 283.15, zhr: 80, ra: 230, dec: 49, con: '牧夫座北邊（舊象限儀座）', parent: '小行星 2003 EH1', extra: '極大很短，只有幾個小時。' },
  { id: 'LYR', zh: '天琴座流星雨', lon: 32.32, zhr: 18, ra: 271, dec: 34, con: '天琴座', parent: '柴契爾彗星' },
  { id: 'ETA', zh: '寶瓶座 η 流星雨', lon: 45.5, zhr: 50, ra: 338, dec: -1, con: '寶瓶座', parent: '哈雷彗星', extra: '輻射點天亮前才升起，低緯度的台灣比歐美好看。' },
  { id: 'PER', zh: '英仙座流星雨', lon: 140.0, zhr: 100, ra: 48, dec: 58, con: '英仙座', parent: '斯威夫特－塔特爾彗星' },
  { id: 'DRA', zh: '天龍座流星雨', lon: 195.4, zhr: 10, ra: 262, dec: 54, con: '天龍座', parent: '賈可比尼－津納彗星', extra: '一般年份數量少，偶爾會爆發。' },
  { id: 'ORI', zh: '獵戶座流星雨', lon: 208, zhr: 20, ra: 95, dec: 16, con: '獵戶座', parent: '哈雷彗星' },
  { id: 'LEO', zh: '獅子座流星雨', lon: 235.27, zhr: 15, ra: 152, dec: 22, con: '獅子座', parent: '坦普爾－塔特爾彗星' },
  { id: 'GEM', zh: '雙子座流星雨', lon: 262.2, zhr: 150, ra: 112, dec: 33, con: '雙子座', parent: '小行星法厄同', extra: '一年中最穩定、數量最多的流星雨。' },
  { id: 'URS', zh: '小熊座流星雨', lon: 270.7, zhr: 10, ra: 217, dec: 76, con: '小熊座', parent: '塔特爾彗星' }
];
const PLANET_ZH = { Mercury: '水星', Venus: '金星', Mars: '火星', Jupiter: '木星', Saturn: '土星', Uranus: '天王星', Neptune: '海王星' };
const SUPERMOON_KM = 360000; // 滿月時地心距離小於 36 萬公里，稱為超級月亮

function list(A, lat, lon, from, days) {
  const obs = new A.Observer(lat, lon, 0);
  const t0 = A.MakeTime(from), end = new Date(from.getTime() + days * DAY);
  const out = [];
  const ECL = A.Rotation_EQJ_ECL();
  const altOf = (body, t) => { const e = A.Equator(body, t, obs, true, true); return A.Horizon(t, obs, e.ra, e.dec, 'normal'); };
  const radAlt = (s, t) => A.Horizon(t, obs, s.ra / 15, s.dec, 'normal').altitude;
  const inWin = (d) => d >= from && d < end;
  const add = (ev) => { if (inWin(ev.at)) out.push(ev); };

  // ---- 流星雨：太陽黃經（J2000 黃道）到達 IMO 極大值的時刻
  const sunLonJ2000 = (t) => { const v = A.RotateVector(ECL, A.GeoVector('Sun', t, true)); return ((Math.atan2(v.y, v.x) * RAD) % 360 + 360) % 360; };
  // 下一次太陽 J2000 黃經到達 target 的時刻：從平均速度估計，再用牛頓法修正（太陽每天約走 0.9856°）
  const sunLonTime = (target, start) => {
    let t = start.AddDays(((target - sunLonJ2000(start)) % 360 + 360) % 360 / 0.985647);
    for (let i = 0; i < 8; i++) {
      const d = ((target - sunLonJ2000(t) + 540) % 360) - 180;
      t = t.AddDays(d / 0.985647);
      if (Math.abs(d) < 1e-7) break;
    }
    return t;
  };
  for (const s of SHOWERS) {
    let peak = sunLonTime(s.lon, t0);
    if (peak.date < from) peak = sunLonTime(s.lon, peak.AddDays(30));
    if (!inWin(peak.date)) continue;
    // 極大前後 16 小時內，天色全暗（太陽低於 −12°）且輻射點高於 10° 的時段
    const runs = []; let cur = null;
    for (let m = -16 * 60; m <= 16 * 60; m += 10) {
      const t = peak.AddDays(m / 1440);
      const ok = altOf('Sun', t).altitude < -12;
      const ra = ok ? radAlt(s, t) : -90;
      if (ok && ra > 10) {
        const mo = altOf('Moon', t).altitude;
        if (!cur) { cur = { a: t, b: t, best: t, bestAlt: ra, n: 0, moonUp: 0 }; runs.push(cur); }
        cur.b = t; cur.n++; if (mo > 0) cur.moonUp++;
        if (ra > cur.bestAlt) { cur.bestAlt = ra; cur.best = t; }
      } else cur = null;
    }
    const dist = (r) => (peak.ut < r.a.ut ? r.a.ut - peak.ut : peak.ut > r.b.ut ? peak.ut - r.b.ut : 0);
    runs.sort((p, q) => dist(p) - dist(q) || q.bestAlt - p.bestAlt);
    const r = runs[0];
    let note, moonTxt = '', level = '', viewAt = peak.date, dtStart = peak.date, dtEnd = new Date(peak.date.getTime() + 3600000);
    if (r) {
      const k = A.Illumination('Moon', r.best).phase_fraction;
      const impact = k * (r.moonUp / r.n);
      level = impact < 0.2 ? '小' : impact < 0.5 ? '中' : '大';
      moonTxt = '月光影響' + level + '（月亮亮面 ' + Math.round(k * 100) + '%' + (r.moonUp === 0 ? '，觀賞時段月亮不在天上' : r.moonUp === r.n ? '，整段時間月亮都在天上' : '') + '）';
      const rate = Math.max(1, Math.round(s.zhr * Math.sin(r.bestAlt * DEG)));
      note = '最佳觀賞：' + mdhm(r.a.date) + '–' + hhmm(r.b.date) + '，' + hhmm(r.best.date) + ' 輻射點最高（' + Math.round(r.bestAlt) + '°）；暗空下每小時約 ' + rate + ' 顆。' + moonTxt + '。';
      viewAt = r.best.date; dtStart = r.a.date; dtEnd = new Date(r.b.date.getTime() + 600000);
    } else note = '極大前後的夜晚，輻射點在你的位置升得不夠高，不易觀賞。';
    out.push({
      type: 'meteor', id: 'met-' + s.id + '-' + peak.date.getUTCFullYear(), title: s.zh + '極大', at: peak.date, viewAt, dtStart, dtEnd,
      desc: '輻射點在' + s.con + '，ZHR 約 ' + s.zhr + '，母天體為' + s.parent + '。' + (s.extra || ''),
      note, moon: level, radiant: [s.ra, s.dec]
    });
  }

  // ---- 月食
  try {
    let le = A.SearchLunarEclipse(t0.AddDays(-1));
    for (let i = 0; i < 6 && le.peak.date < end; i++) {
      const pk = le.peak;
      const KIND = { penumbral: '半影月食', partial: '月偏食', total: '月全食' };
      const at = (min) => new Date(pk.date.getTime() + min * 60000);
      const ph = [['半影食始', -le.sd_penum]];
      if (le.sd_partial > 0) ph.push(['初虧', -le.sd_partial]);
      if (le.sd_total > 0) ph.push(['食既', -le.sd_total]);
      ph.push(['食甚', 0]);
      if (le.sd_total > 0) ph.push(['生光', le.sd_total]);
      if (le.sd_partial > 0) ph.push(['復圓', le.sd_partial]);
      ph.push(['半影食終', le.sd_penum]);
      const alts = ph.map(([, m]) => altOf('Moon', A.MakeTime(at(m))).altitude);
      const peakAlt = altOf('Moon', pk).altitude;
      const anyUp = alts.some((a) => a > 0);
      const vis = peakAlt > 0 ? '本地看得到：食甚時月亮高度 ' + Math.round(peakAlt) + '°' : anyUp ? '本地只看得到部分過程（食甚時月亮在地平線下）' : '本地看不到（整個過程月亮都在地平線下）';
      add({
        type: 'eclipse', id: 'lun-' + pk.date.toISOString().slice(0, 10), title: KIND[le.kind], at: pk.date, viewAt: pk.date,
        dtStart: at(-le.sd_penum), dtEnd: at(le.sd_penum), visible: anyUp,
        desc: (le.kind === 'penumbral' ? '月亮只進入地球的半影，亮度變暗不明顯。' : le.kind === 'total' ? '月亮完全進入地球本影，會變成暗紅色的「血月」。' : '月亮一部分進入地球本影，看起來像被咬了一口。') + '食分 ' + (le.obscuration * 100).toFixed(0) + '%（本影遮住月面的比例）。',
        note: vis + '。' + ph.map(([n, m]) => n + ' ' + hhmm(at(m))).join('、') + '。'
      });
      le = A.NextLunarEclipse(pk);
    }
  } catch (e) { /* ignore */ }

  // ---- 日食（全球列表，另外判斷你的位置看不看得到）
  try {
    let ge = A.SearchGlobalSolarEclipse(t0.AddDays(-1));
    for (let i = 0; i < 6 && ge.peak.date < end; i++) {
      const KIND = { partial: '日偏食', annular: '日環食', total: '日全食', hybrid: '全環食' };
      let loc = null;
      try {
        const l = A.SearchLocalSolarEclipse(ge.peak.AddDays(-1), obs);
        if (Math.abs(l.peak.time.ut - ge.peak.ut) < 1) loc = l;
      } catch (e) { /* none */ }
      const up = loc && [loc.partial_begin, loc.peak, loc.partial_end].some((x) => x && x.altitude > 0);
      let note, dtStart = ge.peak.date, dtEnd = new Date(ge.peak.date.getTime() + 3600000), viewAt = ge.peak.date;
      if (up) {
        const p = loc.peak;
        note = '本地看得到' + (loc.kind !== ge.kind ? '（你的位置是' + KIND[loc.kind] + '）' : '') + '：初虧 ' + hhmm(loc.partial_begin.time.date) +
          (loc.total_begin ? '、食既 ' + hhmm(loc.total_begin.time.date) : '') + '、食甚 ' + hhmm(p.time.date) + '（太陽高度 ' + Math.round(p.altitude) + '°，遮住 ' + Math.round(loc.obscuration * 100) + '%）' +
          (loc.total_end ? '、生光 ' + hhmm(loc.total_end.time.date) : '') + '、復圓 ' + hhmm(loc.partial_end.time.date) + '。一定要用合格的日食眼鏡或減光濾鏡觀看。';
        dtStart = loc.partial_begin.time.date; dtEnd = loc.partial_end.time.date; viewAt = p.time.date;
      } else {
        const lat2 = ge.latitude, lon2 = ge.longitude;
        note = '本地看不到。' + (lat2 != null ? '食甚約在 ' + Math.abs(lat2).toFixed(0) + '°' + (lat2 >= 0 ? 'N' : 'S') + ' ' + Math.abs(lon2).toFixed(0) + '°' + (lon2 >= 0 ? 'E' : 'W') + ' 附近。' : '');
      }
      out.push({ type: 'eclipse', id: 'sol-' + ge.peak.date.toISOString().slice(0, 10), title: KIND[ge.kind], at: ge.peak.date, viewAt, dtStart, dtEnd, visible: !!up,
        desc: (ge.kind === 'total' ? '月亮完全遮住太陽，白天會暗下來，看得到日冕。' : ge.kind === 'annular' ? '月亮比太陽小一點，遮不住邊緣，形成一圈「金環」。' : '月亮只遮住太陽的一部分。') + '全球食甚 ' + mdhm(ge.peak.date) + '。',
        note });
      ge = A.NextGlobalSolarEclipse(ge.peak);
    }
  } catch (e) { /* ignore */ }
  for (let i = out.length - 1; i >= 0; i--) if (out[i].type === 'eclipse' && !inWin(out[i].at)) out.splice(i, 1);

  // ---- 行星：外行星衝、內行星大距
  for (const b of ['Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']) {
    try {
      const t = A.SearchRelativeLongitude(b, 0, t0);
      if (!t || !inWin(t.date)) continue;
      const mag = A.Illumination(b, t).mag;
      const tr = A.SearchHourAngle(b, obs, 0, t.AddDays(-0.5), +1);
      const naked = mag < 6;
      out.push({ type: 'planet', id: 'opp-' + b + '-' + t.date.toISOString().slice(0, 10), title: PLANET_ZH[b] + '衝', at: t.date, viewAt: tr.time.date,
        dtStart: new Date(tr.time.date.getTime() - 3600000), dtEnd: new Date(tr.time.date.getTime() + 3600000),
        desc: PLANET_ZH[b] + '和太陽分別在地球兩側，整晚都在天上，是一年中最亮、最接近地球的時候。亮度 ' + fmtMag(mag) + (naked ? '。' : '，需要望遠鏡。'),
        note: '傍晚從東方升起，' + hhmm(tr.time.date) + ' 前後最高（' + dirName(tr.hor.azimuth) + '方 ' + Math.round(tr.hor.altitude) + '°）。' });
    } catch (e) { /* ignore */ }
  }
  for (const b of ['Mercury', 'Venus']) {
    try {
      let t = t0;
      for (let i = 0; i < 8; i++) {
        const e = A.SearchMaxElongation(b, t);
        if (!e || e.time.date >= end) break;
        t = e.time.AddDays(5);
        if (e.time.date < from) continue;
        const evening = e.visibility === 'evening';
        const sun = A.SearchRiseSet('Sun', obs, evening ? -1 : +1, e.time.AddDays(-0.5), 1.1);
        const v = sun ? new Date(sun.date.getTime() + (evening ? 1 : -1) * 40 * 60000) : e.time.date;
        const h = altOf(b, A.MakeTime(v));
        const mag = A.Illumination(b, e.time).mag;
        out.push({ type: 'planet', id: 'elo-' + b + '-' + e.time.date.toISOString().slice(0, 10), title: PLANET_ZH[b] + (evening ? '東大距' : '西大距'), at: e.time.date, viewAt: v,
          dtStart: new Date(v.getTime() - 20 * 60000), dtEnd: new Date(v.getTime() + 40 * 60000),
          desc: PLANET_ZH[b] + '離太陽最遠（' + e.elongation.toFixed(1) + '°），' + (evening ? '黃昏在西方天空' : '清晨在東方天空') + '最好找。亮度 ' + fmtMag(mag) + '。',
          note: (evening ? '日落後' : '日出前') + '約 40 分鐘（' + hhmm(v) + '）在' + dirName(h.azimuth) + '方，高度 ' + Math.round(h.altitude) + '°' + (h.altitude < 8 ? '，很低，需要開闊的地平線' : '') + '。' });
      }
    } catch (e) { /* ignore */ }
  }

  // ---- 月亮：滿月、新月、超級月亮
  for (const [phase, name] of [[0, '新月'], [180, '滿月']]) {
    let t = t0;
    for (let i = 0; i < 15; i++) {
      const p = A.SearchMoonPhase(phase, t, 40);
      if (!p || p.date >= end) break;
      t = p.AddDays(5);
      const v = A.GeoMoon(p), km = Math.hypot(v.x, v.y, v.z) * 149597870.7;
      const sup = phase === 180 && km < SUPERMOON_KM;
      let note;
      if (phase === 180) {
        const rise = A.SearchRiseSet('Moon', obs, +1, p.AddDays(-0.75), 1.5);
        note = (rise ? '月亮約 ' + mdhm(rise.date) + ' 從東方升起，整晚都在天上。' : '') + '滿月前後月光很亮，暗的星星和銀河不容易看到。';
      } else note = '前後幾天沒有月光干擾，最適合看銀河和暗的星雲星團。';
      out.push({ type: 'moon', id: (phase ? 'full-' : 'new-') + p.date.toISOString().slice(0, 10), title: sup ? '超級月亮（滿月）' : name, at: p.date, viewAt: p.date,
        dtStart: p.date, dtEnd: new Date(p.date.getTime() + 3600000), supermoon: sup,
        desc: (sup ? '滿月時月亮接近近地點，看起來比平常大一點、亮一點。' : phase ? '月亮和太陽分別在地球兩側，整個圓面被照亮。' : '月亮和太陽在同一方向，整晚看不到月亮。') + '月地距離約 ' + (km / 10000).toFixed(1) + ' 萬公里。',
        note });
    }
  }

  // ---- 春分、夏至、秋分、冬至
  const y0 = from.getUTCFullYear();
  for (const y of [y0, y0 + 1]) {
    const s = A.Seasons(y);
    const south = lat < 0;
    [['mar_equinox', '春分', '太陽直射赤道，白天和黑夜幾乎一樣長。'], ['jun_solstice', '夏至', south ? '南半球白天最短的一天。' : '北半球白天最長的一天。'],
     ['sep_equinox', '秋分', '太陽直射赤道，白天和黑夜幾乎一樣長。'], ['dec_solstice', '冬至', south ? '南半球白天最長的一天。' : '北半球白天最短、黑夜最長的一天。']].forEach(([k, zh, d]) => {
      const t = s[k].date;
      add({ type: 'season', id: 'sea-' + k + '-' + y, title: zh, at: t, viewAt: t, dtStart: t, dtEnd: new Date(t.getTime() + 3600000), desc: d + '這是天文上太陽到達該位置的時刻。', note: '' });
    });
  }

  out.sort((p, q) => p.at - q.at);
  return out;
}

// ---------------------------------------------------------------- iCalendar (RFC 5545)
const icsDate = (d) => d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
const icsText = (s) => String(s).replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n');
function fold(line) {
  // 每行最多 75 個位元組（UTF-8），中文字不能從中間切開
  const parts = []; let cur = '', bytes = 0;
  for (const ch of line) {
    const n = new TextEncoder().encode(ch).length;
    if (bytes + n > (parts.length ? 74 : 75)) { parts.push(cur); cur = ''; bytes = 0; }
    cur += ch; bytes += n;
  }
  parts.push(cur);
  return parts.join('\r\n ');
}
function evText(ev) { return ev.desc + (ev.note ? '\n' + ev.note : '') + '\n（頭頂星空 天象行事曆）'; }
function ics(events, loc) {
  const now = icsDate(new Date());
  const L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//s70680.github.io//頭頂星空 天象行事曆//ZH-TW', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'X-WR-CALNAME:頭頂星空 天象'];
  for (const ev of events) {
    const loctxt = loc ? loc.name + ' (' + loc.lat.toFixed(2) + ', ' + loc.lon.toFixed(2) + ')' : '';
    L.push('BEGIN:VEVENT', 'UID:' + ev.id + (loc ? '-' + loc.lat.toFixed(1) + '_' + loc.lon.toFixed(1) : '') + '@s70680.github.io', 'DTSTAMP:' + now,
      'DTSTART:' + icsDate(ev.dtStart), 'DTEND:' + icsDate(ev.dtEnd > ev.dtStart ? ev.dtEnd : new Date(ev.dtStart.getTime() + 3600000)),
      'SUMMARY:' + icsText(ev.title), 'DESCRIPTION:' + icsText(evText(ev)));
    if (loctxt) L.push('LOCATION:' + icsText(loctxt));
    L.push('BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:' + icsText(ev.title), 'TRIGGER:-PT1H', 'END:VALARM', 'END:VEVENT');
  }
  L.push('END:VCALENDAR');
  return L.map(fold).join('\r\n') + '\r\n';
}
function google(ev, loc) {
  const end = ev.dtEnd > ev.dtStart ? ev.dtEnd : new Date(ev.dtStart.getTime() + 3600000);
  return 'https://calendar.google.com/calendar/render?action=TEMPLATE&text=' + encodeURIComponent(ev.title) +
    '&dates=' + icsDate(ev.dtStart) + '/' + icsDate(end) + '&details=' + encodeURIComponent(evText(ev)) +
    (loc ? '&location=' + encodeURIComponent(loc.name) : '');
}

root.SkyEvents = { list, ics, google, SHOWERS, SUPERMOON_KM };
})(typeof window !== 'undefined' ? window : globalThis);
