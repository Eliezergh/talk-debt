# Talk Debt

Talk Debt is a tiny macOS floating standup timer built with Python + PySide6.
It stays visible while screen sharing, counts down for each teammate update, and
keeps counting in red once time goes negative.

## Features

- Always-on-top floating timer window
- Draggable frameless UI
- Start / pause / reset / next speaker controls
- Preset durations: 30s, 1m, 2m, 3m, 5m
- Custom duration in seconds or minutes
- Tray/menu bar controls for timer and mode toggles
- Compact mode and screen-share mode
- Optional click-through mode
- Local JSON settings persistence (duration, position, modes)

## Requirements

- Python 3.12+
- macOS (uses menu bar tray behavior)

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run locally

```bash
python -m talk_debt.app
```

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"
```

## Basic usage

- Drag the timer window to place it near your board
- Use buttons or tray menu to:
  - Start / Pause
  - Reset
  - Next speaker
  - Change duration presets or set custom duration
  - Toggle compact mode / screen-share mode
  - Toggle click-through mode
  - Toggle always-on-top
- Timer display:
  - Positive: `MM:SS`
  - Negative: `-MM:SS` in red

## macOS packaging (simple)

One straightforward option is `py2app`:

1. Add `py2app` as a build dependency.
2. Create a setup config for app bundling.
3. Build with:

```bash
python setup.py py2app
```

You can also package with alternatives like Briefcase or PyInstaller.

## Suggested next improvements

- Keyboard shortcuts (start/pause, reset, next speaker)
- Sound cue when crossing zero
- Per-speaker timing history
- Total standup overflow tracker
- “Today’s Talk Debt” summary panel
