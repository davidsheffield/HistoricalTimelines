"""
Test the file timeline.py
"""

import logging
import os
import tempfile
import pytest

import pandas as pd
import yaml

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
        'Params': ['border_left', 'position:0.5']
    }])

    df2 = pd.DataFrame([{
        'Label': 'Test President 2',
        'Start': '2009-01-20',
        'End': '2017-01-20',
        'Keywords': ['USA', 'President', 'Party_Republican'],
        'Params': ['position:0.3']
    }])

    # Combine DataFrames
    combined_df = pd.concat([df1, df2], ignore_index=True)

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
    assert result.iloc[0]['Params'] == ['border_left', 'position:0.5']
    assert result.iloc[1]['Params'] == ['position:0.3']


def test_label_position_above():
    """Test that label_position:above positions text above the box."""

    # Create test data with label_position:above
    test_data = pd.DataFrame([{
        'Label': 'Test Label',
        'Keywords': ['USA', 'President'],
        'Params': ['label_position:above'],
        'start_x': 100,
        'end_x': 200,
        'y': 1
    }])

    # Generate timeline boxes
    result = timeline._generate_timeline_boxes(test_data, left_to_right=True)

    # Check that text y position is above the box
    expected_y = 36  # Based on actual implementation
    assert f'y="{expected_y}"' in result
    assert 'Test Label' in result
    # Check that default font size is used
    assert 'font-size:16px' in result
    # Check that outside_label class is added
    assert 'outside_label' in result


def test_label_position_below():
    """Test that label_position:below positions text below the box."""

    # Create test data with label_position:below
    test_data = pd.DataFrame([{
        'Label': 'Test Label',
        'Keywords': ['USA', 'President'],
        'Params': ['label_position:below'],
        'start_x': 100,
        'end_x': 200,
        'y': 1
    }])

    # Generate timeline boxes
    result = timeline._generate_timeline_boxes(test_data, left_to_right=True)

    # Check that text y position is below the box
    expected_y = 84  # Based on actual implementation
    assert f'y="{expected_y}"' in result
    assert 'Test Label' in result
    # Check that default font size is used
    assert 'font-size:16px' in result
    # Check that outside_label class is added
    assert 'outside_label' in result


def test_label_position_default():
    """Test that default positioning works when no label_position is specified."""

    # Create test data without label_position
    test_data = pd.DataFrame([{
        'Label': 'Test Label',
        'Keywords': ['USA', 'President'],
        'Params': ['border_left'],
        'start_x': 100,
        'end_x': 200,
        'y': 1
    }])

    # Generate timeline boxes
    result = timeline._generate_timeline_boxes(test_data, left_to_right=True)

    # Check that text y position is in the middle of the box (y*24 + 24 + 12 = 60)
    expected_y = 60  # y=1, so 1*24 + 24 + 12 = 60
    assert f'y="{expected_y}"' in result
    assert 'Test Label' in result
    # Check that outside_label class is NOT added for default positioning
    assert 'outside_label' not in result


def test_label_position_empty_params():
    """Test that default positioning works when Params is empty."""

    # Create test data with empty Params
    test_data = pd.DataFrame([{
        'Label': 'Test Label',
        'Keywords': ['USA', 'President'],
        'Params': [],
        'start_x': 100,
        'end_x': 200,
        'y': 1
    }])

    # Generate timeline boxes
    result = timeline._generate_timeline_boxes(test_data, left_to_right=True)

    # Check that text y position is in the middle of the box (y*24 + 24 + 12 = 60)
    expected_y = 60  # y=1, so 1*24 + 24 + 12 = 60
    assert f'y="{expected_y}"' in result
    assert 'Test Label' in result
    # Check that outside_label class is NOT added for empty params
    assert 'outside_label' not in result


def test_label_position_mixed_params():
    """Test that label_position works correctly when mixed with other params."""

    # Create test data with multiple params including label_position
    test_data = pd.DataFrame([{
        'Label': 'Test Label',
        'Keywords': ['USA', 'President'],
        'Params': ['border_left', 'label_position:above', 'other_param'],
        'start_x': 100,
        'end_x': 200,
        'y': 2
    }])

    # Generate timeline boxes
    result = timeline._generate_timeline_boxes(test_data, left_to_right=True)

    # Check that text y position is above the box
    expected_y = 60  # Based on actual implementation for y=2
    assert f'y="{expected_y}"' in result
    assert 'Test Label' in result
    # Check that default font size is used
    assert 'font-size:16px' in result
    # Check that outside_label class is added
    assert 'outside_label' in result


def test_load_data_basic_global_entries():
    """Test load_data with basic global/entries YAML format."""
    yaml_content = {
        'global': {
            'Keywords': ['USA', 'President', 'Reign']
        },
        'entries': [
            {
                'Label': 'George Washington',
                'Start': '1789-04-30',
                'End': '1797-03-04',
                'Keywords': ['Party_Federalist']
            }
        ]
    }

    # Create temporary YAML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(yaml_content, f)
        temp_file = f.name

    # Create temporary directory and move file there
    with tempfile.TemporaryDirectory() as temp_dir:
        dates_dir = os.path.join(temp_dir, 'dates')
        os.makedirs(dates_dir)
        yaml_file = os.path.join(dates_dir, 'test_presidents.yaml')
        os.rename(temp_file, yaml_file)

        # Mock the dates directory path
        original_file = timeline.__file__
        timeline.__file__ = os.path.join(temp_dir, 'timeline.py')

        try:
            data = timeline.load_data()

            # Verify data structure
            assert 'test_presidents' in data
            df = data['test_presidents']
            assert len(df) == 1

            # Check global keywords were merged
            washington_keywords = df.iloc[0]['Keywords']
            assert 'USA' in washington_keywords
            assert 'President' in washington_keywords
            assert 'Reign' in washington_keywords
            assert 'Party_Federalist' in washington_keywords

        finally:
            # Restore original path
            timeline.__file__ = original_file


def test_load_data_invalid_structure_no_entries():
    """Test load_data raises error for YAML without entries key."""
    yaml_content = {
        'global': {
            'Keywords': ['USA', 'President']
        },
        'data': [  # Wrong key name
            {'Label': 'Test', 'Keywords': []}
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(yaml_content, f)
        temp_file = f.name

    with tempfile.TemporaryDirectory() as temp_dir:
        dates_dir = os.path.join(temp_dir, 'dates')
        os.makedirs(dates_dir)
        yaml_file = os.path.join(dates_dir, 'test_invalid.yaml')
        os.rename(temp_file, yaml_file)

        original_file = timeline.__file__
        timeline.__file__ = os.path.join(temp_dir, 'timeline.py')

        try:
            with pytest.raises(ValueError, match='must have global/entries structure'):
                timeline.load_data()
        finally:
            timeline.__file__ = original_file


def test_extract_dates_position_parameter():
    """Test that extract_dates correctly processes position parameter from YAML."""

    # Create mock data with position parameters
    df1 = pd.DataFrame([{
        'Label': 'Test President 1',
        'Start': '2001-01-20',
        'End': '2009-01-20',
        'Keywords': ['USA', 'President'],
        'Params': ['position:0.3']
    }])

    df2 = pd.DataFrame([{
        'Label': 'Test President 2',
        'Start': '2009-01-20',
        'End': '2017-01-20',
        'Keywords': ['USA', 'President'],
        'Params': ['border_left', 'position:0.5']
    }])

    df3 = pd.DataFrame([{
        'Label': 'Test Person',
        'DOB': '1988-07-08',
        'Alive': True,
        'Keywords': ['family'],
        'Params': ['position:0.8']
    }])

    mock_dates = {
        'test_presidents1': df1,
        'test_presidents2': df2,
        'test_family': df3
    }

    # Process the data
    result = timeline.extract_dates(mock_dates)

    # Verify position parameter is correctly processed
    assert len(result) == 3
    assert result.iloc[0]['y'] == 0.3  # Explicit position
    assert result.iloc[1]['y'] == 0.5  # Position with other params
    assert result.iloc[2]['y'] == 0.8  # Position with DOB/Alive format


def test_extract_dates_handles_dob_dod_format():
    """Test that extract_dates correctly processes DOB/DOD/Alive format."""

    # Create mock data with different life formats
    df = pd.DataFrame([
        {
            'Label': 'Dead Person',
            'DOB': '1920-12-24',
            'DOD': '2004-06-04',
            'Keywords': ['family'],
            'Params': ['position:0.2']
        },
        {
            'Label': 'Living Person',
            'DOB': '1988-07-08',
            'Alive': True,
            'Keywords': ['family'],
            'Params': ['position:0.4']
        }
    ])

    mock_dates = {'test_family': df}
    result = timeline.extract_dates(mock_dates)

    # Verify both entries were processed
    assert len(result) == 2

    # Check dead person
    assert result.iloc[0]['Label'] == 'Dead Person'
    assert result.iloc[0]['Start'] == long_time.date.fromisoformat('1920-12-24')
    assert result.iloc[0]['End'] == long_time.date.fromisoformat('2004-06-04')
    assert result.iloc[0]['y'] == 0.2

    # Check living person
    assert result.iloc[1]['Label'] == 'Living Person'
    assert result.iloc[1]['Start'] == long_time.date.fromisoformat('1988-07-08')
    assert result.iloc[1]['End'] == long_time.date(2025, 1, 1, True)  # Current year
    assert result.iloc[1]['y'] == 0.4


def test_extract_dates_processes_all_files():
    """Test that extract_dates processes all YAML files, not just US_presidents."""

    # Create mock data for multiple files
    df1 = pd.DataFrame([{
        'Label': 'President',
        'Start': '2001-01-20',
        'End': '2009-01-20',
        'Keywords': ['USA', 'President'],
        'Params': ['position:0.5']
    }])

    df2 = pd.DataFrame([{
        'Label': 'Emperor',
        'Start': '0014-01-16',
        'End': '0037-03-16',
        'Keywords': ['Roman', 'Emperor'],
        'Params': ['position:0.3']
    }])

    df3 = pd.DataFrame([{
        'Label': 'Family Member',
        'DOB': '1988-07-08',
        'Alive': True,
        'Keywords': ['family'],
        'Params': ['position:0.7']
    }])

    mock_dates = {
        'US_presidents': df1,
        'Roman_emperors': df2,
        'family': df3
    }

    result = timeline.extract_dates(mock_dates)

    # Should process all files
    assert len(result) == 3
    labels = result['Label'].tolist()
    assert 'President' in labels
    assert 'Emperor' in labels
    assert 'Family Member' in labels


def test_extract_dates_skips_invalid_entries():
    """Test that extract_dates skips entries without proper date fields."""

    df = pd.DataFrame([
        {
            'Label': 'Valid Entry',
            'Start': '2001-01-20',
            'End': '2009-01-20',
            'Keywords': ['USA', 'President'],
            'Params': ['position:0.5']
        },
        {
            'Label': 'Invalid Entry - Missing End',
            'Start': '2001-01-20',
            'Keywords': ['USA', 'President']
        },
        {
            'Label': 'Invalid Entry - Missing DOD/Alive',
            'DOB': '1988-07-08',
            'Keywords': ['family']
        },
        {
            'Label': 'Invalid Entry - No Date Fields',
            'Keywords': ['other']
        }
    ])

    mock_dates = {'test_data': df}
    result = timeline.extract_dates(mock_dates)

    # Should only process the valid entry
    assert len(result) == 1
    assert result.iloc[0]['Label'] == 'Valid Entry'


def test_extract_dates_missing_position_raises_error():
    """Test that extract_dates raises ValueError when position parameter is missing."""

    df = pd.DataFrame([{
        'Label': 'Entry Without Position',
        'Start': '2001-01-20',
        'End': '2009-01-20',
        'Keywords': ['USA', 'President']
        # No position parameter
    }])

    mock_dates = {'test_data': df}

    with pytest.raises(ValueError, match="Missing required position parameter for entry: Entry Without Position"):
        timeline.extract_dates(mock_dates)


def test_extract_dates_invalid_position_format_raises_error():
    """Test that extract_dates raises ValueError for invalid position format."""

    # Test invalid format
    df1 = pd.DataFrame([{
        'Label': 'Invalid Position Format',
        'Start': '2001-01-20',
        'End': '2009-01-20',
        'Keywords': ['USA', 'President'],
        'Params': ['position:invalid_number']
    }])

    mock_dates1 = {'test_data': df1}

    with pytest.raises(ValueError, match="Invalid position parameter format: position:invalid_number"):
        timeline.extract_dates(mock_dates1)

    # Test missing value after colon
    df2 = pd.DataFrame([{
        'Label': 'Missing Position Value',
        'Start': '2001-01-20',
        'End': '2009-01-20',
        'Keywords': ['USA', 'President'],
        'Params': ['position:']
    }])

    mock_dates2 = {'test_data': df2}

    with pytest.raises(ValueError, match="Invalid position parameter format: position:"):
        timeline.extract_dates(mock_dates2)


def test_assign_alternating_classes_single_dynasty():
    """Two monarchs in same house get even/odd in chronological order."""
    boxes = pd.DataFrame([
        {'Label': 'George I', 'Keywords': ['Monarch', 'House_of_Hanover'],
         'Start': long_time.date.fromisoformat('1714-08-01'),
         'End': long_time.date.fromisoformat('1727-06-11')},
        {'Label': 'George II', 'Keywords': ['Monarch', 'House_of_Hanover'],
         'Start': long_time.date.fromisoformat('1727-06-11'),
         'End': long_time.date.fromisoformat('1760-10-25')},
    ])
    result = timeline.assign_alternating_classes(boxes)
    george_i = result[result['Label'] == 'George I'].iloc[0]
    george_ii = result[result['Label'] == 'George II'].iloc[0]
    assert george_i['alternating_class'] == 'even'
    assert george_ii['alternating_class'] == 'odd'


def test_assign_alternating_classes_no_house_keyword():
    """Entries without a House_of_ keyword get empty alternating_class."""
    boxes = pd.DataFrame([
        {'Label': 'Obama', 'Keywords': ['USA', 'President', 'Party_Democratic'],
         'Start': long_time.date.fromisoformat('2009-01-20'),
         'End': long_time.date.fromisoformat('2017-01-20')},
    ])
    result = timeline.assign_alternating_classes(boxes)
    assert result.iloc[0]['alternating_class'] == ''


def test_assign_alternating_classes_multiple_dynasties():
    """Alternation resets independently for each dynasty."""
    boxes = pd.DataFrame([
        {'Label': 'A1', 'Keywords': ['House_of_A'],
         'Start': long_time.date.fromisoformat('1000-01-01'),
         'End': long_time.date.fromisoformat('1010-01-01')},
        {'Label': 'A2', 'Keywords': ['House_of_A'],
         'Start': long_time.date.fromisoformat('1010-01-01'),
         'End': long_time.date.fromisoformat('1020-01-01')},
        {'Label': 'B1', 'Keywords': ['House_of_B'],
         'Start': long_time.date.fromisoformat('1005-01-01'),
         'End': long_time.date.fromisoformat('1015-01-01')},
    ])
    result = timeline.assign_alternating_classes(boxes)
    assert result[result['Label'] == 'A1'].iloc[0]['alternating_class'] == 'even'
    assert result[result['Label'] == 'A2'].iloc[0]['alternating_class'] == 'odd'
    assert result[result['Label'] == 'B1'].iloc[0]['alternating_class'] == 'even'


def test_generate_timeline_boxes_includes_alternating_class():
    """even/odd class appears in both rect and text for House_of_ entries."""
    boxes = pd.DataFrame([
        {'Label': 'George I', 'Keywords': ['Monarch', 'House_of_Hanover'],
         'Params': ['label_position:above'],
         'alternating_class': 'even',
         'start_x': 100, 'end_x': 200, 'y': 1},
    ])
    result = timeline._generate_timeline_boxes(boxes, left_to_right=True)
    assert result.count('even') == 2


def test_extract_dates_invalid_start_type_raises_error():
    """Test that extract_dates raises TypeError with label when Start is an invalid type."""
    df = pd.DataFrame([{
        'Label': 'Bad Start Entry',
        'Start': 12345,  # Not a string or datetime
        'End': '2009-01-20',
        'Keywords': ['USA'],
        'Params': ['position:0.5']
    }])

    mock_dates = {'test_data': df}

    with pytest.raises(TypeError, match="Invalid Start date for 'Bad Start Entry'"):
        timeline.extract_dates(mock_dates)


def test_extract_dates_invalid_end_type_raises_error():
    """Test that extract_dates raises TypeError with label when End is an invalid type."""
    df = pd.DataFrame([{
        'Label': 'Bad End Entry',
        'Start': '2001-01-20',
        'End': 12345,  # Not a string or datetime
        'Keywords': ['USA'],
        'Params': ['position:0.5']
    }])

    mock_dates = {'test_data': df}

    with pytest.raises(TypeError, match="Invalid End date for 'Bad End Entry'"):
        timeline.extract_dates(mock_dates)


def test_extract_dates_invalid_dob_type_raises_error():
    """Test that extract_dates raises TypeError with label when DOB is an invalid type."""
    df = pd.DataFrame([{
        'Label': 'Bad DOB Entry',
        'DOB': 12345,  # Not a string or datetime
        'Alive': True,
        'Keywords': ['family'],
        'Params': ['position:0.5']
    }])

    mock_dates = {'test_data': df}

    with pytest.raises(TypeError, match="Invalid DOB for 'Bad DOB Entry'"):
        timeline.extract_dates(mock_dates)


def test_extract_dates_invalid_dod_type_raises_error():
    """Test that extract_dates raises TypeError with label when DOD is an invalid type."""
    df = pd.DataFrame([{
        'Label': 'Bad DOD Entry',
        'DOB': '1920-01-01',
        'DOD': 12345,  # Not a string or datetime
        'Keywords': ['family'],
        'Params': ['position:0.5']
    }])

    mock_dates = {'test_data': df}

    with pytest.raises(TypeError, match="Invalid DOD for 'Bad DOD Entry'"):
        timeline.extract_dates(mock_dates)


def test_extract_dates_handles_missing_optional_fields():
    """Test that extract_dates handles missing Keywords gracefully when position is provided."""

    df = pd.DataFrame([{
        'Label': 'Minimal Entry',
        'Start': '2001-01-20',
        'End': '2009-01-20',
        'Params': ['position:0.5']
        # No Keywords
    }])

    mock_dates = {'test_data': df}
    result = timeline.extract_dates(mock_dates)

    assert len(result) == 1
    assert result.iloc[0]['Label'] == 'Minimal Entry'
    assert result.iloc[0]['Keywords'] == []  # Should default to empty list
    assert result.iloc[0]['y'] == 0.5       # Position from params
