# What's New in Python 3.15

A whirlwind tour of how Python is getting better, as an executable deck:
the slides are [counterweight](https://github.com/JoshKarpel/counterweight) components,
and the code on screen is the code that runs, live, on 3.14 and 3.15 side by side.

[`slides.html`](slides.html) is a static copy of every slide.

## Running it yourself

```bash
docker run --rm -it --network none ghcr.io/joshkarpel/whats-new-in-python-315:main
```

The deck depends on counterweight from git, a prebuilt pre-1.0 `libghostty-vt`, three type checkers,
and six Python interpreters, so it runs in a container rather than on your machine.
The container is the safety boundary: with `--network none` and nothing mounted,
a compromised dependency can't read your files or credentials, and can't send anything anywhere.
Mounting your home directory or the Docker socket, or running with `--privileged`, removes that boundary.

`main` follows the latest build. To run a fixed build, use a commit SHA tag instead.

The deck is drawn for a 90x30 terminal: press F2 to see your terminal's size, green when it fits.

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
| Left / Right | previous / next slide |
| Space | reveal the next step |
| `1`–`9` | run the slide's programs |
| Escape | stop the runs in progress |
| `r` | reset the slide |
| `d` | the slide grid: arrows move, Enter jumps, Escape goes back |
| F1 / F2 | the clock / the size check |
| Ctrl+C | quit |

## Developing

Install [mise](https://mise.jdx.dev/), then run `just setup`, which installs the interpreters and the environment.
`just --list` shows the other recipes.
