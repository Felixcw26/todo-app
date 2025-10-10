from functools import total_ordering
from datetime import timedelta, date as dt_date

class FalseDateError(Exception):
    """Raised when an invalid date is created or used."""
    def __init__(self, month, day, year):
        message = f"Invalid date: {month}-{day}-{year}"
        super().__init__(message)

@total_ordering
class Date:
    """
    A lightweight calendar date class with natural comparison,
    validation, arithmetic, and conversion utilities.

    The `Date` class provides a clean, minimal abstraction of a calendar
    date (year–month–day), supporting ordering, equality, and arithmetic
    operations, as well as conversion to and from Python’s built-in
    ``datetime.date`` type. Instances behave naturally in comparisons
    and truth-value contexts and reject invalid calendar dates.

    Examples
    --------
    >>> d1 = Date(3, 5, 2024)
    >>> d2 = Date(1, 7, 2025)
    >>> d1 < d2
    True
    >>> (d2 - d1)
    299
    >>> (d1 + 10)
    3-15-2024
    >>> Date.today()
    10-7-2025
    >>> Date.from_string("12-25-2025").to_string("%B %d, %Y")
    'December 25, 2025'

    Attributes
    ----------
    month : int
        Month of the year (1–12).
    day : int
        Day of the month (1–31).
    year : int
        Year value (e.g., 2025).

    Notes
    -----
    - Invalid dates raise ``FalseDateError`` during initialization.
    - The object evaluates to ``False`` if any of ``year``, ``month``,
      or ``day`` are ``None``.
    - Lexicographic tuple ordering (``(year, month, day)``) is used for
      all comparisons.
    - Date arithmetic (`+`, `-`) and difference in days are supported.
    - Conversion methods link seamlessly with Python’s ``datetime`` module.

    Methods
    -------
    is_valid()
        Validate the date according to Gregorian calendar rules.
    days_between(other)
        Return the number of days between this date and another.
    to_datetime()
        Convert this Date to a ``datetime.date`` object.
    to_string(fmt="%m-%d-%Y")
        Return the date as a formatted string.
    from_datetime(dt)
        Create a Date instance from a ``datetime.date`` object.
    today()
        Return today’s date as a Date instance.
    from_string(s, fmt="%m-%d-%Y")
        Parse a date string and return a corresponding Date instance.
    """

    def __init__(self, month: int = None, day: int = None, year: int = None):
        """
        Initialize a Date object.

        Parameters
        ----------
        month : int, optional
            Month value (1–12).
        day : int, optional
            Day value (1–31).
        year : int, optional
            Year value (e.g., 2025).
        """
        self.month = month
        self.day = day
        self.year = year

        if not self.is_valid():
            raise FalseDateError(self.month, self.day, self.year)

    def __repr__(self) -> str:
        """
        Return a developer-friendly string representation of the Date.

        Returns
        -------
        str
            The date formatted as 'month-day-year'.
        """
        return f"{self.month}-{self.day}-{self.year}"

    def __bool__(self) -> bool:
        """
        Define truthiness for the Date object.

        Returns
        -------
        bool
            True if all components (year, month, day) are not None,
            False otherwise.
        """
        return all(x is not None for x in (self.year, self.month, self.day))

    def __eq__(self, other: object) -> bool:
        """
        Compare two Date objects for equality.

        Parameters
        ----------
        other : object
            The object to compare with.

        Returns
        -------
        bool
            True if all fields (year, month, day) are equal.
        """
        if not isinstance(other, Date):
            return NotImplemented
        return (self.year, self.month, self.day) == (other.year, other.month, other.day)

    def __lt__(self, other: object) -> bool:
        """
        Compare whether this Date is earlier than another Date.

        Parameters
        ----------
        other : object
            The object to compare with.

        Returns
        -------
        bool
            True if this Date is chronologically before the other.
        """
        if not isinstance(other, Date):
            return NotImplemented
        return (self.year, self.month, self.day) < (other.year, other.month, other.day)
    
    def __str__(self):
        """Return a human-readable date string."""
        months = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]
        return f"{months[self.month - 1]} {self.day}, {self.year}"
    
    def __add__(self, days: int):
        """Add a number of days to the date."""
        if not isinstance(days, int):
            return NotImplemented
        d = dt_date(self.year, self.month, self.day) + timedelta(days=days)
        return Date(d.month, d.day, d.year)

    def __sub__(self, other):
        """Subtract a date or integer days."""
        from datetime import timedelta, date as dt_date
        if isinstance(other, int):
            d = dt_date(self.year, self.month, self.day) - timedelta(days=other)
            return Date(d.month, d.day, d.year)
        elif isinstance(other, Date):
            d1 = dt_date(self.year, self.month, self.day)
            d2 = dt_date(other.year, other.month, other.day)
            return (d1 - d2).days
        else:
            return NotImplemented
        
    def is_valid(self) -> bool:
        """Return True if the date is a valid calendar date."""
        if not self:
            return False
        if not (1 <= self.month <= 12):
            return False
        if not (1 <= self.day <= 31):
            return False
        if self.month in (4, 6, 9, 11) and self.day > 30:
            return False
        if self.month == 2:
            leap = (self.year % 4 == 0 and (self.year % 100 != 0 or self.year % 400 == 0))
            if self.day > (29 if leap else 28):
                return False
        return True

    def days_between(self, other: "Date") -> int:
        """Return the number of days between this date and another."""
        d1 = dt_date(self.year, self.month, self.day)
        d2 = dt_date(other.year, other.month, other.day)
        return abs((d2 - d1).days)
    
    def to_datetime(self) -> dt_date:
        """Convert to a built-in datetime.date object."""
        return dt_date(self.year, self.month, self.day)
    
    def to_string(self, fmt: str = "%m-%d-%Y") -> str:
        """Return the date as a formatted string."""
        from datetime import date as dt_date
        d = dt_date(self.year, self.month, self.day)
        return d.strftime(fmt)
    
    @classmethod
    def from_datetime(cls, dt: dt_date) -> "Date":
        """Create a Date object from a datetime.date."""
        return cls(dt.month, dt.day, dt.year)
    
    @classmethod
    def today(cls) -> "Date":
        """Return today's date as a Date object."""
        from datetime import date as dt_date
        d = dt_date.today()
        return cls(d.month, d.day, d.year)
    
    @classmethod
    def from_string(cls, s: str, fmt: str = "%m-%d-%Y") -> "Date":
        """Parse a date string using the given format."""
        from datetime import datetime
        d = datetime.strptime(s, fmt).date()
        return cls(d.month, d.day, d.year)