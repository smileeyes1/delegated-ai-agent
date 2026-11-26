"""Exact comparison for the Tanzil and Quranpedia Uthmani encodings."""

import re
import unicodedata


COMPARISON_METHOD = 'tanzil_quranpedia_uthmani_v1'

# These signs annotate pauses, a verse division, or the rendering of tanwin.
# All letters, vowels, shadda, and unlisted marks stay in the comparison.
_ANNOTATIONS = '\u06d6\u06d7\u06da\u06db\u06de\u06e2\u06ed'
_DISPLAY_SIGNS = dict.fromkeys(map(ord, _ANNOTATIONS + '\u0640'))
_QURANPEDIA_GLYPHS = str.maketrans('\u08f0\u08f1\u08f2\u06e1', '\u064b\u064c\u064d\u0652')
_TANZIL_SILENT_ALIF = re.compile(r'(آ?)\u06df')
_TANZIL_DOTLESS_YA = re.compile(r'(?<=ِ)ى(?!ٰ)|ى(?=ْ)')


def tanzil_verse_form(reference: str, text: str, basmalah: str) -> str:
    # The Tanzil export prepends 1:1 to 14:1. Quranpedia stores 14:1 alone.
    if reference == '14:1' and basmalah:
        text = text.removeprefix(basmalah + ' ')
    text = _TANZIL_SILENT_ALIF.sub(r'\1ْ', text)
    return _TANZIL_DOTLESS_YA.sub('ي', _display_form(text))


def quranpedia_verse_form(text: str) -> str:
    return _display_form(text.translate(_QURANPEDIA_GLYPHS))


def _display_form(text: str) -> str:
    text = text.removeprefix('\ufeff').translate(_DISPLAY_SIGNS)
    return unicodedata.normalize('NFC', ' '.join(text.split()))


def verify_verse(reference: str, tanzil: str, quranpedia: str, basmalah: str) -> bool:
    tanzil_form = tanzil_verse_form(reference, tanzil, basmalah)
    return bool(tanzil_form) and tanzil_form == quranpedia_verse_form(quranpedia)


def quranpedia_text(reference: str, record: dict) -> str:
    """Reject misaddressed verses and distinct Hafs numbering before comparing."""
    surah, ayah = reference.split(':')
    if not isinstance(record, dict):
        raise ValueError(f'Unexpected Quranpedia verse response for {reference}')
    text = record.get('text')
    number = record.get('number')
    hafs_numbers = record.get('number_in_hafs')
    if (
        record.get('surah') != surah
        or type(number) is not int
        or number != int(ayah)
        or hafs_numbers != [number]
        or type(hafs_numbers[0]) is not int
        or not isinstance(text, str)
        or not text.strip()
    ):
        raise ValueError(f'Unexpected Quranpedia verse response for {reference}')
    return text
