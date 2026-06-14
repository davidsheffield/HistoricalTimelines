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

Interactive web viewer
----------------------

`web/index.html` is a separate, screen-oriented viewer (not for printing).
Instead of stitching pre-rendered sheets, it lays the data out dynamically in
the browser on a single continuous time axis, so there are no sheets to
navigate and you choose what to display.

First export the data, then open the page:

    python export_web_data.py        # writes web/timeline_data.js
    open web/index.html              # works directly from disk (file://)

Re-run `export_web_data.py` whenever the YAML files in `dates/` change.

Features:

- **Fixed horizontal scale** so a year is always the same width and a whole
  lifespan fits on one screen. The scale is a single constant (`PX_PER_YEAR`),
  so a zoom control can be added later without restructuring.
- **Hierarchical category picker** — categories (one per YAML file) are grouped
  into themes (Rulers & Dynasties, Civilizations & Periods, Wars & Battles,
  Science & Technology, Arts & Letters, Thought & Religion, People, Events).
  Toggle whole themes or individual categories; a curated starter set is shown
  on first load.
- **Dynamic layout** — each visible category becomes a band whose entries are
  packed into the fewest non-overlapping rows, recomputed as you change the
  selection.
- **Detail on demand** — hover a bar for its name and dates; click to highlight.
- Bar colours reuse the print stylesheet from `template.svg` where defined, and
  fall back to a per-category hue otherwise.

Navigation:

- **Go to year** input — accepts `1776` or `44 BCE`
- Click-drag, mouse wheel, or arrow / PageUp / PageDown keys — pan in time
- Query string — open pre-centered, e.g. `web/index.html?year=1776`

Files
-----

- **timeline.py**: Generates a visual historical timeline. It calculates and
plots events spanning from 1740 BCE to 2100 CE, with a scale of 0.25 inches
per year.
- **long_time.py** `datetime.date` that functions for both BCE and CE.
- **viewer.html**: Browser-based viewer that stitches all generated
sheets into a single continuous timeline with horizontal scrolling and
year/sheet navigation.
- **export_web_data.py**: Exports all `dates/` entries to
`web/timeline_data.js` for the interactive web viewer, reusing `timeline.py`'s
data pipeline and resolving bar colours from `template.svg`.
- **web/index.html**: Interactive, screen-oriented timeline viewer with a
fixed time scale, a hierarchical category picker, and dynamic non-overlapping
layout. Reads `web/timeline_data.js`.
