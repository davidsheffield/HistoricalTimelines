"""
Test the file timeline.py
"""

import pytest

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
