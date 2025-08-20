import datetime
from operator import index as _index
from typing import Union


class date:
    """
    Extended date class supporting both BCE and CE dates.

    This class extends Python's datetime functionality to handle historical
    dates before the Common Era. It uses a boolean era flag to distinguish
    between BCE (False) and CE (True) periods.

    Date Representation:
        - Positive years with era=True: CE dates (1, 2, 3, ... CE)
        - Positive years with era=False: BCE dates (1, 2, 3, ... BCE)
        - ISO format uses negative years for BCE: "-0001-01-01" = 1 BCE

    Attributes:
        year (int): Year number (1-9999)
        month (int): Month number (1-12)
        day (int): Day number (1-31, depending on month)
        era (bool): True for CE, False for BCE

    Example:
        >>> # Create dates
        >>> bce_date = date(50, 3, 15, False)  # March 15, 50 BCE
        >>> ce_date = date(50, 3, 15, True)    # March 15, 50 CE
        >>>
        >>> # From ISO format
        >>> date.fromisoformat("-0050-03-15")  # March 15, 50 BCE
        >>> date.fromisoformat("0050-03-15")   # March 15, 50 CE
        >>>
        >>> # Comparisons
        >>> bce_date < ce_date  # True (BCE < CE)
    """

    def __init__(self, year: int, month: int, day: int, era: bool = True) -> None:
        """
        Initialize a new date object.

        Args:
            year: Year number (1-9999)
            month: Month number (1-12)
            day: Day number (1-31, depending on month and leap year)
            era: True for CE (Common Era), False for BCE (Before Common Era)

        Raises:
            ValueError: If year, month, or day are out of valid ranges
            TypeError: If era is not a boolean or other args are not integers

        Example:
            >>> date(2023, 12, 25)           # December 25, 2023 CE
            >>> date(44, 3, 15, False)       # March 15, 44 BCE (Ides of March)
            >>> date(1, 1, 1, True)          # January 1, 1 CE
        """

        year, month, day, era = _check_date_fields(year, month, day, era)
        self._year = year
        self._month = month
        self._day = day
        self._era = era
        self._hashcode = -1


    @classmethod
    def fromisoformat(cls, date_string: str) -> 'date':
        """
        Construct a date from an ISO 8601 format string with BCE support.

        Parses ISO format strings where negative years represent BCE dates.

        Args:
            date_string: Extended ISO format date string
                        - CE format: "YYYY-MM-DD" (e.g., "0050-03-15")
                        - BCE format: "-YYYY-MM-DD" (e.g., "-0050-03-15")

        Returns:
            date: New date object

        Raises:
            TypeError: If date_string is not a string
            ValueError: If string format is invalid or date is invalid

        Example:
            >>> date.fromisoformat("2023-12-25")     # December 25, 2023 CE
            >>> date.fromisoformat("-0044-03-15")    # March 15, 44 BCE
            >>> date.fromisoformat("0001-01-01")     # January 1, 1 CE
        """
        if not isinstance(date_string, str):
            raise TypeError('fromisoformat: argument must be str')

        if len(date_string) not in (8, 9, 10, 11):
            raise ValueError(f'Invalid isoformat string: {date_string!r}')

        try:
            return cls(*cls._parse_isoformat_date(date_string))
        except Exception:
            raise ValueError(f'Invalid isoformat string: {date_string!r}')


    def _parse_isoformat_date(dtstr: str) -> list[Union[int, bool]]:
        """
        Parse an extended ISO format date string into its components.

        Args:
            dtstr: Extended ISO-8601 date string

        Returns:
            list[Union[int, bool]]: Parsed components [year, month, day, era]
        """
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


    @classmethod
    def fromdatetime(cls, input_date: datetime.date) -> 'date':
        """
        Construct a date from a standard datetime.date object.

        Converts a Python datetime.date to a long_time.date. All datetime.date
        are dates in the Common Era.

        Args:
            input_date: Standard Python datetime.date object

        Returns:
            date: New date object with era=True (CE)

        Raises:
            TypeError: If input_date is not a datetime.date
            ValueError: If the date values are invalid

        Example:
            >>> import datetime
            >>> dt = datetime.date(2023, 12, 25)
            >>> long_date = date.fromdatetime(dt)
            >>> print(long_date.era)  # True (CE)
        """
        if not isinstance(input_date, datetime.date):
            raise TypeError('fromdatetime: argument must be datetime.date')

        try:
            return cls(input_date.year, input_date.month, input_date.day, True)
        except Exception:
            raise ValueError(f'Invalid date: {input_date!r}')


    def __repr__(self) -> str:
        """
        Return the official string representation of the date.

        Produces a string that can be used to recreate the date object.

        Returns:
            str: String representation in format 'long_time.date(year, month, day, era)'
        """

        return f'{self.__class__.__module__}.{self.__class__.__qualname__}({self._year}, {self._month}, {self._day}, {self._era})'


    def isoformat(self) -> str:
        """
        Return the date in ISO 8601 format with BCE support.

        Formats the date as ISO string where BCE dates use negative years.
        The format is 'YYYY-MM-DD' for CE and '-YYYY-MM-DD' for BCE.

        Returns:
            str: ISO format date string
                - CE dates: "YYYY-MM-DD" (e.g., "2023-12-25")
                - BCE dates: "-YYYY-MM-DD" (e.g., "-0044-03-15")

        Example:
            >>> date(2023, 12, 25, True).isoformat()
            '2023-12-25'
            >>> date(44, 3, 15, False).isoformat()
            '-0044-03-15'
        """

        if self._era:
            return f'{self._year:04d}-{self._month:02d}-{self._day:02d}'
        else:
            return f'-{self._year:04d}-{self._month:02d}-{self._day:02d}'


    __str__ = isoformat


    def days_in_year(self) -> int:
        """
        Return the number of days in the year of this date.

        Calculates whether the year is a leap year and returns the appropriate
        number of days. Leap year calculation is the same for BCE and CE.

        Returns:
            int: 366 for leap years, 365 for regular years

        Leap Year Rules:
            - Divisible by 4: leap year
            - Divisible by 100: not a leap year
            - Divisible by 400: leap year
        """

        return 366 if _is_leap(self._year) else 365


    def ordinal_day(self) -> int:
        """Return the ordinal day of the year for this date.

        Calculates the day number within the year, accounting for leap years.
        January 1st is day 1, December 31st is day 365 or 366.

        Returns:
            int: Day number within the year (1-366)
                - January 1st: 1
                - December 31st: 365 (regular year) or 366 (leap year)
        """

        return _DAYS_BEFORE_MONTH[self._month] + self._day + (self._month > 2 and _is_leap(self._year))


    # Read-only field accessors
    @property
    def year(self) -> int:
        """
        Year number.

        Returns:
            int: The year component of the date

        Note:
            Use the 'era' property to determine if this is BCE or CE.
        """
        return self._year


    @property
    def month(self) -> int:
        """
        Month number (1-12).

        Returns:
            int: The month component (1=January, 12=December)
        """
        return self._month


    @property
    def day(self) -> int:
        """
        Day of month (1-31).

        Returns:
            int: The day component (1-31, depending on month)
        """
        return self._day


    @property
    def era(self) -> bool:
        """
        Historical era designation.

        Returns:
            bool: True for CE, False for BCE
        """
        return self._era


    # Comparisons of date objects with other.


    def __eq__(self, other: object) -> bool:
        """
        Check if two dates are equal.

        Args:
            other: Another date object to compare

        Returns:
            bool: True if dates are equal, False otherwise
        """
        if not isinstance(other, date):
            return False
        return self._cmp(other) == 0


    def __le__(self, other: 'date') -> bool:
        """
        Check if this date is less than or equal to another.

        Args:
            other: Another date object to compare

        Returns:
            bool: True if this date <= other date
        """
        return self._cmp(other) <= 0


    def __lt__(self, other: 'date') -> bool:
        """
        Check if this date is less than another.

        Args:
            other: Another date object to compare

        Returns:
            bool: True if this date < other date
        """
        return self._cmp(other) < 0


    def __ge__(self, other: 'date') -> bool:
        """
        Check if this date is greater than or equal to another.

        Args:
            other: Another date object to compare

        Returns:
            bool: True if this date >= other date
        """
        return self._cmp(other) >= 0


    def __gt__(self, other: 'date') -> bool:
        """
        Check if this date is greater than another.

        Args:
            other: Another date object to compare

        Returns:
            bool: True if this date > other date
        """
        return self._cmp(other) > 0


    def _cmp(self, other: 'date') -> int:
        """
        Compare two dates with BCE/CE awareness.

        Implements chronological comparison where:
        - All BCE dates < all CE dates
        - Within BCE: higher year numbers are earlier (100 BCE < 50 BCE)
        - Within CE: higher year numbers are later (50 CE < 100 CE)

        Args:
            other: Another date object to compare

        Returns:
            int: -1 if self < other, 0 if equal, 1 if self > other
        """
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


    def __hash__(self) -> int:
        """
        Return hash value for the date object.

        Enables use of date objects as dictionary keys and in sets.

        Returns:
            int: Hash value based on year, month, day, and era
        """
        if self._hashcode == -1:
            yhi, ylo = divmod(self._year, 256)
            self._hashcode = hash(bytes([yhi, ylo, self._month, self._day, self._era]))
        return self._hashcode


MINYEAR = 1
MAXYEAR = 9999

def _check_date_fields(year: int, month: int, day: int, era: bool) -> tuple[int, int, int, bool]:
    """
    Validate and normalize date field values.

    Checks that all date components are within valid ranges and of correct types.

    Args:
        year: Year number (must be 1-9999)
        month: Month number (must be 1-12)
        day: Day number (must be 1-31, depending on month)
        era: Era flag (must be boolean)

    Returns:
        tuple[int, int, int, bool]: Validated (year, month, day, era) tuple

    Raises:
        ValueError: If year, month, or day are out of valid ranges
        TypeError: If any argument is not the expected type
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
        raise TypeError('era must be bool', era)
    return year, month, day, era


# -1 is a placeholder for indexing purposes.
_DAYS_IN_MONTH = [-1, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
# -1 is a placeholder for indexing purposes.
_DAYS_BEFORE_MONTH = [-1, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

def _days_in_month(year: int, month: int) -> int:
    """
    Return the number of days in a given month and year.

    Accounts for leap years when calculating February days.

    Args:
        year: Year number (used for leap year calculation)
        month: Month number (1-12)

    Returns:
        int: Number of days in the month (28-31)

    Example:
        >>> _days_in_month(2024, 2)  # February in leap year
        29
        >>> _days_in_month(2023, 2)  # February in regular year
        28
    """
    assert 1 <= month <= 12, month
    if month == 2 and _is_leap(year):
        return 29
    return _DAYS_IN_MONTH[month]


def _is_leap(year: int) -> bool:
    """
    Determine if a year is a leap year.

    Uses the Gregorian calendar leap year rules:
    - Divisible by 4: leap year
    - Divisible by 100: not a leap year
    - Divisible by 400: leap year

    Args:
        year: Year to check

    Returns:
        bool: True if leap year, False otherwise
    """
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
