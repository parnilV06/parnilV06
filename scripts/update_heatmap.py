#!/usr/bin/env python3
"""Render the real GitHub contribution calendar as a monochrome terminal heatmap."""
from __future__ import annotations
import html, re, sys
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "parnilv06"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "assets/heatmap.svg")

URL = f"https://github.com/users/{USERNAME}/contributions"
req = Request(URL, headers={"User-Agent": "Mozilla/5.0 (GitHub Profile Heatmap)"})
with urlopen(req, timeout=30) as r:
    raw = r.read().decode("utf-8", "ignore")

# GitHub's contribution calendar provides exact date, level and accessible count text per cell.
cells = []
for tag in re.findall(r"<[^>]*data-date=[^>]*>", raw):
    dm = re.search(r'data-date=["\']([^"\']+)', tag)
    if not dm:
        continue
    try:
        d = date.fromisoformat(dm.group(1))
    except ValueError:
        continue
    lm = re.search(r'data-level=["\'](\d+)', tag)
    am = re.search(r'aria-label=["\']([^"\']+)', tag)
    count = 0
    if am:
        m = re.search(r'([\d,]+)\s+contribution', html.unescape(am.group(1)), re.I)
        if m:
            count = int(m.group(1).replace(",", ""))
    level = int(lm.group(1)) if lm else 0
    cells.append((d, count, level))

if not cells:
    raise SystemExit("Could not find GitHub contribution cells; GitHub markup may have changed.")

by_date = {d: (count, level) for d, count, level in cells}
latest = max(by_date)
first = latest - timedelta(days=((latest.weekday()+1) % 7) + 52*7)
weeks = []
for c in range(53):
    week=[]
    start = first + timedelta(days=c*7)
    for row in range(7):
        d = start + timedelta(days=row)
        week.append((d, *by_date.get(d, (0,0))))
    weeks.append(week)

BG, PANEL, TERM, BAR = "#07090d", "#0a0d12", "#080b10", "#11151c"
BORDER, TEXT, MUTED, DIM = "#27303a", "#e8ebef", "#77818d", "#4e5864"
ACCENT, ACCENT2 = "#4da3ff", "#8ac7ff"
palette = {0:"#141920",1:"#183149",2:"#245b86",3:"#3887c2",4:"#5ba9eb"}
x0, y0, cell, gap = 28, 98, 15, 5
parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="550" viewBox="0 0 1200 550" role="img">']
parts.append(f'<rect x="2" y="2" width="1196" height="546" rx="18" fill="{BG}" stroke="{BORDER}" stroke-width="2"/>')
parts.append(f'<text x="42" y="40" fill="{ACCENT}" font-family="ui-monospace,monospace" font-size="18" font-weight="700">HEATMAP</text>')
parts.append(f'<g transform="translate(40,70)"><rect width="1120" height="430" rx="12" fill="{TERM}" stroke="{BORDER}"/><rect width="1120" height="44" rx="12" fill="{BAR}"/><rect y="43" width="1120" height="1" fill="{BORDER}"/>')
parts.append('<circle cx="24" cy="22" r="6" fill="#6c737c"/><circle cx="46" cy="22" r="6" fill="#8b929b"/><circle cx="68" cy="22" r="6" fill="#b7bec7"/>')
parts.append(f'<text x="560" y="27" text-anchor="middle" fill="{MUTED}" font-family="ui-monospace,monospace" font-size="12">parnilv06@github:~$ ./contributions.sh</text>')
seen=set()
for c,week in enumerate(weeks):
    for d,_,_ in week:
        if d.day <= 7 and (d.year,d.month) not in seen:
            seen.add((d.year,d.month))
            parts.append(f'<text x="{x0+c*(cell+gap)}" y="88" fill="{MUTED}" font-family="ui-monospace,monospace" font-size="10">{d.strftime("%b")}</text>')
            break
for c,week in enumerate(weeks):
    for row,(d,count,level) in enumerate(week):
        x=x0+c*(cell+gap); y=y0+row*(cell+gap)
        title=html.escape(f"{d.isoformat()} — {count} contribution" + ("s" if count != 1 else ""))
        parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{palette.get(level,palette[4])}"><title>{title}</title></rect>')
total=sum(v[0] for v in by_date.values()); active=sum(1 for v in by_date.values() if v[0] > 0)
parts.append(f'<text x="28" y="244" fill="{TEXT}" font-family="ui-monospace,monospace" font-size="12">{total:,} contributions • {active:,} active days • last 12 months</text>')
parts.append(f'<text x="28" y="270" fill="{DIM}" font-family="ui-monospace,monospace" font-size="11">source = github.com/users/{USERNAME}/contributions</text>')
parts.append('</g></svg>')
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(''.join(parts), encoding='utf-8')
print(f"Generated {OUT}: {total} contributions across {len(by_date)} daily cells")
