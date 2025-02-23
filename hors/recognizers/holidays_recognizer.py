from .recognizer import Recognizer
from ..dict import Keywords, Morph, LemmaSearchOptions
from ..models import DatesRawData, TextToken
from .recognizer import Recognizer


class HolidaysRecognizer(Recognizer):
    regex_pattern = r'W'

    def parse_match(self, data: DatesRawData, match, _) -> bool:
        s, _ = match.span()
        token = data.tokens[s]
        data.remove_range(s, 1)
        if Morph.has_lemma(token.value, Keywords.HOLIDAY[0], LemmaSearchOptions.ONLY_SINGULAR):
            saturday = TextToken(Keywords.SATURDAY[0], token.start, token.end)
            data.return_tokens(s, 'D', saturday)
        else:
            holidays = [TextToken(h, token.start, token.end) for h in [Keywords.SATURDAY[0], Keywords.TIME_TO[0], Keywords.SUNDAY[0]]]
            data.return_tokens(s, 'DtD', *holidays)
        return True
