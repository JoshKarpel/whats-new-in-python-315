# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

An executable talk: every slide is a [counterweight](https://github.com/JoshKarpel/counterweight)
component, and the code on screen is a real file the slide runs, live, on 3.15 and 3.14.
`PLAN.md` is the design doc: the running order, what each slide shows and why,
and the architecture decisions behind the deck.
Each module's docstring says what role it plays; read those before adding a file.

## Commands

`just --list` shows every recipe. The ones you'll reach for:

- `just setup` installs the six interpreters the runs need, the environment, and the git hook.
  Most tests need it first.
- `just test` runs mypy, then pytest. Arguments go to pytest, so
  `just test tests/test_animation.py -k shine` runs a single test.
  Run pytest without mypy with `uv run pytest ...`.
- `just check-examples` runs only `tests/test_examples.py`, which executes every slide's runs.
- `just present` presents the deck; `just watch` restarts it on any change under `src/` or `examples/`,
  landing back on the same slide.
- `just export` regenerates `slides.html`.
  A pre-commit hook does the same on any change under `src/` or `examples/` and fails the commit
  when the file changes, so include the regenerated `slides.html` with the change rather than editing it.
- `just record` regenerates `slides.cast`, the deck presented by an autopilot with every run and slide `tour`.
  It takes minutes of real time and differs on every run, so no hook regenerates it.
- `just showcase` regenerates `transitions.cast`, every slide transition played one after another,
  and `just grid-showcase` regenerates `grid-transitions.cast`, every one of the grid's own transitions.
  They wait for nothing real, so they come out the same every time, and pre-commit hooks regenerate them as the export's does.
- `pre-commit-autofix` (or `just pre-commit`) runs ruff and the other hooks.

counterweight is pinned by `uv.lock` (`pyproject.toml` says whether to a release or a commit on `main`), and moves fast.
Read its API from the installed source under `.venv/lib/python3.15/site-packages/counterweight/`,
not from memory or its docs site.

## How a slide gets on screen

- A section module in `sections/` builds a tuple of `Slide` values (`slides.py`):
  a title, a content component taking `SlideProps`, a reveal-step count, cited PEPs, and `runs`.
  `deck.py` concatenates the sections into `SLIDES`, in running order.
- Everything walks that one tuple: the presenter (`presenter.py`, the root component),
  the slide grid, the export, the recording, the smoke test, and the example check.
- A slide's code comes from `examples/` through `components/code.py`,
  and its `runs` are `Run` values (`runs.py`, built with helpers like `python` and `on_both`)
  carrying an `Expect`.
  `run_pane` executes them on the number keys or a click on a run's name, and `test_examples.py` executes every one and asserts its `Expect`,
  so what's shown, what runs, and what's tested are one declaration.
  Changing an example's output means changing its `Expect` in the section module.
- On stage an example is editable. A run executes a temporary copy of `examples/` with the slide's edits
  written over it, never `examples/` itself.
- Machine facts (interpreter paths, the deck's PID, where flamegraphs are served) are resolved once,
  at startup, into a `Host` (`host.py`), so a missing interpreter fails at launch rather than on a key press.
- Diagrams in `diagrams/` are drawn by hand: nodes and box-drawing text placed at fixed cell coordinates
  inside an `area` (`diagrams/draw.py`), with reveal steps chosen by `props.step`.

## Constraints that aren't visible from one file

- `examples/` is slide content: ruff skips it, each file is formatted for the screen
  (one blank line between definitions, which `test_example_layout.py` checks),
  and some are invalid on purpose on one interpreter or another.
  Don't "fix" an example's style or a deliberate error.
- The deck is drawn for 100x30 (`size.PRESENTING`), and diagrams are laid out for that exact width.
  `test_diagrams.py` checks a drawing's width, not its height or what overlaps,
  so look at the rendered slide after changing a layout (see below).
- A swipe (`components/swipe.py`) mounts two slides at once, so each mounting of a slide gets its own key and
  `FocusHandle` (`presenter.Mounting`): never give two mounted slides one handle, or key a slide by its index.
- Mounting a slide starts nothing: no subprocess, focus grab or explanatory animation.
  The slide grid, the smoke test and the export each mount many slides at once,
  so anything started on mount starts in all of them, and the smoke test fails if a child process is left over.
  A transition drawn from pictures (`components/crossing.py`) also renders the arriving slide headless, in an app
  of its own, moved on by the transition's length, and ends on that picture, so the slide has to draw the same
  however it's mounted: anything that moves counts from its own mount, never the app's start.
- Time comes only from counterweight's clock, through its `use_progress` and `use_loop`,
  used as `components/animation.py` says.
  Tests and the export run on a frozen clock (`export.EXPORT_CLOCK`) moved by `AdvanceClock`,
  which is what keeps both deterministic.

## Seeing a change

Render a slide to text headless rather than asking for a screenshot:
pass a tuple of just that slide to `export.screenshots` with a `Host` built the way
`__main__.py` builds the export's, then print each frame's `text(ansi=False)`.
`tests/test_animation.py` and `tests/test_diagrams.py` show the same pattern
for a single component.
