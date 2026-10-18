"""
Core parsing pipeline: tokenize the phrase, run every recognizer over the token
pattern, merge adjacent/overlapping periods and materialize them into DateTimeTokens.
"""

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
    """
    Materialize a raw period into a concrete DateTimeToken relative to `now`.

    The period is first fixed down to its finest resolved component (min_fixed)
    and anchored against the reference moment:
      - MONTH-fixed periods are placed in the current year, rolling over to the
        next one if that date has already passed;
      - DAY-fixed periods ('во вторник') are moved to the next occurrence of
        that weekday;
      - TIME / TIME_UNCERTAIN-only periods are anchored to `now` itself.

    The clock is taken from period.time when fixed, otherwise midnight. Token
    type and bounds follow max_fixed: YEAR/MONTH/WEEK produce a PERIOD covering
    the whole year/month/week, DAY/TIME produce a FIXED token for that day or
    moment (TIME sets has_time). A non-zero span_direction overrides the type
    to SPAN_FORWARD / SPAN_BACKWARD and carries period.span.

    Args:
        period: The raw period produced by recognizers; mutated in place.
        now: Reference datetime against which relative parts are resolved.

    Returns:
        A DateTimeToken with start/end offsets and duplicate_group copied from `period`.
    """
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
    """
    Merge two adjacent raw periods in place so each absorbs the fixed components of the other.

    Each side is masked to its own fixed parts, then collapse_two pulls the
    missing components across — e.g. in 'с 1 мая по 3' the bare day inherits
    month/year from the first endpoint. Mutates data.dates at both indices;
    the second slot may be replaced by the merged copy when it is the finer
    side of the pair.

    Args:
        data: Working set of raw dates being parsed; mutated in place.
        first_index: Index of the first period in data.dates.
        second_index: Index of the second period in data.dates.
        is_linked: Whether the two periods are linked (affects time merging).

    Returns:
        The merged pair as (data.dates[first_index], data.dates[second_index]).
    """
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
    """
    Recognizer callback: merge the two periods matched by a start/end-periods pattern.

    Delegates to take_from_adjacent_i for the periods at match groups 2 and 5.
    Always returns False, so the matcher skips this match after the merge —
    the spliced result is picked up later by create_date_period.
    """
    take_from_adjacent_i(data, match.start(2), match.start(5), is_linked)
    return False


def fix_indexes(final_periods: List[DateTimeToken], split_tokens: ITuplesList) -> None:
    """
    Re-map token offsets from the internal pattern space back to the original text.

    The internal pattern counts every separator run as a single character, so
    start/end offsets are off by (separator_length - 1) for everything after
    each separator. For every separator match this shifts the period forward
    when it starts after it, and stretches its end when it straddles it.

    Args:
        final_periods: Tokens to fix; mutated in place.
        split_tokens: (position, length) of each separator run in the source text.
    """
    for item1, item2 in split_tokens:
        for period in final_periods:
            if period.start > item1:
                period.start += item2 - 1
                period.end += item2 - 1
            elif period.start < item1 and period.end > item1:
                period.end += item2 - 1


def create_date_period(match, data: DatesRawData, now: datetime, final_periods: List[DateTimeToken]) -> bool:
    """
    Materialize a matched pattern region into a final DateTimeToken and splice it back into the data.

    Two shapes are handled by the match:
      - a range 'from X to Y' (groups 3 and 4 present): both endpoints are merged
        via take_from_adjacent_i, converted with convert_to_token, and the end
        is advanced — by day, week, month or year depending on its resolution —
        until it reaches or passes the start;
      - a single date (group 6): converted directly.

    The token's text edges are resolved through data.edges_by_index, appended
    to final_periods, and the matched region is replaced by a placeholder
    TextToken '{i}' with the consumed dates removed from data.

    Args:
        match: Match of the period pattern inside the internal pattern string.
        data: Working set of raw dates; mutated in place.
        now: Reference datetime for resolving relative parts.
        final_periods: Accumulator for finished tokens; appended to in place.

    Returns:
        True — the match is consumed by this pass.
    """
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
    """
    Recognizer callback: fold two adjacent matched periods into one.

    If can_collapse holds for the periods at match groups 2 and 5, the finer-
    grained period absorbs the coarser one via collapse_two, its text edges are
    unified, and the tokens between them are cut out of the pattern.

    Returns:
        True if a collapse happened (match consumed), False otherwise.
    """
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
    """
    Recognizer callback: merge two periods separated by at most `collapse_distance` characters.

    Catches near misses ('1 мая 3') that the direct-adjacency passes left apart:
    the finer period absorbs the coarser one, both slots share a duplicate_group
    (inherited from either side or freshly generated), and the original text
    edges are restored after the merge.

    Returns:
        False — the match is skipped by the matcher after processing.
    """
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
    """
    Expand overlapping final tokens to their union span in place.

    Tokens whose text ranges overlap form a cluster; every member of the cluster
    is stretched to cover min(start)..max(end) of the whole cluster, so that
    dates referring to the same phrase end up with identical edges.
    """
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
    """
    Parse raw text into structured date tokens (library entry point).

    Splits `text` on non-alphanumeric runs via RX_SPLIT and delegates to do_parse.

    Args:
        text: The phrase to parse (already preprocessed by the caller, if any).
        now: Reference datetime against which relative expressions are resolved.

    Returns:
        A HorsParseResult with tokens, cleaned text and resolved dates.
    """
    tokens = RX_SPLIT.split(text)
    split_tokens = [(m.start(), m.end() - m.start()) for m in RX_SPLIT.finditer(text)]
    return do_parse(tokens, text, split_tokens, now)


def do_parse(tokens: List[str], text: str, split_tokens: ITuplesList, now: datetime) -> HorsParseResult:
    """
    Core parsing pipeline over pre-split tokens.

    Steps:
      1. Build a DatesRawData pattern from the tokens and run every recognizer
         to populate raw periods;
      2. Fold adjacent periods (start/end patterns) and merge 'from X to Y'
         pairs, then close remaining gaps of up to `collapse_distance` chars;
      3. Materialize each surviving period into a final DateTimeToken via
         create_date_period;
      4. Fix overlapping token edges (fix_overlap) and re-map offsets onto the
         original text (fix_indexes).

    Args:
        tokens: Text pieces produced by splitting on separators.
        text: The full source phrase, kept for HorsParseResult.
        split_tokens: (position, length) of each separator run in `text`.
        now: Reference datetime against which relative expressions are resolved.

    Returns:
        A HorsParseResult with cleaned tokens/text and resolved dates.
    """
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
