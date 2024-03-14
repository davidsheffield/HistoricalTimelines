"""
Test long_time.py
"""

import pytest

import long_time


@pytest.mark.parametrize('year,month,day,era',
                         [(2000, 1, 1, True),
                          (2000, 1, 31, True),
                          (2000, 12, 31, True),
                          (1, 1, 1, True),
                          (1, 1, 1, False)])
def test_init__full(year, month, day, era):
    date = long_time.date(year, month, day, era)
    assert date._year == year
    assert date._month == month
    assert date._day == day
    assert date._era == era


def test_init__no_era():
    date = long_time.date(2000, 1, 2)
    assert date._year == 2000
    assert date._month == 1
    assert date._day == 2
    assert date._era == True


@pytest.mark.parametrize('input_date,expected_year,expected_month,expected_day,expected_era',
                         [('0001-02-03', 1, 2, 3, True),
                          ('-0001-02-03', 1, 2, 3, False)])
def test_fromisoformat(input_date, expected_year, expected_month, expected_day, expected_era):
    assert long_time.date.fromisoformat(input_date) \
        == long_time.date(expected_year, expected_month, expected_day, expected_era)


def test_repr():
    date = long_time.date(2000, 1, 2, True)
    assert date.__repr__() == 'long_time.date(2000, 1, 2, True)'


@pytest.mark.parametrize('year,month,day,era',
                         [(2000, 1, 1, True),
                          (2000, 1, 31, True),
                          (2000, 12, 1, True),
                          (1, 1, 1, True),
                          (1, 1, 1, False),
                          (9999, 12, 31, True)])
def test_check_date_fields(year, month, day, era):
    result_year, result_month, result_day, result_era = long_time._check_date_fields(year, month, day, era)
    assert result_year == year
    assert result_month == month
    assert result_day == day
    assert result_era == era


@pytest.mark.parametrize('era,expected',
                         [(True, '0001-01-01'),
                          (False, '-0001-01-01')])
def test_isoformat(era, expected):
    date = long_time.date(1, 1, 1, era)
    assert date.isoformat() == expected


@pytest.mark.parametrize('date1,date2,expected',
                         [(long_time.date(2000, 6, 15, True), long_time.date(2000, 6, 15, True), 0),
                          (long_time.date(2000, 6, 15, True), long_time.date(2000, 6, 14, True), 1),
                          (long_time.date(2000, 6, 15, True), long_time.date(2000, 6, 16, True), -1),
                          (long_time.date(2000, 6, 15, True), long_time.date(2000, 5, 16, True), 1),
                          (long_time.date(2000, 6, 15, True), long_time.date(2000, 7, 14, True), -1),
                          (long_time.date(2000, 6, 15, True), long_time.date(1999, 6, 15, True), 1),
                          (long_time.date(2000, 6, 15, True), long_time.date(2001, 6, 15, True), -1),
                          (long_time.date(2000, 6, 15, True), long_time.date(1999, 7, 15, True), 1),
                          (long_time.date(2000, 6, 15, True), long_time.date(2001, 5, 15, True), -1),
                          (long_time.date(2000, 6, 15, False), long_time.date(2000, 6, 15, False), 0),
                          (long_time.date(2000, 6, 15, False), long_time.date(2000, 6, 14, False), 1),
                          (long_time.date(2000, 6, 15, False), long_time.date(2000, 6, 16, False), -1),
                          (long_time.date(2000, 6, 15, False), long_time.date(2000, 7, 24, False), -1),
                          (long_time.date(2000, 6, 15, False), long_time.date(2000, 5, 16, False), 1),
                          (long_time.date(2000, 6, 15, False), long_time.date(1999, 6, 15, False), -1),
                          (long_time.date(2000, 6, 15, False), long_time.date(2001, 6, 15, False), 1),
                          (long_time.date(2000, 6, 15, False), long_time.date(1999, 5, 15, False), -1),
                          (long_time.date(2000, 6, 15, False), long_time.date(2001, 7, 15, False), 1),
                          (long_time.date(2000, 6, 15, True), long_time.date(2000, 6, 15, False), 1),
                          (long_time.date(2000, 6, 15, False), long_time.date(2000, 6, 15, True), -1),
                          (long_time.date(2000, 6, 15, False), long_time.date(2000, 6, 14, True), -1),
                          (long_time.date(2000, 6, 15, False), long_time.date(2000, 6, 16, True), -1)])
def test_cmp(date1, date2, expected):
    assert date1._cmp(date2) == expected


@pytest.mark.parametrize('year,month,day,era,error',
                         [(0, 1, 1, True, ValueError),
                          (10000, 1, 1, True, ValueError),
                          (2000, 0, 1, True, ValueError),
                          (2000, 13, 1, True, ValueError),
                          (2000, 1, 0, True, ValueError),
                          (2000, 1, 32, True, ValueError),
                          ('2000', 1, 1, True, TypeError),
                          (2000, '1', 1, True, TypeError),
                          (2000, 1, '1', True, TypeError),
                          (2000, 1, 1, 1, TypeError)])
def test_check_date_fields__raises(year, month, day, era, error):
    with pytest.raises(error):
        long_time._check_date_fields(year, month, day, era)


@pytest.mark.parametrize('year,month,expected',
                         [(1995, 1, 31),
                          (1995, 2, 28),
                          (1995, 3, 31),
                          (1995, 4, 30),
                          (1995, 5, 31),
                          (1995, 6, 30),
                          (1995, 7, 31),
                          (1995, 8, 31),
                          (1995, 9, 30),
                          (1995, 10, 31),
                          (1995, 11, 30),
                          (1995, 12, 31),
                          (1996, 2, 29),
                          (1996, 1, 31)])
def test_days_in_month(year, month, expected):
    assert long_time._days_in_month(year, month) == expected


@pytest.mark.parametrize('year,expected',
                         [(1995, 0),
                          (1900, 0),
                          (1996, 1),
                          (2000, 1)])
def test_is_leap(year, expected):
    assert long_time._is_leap(year) == expected
