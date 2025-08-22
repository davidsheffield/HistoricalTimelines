"""
Historical Timeline SVG Generator

Generates printable historical timeline sheets spanning from 1740 BCE
to 2100 CE. Each sheet covers 42 years with a scale of 0.25 inches per year
(24 pixels per year), designed for a 10.5 in by 8 in printable area on
11 in by 8.5 in letter paper.

The timeline uses a reverse chronological sheet numbering system:
- Sheet 1: 2058-2100 CE (most recent)
- Sheet 92: 1782-1740 BCE (oldest)

Features:
- Processes YAML data files containing historical events
- Generates SVG files with color-coded periods and labels
- Embedded CSS styling for different historical categories

Usage:
    python timeline.py -s 50               # Generate specific sheet
    python timeline.py --all               # Generate all sheets
    python timeline.py --sheet 50 --debug  # Debug mode with guides

Output:
    SVG files in sheets/ directory named: Sheet_{number}_{start_year}_{end_year}.svg
"""

import argparse
import logging
import os
import pathlib
from string import Template

import pandas as pd
import yaml

import long_time


logger = logging.getLogger(__name__)


def timeline() -> None:
    """
    Main entry point for generating historical timeline SVGs.

    Parses command line arguments and orchestrates the timeline generation
    process. Supports generating individual sheets or all sheets at once,
    with optional debug mode.

    Command line arguments:
        --sheet, -s: Generate specific sheet number (1-91)
        --all, -a: Generate all timeline sheets
        --debug, -d: Enable debug mode with visual guides

    Examples:
        >>> # Generate sheet 50 (around 1 CE)
        >>> python timeline.py --sheet 50
        >>>
        >>> # Generate all sheets
        >>> python timeline.py --all
        >>>
        >>> # Generate with debug guides
        >>> python timeline.py --sheet 1 --debug
    """

    parser = argparse.ArgumentParser(prog='timeline')
    sheet_group = parser.add_mutually_exclusive_group(required=True)
    sheet_group.add_argument('-a', '--all', action=argparse.BooleanOptionalAction)
    sheet_group.add_argument('--sheet', '-s', action='store', type=str)
    parser.add_argument('-d', '--debug', action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    if args.all:
        sheets = [1, 93]
    else:
        sheets = parse_sheet_ranges(args.sheet)

    dates = load_data()

    boxes = extract_dates(dates)

    make_svgs(sheets, boxes, args.debug)


def parse_sheet_ranges(range_string: str) -> list[int]:
    """
    Parse sheet range string into list of sheet numbers.

    Supports single numbers and ranges separated by commas.
    Ranges are specified with dashes (e.g., '1-3' becomes [1,2,3]).

    Args:
        range_string: String like '1', '2-4', '1-3,5', or '1-2,4-5'

    Returns:
        list[int]: List of sheet numbers in ascending order

    Raises:
        ValueError: If range format is invalid or numbers are out of bounds

    Examples:
        >>> parse_sheet_ranges('1')
        [1]
        >>> parse_sheet_ranges('2-4')
        [2, 3, 4]
        >>> parse_sheet_ranges('1-3,5')
        [1, 2, 3, 5]
        >>> parse_sheet_ranges('1-2,4-5')
        [1, 2, 4, 5]
    """

    if not range_string.strip():
        raise ValueError('Empty range string')

    sheets = set()

    # Split by commas to handle multiple ranges
    for part in range_string.split(','):
        part = part.strip()
        if not part:
            raise ValueError('Invalid sheet number')

        if '-' in part:
            # Handle range like '2-4'
            try:
                start_str, end_str = part.split('-', 1)
                start_str = start_str.strip()
                end_str = end_str.strip()

                if not start_str or not end_str:
                    raise ValueError(f'Invalid range format: {part}')

                start = int(start_str)
                end = int(end_str)

                if start > end:
                    raise ValueError(f'Invalid range {part}: start {start} > end {end}')

                sheets.update(range(start, end + 1))

            except ValueError as e:
                if 'invalid literal' in str(e):
                    raise ValueError(f'Invalid range format: {part}')
                raise

        else:
            # Handle single number like '1'
            try:
                sheet = int(part)
                sheets.add(sheet)
            except ValueError:
                raise ValueError(f'Invalid sheet number: {part}')

    # Validate all sheet numbers are in valid range
    for sheet in sheets:
        if sheet < 1 or sheet > 91:
            raise ValueError(f'Sheet number {sheet} out of range (1-91)')

    return sorted(list(sheets))


def load_data() -> dict[str, pd.DataFrame]:
    """
    Load historical event data from YAML files in the dates/ directory.

    Scans the dates/ directory for .yaml files and loads them into pandas DataFrames.

    Returns:
        dict[str, pd.DataFrame]: Dictionary mapping file stems to DataFrames
    """

    dir_dates = pathlib.Path(__file__).parent.joinpath('dates')
    dates = {}

    for file in os.listdir(dir_dates):
        file = pathlib.Path(file)
        if file.suffix != '.yaml':
            continue
        with open(dir_dates.joinpath(file), 'r') as f:
            df = pd.DataFrame(yaml.safe_load(f))
            dates[file.stem] = df
    return dates


def make_svgs(sheets: list[int],
              boxes: pd.DataFrame,
              debug: bool = False,
              left_to_right: bool = True) -> None:
    """
    Generate SVG timeline files from processed historical data.

    Creates SVG files with embedded styling, crop marks, year labels,
    and historical event boxes. The coordinate system uses 24 pixels per year
    to achieve 0.25 inches per year when printed.

    Args:
        sheets: List of sheet numbers to generate (1-91)
        boxes: DataFrame containing processed historical events with columns:
               ['Label', 'Keywords', 'Params', 'Start', 'End', 'y', 'Gradient']
        debug: If True, adds visual guides and corner markers
        left_to_right: If True, timeline flows left to right; if False, right to left

    Technical specs:
        - 24 pixels per year = 0.25 inches per year at 96 DPI
        - 42 years per sheet = 1008 pixels = 10.5 inches width
        - 768 pixels height = 8 inches tall
        - Total canvas: 1056x816 pixels (11"x8.5")

    Output files:
        Generated in sheets/ directory as: Sheet_{number}_{start_year}_{end_year}.svg
    """

    # Load the SVG template
    template_path = pathlib.Path(__file__).parent.joinpath('template.svg')
    with open(template_path, 'r') as f:
        template_content = f.read()

    template = Template(template_content)
    dir_sheets = pathlib.Path(__file__).parent.joinpath('sheets')

    for sheet in sheets:
        years = get_years(sheet)
        start_year = era_year(years[0], space=False)
        end_year = era_year(years[-1], space=False)

        sheet_boxes = extract_sheet_boxes(boxes, years[0], years[-1], left_to_right)

        # Generate template substitutions
        debug_corners = _generate_debug_corners() if debug else ''
        year_labels = _generate_year_labels(years, left_to_right, debug)
        year_markers = _generate_year_markers(years)
        timeline_boxes = _generate_timeline_boxes(sheet_boxes, left_to_right)

        # Substitute template variables
        svg_content = template.substitute(
            debug_corners=debug_corners,
            year_labels=year_labels,
            year_markers=year_markers,
            timeline_boxes=timeline_boxes
        )

        with open(dir_sheets.joinpath(f'Sheet_{sheet}_{start_year}_{end_year}.svg'), 'w') as file:
            file.write(svg_content)


def _generate_debug_corners() -> str:
    """Generate debug corner markers for template substitution."""
    return '''<g>
<rect fill="#666666" stroke="none" x="20" y="20" width="4" height="4"/>
<rect fill="#666666" stroke="none" x="1032" y="20" width="4" height="4"/>
<rect fill="#666666" stroke="none" x="20" y="792" width="4" height="4"/>
<rect fill="#666666" stroke="none" x="1032" y="792" width="4" height="4"/>
</g>'''


def _generate_year_labels(years: list[int], left_to_right: bool, debug: bool) -> str:
    """Generate year label elements for template substitution."""
    content = []
    ordered_years = years if left_to_right else reversed(years)

    for i, year in enumerate(ordered_years):
        color = '#eeeeee' if i % 2 == 0 else '#dddddd'
        x = i * 24 + 24
        content.append(f'<rect fill="{color}" stroke="none" x="{x}" y="6" width="24" height="12"/>')
        content.append(f'<text x="{x + 3}" y="14" style="font-family:Optima; font-size:8px">{year}</text>')
        if debug:
            content.append(f'<rect fill="{color}" stroke="none" x="{x}" y="24" width="24" height="768"/>')

    return '\n'.join(content)


def _generate_year_markers(years: list[int]) -> str:
    """Generate 50-year interval markers for template substitution."""
    content = []

    for year in years:
        abs_year = abs(year)
        if abs_year % 50 == 0:
            x = (years[-1] - year) * 24 + 24 + 12
            content.append(f'<text x="{x}" y="790" text-anchor="middle" style="font-family:Optima; font-size:12px">{abs_year}</text>')

    return '\n'.join(content)


def _calculate_font_size(label: str,
                         box_width: float,
                         max_font_size: int = 16,
                         min_font_size: int = 8) -> int:
    """
    Calculate appropriate font size for a label to fit within a box.

    Args:
        label: Text label to display
        box_width: Width of the box in pixels
        max_font_size: Maximum font size to use (current standard)
        min_font_size: Minimum font size for readability

    Returns:
        int: Font size in pixels that should fit the label in the box
    """
    if not label.strip():
        return max_font_size

    # Estimate character width as 55% of font size
    char_width_ratio = 0.55
    # Use 95% of box width to allow some padding
    usable_width = box_width * 0.95

    # Calculate font size needed to fit text
    estimated_font_size = usable_width / (len(label) * char_width_ratio)

    # Log warning if estimated font size is below minimum
    if estimated_font_size < min_font_size:
        logger.warning(
            f"Label '{label}' may not fit properly in box (width: {box_width}px). "
            f"Estimated font size {estimated_font_size:.1f}px is below minimum {min_font_size}px."
        )

    # Clamp to min/max bounds
    font_size = max(min_font_size, min(max_font_size, estimated_font_size))

    return font_size


def _generate_timeline_boxes(sheet_boxes: pd.DataFrame, left_to_right: bool) -> str:
    """Generate timeline box elements for template substitution."""
    content = []

    for idx, row in sheet_boxes.iterrows():
        if left_to_right:
            x = row['start_x']
            width = row['end_x'] - row['start_x']
        else:
            x = row['end_x']
            width = row['start_x'] - row['end_x']

        y = row['y'] * 24 + 24
        classes = ' '.join(row['Keywords'])

        content.append(f'<rect x="{x}" y="{y}" width="{width}" height="24" class="{classes}"/>')

        # Check if border is needed (draw after main rect so it appears on top)
        params = row.get('Params', [])
        if not isinstance(params, list):
            params = []
        if 'border_left' in params:
            # Find the party class to determine border style
            party_class = None
            for keyword in row['Keywords']:
                if keyword.startswith('Party_'):
                    party_class = keyword
                    break

            if party_class:
                border_classes = f'border {party_class}'
                content.append(f'<rect x="{x}" y="{y}" width="2" height="24" class="{border_classes}"/>')

        middle_x = (row['start_x'] + row['end_x']) / 2
        label = row['Label']

        # Determine label position based on params
        label_position = None
        for param in params:
            if param.startswith('label_position:'):
                label_position = param.split(':', 1)[1]
                break

        # Calculate font size, y position, and classes based on label_position
        text_y = y + 12  # Default: middle of box
        text_classes = classes
        if label_position == 'above':
            text_y -= 24
            font_size = 16  # Default font size
            text_classes += ' outside_label'
        elif label_position == 'below':
            text_y += 24
            font_size = 16  # Default font size
            text_classes += ' outside_label'
        else:
            font_size = _calculate_font_size(label, width)

        content.append(f'<text x="{middle_x}" y="{text_y}" class="{text_classes}" style="font-size:{font_size}px">{label}</text>')

    return '\n'.join(content)


def get_years(sheet: int) -> list[int]:
    """
    Calculate the range of years covered by a specific timeline sheet.

    Uses reverse chronological numbering where sheet 1 covers the most recent
    years. Sheet numbering accounts for the transition from BCE to CE between
    sheets 50 and 51.

    Args:
        sheet: Sheet number (1-91)

    Returns:
        list[int]: List of years in chronological order
                  Negative years represent BCE dates
    """

    start_year = 2100 - sheet * 42
    if sheet <= 50:
        start_year += 1
    end_year = start_year + 42
    years = list(range(start_year, end_year))
    return years


def era_year(year: int, space: bool = True) -> str:
    """
    Format a year with its historical era designation (BCE/CE).

    Converts numeric years to human-readable format with era labels.
    Positive years become CE, negative years become BCE.

    Args:
        year: Year as integer (negative for BCE, positive for CE)
        space: If True, adds space between year and era ("1 CE")
               If False, no space ("1CE")

    Returns:
        str: Formatted year string with era designation
    """

    if space:
        spacer = ' '
    else:
        spacer = ''

    if year > 0:
        return f'{year}{spacer}CE'
    else:
        return f'{abs(year)}{spacer}BCE'


def extract_dates(dates: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Process raw historical data into timeline boxes for visualization.

    Converts date strings to long_time.date objects and adds positioning
    information.

    Args:
        dates: Dictionary of DataFrames loaded from YAML files
               Each DataFrame should have columns: ['Label', 'Start', 'End', 'Keywords', 'Params']

    Returns:
        pd.DataFrame: Processed timeline data with columns:
                     - Label: Event description
                     - Keywords: List of CSS classes for styling
                     - Params: List of functional parameters (e.g., border_left)
                     - Start: long_time.date object for start date
                     - End: long_time.date object for end date
                     - y: Vertical position (0.5 for center)
                     - Gradient: Styling gradient value (0)
    """

    boxes = []

    for idx, row in dates['US_presidents'].iterrows():
        try:
            start_date = long_time.date.fromisoformat(row['Start'])
        except TypeError:
            start_date = long_time.date.fromdatetime(row['Start'])
        try:
            end_date = long_time.date.fromisoformat(row['End'])
        except TypeError:
            end_date = long_time.date.fromdatetime(row['End'])

        boxes.append({'Label': row['Label'],
                      'Keywords': row['Keywords'],
                      'Params': row.get('Params', []),
                      'Start': start_date,
                      'End': end_date,
                      'y': 0.5,
                      'Gradient': 0})

    boxes = pd.DataFrame(boxes)
    return boxes


def extract_sheet_boxes(boxes: pd.DataFrame,
                        start_year: int,
                        end_year: int,
                        left_to_right: bool) -> pd.DataFrame:
    """
    Filter and position historical events for a specific timeline sheet.

    Selects events that overlap with the sheet's time range and calculates their
    horizontal positions in the SVG coordinate system.

    Args:
        boxes: DataFrame of all historical events
        start_year: First year covered by this sheet
        end_year: Last year covered by this sheet
        left_to_right: Direction of timeline flow

    Returns:
        pd.DataFrame: Filtered events with added columns:
                     - start_x: X coordinate of event start (pixels)
                     - end_x: X coordinate of event end (pixels)

    Note:
        Events are included if they overlap the sheet period, even partially.
        X coordinates use 24 pixels per year scale with 24-pixel left margin.
    """

    sheet_boxes = boxes.loc[(boxes['Start'] <= long_time.date.fromisoformat(f'{end_year}-12-31'))
                            & (boxes['End'] >= long_time.date.fromisoformat(f'{start_year}-01-01'))].copy()

    sheet_boxes['start_x'] = sheet_boxes['Start'].apply(calculate_x, args=(start_year, end_year, left_to_right))
    sheet_boxes['end_x'] = sheet_boxes['End'].apply(calculate_x, args=(start_year, end_year, left_to_right))

    return sheet_boxes


def calculate_x(date: 'long_time.date', start_year: int, end_year: int, left_to_right: bool) -> float:
    """
    Calculate the horizontal pixel position of a date within a timeline sheet.

    Converts a date to its x coordinate in the SVG coordinate system, accounting
    for the sheet's time range and layout direction.

    Args:
        date: The date to position
        start_year: First year of the sheet's time range
        end_year: Last year of the sheet's time range (exclusive)
        left_to_right: If True, earlier dates appear on the left
                       If False, earlier dates appear on the right

    Returns:
        float: x coordinate in pixels from the left edge of the SVG
               Range: 24 to 1032 pixels (accounting for margins)

    Calculation:
        - Determines fractional years since start using ordinal day within year
        - Applies 24 pixels per year scale
        - Adds 24-pixel left margin
        - Reverses for right-to-left layout
    """

    years_since_start = date.year - start_year + (date.ordinal_day() - 1) / (date.days_in_year() - 1)
    if left_to_right:
        return 24 + years_since_start * 24
    else:
        return 1032 - years_since_start * 24


if __name__ == '__main__':
    timeline()
