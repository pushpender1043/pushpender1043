#!/usr/bin/env python3
"""LeetCode profile card: solved ring, difficulty bars, streaks and a 52-week heatmap.

Run by GitHub Actions (see .github/workflows/leetcode.yml). Writes assets/leetcode.svg.
Fonts are embedded from scripts/fonts.css so the card looks identical everywhere.
"""
import datetime as dt
import html
import json
import os
import sys
import urllib.request

USER = os.environ.get("LEETCODE_USER", "pushpender_1043")
OUT = os.environ.get("OUT", "assets/leetcode.svg")
HERE = os.path.dirname(os.path.abspath(__file__))
ICON = "M13.483 0a1.374 1.374 0 0 0-.961.438L7.116 6.226l-3.854 4.126a5.266 5.266 0 0 0-1.209 2.104 5.35 5.35 0 0 0-.125.513 5.527 5.527 0 0 0 .062 2.362 5.83 5.83 0 0 0 .349 1.017 5.938 5.938 0 0 0 1.271 1.818l4.277 4.193.039.038c2.248 2.165 5.852 2.133 8.063-.074l2.396-2.392c.54-.54.54-1.414.003-1.955a1.378 1.378 0 0 0-1.951-.003l-2.396 2.392a3.021 3.021 0 0 1-4.205.038l-.02-.019-4.276-4.193c-.652-.64-.972-1.469-.948-2.263a2.68 2.68 0 0 1 .066-.523 2.545 2.545 0 0 1 .619-1.164L9.13 8.114c1.058-1.134 3.204-1.27 4.43-.278l3.501 2.831c.593.48 1.461.387 1.94-.207a1.384 1.384 0 0 0-.207-1.943l-3.5-2.831c-.8-.647-1.766-1.045-2.774-1.202l2.015-2.158A1.384 1.384 0 0 0 13.483 0zm-2.866 12.815a1.38 1.38 0 0 0-1.38 1.382 1.38 1.38 0 0 0 1.38 1.382H20.79a1.38 1.38 0 0 0 1.38-1.382 1.38 1.38 0 0 0-1.38-1.382z"
BASE_CSS = r"""
.sg{font-family:'Space Grotesk',system-ui,'Segoe UI',sans-serif}
.jb{font-family:'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace}
.pf{font-family:'Playfair Display',Georgia,serif;font-style:italic}
.cv{font-family:'Caveat','Segoe Script',cursive}
.w4{font-weight:400}.w5{font-weight:500}.w6{font-weight:600}.w7{font-weight:700}
.fg{fill:#E6EDF3}.so{fill:#B6C0CC}.mu{fill:#8B949E}.mint{fill:#7EE7C7}.peri{fill:#8B9DFF}.amber{fill:#FFC857}.coral{fill:#FF6B81}
.ln{stroke:#30363D}.track{fill:#8B949E;fill-opacity:.2}
.ic{fill:#9FB0C3}.lu{fill:none;stroke:#9FB0C3;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.s1{stop-color:#F0F6FC}.s2{stop-color:#7EE7C7}.s3{stop-color:#8B9DFF}
.card{fill:#0F141B;stroke:#30363D}
.e0{fill:#21262D}.l1{fill:#123D34}.l2{fill:#1D6B57}.l3{fill:#35B08C}.l4{fill:#7EE7C7}
.pill{fill:none;stroke:#30363D}
.fu{animation:fu .8s cubic-bezier(.2,.7,.2,1) both}
@keyframes fu{from{opacity:0;transform:translateY(8px)}}
@media (prefers-color-scheme: light){
.fg{fill:#1F2328}.so{fill:#3D4650}.mu{fill:#57606A}.mint{fill:#0F8F73}.peri{fill:#4F5BD5}.amber{fill:#B7791F}.coral{fill:#D6336C}
.ln{stroke:#D0D7DE}.ic{fill:#57606A}.lu{stroke:#57606A}
.s1{stop-color:#1F2328}.s2{stop-color:#0F8F73}.s3{stop-color:#4F5BD5}
.card{fill:#F6F8FA;stroke:#D0D7DE}
.e0{fill:#EBEDF0}.l1{fill:#B7ECDC}.l2{fill:#7DD4B9}.l3{fill:#3FB08C}.l4{fill:#0F8F73}
.pill{stroke:#D0D7DE}
}
"""

STATS_Q = """
query stats($u: String!) {
  allQuestionsCount { difficulty count }
  matchedUser(username: $u) {
    profile { ranking }
    submitStats: submitStatsGlobal { acSubmissionNum { difficulty count } }
  }
  userContestRanking(username: $u) { rating attendedContestsCount }
}
"""
CAL_Q = """
query cal($u: String!, $y: Int) {
  matchedUser(username: $u) {
    userCalendar(year: $y) { activeYears submissionCalendar }
  }
}
"""


def gql(query, variables):
    req = urllib.request.Request(
        "https://leetcode.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Content-Type": "application/json", "Referer": "https://leetcode.com",
                 "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("errors") or not data.get("data"):
        raise RuntimeError(f"LeetCode API error: {data.get('errors')}")
    return data["data"]


def fetch_stats():
    d = gql(STATS_Q, {"u": USER})
    if not d.get("matchedUser"):
        raise RuntimeError("LeetCode user not found")
    return {
        "solved": {x["difficulty"]: x["count"] for x in d["matchedUser"]["submitStats"]["acSubmissionNum"]},
        "total": {x["difficulty"]: x["count"] for x in d["allQuestionsCount"]},
        "rank": d["matchedUser"]["profile"]["ranking"],
    }


def fetch_days():
    """{day_number: submissions} over every active year, or None if the calendar is unavailable."""
    try:
        now = dt.datetime.now(dt.timezone.utc)
        first = gql(CAL_Q, {"u": USER, "y": now.year})["matchedUser"]["userCalendar"]
        years = set(first.get("activeYears") or []) | {now.year}
        days = {}
        for y in sorted(years):
            cal = first if y == now.year else gql(CAL_Q, {"u": USER, "y": y})["matchedUser"]["userCalendar"]
            for ts, n in json.loads(cal["submissionCalendar"] or "{}").items():
                d = int(ts) // 86400
                days[d] = days.get(d, 0) + int(n)
        return days
    except Exception as e:  # the card still renders, just without streaks and heatmap
        print("WARNING: calendar unavailable:", e, file=sys.stderr)
        return None


def streaks(days, today):
    active = {d for d, n in days.items() if n > 0}
    cur, d = 0, (today if today in active else today - 1)
    while d in active:
        cur += 1
        d -= 1
    best = run = 0
    prev = None
    for d in sorted(active):
        run = run + 1 if prev is not None and d == prev + 1 else 1
        best, prev = max(best, run), d
    return cur, best, len(active)


def level(n):
    return 0 if n <= 0 else 1 if n == 1 else 2 if n <= 3 else 3 if n <= 6 else 4


def render(st, days):
    W, PAD = 900, 30
    solved, total = st["solved"], st["total"]
    all_s, all_t = solved.get("All", 0), max(total.get("All", 1), 1)
    pct = max(1.2, 100 * all_s / all_t)
    has_cal = days is not None
    top_h = 276
    H = 466 if has_cal else top_h + 22

    # ---- header
    body = (f'<rect class="card" x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18"/>'
            f'<g transform="translate({PAD},24) scale(1.3)"><path fill="#FFA116" d="{ICON}"/></g>'
            f'<text x="{PAD + 44}" y="48" class="sg w7 fg" font-size="23" letter-spacing="-.3">{html.escape(USER)}</text>'
            f'<text x="{W - PAD}" y="34" class="jb w4 mu" font-size="10" letter-spacing="2.4" text-anchor="end">GLOBAL RANK</text>'
            f'<text x="{W - PAD}" y="58" class="sg w6 fg" font-size="22" text-anchor="end">#{st["rank"]:,}</text>'
            f'<line x1="{PAD}" y1="82" x2="{W - PAD}" y2="82" class="ln" stroke-opacity=".8"/>')

    # ---- ring
    cx, cy, r = 118, 184, 62
    circ = 2 * 3.14159265 * r
    arc = circ * pct / 100
    body += (f'<defs><linearGradient id="rg" x1="0" x2="1" y1="0" y2="1"><stop offset="0" class="s2"/><stop offset="1" class="s3"/></linearGradient></defs>'
             f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke-width="11" stroke="#8B949E" stroke-opacity=".2"/>'
             f'<circle class="ring" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#rg)" stroke-width="11" '
             f'stroke-linecap="round" stroke-dasharray="{arc:.1f} {circ:.1f}" transform="rotate(-90 {cx} {cy})"/>'
             f'<text x="{cx}" y="{cy + 8}" class="sg w7 fg" font-size="38" text-anchor="middle" letter-spacing="-1">{all_s}</text>'
             f'<text x="{cx}" y="{cy + 28}" class="jb w4 mu" font-size="9.5" letter-spacing="2.4" text-anchor="middle">SOLVED</text>')

    # ---- difficulty bars
    bx, bw = 250, 330
    for i, (name, cls) in enumerate([("Easy", "mint"), ("Medium", "amber"), ("Hard", "coral")]):
        y = 128 + i * 52
        s, t = solved.get(name, 0), max(total.get(name, 1), 1)
        w = max(7, bw * s / t)
        body += (f'<text x="{bx}" y="{y}" class="sg w5 fg" font-size="15">{name}</text>'
                 f'<text x="{bx + bw}" y="{y}" class="jb w4 mu" font-size="12" text-anchor="end">/ {t}</text>'
                 f'<text x="{bx + bw - 7.2 * (len(str(t)) + 3):.1f}" y="{y}" class="jb w5 fg" font-size="12" text-anchor="end">{s}</text>'
                 f'<rect class="track" x="{bx}" y="{y + 12}" width="{bw}" height="8" rx="4"/>'
                 f'<rect class="bar {cls}" x="{bx}" y="{y + 12}" width="{w:.1f}" height="8" rx="4" style="animation-delay:{i * .15:.2f}s"/>')

    # ---- streak panel + heatmap
    if has_cal:
        now = dt.datetime.now(dt.timezone.utc)
        today_n = int(now.timestamp()) // 86400
        today = dt.date.fromtimestamp(today_n * 86400)
        cur, best, active_total = streaks(days, today_n)
        px = 640
        for i, (lab, num, unit, cls) in enumerate([("CURRENT STREAK", cur, "days", "mint"),
                                                   ("LONGEST STREAK", best, "days", "peri"),
                                                   ("ACTIVE DAYS", active_total, "", "fg")]):
            y = 112 + i * 56
            body += (f'<text x="{px}" y="{y}" class="jb w4 mu" font-size="10" letter-spacing="2.4">{lab}</text>'
                     f'<text x="{px}" y="{y + 30}" class="sg w7 {cls}" font-size="32" letter-spacing="-.5">{num}'
                     f'<tspan class="sg w4 mu" font-size="13" font-weight="400" letter-spacing="0"> {unit}</tspan></text>')
        for x in (222, 614):
            body += f'<line x1="{x}" y1="104" x2="{x}" y2="262" class="ln" stroke-opacity=".6"/>'

        body += f'<line x1="{PAD}" y1="{top_h}" x2="{W - PAD}" y2="{top_h}" class="ln" stroke-opacity=".8"/>'
        inner, gap = W - 2 * PAD, 3
        step = (inner + gap) / 53
        cell = step - gap
        gx, gy = PAD, top_h + 38
        dow = (today.weekday() + 1) % 7
        start = today - dt.timedelta(days=dow + 52 * 7)
        cells, months, last_m, year_subs = [], [], None, 0
        for col in range(53):
            for row in range(7):
                d = start + dt.timedelta(days=col * 7 + row)
                if d > today:
                    continue
                n = days.get((d - dt.date(1970, 1, 1)).days, 0)
                year_subs += n
                cells.append(f'<rect class="c e{level(n)}" x="{gx + col * step:.1f}" y="{gy + row * step:.1f}" '
                             f'width="{cell:.1f}" height="{cell:.1f}" rx="3" style="animation-delay:{col * .014:.3f}s"/>'
                             if level(n) == 0 else
                             f'<rect class="c l{level(n)}" x="{gx + col * step:.1f}" y="{gy + row * step:.1f}" '
                             f'width="{cell:.1f}" height="{cell:.1f}" rx="3" style="animation-delay:{col * .014:.3f}s"/>')
            m = (start + dt.timedelta(days=col * 7)).month
            if m != last_m:
                months.append(f'<text x="{gx + col * step:.1f}" y="{gy - 10}" class="jb w4 mu" font-size="10">{dt.date(2000, m, 1):%b}</text>')
                last_m = m
        body += "".join(months) + "".join(cells)
        fy = gy + 7 * step + 22
        body += f'<text x="{PAD}" y="{fy:.1f}" class="jb w4 mu" font-size="11"><tspan class="fg" font-weight="500">{year_subs:,}</tspan> submissions in the last year</text>'
        lx = W - PAD - (28 + 5 * 17 + 34)
        body += f'<text x="{lx}" y="{fy:.1f}" class="jb w4 mu" font-size="10">less</text>'
        for i in range(5):
            body += f'<rect class="{"e0" if i == 0 else "l" + str(i)}" x="{lx + 28 + i * 17}" y="{fy - 10:.1f}" width="12" height="12" rx="3"/>'
        body += f'<text x="{lx + 28 + 5 * 17 + 4}" y="{fy:.1f}" class="jb w4 mu" font-size="10">more</text>'

    css = (".bar{transform-box:fill-box;transform-origin:left;animation:grow 1.2s cubic-bezier(.2,.7,.2,1) both}"
           "@keyframes grow{from{transform:scaleX(0)}}"
           f".ring{{animation:ring 1.6s cubic-bezier(.2,.7,.2,1) both}}@keyframes ring{{from{{stroke-dasharray:0 {circ:.1f}}}}}"
           ".c{animation:cf .5s ease both}@keyframes cf{from{opacity:0}}")
    fonts = ""
    fp = os.path.join(HERE, "fonts.css")
    if os.path.exists(fp):
        fonts = open(fp, encoding="utf-8").read()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f"<style>{fonts}{BASE_CSS}{css}</style>{body}</svg>")


def main():
    try:
        stats = fetch_stats()
    except Exception as e:  # keep the previous SVG and make the run visibly fail
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)
    days = fetch_days()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(stats, days))
    print("wrote", OUT, "(heatmap)" if days is not None else "(no heatmap)")


if __name__ == "__main__":
    main()
