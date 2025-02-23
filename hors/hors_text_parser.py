from typing import List, Tuple, Set
from datetime import datetime, timedelta
from re import compile
from random import randint
from sys import maxsize

from .models import *
from .models.parser_models import *
from .recognizers import Recognizer, recognizers


ITuplesList = List[Tuple[int, int]]

RX_SPLIT = compile(r'[^а-яА-ЯёЁa-zA-Z0-9-]+')


def convert_to_token(period: AbstractPeriod, now: datetime) -> DateTimeToken:
    min_fixed = period.min_fixed()
    period.fix_down_to(min_fixed)
    if min_fixed == FixPeriod.MONTH:
        period.date = datetime(now.year, period.date.month, period.date.day)
        if now > period.date:
            period.date = datetime(now.year + 1, period.date.month, period.date.day)
    elif min_fixed == FixPeriod.DAY:
        now_dow = now.weekday() + 1
        date_dow = period.date.weekday() + 1
        diff = date_dow - now_dow
        if diff <= 0:
            diff += 7
        new_date = now + timedelta(days=diff)
        period.date = datetime(new_date.year, new_date.month, new_date.day)
    elif min_fixed in [FixPeriod.TIME, FixPeriod.TIME_UNCERTAIN]:
        period.date = now

    if period.is_fixed(FixPeriod.TIME) or period.is_fixed(FixPeriod.TIME_UNCERTAIN):
        s = period.time.seconds
        h = s//(60*60)
        m = (s - h*(60*60))//60
        period.date = period.date.replace(hour=h, minute=m, second=0, microsecond=0)
    else:
        period.date = period.date.replace(hour=0, minute=0, second=0, microsecond=0)

    token = DateTimeToken()
    token.type = DateTimeTokenType.FIXED
    token.start = period.start
    token.end = period.end
    token.set_duplicate_group(period.duplicate_group)

    max_fixed = period.max_fixed()
    if max_fixed == FixPeriod.YEAR:
        token.type = DateTimeTokenType.PERIOD
        token.date_from = datetime(period.date.year, 1, 1)
        token.date_to = datetime(period.date.year + 1, 1, 1) - timedelta(microseconds=1)
    elif max_fixed == FixPeriod.MONTH:
        token.type = DateTimeTokenType.PERIOD
        token.date_from = datetime(period.date.year, period.date.month, 1)
        token.date_to = datetime(period.date.year, period.date.month + 1, 1) - timedelta(microseconds=1)
    elif max_fixed == FixPeriod.WEEK:
        dow = period.date.weekday() + 1
        token.type = DateTimeTokenType.PERIOD
        token.date_from = period.date + timedelta(days=(1 - dow))
        token.date_to = period.date + timedelta(days=(8 - dow)) - timedelta(microseconds=1)
    elif max_fixed == FixPeriod.DAY:
        token.type = DateTimeTokenType.FIXED
        token.date_from = period.date
        token.date_to = period.date + timedelta(days=1) - timedelta(microseconds=1)
    elif max_fixed in [FixPeriod.TIME, FixPeriod.TIME_UNCERTAIN]:
        token.type = DateTimeTokenType.FIXED
        token.date_from = period.date
        token.date_to = period.date
        token.has_time = True

    if period.span_direction != 0:
        token.type = DateTimeTokenType.SPAN_FORWARD if period.span_direction == 1 else DateTimeTokenType.SPAN_BACKWARD
        token.span = period.span

    return token
# def convert_to_token(period: AbstractPeriod, now: datetime) -> DateTimeToken:


def take_from_adjacent_i(data: DatesRawData, first_index: int, second_index: int, is_linked: bool) -> Tuple[AbstractPeriod, AbstractPeriod]:
    first_date = data.dates[first_index]
    second_date = data.dates[second_index]
    first_copy = first_date.copy()
    second_copy = second_date.copy()
    first_copy.fixed &= ~second_date.fixed
    second_copy.fixed &= ~first_date.fixed
    if first_date.min_fixed().value > second_copy.min_fixed().value:
        AbstractPeriod.collapse_two(first_date, second_copy, is_linked)
    else:
        AbstractPeriod.collapse_two(second_copy, first_date, is_linked)
        data.dates[first_index] = second_copy
        second_copy.start = first_date.start
        second_copy.end = first_date.end
    if second_date.min_fixed().value > first_copy.min_fixed().value:
        AbstractPeriod.collapse_two(second_date, first_copy, is_linked)
    else:
        AbstractPeriod.collapse_two(first_copy, second_date, is_linked)
        data.dates[second_index] = first_copy
        first_copy.start = second_date.start
        first_copy.end = second_date.end
    return (data.dates[first_index], data.dates[second_index])


def take_from_adjacent(match, data: DatesRawData, _, is_linked: bool) -> bool:
    take_from_adjacent_i(data, match.start(2), match.start(5), is_linked)
    return False


def fix_indexes(final_periods: List[DateTimeToken], split_tokens: ITuplesList) -> None:
    for item1, item2 in split_tokens:
        for period in final_periods:
            if period.start > item1:
                period.start += item2 - 1
                period.end += item2 - 1
            elif period.start < item1 and period.end > item1:
                period.end += item2 - 1


def create_date_period(match, data: DatesRawData, now: datetime, final_periods: List[DateTimeToken]) -> bool:
    if match.group(3) is not None and match.group(4) is not None:
        from_date, to_date = take_from_adjacent_i(data, match.start(3), match.start(4), True)
        from_token = convert_to_token(from_date, now)

        to_token = convert_to_token(to_date, now)
        date_to = to_token.date_to
        resolution = to_date.max_fixed()
        while date_to < from_token.date_from:
            if resolution == FixPeriod.TIME:
                date_to += timedelta(days=1)
            elif resolution == FixPeriod.DAY:
                date_to += timedelta(days=7)
            elif resolution == FixPeriod.WEEK:
                date_to = date_to.replace(month=date_to.month + 1)
            elif resolution == FixPeriod.MONTH:
                date_to = date_to.replace(year=date_to.year + 1)
            else:
                date_to = date_to.replace(hour=date_to.hour + 12)                

        date_to_save = DateTimeToken()
        date_to_save.date_from = from_token.date_from
        date_to_save.date_to = date_to
        date_to_save.type = DateTimeTokenType.PERIOD
        date_to_save.has_time = from_token.has_time or to_token.has_time
    else:
        single_date = data.dates[match.start(6)]
        date_to_save = convert_to_token(single_date, now)
    # if match.group(3) is not None and match.group(4) is not None:

    s, e = match.span()
    date_to_save.set_edges(data.edges_by_index(s).start, data.edges_by_index(e - 1).end)
    next_index = len(final_periods)
    final_periods.append(date_to_save)
    suffix = '$' if e < len(data.pattern) else ''
    data.pattern = data.pattern[:s] + suffix + data.pattern[e:]
    data.tokens[s] = TextToken(f'{{{ next_index }}}', date_to_save.start, date_to_save.end)
    data.dates[s] = None
    if e - s > 1:
        data.tokens = data.tokens[:s + 1] + data.tokens[e:]
        data.dates = data.dates[:s + 1] + data.dates[e:]

    return True
# def create_date_period(match, data: DatesRawData, now: datetime, final_periods: List[DateTimeToken]) -> bool:


def collapse_dates(match, data: DatesRawData, _, is_linked: bool) -> bool:
    first_date = data.dates[match.start(2)]
    second_date = data.dates[match.start(5)]
    if not AbstractPeriod.can_collapse(first_date, second_date):
        return False

    if first_date.min_fixed().value < second_date.min_fixed().value:
        AbstractPeriod.collapse_two(second_date, first_date, is_linked)
        second_date.start = first_date.start
        data.remove_range(match.start(2), match.end(2) - match.start(2) + match.end(4) - match.start(4))
    else:
        AbstractPeriod.collapse_two(first_date, second_date, is_linked)
        first_date.end = second_date.end
        data.remove_range(match.start(3), match.end(3) - match.start(3))
    return True


def collapse_closest(match, data: DatesRawData, _, is_linked: bool) -> bool:
    first_date = data.dates[match.start(1)]
    second_date = data.dates[match.start(2)]
    if AbstractPeriod.can_collapse(first_date, second_date):
        first_start, first_end, second_start, second_end = first_date.start, first_date.end, second_date.start, second_date.end
        if first_date.min_fixed().value > second_date.min_fixed().value:
            AbstractPeriod.collapse_two(first_date, second_date, is_linked)
        else:
            AbstractPeriod.collapse_two(second_date, first_date, is_linked)

        duplicate_group: int
        if first_date.duplicate_group != -1:
            duplicate_group = first_date.duplicate_group
        elif second_date.duplicate_group != -1:
            duplicate_group = second_date.duplicate_group
        else:
            duplicate_group = randint(0, maxsize)

        second_date.duplicate_group = duplicate_group
        first_date.duplicate_group = duplicate_group

        first_date.start = first_start
        first_date.end = first_end
        second_date.start = second_start
        second_date.end = second_end
    return False


def fix_overlap(final_periods: List[DateTimeToken]) -> None:
    skipped: Set[DateTimeToken] = set()
    for period in final_periods:
        if period not in skipped:
            overlap_periods = [p for p in final_periods if p.overlapping_with(period) and p not in skipped]
            min_index = min(o.start for o in overlap_periods)
            max_index = max(o.end for o in overlap_periods)

            for p in overlap_periods:
                p.start = min_index
                p.end = max_index
                skipped.add(p)


def parse(text: str, now: datetime) -> HorsParseResult:
    tokens = RX_SPLIT.split(text)
    split_tokens = [(m.start(), m.end() - m.start()) for m in RX_SPLIT.finditer(text)]
    return do_parse(tokens, text, split_tokens, now)


def do_parse(tokens: List[str], text: str, split_tokens: ITuplesList, now: datetime) -> HorsParseResult:
    collapse_distance = 4

    data = DatesRawData(tokens)
    data.create_tokens(tokens)

    for r in recognizers:
        r.parse_tokens(data, now)

    start_periods_pattern = r'(?<!(t))(@)(?=((N?[fo]?)(@)))'
    end_periods_pattern = r'(?<=(t))(@)(?=((N?[fot]?)(@)))'

    Recognizer.for_all_matches(data.get_pattern, start_periods_pattern, lambda m: collapse_dates(m, data, now, False), True)
    Recognizer.for_all_matches(data.get_pattern, end_periods_pattern, lambda m: collapse_dates(m, data, now, False), True)
    Recognizer.for_all_matches(data.get_pattern, end_periods_pattern, lambda m: take_from_adjacent(m, data, now, False), True)
    Recognizer.for_all_matches(data.get_pattern, start_periods_pattern, lambda m: take_from_adjacent(m, data, now, False), True)

    if collapse_distance > 0:
        pattern = '(@)[^@t]{1,' + str(collapse_distance) + '}(?=(@))'
        Recognizer.for_all_matches(data.get_pattern, pattern, lambda m: collapse_closest(m, data, now, False), True)

    final_periods: List[DateTimeToken] = []
    Recognizer.for_all_matches(data.get_pattern, '(([fo]?(@)t(@))|([fo]?(@)))', lambda m: create_date_period(m, data, now, final_periods))

    fix_overlap(final_periods)
    fix_indexes(final_periods, split_tokens)

    return HorsParseResult(text, [t.value for t in data.tokens], final_periods)
