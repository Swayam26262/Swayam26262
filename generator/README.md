# Profile generator

Everything visual on the profile README is an SVG rendered from
[`profile.toml`](profile.toml). Edit that file, push to `main`, and the
**Profile refresh** workflow rebuilds the artwork. The same workflow also runs
every day to refresh the live GitHub and LeetCode numbers and the contribution
snake.

## Run it locally

```bash
pip install -r generator/requirements.txt
python generator/build.py                      # every card, from the cached live data
python generator/build.py hero terminal        # just these cards
GITHUB_TOKEN=... python generator/build.py --live   # refresh live data first
python -m unittest discover -s generator/tests
```

Output goes to `assets/` as `<card>-dark.svg` and `<card>-light.svg`. The
README picks one with `<picture>` and `prefers-color-scheme`.

## What's where

| Path | What it does |
| --- | --- |
| `profile.toml` | All the words: taglines, terminal lines, impact numbers, timeline, stack, projects, links |
| `build.py` | Renders every card in both themes |
| `cards/` | One module per sheet: hero, buttons, about, impact, journey, stack, projects, telemetry, footer |
| `core/design.py` | The design system: 8pt grid, hard 1px rules, solid offset block shadows, hatch/dot textures |
| `core/` | Also fonts (subset per SVG, embedded as WOFF2), flat themes, icons, typing and odometer animations |
| `live.py` | GitHub GraphQL + LeetCode fetchers; results are cached in `data/live.json` |
| `connect4/` | The README Connect Four game: engine, AI, board art and the workflow runner |

The look is deliberately flat: paper, ink and one signal orange, no gradients,
no glows, no rounded pills. Display type is Instrument Serif, text is
Instrument Sans, utilities are JetBrains Mono, and every box, padding and gap
sits on an 8px grid.

The projects bento shows the first six `[[projects]]`; keep the text links under
it in the README in sync when you change them.

## Connect Four

The column buttons open an issue titled `c4|drop|<column>`. The **Connect Four**
workflow plays the move, lets the AI reply (negamax with alpha-beta pruning,
`DEPTH` in `connect4/game.py`), redraws the board between the
`CONNECT4:START/END` markers in the README, and closes the issue. Game state is
in `data/connect4.json`. To reset everything, delete that file and run
`python generator/connect4/play.py --render`.

## Credits

- Fonts: [Instrument Serif and Instrument Sans](https://github.com/Instrument/instrument-serif) and
  [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono), all under the SIL Open Font License
  (see `fonts/OFL-*.txt`).
- Brand icons: [Simple Icons](https://simpleicons.org) (CC0); the LinkedIn and AWS marks come from
  [skill-icons](https://github.com/tandpfun/skill-icons) (MIT, see `data/LICENSE-skill-icons.txt`).
- Snake: [Platane/snk](https://github.com/Platane/snk).
