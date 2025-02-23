from datetime import datetime, timedelta
from copy import deepcopy

from ..models.parser_models import FixPeriod, MAX_PERIOD
from .i_has_edges import IHasEdges


HALF_OF_DAY_IN_SEC = 12*60*60


class AbstractPeriod(IHasEdges):
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
        for fix in fixes:
            self.fixed |= fix.value

    def unfix(self, time: FixPeriod) -> None:
        self.fixed &= ~time

    def fix_down_to(self, period: FixPeriod) -> None:
        for i in reversed(range(MAX_PERIOD)):
            to_fix = FixPeriod(2**i)
            if to_fix.value < period.value:
                return
            self.fix(to_fix)

    def copy(self):
        return deepcopy(self)

    def is_fixed(self, period: FixPeriod) -> bool:
        return (self.fixed&period.value) > 0

    def min_fixed(self) -> FixPeriod:
        for i in reversed(range(MAX_PERIOD)):
            p = FixPeriod(2**i)
            if self.is_fixed(p):
                return p
        return FixPeriod.NONE

    def max_fixed(self) -> FixPeriod:
        for i in range(MAX_PERIOD):
            p = FixPeriod(2**i)
            if self.is_fixed(p):
                return p
        return FixPeriod.NONE

    def __str__(self) -> str:
        return f'[Date={ self.date.isoformat() }, Time={ str(self.time) }, Fixed={ bin(self.fixed) }]'

    @staticmethod
    def take_day_of_week_from(current: datetime, take: datetime, forward: bool = False) -> datetime:
        need_dow = take.weekday() + 1
        current_dow = current.weekday() + 1
        diff = need_dow - current_dow
        if forward and diff < 0:
            diff += 7
        return current + timedelta(days=diff)

    @staticmethod
    def can_collapse(base, cover) -> bool:
        if base.fixed & cover.fixed != 0:
            return False
        return base.span_direction != -cover.span_direction or base.span_direction == 0

    @staticmethod
    def collapse_two(base, cover, is_linked: bool) -> bool:
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
