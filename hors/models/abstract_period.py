"""
AbstractPeriod — internal mutable representation of a date/time expression during parsing.
"""

from datetime import datetime, timedelta
from copy import deepcopy

from ..models.parser_models import FixPeriod, MAX_PERIOD
from .i_has_edges import IHasEdges


# Half of a day in seconds; the AM/PM boundary for clock times stored as timedelta.
HALF_OF_DAY_IN_SEC = 12*60*60


class AbstractPeriod(IHasEdges):
    """
    Internal mutable representation of a date/time expression during parsing.

    Unlike the public DateTimeToken, a period is only partially known: `fixed`
    is a FixPeriod bitmask telling which components are already determined;
    the rest get filled in when periods are merged (collapse_two) or resolved
    against the reference moment. Unfixed components of `date`/`time` carry
    whatever value was last seen and must not be trusted.

    Fields:
        date: calendar part of the date;
        time: clock time as a timedelta since midnight;
        fixed: FixPeriod bitmask of already known components;
        span: duration for span tokens ('через 3 дня'), zero otherwise;
        span_direction: 1 forward, -1 backward, 0 no span;
        duplicate_group: id shared by periods merged from one expression (-1 = none);
        fix_day_of_week: True when the day comes from a weekday name ('во вторник')
            rather than a calendar day.

    start/end (from IHasEdges) are character offsets of the expression in the
    source phrase.
    """
    date: datetime
    time: timedelta = timedelta(0)
    fixed: int = 0
    span: timedelta = timedelta(0)
    span_direction: int = 0
    duplicate_group: int = -1
    fix_day_of_week: bool = False

    def __init__(self,
        date: datetime = datetime(1, 1, 1),
        time: timedelta = timedelta(0),
        span: timedelta = timedelta(0),
        fixed: int = 0,
        span_direction: int = 0,
        duplicate_group: int = -1,
        fix_day_of_week: bool = False,
        start: int = 0,
        end: int = 0
    ) -> None:
        """
        Create a period; all components are unfixed unless explicitly given.

        Args:
            date: Calendar part of the date.
            time: Clock time as a timedelta since midnight.
            span: Duration for span tokens, zero otherwise.
            fixed: FixPeriod bitmask of already known components.
            span_direction: 1 forward, -1 backward, 0 no span.
            duplicate_group: Shared id of periods merged from one expression (-1 = none).
            fix_day_of_week: True when the day comes from a weekday name.
            start: Offset of the first character in the source phrase.
            end: Offset just past the last character (exclusive).
        """
        self.date = date
        self.time = time
        self.span = span
        self.fixed = fixed
        self.span_direction = span_direction
        self.duplicate_group = duplicate_group
        self.fix_day_of_week = fix_day_of_week
        self.start = start
        self.end = end

    def fix(self, *fixes: FixPeriod) -> None:
        """
        Mark the given resolution levels as fixed by ORing their bits into `fixed`.
        """
        for fix in fixes:
            self.fixed |= fix.value

    def unfix(self, time: FixPeriod) -> None:
        """
        Clear one resolution level from `fixed`.
        """
        self.fixed &= ~time.value

    def fix_down_to(self, period: FixPeriod) -> None:
        """
        Mark `period` and every coarser resolution level as fixed
        (e.g. DAY also fixes week, month and year).
        """
        for i in reversed(range(MAX_PERIOD)):
            to_fix = FixPeriod(2**i)
            if to_fix.value < period.value:
                return
            self.fix(to_fix)

    def copy(self) -> "AbstractPeriod":
        """
        Returns:
            A deep copy of this period.
        """
        return deepcopy(self)

    def is_fixed(self, period: FixPeriod) -> bool:
        """
        Returns:
            True when the given resolution level is already fixed.
        """
        return (self.fixed&period.value) > 0

    def min_fixed(self) -> FixPeriod:
        """
        Returns:
            The coarsest fixed level (largest value, e.g. YEAR over DAY),
            or FixPeriod.NONE when nothing is fixed.
        """
        for i in reversed(range(MAX_PERIOD)):
            p = FixPeriod(2**i)
            if self.is_fixed(p):
                return p
        return FixPeriod.NONE

    def max_fixed(self) -> FixPeriod:
        """
        Returns:
            The finest fixed level (smallest value, e.g. TIME over YEAR),
            or FixPeriod.NONE when nothing is fixed.
        """
        for i in range(MAX_PERIOD):
            p = FixPeriod(2**i)
            if self.is_fixed(p):
                return p
        return FixPeriod.NONE

    def __str__(self) -> str:
        """
        Human-readable form: date, clock time and the fixed bitmask.
        """
        return f'[Date={ self.date.isoformat() }, Time={ str(self.time) }, Fixed={ bin(self.fixed) }]'

    @staticmethod
    def take_day_of_week_from(current: datetime, take: datetime, forward: bool = False) -> datetime:
        """
        Shift `current` to the nearest day with `take`'s weekday.

        Args:
            current: The reference datetime.
            take: A datetime whose weekday is wanted.
            forward: When True the result is strictly ahead (up to +7 days);
                when False it may be today or in the past (down to -6 days).

        Returns:
            `current` plus the day offset so that the result has take's weekday.
        """
        need_dow = take.weekday() + 1
        current_dow = current.weekday() + 1
        diff = need_dow - current_dow
        if forward and diff < 0:
            diff += 7
        return current + timedelta(days=diff)

    @staticmethod
    def can_collapse(base, cover) -> bool:
        """
        Check whether two periods can be merged into one.

        Args:
            base: The period that will absorb the other.
            cover: The period being absorbed.

        Returns:
            True when they fix disjoint components and their span directions do
            not conflict (a forward and a backward span cannot be merged).
        """
        if base.fixed & cover.fixed != 0:
            return False
        return base.span_direction != -cover.span_direction or base.span_direction == 0

    @staticmethod
    def collapse_two(base, cover, is_linked: bool) -> bool:
        """
        Merge `cover` into `base` in place.

        Copies every component that `cover` fixes and `base` does not (year,
        month, week, day, clock time), adds up spans when both have a direction,
        and extends base's start/end edges to cover both source expressions.

        Args:
            base: The period receiving the missing components (mutated in place).
            cover: The period contributing its fixed components.
            is_linked: Whether the two source expressions are adjacent in the phrase;
                affects how uncertain clock times combine.

        Returns:
            True when the merge happened, False when can_collapse() rejected it.
        """
        if not AbstractPeriod.can_collapse(base, cover):
            return False

        if base.span_direction != 0 and cover.span_direction != 0:
            base.span += cover.span

        if cover.is_fixed(FixPeriod.YEAR) and not base.is_fixed(FixPeriod.YEAR):
            base.date = datetime(cover.date.year, cover.date.month, cover.date.day)
            base.fix(FixPeriod.YEAR)
        if cover.is_fixed(FixPeriod.MONTH) and not base.is_fixed(FixPeriod.MONTH):
            base.date = datetime(base.date.year, cover.date.month, cover.date.day)
            base.fix(FixPeriod.MONTH)

        if cover.is_fixed(FixPeriod.WEEK) and not base.is_fixed(FixPeriod.WEEK):
            if base.is_fixed(FixPeriod.DAY):
                base.date = AbstractPeriod.take_day_of_week_from(cover.date, base.date)
                base.fix(FixPeriod.WEEK)
            elif not cover.is_fixed(FixPeriod.DAY):
                base.date = datetime(base.date.year, base.date.month, cover.date.day)
                base.fix(FixPeriod.WEEK)
        elif base.is_fixed(FixPeriod.WEEK) and cover.is_fixed(FixPeriod.DAY):
            base.date = AbstractPeriod.take_day_of_week_from(base.date, cover.date)
            base.fix(FixPeriod.WEEK, FixPeriod.DAY)

        if cover.is_fixed(FixPeriod.DAY) and not base.is_fixed(FixPeriod.DAY):
            if cover.fix_day_of_week:
                base.date = AbstractPeriod.take_day_of_week_from(
                    datetime(base.date.year, base.date.month, base.date.day if base.is_fixed(FixPeriod.WEEK) else 1),
                    cover.date, not base.is_fixed(FixPeriod.WEEK))
            else:
                base.date = datetime(base.date.year, base.date.month, cover.date.day)
            base.fix(FixPeriod.WEEK, FixPeriod.DAY)

        time_got = False

        if cover.is_fixed(FixPeriod.TIME) and not base.is_fixed(FixPeriod.TIME):
            base.fix(FixPeriod.TIME)
            if not base.is_fixed(FixPeriod.TIME_UNCERTAIN):
                base.time = cover.time
            else:
                if base.time.seconds <= HALF_OF_DAY_IN_SEC and cover.time.seconds > HALF_OF_DAY_IN_SEC:
                    if not is_linked:
                        base.time += timedelta(seconds=HALF_OF_DAY_IN_SEC)
            time_got = True

        if cover.is_fixed(FixPeriod.TIME_UNCERTAIN) and not base.is_fixed(FixPeriod.TIME_UNCERTAIN):
            base.fix(FixPeriod.TIME_UNCERTAIN)
            if base.is_fixed(FixPeriod.TIME):
                make_offset = cover.time.seconds <= HALF_OF_DAY_IN_SEC and base.time.seconds > HALF_OF_DAY_IN_SEC
                offset = HALF_OF_DAY_IN_SEC if make_offset else 0
                base.time = timedelta(seconds=cover.time.seconds + offset)
            else:
                base.time = cover.time
                time_got = True

        if time_got and base.span_direction != 0 and cover.span_direction == 0:
            base.span += base.time*base.span_direction

        base.start = min(base.start, cover.start)
        base.end = max(base.end, cover.end)

        return True
    # def collapse_two(base: AbstractPeriod, cover: AbstractPeriod, is_linked: bool) -> bool:
