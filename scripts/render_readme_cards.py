#!/usr/bin/env python3
"""Render the animated SVG profile cards for github.com/misbahulhaq09.

Data-driven: reads data/profile.json + data/contributions.json and writes
10 SVGs into cards/. Stdlib only.

Animation rules (GitHub renders these inside <img>, so no JS and no external
assets): inline <style> CSS keyframes + SMIL only. Every animated element's
BASE state is its final state — CSS keyframes animate *from* an offset, so
static renderers (and reduced-motion users) still see the finished design.

Env:
  STATIC=1     render with animations disabled (final state) for screenshots.
  CARDS_OUT=dir  write SVGs to dir instead of cards/ (used for previews).
"""
import json
import os
from collections import OrderedDict
from datetime import date
from xml.sax.saxutils import escape as xesc

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
STATIC = os.environ.get("STATIC") == "1"
OUTDIR = os.environ.get("CARDS_OUT", os.path.join(ROOT, "cards"))

# ---- brand ---------------------------------------------------------------
BG = "#101012"
PANEL = "#17171A"
INK = "#F5F0E6"
GOLD = "#C9A227"
GOLD_HI = "#F2CE4B"
MUTED = "#9A958A"
HAIR = "#2A2A2E"
SERIF = "Georgia, 'Times New Roman', serif"
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, Menlo, Consolas, monospace"
LEVEL_FILL = ["#232329", "#57460F", "#8A6D1B", "#C9A227", "#F2CE4B"]
LANG_COLOR = {"TypeScript": "#3178C6", "JavaScript": "#F1E05A"}

REDUCED = ("@media (prefers-reduced-motion: reduce)"
           "{*{animation:none!important;transition:none!important}}")
# NOTE: only animations are disabled — a blanket `transform:none` would also
# wipe legitimate transform *attributes* (e.g. the tile arrow's position).
# Base state == final state by design, so animation:none is sufficient.
STATIC_CSS = "*{animation:none!important}"


def style(css: str) -> str:
    css += REDUCED
    if STATIC:
        css += STATIC_CSS
    return f"<style>{css}</style>"


def svg_open(w, h, title, css):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{xesc(title)}">'
            f"<title>{xesc(title)}</title>{style(css)}")


def bg_rect(w, h):
    return (f'<rect width="{w}" height="{h}" rx="16" fill="{BG}"/>'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="15.5" '
            f'fill="none" stroke="{HAIR}"/>')


# ---- stats -----------------------------------------------------------------
def compute_stats(days):
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    streak = best_streak = 0
    for d in days:
        streak = streak + 1 if d["count"] > 0 else 0
        best_streak = max(best_streak, streak)
    busiest = max(days, key=lambda d: d["count"])
    months = OrderedDict()
    for d in days:
        key = d["date"][:7]
        months[key] = months.get(key, 0) + d["count"]
    best_month_key = max(months, key=lambda k: months[k])
    return {
        "total": total,
        "activeDays": active,
        "longestStreak": best_streak,
        "busiestDay": busiest["date"],
        "busiestCount": busiest["count"],
        "months": months,
        "bestMonthKey": best_month_key,
        "bestMonthCount": months[best_month_key],
    }


def month_label(key):  # "2026-09" -> ("Sep", "Sep 2026")
    y, m = int(key[:4]), int(key[5:7])
    short = date(y, m, 1).strftime("%b")
    return short, f"{short} {y}"


# ---- hero ------------------------------------------------------------------
def hero(p, stats):
    css = """
.rise{animation:riseIn .85s cubic-bezier(.2,.7,.25,1) both}
@keyframes riseIn{from{opacity:0;transform:translateY(28px)}}
.growX{animation:growX 1s .45s cubic-bezier(.2,.7,.25,1) both;transform-box:fill-box;transform-origin:0 50%}
@keyframes growX{from{transform:scaleX(0)}}
.pulseDot{animation:pulseDot 2.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes pulseDot{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.55);opacity:.55}}
.ringPulse{animation:ringPulse 3.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes ringPulse{0%,100%{transform:scale(1);opacity:.55}50%{transform:scale(1.1);opacity:.25}}
"""
    name = xesc(p["name"])
    shine = "" if STATIC else (
        '<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{INK}"/><stop offset=".40" stop-color="{INK}"/>'
        f'<stop offset=".50" stop-color="{GOLD_HI}"/><stop offset=".60" stop-color="{INK}"/>'
        f'<stop offset="1" stop-color="{INK}"/>'
        '<animateTransform attributeName="gradientTransform" type="translate" '
        'values="-1.6 0;-1.6 0;2.6 0;2.6 0" keyTimes="0;.45;.75;1" dur="6s" '
        'begin="1.1s" repeatCount="indefinite"/></linearGradient>')
    shine_fill = ' fill="url(#shine)"' if not STATIC else ""
    s = [svg_open(880, 300, f"{p['name']} — {p['tagline']}", css),
         f"<defs>{shine}</defs>" if shine else "",
         bg_rect(880, 300),
         # decorative corner rings
         f'<circle class="ringPulse" cx="792" cy="66" r="34" fill="none" stroke="{GOLD}" stroke-width="1.5"/>',
         f'<circle cx="792" cy="66" r="25" fill="none" stroke="{HAIR}" stroke-width="1.5"/>',
         f'<circle cx="792" cy="66" r="4" fill="{GOLD}"/>',
         # eyebrow
         f'<text class="rise" style="animation-delay:.05s" x="56" y="80" font-family="{MONO}" '
         f'font-size="13" letter-spacing="3.5" fill="{GOLD}">{xesc(p["eyebrow"])}</text>',
         # name (base ink + SMIL shine sweep copy on top)
         f'<text class="rise" style="animation-delay:.18s" x="54" y="152" font-family="{SERIF}" '
         f'font-size="63" font-weight="bold" fill="{INK}">{name}</text>',
         f'<text class="rise" style="animation-delay:.18s" x="54" y="152" font-family="{SERIF}" '
         f'font-size="63" font-weight="bold"{shine_fill}>{name}</text>' if not STATIC else "",
         f'<rect class="growX" x="56" y="176" width="128" height="3" fill="{GOLD}"/>',
         # tagline
         f'<text class="rise" style="animation-delay:.34s" x="56" y="216" font-family="{SANS}" '
         f'font-size="21" fill="{INK}" opacity=".94">{xesc(p["tagline"])}</text>',
         # location row
         f'<circle class="pulseDot" cx="62" cy="250" r="5" fill="{GOLD}"/>',
         f'<text class="rise" style="animation-delay:.48s" x="78" y="256" font-family="{SANS}" '
         f'font-size="15" fill="{MUTED}">{xesc(p["location"])}</text>',
         f'<text class="rise" style="animation-delay:.55s" x="824" y="256" text-anchor="end" '
         f'font-family="{MONO}" font-size="11.5" letter-spacing="1.5" fill="{MUTED}">'
         f'GITHUB MEMBER SINCE {xesc(p["memberSince"].upper())}</text>',
         "</svg>"]
    return "".join(s)


# ---- heatmap ----------------------------------------------------------------
def heatmap(days, stats):
    css = """
.cell{animation:cellPop .45s cubic-bezier(.2,.7,.25,1) both;transform-box:fill-box;transform-origin:center}
@keyframes cellPop{from{opacity:0;transform:scale(.3)}}
.fadeIn{animation:fadeIn .8s ease both}
@keyframes fadeIn{from{opacity:0}}
"""
    x0, y0, pitch, cell = 48, 58, 14.4, 11
    first = date.fromisoformat(days[0]["date"])  # a Sunday
    parts = [svg_open(880, 190, "Contribution heatmap — last year", css), bg_rect(880, 190),
             f'<text class="fadeIn" style="animation-delay:.5s" x="48" y="32" font-family="{MONO}" '
             f'font-size="12" letter-spacing="2.5" fill="{GOLD}">CONTRIBUTIONS — LAST 12 MONTHS</text>',
             f'<text class="fadeIn" style="animation-delay:.55s" x="832" y="32" text-anchor="end" '
             f'font-family="{SANS}" font-size="12.5" fill="{MUTED}">'
             f'{stats["total"]} contributions in the last year</text>']
    # weekday labels (Mon / Wed / Fri rows)
    for row, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(f'<text x="40" y="{y0 + row*pitch + cell - 2}" text-anchor="end" '
                     f'font-family="{SANS}" font-size="8.5" fill="{MUTED}">{lab}</text>')
    prev_month = None
    for i, d in enumerate(days):
        dt = date.fromisoformat(d["date"])
        col, row = divmod((dt - first).days, 7)  # start is Sunday -> row = weekday
        x, y = x0 + col * pitch, y0 + row * pitch
        if row == 0 and dt.month != prev_month:
            prev_month = dt.month
            parts.append(f'<text x="{x}" y="48" font-family="{SANS}" font-size="10" '
                         f'fill="{MUTED}">{dt.strftime("%b")}</text>')
        delay = 0.55 + col * 0.016
        parts.append(f'<rect class="cell" style="animation-delay:{delay:.2f}s" x="{x:.1f}" '
                     f'y="{y:.1f}" width="{cell}" height="{cell}" rx="2.5" '
                     f'fill="{LEVEL_FILL[d["level"]]}"><title>{d["date"]}: {d["count"]}</title></rect>')
    # legend
    lx = 690
    parts.append(f'<text x="{lx}" y="179" font-family="{SANS}" font-size="10.5" fill="{MUTED}">Less</text>')
    for i, fill in enumerate(LEVEL_FILL):
        parts.append(f'<rect x="{lx + 30 + i*15}" y="169" width="10.5" height="10.5" rx="2.5" fill="{fill}"/>')
    parts.append(f'<text x="{lx + 30 + 5*15 + 4}" y="179" font-family="{SANS}" font-size="10.5" fill="{MUTED}">More</text>')
    parts.append("</svg>")
    return "".join(parts)


# ---- activity ----------------------------------------------------------------
def activity(stats):
    css = """
.bar{animation:barGrow .8s cubic-bezier(.2,.7,.25,1) both;transform-box:fill-box;transform-origin:50% 100%}
@keyframes barGrow{from{transform:scaleY(0)}}
.fadeIn{animation:fadeIn .8s ease both}
@keyframes fadeIn{from{opacity:0}}
.popLate{animation:popLate .5s cubic-bezier(.2,.9,.3,1.4) both;transform-box:fill-box;transform-origin:center}
@keyframes popLate{from{opacity:0;transform:scale(.4)}}
"""
    months = list(stats["months"].items())[-12:]  # last 12 calendar months
    maxv = max(v for _, v in months)
    base_y, top_y = 216, 64
    plot_h = base_y - top_y
    x_start, slot, bar_w = 70, 63.3, 34
    _, best_full = month_label(stats["bestMonthKey"])
    first_lab, _ = month_label(months[0][0])
    last_lab, last_full = month_label(months[-1][0])
    parts = [svg_open(880, 300, "Monthly activity — last 12 months", css), bg_rect(880, 300),
             f'<text x="48" y="38" font-family="{MONO}" font-size="12" letter-spacing="2.5" '
             f'fill="{GOLD}">ACTIVITY — LAST 12 MONTHS</text>',
             f'<text x="832" y="38" text-anchor="end" font-family="{MONO}" font-size="11" '
             f'letter-spacing="1.5" fill="{MUTED}">{first_lab.upper()} {months[0][0][:4]} — '
             f'{last_lab.upper()} {months[-1][0][:4]}</text>']
    for i, (key, v) in enumerate(months):
        cx = x_start + i * slot + slot / 2
        x = cx - bar_w / 2
        h = max(3, v / maxv * plot_h) if maxv else 3
        is_best = key == stats["bestMonthKey"]
        fill = GOLD if is_best else ("#7A641F" if v > 0 else "#2E2E33")
        delay = 1.0 + i * 0.05
        parts.append(f'<rect class="bar" style="animation-delay:{delay:.2f}s" x="{x:.1f}" '
                     f'y="{base_y - h:.1f}" width="{bar_w}" height="{h:.1f}" rx="4" fill="{fill}"/>')
        if v > 0:
            if is_best:
                parts.append(f'<text class="popLate" style="animation-delay:1.85s" x="{cx:.1f}" '
                             f'y="{base_y - h - 10:.1f}" text-anchor="middle" font-family="{SANS}" '
                             f'font-size="15" font-weight="bold" fill="{GOLD_HI}">{v}</text>')
            else:
                parts.append(f'<text class="fadeIn" style="animation-delay:{delay + .5:.2f}s" '
                             f'x="{cx:.1f}" y="{base_y - h - 8:.1f}" text-anchor="middle" '
                             f'font-family="{SANS}" font-size="12" fill="{MUTED}">{v}</text>')
        short, _ = month_label(key)
        parts.append(f'<text x="{cx:.1f}" y="237" text-anchor="middle" font-family="{SANS}" '
                     f'font-size="10.5" fill="{GOLD if is_best else MUTED}"'
                     f'{" font-weight=\"bold\"" if is_best else ""}>{short}</text>')
    parts.append(f'<rect x="48" y="{base_y}" width="784" height="1" fill="{HAIR}"/>')
    parts.append(f'<rect x="48" y="254" width="784" height="1" fill="{HAIR}"/>')
    bd = date.fromisoformat(stats["busiestDay"])
    busiest_lab = f"{bd.day} {bd.strftime('%b %Y')}"
    stat_items = [
        (48, str(stats["total"]), "TOTAL"),
        (205, str(stats["activeDays"]), "ACTIVE DAYS"),
        (385, str(stats["longestStreak"]), "DAYS — LONGEST STREAK"),
        (640, str(stats["busiestCount"]), f"BUSIEST DAY · {busiest_lab.upper()}"),
    ]
    for x, val, lab in stat_items:
        parts.append(
            f'<text class="fadeIn" style="animation-delay:1.7s" x="{x}" y="285" font-family="{SANS}">'
            f'<tspan font-size="18" font-weight="bold" fill="{INK}">{val}</tspan>'
            f'<tspan font-size="10.5" letter-spacing="1" fill="{MUTED}">  {lab}</tspan></text>')
    parts.append("</svg>")
    return "".join(parts)


# ---- tiles --------------------------------------------------------------------
def count_up_texts(x, y, target, base_delay):
    """SMIL <set> count-up: one text element per value, like the blog.
    Base state of every frame is hidden except through its <set> window;
    the final value freezes on. (STATIC renders emit only the final value.)"""
    if STATIC or target <= 0:
        return (f'<text x="{x}" y="{y}" font-family="{SERIF}" font-size="58" '
                f'font-weight="bold" fill="{INK}">{target}</text>')
    step = max(0.03, min(0.07, 1.1 / target))
    out = []
    for v in range(target + 1):
        t = base_delay + v * step
        if v < target:
            anim = f'<set attributeName="opacity" to="1" begin="{t:.2f}s" dur="{step:.3f}s"/>'
            op = "0"
        else:
            anim = f'<set attributeName="opacity" to="1" begin="{t:.2f}s" dur="0.1s" fill="freeze"/>'
            op = "0"
        out.append(f'<text x="{x}" y="{y}" font-family="{SERIF}" font-size="58" '
                   f'font-weight="bold" fill="{INK}" opacity="{op}">{v}{anim}</text>')
    return "".join(out)


TILE_LINES = {
    "build": ["Websites &", "Web Apps"],
    "automate": ["AI Automation &", "Lead Systems"],
    "grow": ["Content, Ads &", "Brand Growth"],
}


def tile(tile_def, value, idx):
    css = """
.swing{animation:swingIn .7s cubic-bezier(.2,.8,.3,1.15) both;transform-origin:50% 100%}
@keyframes swingIn{from{opacity:0;transform:translateY(36px) rotate(-2.6deg)}}
.ringPulse{animation:ringPulse 2.6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes ringPulse{0%,100%{transform:scale(.88);opacity:.95}50%{transform:scale(1.14);opacity:.4}}
.nudge{animation:nudgeX 1.9s ease-in-out infinite}
@keyframes nudgeX{0%,100%{transform:translateX(0)}50%{transform:translateX(7px)}}
.fadeIn{animation:fadeIn .8s ease both}
@keyframes fadeIn{from{opacity:0}}
"""
    delay = 1.45 + idx * 0.18
    lines = TILE_LINES[tile_def["id"]]
    parts = [svg_open(283, 300, f"{tile_def['kicker']} — {tile_def['title']}", css),
             f'<rect width="283" height="300" rx="16" fill="{PANEL}"/>'
             f'<rect x="0.5" y="0.5" width="282" height="299" rx="15.5" fill="none" stroke="{HAIR}"/>',
             f'<g class="swing" style="animation-delay:{delay:.2f}s">',
             f'<circle class="ringPulse" cx="239" cy="44" r="16" fill="none" stroke="{GOLD}" stroke-width="1.6"/>',
             f'<circle cx="239" cy="44" r="3.2" fill="{GOLD}"/>',
             f'<text x="28" y="60" font-family="{MONO}" font-size="13" letter-spacing="3.5" '
             f'fill="{GOLD}">{xesc(tile_def["kicker"])}</text>']
    for j, line in enumerate(lines):
        parts.append(f'<text x="28" y="{94 + j*27}" font-family="{SANS}" font-size="21" '
                     f'font-weight="600" fill="{INK}">{xesc(line)}</text>')
    parts.append(count_up_texts(28, 202, value, delay + 0.45))
    parts.append(f'<text class="fadeIn" style="animation-delay:{delay + .8:.2f}s" x="28" y="230" '
                 f'font-family="{SANS}" font-size="13.5" fill="{MUTED}">{xesc(tile_def["label"])}</text>')
    parts.append(f'<rect x="28" y="248" width="44" height="2.5" fill="{GOLD}"/>')
    # Arrow drawn as a path (not a text glyph) so it renders in every font stack.
    parts.append(f'<g transform="translate(28,274)"><g class="nudge">'
                 f'<path d="M0 0 H25 M18 -6.5 L25.5 0 L18 6.5" fill="none" stroke="{GOLD}" '
                 f'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></g></g>')
    parts.append("</g></svg>")
    return "".join(parts)


# ---- repo cards -----------------------------------------------------------------
def repo_card(repo, idx):
    css = """
.fadeRise{animation:fadeRise .7s cubic-bezier(.2,.7,.25,1) both}
@keyframes fadeRise{from{opacity:0;transform:translateY(16px)}}
"""
    delay = 2.05 + idx * 0.15
    lang = repo["language"]
    parts = [svg_open(430, 150, f"{repo['name']} — {repo['description']}", css),
             bg_rect(430, 150),
             f'<g class="fadeRise" style="animation-delay:{delay:.2f}s">',
             f'<rect x="26" y="29" width="9" height="9" rx="2" fill="{GOLD}"/>',
             f'<text x="45" y="40" font-family="{SANS}" font-size="19" font-weight="700" '
             f'fill="{GOLD}">{xesc(repo["name"])}</text>',
             f'<rect x="350" y="23" width="54" height="19" rx="9.5" fill="none" stroke="{HAIR}"/>',
             f'<text x="377" y="36.5" text-anchor="middle" font-family="{SANS}" font-size="9.5" '
             f'fill="{MUTED}">Public</text>',
             f'<text x="26" y="76" font-family="{SANS}" font-size="14.5" fill="{INK}" '
             f'opacity=".88">{xesc(repo["description"])}</text>',
             f'<circle cx="32" cy="112" r="5" fill="{LANG_COLOR.get(lang, GOLD)}"/>',
             f'<text x="45" y="117" font-family="{SANS}" font-size="12.5" fill="{MUTED}">{xesc(lang)}</text>',
             f'<text x="384" y="117" text-anchor="end" font-family="{SANS}" font-size="12" '
             f'fill="{GOLD}">View</text>',
             f'<path d="M390 112 H401 M396.5 108 L401.5 112 L396.5 116" fill="none" '
             f'stroke="{GOLD}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
             "</g></svg>"]
    return "".join(parts)


# ---- main -----------------------------------------------------------------------
def main():
    with open(os.path.join(ROOT, "data", "profile.json"), encoding="utf-8") as fh:
        profile = json.load(fh)
    with open(os.path.join(ROOT, "data", "contributions.json"), encoding="utf-8") as fh:
        contrib = json.load(fh)
    days = sorted(contrib["contributions"], key=lambda d: d["date"])
    stats = compute_stats(days)

    tile_values = {
        "publicRepos": profile["publicRepos"],
        "totalContributions": stats["total"],
        "activeDays": stats["activeDays"],
    }
    cards = {
        "hero.svg": hero(profile, stats),
        "heatmap.svg": heatmap(days, stats),
        "activity.svg": activity(stats),
    }
    for i, t in enumerate(profile["tiles"]):
        cards[f"{t['id']}.svg"] = tile(t, tile_values[t["countKey"]], i)
    for i, r in enumerate(profile["featuredRepos"]):
        cards[r["file"]] = repo_card(r, i)

    os.makedirs(OUTDIR, exist_ok=True)
    for name, svg in cards.items():
        with open(os.path.join(OUTDIR, name), "w", encoding="utf-8") as fh:
            fh.write(svg)
    print(json.dumps({
        "cards": sorted(cards),
        "outdir": OUTDIR,
        "static": STATIC,
        "stats": {
            "total": stats["total"],
            "activeDays": stats["activeDays"],
            "longestStreak": stats["longestStreak"],
            "busiestDay": stats["busiestDay"],
            "busiestCount": stats["busiestCount"],
            "bestMonth": month_label(stats["bestMonthKey"])[1],
            "bestMonthCount": stats["bestMonthCount"],
        },
    }, indent=1))


if __name__ == "__main__":
    main()
