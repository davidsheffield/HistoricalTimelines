"""
Tool to generate historical timeline SVGs. The timeline has 0.25 in per year with a printed area
of 10.5 in by 8 in on an 11 in by 8.5 in letter page.
"""

import argparse
import os
import pathlib

import pandas as pd
import yaml

import long_time


def timeline():
    """
    Main function to run the code to generate the historical timelines
    """

    parser = argparse.ArgumentParser(prog='timeline')
    sheet_group = parser.add_mutually_exclusive_group(required=True)
    sheet_group.add_argument('-a', '--all', action=argparse.BooleanOptionalAction)
    sheet_group.add_argument('--sheet', '-s', action='store', type=int, choices=range(1, 92))
    parser.add_argument('-d', '--debug', action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    if args.all:
        sheets = [1, 93]
    else:
        sheets = [args.sheet]

    dates = load_data()

    boxes = extract_dates(dates)

    make_svgs(sheets, boxes, args.debug)


def load_data():
    """
    Load date data from files
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


def make_svgs(sheets, boxes, debug=False, left_to_right=True):
    """
    Make SVG files from dates.

    24 pixels per year = 0.25 inches per year
    42 years per sheet = 10.5 inches per sheet
    768 pixels tall = 8 inches tall
    """

    dir_sheets = pathlib.Path(__file__).parent.joinpath('sheets')

    for sheet in sheets:
        years = get_years(sheet)
        start_year = era_year(years[0], space=False)
        end_year = era_year(years[-1], space=False)

        sheet_boxes = extract_sheet_boxes(boxes, years[0], years[-1], left_to_right)

        contents = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        contents += '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
        contents += '<svg width="1056" height="816" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        contents += """<style>
rect { stroke: none; }

rect.Party_Unaffiliated_Federalist { fill : #e8bfb1; }
rect.Party_Federalist { fill: #ea9978; }
rect.Party_Democratic-Republican { fill: #0044c9; }
rect.Party_National_Republican { fill: #0044c9; }
rect.Party_Democratic { fill: #0044c9; }
rect.Party_Whig { fill: #f0c862; }
rect.Party_Republican { fill: #e81b23; }

text.President {
    text-anchor: middle;
    dominant-baseline: middle;
    }
text.President {
    font-family: Palatino;
    font-size: 16px;
    fill: #ffffff;
    }
</style>
        """

        # Crop marks
        contents += '<g>\n'
        if debug:
            contents += '<g>\n'
            contents += f'<rect fill="#666666" stroke="none" x="20" y="20" width="4" height="4"/>\n'
            contents += f'<rect fill="#666666" stroke="none" x="1032" y="20" width="4" height="4"/>\n'
            contents += f'<rect fill="#666666" stroke="none" x="20" y="792" width="4" height="4"/>\n'
            contents += f'<rect fill="#666666" stroke="none" x="1032" y="792" width="4" height="4"/>\n'
            contents += '</g>\n'
        # Top left crop marks
        contents += '<g>\n'
        contents += '<rect fill="#000000" stroke="none" x="23" y="8" width="1" height="12"/>\n'
        contents += '<rect fill="#000000" stroke="none" x="8" y="23" width="12" height="1"/>\n'
        contents += '</g>\n'
        # Top right crop marks
        contents += '<g>\n'
        contents += '<rect fill="#000000" stroke="none" x="1032" y="8" width="1" height="12"/>\n'
        contents += '<rect fill="#000000" stroke="none" x="1036" y="23" width="12" height="1"/>\n'
        contents += '</g>\n'
        # Bottom left crop marks
        contents += '<g>\n'
        contents += '<rect fill="#000000" stroke="none" x="23" y="796" width="1" height="12"/>\n'
        contents += '<rect fill="#000000" stroke="none" x="8" y="792" width="12" height="1"/>\n'
        contents += '</g>\n'
        # Bottom right crop marks
        contents += '<g>\n'
        contents += '<rect fill="#000000" stroke="none" x="1032" y="796" width="1" height="12"/>\n'
        contents += '<rect fill="#000000" stroke="none" x="1036" y="792" width="12" height="1"/>\n'
        contents += '</g>\n'
        contents += '</g>\n'

        # Years
        contents += '<g>\n'
        ordered_years = years if left_to_right else reversed(years)
        for i, year in enumerate(ordered_years):
            if i % 2 == 0:
                color = '#eeeeee'
            else:
                color = '#dddddd'
            x = i * 24 + 24
            contents += f'<rect fill="{color}" stroke="none" x="{x}" y="6" width="24" height="12"/>\n'
            contents += f'<text x="{x + 3}" y="14" style="font-family:Optima; font-size:8px">{year}</text>\n'
            if debug:
                contents += f'<rect fill="{color}" stroke="none" x="{x}" y="24" width="24" height="768"/>\n'
        contents += '</g>\n'

        for year in years:
            abs_year = abs(year)
            if abs_year % 50 == 0:
                x = (years[-1] - year) * 24 + 24 + 12
                contents += f'<text x="{x}" y="790" text-anchor="middle" style="font-family:Optima; font-size:12px">{abs_year}</text>\n'
                # contents += f'<line x1="{x}" y1="0" x2="{x}" y2="900" stroke="#0000ff" stroke-width="1" />\n'
                # contents += f'<line x1="{(years[-1] - year) * 24 + 24}" y1="0" x2="{(years[-1] - year) * 24 + 24}" y2="900" stroke="#0000ff" stroke-width="1" />\n'
                # contents += f'<line x1="{(years[-1] - year + 1) * 24 + 24}" y1="0" x2="{(years[-1] - year + 1) * 24 + 24}" y2="900" stroke="#0000ff" stroke-width="1" />\n'

        contents += '<g>\n'
        # Draw boxes
        for idx, row in sheet_boxes.iterrows():
            if left_to_right:
                x = row['start_x']
                width = row['end_x'] - row['start_x']
            else:
                x = row['end_x']
                width = row['start_x'] - row['end_x']
            y = row['y'] * 24 + 24
            classes = ' '.join(row['Keywords'])
            contents += f'<rect x="{x}" y="{y}" width="{width}" height="24" class="{classes}"/>\n'
            middle_x = (row['start_x'] + row['end_x']) / 2
            label = row['Label']
            contents += f'<text x="{middle_x}" y="{y + 12}" class="{classes}">{label}</text>\n'
        contents += '</g>\n'

        contents += '</svg>\n'

        with open(dir_sheets.joinpath(f'Sheet_{sheet}_{start_year}_{end_year}.svg'), 'w') as file:
            file.write(contents)


def get_years(sheet):
    """
    Get the list of years for a sheet.
    """

    start_year = 2100 - sheet * 42
    if sheet <= 50:
        start_year += 1
    end_year = start_year + 42
    years = list(range(start_year, end_year))
    return years


def era_year(year, space=True):
    """
    Add the era to a year based on positive or negative
    """

    if space:
        spacer = ' '
    else:
        spacer = ''

    if year > 0:
        return f'{year}{spacer}CE'
    else:
        return f'{abs(year)}{spacer}BCE'


def extract_dates(dates):
    """
    Extract dates and create data frames with boxes and lables
    """

    boxes = []

    for idx, row in dates['presidents'].iterrows():
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
                      'Start': start_date,
                      'End': end_date,
                      'y': 0.5,
                      'Gradient': 0})

    boxes = pd.DataFrame(boxes)
    return boxes


def extract_sheet_boxes(boxes, start_year, end_year, left_to_right):
    """
    Filter boxes to only those that will appear in the sheet and calculate the positions.
    """

    sheet_boxes = boxes.loc[(boxes['Start'] <= long_time.date.fromisoformat(f'{end_year}-12-31'))
                            & (boxes['End'] >= long_time.date.fromisoformat(f'{start_year}-01-01'))].copy()

    sheet_boxes['start_x'] = sheet_boxes['Start'].apply(calculate_x, args=(start_year, end_year, left_to_right))
    sheet_boxes['end_x'] = sheet_boxes['End'].apply(calculate_x, args=(start_year, end_year, left_to_right))
    
    return sheet_boxes


def calculate_x(date, start_year, end_year, left_to_right):
    """
    Calculate the x positions of a date
    """

    years_since_start = date.year - start_year + (date.ordinal_day() - 1) / (date.days_in_year() - 1)
    if left_to_right:
        return 24 + years_since_start * 24
    else:
        return 1032 - years_since_start * 24


if __name__ == '__main__':
    timeline()
