"""
Morphology dictionary of Russian date/time words.

Maps every inflected word form to its normal (lemma) form; the data is
loaded from time_words.txt at import time and queried by the recognizers.
"""

from typing import List, Dict, Tuple, Optional, Union
from enum import Enum
from os.path import join, dirname


class LemmaSearchOptions(Enum):
    """Filter lemma search by number: any form, singular only or plural only."""

    ALL           = 0
    ONLY_SINGULAR = 1
    ONLY_PLURAL   = 2


MorphDict = Dict[str, Tuple[str, LemmaSearchOptions]]

MORPH_DICT_FNAME = 'time_words.txt'


class Morph:
    """Lookup of a word's normal form in the morphology dictionary."""

    storage: MorphDict = {}

    @staticmethod
    def get_normal_form(word: str, option: LemmaSearchOptions = LemmaSearchOptions.ALL) -> Optional[str]:
        """
        Return the normal (lemma) form of word, None if it is not in the dictionary.

        The option filters by number: a form stored as singular/plural is only
        returned when option matches it or is ALL.
        """
        if word not in Morph.storage:
            return None
        normal_form, plural = Morph.storage[word]
        any_form = plural == 0 or option == LemmaSearchOptions.ALL
        return normal_form if any_form or plural == option.value else None

    @staticmethod
    def has_lemma(word: str, lemma: str, option: LemmaSearchOptions = LemmaSearchOptions.ALL) -> bool:
        """Check whether the lemma of word equals lemma (case-insensitive match counts too)."""
        if word.lower() == lemma:
            return True
        normal_form = Morph.get_normal_form(word, option)
        return normal_form is not None and normal_form == lemma

    @staticmethod
    def has_one_of_lemmas(word: str, lemmas: List[Union[str, List[str]]]) -> bool:
        """Check whether word matches any of the given lemmas (or nested lemma lists)."""
        if isinstance(lemmas[0], list):
            return any(Morph.has_one_of_lemmas(word, sublist) for sublist in lemmas)
        else:
            return any(Morph.has_lemma(word, lemma) for lemma in lemmas)

# class Morph:


def load() -> None:
    """
    Load time_words.txt into Morph.storage (called at import time).

    File format: lines 'form|number' (0 — singular, 1 — plural); all forms of a
    block share the normal form of the first word in the block; an empty line
    starts a new block.
    """
    last_normal_form = None

    morph_dict_path = join(dirname(__file__), MORPH_DICT_FNAME)
    with open(morph_dict_path, 'rt', encoding='utf-8') as mdf:
        for line in mdf.readlines():
            line = line.strip()
            if line == '':
                last_normal_form = None
                continue
            word, s_plural = line.split('|')
            plural = LemmaSearchOptions(int(s_plural))
            if last_normal_form is None:
                last_normal_form = word
            Morph.storage[word] = (last_normal_form, plural)


load()
