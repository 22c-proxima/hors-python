"""
Public API of the library: process_phrase() and its text preprocessing helpers.
"""

from datetime import datetime
from typing import Optional
from re import sub

from .models.hors_parse_result import HorsParseResult
from .hors_text_parser import parse


def preprocess(phrase: str) -> str:
    """
    Normalize colloquial Russian time expressions in a phrase before parsing.

    Pure string transformation (no dates are computed here); applied to every
    input inside process_phrase, including the fallback pass.

    Normalizations performed:
      - diminutive forms reduced to base units: 'часок' -> 'час',
        'часиков' -> 'часов', 'минуток' -> 'минут';
      - duration/time words expanded to numbers: 'полчаса' / 'полчасика' /
        'получас' -> '30 минут', 'полтора часа' -> '1 час 30 минут',
        '<N> с половиной часа' -> '<N> часа 30 минут';
      - fuzzy durations made concrete: 'через пару часов' -> 'через 2 часа';
      - mealtime words pinned to clock hours: 'в обед' -> 'в 13 часов',
        'после обеда' -> 'в 14 часов';
      - word order canonicalized so the number precedes the unit:
        'через минут N' / '<unit> через N' -> 'через N минут';
        'в течение <слово, оканчивающееся на а>' (e.g. 'в течение часа') -> 'через <слово>'.

    Args:
        phrase: Raw input phrase in Russian.

    Returns:
        The same phrase with the substitutions applied; the original string is not mutated.
    """
    # change forms
    phrase = phrase.replace('часок', 'час')
    phrase = phrase.replace('часиков', 'часов')
    phrase = phrase.replace('минуток', 'минут')

    # translate times
    phrase = phrase.replace('полчаса', '30 минут')
    phrase = phrase.replace('полчасика', '30 минут')
    phrase = phrase.replace('полтора часа', '1 час 30 минут')
    phrase = phrase.replace('через пару часов', 'через 2 часа')
    phrase = phrase.replace('в обед', 'в 13 часов')
    phrase = phrase.replace('после обеда', 'в 14 часов')

    # swap syntax
    phrase = sub(r'через (минут|часов|часа) (\d*)', r'через \2 \1', phrase)
    phrase = sub(r'(минут|часов|часа) через (\d*)', r'через \2 \1', phrase)
    phrase = sub(r'в течение (\w*а)', r'через \1', phrase)
    phrase = phrase.replace('получас', '30 минут')
    phrase = sub(r'(\d+) с половиной часа', r'\1 часа 30 минут', phrase)

    return phrase


def preprocess_today(phrase: str) -> str:
    """
    Pin bare time-of-day words (morning/noon/evening) to the current day.

    Used as a fallback inside process_phrase when the first parsing pass found
    no dates at all: phrases like 'вечером встреча' then refer to today rather
    than remaining unparsed.

    Transformations:
      - 'вечерком' -> 'вечером', 'ближе к вечеру' -> 'вечером';
      - the words 'утром', 'днём', 'вечером' are prefixed with 'сегодня '
        (e.g. 'встреча вечером' -> 'встреча сегодня вечером').

    Args:
        phrase: Preprocessed input phrase in Russian.

    Returns:
        The phrase with the 'сегодня' prefix applied; the original string is not mutated.
    """
    phrase = phrase.replace('вечерком', 'вечером').replace('ближе к вечеру', 'вечером')
    phrase = sub(r'(вечером|днём|утром)', r'сегодня \1', phrase)
    return phrase


def process_phrase(phrase: str, now: Optional[datetime] = None) -> HorsParseResult:
    """
    Parse a Russian phrase into structured date/time tokens. Main entry point of the library.

    The phrase is interpreted RELATIVE TO THE REFERENCE MOMENT `now`. In the
    vast majority of cases phrases refer to the present, so omit `now` and let
    the library use the current time — only pass an explicit `now` when you
    intentionally need a fixed reference moment (e.g. replaying a saved phrase).

    Behavior:
      1. The phrase is normalized via preprocess().
      2. It is parsed into date/time tokens relative to `now`.
      3. If no dates were found, the phrase is re-parsed after pinning bare
         time-of-day words (утром/днём/вечером) to today via preprocess_today().

    Args:
        phrase: The raw input phrase in Russian containing date/time information.
        now: Reference datetime for relative expressions ('завтра', 'во вторник', ...).
            Optional; defaults to the current time. Omit it unless you have a specific reason.

    Returns:
        A HorsParseResult with:
          - source_text: the input phrase as received;
          - tokens: the phrase tokens in order, where each matched date region is
            replaced by a placeholder entry like '{0}' (one per kept date);
          - text: the phrase with date expressions removed (cleaned remainder);
          - dates: list of DateTimeToken objects, each carrying type
            (FIXED / PERIOD / SPAN_FORWARD / SPAN_BACKWARD), date_from, date_to,
            and its start/end offsets into source_text. Empty if no dates found.
    """
    phrase = preprocess(phrase)
    now = now or datetime.now()

    hors_result = parse(phrase, now)
    if not hors_result.dates:
        phrase = preprocess_today(phrase)
        hors_result = parse(phrase, now)

    return hors_result
