# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Commands

### Testing
- Run tests: `python -m pytest`
- Run specific test file: `python -m pytest test_long_time.py`
- Run specific test: `python -m pytest test_long_time.py::test_init__full`

### Running the Timeline Generator
- Generate a specific sheet: `python timeline.py --sheet 3`
- Generate all sheets: `python timeline.py --all`
- Debug mode: `python timeline.py --sheet 3 --debug`

### Interactive Web Viewer
- Export data for the web viewer: `python export_web_data.py`
  (writes `web/timeline_data.js`; re-run after changing `dates/`)
- Then open `web/index.html` in a browser (works over `file://`)

## Architecture

### Core Components

**timeline.py** - Main SVG timeline generator
- Generates historical timeline sheets
- Processes YAML data files to create visual timeline boxes with labels and styling

**long_time.py** - Extended date class for BCE/CE handling
- Custom `date` class that extends functionality beyond Python's datetime limitations
- Handles both BCE (Before Common Era) and CE (Common Era) dates
- Key methods: `fromisoformat()`, `fromdatetime()`, `ordinal_day()`, `days_in_year()`
- ISO format uses negative years for BCE (e.g., "-0001-01-01" for 1 BCE)

**export_web_data.py** - Data exporter for the interactive web viewer
- Reuses `timeline.py`'s pipeline (`load_data`, `extract_dates`,
  `assign_alternating_classes`) rather than re-parsing the YAML
- Resolves each bar's color from `template.svg`'s stylesheet, falling back to a
  per-category hue; classifies categories (YAML file stems) into themes
- Writes `web/timeline_data.js` (`window.TIMELINE_DATA`) as a `.js` file (not
  JSON) so the viewer loads it over `file://`, where `fetch` is blocked

**web/index.html** - Interactive, screen-oriented timeline viewer
- Separate from the print pipeline (no sheets); lays entries out dynamically on
  a continuous time axis with a fixed scale (`PX_PER_YEAR`, a single constant so
  zoom can be added later)
- Greedy lane-packs each visible category's entries into non-overlapping rows,
  recomputed when the selection changes; hierarchical theme/category picker;
  hover/click for detail

### Data Structure

**dates/** - Historical data in YAML format
- Each YAML file contains arrays of historical events, periods, and lives
- Dates in ISO format, negative years for BCE periods

**sheets/** - Generated SVG output files
- Named pattern: `Sheet_{number}_{start_year}_{end_year}.svg`
- Contains timeline visualization with color-coded periods and labels

### Style

- PEP 8
- 4 space indents
- 80 characters per line unless it will make the result harder to read than a long line
- Prefer single quotes `''` over double quotes `""`
- Run `ruff check . --select W291 --select W293 --fix` after making changes to remove trailing whitespace

### Testing

- Add unit tests when possible for new functionality or bug fixes
