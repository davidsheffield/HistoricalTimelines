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

Viewing
-------

`viewer.html` stitches all generated sheets side-by-side into one
continuous, horizontally-scrollable timeline in the browser, with the
most recent sheet on the right and the oldest on the left. The printer
crop-mark margins are hidden so adjacent sheets meet seamlessly, while
the year labels at the top of each sheet remain visible.

Open `viewer.html` directly in a browser (no server needed).

Navigation:

- **Sheet #** input — jumps to a specific sheet
- **Year** input — accepts `1776`, `1776CE`, `44BCE`, or `-43`
- **← / →** buttons or arrow keys — step one sheet
- Mouse wheel — scrolls horizontally
- Query string — open pre-centered, e.g.
  `viewer.html?year=1776` or `viewer.html?sheet=50`

Files
-----

- **timeline.py**: Generates a visual historical timeline. It calculates and
plots events spanning from 1740 BCE to 2100 CE, with a scale of 0.25 inches
per year.
- **long_time.py** `datetime.date` that functions for both BCE and CE.
- **viewer.html**: Browser-based viewer that stitches all generated
sheets into a single continuous timeline with horizontal scrolling and
year/sheet navigation.
