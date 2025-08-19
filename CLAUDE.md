# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Commands

### Testing
- Run tests: `python -m pytest`
- Run specific test file: `python -m pytest test_long_time.py`
- Run specific test: `python -m pytest test_long_time.py::test_init__full`

### Running the Timeline Generator
- Generate a specific sheet: `python timeline.py --sheet 50`
- Generate all sheets: `python timeline.py --all`
- Debug mode: `python timeline.py --sheet 50 --debug`

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
- Do not leave any trailing whitespace
