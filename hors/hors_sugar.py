from datetime import datetime
from typing import Optional
from re import sub

from .models.hors_parse_result import HorsParseResult
from .hors_text_parser import parse


def preprocess(phrase: str) -> str:
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
    phrase = phrase.replace('вечерком', 'вечером').replace('ближе к вечеру', 'вечером')
    phrase = sub(r'(вечером|днём|утром)', r'сегодня \1', phrase)
    return phrase


def process_phrase(phrase: str, now: Optional[datetime] = None) -> HorsParseResult:
    phrase = preprocess(phrase)
    now = now or datetime.now()

    hors_result = parse(phrase, now)
    if not hors_result.dates:
        phrase = preprocess_today(phrase)
        hors_result = parse(phrase, now)

    return hors_result
