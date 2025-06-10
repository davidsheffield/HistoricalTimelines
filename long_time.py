from operator import index as _index


class date:
    """
    datetime.date that functions for both BCE and CE

    Parameters
    ----------
    year
    month
    day
    era
    """

    def __init__(self, year, month, day, era=True):
        """
        Initialize
        """

        year, month, day, era = _check_date_fields(year, month, day, era)
        self._year = year
        self._month = month
        self._day = day
        self._era = era
        self._hashcode = -1


    @classmethod
    def fromisoformat(cls, date_string):
        """Construct a date from a string in ISO 8601 format, where year -0001 is 1 BCE"""
        if not isinstance(date_string, str):
            raise TypeError('fromisoformat: argument must be str')

        if len(date_string) not in (8, 9, 10, 11):
            raise ValueError(f'Invalid isoformat string: {date_string!r}')

        try:
            return cls(*cls._parse_isoformat_date(date_string))
        except Exception:
            raise ValueError(f'Invalid isoformat string: {date_string!r}')


    def _parse_isoformat_date(dtstr):
        # It is assumed that this is an ASCII-only string of lengths 10 or 11,
        era = dtstr[0] != '-'

        if era:
            assert len(dtstr) == 10
            year = int(dtstr[0:4])
            month = int(dtstr[5:7])
            day = int(dtstr[8:])
        else:
            assert len(dtstr) == 11
            year = int(dtstr[1:5])
            month = int(dtstr[6:8])
            day = int(dtstr[9:])
        return [year, month, day, era]


    def __repr__(self):
        """Convert to formal string, for repr().

        >>> d = date(2010, 1, 1, True)
        >>> repr(d)
        'long_time.date(2010, 1, 1, True)'
        """

        return f'{self.__class__.__module__}.{self.__class__.__qualname__}({self._year}, {self._month}, {self._day}, {self._era})'


    def isoformat(self):
        """Return the date formatted according to ISO.

        This is 'YYYY-MM-DD'.

        References:
        - http://www.w3.org/TR/NOTE-datetime
        - http://www.cl.cam.ac.uk/~mgk25/iso-time.html
        """

        if self._era:
            return f'{self._year:04d}-{self._month:02d}-{self._day:02d}'
        else:
            return f'-{self._year:04d}-{self._month:02d}-{self._day:02d}'


    __str__ = isoformat


    def days_in_year(self):
        """Return the number of days in the year of this date."""

        return 366 if _is_leap(self._year) else 365


    # Read-only field accessors
    @property
    def year(self):
        """year (1-9999)"""
        return self._year


    @property
    def month(self):
        """month (1-12)"""
        return self._month


    @property
    def day(self):
        """day (1-31)"""
        return self._day


    @property
    def era(self):
        """era (True,False)"""
        return self._era
    
    # Comparisons of date objects with other.

    def __eq__(self, other):
        return self._cmp(other) == 0
    

    def __le__(self, other):
        return self._cmp(other) <= 0


    def __lt__(self, other):
        return self._cmp(other) < 0


    def __ge__(self, other):
        return self._cmp(other) >= 0


    def __gt__(self, other):
        return self._cmp(other) > 0


    def _cmp(self, other):
        assert isinstance(other, date)
        y, m, d, e = self._year, self._month, self._day, self._era
        y2, m2, d2, e2 = other._year, other._month, other._day, other._era
        if (y, m, d, e) == (y2, m2, d2, e2):
            return 0
        elif e:
            if not e2:
                return 1
            elif (y, m, d) > (y2, m2, d2):
                return 1
            else:
                return -1
        else:
            if e2:
                return -1
            elif y < y2:
                return 1
            elif y > y2:
                return -1
            elif (m, d) > (m2, d2):
                return 1
            else: return -1
    

    def __hash__(self):
        "Hash."
        if self._hashcode == -1:
            yhi, ylo = divmod(self._year, 256)
            self._hashcode = hash(bytes([yhi, ylo, self._month, self._day, self._era]))
        return self._hashcode


MINYEAR = 1
MAXYEAR = 9999

def _check_date_fields(year, month, day, era):
    """
    Check that date fields are acceptable.
    """

    year = _index(year)
    month = _index(month)
    day = _index(day)
    if not MINYEAR <= year <= MAXYEAR:
        raise ValueError('year must be in %d..%d' % (MINYEAR, MAXYEAR), year)
    if not 1 <= month <= 12:
        raise ValueError('month must be in 1..12', month)
    dim = _days_in_month(year, month)
    if not 1 <= day <= dim:
        raise ValueError('day must be in 1..%d' % dim, day)
    if not isinstance(era, bool):
        raise TypeError('era mus be bool', era)
    return year, month, day, era


# -1 is a placeholder for indexing purposes.
_DAYS_IN_MONTH = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def _days_in_month(year, month):
    "year, month -> number of days in that month in that year."
    assert 1 <= month <= 12, month
    if month == 2 and _is_leap(year):
        return 29
    return _DAYS_IN_MONTH[month]


def _is_leap(year):
    "year -> 1 if leap year, else 0."
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
