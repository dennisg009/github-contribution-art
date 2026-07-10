#!/usr/bin/env python3
"""Spell a word in a GitHub contribution graph — as an image or as real commits.

The GitHub contribution graph is a 7-row (Sun–Sat) × ~53-column (weeks) grid of
green squares. Backdate enough commits onto the right days and the squares spell
a word. This tool renders that art three ways:

    # Organic year-graph preview (varied greens + faint noise) — a PNG, no commits
    python3 spell_graph.py

    # Flat, bright LinkedIn banner at the exact 4:1 ratio — a PNG, no commits
    python3 spell_graph.py --banner

    # Build a local repo of backdated empty commits (reversible until you push)
    python3 spell_graph.py --commit --email you@verified-on-github.com

Spell any word (uppercase A–Z and 0–9 supported):

    python3 spell_graph.py --word ALICE --year 2021
    python3 spell_graph.py --word OPENAI --banner

Pick the year that lands your art on an empty patch of graph — handy on a real
account with a crowded recent history and no throwaway to fall back on. Point
--year at a quiet past year, or give a range to repeat the word across several:

    python3 spell_graph.py --commit --year 2019       # one emptier year
    python3 spell_graph.py --commit --year 2016-2019  # spanning four years

For the commit route, push ./github-art to a brand-new EMPTY GitHub repo. A fresh
throwaway account gives the cleanest letters (blank canvas). The commits are real
but empty and decorative — a well-known, harmless trick, not a ToS violation.
"""
import argparse
import os
import random
import subprocess
import sys
from datetime import date, timedelta

GITHUB_BORN = 2008  # contribution graphs don't exist before GitHub did

# ---------------- DEFAULTS (override via CLI flags) ----------------
NAME = "Dennis Gavrilenko"   # git author name for --commit
EMAIL = "you@example.com"    # MUST be a VERIFIED email on the target account for green to show
YEAR = 2025                  # a fully-past year shows the whole word immediately
WORD = "DENNIS"
MARGIN = 10                  # left inset in weeks, to center the word in the year grid
LETTER_LO, LETTER_HI = 6, 13 # commits per lit cell -> medium..bright, varied "organic" shades
NOISE_P, NOISE_MAX = 0.14, 3 # faint scattered "real" commits (L1) so it reads as genuine
SEED = 7                     # reproducible layout; change for a different noise pattern
COMMITS = None               # target total commits/year; None = natural ~1000 from per-cell shading
REPO_DIR = "github-art"      # where --commit writes the backdated-commit repo
# -------------------------------------------------------------------

# A 7-row pixel font ('#' = lit square). Most glyphs are 5 wide; 'I' and the
# space are narrower. glyphs() joins letters with a one-column gap.
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": ["#####", "#....", "#....", "#####", "....#", "....#", "#####"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    " ": ["..", "..", "..", "..", "..", "..", ".."],
}

# GitHub dark-theme palette.
BG, EMPTY = "#0d1117", "#161b22"
LEVELS = ["#0e4429", "#006d32", "#26a641", "#39d353"]  # L1..L4 greens
FG, FG_MUTED = "#e6edf3", "#7d8590"  # header text / muted month+day labels


def glyphs(word):
    """Turn a word into 7 rows of '#'/'.' pixels, one blank column between letters."""
    rows = [""] * 7
    chars = list(word)
    for i, ch in enumerate(chars):
        g = FONT.get(ch.upper())
        if g is None:  # unsupported char -> render a space so nothing breaks
            g = FONT[" "]
        for r in range(7):
            rows[r] += g[r]
        if i != len(chars) - 1:
            for r in range(7):
                rows[r] += "."
    return rows


def build_counts(rows, cfg):
    """Map lit pixels to commit counts, placed at MARGIN, plus faint background noise."""
    ww = len(rows[0])
    random.seed(cfg.seed)
    counts = {}
    for r in range(7):
        for c in range(ww):
            if rows[r][c] == "#":
                counts[(r, cfg.margin + c)] = random.randint(LETTER_LO, LETTER_HI)
    for r in range(7):
        for c in range(53):
            if (r, c) not in counts and random.random() < NOISE_P:
                counts[(r, c)] = random.randint(1, NOISE_MAX)
    if getattr(cfg, "commits", None):
        counts = scale_to_total(counts, cfg.commits)
    return counts


def scale_to_total(counts, target):
    """Rescale per-cell commit counts so the year's total is ~target, keeping the
    relative shading (every lit cell stays lit — min 1 — so the word never breaks)."""
    base = sum(counts.values())
    if base == 0 or target <= 0:
        return counts
    scaled = {k: max(1, round(v * target / base)) for k, v in counts.items()}
    got = sum(scaled.values())
    if got > target * 1.15:  # the min-1 floor dominated: target below the word's minimum
        print(f"note: ~{target} is fewer commits than the {got} needed to light every "
              "cell once; showing the dimmest full-word version.")
    return scaled


def _rounded(ax, x, y, color):
    from matplotlib.patches import FancyBboxPatch
    ax.add_patch(FancyBboxPatch(
        (x + 0.09, y + 0.09), 0.82, 0.82,
        boxstyle="round,pad=0,rounding_size=0.18", linewidth=0, facecolor=color))


def render_preview(counts, cfg, out):
    """A real-looking contribution chart PNG — the organic 53×7 graph plus the
    GitHub chrome (month headers, Mon/Wed/Fri labels, 'N contributions in YEAR'
    heading, and the Less→More legend). Use it straight, no commits needed."""
    import calendar
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    mx = max(counts.values())

    def color(n):
        if n <= 0:
            return EMPTY
        q = n / mx
        return LEVELS[0] if q <= .25 else LEVELS[1] if q <= .5 else LEVELS[2] if q <= .75 else LEVELS[3]

    year = cfg.years[0]
    fs = first_sunday(year)

    def date_of(r, c):
        return fs + timedelta(weeks=c, days=r)

    total = sum(n for (r, c), n in counts.items() if date_of(r, c).year == year)

    # Extra room: top for heading+months, left for weekday labels, bottom for legend.
    fig = plt.figure(figsize=(58 * 0.22, 12 * 0.22), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BG)
    fig.patch.set_facecolor(BG)
    ax.set_xlim(-6, 54)
    ax.set_ylim(-3.4, 9.6)
    ax.invert_yaxis()
    ax.axis("off")

    # Squares — days outside the target year stay blank (like GitHub's year view).
    for c in range(53):
        for r in range(7):
            if date_of(r, c).year != year:
                continue
            _rounded(ax, c, r, color(counts.get((r, c), 0)))

    # Heading, e.g. "137 contributions in 2019".
    ax.text(-5, -2.5, f"{total} contributions in {year}",
            color=FG, fontsize=9, ha="left", va="center")

    # Month labels at the first column each month appears in.
    seen = set()
    for c in range(53):
        d = date_of(0, c)
        if d.year == year and d.month not in seen:
            seen.add(d.month)
            ax.text(c + 0.1, -0.6, calendar.month_abbr[d.month],
                    color=FG_MUTED, fontsize=7, ha="left", va="center")

    # Weekday labels (GitHub shows only Mon/Wed/Fri).
    for r, lbl in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        ax.text(-0.6, r + 0.5, lbl, color=FG_MUTED, fontsize=6.5, ha="right", va="center")

    # Legend: Less [] [] [] [] [] More.
    ax.text(41.4, 8.5, "Less", color=FG_MUTED, fontsize=6.5, ha="right", va="center")
    for i, col in enumerate([EMPTY, *LEVELS]):
        _rounded(ax, 42 + i, 8, col)
    ax.text(48.4, 8.5, "More", color=FG_MUTED, fontsize=6.5, ha="left", va="center")

    fig.savefig(out, facecolor=BG)
    print(f"preview -> {os.path.abspath(out)}")


def render_banner(rows, out):
    """Flat, bright LinkedIn banner at exactly 1584×396 (4:1), rendered at 2×."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ww = len(rows[0])
    PAD_COLS, PAD_ROWS = 2, 1
    W, H, SCALE = 1584, 396, 2
    fig = plt.figure(figsize=(W * SCALE / 200, H * SCALE / 200), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BG)
    fig.patch.set_facecolor(BG)
    cols, rowsn = ww + 2 * PAD_COLS, 7 + 2 * PAD_ROWS
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rowsn)
    ax.invert_yaxis()
    ax.axis("off")
    for c in range(cols):
        for r in range(rowsn):
            gc, gr = c - PAD_COLS, r - PAD_ROWS
            lit = 0 <= gr < 7 and 0 <= gc < ww and rows[gr][gc] == "#"
            _rounded(ax, c, r, LEVELS[3] if lit else EMPTY)
    fig.savefig(out, facecolor=BG)
    print(f"banner  -> {os.path.abspath(out)}  ({W}×{H} at {SCALE}× = {W*SCALE}×{H*SCALE})")


def parse_years(spec):
    """Turn '2019' or '2016-2019' (inclusive, either order) into a sorted year list."""
    spec = str(spec).strip()
    try:
        if "-" in spec.lstrip("-"):  # a range like 2016-2019 (leading '-' = negative, not a range)
            lo, hi = (int(part) for part in spec.split("-", 1))
            lo, hi = sorted((lo, hi))
            return list(range(lo, hi + 1))
        return [int(spec)]
    except ValueError:
        sys.exit(f"error: --year expected a year or range (e.g. 2019 or 2016-2019), got '{spec}'")


def validate_years(years):
    """Reject pre-GitHub years; warn on future ones (which won't have filled in yet)."""
    too_old = [y for y in years if y < GITHUB_BORN]
    if too_old:
        sys.exit(f"error: {too_old} predate GitHub ({GITHUB_BORN}) — the graph can't show them. "
                 f"Pick {GITHUB_BORN} or later.")
    future = [y for y in years if y > date.today().year]
    if future:
        print(f"note: {future} sit in the future — the commits are valid, but those weeks only "
              "turn green as their dates arrive. A fully-past year shows the whole word at once.")


def year_label(years):
    """'2019' for one year, '2016–2019' for a contiguous span."""
    return str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"


def first_sunday(y):
    j = date(y, 1, 1)
    return j - timedelta(days=(j.weekday() + 1) % 7)


def generate(counts, cfg):
    """Write REPO_DIR full of backdated empty commits (one per unit in `counts`).

    The word is stamped into each year in cfg.years, so a range repeats the art
    across a multi-year span of otherwise-empty history.
    """
    def date_of(y, r, c):
        return first_sunday(y) + timedelta(weeks=c, days=r)

    os.makedirs(REPO_DIR, exist_ok=True)
    os.chdir(REPO_DIR)
    if not os.path.exists(".git"):
        subprocess.run(["git", "init", "-q"], check=True)
    subprocess.run(["git", "config", "user.name", cfg.name], check=True)
    subprocess.run(["git", "config", "user.email", cfg.email], check=True)
    total, days = 0, 0
    for y in cfg.years:
        cells = [(r, c, n) for (r, c), n in counts.items() if date_of(y, r, c).year == y]
        cells.sort(key=lambda t: date_of(y, t[0], t[1]))
        days += len(cells)
        for r, c, n in cells:
            stamp = f"{date_of(y, r, c).isoformat()}T12:00:00"
            env = {**os.environ, "GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}
            for _ in range(n):
                subprocess.run(["git", "commit", "--allow-empty", "-q", "-m", f"art {date_of(y, r, c)}"],
                               env=env, check=True)
                total += 1
    print(f"\nGenerated {total} commits across {days} days in ./{REPO_DIR}  "
          f"(email={cfg.email}, year={year_label(cfg.years)})")


def parse_args():
    p = argparse.ArgumentParser(description="Spell a word in a GitHub contribution graph.")
    p.add_argument("--word", default=WORD, help=f"word to spell (default: {WORD})")
    p.add_argument("--year", default=str(YEAR),
                   help=f"target year, or an inclusive range like 2016-2019 (default: {YEAR})")
    p.add_argument("--name", default=NAME, help="git author name for --commit")
    p.add_argument("--email", default=EMAIL,
                   help="git author email for --commit (must be VERIFIED on the target account)")
    p.add_argument("--commits", type=int, default=COMMITS, metavar="N",
                   help="approx total commits to show in the year (scales the shading; "
                        "default: the natural ~1000). Note: --commit builds the repo, --commits sets the count")
    p.add_argument("--margin", type=int, default=MARGIN, help="left inset in weeks (centers the word)")
    p.add_argument("--seed", type=int, default=SEED, help="RNG seed for the shade/noise layout")
    p.add_argument("--out", default=None, help="output PNG path (default derived from the word)")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--banner", action="store_true",
                      help="render a flat 4:1 LinkedIn banner instead of the organic graph")
    mode.add_argument("--commit", action="store_true",
                      help="build ./github-art of backdated commits (push it to a new empty repo)")
    return p.parse_args()


def main():
    cfg = parse_args()
    cfg.years = parse_years(cfg.year)
    validate_years(cfg.years)
    word = cfg.word.upper()
    rows = glyphs(word)
    slug = "".join(ch for ch in word.lower() if ch.isalnum()) or "art"
    span = year_label(cfg.years)

    if cfg.commit:
        counts = build_counts(rows, cfg)
        per_year = sum(counts.values())
        print(f"word={word} year={span}  lit+noise cells={len(counts)}  "
              f"total commits≈{per_year * len(cfg.years)}"
              + (f" ({per_year}/year × {len(cfg.years)})" if len(cfg.years) > 1 else ""))
        generate(counts, cfg)
        print("\nNEXT:\n"
              " 1. Create an EMPTY repo on the target account (e.g. 'contribution-art').\n"
              " 2. cd github-art && git branch -M main\n"
              " 3. git remote add origin https://github.com/<USERNAME>/contribution-art.git\n"
              " 4. git push -u origin main   (use a Personal Access Token as the password)\n"
              "\nThe letters turn green only if --email is VERIFIED on that account.")
    elif cfg.banner:
        out = cfg.out or f"{slug}-linkedin-banner.png"
        render_banner(rows, out)
        print("Upload to LinkedIn (Profile → edit banner). Keep letters clear of the "
              "bottom-left — your profile photo overlaps that corner.")
    else:
        counts = build_counts(rows, cfg)
        out = cfg.out or f"{slug}-graph-preview.png"
        print(f"word={word} year={span}  lit+noise cells={len(counts)}  "
              f"total commits≈{sum(counts.values())}")
        render_preview(counts, cfg, out)
        print("(dry run — rerun with --commit to build the repo, or --banner for the flat banner)")


if __name__ == "__main__":
    main()
