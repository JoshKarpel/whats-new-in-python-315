# What's New in Python 3.15: Talk Plan

This plan covers the talk's content, its running order, and how to build it as an
executable counterweight deck. It doesn't contain the slide text itself. The model
is the
[python-concurrency-and-parallelism](https://github.com/JoshKarpel/python-concurrency-and-parallelism)
talk: slides are counterweight components, and the code on screen is the code that runs.

Everything marked "observed" below was run on CPython 3.15.0rc2/rc3 and 3.14.7 on a
2-vCPU Linux VM. Probe scripts from that research live (temporarily) in the session
scratchpad. The useful ones get promoted into `examples/` during the build.

## The pitch

A whirlwind tour of how Python is getting better, for working Python programmers
(not C-extension authors). There's no single theme. The deck is executable: show a
snippet, press a key, and see its output, mypy's verdict, or a timing, run live on
3.14 and 3.15 side by side.

### Running observation: the features are unusually thorough

Several features arrive as complete toolkits rather than a single function:

- threading gains `serialize_iterator`, `synchronized_iterator` and `concurrent_tee`.
- unicodedata gains `iter_graphemes` plus five related property functions.
- base64 gains C rewrites plus `padded=`, `canonical=`, `wrapcol=` and `alphabet=`.
- lazy imports come with syntax, `-X`/env/`sys` switches, a filter hook,
  and a 3.14-compatible `__lazy_modules__`.
- Tachyon has a dozen output formats, a live TUI, async awareness, attach, dump and replay.

Collect these as the talk goes, and close by asking whether coding agents make this
kind of completeness cheaper. Pose it as a question, not a claim: there's no
evidence here about how any of these were written.

## Running order

The talk aims for about an hour, with questions taken during it, and can stretch
to 90 minutes. Items are tagged **core** (always in), **std** (in unless questions
run long) or **cut-first** (the first to go, or folded into the lightning round).

| Section | Minutes |
|---|---|
| 0. Opening | 3 |
| 1. Small things you'll use tomorrow | 12 |
| 2. Startup and imports | 7 |
| 3. Concurrency | 7 |
| 4. Typing | 8 |
| 5. Performance (Tachyon about 14 of it) | 22 |
| 6. Lightning round | 4 |
| 7. Closing | 2 |
| Material | 65 |

The cut-first items are worth about 6 minutes. Cutting them puts the material at
about an hour, and questions use up the slack before the 90-minute limit.

### 0. Opening (core)
- Title, who I am.
- "This deck is a Python 3.15 program": press a key to show `sys.version`, then run
  the same one-liner on 3.14.
- A quick glance at the 3.15 changelog's size, to set up the "thorough" observation.

### 1. Small things you'll use tomorrow

#### frozendict, PEP 814 (core)
- The builtin immutable mapping, set beside `frozenset`. Observed behavior:
  - `frozendict(x=1) == {"x": 1}` is True, mirroring `frozenset({1}) == {1}`.
  - It is _not_ a dict subclass: `isinstance(fd, dict)` is False, so use `Mapping`.
  - Hashing is order-insensitive, and it is hashable only if all its values are.
  - `fd | {...}` returns a frozendict.
- Example: the mutable-default-argument footgun, fixed with `options=frozendict(...)`.
- Example: `functools.cache` rejects a dict argument (`unhashable type: 'dict'`) and
  accepts a frozendict.
- The sad note: no literal syntax. The PEP defers it ("can be added later").

#### json `array_hook` (core, paired with frozendict)
- New `array_hook=` on `load`, `loads` and `JSONDecoder` (it is a TypeError on 3.14).
- Build `loads_immutable` and `load_immutable`:
  `json.loads(s, object_pairs_hook=frozendict, array_hook=tuple)`.
- Show the result is deeply immutable and usable as a cache key. Run the same file
  on 3.14 to show the TypeError.

#### Unpacking in comprehensions, PEP 798 (core)
- `[*row for row in rows]` replaces `list(chain.from_iterable(rows))`.
- `{**d for d in dicts}` merges dicts, last key wins.
- Async version: `[*page async for page in pages()]` flattens a paginated async API.
- Correction to the original premise: this does _not_ replace an async
  `chain`. The inner value must be a _sync_ iterable, so
  `[*src async for src in sources()]` over async generators raises
  `TypeError: Value after * must be an iterable, not async_generator`. It flattens
  an async stream of sync batches. Show that error on purpose.
- On 3.14 this is a `SyntaxError: iterable unpacking cannot be used in comprehension`.

#### `Counter.__xor__` (std)
- Gives `|c[x] - d[x]|` per key, i.e. `(c - d) + (d - c)`.
- Example: expected vs on-shelf inventory. `set(a) ^ set(b)` only catches missing
  SKUs; `Counter ^` also catches wrong quantities.

#### `bytearray.take_bytes` (std)
- Take the whole buffer as `bytes` without a copy; `bytes(ba)` always copied.
- Example: peeling an HTTP status line off a receive buffer.
- Observed on a 50 MB buffer: the copy doubles peak memory and `take_bytes` doesn't.
  Run it live with `tracemalloc` peak numbers.

#### `re.prefixmatch` (cut-first, lightning round)
- `match` is soft-deprecated: no warnings, no removal. `re.match is re.prefixmatch` at module level.
- The rationale is that "match" means "search" in most other regex engines.

#### `unicodedata.iter_graphemes` (std)
- `len("👨‍👩‍👧‍👦") == 7`, but it is one grapheme.
- Reversing `"Café 🇯🇵 👩‍💻!"` naively turns 🇯🇵 into 🇵🇯 and splits the ZWJ sequence.
  Reversing by grapheme gets it right.
- Personal hook: counterweight uses it
  ([#392](https://github.com/JoshKarpel/counterweight/issues/392), PR #398) for
  segmentation. Width still comes from `wcwidth`, because the stdlib segments
  graphemes but doesn't measure terminal cells.
- Self-referential demo: the deck rendering that string is the code under discussion.

### 2. Startup and imports

#### Lazy imports, PEP 810 (core)
- Syntax: `lazy import x`, `lazy from x import y`. Module scope only.
- Show `sys.lazy_modules` and the proxy repr `<lazy_import 'json'>`.
- Startup demo, run with hyperfine: a fake CLI that eagerly imports asyncio,
  sqlite3, email, http.client, etc. but only prints `--version`. Observed: eager
  84–93 ms, lazy 13–16 ms, bare interpreter 9 ms. `-X importtime` shows 215 vs 25 imports.
- The global switch: run the _unmodified_ eager file with `-X lazy_imports=all` (10 ms).
  `PYTHON_LAZY_IMPORTS` and `sys.set_lazy_imports` do the same.
  `sys.set_lazy_imports_filter` decides per import.
- Failure mode: a typo in a lazy import surfaces at first use, with a chained
  traceback pointing at both lines. Show it.
- Gotchas worth a line each:
  - imports inside `try` stay eager even in `all` mode, which is right for optional deps
  - import-time side effects (plugin registration) break under laziness
  - `__lazy_modules__` is the 3.14-compatible spelling
- Framing: mostly a CLI win, but the global switch makes it a one-flag experiment
  for any app.
- Dogfood: the deck itself can `lazy import` its heavy demo dependencies (numpy).

#### `.start` files, PEP 829 (std)
- The problem: a `.pth` line beginning with `import` is `exec()`ed on _every_
  interpreter start, whether or not the package is used, and it's hard to audit.
- The new format: `<name>.start` lists `pkg.mod:callable` entry points. A `.start`
  with a matching basename suppresses that `.pth`'s import lines.
- Live demo with two throwaway venvs:
  - a `.pth` alone runs its code
  - adding a `.start` makes the `.pth` import line go silent; `-v` explains why
  - 3.14 ignores `.start`
- Timeline: import lines still run through 3.17 (warning only under `-v`), are
  ignored from 3.18, and warn in 3.20.
- Be precise about motivation. The SC acceptance says it narrows one vector,
  supply-chain `exec()` via `.pth`. It doesn't stop a malicious package running code
  at startup; the gain is that startup code becomes an inspectable entry point. The
  PEP landed a week after the litellm `.pth` compromise but doesn't cite it, and
  people in the thread disputed that `.pth` is a common attack vector. Present the
  litellm link as timing context only. Sources are under References.

### 3. Concurrency

#### `TaskGroup.cancel()` (core)
- It cancels the children and the body, and the `async with` exits _without_
  raising `CancelledError`.
- Example 1, first-mirror-wins: the first successful fetch calls `tg.cancel()`.
  Observed: returns `('eu', ...)` in 0.10 s.
- Example 2: `loop.add_signal_handler(SIGTERM, tg.cancel)` for clean shutdown.
- Before/after: the 3.14 version needs a private `_Done` exception plus `except* _Done`.
  Show both, run both.

#### Iterator synchronization (core)
- Sharing one generator across threads was never safe. Run the unsafe demo, 4 threads
  on one iterator, on each build:
  - Generator, any build: `ValueError: generator already executing`. Three
    workers die and one does all the work.
  - Hand-written `__next__` on a free-threaded build: silently hands out
    duplicates (observed 540k dupes in 1.5M items on 3.14t). The 3.15t build does this too.
- Old safe patterns (both correct): a lock-wrapping iterator class, or a feeder
  thread pushing into a `queue.Queue` with a stop marker.
- New: `threading.serialize_iterator(it)`, `@threading.synchronized_iterator`, and
  `threading.concurrent_tee(it, n)` (every consumer sees every item).
- Honest caveat: production stays serial, since the lock is held across
  `__next__`. Only consumer work runs in parallel.
- Needs 3.14t and 3.15t interpreters for the free-threaded half.

### 4. Typing

Run all checkers live from the slide: mypy, pyright and ty, as one key each or one
key for all three. Tool versions observed: mypy 2.4.0, pyright 1.1.414, ty 0.0.87.

#### Sentinels, PEP 661 (core)
- The runtime: builtin `sentinel("MISSING")`.
  - repr is the name, always truthy, identity-equal only.
  - `copy`/`deepcopy` return the same object.
  - pickles by module and name.
  - can't be subclassed.
- The real story is typing. A four-slide matrix,
  all running the same `greet(name=MISSING)` function:

  | Approach | Checker | Narrowing | `greet(42)` caught |
  |---|---|---|---|
  | `MISSING: Final = object()`, `str \| object` | mypy, pyright, ty (on 3.14) | broken; all report `"object" has no attribute "upper"` | no; the annotation is just `object` |
  | enum workaround, `str \| Literal[_Missing.MISSING]` | all three (on 3.14) | works | yes |
  | `sentinel`, `str \| MISSING` | mypy 2.4.0 (on 3.15) | works | yes |
  | `sentinel`, `str \| MISSING` | mypy 2.3.1 | `not valid as a type`, reveals `Any` | |

  The last row is old mypy against new Python: support arrived in mypy 2.4.0 and pyright 1.1.410.
- Bridge for 3.14 users: `typing_extensions.Sentinel`. Use the capital S; pyright's
  typeshed lacks the lowercase alias.
- Aside: only pyright enforces that the sentinel's name matches the variable.

#### TypeForm, PEP 747 (core)
- The [Why not `type[C]`](https://peps.python.org/pep-0747/#why-not-type-c) argument
  in one slide: `type[T]` only accepts class objects, so `int | None`,
  `Literal["GET", "POST"]` and protocols are rejected.
- Demo: the same `validate(value, typ)` function (think `TypeAdapter`) with
  `type[T]` and with `TypeForm[T]`. Run all three checkers. Observed:
  - `type[T]`: errors everywhere, and reveals of `Never` or `Unknown`.
  - `TypeForm[T]`: `int | None` and `Literal['GET', 'POST']` inferred correctly.

#### TypedDict, PEP 728 (std)
- Lean into the "I kinda hate TypedDict" angle: it keeps getting better anyway, and
  LangChain state is the motivating day job.
- `closed=True`:
  - rejects extra keys and structural "wider" assignment
  - lets `"isbn" in item` narrow a union soundly
- `extra_items=str` types the leftover keys (an HTTP headers example).
- Checker gap, shown live: mypy 2.4 doesn't support `extra_items` and rejects valid
  code. pyright and ty get it right.

#### `@disjoint_base`, PEP 800 (cut-first)
- Practical example with no decorator: two `@dataclass(slots=True)` classes.
  - At runtime `class ColoredPoint(Point, Color)` raises a layout-conflict `TypeError`.
  - Checkers now know, so `isinstance(p, Color)` inside `def draw(p: Point)` is unreachable.
  - Without `slots=True` it's reachable, which makes a good control slide.
- Support varies: mypy (with `--warn-unreachable`) and ty narrow, while pyright
  only checks the class definition.
- The decorator itself is mostly for stub authors.

Typing lightning round (cut-first): `TypeVarTuple` variance, the Protocol
`isinstance` deprecation warning, and the removals.

### 5. Performance

#### Tachyon, PEP 799 (core, the centerpiece, about a third of the talk)

1. Why the name? Physicist digression: a tachyon is a hypothetical
   faster-than-light particle ("tachy" is Greek for swift). The PEP calls it an
   internal codename and gives no reason.
2. Why sampling? Production performance problems show up in situ and can't be
   deduced ahead of time, so measure before optimizing.
   - Overhead demo: run a CPU benchmark plain, under `profiling.tracing` (cProfile's
     new home), and under `profiling.sampling`, and show the three timings live.
     Don't assert a number before measuring it on the presenting VM.
3. Why in CPython? py-spy and austin read interpreter memory from outside, so each
   new CPython release needs them to catch up.
   - Tachyon uses CPython's own `_remote_debugging` (the PEP 768 machinery from 3.14),
     so it supports each release on day one.
   - The flip side is a strict coupling: profiler and target must be the same minor
     version. Show the error message from attaching 3.15 to a 3.14 process.
   - Check py-spy/austin's 3.15 support status close to the talk date and state it
     accurately.
4. Profile the running talk. The headline demo, built on counterweight's embedded
   terminals ([#423](https://github.com/JoshKarpel/counterweight/pull/423)).
   See [The Tachyon stage](#the-tachyon-stage) below for how it's built.
   - The deck runs Tachyon's live TUI _inside itself_, attached to its own PID.
   - Workload keys make the deck do expensive things at a few intensities
     (light, medium, heavy), and the profiler shows each one as it happens:

     | Key | Workload | What to point at |
     |---|---|---|
     | `c` | pure-Python CPU (nbody) in a worker thread | the hot function and per-line attribution |
     | `C` | the same on the event loop, bounded to about 2 s | the deck freezes; the profile explains it after |
     | `n` | numpy matmul (`lazy import numpy`) | compiled code appears as `<native>` frames |
     | `i` | blocking file/sleep I/O in a thread | wall vs cpu mode: idle time vanishes in cpu mode |
     | `a` | a fan of asyncio tasks | `--async-aware` reconstructs task trees |
     | `g` | garbage-cycle churn | `<GC>` frames, which links to the GC story below |

   - `m` cycles the profiler's mode (wall, cpu, gil, async-aware) by restarting it
     with new flags. gil mode pairs with `c`: the worker thread holds the GIL while
     the render loop waits for it, which is also why the deck stutters.
   - The mirror moment: drawing the profiler's screen is itself work the deck
     does (the #423 plan measures 3 to 10 ms per emulator snapshot of a busy colored
     screen), so it may show up in the profile it's drawing. Check it on the real
     deck before building a beat around it.
   - The presenter can hand the keyboard to the pane and use Tachyon's own keys
     (`s` sort, `t` mode, `x` trends, arrows for threads, `h` help), then take it
     back with a prefix key.
5. Tachyon's own flamegraph (cut-first). A key runs
   `attach -d 10 --flamegraph -o out/deck-flamegraph.html` against the deck in a
   second embedded pane while a workload runs. The output is a self-contained HTML
   file (observed: about 630 KB, with no external scripts).
   - The deck serves `out/` with
     `python -m http.server --bind 127.0.0.1 8315 --directory out` and prints
     `https://<vm>.exe.xyz:8315/deck-flamegraph.html`. zellij web's browser client
     bundles xterm.js's link addon, so clicking the URL opens it in a new tab.
   - It stays private: exe.dev proxies ports 3000 to 9999 behind the same exe.dev
     login as zellij web. Opening the page is an ordinary top-level navigation, so
     no CORS or public port is involved.
   - Other formats get one line each: `--gecko` for profiler.firefox.com, `--heatmap`,
     and `--collapsed` for any flamegraph tool.
6. Also: `profiling.sampling dump <pid>` prints a one-shot stack, which is how you'd
   ask a hung production process what it's doing. Run it against the deck in a pane
   while a threaded workload is busy. Not during `C`: a frozen deck can't draw the answer.
   - `--diff-flamegraph` compares a baseline with the current run.
   - `heatmap` is another output format.
   - Sampling-rate claims depend on hardware: the VM topped out near 120k samples/s,
     not the documented 1 MHz, so don't quote 1 MHz on stage.

#### Frame pointers, PEP 831 (std, right after Tachyon)
- Plain explanation: with frame pointers, every C function saves its caller's frame
  address in a register (`rbp`), forming a linked list on the stack. `perf`, eBPF
  and debuggers walk that list cheaply.
  - Without frame pointers, unwinding needs DWARF tables, and eBPF can't use those at all.
  - Compilers dropped frame pointers to free a register. That mattered on 32-bit x86;
    the PEP measures 1.5–2% on x86-64.
- Why it matters here: Tachyon's `--native` only inserts `<native>` placeholders. Real
  C-level stacks come from perf/eBPF, which need frame pointers _everywhere_. One
  extension built without them breaks unwinding for the whole process, and 3.15
  bakes the flags into `sysconfig`, so extensions inherit them.
- The naive demo doesn't work. On uv's builds, 3.14 already has frame pointers
  (python-build-standalone turned them on in early 2026), and pure-Python stacks
  unwind fine even on Ubuntu's 3.12. The demo that works:
  - A tiny C extension that calls back into Python, built twice (`-fno-omit-frame-pointer`
    vs `-fomit-frame-pointer`), run under `perf record --call-graph fp -- python -X perf`.
  - Observed: 96.9% of stacks reach `_start` with frame pointers, and 4.7% without.
    The Python caller above the extension disappears entirely.
  - Show it as two flamegraphs or two `perf script` excerpts.
  - Run it live. `perf` works on the presenting VM without sudo (user-space
    sampling, `perf_event_paranoid` 2), and the probe above ran there.

#### JIT (std)
- What changed: a tracing frontend, register allocation, and more constant
  propagation and refcount elimination. The whatsnew cites 7–8% geomean on x86-64
  Linux and 11–12% on AArch64 macOS, still experimental.
- uv builds ship it compiled-in but off (`yes-off`). `PYTHON_JIT=1` turns it on, and
  `sys._jit.is_enabled()` proves it.
- Live demo: an nbody/float loop, 3.14 vs 3.15 × JIT off/on, under hyperfine.
  Observed about 1.5x for 3.15+JIT, while the 3.14 JIT was flat or slower. The VM
  is noisy, so use hyperfine's warmup and runs rather than one shot.

#### base64 (cut-first, could join the lightning round)
- Encode is about 2.5–3.4x faster and decode about 3.4x (observed, 5 MB). b32/b85
  were rewritten in C (58–140x observed).
- LLM angle: a JSON request body with a 5 MB base64 PDF went from about 23 to about
  15 ms. Real, but small next to network latency, so say so.
- Behavior change worth a warning: `urlsafe_b64decode(b"aGk")` no longer raises on
  missing padding. Pass `padded=True` for the old strictness.

#### The GC story (std)
- Incremental GC:
  - landed for 3.13 and was rolled back before 3.13.0
  - shipped in 3.14.0
  - production memory-growth reports followed
  - the SC-backed revert came in 3.14.5 _and_ 3.15 (announced 2026-04-16)
- 3.15 ships the generational GC. Reintroducing incremental GC now needs a PEP.
- Live demo: the same cycle-churn script across 3.13, 3.14.4, 3.14.7 and 3.15.
  Observed peak RSS was 65 / 233 / 65 / 66 MiB.
  - `gc.get_threshold()` (`(2000, 10, 0)` on the incremental builds) is a one-line
    test for which collector a 3.14.x has.
  - Caveat to say aloud: this workload reproduces the memory complaint but not the
    incremental GC's pause benefit, so it isn't a general verdict.
- Bonus: 3.15 adds `candidates` and `duration` to `gc.get_stats()`.

### 6. Lightning round (core, one slide or a rapid sequence)

Each item gets one runnable line where possible:

- "Did you mean" hints from other languages: `[1,2].push(3)` → `.append`,
  `'hi'.toUpperCase()` → `.upper`, and nested `container.area` → `.inner.area`.
- UTF-8 by default (PEP 686).
- `pprint(..., expand=True)` gives JSON-style output.
- `@contextmanager` on a generator function now holds across the whole iteration.
- tomllib supports TOML 1.1.
- `math.integer`.
- `-W` accepts regexes.
- `http.server -H`.
- `timeit --target-time`.
- argparse suggests fixes for typos.
- More colored CLIs.
- `re.prefixmatch`.

### 7. Closing (core)

- The thoroughness observation, with the examples collected along the way, and the
  open question about agents.
- Links: the whatsnew, the PEPs, and this repo.

## Deck architecture

### Stack
- Python: 3.15, requires-python `>=3.15`. Pin `.python-version` to 3.15.0 final
  once python-build-standalone publishes it. rc2 has a Tachyon bug (gh-154335: pstats
  output ignores `NO_COLOR`) that rc3 fixes.
- counterweight: a git source on `main` until the next release, then the release:

  ```toml
  [tool.uv.sources]
  counterweight = { git = "https://github.com/JoshKarpel/counterweight", branch = "main" }
  ```

  - `uv.lock` pins the exact commit, and `uv lock --upgrade-package counterweight`
    moves it forward. So a counterweight change reaches the deck only when we
    choose to take it.
  - The Tachyon stage needs
    [#423](https://github.com/JoshKarpel/counterweight/pull/423) (`Canvas`, the
    phase 2 framework fixes, and `use_terminal`) to be on `main`. Everything else
    works on today's `main`.
  - #423 brings in `pyghostty`, which bundles a prebuilt, pre-1.0 `libghostty-vt`.
    That's a supply-chain cost the deck inherits, not one it chooses.
  - counterweight already requires 3.15, and imports and renders headless on rc2.
    Pygments 2.21 already lexes `lazy`, `sentinel` and `frozendict`.
- Demo tools:
  - mypy, pyright and ty as a pinned uv dependency group.
  - The deliberately old mypy 2.3.1, run via `uvx --from mypy==2.3.1`, since it
    exists only to show the before state.
  - hyperfine via `mise.toml`.
- Interpreters needed: 3.15, 3.14 (current), 3.14.4 (incremental-GC era),
  3.13, 3.14t and 3.15t.

### Layout
```text
src/whats_new/
  __main__.py        app entry: root component, navigation, export
  deck.py            SLIDES = (*OPENING, *SMALL_THINGS, ..., *CLOSING)
  sections/          one module per running-order section, each exporting a tuple of slides
  components/        title card, footer, code_example, run_pane, split layouts
  runs.py            Run values, interpreter resolution
  tachyon.py         the Tachyon stage: profiler pane, modes, flamegraph server
  workloads.py       in-process workloads the Tachyon stage triggers
examples/            every snippet shown on screen, as real files
  frozendict_default.py, json_immutable.py, sentinel_naive.py, ...
demos/frame_pointers/  churn.c + build script
tests/
```

### Design decisions

- Examples are files, not strings. Each on-screen snippet is a real `.py` file
  that the slide reads and highlights with `counterweight.highlighting.code_block`.
  The same file runs on 3.14 to show the `SyntaxError` and is fed to the type
  checkers, so display and execution can't drift. (The reference talk used
  `inspect.getsource`, which can't hold 3.15-only syntax that must also be shown
  failing on 3.14.)
- A `Run` is a value. Something like
  `Run(label="3.14", argv=(...), env=frozendict(...))`. Slides declare a tuple of
  runs, bound to keys `1`–`9`, and a shared `run_pane` component shows the output.
  - Once #423 lands, `run_pane` runs each `Run` in an embedded terminal. Output
    keeps its color, which matters because 3.15 colors tracebacks, argparse, the
    REPL and more. The same widget can host a live `python3.15` REPL for the error
    hints and colored REPL in the lightning round.
  - Until then, `run_pane` streams pipe output as plain text with `NO_COLOR` set.
    It uses the pattern from counterweight's `examples/chat.py`: a key bumps a run
    ID in state, and an effect keyed on that ID runs `asyncio.create_subprocess_exec`
    and appends lines to a pane styled `overflow_y_scroll | stick_to_end_y`. A
    headless probe confirmed this works end to end.
  - Slides only see `run_pane(runs)`, so swapping the inside changes no slide.
- Resolve interpreters once, at startup. Resolve each interpreter path
  (`uv python find 3.14`, etc.) into a typed `Interpreters` value and fail loudly if
  one is missing. That turns a missing interpreter into a startup error, not a dead
  key on stage.
- Dogfood 3.15 in the deck's own code where it fits naturally:
  - `frozendict` for `Run.env`
  - `sentinel` for "not yet run" output state
  - `lazy import` for numpy and other demo-only modules
  - `TaskGroup.cancel()` for tearing down a run when leaving a slide

  Worth one aside on stage.
- Keys, carried over from the reference talk where possible:
  - Left/Right: navigate.
  - Space: reveal.
  - `1`–`9`: run.
  - `r`: reset the current slide, by remounting via `.with_key`.
  - A clock toggle and a content-width check against the projector. The reference
    talk put these on F1 and F2, but in a browser F1 opens help, so they move to
    plain letter keys.
  - Slide-specific keys on Tachyon slides only.

  See [Presenting over zellij web](#presenting-over-zellij-web) for which keys the
  browser and zellij take first.
- Persist the slide index to a temp file, as the reference talk does, so a
  `watchfiles` restart lands on the same slide.
- Export: keep the reference talk's headless autopilot to SVG/HTML for a
  shareable copy. Run panes show their pre-run state there.

### The Tachyon stage

The Tachyon demo is one slide whose steps advance with Space, so the profiler pane
survives the whole section. A separate slide per step would unmount the pane on
every navigation and restart the profiler.

- Layout: the profiler pane takes the full width at the bottom, and a strip on top
  holds the current talking point and which workload is running.
  - Tachyon's live TUI needs at least 60x12. Below that it shows a "Terminal too
    small!" screen (observed).
  - At the 90-column projector width, a side-by-side split would leave about 30
    columns for the slide, so stack the panes instead.
  - The `file:line` column truncates long paths, so run the deck from a short path.
- The pane runs `use_terminal` with
  `[sys.executable, "-m", "profiling.sampling", "attach", "--live", "-a", str(os.getpid())]`.
  - `sys.executable` matters: profiler and target must be the same minor version.
  - `-a` samples every thread, so workloads in worker threads show up.
  - The mode lives in state. Changing it changes the pane's argv and key, which
    remounts the pane and restarts the profiler. Leaving the slide unmounts the
    pane, which hangs up the PTY and ends the profiler.
- Focus: keys go to the deck by default, so workload keys work.
  - A key hands focus to the pane, and the presenter drives Tachyon's own keys.
  - A prefix key (Ctrl+B, as in #423's multiplexer example) takes it back.
  - #423's phase 2 covers both halves: focusing a pane that mounts in the same
    update, and reading modal prefix state synchronously.
  - Raw input mode isn't needed, since Ctrl+C never has to reach the profiler.
- ptrace: the profiler is the deck's _child_, attaching to its parent.
  - The presenting VM has no Yama LSM, so the attach works, as observed.
  - Under Yama's `ptrace_scope` 1 (stock Ubuntu) it would be refused, because
    scope 1 only lets a process trace its own descendants. If the deck ever moves
    to such a machine, the deck can opt in with `prctl(PR_SET_PTRACER, ...)` before
    spawning the profiler.
- Workloads (`workloads.py`) run off the event loop, so the deck keeps drawing.
  - They still share the GIL with the render loop. That's the point of the gil-mode beat.
  - Each one ends on its own after a few seconds. A key starts it; nothing has to
    stop it.
  - `C` deliberately runs on the event loop and freezes the deck. The pane can't
    redraw during the freeze, so the profile only becomes visible afterwards.
  - While the deck isn't reading the PTY, Tachyon's screen writes back up. Probe
    whether a full PTY buffer stalls Tachyon's sampling, not only its drawing. If
    it does, keep `C` short enough that the buffer never fills, or cut it.

### Presenting over zellij web

The deck runs on this exe.dev VM (2 vCPU) inside zellij, and the audience sees a
browser showing zellij web.

- Keys pass through two layers before the deck sees them.
  - zellij's normal mode takes Ctrl+B, Ctrl+G, Ctrl+P, Ctrl+T, Ctrl+N, Ctrl+H,
    Ctrl+S, Ctrl+O and Ctrl+Q, so the Tachyon stage's Ctrl+B prefix wouldn't reach
    the deck. Present in locked mode (Ctrl+G), where zellij passes every key through.
  - The browser keeps some keys whatever zellij does: F1 (help), F5 (reload), F11,
    and Ctrl+W/T/N. The deck binds none of them.
  - `just rehearse` presses every deck key through zellij web and confirms the deck
    received it.
- The screen size is the browser window and its font size. Fix both before the
  talk and check the content width with the deck's width key.
- Terminal rendering is xterm.js, not a native terminal. The grapheme slide depends
  on how it draws ZWJ sequences, flags and skin tones. Check those, because a
  broken family emoji on the "graphemes are hard" slide would be on-message, but
  only if it's intended.
- Clickable links come from xterm.js's link addon, which zellij web bundles (found
  in the zellij 0.45.1 binary). That's untested end to end.
- The network sits between the deck and the projector. The live Tachyon pane
  redraws constantly, so rehearse on the venue network, and have a phone hotspot.
- 2 vCPUs are shared by the deck, the profiler, the workloads and the zellij server.
  - Timings will be noisy. Phrase results as "on this VM, right now".
  - The free-threaded duplicate-items demo did reproduce here.

### Counterweight gaps likely to matter
- No controls from effects (`plans/react-features.md` step 2, not started). An
  effect can't `Quit()` or ring the bell. Probably fine.
- No context or `use_reducer`. Pass the slide index and flags down as props.
- No built-in timer or footer. `use_clock` makes these easy.
- Rendering cost: the embedded pane costs real frame time (the emulator snapshot),
  on top of whatever workload is running. Watch the frame rate on the Tachyon stage
  as the audience sees it, through zellij web.

## Verification

- Example check: a test (`just check-examples` or pytest) runs every `Run`
  declared on every slide and asserts its expected outcome.
  - The expected outcome is an exit code plus a key substring:
    `SyntaxError` on 3.14, `Success: no issues found` for mypy, and so on.
  - Without this, an interpreter or checker bump silently breaks a slide.
  - Assert against the run's own output, not the rendered deck, which embeds the source.
- Smoke test: a headless autopilot walks every slide, catching render crashes
  and slides wider than the projector width.
- `just rehearse` checks the presenting setup before the talk. It scripts what
  it can:
  - every interpreter resolves
  - the embedded profiler attaches to the deck's PID
  - `perf` works
  - numpy has a 3.15 wheel installed

  Then it prints a manual checklist for the browser side, run over zellij web
  from the presenting browser:
  - every deck key arrives through the browser and zellij's locked mode
  - the flamegraph URL opens from a click
  - the grapheme slide renders as intended

  The intent is to find problems the day before, not to keep a canned-output
  fallback path in the deck.

## Risks

- The venue network. Everything the audience sees crosses it. Rehearse there,
  and have a hotspot.
- #423 timing. The Tachyon stage and colored run panes wait on #423 reaching
  `main`. Build everything else first, so a late #423 delays only one section.
- numpy wheels for 3.15. Confirm cp315 wheels exist before relying on the
  compiled-extension workload.
- Noisy timings (JIT, base64, lazy imports, profiler overhead) on a shared
  2-vCPU VM. Use hyperfine with warmup, and phrase results as "on this VM, right now".
- Free-threaded builds are needed for the duplicate-items demo. Pin
  3.14t and 3.15t.
- 3.14.4 specifically is needed for the GC demo, since later 3.14 patches have the revert.

## Decisions

- Length: about an hour of material with questions during the talk, and 90 minutes
  at most.
- Venue setup: present from this VM over zellij web.
- Color: the embed (#423) renders program output with its colors. If that falls
  through, the deck stays plain text and color becomes later work.
- No speedscope. The point is Tachyon, so the browser step (if kept) shows
  Tachyon's own HTML flamegraph.

## Build order

1. Scaffold: pyproject with counterweight as a git source on `main`, `mise.toml`,
   `.python-version`, `justfile` (`present`, `watch`, `check-examples`,
   `rehearse`, `export`).
2. Deck skeleton: navigation, footer, title cards, slide-index persistence, export.
3. `code_example` + `Run` + `run_pane`, built and proven on the frozendict and json
   slides, plus `check-examples`.
4. Sections 1–4 in order: mostly content once step 3 exists.
5. Tachyon, in two halves:
   - Now: `workloads.py` and the flamegraph link. Run the profiler from a plain
     zellij pane against the deck while building these.
   - Once #423 is on `main`: the Tachyon stage, then swap `run_pane` to embedded
     terminals. Budget the most time here.
6. Frame pointers, JIT, GC and base64 demos.
7. Lightning round, closing, and the thoroughness slide.
8. `rehearse` over zellij web from the presenting browser, then the projector width pass.

## References

- [What's New in Python 3.15](https://docs.python.org/3/whatsnew/3.15.html)
- PEPs: [661](https://peps.python.org/pep-0661/) sentinels,
  [728](https://peps.python.org/pep-0728/) closed TypedDict,
  [747](https://peps.python.org/pep-0747/) TypeForm,
  [798](https://peps.python.org/pep-0798/) unpacking in comprehensions,
  [799](https://peps.python.org/pep-0799/) profiling package,
  [800](https://peps.python.org/pep-0800/) disjoint bases,
  [810](https://peps.python.org/pep-0810/) lazy imports,
  [814](https://peps.python.org/pep-0814/) frozendict,
  [829](https://peps.python.org/pep-0829/) startup configuration files,
  [831](https://peps.python.org/pep-0831/) frame pointers
- Tachyon: [library docs](https://docs.python.org/3.15/library/profiling.sampling.html),
  [Talk Python guide](https://talkpython.fm/guides/565/tachyon-python-3.15s-built-in-sampling-profiler),
  [PyCon US 2026 talk](https://us.pycon.org/2026/schedule/presentation/31/)
- GC:
  [the 3.13 rollback](https://discuss.python.org/t/incremental-gc-and-pushing-back-the-3-13-0-release/65285),
  [the 3.14/3.15 revert](https://discuss.python.org/t/reverting-the-incremental-gc-in-python-3-14-and-3-15/107014),
  [3.14.5 release](https://discuss.python.org/t/python-3-14-5-is-here-with-a-new-old-garbage-collector/107304)
- [PEP 829 discussion](https://discuss.python.org/t/pep-829-structured-startup-configuration-files/106789)
- [litellm `.pth` compromise](https://futuresearch.ai/blog/litellm-pypi-supply-chain-attack/)
  (timing context only)
- [counterweight grapheme work](https://github.com/JoshKarpel/counterweight/issues/392)
- Prior art: [py-spy](https://github.com/benfred/py-spy),
  [austin](https://github.com/P403n1x87/austin)
- [Reference talk](https://github.com/JoshKarpel/python-concurrency-and-parallelism)
