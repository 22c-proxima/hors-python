"""Hors - parsing dates and times from Russian natural-language phrases.

Turns phrases like 'завтра в 15 часов' or 'с 1 мая по 3' into structured
date/time tokens resolved relative to a reference moment.

Public entry point: process_phrase(phrase, now=None) -> HorsParseResult.
"""
from .hors_sugar import process_phrase


VERSION = '0.1.6'

__all__ = [
    'process_phrase',
]
