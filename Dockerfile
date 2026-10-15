# The image others run the deck from, with everything it uses baked in, so it runs with `--network none`:
# the interpreters, the locked environment, the type checkers (and Node for pyright), the old mypy, hyperfine,
# and a C compiler and perf for the frame pointer demo.
#
#   docker run --rm -it --network none ghcr.io/joshkarpel/whats-new-in-python-315:main

FROM docker.io/jdxcode/mise:2026.10.3 AS mise

FROM docker.io/library/debian:trixie-slim

# git: counterweight is a git source. gcc and libc6-dev: the frame pointer demo builds a C extension.
# tzdata: the footer's clock reads Chicago time, through zoneinfo.
# linux-perf: the frame pointer demo samples with perf. nodejs: pyright runs on it.
# locales: the UTF-8 slide runs under en_US, a Latin-1 locale, to show the old default.
RUN <<EOF
set -e
apt-get update
apt-get install -y --no-install-recommends ca-certificates git gcc libc6-dev linux-perf locales nodejs tzdata
echo "en_US ISO-8859-1" >> /etc/locale.gen
locale-gen
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF

COPY --from=mise /usr/local/bin/mise /usr/local/bin/mise

RUN <<EOF
set -e
groupadd --gid 1001 deck
useradd --uid 1001 --gid deck --create-home --shell /bin/bash deck
EOF
USER deck
WORKDIR /home/deck/deck

ENV PATH=/home/deck/.local/share/mise/shims:/home/deck/.local/bin:$PATH
ENV MISE_LOCKED=1
ENV UV_PYTHON_PREFERENCE=only-managed
ENV UV_LINK_MODE=copy
# The flamegraph's link: the deck can't ask exe.dev for a VM name here, so it serves on every interface
# and links to the port published with `-p 127.0.0.1:8315:8315`.
ENV WHATS_NEW_FLAMEGRAPH_BASE_URL=http://127.0.0.1:8315
ENV WHATS_NEW_FLAMEGRAPH_BIND=0.0.0.0

# Tools first, then the environment, then the source, so a source change rebuilds only the last layers.
COPY --chown=deck:deck mise.toml mise.lock ./
RUN <<EOF
set -e
mise trust
mise install
EOF

COPY --chown=deck:deck pyproject.toml uv.lock .python-version README.md ./
RUN uv sync --frozen --no-install-project

COPY --chown=deck:deck src ./src
RUN <<EOF
set -e
uv sync --frozen
uv python install $(uv run --frozen python -m whats_new.runs)
EOF

# Fetch what pyright and the old mypy download on first use, so they work offline.
RUN <<EOF
set -e
uv run --frozen pyright --version
uvx --from mypy==2.3.1 mypy --version
EOF

COPY --chown=deck:deck examples ./examples
COPY --chown=deck:deck demos ./demos
COPY --chown=deck:deck tests ./tests

# Nothing may reach for the network at run time; uv in particular resolves nothing from here on.
ENV UV_OFFLINE=1
ENV UV_FROZEN=1

ENTRYPOINT ["/home/deck/deck/.venv/bin/python", "-m", "whats_new"]
