#!/usr/bin/env python3
# source/ のテキストを読み取り index.html を生成する（GitHub Actions 用）
import re, os

START_YEAR = 2026  # 年度の開始年（4〜12月）。年度を切り替えるときはここを変更。

BASE = os.path.dirname(os.path.abspath(__file__))

# ── パーサー ──────────────────────────────────────────────
def parse_events(filename):
    events = {}
    path = os.path.join(BASE, 'source', filename)
    if not os.path.exists(path):
        return events
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            m = re.match(r'(\d+)月(\d+)日\s*(.+)', line)
            if m:
                month = int(m.group(1))
                day   = int(m.group(2))
                event = m.group(3).strip()
                year  = START_YEAR if month >= 4 else START_YEAR + 1
                key   = '%d-%02d-%02d' % (year, month, day)
                events[key] = event
    return events

def js_obj(d):
    lines = []
    for k in sorted(d):
        v = d[k].replace('\\', '\\\\').replace("'", "\\'")
        lines.append("  '%s': '%s'" % (k, v))
    return '{\n' + ',\n'.join(lines) + '\n}'

# ── 読み込み ─────────────────────────────────────────────
holidays = parse_events('祝日.txt')
narumi   = parse_events('なる実.txt')
yayoi    = parse_events('弥生.txt')
mitsuki  = parse_events('充希.txt')
yuko     = parse_events('由布子.txt')
zenin    = parse_events('全員.txt')

SY  = START_YEAR
EY  = START_YEAR + 1
OUT = os.path.join(BASE, 'index.html')

# ── HTML テンプレート ─────────────────────────────────────
TMPL = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__SY__年度 カレンダー</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Meiryo", sans-serif;
  font-size: 9pt;
  color: #222;
  background: #fff;
  padding: 10px;
}
.page-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  align-items: start;
  margin-bottom: 16px;
}
.month-heading {
  font-size: 10.5pt;
  font-weight: bold;
  padding: 8px 8px;
  background: transparent;
  border-left: 4px solid #444;
  margin-bottom: 2px;
  white-space: nowrap;
}
table.cal {
  width: 100%;
  border-collapse: collapse;
  font-size: 8pt;
  border: 1px solid #888;
}
table.cal thead th {
  padding: 3px 4px;
  background: #e8e8e8;
  border-bottom: 2px solid #666;
  border-right: 1px solid #888;
  text-align: center;
  font-weight: bold;
  white-space: nowrap;
}
th.th-events {
  text-align: left;
  padding-left: 5px;
}
.td-events {
  position: relative;
  padding-bottom: 11px;
}
.events-note {
  position: absolute;
  right: 4px;
  bottom: 1px;
  font-size: 6.5pt;
  color: #666;
  line-height: 1;
  white-space: nowrap;
}
table.cal tbody td {
  padding: 3px 4px;
  border-bottom: 1px solid #aaa;
  border-right: 1px solid #aaa;
  vertical-align: top;
  line-height: 1.45;
}
.td-date {
  text-align: right;
  white-space: nowrap;
  font-weight: bold;
  width: 18px;
}
.td-dow {
  text-align: center;
  white-space: nowrap;
  width: 13px;
}
tr.row-red           { background: #fff0f0; }
tr.row-red .td-date,
tr.row-red .td-dow   { color: #c0392b; font-weight: bold; }
tr.row-sat           { background: #f0f4ff; }
tr.row-sat .td-date,
tr.row-sat .td-dow   { color: #1d4ed8; font-weight: bold; }
.badge {
  display: inline-block;
  width: 10px;
  height: 10px;
  line-height: 10px;
  text-align: center;
  border-radius: 50%;
  color: #fff;
  font-size: 5pt;
  font-weight: bold;
  vertical-align: middle;
  margin-right: 1px;
}
.badge + .badge { margin-left: -1px; }
.badge-na { background: #EE6C4D; }
.badge-ya { background: #2D5D7B; }
.badge-yu { background: #0A8754; }
.badge-mi { background: #9E0059; }
.legend {
  margin: 4px 0 14px;
  font-size: 8pt;
  color: #444;
}
.legend .badge { margin-right: 3px; }
.legend span.item { margin-right: 12px; white-space: nowrap; }
.updated { font-size: 7.5pt; color: #999; margin-bottom: 10px; }
@media print {
  @page { size: A4 landscape; margin: 8mm; }
  body { padding: 0; font-size: 7.5pt; }
  .legend, .updated { display: none; }
  .page-row { gap: 6px; margin-bottom: 0; }
  .page-row:not(:last-child) { page-break-after: always; }
  table.cal { font-size: 7pt; }
  table.cal tbody td { padding: 3px 3px; }
  .month-heading { font-size: 9pt; padding: 6px 6px; }
  .events-note { font-size: 6pt; }
}
</style>
</head>
<body>
<div class="legend">
  <span class="item"><span class="badge badge-na">な</span>なる実</span>
  <span class="item"><span class="badge badge-ya">や</span>弥生</span>
  <span class="item"><span class="badge badge-yu">ゆ</span>由布子</span>
  <span class="item"><span class="badge badge-mi">み</span>充希</span>
</div>
<div class="updated" id="updated"></div>
<div id="calendar"></div>
<script>
const DOW_JP = ['日','月','火','水','木','金','土'];

function dateKey(y, m, d) {
  return y + '-' + String(m).padStart(2,'0') + '-' + String(d).padStart(2,'0');
}
function daysInMonth(year, month) {
  return new Date(year, month, 0).getDate();
}

const holidays = __HOLIDAYS__;
const narumiEvents = __NARUMI__;
const yayoiEvents = __YAYOI__;
const mitsukiEvents = __MITSUKI__;
const yukoEvents = __YUKO__;
const zeninEvents = __ZENIN__;

const MONTHS = [
  [__SY__,4],[__SY__,5],[__SY__,6],[__SY__,7],
  [__SY__,8],[__SY__,9],[__SY__,10],[__SY__,11],
  [__SY__,12],[__EY__,1],[__EY__,2],[__EY__,3]
];

function buildMonth(year, month) {
  const numDays = daysInMonth(year, month);
  const block = document.createElement('div');
  block.className = 'month-block';

  const heading = document.createElement('div');
  heading.className = 'month-heading';
  heading.textContent = year + '年' + month + '月';
  block.appendChild(heading);

  const table = document.createElement('table');
  table.className = 'cal';
  table.innerHTML = '';

  const tbody = document.createElement('tbody');

  for (let d = 1; d <= numDays; d++) {
    const key     = dateKey(year, month, d);
    const dow     = new Date(year, month - 1, d).getDay();
    const holiday = holidays[key]      || '';
    const narumi  = narumiEvents[key]  || '';
    const yayoi   = yayoiEvents[key]   || '';
    const mitsuki = mitsukiEvents[key] || '';
    const yuko    = yukoEvents[key]    || '';
    const zenin   = zeninEvents[key]   || '';

    const tr = document.createElement('tr');
    if (holiday || dow === 0) tr.className = 'row-red';
    else if (dow === 6)       tr.className = 'row-sat';

    const tdDate = document.createElement('td');
    tdDate.className = 'td-date';
    tdDate.textContent = d;

    const tdDow = document.createElement('td');
    tdDow.className = 'td-dow';
    tdDow.textContent = DOW_JP[dow];

    const tdEvents = document.createElement('td');
    tdEvents.className = 'td-events';
    const items = [];
    const notes = [];
    function pushEvent(badges, raw) {
      if (!raw) return;
      const bracketRe = /\[([^\]]+)\]/g;
      let m;
      while ((m = bracketRe.exec(raw)) !== null) notes.push(m[1]);
      const stripped = raw.replace(/\[([^\]]+)\]/g, '').trim();
      if (stripped) items.push({ badges, text: stripped });
    }
    pushEvent([], zenin);
    pushEvent([['na','な']], narumi);
    pushEvent([['ya','や']], yayoi);
    if (yuko && mitsuki && yuko === mitsuki) {
      pushEvent([['yu','ゆ'],['mi','み']], yuko);
    } else {
      pushEvent([['yu','ゆ']], yuko);
      pushEvent([['mi','み']], mitsuki);
    }
    items.forEach((item, idx) => {
      if (idx > 0) tdEvents.appendChild(document.createTextNode(' / '));
      item.badges.forEach(([cls, label]) => {
        const span = document.createElement('span');
        span.className = 'badge badge-' + cls;
        span.textContent = label;
        tdEvents.appendChild(span);
      });
      if (item.badges.length) tdEvents.appendChild(document.createTextNode(' '));
      tdEvents.appendChild(document.createTextNode(item.text));
    });
    if (notes.length) {
      const note = document.createElement('span');
      note.className = 'events-note';
      note.textContent = notes.map(n => '(' + n + ')').join(' ');
      tdEvents.appendChild(note);
    }

    tr.appendChild(tdDate);
    tr.appendChild(tdDow);
    tr.appendChild(tdEvents);
    tbody.appendChild(tr);
  }

  table.appendChild(tbody);
  block.appendChild(table);
  return block;
}

const calDiv = document.getElementById('calendar');
for (let i = 0; i < MONTHS.length; i += 3) {
  const row = document.createElement('div');
  row.className = 'page-row';
  MONTHS.slice(i, i + 3).forEach(([y, m]) => row.appendChild(buildMonth(y, m)));
  calDiv.appendChild(row);
}

document.getElementById('updated').textContent = '最終更新: __BUILT__';
</script>
</body>
</html>"""

# ── プレースホルダー置換 ──────────────────────────────────
import datetime, time
built = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime('%Y-%m-%d %H:%M') + ' (JST)'

html = (TMPL
    .replace('__HOLIDAYS__', js_obj(holidays))
    .replace('__NARUMI__',   js_obj(narumi))
    .replace('__YAYOI__',    js_obj(yayoi))
    .replace('__MITSUKI__',  js_obj(mitsuki))
    .replace('__YUKO__',     js_obj(yuko))
    .replace('__ZENIN__',    js_obj(zenin))
    .replace('__SY__',       str(SY))
    .replace('__EY__',       str(EY))
    .replace('__BUILT__',    built)
)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)

print('Generated:', OUT)
