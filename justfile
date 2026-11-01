#!/usr/bin/env just --justfile

set dotenv-load
set ignore-comments

[default]
[doc('List available recipes')]
list:
    @just --list

alias l := list

# mise installs the tools in mise.toml; this does what mise can't: the six interpreters the demos run on
# (the list comes from `Interpreter` in src/whats_new/runs.py), the project environment, the git hook,
# and a cached copy of the deliberately old mypy the sentinel slide runs, so it works offline after.
[doc('Install everything the deck needs beyond mise: interpreters, the environment, hooks')]
setup:
    mise install
    uv sync --locked
    uv python install $(uv run --frozen python -m whats_new.runs)
    uv run --frozen pre-commit install
    uvx --from mypy==2.3.1 mypy --version
    @command -v perf >/dev/null || echo "perf is missing: install linux-tools for your kernel for the frame pointer demo"
    @command -v cc >/dev/null || echo "cc is missing: install a C compiler for the frame pointer demo"

[doc('Present the deck')]
present:
    exec uv run --frozen python -m whats_new

alias p := present

# The deck checkpoints its slide and code theme to a temp file, so each restart lands where it left off.
# Runs from .venv rather than under `uv run`, which holds the uv cache lock for as long as it lives and
# so blocks every `uv cache prune` for the whole editing session.
[doc('Present the deck, restarting it whenever a source or example file changes')]
watch:
    uv sync --frozen
    exec .venv/bin/watchfiles --verbosity warning '.venv/bin/python -m whats_new' src/ examples/

alias w := watch

[doc('Regenerate slides.html, the shareable export')]
export:
    uv run --frozen python -m whats_new export

# Not a pre-commit hook as the export is: it runs every demo, which takes minutes and comes out different every time.
[doc('Record slides.cast: the whole deck presented by an autopilot, running every demo')]
record:
    uv run --frozen python -m whats_new record

[doc('Record transitions.cast: every slide transition F6 offers, played one after another')]
showcase:
    uv run --frozen python -m whats_new showcase

[doc("Record grid-transitions.cast: every one of the grid's own transitions F7 offers, played one after another")]
grid-showcase:
    uv run --frozen python -m whats_new grid-showcase

[doc('Upload slides.cast to asciinema, passing any arguments on to asciinema upload')]
upload *ARGS:
    asciinema upload slides.cast {{ ARGS }}

[doc('Run every run declared on every slide and check its outcome')]
check-examples *ARGS:
    uv run --frozen pytest tests/test_examples.py {{ ARGS }}

[doc('Check the presenting setup, then print a checklist for the browser side')]
rehearse:
    uv run --frozen python -m whats_new rehearse

[doc('Run type checking, then the tests, passing any arguments on to pytest')]
[positional-arguments]
test *ARGS:
    uv run --frozen mypy
    uv run --frozen pytest "$@"

alias t := test

[doc('Stage updated files and run pre-commit hooks')]
pre-commit:
    git add --update
    uv run --frozen pre-commit

[doc('Upgrade all dependencies, and the tools in mise.toml')]
upgrade:
    uv lock --upgrade
    mise upgrade --local --bump
    mise lock
