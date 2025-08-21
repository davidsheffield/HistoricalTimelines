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


@pytest.mark.parametrize('label,box_width,expected',
                         [
                             # Test with default max/min font sizes (16px max, 8px min)
                             ('Short', 200, 16),  # Wide box, short text -> max font size
                             ('Very Long Presidential Name', 50, 8),  # Narrow box, long text -> min font size
                             ('Medium', 96, 16),  # Standard 4-year presidency box, medium text -> max font size
                             ('Franklin Delano Roosevelt', 291, 16),  # Long name, wide box (12+ year presidency) -> max font size
                             ('George H W Bush', 96, 11.054545454545453),  # Long name, standard box -> calculated size
                             ('Lyndon Baines Johnson', 124, 10.199134199134198),  # Very long name, medium box -> calculated size
                             ('John F Kennedy', 68, 8.389610389610388),  # Medium name, narrow box -> min font size
                             ('Obama', 192, 16),  # Short name, wide box -> max font size
                             ('', 100, 16),  # Empty string -> max font size
                             ('   ', 100, 16),  # Whitespace only -> max font size
                         ])
def test_calculate_font_size_defaults(label, box_width, expected):
    """Test _calculate_font_size with default parameters."""
    result = timeline._calculate_font_size(label, box_width)
    assert result == expected


@pytest.mark.parametrize('label,box_width,max_font,min_font,expected',
                         [
                             # Test with custom max/min font sizes
                             ('Test', 200, 20, 10, 20),  # Wide box -> custom max
                             ('Very Very Long Text Here', 50, 20, 10, 10),  # Narrow box -> custom min
                             ('Medium Text', 100, 12, 6, 12),  # Medium box with custom bounds -> custom max
                             ('Longer Text String', 80, 12, 6, 7.6767676767676765),  # Calculated size within custom bounds
                         ])
def test_calculate_font_size_custom_bounds(label, box_width, max_font, min_font, expected):
    """Test _calculate_font_size with custom max and min font sizes."""
    result = timeline._calculate_font_size(label, box_width, max_font, min_font)
    assert result == expected


def test_calculate_font_size_edge_cases():
    """Test _calculate_font_size with edge cases and boundary conditions."""

    # Very wide box should always return max font size
    assert timeline._calculate_font_size('Any Text', 1000) == 16

    # Very narrow box should always return min font size
    assert timeline._calculate_font_size('Any Text', 10) == 8

    # Single character should get max font size in reasonable box
    assert timeline._calculate_font_size('A', 100) == 16

    # Zero width box should return min font size
    assert timeline._calculate_font_size('Test', 0) == 8

    # Negative width box should return min font size
    assert timeline._calculate_font_size('Test', -10) == 8


def test_calculate_font_size_formula_consistency():
    """Test that the font size calculation formula works consistently."""

    # Test that the formula: usable_width / (len(label) * char_width_ratio)
    # With usable_width = box_width * 0.95 and char_width_ratio = 0.55

    label = 'TestLabel'  # 9 characters
    box_width = 100

    expected_usable_width = box_width * 0.95  # 95
    expected_char_width_ratio = 0.55
    expected_font_size = expected_usable_width / (len(label) * expected_char_width_ratio)
    expected_font_size = max(8, min(16, expected_font_size))  # Clamp to bounds
    expected_font_size = int(expected_font_size)

    result = timeline._calculate_font_size(label, box_width)
    assert result == expected_font_size
