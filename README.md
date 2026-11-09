# Math Tic-Tac-Toe

A **mobile app** (Android and iOS) built in Python with Flet: tic-tac-toe where
every move requires solving a math question. Its Portuguese name is
*Cálculo da Velha*, a pun on *jogo da velha* (Portuguese for tic-tac-toe) and
*cálculo* ("calculation").

## How to play

- The app opens on the **settings** screen (see below). Tap **Play** to start.
- Each cell of the 3x3 board shows a math question.
- Tap a cell: a modal shows the question and 3 possible answers.
- Right answer: the cell gets your mark (X or O) and the turn passes.
  Wrong answer: the cell gets a new question and you keep the turn.
- Each player has a color: **X is blue, O is orange**. The message showing
  whose turn it is uses that player's color, like their marks on the board.
- After each answer, a message shows **"Correct answer." in green** or
  **"Wrong answer." in red**.
- When someone wins, the 3 cells of the winning line turn **gold**.
- When the match ends (win or draw), a **Restart** button (*Jogar novamente*
  in Portuguese) appears below the board to start a new match with the same
  settings.
- The **⚙ button** next to the title (or the phone's back button) returns to
  the settings screen. Tapping **Play** there starts a new match.

## Settings

The settings screen chooses what the match practices. **Everything starts
selected**: all 4 operations and all 10 times tables.

- **Operation**: 4 square buttons, **+ − × ÷**.
- **Times table** (*Tabuada*): only shown when **×** or **÷** is selected.
  Buttons **1 to 10**.
- Selected options are dark; unselected ones are light.
- **Each tap changes only the option tapped**: a selected option becomes
  unselected, an unselected one becomes selected. The other options never
  change. For example, with everything selected, tapping **5** removes only
  the 5 table.
- One option of each section always stays selected (tapping the last one
  does nothing), so the game always has questions to ask.

What each operation asks:

| Operation | Questions |
| --- | --- |
| + Addition | Numbers from 1 up to 10, 15 or 20 (the center of the board has the biggest numbers) |
| − Subtraction | Same numbers; the result is never negative |
| × Multiplication | The chosen tables: `7 × 1` to `7 × 10` for each one |
| ÷ Division | The chosen division tables: `7 ÷ 7` to `70 ÷ 7` (answers 1 to 10) for each one |

- With several operations, each question first picks one of them at random,
  so they appear about equally often (addition has hundreds of possible
  questions, a times table only 10).
- The 9 questions on the board are always different from each other, and a
  wrong answer always brings a question that is not on the board. (A times
  table has 10 facts, so there is always one left.)
- Settings last while the app is open; they are not saved when it closes.

## Screen and orientation

- **Portrait only**: the app locks itself in vertical (portrait) orientation
  when it starts, so rotating the phone does not rotate the game.
- **Full width**: the board fills the whole screen width (minus an 8 dp
  margin). Cells stay square and every size on the screen (title, messages,
  board text, restart button) grows with the screen, so bigger phones and
  tablets get a bigger, proportional game.
- **Everything always fits**: the restart button can never be pushed off the
  screen. On screens that are not tall enough for a full-width board (iPads,
  unfolded foldables, square or landscape windows), the board shrinks just
  enough for the whole screen to fit, restart button included. The space for
  that button is reserved even while it is hidden, so nothing moves when a
  match ends. On phones in portrait the board always gets the full width.
  The settings screen is always shorter than the game screen, so its Play
  button is never hidden either.
- If the screen size or the system bars change (e.g. split screen), the
  layout adapts immediately.

Platform limits of the portrait lock (set by Android/iOS, not by the app):

- **Android 16+ on large screens** (tablets and foldables at 600 dp or wider)
  may ignore the lock; Android lets the user choose there.
- **iPad**: iOS only honors the lock if the app opts out of multitasking
  (Split View / Slide Over). This is not configured.
- The lock is applied when the app code starts, so the brief launch (splash)
  screen follows the system rotation.

## Languages

The app is available in **Portuguese** and **English** and picks the language
automatically from the phone settings:

- If the phone's primary language is Portuguese (any variant: `pt`, `pt-BR`,
  `pt-PT`, ...), the app is shown in Portuguese.
- In any other case (English, Spanish, unknown, ...), the app is shown in
  English.

The language is read once, when the app starts. To test the other language,
change the phone language and reopen the app. All texts live in
`src/math_tic_tac_toe/i18n/catalogs/` (one file per language).

## Requirements

- **Python 3.10 or newer** on your computer. Check with `python --version`
  (on macOS/Linux the command may be `python3`; on Windows you can also use
  the `py` launcher).
- **An Android or iOS phone** with the **Flet** app installed from Google Play
  or the App Store, to run the app during development.
- **Your computer and your phone on the same Wi-Fi network.**
- To build the installable app: see [Building the mobile app](#building-the-mobile-app).

## Setting up the environment

This project **always** uses a Python virtual environment (venv) named `.venv`
in the project root. Every command in this README assumes that environment is
**active**. Do not install the project in your global Python.

Why:

- Flet, its CLI, pytest and ruff stay isolated from other Python projects, so
  everyone works with the same dependency versions.
- Recent Linux distributions (e.g. Debian 12+, Ubuntu 23.04+) and Homebrew's
  Python refuse `pip install` outside a virtual environment
  (`externally-managed-environment` error, PEP 668).

No `.env` file or environment variables are needed.

### 1. Create the venv (once)

From the project root (the folder containing `pyproject.toml`):

```powershell
# Windows (PowerShell)
python -m venv .venv
```

```bash
# macOS / Linux
python3 -m venv .venv
```

This creates the `.venv` folder, which is already listed in `.gitignore`.

> On Debian/Ubuntu, if you get `ensurepip is not available`, install the venv
> module first: `sudo apt install python3-venv`.

### 2. Activate the venv (every new terminal)

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

```bat
:: Windows (cmd.exe)
.venv\Scripts\activate.bat
```

```bash
# macOS / Linux
source .venv/bin/activate
```

When it is active, the prompt starts with `(.venv)`. From then on, `python`,
`pip`, `flet`, `pytest` and `ruff` refer to the venv on every platform. If the
prompt does not show `(.venv)`, activate it before running anything else.

> If PowerShell refuses to run `Activate.ps1` ("running scripts is disabled on
> this system"), allow local scripts for your user and try again:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

> Editors: point VS Code / PyCharm to the interpreter in `.venv`
> (`.venv\Scripts\python.exe` on Windows, `.venv/bin/python` elsewhere) so
> their terminals, test runner and debugger use it too.

### 3. Install the project (once, and after dependency changes)

With the venv active:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

- `-e` (editable) installs the package in place, so code changes take effect
  without reinstalling.
- `[dev]` installs the development tools: the Flet CLI (`flet run`,
  `flet build`), pytest, pytest-cov and ruff.

Dependencies are declared in `pyproject.toml`:

- `dependencies`: what the app needs at runtime. **These are bundled into the
  mobile app**, so keep this list small.
- `[project.optional-dependencies] dev`: development tools only, never bundled.

After changing them, run the install command again.

### 4. Leave the venv

```powershell
deactivate
```

To start from scratch, delete the `.venv` folder and repeat steps 1 to 3.

## Running on your phone (development)

With the venv active, from the project root:

```powershell
# Android
flet run --android -r

# iOS
flet run --ios -r
```

1. The terminal prints a QR code.
2. Scan it with the phone camera; it opens the app inside the Flet app.
3. With `-r`, the app reloads on the phone whenever you save a file in `src/`.

`flet run` finds the app through `[tool.flet.app] path = "src"` in
`pyproject.toml`, which points to `src/main.py`.

> If the phone cannot connect, make sure both devices are on the same Wi-Fi
> network and that your computer's firewall allows incoming connections for
> Python.

### Quick preview on the computer (optional)

For fast iterations without the phone, `flet run --web -r` opens the app in
the browser. This is only a development shortcut: always check the result on
a phone, which is the target platform. In the browser the orientation is not
locked and the board fills the browser window width; use a narrow window or
the browser's device mode (F12, then "Toggle device toolbar") to see a phone
layout.

## Building the mobile app

`flet build` always needs the **target platform** right after `build`
(`apk`, `aab` or `ipa`). With the venv active, from the project root:

```powershell
# Android test build (first time: also installs Flutter, JDK and Android SDK)
flet build apk --yes
```

| Command | Output | Use | Build machine |
| --- | --- | --- | --- |
| `flet build apk` | `build/apk/` | Install directly on Android phones for testing | Windows, macOS or Linux |
| `flet build aab` | `build/aab/` | Upload to Google Play | Windows, macOS or Linux |
| `flet build ipa` | `build/ipa/` | Install on iPhones / upload to the App Store | macOS with Xcode only |

- On the first build Flet installs what is missing (Flutter SDK and, for
  Android, the JDK and the Android SDK). It asks for confirmation; add `--yes`
  after the platform (e.g. `flet build apk --yes`) to accept automatically.
  This takes a while and needs internet.
- Only `src/` (see `[tool.flet.app]` in `pyproject.toml`) and the runtime
  `dependencies` are packaged; tests, docs and the venv are not.
- The build bundles the newest Python version supported by Flet that matches
  `requires-python`. CI tests every version from 3.10 to 3.14 for that reason.
- Before publishing to the stores, set the app identity in `pyproject.toml`
  under `[tool.flet]`: `org` (e.g. `com.yourcompany`, which forms the bundle
  ID), `product` (name under the app icon) and `company`.

### Troubleshooting

- **`flet build: error: the following arguments are required: target_platform`**:
  the platform is missing. Run `flet build apk` (or `aab` / `ipa`), not just
  `flet build` or `flet build --yes`.
- **`flet: command not found`** / **`'flet' is not recognized`**: the venv is
  not active, or the dev tools are not installed. Activate the venv and run
  `python -m pip install -e ".[dev]"`.

## Quality checks

With the venv active:

```powershell
ruff check .         # lint
ruff check --fix .   # lint and apply automatic fixes
pytest               # tests + coverage report
```

### Test coverage

Every `pytest` run measures line and branch coverage of `src/` and prints the
lines that are not covered. **The run fails if total coverage is below 90%**
(`fail_under` in `[tool.coverage.report]`, `pyproject.toml`), even if every
test passes. New code must come with tests.

To browse the uncovered lines in detail, generate an HTML report and open
`htmlcov/index.html`:

```powershell
pytest --cov-report=html
```

### Continuous integration

The same checks run on GitHub for **every push to any branch and every pull
request** (`.github/workflows/ci.yml`):

- **Ruff lint**: `ruff check`, with problems shown inline on the commit/PR.
- **Pytest**: the test suite with the 90% coverage minimum, on Python 3.10,
  3.11, 3.12, 3.13 and 3.14. The coverage table is shown on the run's summary
  page.

CI also creates a venv and installs with `pip install -e ".[dev]"`, exactly as
described above. Ruff is pinned to an exact version in `pyproject.toml`, so
local and CI results always match; upgrade it on purpose.

The game core (`game.py`) does not depend on Flet, so the rules are tested
without running the app. The screen is tested too: `tests/test_app.py` starts
the real app on a fake page and plays full matches by tapping its controls. The current interface is only the first skeleton;
game modes, a computer opponent, stealing, profiles and a scoreboard will be
added in the next steps.

## Project structure

```
.github/workflows/ci.yml      CI: lint, tests and coverage on every commit
pyproject.toml                dependencies, Flet, pytest and ruff settings
src/                          everything packaged into the mobile app
  main.py                     mobile entry point (flet run / flet build)
  math_tic_tac_toe/           the game package
tests/                        pytest suite
```

Each module in `src/math_tic_tac_toe/` has a single responsibility:

| Module | Responsibility |
| --- | --- |
| `game.py` | Game rules: board, turns, victory (and its winning line), draw, end of match, no repeated questions on the board. Language-agnostic. |
| `settings.py` | What players choose: any combination of operations (+ − × ÷) and times tables (1 to 10); everything by default. |
| `questions.py` | One problem maker per operation, and the generator that picks a question and its answer choices. |
| `app.py` | Builds the app: detects the language, creates both screens and wires them together. |
| `i18n/language.py` | Supported languages and mapping of a device code (`pt-BR`) to one of them. |
| `i18n/text_key.py` | Identifiers of every text shown to the user. |
| `i18n/catalogs/` | One file of texts per language, plus the registry. |
| `i18n/translator.py` | Looks up and formats texts in one language. |
| `ui/device_language.py` | Asks the phone which language it uses. |
| `ui/orientation.py` | Locks the app in portrait on phones (no-op on web/desktop). |
| `ui/layout.py` | Computes every size from the screen size: full-width board, never hiding the restart button (no Flet). |
| `ui/responsive.py` | Reads the screen size and system bars; applies the layout again when they change. |
| `ui/presenter.py` | Turns the game state into translated display data (no Flet). |
| `ui/ports.py` | Interfaces the controller expects from the screen, grouped in `Screen` (no Flet). |
| `ui/controller.py` | Connects screen events to the game rules; starts new matches (with new settings on Play). |
| `ui/screens.py` | Common frame of both screens (margins, safe area, centering, scrolling). |
| `ui/navigator.py` | Switches between the settings and the game screens (back button included). |
| `ui/settings_view.py` | Settings screen: operation buttons, times table buttons and the Play button. |
| `ui/game_header.py` | Top of the game screen: the title and the ⚙ settings button. |
| `ui/title_view.py` | A screen title (single line, sized by the layout). |
| `ui/board_view.py` | Draws the 3x3 board of square buttons across the full width, with the winning line in gold. |
| `ui/question_dialog.py` | Modal showing the question and 3 answer choices. |
| `ui/status_view.py` | Shows whose turn it is and feedback on the last move. |
| `ui/restart_button.py` | Restart button as wide as the board, shown when a match ends. |
| `ui/square_button.py`, `ui/styles.py` | Shared square-button look, player and feedback colors, fixed dialog sizes. |

Only the `ui/` modules (except `presenter.py` and `ports.py`) import Flet. The
controller depends on the interfaces in `ui/ports.py`, so it is tested with
fake screens (`tests/test_controller.py`).

### Adding a language

1. Add it to `Language` in `i18n/language.py` (e.g. `SPANISH = "es"`).
2. Create `i18n/catalogs/spanish.py` with a text for every `TextKey`.
3. Register it in `CATALOGS` in `i18n/catalogs/__init__.py`.

The tests in `tests/test_i18n.py` fail if a language has no catalog or a
catalog misses a text.
