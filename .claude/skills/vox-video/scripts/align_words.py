"""Align the known narration script to ASR (MLX Whisper) word timings.

The script text is the ground truth; Whisper only lends timings. Alignment is
character-level: normalized script characters are matched against normalized
ASR characters with difflib, so Korean spacing differences between the script
and the ASR output do not break the mapping. Unmatched script words get
interpolated timings between their matched neighbors.

Output schema matches the pipeline's words.json:
  [{"word": ..., "start": ..., "end": ...}, ...]
"""
import re
import unicodedata
from difflib import SequenceMatcher

WORD_PATTERN = re.compile(r"\S+")


def _norm_chars(text):
    """NFKC + casefold, keep alphanumerics only (Korean syllables included)."""
    return [c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum()]


def _script_char_map(script):
    """Return (norm_chars, word_index_per_char, words) for the script."""
    words = [m.group(0) for m in WORD_PATTERN.finditer(script)]
    chars, owner = [], []
    for wi, word in enumerate(words):
        for c in _norm_chars(word):
            chars.append(c)
            owner.append(wi)
    return chars, owner, words


def _asr_char_times(asr_words):
    """Spread each ASR word's duration linearly across its normalized chars."""
    chars, starts, ends = [], [], []
    for item in asr_words:
        text = str(item.get("text", item.get("word", ""))).strip()
        norm = _norm_chars(text)
        if not norm:
            continue
        w_start, w_end = float(item["start"]), float(item["end"])
        span = max(w_end - w_start, 0.001)
        step = span / len(norm)
        for i, c in enumerate(norm):
            chars.append(c)
            starts.append(w_start + step * i)
            ends.append(w_start + step * (i + 1))
    return chars, starts, ends


def align(script, asr_words, audio_duration):
    """Return (words, alignment_ratio). words = [{"word","start","end"}, ...]."""
    s_chars, owner, words = _script_char_map(script)
    if not s_chars:
        raise ValueError("대본에서 정렬할 문자를 찾지 못했습니다.")
    a_chars, a_starts, a_ends = _asr_char_times(asr_words)
    if not a_chars:
        raise ValueError("ASR 결과에 정렬할 단어가 없습니다.")

    # char-level global alignment
    matcher = SequenceMatcher(None, "".join(s_chars), "".join(a_chars), autojunk=False)
    char_start = [None] * len(s_chars)
    char_end = [None] * len(s_chars)
    matched_chars = 0
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            char_start[block.a + k] = a_starts[block.b + k]
            char_end[block.a + k] = a_ends[block.b + k]
        matched_chars += block.size

    # per-word times from matched chars
    result = [{"word": w, "start": None, "end": None} for w in words]
    for ci in range(len(s_chars)):
        if char_start[ci] is None:
            continue
        entry = result[owner[ci]]
        if entry["start"] is None or char_start[ci] < entry["start"]:
            entry["start"] = char_start[ci]
        if entry["end"] is None or char_end[ci] > entry["end"]:
            entry["end"] = char_end[ci]

    # interpolate words with no matched chars
    n = len(result)
    if all(e["start"] is None for e in result):
        raise ValueError("대본과 ASR이 전혀 일치하지 않습니다. 오디오를 확인하세요.")
    i = 0
    while i < n:
        if result[i]["start"] is not None:
            i += 1
            continue
        j = i
        while j < n and result[j]["start"] is None:
            j += 1
        prev_end = result[i - 1]["end"] if i > 0 else 0.0
        next_start = result[j]["start"] if j < n else audio_duration
        span = max(next_start - prev_end, 0.001 * (j - i))
        step = span / (j - i)
        for k in range(i, j):
            result[k]["start"] = prev_end + step * (k - i)
            result[k]["end"] = prev_end + step * (k - i + 1)
        i = j

    # enforce monotonic, rounded times
    cursor = 0.0
    for e in result:
        e["start"] = round(max(cursor, e["start"]), 3)
        e["end"] = round(max(e["start"] + 0.001, e["end"]), 3)
        cursor = e["end"]

    ratio = matched_chars / len(s_chars)
    return result, round(ratio, 4)
