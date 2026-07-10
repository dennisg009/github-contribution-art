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
# Full contribution-chart PNG — month headers, weekday + "N contributions in
# YEAR" labels, the Less→More legend. Looks like a real profile; no commits.
python3 spell_graph.py --year 2019

# Flat, bright LinkedIn banner at the exact 4:1 ratio — a PNG, no commits
python3 spell_graph.py --banner

# Spell any word (A–Z, 0–9)
python3 spell_graph.py --word ALICE --banner
python3 spell_graph.py --word OPENAI --year 2021

# Dial the total number of commits shown for the year (default is ~1000)
python3 spell_graph.py --year 2019 --commits 250

# Drop the commits into a specific quiet year, or repeat across a range
python3 spell_graph.py --commit --year 2019       # one emptier year
python3 spell_graph.py --commit --year 2016-2019  # spanning four years
```

Both PNGs land in the current directory (`dennis-graph-preview.png`,
`dennis-linkedin-banner.png`, or `<word>-…` for a custom word).

## The two routes

### 1. Just want the image? (recommended)

If the goal is a graphic — not live commits — you don't need GitHub at all. Two
no-commit renders:

- **`python3 spell_graph.py --year 2019` → a full contribution chart.** Draws the
  53×7 graph *with the real GitHub chrome*: month headers across the top,
  Mon/Wed/Fri labels down the side, an "N contributions in YEAR" heading, and the
  Less→More legend. The `--year` only sets the month/heading labels here (no
  commits are made), so pick whichever year you want the image to read as. Upload
  or share the PNG directly — it looks like a screenshot of a real profile.
- **`python3 spell_graph.py --banner` → a LinkedIn banner** at **1584 × 396 px
  (4:1)**, rendered at 2× (3168 × 792) for retina. Safe zones: your profile photo
  overlaps the **bottom-left** and your name/headline sit over the **lower strip**
  on desktop — keep the letters centered and clear of that corner.

Both are dry runs; nothing touches GitHub. Use the commit route below only if you
want the art *live* on an actual profile graph.

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
>
> **No throwaway account?** Point `--year` at a year where your real graph is
> quiet, so the art lands on empty squares instead of colliding with existing
> commits — `--year 2019`. Pass a range like `--year 2016-2019` to repeat the
> word across a multi-year blank stretch (each year gets its own copy). Years
> before GitHub existed (2008) are rejected; future years warn, since those
> squares only fill in as their dates arrive.

### Putting the art on your MAIN account (no throwaway)

If you want this on your real profile, the trick is to aim at an **empty year**
so the letters don't collide with commits you already have.

1. **Find a quiet year.** Open your profile, use the year switcher on the
   contribution graph (right-hand side), and look for a year that's mostly grey
   — often an early year before you were active. Say that's **2019**.
2. **Build the commits for that year:**
   ```bash
   python3 spell_graph.py --commit --word DENNIS --year 2019 \
       --name "Your Name" --email you@verified.com
   ```
   Use an email that is **verified on your main account** (Settings → Emails),
   or the squares stay grey. This only writes a local `./github-art` folder — it
   touches nothing on GitHub yet, so it's safe to inspect or delete.
3. **Make a brand-new EMPTY repo** on your main account (e.g. `contribution-art`)
   — no README, no license, so the first push is clean.
4. **Push it:**
   ```bash
   cd github-art
   git branch -M main
   git remote add origin https://github.com/<YOUR-USERNAME>/contribution-art.git
   git push -u origin main
   ```
5. **Reload your profile** and switch to 2019 — the word should be spelled out.

**Because it's your real account, keep in mind:** this adds a public repo full of
empty commits, the contributions are permanent unless you delete that repo, and
picking a year where you *do* have activity will blend your real commits into the
letters and muddy them. Prefer the emptiest year you can find.

**Tune the volume.** The default paints ~1000 commits into the year, which is a
lot — roughly 3/day. Use `--commits` to pick a more believable total for that
year, e.g. `--commits 250`. It scales the shading proportionally, so the word
still reads; it just gets dimmer as the count drops.

## Options

| Flag | Default | What it does |
|------|---------|--------------|
| `--word` | `DENNIS` | Word to spell (A–Z, 0–9; unknown chars become spaces) |
| `--banner` | — | Render the flat 4:1 LinkedIn banner instead of the organic graph |
| `--commit` | — | Build `./github-art` of backdated commits to push |
| `--year` | `2025` | Target year for the graph/commits — a single year (`2019`) or an inclusive range (`2016-2019`) that repeats the word across each year |
| `--commits` | auto (~1000) | Approx total commits/contributions to show in the year — scales the per-cell shading to hit it (e.g. `--commits 250`) |
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
