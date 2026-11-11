# What's New in Python 3.15

A whirlwind tour of how Python is getting better, as an executable deck:
the slides are [counterweight](https://github.com/JoshKarpel/counterweight) components,
and the code on screen is the code that runs, live, on 3.15 and on 3.14.

[`slides.html`](slides.html) is a static copy of every slide,
and [`slides.cast`](slides.cast) is a recording of the deck presented, every demo run,
which [asciinema](https://asciinema.org/) plays with `asciinema play slides.cast`.
[`transitions.cast`](transitions.cast) shows off every slide transition the deck can play, one after another,
and [`grid-transitions.cast`](grid-transitions.cast) every way the slide grid can open and close.

## Running it yourself

```bash
docker run --rm -it --network none ghcr.io/joshkarpel/whats-new-in-python-315:main
```

The deck depends on a pre-1.0 counterweight, a prebuilt pre-1.0 `libghostty-vt`, three type checkers,
and six Python interpreters, so it runs in a container rather than on your machine.
The container is the safety boundary: with `--network none` and nothing mounted,
a compromised dependency can't read your files or credentials, and can't send anything anywhere.
Mounting your home directory or the Docker socket, or running with `--privileged`, removes that boundary.

`main` follows the latest build. To run a fixed build, use a commit SHA tag instead.

The deck is drawn for a 100x30 terminal: press F2 to see your terminal's size, green when it fits.

The Tachyon slide can serve a flamegraph to your browser, which needs a port, so give the container one,
on your machine's loopback only:

```bash
docker run --rm -it -p 127.0.0.1:8315:8315 ghcr.io/joshkarpel/whats-new-in-python-315:main
```

What doesn't work in a default container:

- The frame pointer demo: Docker's default seccomp profile blocks `perf`.
  The slide shows `perf`'s error, as it would show any run's.
  Running with `--privileged` would fix it, and would also remove the isolation the container is for.

### Keys

| Key | Does |
|---|---|
| Left / Right | previous / next slide, skipping ghosts unless on one |
| Shift+Left / Shift+Right | previous / next slide, ghost or not |
| Page Up / Page Down | the start of this section (or the previous one, from its start) / the next section |
| Space | reveal the next step |
| `1`–`9` | run the slide's programs, with any edits to its code |
| Escape | stop the run in progress |
| Up / Down | scroll the run's output |
| Tab / Shift+Tab | move between the slide's code and its runs: in the code, every key types until Tab |
| `r` | reset the slide, undoing its edits |
| `d` | the slide grid, one section at a time: arrows move, Enter or `d` jumps, Escape goes back, `g` makes the selected slide a ghost 👻 or not |
| F1 / F2 | the clock / the size check |
| F4 | pick the code theme: type to narrow the list, Up and Down move, Enter chooses, F4 closes |
| F6 | pick the slide transition: off, random for a different one each move, swipe, or one of the effects (type to narrow the list); as F4's picker, F6 closes |
| F7 | pick the grid's transition as it opens and closes: off, random, one of the grid's own effects or the slide effects, or a section's bar for a different one of that section each time; F7 closes |
| F8 | pick the transition speed, from a quarter to twice as fast; F8 closes |
| Ctrl+C | quit |

A ghost is a slide trimmed from the talk but kept in the deck:
presenting skips it and the slide count leaves it out, but the grid and Shift+Left and Shift+Right still reach it.
`Slide.is_ghost` sets one in the deck; `g` overrides that for practice, and the overrides survive a restart.

## Developing

Install [mise](https://mise.jdx.dev/), then run `just setup`, which installs the interpreters and the environment.
`just --list` shows the other recipes.
