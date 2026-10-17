# What's New in Python 3.15: Talk Plan

Artifact: https://claude.ai/code/artifact/661c4edd-7424-4218-8c92-58912482fd24

This plan covers the talk's content, its running order, and how to build it as an
executable counterweight deck. It doesn't contain the slide text itself. The model
is the
[python-concurrency-and-parallelism](https://github.com/JoshKarpel/python-concurrency-and-parallelism)
talk: slides are counterweight components, and the code on screen is the code that runs.

The source material is
[What's New in Python 3.15](https://docs.python.org/3.15/whatsnew/3.15.html).

Everything marked "observed" below was run on CPython 3.15 (rc2, rc3 or 3.15.0 final)
and 3.14.7 on a 2-vCPU Linux VM. Probe scripts from that research live (temporarily) in the session
scratchpad. The useful ones get promoted into `examples/` during the build.

## The pitch

A whirlwind tour of how Python is getting better, for working Python programmers
(not C-extension authors). There's no single theme. The deck is executable: show a
snippet, press a key, and see its output, mypy's verdict, or a timing, run live on
3.15. Where behavior changed, or the syntax is new, another key runs it on 3.14.
An addition gets no 3.14 run: all 3.14 can say is that it doesn't exist.

Prefer a diagram to text wherever a picture can carry the point: a mechanism, a
before/after, a fan-out, a timeline. Timing comparisons usually get a bar chart
beside the raw numbers.
The running order below lists the diagrams each item wants, and
[Diagrams](#diagrams) covers how they're built.

### Running observation: the features are unusually thorough

Several features arrive as complete toolkits rather than a single function:

- threading gains `serialize_iterator`, `synchronized_iterator` and `concurrent_tee`.
- unicodedata gains `iter_graphemes` plus five related property functions.
- base64 gains C rewrites plus `padded=`, `canonical=`, `wrapcol=` and `alphabet=`.
- lazy imports come with syntax, `-X`/env/`sys` switches, a filter hook,
  and a 3.14-compatible `__lazy_modules__`.
- Tachyon has a dozen output formats, a live TUI, async awareness, attach, dump and replay.
- frozendict arrives with the stdlib already updated around it: copy, decimal, json,
  marshal, pickle, pprint, plistlib and ElementTree accept it, as do `eval`/`exec`
  globals, `type()` and `str.maketrans`.
- "More color" reaches about 20 command-line interfaces, from argparse and
  `python --help` to sqlite3, timeit, pickletools and unraisable exceptions.

Collect these as the talk goes, and close with them. Whether coding agents make this
kind of completeness cheaper is a question to ask aloud, not one to put on the slide:
there's no evidence here about how any of these were written.

## Running order

The talk aims for about an hour, with questions taken during it, and can stretch
to 90 minutes. Items are tagged **core** (always in), **std** (in unless questions
run long) or **cut-first** (the first to go, or folded into the lightning round).

| Section | Minutes |
|---|---|
| 0. Opening | 3 |
| 1. Small things you'll use tomorrow | 12 |
| 2. Startup and imports | 7 |
| 3. Concurrency | 9 |
| 4. Typing | 8 |
| 5. Performance (Tachyon about 15 of it) | 23 |
| 6. Before you upgrade | 3 |
| 7. Lightning round | 6 |
| 8. Closing | 2 |
| Material | 73 |

Every item gets built, cut-first ones included, and the cutting happens while
practicing the talk. So the tags and minutes are first guesses, to be revised
once rehearsals show what each item really takes and how well it lands. The
cut-first items are worth about 6 minutes, so getting back to about an hour
also means trimming some of the std items.

### 0. Opening (core)
- Title, who I am.
- Don't announce that the deck is a Python 3.15 program. The first run box gives
  it away, and the audience working that out is part of the fun.
- A quick glance at the 3.15 changelog's size, to set up the "thorough" observation.
- Disclose that the deck was built with help from Claude Code: a
  `✻ built with help from Claude Code` line under the title, in Claude Code's
  orange. The Thanks slide repeats it beside Claude Code's mascot.

### 1. Small things you'll use tomorrow

#### frozendict, PEP 814 (core)
- The builtin immutable mapping, set beside `frozenset`. Observed behavior:
  - `frozendict(x=1) == {"x": 1}` is True, mirroring `frozenset({1}) == {1}`.
  - It is _not_ a dict subclass: `isinstance(fd, dict)` is False, so use `Mapping`.
  - Hashing is order-insensitive, and it is hashable only if all its values are.
  - `fd | {...}` returns a frozendict.
- Example: the mutable-default-argument footgun, shown first with a `dict` default
  that one call mutates for every later call, then fixed with
  `options=frozendict(...)` in a file shaped the same way.
- Example: `functools.cache` rejects a dict argument (`unhashable type: 'dict'`) and
  accepts a frozendict. The cached function prints `cache miss...` when it runs.
- The sad note: no literal syntax. The PEP defers it ("can be added later").
- Why not a subclass? The common first guess is that `frozendict` should subclass
  `dict`. That's backwards: `frozendict` has _fewer_ methods, so if anything `dict`
  would extend `frozendict`. And that fails too. Code holding a `frozendict` relies
  on it never changing and being hashable, and a `dict` standing in for one breaks
  both promises, which violates Liskov substitution. So neither subclasses the
  other, exactly as with `set` and `frozenset`.
- Diagram: the class hierarchy as the ABCs register it. `dict` sits under
  `MutableMapping` under `Mapping`, and `frozendict` directly under `Mapping`, level
  with `dict`. The sets mirror it: `set` under `MutableSet` under `Set`, `frozenset`
  directly under `Set`. Reveal the mappings, then the sets, then draw the tempting
  `frozendict → dict` edge and cross it out, then the reversed `dict → frozendict`
  edge and cross that out too. "Use `Mapping`" then reads as a consequence rather
  than a gotcha. The drawing keeps one size at every step, so a reveal moves nothing.
  The key to the box styles sits alone in the bottom right corner, away from the
  argument's text.

#### json `array_hook` (core, paired with frozendict)
- New `array_hook=` on `load`, `loads` and `JSONDecoder`.
- Call it inline, with no wrapper function to spend rows on:
  `json.loads(s, object_pairs_hook=frozendict, array_hook=tuple)`.
- Show the result is deeply immutable and usable as a cache key, and that
  `json.dumps` writes it back out as the same JSON. Each print is an `f"{expr = }"`,
  so the output says which line is which.

#### Unpacking in comprehensions, PEP 798 (core)
- `[*row for row in rows]` replaces `list(chain.from_iterable(rows))`.
- `{**d for d in dicts}` merges dicts, last key wins.
- Async version: `[*page async for page in pages()]` flattens a paginated async API.
  The async examples get a slide each (pages, the `TypeError`, the nested form), so
  each run executes the code on screen.
- Correction to the original premise: this does _not_ replace an async
  `chain`. The inner value must be a _sync_ iterable, so
  `[*src async for src in sources()]` over async generators raises
  `TypeError: Value after * must be an iterable, not async_generator`. It flattens
  an async stream of sync batches. Show that error on purpose, then show what
  flattening async generators actually takes:

  ```python
  async def flatten(sources):
      async for source in sources:
          async for item in source:
              yield item
  ```

  The one-line form is a nested async comprehension,
  `[x async for src in sources() async for x in src]`, which predates 3.15.
  Observed: both give the same list on 3.15.
- On 3.14 this is a `SyntaxError: iterable unpacking cannot be used in comprehension`.

#### `Counter.__xor__` (std)
- Gives `|c[x] - d[x]|` per key, i.e. `(c - d) + (d - c)`.
- The result is unsigned, so it fits a question where the direction doesn't
  matter. A diff like expected vs on-shelf inventory doesn't fit: it needs to know
  which side is short, which `c - d` and `d - c` already answer separately.
- Example: how many letters must be deleted to make two words anagrams?
  `(Counter(a) ^ Counter(b)).total()`. A deletion from either word counts the same,
  so the missing sign is exactly right. Observed: `"cde"` and `"abc"` give 4.

#### `bytearray.take_bytes` (std)
- Take the whole buffer as `bytes` without a copy; `bytes(ba)` always copied.
- One slide: `bytes` and `bytearray.take_bytes` over the same 50 MB buffer, with
  `tracemalloc` peaks. Each prints the buffer's length before and after (the
  copy leaves it full, `take_bytes` empties it), and the two results are
  asserted equal. Observed: the copy doubles peak memory and `take_bytes`
  doesn't.
- Diagram: memory before and after. `bytes(ba)` leaves two buffers; `take_bytes`
  hands the one buffer over and leaves the bytearray empty.

#### `re.prefixmatch` (cut-first, lightning round)
- `match` is soft-deprecated: no warnings, no removal. `re.match is re.prefixmatch` at module level.
- The rationale is that "match" means "search" in most other regex engines.

#### `unicodedata.iter_graphemes` (std)
- Background first, since much of the audience won't have thought about Unicode or
  text rendering: a "Text, in layers" diagram, revealed a layer at a time. "café"
  spelled with a combining accent is 4 graphemes (what a reader counts), 5 code
  points (what a `str` holds and `len()` counts), and 6 UTF-8 bytes (what a file or
  socket holds). Then what a font does (draws a grapheme as one glyph) and a terminal
  (gives it cells, by `wcwidth`), and that `é` has a one-code-point spelling NFC
  picks while many graphemes have none.
- `"Spinal Tap"` with an umlaut on its n is 11 code points but 10 graphemes: the n̈
  is `n` and U+0308 COMBINING DIAERESIS, with no precomposed form, so NFC can't fold
  it away.
- Reversing it naively moves the umlaut onto the `a`. Reversing by grapheme gets it
  right.
- No combining mark ever reaches the terminal. zellij 0.45.1 drops every zero-width
  code point, combining marks included
  ([zellij-org/zellij#5500](https://github.com/zellij-org/zellij/pull/5500), open,
  fixes it), so the n̈ showed as a plain n on stage. The example spells the mark
  `\N{COMBINING DIAERESIS}` and prints with `!a`, so the output reads
  `'paT la\u0308nipS'`, and the diagrams draw a mark as its spacing look-alike
  (`¨`, `´`). zellij dropping the marks becomes a talking point: segmentation is hard.
- Personal hook: counterweight uses it
  ([#392](https://github.com/JoshKarpel/counterweight/issues/392), PR #398) for
  segmentation. Width still comes from `wcwidth`, because the stdlib segments
  graphemes but doesn't measure terminal cells.
- Diagram: the string's code points under grapheme brackets, with one bracket
  spanning the `n` and its combining diaeresis.

### 2. Startup and imports

#### Lazy imports, PEP 810 (core)
- Syntax: `lazy import x`, `lazy from x import y`. Module scope only.
- Show `sys.lazy_modules` and the proxy repr `<lazy_import 'json'>`. The proxy's type
  is `types.LazyImportType`.
- Startup demo, run with hyperfine: a fake CLI that eagerly imports asyncio,
  sqlite3, email, http.client, etc. but only prints `--version`. Observed: eager
  84–93 ms, lazy 13–16 ms, bare interpreter 9 ms. `-X importtime` shows 215 vs 25 imports.
- The global switch: run the _unmodified_ eager file with `-X lazy_imports=all` (10 ms).
  `PYTHON_LAZY_IMPORTS` and `sys.set_lazy_imports` do the same.
  `sys.set_lazy_imports_filter` decides per import.
- Failure mode: a typo in a lazy import surfaces at first use, with a chained
  traceback pointing at both lines. Show it. The example prints one line before the
  failing use, so the print and the whole traceback fit the run box together.
- Gotchas worth a line each:
  - `try` blocks go both ways. Writing `lazy import` inside one is a `SyntaxError`
    (observed: `lazy import not allowed inside try/except blocks`), and a plain
    import inside one stays eager even in `all` mode, which is right for optional
    deps.
  - `lazy from x import *` and lazy `__future__` imports are `SyntaxError`s too.
  - import-time side effects (plugin registration) break under laziness
  - `__lazy_modules__` is the 3.14-compatible spelling
  - The gotchas slide shows two examples side by side, each labeled ("left: lazy
    import inside try", "right: the 3.14-compatible spelling"), and its runs say
    which they run where: "left on 3.15", "right on 3.14", "right on 3.15".
- Framing: mostly a CLI win, but the global switch makes it a one-flag experiment
  for any app.
- Dogfood: the deck itself can `lazy import` its heavy demo dependencies (numpy).
- No diagrams. The live runs and their timings carry it.

#### `.start` files, PEP 829 (std)
- The problem: a `.pth` line beginning with `import` is `exec()`ed on _every_
  interpreter start, whether or not the package is used, and it's hard to audit.
- The new format: `<name>.start` lists `pkg.mod:callable` entry points. A `.start`
  with a matching basename suppresses that `.pth`'s import lines.
- Live demo with two throwaway venvs:
  - a `.pth` alone runs its code
  - adding a `.start` makes the `.pth` import line go silent; `-v` explains why
  - 3.14 ignores `.start`
- Diagram: `site.py`'s startup flow. A `.pth` import line goes to `exec()`; a
  `.start` with a matching basename suppresses it and calls a named entry point.
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
- Diagram: the task tree for first-mirror-wins, revealed in steps. Three fetches
  start, one finishes, its `tg.cancel()` cancels the other two, and the
  `async with` exits cleanly.

#### Iterator synchronization (core)
- Sharing one generator across threads was never safe. Run the unsafe demo, 4 threads
  on one iterator, on each build:
  - Generator, any build: `ValueError: generator already executing`. Three
    workers die and one does all the work.
  - Hand-written `__next__` on a free-threaded build: silently hands out
    duplicates (observed 540k dupes in 1.5M items on 3.14t). The 3.15t build does this too.
- Old safe patterns (both correct), side by side on one slide: a lock-wrapping
  iterator class, and a feeder thread pushing into a `queue.Queue` with a stop
  marker, which workers drain with `for item in iter(q.get, DONE)`.
- New: `threading.serialize_iterator(it)`, `@threading.synchronized_iterator`, and
  `threading.concurrent_tee(it, n)` (every consumer sees every item).
- Honest caveat: production stays serial, since the lock is held across
  `__next__`. Only consumer work runs in parallel.
- Needs 3.14t and 3.15t interpreters for the free-threaded half.
- Diagram: three fan-outs, one source and four threads each.
  - a bare generator: three threads die with `ValueError`
  - `serialize_iterator`: each item goes to exactly one thread
  - `concurrent_tee`: each item goes to every thread

  The difference between the last two is the one people will mix up.

#### Free-threading status (std, right after iterator synchronization)
- The previous item already runs on 3.15t, so this is the state of play rather
  than an introduction. Keep it to what changes for someone who installs
  packages, not someone who builds them.
- PEP 803's stable ABI for free-threaded builds (`abi3t`): a library can ship one
  wheel that works on free-threaded builds of 3.15 and later, instead of a
  `cp315t` wheel per release. Expect the packages you depend on to grow
  free-threaded wheels faster. meson-python, scikit-build-core and Maturin support it.
- The python.org macOS installer installs free-threading support by default.
- Raw memory allocations now use mimalloc, for better performance on
  free-threaded builds.
- Demo: `sys.abi_info`, new in 3.15, on both builds. Observed:
  `namespace(pointer_bits=64, free_threaded=False, ...)` on 3.15 and
  `free_threaded=True` on 3.15t, with `sys._is_gil_enabled()` True and False.
- Check how many popular packages ship free-threaded wheels close to the talk
  date, and state it as of that day.

### 4. Typing

Run mypy live from the slide, and say once, on the section's title card, that pyright
and ty agree unless a slide says otherwise. Three checkers' output on every run
crowded the box and repeated one verdict. Where they differ, the slide says so:
`extra_items` runs pyright beside mypy, since mypy rejects valid code there, and the
disjoint-bases slide notes that pyright and ty flag the class but don't narrow.
Tool versions observed: mypy 2.4.0, pyright 1.1.414, ty 0.0.87.

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

A possible frame for the section: 3.15 is an observability release. Tachyon
watches a running process, frame pointers let `perf` and eBPF walk native
stacks, the JIT publishes unwind information so GDB and `backtrace()` see
through JIT frames, `gc.get_stats()` reports `candidates` and `duration`, and
`faulthandler` gains `max_threads`. Each item below then answers "how do I see
what Python is doing?" from a different side. Decide in rehearsal whether the
frame earns a slide or just a sentence.

#### Tachyon, PEP 799 (core, the centerpiece, about a third of the talk)

1. Why the name? Physicist digression: a tachyon is a hypothetical
   faster-than-light particle ("tachy" is Greek for swift). The PEP calls it an
   internal codename and gives no reason.
2. Why sampling? Production performance problems show up in situ and can't be
   deduced ahead of time, so measure before optimizing.
   - Overhead demo, on its own slide with the program shown: `fib(32)`, timing itself,
     run plain, under `profiling.tracing` (cProfile's new home), and under
     `profiling.sampling run`, best of three each. The program reports its own time,
     because timing the whole command charges the sampler's start-up and report to
     it, and on a short program that made sampling look slower than tracing.
     Observed: 0.19 s plain, 1.33 s tracing, 0.20 s sampling.
   - Diagram: one timeline of a program's calls, drawn twice. Tracing puts a hook on
     every call and return. Sampling takes a stack snapshot at fixed intervals.
     A playhead runs along the calls on Space, and each row fires as it passes.
     Then a bar chart of the three overhead timings.
3. Why in CPython? py-spy and austin read interpreter memory from outside, so each
   new CPython release needs them to catch up.
   - Tachyon uses CPython's own `_remote_debugging` (the PEP 768 machinery from 3.14),
     so it supports each release on day one.
   - The flip side is a strict coupling: profiler and target must be the same minor
     version. Show the error message from attaching 3.15 to a 3.14 process.
   - Check py-spy/austin's 3.15 support status close to the talk date and state it
     accurately.
   - Diagram: the two architectures side by side. py-spy and austin read the
     target's memory from outside with struct layouts specific to each version.
     Tachyon reads it through `_remote_debugging`, which ships with the interpreter.
     The coupling becomes visible: the reader has to match the target's version.
4. Profile the running talk. The headline demo, built on counterweight's embedded
   terminals ([#423](https://github.com/JoshKarpel/counterweight/pull/423)).
   See [The Tachyon stage](#the-tachyon-stage) below for how it's built.
   - Diagram, shown before the live demo: the loop. The deck, labeled with its real
     PID, spawns the profiler as a child; the profiler's box holds the exact command
     the stage runs, built by the same function; the profiler attaches back to its
     parent, its screen comes back through the PTY, and the deck draws it in its own
     pane. The ptrace permissions (Yama) stay off the slide.
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
     | `e` | a raise-and-catch loop in a worker thread | exception mode shows only it |

   - `m` cycles the profiler's mode (wall, cpu, gil, exception, async-aware) by
     restarting it with new flags. Exception mode samples only threads with an
     active exception (observed in `--help`: `--mode {wall,cpu,gil,exception}`). gil mode pairs with `c`: the worker thread holds the GIL while
     the render loop waits for it, which is also why the deck stutters.
   - The mirror moment: drawing the profiler's screen is itself work the deck
     does (the #423 plan measures 3 to 10 ms per emulator snapshot of a busy colored
     screen), and it shows up in the profile it's drawing. Observed on the real
     deck: counterweight's `layout.place` and `Emulator.convert_row` were the top
     two functions in Tachyon's live view.
   - The presenter can hand the keyboard to the pane and use Tachyon's own keys
     (`s` sort, `t` mode, `x` trends, arrows for threads, `h` help), then take it
     back with Tab.
5. Tachyon's own flamegraph (cut-first). A key runs
   `attach -d 10 --flamegraph -o out/deck-flamegraph.html` against the deck in a
   second embedded pane while a workload runs. The output is a self-contained HTML
   file (observed: about 630 KB, with no external scripts).
   - The deck serves `out/` with
     `python -m http.server --bind 127.0.0.1 8315 --directory out` and prints
     `https://<vm>.exe.xyz:8315/deck-flamegraph.html`. zellij web's browser client
     bundles xterm.js's link addon, so clicking the URL opens it in a new tab.
   - `<vm>` comes from exe.dev's
     [reflection integration](https://exe.dev/docs/integrations-reflection.md):
     `https://reflection.int.exe.xyz/` returns the VM's own name at the top level
     (observed: `"name": "cumulus"`). The deck resolves it once at startup,
     alongside the interpreters, so a missing integration fails at launch rather
     than on the flamegraph key. The image sets the base URL and bind address
     instead; see [Running it yourself](#running-it-yourself).
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
   - `--opcodes` records which bytecode instructions are executing, including the
     adaptive interpreter's specializations. Profile the nbody workload with it and
     point at the specialized float instructions: that's the hand-off to the JIT
     section, which builds on specialization. Check whether the live TUI shows
     opcodes or only the file outputs before choosing how to show it.
   - Sampling-rate claims depend on hardware: the VM topped out near 120k samples/s,
     not the documented 1 MHz, so don't quote 1 MHz on stage.

#### Frame pointers, PEP 831 (std, right after Tachyon)
- Plain explanation: with frame pointers, every C function saves its caller's frame
  address in a register (`rbp`), forming a linked list on the stack. `perf`, eBPF
  and debuggers walk that list cheaply.
  - Without frame pointers, unwinding needs DWARF tables, and eBPF can't use those at all.
  - Compilers dropped frame pointers to free a register. That mattered on 32-bit x86;
    the PEP measures 1.5–2% on x86-64.
  - Diagram, revealed in steps: the stack as a column of frames, each saved `rbp`
    pointing at its caller's frame. Then one extension frame built without frame
    pointers breaks the chain, and everything above it becomes unreachable. That's
    the 96.9% vs 4.7% result before the perf output appears.
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
- The JIT now publishes unwind information for its machine code to GDB, and to
  GNU `backtrace()` where libgcc frame registration is available, so native
  debuggers and crash handlers unwind through JIT frames instead of stopping at
  them. One line, and it belongs to the observability frame.
- uv builds ship it compiled-in but off (`yes-off`). `PYTHON_JIT=1` turns it on, and
  `sys._jit.is_enabled()` proves it. Said in a bullet: running a script just to
  print that showed code that wasn't on screen and proved little.
- Live demo: an nbody/float loop, 3.14 vs 3.15 × JIT off/on, under hyperfine, with
  the loop's hot part on screen.
  Observed about 1.5x for 3.15+JIT, while the 3.14 JIT was flat or slower. The VM
  is noisy, so use hyperfine's warmup and runs rather than one shot.
- Diagrams:
  - the pipeline: bytecode, specialized bytecode, a trace, optimized micro-ops,
    machine code. Mark the stages that changed in 3.15.
  - a bar chart of the four hyperfine timings.

#### base64 (cut-first, could join the lightning round)
- Encode is about 2.5–3.4x faster and decode about 3.4x (observed, 5 MB). b32/b85
  were rewritten in C (58–140x observed).
- LLM angle: a JSON request body with a 5 MB base64 PDF went from about 23 to about
  15 ms. Real, but small next to network latency, so say so.
- One run puts 3.14 and 3.15 side by side: a harness runs the script on each and
  draws a pair of bars per timing, with how much faster 3.15 is. Observed 3.1x
  encode, 3.0x decode and 55x for b85.
- The padding change lives in [Before you upgrade](#6-before-you-upgrade-std), so
  it stays in the talk if this item is cut.

#### The GC story (std)
- It opens with its own title card, "The garbage collector saga": a story inside
  the performance section.
- Incremental GC:
  - landed for 3.13 and was rolled back before 3.13.0
  - shipped in 3.14.0
  - production memory-growth reports followed
  - the SC-backed revert came in 3.14.5 _and_ 3.15 (announced 2026-04-16)
- 3.15 ships the generational GC. Reintroducing incremental GC now needs a PEP.
- Live demo, with the workload on screen: the same cycle-churn script (pairs of
  objects in a reference cycle, churned beside a long-lived heap) across 3.13,
  3.14.4, 3.14.7 and 3.15.
  Observed peak RSS was 65 / 233 / 65 / 66 MiB.
  - `gc.get_threshold()` (`(2000, 10, 0)` on the incremental builds) is a one-line
    test for which collector a 3.14.x has.
  - Caveat to say aloud: this workload reproduces the memory complaint but not the
    incremental GC's pause benefit, so it isn't a general verdict.
- Diagrams:
  - a timeline: the 3.13 rollback, 3.14.0 shipping it, 3.14.4, the 3.14.5 revert,
    and 3.15. Mark which collector each release has. It's its own slide, one
    release per Space, the axis drawing itself out to each.
  - a bar chart of peak RSS per interpreter, laid out to match the timeline.

### 6. Before you upgrade (std)

What will bite on upgrade, from the whatsnew's
[Porting](https://docs.python.org/3.15/whatsnew/3.15.html#porting-to-python-3-15)
section and its removals. One script runs on 3.14 and on 3.15. Observed:

| Change | 3.14.7 | 3.15 |
|---|---|---|
| `strptime("29", "%d")` | `DeprecationWarning`, returns 1900-01-29 | `ValueError` |
| `sqlite3.connect(":memory:", 5.0)` | `DeprecationWarning` | `TypeError`: at most 1 positional argument |
| `NamedTuple("P", x=int)` | `DeprecationWarning` | `TypeError` |
| `TypedDict("TD")` | `DeprecationWarning` | `TypeError`: missing `fields` |
| `urlsafe_b64decode(b"aGk")` | `binascii.Error: Incorrect padding` | `b'hi'` |
| `assertWarns(DeprecationWarning)` around an unrelated `UserWarning` | swallowed | escapes the test |

- The punchline: every `TypeError` and `ValueError` in that table was a
  `DeprecationWarning` on 3.14. Run your tests on 3.14 with
  `-W error::DeprecationWarning` before upgrading and you find them first.
- `assertWarns` and `assertWarnsRegex` no longer swallow warnings that don't
  match, so a test suite can start leaking warnings it used to hide.
- UTF-8 by default (PEP 686). It's a release highlight and the change most
  likely to alter behavior silently, especially on Windows.
  - Demo with a non-UTF-8 locale: under `LC_ALL=en_US` (ISO-8859-1 on the VM),
    `open(...).encoding` is `ISO-8859-1` on 3.14.7 and `utf-8` on 3.15 (observed).
    `LC_ALL=C` doesn't show it: the C locale already gets UTF-8 mode on 3.14
    (observed `sys.flags.utf8_mode` 1).
  - `PYTHONUTF8=0` or `-X utf8=0` restores the old behavior, `encoding="locale"`
    asks for the locale explicitly, and `-X warn_default_encoding` emits an
    `EncodingWarning` at every call that relies on the default.
- `urlsafe_b64decode` no longer requires padding. Pass `padded=True`, or use
  `b64decode(..., altchars=b"-_")` on any version, for the old strictness.
- `importlib.metadata.metadata()` raises `MetadataNotFound` for a distribution
  directory with no metadata file, instead of returning empty metadata.
- argparse infers `dest` from a single-dash long option:
  `add_argument("-f", "-foo")` now stores to `foo`, not `f`.
- Coming next: `profile` is removed in 3.17 (use `profiling.tracing`), and
  `__version__` attributes in about 25 stdlib modules are deprecated for removal
  in 3.20 (observed: `argparse.__version__` warns).
- No diagram. The runs on each version carry it.

### 7. Lightning round (core, one slide or a rapid sequence)

Each item gets one runnable line where possible:

- "Did you mean" hints from other languages: `[1,2].push(3)` → `.append`,
  `'hi'.toUpperCase()` → `.upper`, and nested `container.area` → `.inner.area`.
- The REPL, live in the embedded REPL pane: tab completions are colored by object
  kind, `from x import <Tab>` completes the module's attributes, and pdb uses the
  new REPL.
  - The pane stretches across the slide: a terminal takes no width from its
    program, so in a centered column it would get none.
- `pprint(..., expand=True)` gives JSON-style output.
- A context manager used as a decorator (`@contextmanager`, `@asynccontextmanager`
  or any `ContextDecorator`) on a generator, coroutine or async generator function
  now stays open across the iteration or `await`. It used to exit as soon as the
  call returned the generator or coroutine object.
- tomllib supports TOML 1.1.
- `math.integer`.
- `-W` accepts regexes.
- `http.server -H`.
- `timeit --target-time`.
- argparse suggests fixes for typos.
- More colored CLIs.
- `re.prefixmatch`.
- Windows python.org builds use the tail-calling interpreter, which the whatsnew
  cites at 15–20% faster on pyperformance. It can't be shown on the Linux VM, so
  quote it as cited.
- A crashed `ProcessPoolExecutor` worker is named: the `BrokenProcessPool`
  message is unchanged, but its chained cause now reads
  `Process <pid> terminated abruptly with exit code 3` (observed).
- `subprocess.Popen.wait(timeout=...)` waits on an event (`pidfd_open` on Linux,
  kqueue on macOS) instead of a sleep loop.
- The import deadlock between one thread importing `pkg.sub` and another importing
  `pkg.sub.mod` is fixed: module locks are taken parent first.
- `__slots__` on a namedtuple subclass. Observed: 3.14 raises
  `TypeError: nonempty __slots__ not supported for subtype of 'P'`, and 3.15
  accepts it.

### 8. Closing (core)

- The thoroughness observation, with the examples collected along the way.
- Links, each labeled and a clickable OSC 8 hyperlink: the whatsnew, this talk's
  repository (public by the time of the talk), and counterweight.
- The Claude Code disclosure from the opening, again, beside Claude Code's mascot.

## Deck architecture

### Stack
- Python: 3.15, requires-python `>=3.15`. Pin `.python-version` to 3.15.0 final,
  which python-build-standalone publishes (`uv python list` offers it). rc2 has a
  Tachyon bug (gh-154335: pstats output ignores `NO_COLOR`) that rc3 fixes. Most
  observed results come from release candidates, so re-run the probes on final.
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
  - [#426](https://github.com/JoshKarpel/counterweight/pull/426) plans a diagram
    engine. Nothing waits on it. If its graph container reaches `main` during the
    build, rebuild the graph-shaped diagrams with it (see [Diagrams](#diagrams)).
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
  __main__.py        app entry: root component, navigation, export, recording
  deck.py            SLIDES = (*OPENING, *SMALL_THINGS, ..., *CLOSING)
  export.py          slides.html: a screenshot per reveal step
  recording.py       slides.cast: the deck presented by an autopilot
  tours.py           autopilot steps for slides' tours: hold, type, wait for the screen
  sections/          one module per running-order section, each exporting a tuple of slides
  components/        title card, drop shadow, footer, slide grid, code_example, run_pane,
                     split layouts, bar chart
  diagrams/          one module per diagram, built from counterweight elements
  size.py            the presenting size, in cells
  runs.py            Run values, interpreter resolution
  tachyon.py         the Tachyon stage: profiler pane, modes, flamegraph server
  workloads.py       in-process workloads the Tachyon stage triggers
examples/            every snippet shown on screen, as real files
  frozendict_default.py, json_immutable.py, sentinel_naive.py, ...
demos/frame_pointers/  churn.c + build script
tests/
Dockerfile           the image others run the deck from
```

### Design decisions

- Examples are files, not strings. Each on-screen snippet is a real `.py` file
  that the slide reads and highlights with `counterweight.highlighting.code_block`.
  The same file runs on 3.14 to show the `SyntaxError` and is fed to the type
  checkers, so display and execution can't drift. (The reference talk used
  `inspect.getsource`, which can't hold 3.15-only syntax that must also be shown
  failing on 3.14.)
- Examples are editable on stage, so an audience question becomes an edit and a
  run.
  - Tab cycles focus through the slide: its examples in order, then the run box,
    then back to the first example; Shift+Tab goes the other way. The run box is
    the stop that means "nothing being edited": it comes after the code in every
    layout and holds the slide's own keys. The slide's element handles Tab with
    counterweight's `tab_focus`, scoped to the slide, and neither an editor nor the
    run box claims Tab. The browser keeps Escape, so it can't be the only way out
    (it leaves an editor outside a browser), and Tab is free in the editor, which
    doesn't insert tabs. While editing, every other key types, so the deck's own
    keys wait until Tab.
  - Only a slide with runs makes its examples editable: an edit there would
    change nothing, and there'd be no run box to Tab back to.
  - The code stays highlighted while it's edited. The border is yellow while
    editing, and red whenever the whole file, hidden lines included, doesn't
    `compile()` on the deck's 3.15. That's the grammar the run will see, so a
    typo shows before the run. An example that is a `SyntaxError` on purpose
    (`lazy import` inside `try`) is red from the start, which is on-message.
  - Every run executes a copy of `examples/` in a temporary directory, with the
    slide's edits written over it, and its argv pointed at the copy. A harness
    finds the files it drives relative to its own copy, so edits reach the type
    checkers and hyperfine too. Never `examples/` itself, which `just watch`
    watches.
  - Edits live in the slide's state, so `r` or leaving the slide undoes them.
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
  - A run executes code the slide shows. A harness that drives a demo (hyperfine,
    the checkers, the overhead or version comparisons) runs the example on screen,
    never one the audience hasn't seen.
  - Where a slide runs the same thing on 3.14 and 3.15, 3.14 comes first, so the
    story runs "this didn't work, and now it does". `on_both` binds `1` to 3.14
    and `2` to 3.15, and hand-built run lists follow the same order.
  - While a run is in progress, the box's border pulses (slate to blue and back,
    1.2 s a breath), so a slow run doesn't look like a dead key.
  - Up and Down scroll the box's output a line at a time, since the run pane is
    the slide's focus stop anyway, so a long traceback reads without the touchpad.
- Resolve interpreters once, at startup. Resolve each interpreter path
  (`uv python find 3.14`, etc.) into a typed `Interpreters` value and fail loudly if
  one is missing. That turns a missing interpreter into a startup error, not a dead
  key on stage.
  - Name the build variant in every request. With a GIL 3.15.0rc2 and a
    free-threaded 3.15.0 final both installed, `uv python find 3.15` returned the
    free-threaded one (observed, uv 0.13.0). Ask for `3.15+gil` and
    `3.15+freethreaded` (both observed to resolve correctly), and the same for 3.14.
- Every slide that references a PEP links to it from its title:
  `PEP 814: frozendict`. The PEP numbers are a field on `Slide`, and the slide
  frame draws them into the heading, so a slide declares which PEPs it cites
  rather than laying out its own links, and the links cost no row of their own.
  - Each link is just `PEP 814`, an OSC 8 hyperlink to the PEP. The URL isn't
    spelled out: from a seat, searching for "PEP 814" is quicker than typing one.
  - A title card has no heading, so it cites no PEP; the slides after it do.
  - Without a URL in the text, xterm.js's link addon can't find it, so a click
    depends on zellij web passing OSC 8 hyperlinks through to xterm.js. That's
    untested; `just rehearse` checks it.
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
  - Up/Down: scroll the run box's output.
  - Tab / Shift+Tab: move between the slide's code and its runs, to edit the code.
  - `r`: reset the current slide, by remounting via `.with_key`.
  - `d`: open the slide grid, as spiel's deck view does. See
    [The slide grid](#the-slide-grid).
  - F1: toggle the clock, as in the reference talk. F1 opens help in some
    browsers, but not in the laptop's.
  - F2: the size check. See [Presenting resolution](#presenting-resolution).
  - F3: the slide transition picker, the same autocomplete field as F4's, offering
    `off` or an easing curve for a swipe. See [Slide transitions](#slide-transitions).
  - F4: the code theme picker, an autocomplete field as in counterweight's
    autocomplete cookbook. Typing narrows the list (the typed letters in order),
    Down and Up move the highlight, and Enter or Tab sets that Pygments style on
    every slide and thumbnail. F4 or Escape closes it unchanged. Either way focus
    goes back to whatever takes the slide's keys, through a focus handle the root
    owns. It offers only the dark styles, by their background's luminance; the
    light ones would clash with the deck. The deck starts in `github-dark`.
  - Slide-specific keys on Tachyon slides only.

  See [Presenting over zellij web](#presenting-over-zellij-web) for which keys the
  browser and zellij take first.
- Title cards sit in a drop shadow, as the reference talk's do. The shadow is an
  outer `Div` whose only borders are right and bottom, contracted by one cell so it
  starts one cell in from the top and left. In current counterweight spelling:

  ```python
  def drop_shadow(*children: Text | Div) -> Div:
      return Div(
          style=border_right
          | border_bottom
          | border_lightshade
          | border_contract(1)
          | border_color("gray", 400),
          children=list(children),
      )
  ```

  The reference talk's `border_bottom_right` and `border_contract_1` utilities no
  longer exist. #426 shows the other shade kinds (`▒`, `▓`, and a half-block
  shadow from `border_thick`) if light shade turns out too faint on the laptop.

  Every section opens with a title card, and so do Tachyon and the GC saga
  inside Performance: subsection cards, which don't start a section of their own.
- Live reload during development: see [Live reload](#live-reload).
- Export: a committed `slides.html`, regenerated by a pre-commit hook. See
  [HTML export](#html-export).
- Mounting a slide starts nothing. Subprocesses, profilers, explanatory
  animations and focus grabs start from a key press, never from mount.
  - On stage, the presenter decides when something moves. A demo or an
    animation that explains something, started on arrival, competes with
    whatever the presenter is saying as the slide comes up.
  - A `use_clock`-driven animation draws its first frame until its key, and ticks
    no clock off the live slide, so it costs nothing in a thumbnail.
  - The exception is a decorative animation, there only to look nice: it can
    start as the live slide mounts. See [Animations](#animations).
  - The slide grid mounts up to nine slides at once to draw their thumbnails, and
    the smoke test and export mount every slide. A slide that spawns on mount
    would spawn in all of them.
  - Run panes already follow this: their effect is keyed on a request that only
    a key press makes.
  - No `use_focus(auto_focus=True)` in slide content. A thumbnail that takes
    focus would take the grid's keys.

### Diagrams

Diagrams are drawn by hand, as counterweight elements rather than text files.

- Nodes are bordered `Div`s or `Text`s, styled like the slides, optionally in a drop
  shadow. Flex rows and columns place them wherever the shape allows. Edges are
  absolutely placed runs of box-drawing text drawn above the nodes, as #426's
  `cw_shadows.py` probe does.
- Border healing only joins corners, so an edge leaving the middle of a border
  draws its own tee, matched to the border's weight (`┯` under a heavy border).
- A box sits centered on the connector that meets it. `draw.py` places boxes from
  connector columns (`centered_node`, `fork`) rather than from hand-picked left
  edges, so moving a box keeps its connector.
- Nothing in a diagram wraps, so anything wider than the slide's 98 content
  columns is clipped. A test draws each diagram, at every reveal step, on a screen
  far wider than the slide and asserts it fits.
- What elements cost over a text file: positions are fiddlier to edit. What they
  buy:
  - color and shadows that match the rest of the deck
  - reveal steps, so a diagram builds up with Space (the frame-pointer chain, then
    the break)
  - a path to #426. Its graph container would compute the node positions that
    the diagram currently writes by hand, and the node components stay.
- A diagram is drawn for one width, so each one targets the
  [presenting size](#presenting-resolution). Draw none until that's settled.
- Bar charts for timings are a shared component drawn from the run's own output
  (hyperfine's `--export-json`, `tracemalloc` peaks), so they show the numbers
  from this run rather than numbers typed in beforehand.
- Animations draw at double vertical resolution with half blocks (`▀` with
  separate foreground and background colors), as the reference talk's `canvas`
  does. See [Animations](#animations) for the candidates.

### Animations

They come in two kinds, which start differently. `components/animation.py` holds
their hooks, `use_progress` and `use_loop`, and `use_synced_loop` for the title
card's border, which counts from the app's start rather than the card's mount, so
every card in view pulses in step.

Every animation runs on `use_clock`, ticking at 20 frames a second while it plays
and not at all otherwise. Off the live slide (a thumbnail) nothing ticks: an
explanatory animation shows its last frame, a still of where it ends, and a
decorative one its first. Nine thumbnails animating at once would cost frame time
for nothing. The exception is a title card's pulsing border, which pulses in the
grid too: few title cards are in view at once, so it's cheap.
The export moves its frozen clock on by a minute after each reveal
step (counterweight's `AdvanceClock`), so each screenshot shows where the step's
animation ends, and the export stays deterministic.

#### Explanatory: started by a key

An animation that explains something starts on a key press, so the presenter can
play it at the moment the explanation needs it: Space, where it stands in for
reveal steps. The animated part of a diagram is a component keyed on the step, so
Space remounts it, which plays it; until then the slide holds a still. It plays
once and stops on its last frame, so nothing moves while the presenter talks over
it.

1. First mirror wins (`TaskGroup.cancel()`). Three bars grow at the mirrors'
   relative speeds (0.3, 0.1 and 0.5 s, the race slowed to 2 s). `eu` reaches the
   end first, and the other two stop partway and turn red. The race shows that
   cancellation lands mid-flight. It replaces the diagram's first two reveal
   steps: the tree, the race, then the clean exit.
2. One source, four threads. Numbered items travel a cell every 100 ms down from
   the source, along the bar, and down each thread's six-row line to T1–T4:
   dealt one per thread for `serialize_iterator`, split at the bar into a copy for
   each of the four for `concurrent_tee`, and for the bare generator, three threads
   dying with the `ValueError` as the second item sets off. The generator's panel shows still,
   then each Space plays the next panel, revealing it.
3. Frame pointers. A cursor walks the saved-`rbp` chain frame by frame, as
   `perf` does, back to `_start`. On the next step it walks again, reaches
   `churn.so`, follows its `rbp` to data that isn't a frame, and stops, and the
   frames below it dim.
4. Tracing vs sampling. A playhead moves along the call line on Space, with quick
   helper calls (`strip`, `len`) hanging off it at each `┬`. The tracing row fires
   a hook (`▲▼`) at every call and return it passes, helpers included, the
   sampling row only at its fixed ticks (`●`), which never land on a helper, so the
   overhead difference reads as how busy each row is.
5. The GC saga's timeline, one release per Space, the axis drawing itself out to
   each before its labels appear.

#### Decorative: free to start on arrival

An animation that's only there to look nice can start as soon as its slide is
the live one, with no key, since there's no moment in the explanation to wait
for. It loops, as ambience for as long as the slide is up.

- The Tachyon title card: a particle streaking across ahead of its own trail, for
  the faster-than-light name.
- Every title card: its border pulsing from slate out to Python's blue, back
  through slate to its yellow, and back, and a shine crossing the title every few
  seconds.
- The title and closing slides' Claude Code credit: its spark turns through Claude
  Code's spinner glyphs while a shimmer sweeps across the words, since those two
  slides stay up for minutes while the talk starts and during questions.

### Presenting resolution

The talk is given from my laptop, a Surface Pro: a browser on the laptop shows
zellij web, which shows the deck. The deck targets one size in cells, declared once
in `size.py`. The hand-drawn diagrams, animations, slide grid, Tachyon stage, export
and smoke test all read it from there.

Columns matter more than rows. Layouts tend to run sideways (code beside its
notes, the Tachyon split, the fan-outs), so the width is the exact target and the
height is a floor. A diagram is drawn for one width, and redrawing all of them
after the width changes is the expensive mistake. Extra rows are slack.

A slide's runs go under its code, at the slide's full width, in one box: `1`
runs the first in it, `2` the next, each replacing what the box showed, and the
line above the box marks which one it shows. Runs beside the code, or side by
side, would halve the width of a traceback that already wraps.

Content is centered both ways by default, and a slide's title is centered on its
top row. The exceptions are pictures drawn for a fixed position, the hand-placed
diagrams. Notes beside code take their natural width and shrink to fit;
code too wide to leave the notes 28 columns puts them under it instead.

The deck is drawn for 100x30, from trying sizes on the presenting laptop.
The reference talk, presented from the same laptop, used 90x30.

- The Surface Pro's screen is 3:2. Cells are roughly twice as tall as they are
  wide, so a 3:2 window gives about 3 columns per row at any zoom, and 100x30 is
  close to that shape. Zoom trades legibility for room. It doesn't change the shape.
- Confirm it before drawing any diagrams. Open zellij web full screen on the
  laptop, in the zellij layout to be used on stage. The default layout spends rows
  on tab and status bars, so present with a bare one. Record the cell count
  `tput cols lines` reports at the zoom that gives 100 columns, and at a step
  either side.
- Judge each candidate by:
  - code: the longest example is legible from across a room
  - the Tachyon stage: the pane gets at least 60x12 with the talking-point strip
    above it, and a side-by-side split leaves the slide enough room
  - run panes: a run's output fits the full-width box under its code
  - the slide grid: thumbnails at a third of the width are still recognizable
  - diagrams: the frame-pointer stack and the CI-sized fan-outs fit
- Repeat with the laptop mirrored to an external display or projector. Projectors
  are usually 16:9, and mirroring can switch the laptop to a 16:9 mode or
  letterbox it. Either changes the cell count at a given zoom, giving more
  columns per row than the laptop alone.
- Pin the columns, not the zoom. The live check is the reference talk's: F2
  toggles a width readout in the footer, green when the terminal is exactly the
  target width and red otherwise, so a wrong width is visible before the first
  diagram. At the venue, press F2 and adjust browser zoom until it goes green.
  - The readout shows the rows too. They turn red only below the floor.
  - F1 through F4, Tab and Shift+Tab aren't among the keys the browser keeps (see
    [Presenting over zellij web](#presenting-over-zellij-web)), but confirm they
    reach the deck through zellij web. `just rehearse` covers it.
  - It's off by default, so the export renders without it.

### Live reload

The reference talk did this with two pieces, and the deck keeps both:

- `just watch` runs the deck under `watchfiles`, which restarts it whenever a file
  under `src/` or `examples/` changes. `watchfiles` goes in the dev dependency group.
- The deck writes a checkpoint to a file in the temp directory whenever the slide
  or the code theme changes, and reads it at startup: the slide's index, clamped
  to the deck's length, and the theme F4 picked. A restart lands on the same
  slide, in the same theme. Reveal steps and run output start fresh. A checkpoint
  that doesn't parse starts over from the first slide, since a deck relaunched on
  stage mustn't refuse to start.

Differences from the reference talk:

- Its `watch` recipe also watched `../counterweight/counterweight/`. Here
  counterweight is a locked git source, so edits in a local checkout don't reach
  the deck. Co-developing counterweight needs a temporary local path source; work
  out the exact uv mechanism when it's first needed.
- Its HTML export reset the index file to 0. Export here leaves the checkpoint
  alone, so exporting doesn't throw the dev session back to the title slide.
- A restart must leave nothing behind. A run pane's subprocess or the Tachyon
  profiler outliving the old deck would pile up across reloads. Check this once
  run panes exist.
- The same file is crash recovery on stage: relaunch the deck and it's on the slide
  it died on.

### HTML export

`slides.html` is the shareable copy, committed at the repository root as the
reference talk's is. `just export` drives the deck headless at the presenting size,
screenshots each slide as SVG, and writes the page.

- One screenshot per reveal step, not per slide, so a diagram that builds up with
  Space builds up in the export too.
- Run panes show their pre-run state, and the Tachyon stage shows its placeholder,
  since mounting starts nothing.
- A pre-commit hook keeps it consistent. It runs the export and rewrites
  `slides.html` in place, and pre-commit fails the commit when the file changes, so
  regenerating _is_ the check: no separate `--check` mode.
  - `repo: local`, `language: unsupported`, `pass_filenames: false`, and
    `entry: uv run --frozen python -m whats_new export`. The entry calls the module
    rather than `just export`, since just comes from mise and the hook shouldn't
    depend on a second installer.
  - Scope it with `files:` to what the render depends on: `src/` (`size.py`
    included), `examples/`, and `uv.lock`, since a counterweight bump can change the
    render with no deck change.
  - The export stages a newly created `slides.html` with `git add --intent-to-add`,
    so the first run fails like any other rewrite rather than passing silently.
- The export must be deterministic, or the hook rewrites the file on every commit.
  Anything that reads the clock, a random source, or the machine (the footer
  clock, animations, interpreter paths, the temp directory) renders a fixed state
  there. The clock is off by default and animations hold their first frame, so the
  open question is what else leaks in. Run the export twice and diff the output
  when it first works.
- pre-commit itself goes in the uv dev group, as do the hooks' tools.

### Asciicast recording

`slides.cast` is the moving copy: the whole deck presented by an autopilot,
as an [asciicast v3](https://docs.asciinema.org/manual/asciicast/v3/) that
asciinema-player plays back. `just record` writes it, through counterweight's
`Recording`, headless at the presenting size.

- Where the export shows each slide before anything runs, the recording runs
  everything: every reveal step, then every run on the slide, in order, each held on
  once it ends. A run that needs a capability the machine lacks (`perf`) is left out,
  as the example check skips it.
- A slide's `tour` carries what a presenter does on a stage the run pane doesn't
  drive, by reveal step: the REPL slide starts the REPL and shows its completions,
  and the Tachyon stage attaches the profiler, starts each workload its talking
  points name, moves through the modes, and dumps every thread. The flamegraph (`F`)
  stays out, since it serves a page the recording can't show. The recording's `Host`
  carries the real PID, so Tachyon attaches to the recording process itself.
- Time is split by what it's waiting for. Reveals hold on the frozen clock, one
  animation frame at a time, so animations play out and a hold lasts the same on
  every recording. Runs, the REPL and Tachyon take real time, which the autopilot
  waits out with `Wait` and `WaitFor` on the frame on screen. A run is waited for in
  two parts, until the run pane shows it in progress and then until it shows an
  outcome, since the previous run's outcome shows until the new run starts.
- Each slide is a chapter (a `Marker`), and the keys pressed are recorded, so the
  player can jump between slides and show the keystrokes.
- The player's idle limit cuts a run's silences down to the length of a hold.
- Real time makes the recording differ on every run, so no hook regenerates it as
  one does the export: re-record by hand when the deck changes.

### Slide transitions

Moving to the next or previous slide can swipe, as
[spiel's transitions](https://www.spiel.how/transitions/) do: the slide being left
and the one arriving sit side by side and slide across together, over 0.75 s.
F3 picks the transition: `off`, or the easing curve the swipe follows.

- The curves are the deck's own, a short list named for how they move: `linear`,
  `ease-out`, `ease-in-out`, `overshoot`, `spring` and `bounce`. `overshoot` and
  `spring` carry the slides past their place and back, so the offsets aren't
  clamped to the screen.
- Only moving from one slide straight to another swipes, as in spiel: not opening
  or leaving the grid, jumping from it, or `r`.
- Both slides are mounted for the length of the swipe. The one being left keeps
  its state (run output, edits), since it continues under its own key, but stops
  being live at once. counterweight auto-focuses a component only on the render it
  mounts, so the arriving slide takes focus, and its keys, as the swipe starts.
- Every mounting of a slide gets its own key and focus handle (`Mounting`), since
  two mounted components can't share a handle, and a slide returned to mid-swipe
  must mount afresh rather than continue the copy still leaving.
- It's `off` by default, so the export and the recording don't change. The
  checkpoint remembers the choice, as it does the code theme.
- The swipe ticks at the deck's 20 frames a second, 15 frames for the whole
  swipe. Whether that reads as smooth on the projector is for rehearsal.

### The slide grid

`d` replaces the current slide with a grid of thumbnails, as
[spiel's deck view](https://github.com/JoshKarpel/spiel/blob/main/spiel/widgets/minislides.py)
does, one section of the deck at a time. Arrows move the selection, Enter or `d`
jumps to the selected slide, and Escape goes back to the slide it was opened from.
Clicking a thumbnail jumps to it.

A headless probe against counterweight `main` drew a 3x3 grid of 14 slides at
90x30 and windowed it, and both Enter and a click jumped to the right slide. It
needed nothing new in counterweight:

- `display_grid` with `grid_template_columns(fr(), fr(), fr())` and matching
  rows lays out the cells.
- Each thumbnail is a bordered `Div` with `overflow_hidden`, holding a title line
  (`12 | Lazy imports`) and the slide's own content component. The content
  reflows into the smaller box and clips at the border, as in spiel. It is the
  live component rather than a picture, so a thumbnail is exactly what the slide
  draws at that width.
- `on_click` on the thumbnail handles the mouse.

Design:

- Deck state is the current index plus `selected: int | None`. `None` means the
  slide is showing, so "the grid is open" and "what's selected" can't disagree.
  Enter or `d` sets the current index to `selected` and clears it. Escape only
  clears it.
- Slides become `Slide(title, content, peps)` values, since the thumbnail needs a
  title. The footer can use the same title, and `peps` prefixes the heading with PEP links.
- Sections divide at title cards: `Slide.title_card` marks one, and each
  `TitleCard.SECTION` starts a section that runs to the next (a
  `TitleCard.SUBSECTION`, such as Tachyon's, doesn't). The grid shows only the selected slide's
  section, under a line naming it ("Concurrency  section 4 of 11"), with each
  section's slides starting a fresh grid rather than continuing the last one's
  row. Left and Right step through the deck in order, across sections; Up and
  Down move a row, from a section's last row into the next section's first and
  back, keeping the column where the row allows. Page Up and Page Down move
  between sections, in the grid and on a slide alike.
- Three columns, each a third of the presenting width. Show three rows of the
  section, windowed around the selected row as spiel does, rather than mounting
  the whole deck in a scroll area. Thumbnails are keyed by slide index, so moving the
  selection down a row mounts one new row and keeps the other two.
- The grid replaces the slide; it isn't an overlay on it. Leaving the slide
  unmounts it, so it comes back fresh, with its reveals and run output reset.
  That's the same as navigating away and back. An overlay would keep the slide
  mounted underneath, including a live Tachyon pane still costing frame time.
- The Tachyon stage leaves the grid while its pane has focus: there, `d` goes to
  the profiler. Take focus back with Tab first.

### The Tachyon stage

The Tachyon demo is one slide whose steps advance with Space, so the profiler pane
survives the whole section. A separate slide per step would unmount the pane on
every navigation and restart the profiler.

- Layout: the profiler pane takes the full width at the bottom, and a strip on top
  holds the current talking point and which workload is running.
  - Each talking point fits on one line, so the pane doesn't move between steps; a
    test holds every point to the slide's width. The line under it, the mode and
    what's running, wraps rather than clipping when two long-named workloads run
    at once.
  - Tachyon's live TUI needs at least 60x12. Below that it shows a "Terminal too
    small!" screen (observed).
  - Stack the panes unless the presenting width leaves the slide a useful
    strip beside a pane of at least 60 columns.
  - The `file:line` column truncates long paths, so run the deck from a short path.
- The pane runs `use_terminal` with
  `[sys.executable, "-m", "profiling.sampling", "attach", "--live", "-a", str(os.getpid())]`.
  - `sys.executable` matters: profiler and target must be the same minor version.
  - `-a` samples every thread, so workloads in worker threads show up.
    Tachyon refuses `-a` with `--async-aware`, so that mode drops it; the
    asyncio workload runs on the deck's own loop, so it still shows up.
  - A key starts the profiler; arriving on the slide doesn't (see the
    mount-starts-nothing decision). Until then the pane shows a placeholder,
    which is also what the slide's thumbnail shows.
  - The mode lives in state. Changing it changes the pane's argv and key, which
    remounts the pane and restarts the profiler. Leaving the slide unmounts the
    pane, which hangs up the PTY and ends the profiler.
- Focus: keys go to the deck by default, so workload keys work.
  - A key hands focus to the pane, and the presenter drives Tachyon's own keys.
  - Tab takes it back. Tachyon's TUI binds letters, arrows, `/`, `+` and `-`,
    but not Tab. Ctrl+B, the prefix from #423's multiplexer example, works too
    where zellij lets it through.
  - #423's phase 2 covers both halves: focusing a pane that mounts in the same
    update, and reading modal prefix state synchronously.
  - Raw input mode isn't needed, since Ctrl+C never has to reach the profiler.
- ptrace: the profiler is the deck's _child_, attaching to its parent. The deck's
  PID comes from the `Host`, resolved at startup like the interpreters, so the loop
  diagram shows the real one (the export pins one, to stay deterministic).
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
browser on my laptop showing zellij web.

- Keys pass through two layers before the deck sees them.
  - zellij's normal mode takes Ctrl+B, Ctrl+G, Ctrl+P, Ctrl+T, Ctrl+N, Ctrl+H,
    Ctrl+S, Ctrl+O and Ctrl+Q. The Tachyon stage gives the keyboard back on Tab,
    which zellij leaves alone, but the embedded REPL still needs Ctrl+B, since Tab
    completes there. Present in locked mode (Ctrl+G), where zellij passes every key
    through.
  - The browser keeps some keys whatever zellij does: F5 (reload), F11, and
    Ctrl+W/T/N. The deck binds none of them. F1 opens help in some browsers, but
    the laptop's passes it through.
  - `just rehearse` presses every deck key through zellij web and confirms the deck
    received it.
- The cell count comes from the browser window and its zoom. See
  [Presenting resolution](#presenting-resolution).
- Terminal rendering is xterm.js, not a native terminal. It draws ZWJ sequences
  and flags at inconsistent widths. Before it, zellij 0.45.1 drops every
  zero-width code point, combining marks included
  ([zellij-org/zellij#5500](https://github.com/zellij-org/zellij/pull/5500) is
  open), so nothing the deck draws may rely on one: the Unicode slides print marks
  as `\u` escapes and draw them as spacing look-alikes.
- Clickable links come from xterm.js's link addon, which zellij web bundles (found
  in the zellij 0.45.1 binary). That's untested end to end.
- The network sits between the deck and the projector. The live Tachyon pane
  redraws constantly, so rehearse on the venue network, and have a phone hotspot.
- 2 vCPUs are shared by the deck, the profiler, the workloads and the zellij server.
  - Timings will be noisy. Phrase results as "on this VM, right now".
  - The free-threaded duplicate-items demo did reproduce here.

### Running it yourself

Anyone can run the deck from one line in the README, without trusting their
machine to its dependency tree: counterweight from git, `pyghostty`'s prebuilt
pre-1.0 `libghostty-vt`, three type checkers and six interpreters.

```bash
docker run --rm -it --network none ghcr.io/joshkarpel/whats-new-in-python-315:main
```

- The container is the safety boundary. A compromised dependency can't read the
  viewer's home directory or credentials, and with `--network none` it can't send
  anything anywhere either.
  - The README says so beside the command, and says what breaks the boundary:
    mounting a home directory or the Docker socket, or `--privileged`.
  - The image runs as a non-root user.
- CI builds the image from `uv.lock` with `uv sync --frozen`, so everyone runs the
  resolution the deck was tested against.
  - Every push to `main` publishes tags `main` and the commit SHA. The README
    uses `main`. Anyone who wants a fixed build pins the SHA tag or the digest.
  - What it costs: a build-and-push workflow, a multi-gigabyte image, and viewers
    trusting this repository's CI build instead of resolving packages themselves.
- Not `uvx --from git+...`. `uv tool run` ignores the project's lockfile and
  resolves fresh, and has no `--locked` or `--frozen`. Observed on uv 0.13.0: a
  lock pinning `six==1.15.0` ran 1.15.0 under `uv run --frozen` and 1.17.0 under
  `uvx --from`. Viewers would get whatever counterweight `main` and `pyghostty`
  look like that day.
- Nothing downloads at launch, which `--network none` requires. The image bakes
  in everything the deck uses:
  - the six interpreters, from `uv python install`, so the startup interpreter
    check passes in the image too
  - the dev group's type checkers, and Node for pyright
  - mypy 2.3.1, by running its `uvx --from mypy==2.3.1` once at build time and
    setting `UV_OFFLINE=1`. Confirm that `uvx` then reuses the cached
    environment without the network.
  - hyperfine from mise, so it's the version `mise.toml` pins
  - a C compiler, for the frame-pointer extension
  - The entrypoint runs the synced venv's Python directly, so uv resolves
    nothing at startup.
- Build for `linux/amd64` and `linux/arm64`, so Docker Desktop on Apple Silicon
  runs it natively.
- The flamegraph link needs a network, so `--network none` costs that
  (cut-first) demo. Its base URL becomes one setting: on the VM the deck fills it
  from the reflection lookup, and the image sets it, so the lookup doesn't run off
  exe.dev. The README gives a second command for it, with
  `-p 127.0.0.1:8315:8315` and the server bound to `0.0.0.0` inside the
  container, since a server bound to the container's own loopback can't be
  reached through a published port.
- Some demos may not work in a default container. Test each in the image, and
  list in the README whatever fails. A failure shows on the slide as any failed
  run's output does, with no special path.
  - `perf`, for frame pointers. Docker's default seccomp profile is expected to
    block `perf_event_open` (untested). The README doesn't suggest
    `--privileged`, since that removes the isolation the image exists for.
  - Tachyon attaching to its parent. It depends on the host kernel's Yama
    `ptrace_scope` (Docker Desktop's VM, on a Mac) and the seccomp profile's
    ptrace rules. The `prctl(PR_SET_PTRACER, ...)` opt-in from
    [The Tachyon stage](#the-tachyon-stage) covers scope 1.
- A viewer's terminal won't be the presenting size. F2's size check shows them
  which way to resize.

### Counterweight gaps likely to matter
- No controls from effects (`plans/react-features.md` step 2, not started). An
  effect can't `Quit()` or ring the bell. Probably fine.
- No context or `use_reducer`. Pass the slide index and flags down as props.
- No built-in timer or footer. `use_clock` makes these easy.
- Rendering cost: the embedded pane costs real frame time (the emulator snapshot),
  on top of whatever workload is running. Watch the frame rate on the Tachyon
  stage as the audience sees it, through zellij web.

## Verification

- Example check: a test (`just check-examples` or pytest) runs every `Run`
  declared on every slide and asserts its expected outcome.
  - The expected outcome is an exit code plus a key substring:
    `SyntaxError` on 3.14, `Success: no issues found` for mypy, and so on.
  - Without this, an interpreter or checker bump silently breaks a slide.
  - Assert against the run's own output, not the rendered deck, which embeds the source.
- Smoke test: a headless autopilot walks every slide at the presenting size,
  catching render crashes and slides that overflow it.
  - It also opens the grid and moves the selection through every row, so a slide
    that crashes at thumbnail width fails here, not on stage.
  - At the end it asserts the deck process has no child processes, which
    enforces that mounting a slide starts nothing.
  - On each slide, every `PEP <n>` in the rendered text must appear in that
    slide's `peps`, so a slide can't cite a PEP without linking it.
- Diagram fit: every diagram, at every reveal step, drawn on a screen far wider
  than the slide, must fit the slide's content width, and every Tachyon talking
  point must fit on one line. From the screen alone, text clipped at the edge
  looks the same as text that ends there, so the test measures drawings where
  nothing clips them.
- The export hook: a commit that changes the render without regenerating
  `slides.html` fails. See [HTML export](#html-export).
- The image: CI runs the smoke test and the example check inside the image, on
  both architectures and with `--network none`, before pushing it. A missing
  interpreter or tool, or anything that reaches for the network, fails the
  build rather than a viewer's run. See [Running it yourself](#running-it-yourself).
- `just rehearse` checks the presenting setup before the talk. It scripts what
  it can:
  - every interpreter resolves, and so does the VM name
  - the embedded profiler attaches to the deck's PID
  - `perf` works
  - numpy has a 3.15 wheel installed

  Then it prints a manual checklist for the browser side, run over zellij web
  from the presenting browser:
  - every deck key arrives through the browser and zellij's locked mode,
    Escape and Enter included
  - F1 through F4, Tab and Shift+Tab reach the deck; Tab moves between a slide's
    code and its runs, and takes the keyboard back from Tachyon's pane
  - clicking a thumbnail in the slide grid reaches the deck
  - the flamegraph URL opens from a click
  - the Unicode slides draw cleanly, with no stray or missing marks

  The intent is to find problems the day before, not to keep a canned-output
  fallback path in the deck.

## Risks

- The venue network. Everything the audience sees crosses it. Rehearse there,
  and have a hotspot.
- #423 timing. The Tachyon stage and colored run panes wait on #423 reaching
  `main`. Build everything else first, so a late #423 delays only one section.
- numpy wheels for 3.15. Confirm cp315 wheels exist, for both x86-64 and
  aarch64 Linux, before relying on the compiled-extension workload.
- Noisy timings (JIT, base64, lazy imports, profiler overhead) on a shared
  2-vCPU VM. Use hyperfine with warmup, and phrase results as "on this VM, right now".
- Free-threaded builds are needed for the duplicate-items demo. Pin
  3.14t and 3.15t.
- 3.14.4 specifically is needed for the GC demo, since later 3.14 patches have the revert.

## Decisions

- Length: about an hour of material with questions during the talk, and 90 minutes
  at most.
- Build content for every item, then cut while practicing. The tags and minutes
  guide the cutting rather than decide what gets built.
- Venue setup: present from this VM over zellij web, in a browser on my laptop.
- Diagrams over text wherever a picture carries the point, drawn by hand as
  counterweight elements. #426's diagram engine replaces hand placement if it
  lands during the build.
- Title cards get drop shadows.
- A committed `slides.html` export, kept current by a pre-commit hook.
- A `slides.cast` recording of the deck presented, runs and all, recorded by hand.
- Color: the embed (#423) renders program output with its colors. If that falls
  through, the deck stays plain text and color becomes later work.
- No speedscope. The point is Tachyon, so the browser step (if kept) shows
  Tachyon's own HTML flamegraph.
- Others run the deck from a CI-built image, built from `uv.lock` and run with
  `--network none`. Not `uvx --from git+...`, which ignores the lockfile.

## Build order

1. Scaffold: pyproject with counterweight as a git source on `main`, `mise.toml`,
   `.python-version`, `justfile` (`present`, `watch`, `check-examples`,
   `rehearse`, `export`), and `.pre-commit-config.yaml` with the base and ruff
   hooks.
2. Deck skeleton: navigation, footer, title cards with drop shadows, live reload,
   and the HTML export with its pre-commit hook. Until step 4 confirms the size,
   the export renders at the starting 90x30.
3. The image: the `Dockerfile`, the CI workflow that tests it and pushes it, and
   the README command. See [Running it yourself](#running-it-yourself). Building
   it this early means each later step adds its interpreters and tools to the
   `Dockerfile` as they arrive, and CI catches the ones that don't.
4. [Presenting resolution](#presenting-resolution): confirm 100x30 on the laptop
   and record the size in `size.py`. The grid, diagrams and Tachyon stage
   depend on it.
5. The slide grid, the size check, and the bar-chart component.
6. `code_example` + `Run` + `run_pane`, built and proven on the frozendict and json
   slides, plus `check-examples`.
7. Sections 1–4 in order, diagrams included: mostly content once step 6 exists.
8. Tachyon, in two halves:
   - Now: `workloads.py` and the flamegraph link. Run the profiler from a plain
     zellij pane against the deck while building these.
   - Once #423 is on `main`: the Tachyon stage, then swap `run_pane` to embedded
     terminals. Budget the most time here.
9. Frame pointers, JIT, GC and base64 demos, with their diagrams. Test `perf` and
   the ptrace attach in the image, and list what fails in the README.
10. Before you upgrade, the lightning round, closing, and the thoroughness slide.
11. `rehearse` over zellij web from the laptop, then a pass with the laptop mirrored
    to an external display at the presenting size.

## References

- [What's New in Python 3.15](https://docs.python.org/3.15/whatsnew/3.15.html)
- PEPs: [661](https://peps.python.org/pep-0661/) sentinels,
  [686](https://peps.python.org/pep-0686/) UTF-8 by default,
  [728](https://peps.python.org/pep-0728/) closed TypedDict,
  [747](https://peps.python.org/pep-0747/) TypeForm,
  [798](https://peps.python.org/pep-0798/) unpacking in comprehensions,
  [799](https://peps.python.org/pep-0799/) profiling package,
  [800](https://peps.python.org/pep-0800/) disjoint bases,
  [803](https://peps.python.org/pep-0803/) stable ABI for free-threaded builds,
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
- [Python Free-Threading Guide](https://py-free-threading.github.io/)
- [PEP 829 discussion](https://discuss.python.org/t/pep-829-structured-startup-configuration-files/106789)
- [litellm `.pth` compromise](https://futuresearch.ai/blog/litellm-pypi-supply-chain-attack/)
  (timing context only)
- [counterweight grapheme work](https://github.com/JoshKarpel/counterweight/issues/392)
- Prior art: [py-spy](https://github.com/benfred/py-spy),
  [austin](https://github.com/P403n1x87/austin)
- [Reference talk](https://github.com/JoshKarpel/python-concurrency-and-parallelism)
