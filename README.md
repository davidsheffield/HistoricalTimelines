Historical Timelines
====================

Code for generating a historical timeline that can be printed out and wrapped
around a room. The room has 80 ft of walls and with 0.25 in per year it will
cover 1740 BCE to 2100 CE. The goal is to help me see the times between
historical events and how events and lives overlapped. The dates are provided
with YAML files in the [dates/](./dates/) directory.

Usage
-----

Generate a specific sheet:

    python timeline.py --sheet 50

Generate a range of sheets:

    python timeline.py --sheet 1-5

Generate all sheets:

    python timeline.py --all

Debug mode (adds visual guides):

    python timeline.py --sheet 50 --debug

Output SVG files are written to the `sheets/` directory, named
`Sheet_{number}_{start_year}_{end_year}.svg`.

Files
-----

- **timeline.py**: Generates a visual historical timeline. It calculates and
plots events spanning from 1740 BCE to 2100 CE, with a scale of 0.25 inches
per year.
- **long_time.py** `datetime.date` that functions for both BCE and CE.
