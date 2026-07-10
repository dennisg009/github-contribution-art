# github-contribution-art

Spell a word in the GitHub contribution graph — as a ready-to-upload **LinkedIn
banner**, as an **organic-looking graph**, or as **real backdated commits** you
push to a throwaway account.

The contribution graph is just a 7-row (Sun–Sat) × ~53-column (weeks) grid of
green squares. Line up enough commits on the right days and the squares spell
whatever you want. This is a well-known, harmless trick — the commits are real,
just empty and decorative.

![DENNIS as a LinkedIn banner](examples/dennis-linkedin-banner.png)

Or the "organic" look — varied green shades plus a little faint background
activity, so it reads like a genuinely busy year rather than obviously-planted
art (inspired by [Lauren Frailey](https://www.linkedin.com/in/lauren-frailey/)'s
"MINTLIFY" contribution graph):

![DENNIS as an organic contribution graph](examples/dennis-graph-preview.png)

## Quick start

Only dependency is `matplotlib` (for the PNG renders):

```bash
pip install -r requirements.txt
```

```bash
# Organic year-graph preview (varied greens + faint noise) — a PNG, no commits
python3 spell_graph.py

# Flat, bright LinkedIn banner at the exact 4:1 ratio — a PNG, no commits
python3 spell_graph.py --banner

# Spell any word (A–Z, 0–9)
python3 spell_graph.py --word ALICE --banner
python3 spell_graph.py --word OPENAI --year 2026
```

Both PNGs land in the current directory (`dennis-graph-preview.png`,
`dennis-linkedin-banner.png`, or `<word>-…` for a custom word).

## The two routes

### 1. Just want the image? (recommended)

If the goal is a LinkedIn banner or a graphic, you don't need GitHub at all —
`--banner` renders a pixel-perfect PNG you upload directly. No account, no
commits, no waiting.

- **LinkedIn personal banner: 1584 × 396 px (4:1).** The tool renders at 2×
  (3168 × 792) for a crisp retina look.
- **Safe zones:** your profile photo overlaps the **bottom-left**, and your
  name/headline sit over the **lower strip** on desktop (mobile crops tighter).
  Keep the letters centered and clear of that bottom-left corner.

### 2. Want it live on a real GitHub profile?

```bash
python3 spell_graph.py --commit --name "Your Name" --email you@verified.com
```

This writes `./github-art` — a local git repo full of backdated empty commits
(reversible until you push). Then:

```bash
cd github-art
git branch -M main
git remote add origin https://github.com/<USERNAME>/contribution-art.git
git push -u origin main       # use a Personal Access Token as the password
```

The letters only turn green if `--email` is a **verified** email on the target
account (this is the #1 gotcha). A **fresh throwaway account** gives the cleanest
result — a blank graph means no stray green in the "off" pixels.

> **Tip:** a past year (the default, `--year 2025`) shows the whole word
> immediately. A current year works too, but any columns past today's date fill
> in as those weeks arrive.

## Options

| Flag | Default | What it does |
|------|---------|--------------|
| `--word` | `DENNIS` | Word to spell (A–Z, 0–9; unknown chars become spaces) |
| `--banner` | — | Render the flat 4:1 LinkedIn banner instead of the organic graph |
| `--commit` | — | Build `./github-art` of backdated commits to push |
| `--year` | `2025` | Target year for the graph/commits |
| `--name` | `Dennis Gavrilenko` | Git author name (commit mode) |
| `--email` | `you@example.com` | Git author email — must be verified on the target account |
| `--margin` | `10` | Left inset in weeks (centers the word in the year grid) |
| `--seed` | `7` | RNG seed for the shade/noise layout |
| `--out` | auto | Output PNG path |

## How it works

Each character maps to a 7-row pixel glyph. `spell_graph.py` places those pixels
on the graph grid, then either colors them into a PNG or, in `--commit` mode,
stamps N empty commits onto the matching calendar date via `GIT_AUTHOR_DATE` /
`GIT_COMMITTER_DATE`. The organic look comes from giving each lit cell a random
commit count (so shades vary) and sprinkling a few faint "real" commits around.

## Notes

- Empty decorative commits aren't a GitHub ToS violation, but do this on a
  repo/account you own and don't use it to fake activity you'd misrepresent.
- If you paste a Personal Access Token to push, revoke it afterward — or, better,
  run the `git push` yourself so the token never leaves your machine.

## License

MIT — see [LICENSE](LICENSE).
