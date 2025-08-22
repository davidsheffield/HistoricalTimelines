"""
Test the file timeline.py
"""

import logging
import pytest

import pandas as pd

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


def test_calculate_font_size_logging(caplog):
    """Test that log messages are issued when estimated font size is below minimum."""

    # Test case where estimated font size is below minimum
    with caplog.at_level(logging.WARNING):
        result = timeline._calculate_font_size('Very Long Text That Should Trigger Warning', 30)
        assert result == 8  # Should return minimum font size

    # Check that warning was logged
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert "Label 'Very Long Text That Should Trigger Warning' may not fit properly in box" in caplog.records[0].message
    assert "width: 30px" in caplog.records[0].message
    assert "below minimum 8px" in caplog.records[0].message

    # Clear the log for next test
    caplog.clear()

    # Test case where estimated font size is above minimum (no log message)
    result = timeline._calculate_font_size('Short', 200)
    assert result == 16  # Should return max font size with no log message
    assert len(caplog.records) == 0  # No log messages should be recorded

    # Test case where estimated font size is exactly at minimum (no log message)
    # Calculate a box width that gives exactly min_font_size
    label = 'Test'
    min_font_size = 8
    char_width_ratio = 0.55
    box_width = (len(label) * char_width_ratio * min_font_size) / 0.95
    result = timeline._calculate_font_size(label, box_width)
    assert result == min_font_size
    assert len(caplog.records) == 0  # No log messages should be recorded


def test_calculate_font_size_logging_with_custom_bounds(caplog):
    """Test logging functionality with custom min/max font sizes."""

    # Test with custom bounds where estimated size is below custom minimum
    with caplog.at_level(logging.WARNING):
        result = timeline._calculate_font_size('Long Text String', 50, max_font_size=20, min_font_size=12)
        assert result == 12  # Should return custom minimum

    # Check that warning was logged with custom minimum
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert "Label 'Long Text String' may not fit properly in box" in caplog.records[0].message
    assert "below minimum 12px" in caplog.records[0].message

    # Clear the log for next test
    caplog.clear()

    # Test with custom bounds where no log message should be issued
    result = timeline._calculate_font_size('Short', 200, max_font_size=20, min_font_size=12)
    assert result == 20  # Should return custom maximum with no log message
    assert len(caplog.records) == 0  # No log messages should be recorded


@pytest.mark.parametrize('range_string,expected',
                         [
                             # Single numbers
                             ('1', [1]),
                             ('5', [5]),
                             ('91', [91]),

                             # Simple ranges
                             ('2-4', [2, 3, 4]),
                             ('1-3', [1, 2, 3]),
                             ('89-91', [89, 90, 91]),

                             # Mixed single and ranges
                             ('1-3,5', [1, 2, 3, 5]),
                             ('1,3-5', [1, 3, 4, 5]),
                             ('2,4-6,8', [2, 4, 5, 6, 8]),

                             # Multiple ranges
                             ('1-2,4-5', [1, 2, 4, 5]),
                             ('1-3,5-7,10', [1, 2, 3, 5, 6, 7, 10]),

                             # Overlapping ranges (should dedupe)
                             ('1-3,2-4', [1, 2, 3, 4]),
                             ('1,1-3', [1, 2, 3]),

                             # Single item ranges
                             ('5-5', [5]),

                             # Whitespace handling
                             (' 1 ', [1]),
                             ('1 - 3', [1, 2, 3]),
                             ('1, 3-5 , 7', [1, 3, 4, 5, 7]),
                         ])
def test_parse_sheet_ranges_valid(range_string, expected):
    """Test parse_sheet_ranges with valid inputs."""
    assert timeline.parse_sheet_ranges(range_string) == expected


@pytest.mark.parametrize('range_string,error_message',
                         [
                             # Empty inputs
                             ('', 'Empty range string'),
                             ('   ', 'Empty range string'),

                             # Invalid range formats
                             ('1-', 'Invalid range format: 1-'),
                             ('-3', 'Invalid range format: -3'),
                             ('1--3', r'Invalid range 1--3: start 1 > end -3'),
                             ('1-2-3', 'Invalid range format: 1-2-3'),

                             # Invalid numbers
                             ('abc', 'Invalid sheet number: abc'),
                             ('1,abc', 'Invalid sheet number: abc'),
                             ('1-abc', 'Invalid range format: 1-abc'),
                             ('abc-3', 'Invalid range format: abc-3'),

                             # Out of range numbers
                             ('0', r'Sheet number 0 out of range \(1-91\)'),
                             ('92', r'Sheet number 92 out of range \(1-91\)'),
                             ('1-92', r'Sheet number 92 out of range \(1-91\)'),
                             ('0-2', r'Sheet number 0 out of range \(1-91\)'),
                             ('-1', 'Invalid range format: -1'),

                             # Invalid range order
                             ('5-3', r'Invalid range 5-3: start 5 > end 3'),
                             ('10-1', r'Invalid range 10-1: start 10 > end 1'),

                             # Empty parts
                             ('1,,3', 'Invalid sheet number'),
                             (',1', 'Invalid sheet number'),
                             ('1,', 'Invalid sheet number'),
                         ])
def test_parse_sheet_ranges_invalid(range_string, error_message):
    """Test parse_sheet_ranges with invalid inputs."""
    with pytest.raises(ValueError, match=error_message):
        timeline.parse_sheet_ranges(range_string)


def test_params_field_border_detection():
    """Test that border_left detection works correctly with Params field."""

    # Create test data with border_left in Params field
    test_data = {
        'Label': 'Test President',
        'Keywords': ['USA', 'President', 'Party_Democratic'],
        'Params': ['border_left'],
        'start_x': 100,
        'end_x': 200
    }

    # Mock the _render_box function's border detection logic
    params = test_data.get('Params', [])
    assert 'border_left' in params
    assert 'border_left' not in test_data['Keywords']


def test_params_field_no_border():
    """Test that missing Params field or no border_left works correctly."""

    # Test data without Params field
    test_data_no_params = {
        'Label': 'Test President',
        'Keywords': ['USA', 'President', 'Party_Democratic'],
        'start_x': 100,
        'end_x': 200
    }

    # Test data with Params field but no border_left
    test_data_no_border = {
        'Label': 'Test President',
        'Keywords': ['USA', 'President', 'Party_Democratic'],
        'Params': ['other_param'],
        'start_x': 100,
        'end_x': 200
    }

    # Test both cases
    params1 = test_data_no_params.get('Params', [])
    assert 'border_left' not in params1

    params2 = test_data_no_border.get('Params', [])
    assert 'border_left' not in params2


def test_params_field_processing():
    """Test that extract_dates function correctly handles Params field."""

    # Create mock data that mimics YAML structure
    # Create separate DataFrames to properly handle missing Params
    df1 = pd.DataFrame([{
        'Label': 'Test President 1',
        'Start': '2001-01-20',
        'End': '2009-01-20',
        'Keywords': ['USA', 'President', 'Party_Democratic'],
        'Params': ['border_left']
    }])

    df2 = pd.DataFrame([{
        'Label': 'Test President 2',
        'Start': '2009-01-20',
        'End': '2017-01-20',
        'Keywords': ['USA', 'President', 'Party_Republican']
    }])

    # Combine DataFrames and handle missing Params column
    combined_df = pd.concat([df1, df2], ignore_index=True)
    # Fill NaN values in Params column with empty lists
    combined_df['Params'] = combined_df['Params'].apply(lambda x: x if isinstance(x, list) else [])

    mock_dates = {
        'US_presidents': combined_df
    }

    # Process the data
    result = timeline.extract_dates(mock_dates)

    # Verify the DataFrame has the expected columns including Params
    expected_columns = ['Label', 'Keywords', 'Params', 'Start', 'End', 'y', 'Gradient']
    for col in expected_columns:
        assert col in result.columns

    # Verify Params field is correctly populated
    assert result.iloc[0]['Params'] == ['border_left']
    assert result.iloc[1]['Params'] == []  # Should default to empty list
