"""
Test the file timeline.py
"""

import pytest

import long_time
import timeline


@pytest.mark.parametrize('sheet,expected',
                         [(1, list(range(2059, 2101))),
                          (2, list(range(2017, 2059))),
                          (50, list(range(1, 43))),
                          (51, list(range(-42, 0)))])
def test_get_years(sheet, expected):
    assert timeline.get_years(sheet) == expected

@pytest.mark.parametrize('year,expected',
                         [(1, '1 CE'),
                          (-1, '1 BCE')])
def test_era_year(year, expected):
    assert timeline.era_year(year) == expected

@pytest.mark.parametrize('year,expected',
                         [(1, '1CE'),
                          (-1, '1BCE')])
def test_era_year__no_space(year, expected):
    assert timeline.era_year(year, False) == expected

@pytest.mark.parametrize('date,start_year,end_year,left_to_right,expected',
                         [(long_time.date(1975, 1, 1, True), 1975, 2016, True, 24), # Left edge of the sheet
                          (long_time.date(1976, 1, 1, True), 1975, 2016, True, 48), # Next year in
                          (long_time.date(1974, 1, 1, True), 1975, 2016, True, 0), # One year earlier
                          (long_time.date(1975, 7, 15, True), 1975, 2016, True, 36.85714285714286), # Middle of middle month
                          (long_time.date(2016, 1, 1, True), 1975, 2016, True, 1008), # Last year on sheet
                          (long_time.date(2016, 12, 31, True), 1975, 2016, True, 1032), # Right edge of the sheet
                          (long_time.date(2017, 1, 1, True), 1975, 2016, True, 1032), # Just after
                          (long_time.date(2017, 12, 31, True), 1975, 2016, True, 1056), # One year after
                          (long_time.date(1975, 1, 1, True), 1975, 2016, False, 1032)]) # Right edge for right to left
def test_calculate_x(date, start_year, end_year, left_to_right, expected):
    assert timeline.calculate_x(date, start_year, end_year, left_to_right) == expected
