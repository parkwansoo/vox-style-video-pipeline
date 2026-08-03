"""Shorten the pauses in a narration without touching the speech itself.

Gemini TTS leaves a lot of dead air: across three finished videos only 55~57%
of the runtime was actual speech, with 27~32% silence (see PROGRESS.md
2026-08-03). Trimming it before clip splitting lets each cut be sized against
real speech instead of pauses.

Pauses are NOT all the same, so a single uniform clamp is wrong. A gap after a
period is the listener's beat between thoughts; a gap inside a sentence is just
breathing. Silence length alone cannot tell them apart — in a measured chapter a
sentence boundary and an inner breath were both exactly 0.59s — so the decision
is made from the SCRIPT: a silence starting within `near` seconds of a
sentence-final word keeps `sentence_keep`, anything else keeps `inner_keep`.
Silences shorter than `mincut` are left completely alone (borrowed from
auto-editor's --smooth mincut, which avoids jittering on tiny gaps).

Because sentence positions come from the alignment, the caller must already
have word timings — tts.py runs one alignment pass to get them, compresses,
then re-aligns against the compressed audio for the final words.json.
"""
import re
import subprocess
import sys

SENTENCE_ENDINGS = (".", "?", "!", "…")


def _run(cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"명령 실패: {' '.join(str(c) for c in cmd[:6])}...\n{r.stderr[-1500:]}")
    return r


def ffprobe_duration(path):
    r = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "default=noprint_wrappers=1:nokey=1", str(path)])
    return float(r.stdout.strip())


def detect_silences(path, threshold="-35dB", min_dur=0.15):
    """Return [(start, end), ...] of silent stretches, in seconds."""
    out = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
                "-af", f"silencedetect=noise={threshold}:d={min_dur}",
                "-f", "null", "-"], check=False).stderr
    starts = [float(m) for m in re.findall(r"silence_start: (-?[\d.]+)", out)]
    ends = [float(m) for m in re.findall(r"silence_end: (-?[\d.]+)", out)]
    if len(ends) < len(starts):  # 파일 끝까지 무음이면 silence_end가 안 찍힌다
        ends.append(ffprobe_duration(path))
    return [(s, e) for s, e in zip(starts, ends) if e > s]


def sentence_end_times(words):
    """End times of words that close a sentence (from the aligned script)."""
    return [float(w["end"]) for w in words
            if str(w.get("word", "")).rstrip().endswith(SENTENCE_ENDINGS)]


def plan_cuts(silences, sent_ends, sentence_keep, inner_keep, mincut, near):
    """Decide how much to remove from each silence.

    Returns (cuts, stats) where cuts is [(from, to), ...] of removed ranges.
    """
    cuts = []
    stats = {"sentence": 0, "inner": 0, "untouched": 0, "removed": 0.0}
    for start, end in silences:
        length = end - start
        if length < mincut:
            stats["untouched"] += 1
            continue
        if any(abs(start - t) <= near for t in sent_ends):
            keep, kind = sentence_keep, "sentence"
        else:
            keep, kind = inner_keep, "inner"
        stats[kind] += 1
        if length > keep:
            cuts.append((start + keep, end))
            stats["removed"] += length - keep
    return cuts, stats


def _keep_ranges(cuts, total):
    """Invert the cut list into the ranges we keep."""
    keeps, prev = [], 0.0
    for c0, c1 in cuts:
        if c0 > prev:
            keeps.append((prev, c0))
        prev = c1
    if prev < total - 1e-3:
        keeps.append((prev, total))
    return keeps


def apply_cuts(src, dst, cuts, total, bitrate="160k"):
    """Write `src` minus `cuts` to `dst`, concatenating the kept ranges."""
    keeps = _keep_ranges(cuts, total)
    if not keeps:
        sys.exit("무음 압축 결과가 비었습니다. 임계값(--silence-threshold)을 확인하세요.")
    parts, labels = [], []
    for i, (s, e) in enumerate(keeps):
        parts.append(f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS[k{i}]")
        labels.append(f"[k{i}]")
    graph = ";".join(parts) + ";" + "".join(labels) + \
        f"concat=n={len(keeps)}:v=0:a=1[out]"
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(src),
          "-filter_complex", graph, "-map", "[out]",
          "-b:a", bitrate, str(dst)])


def compress(src, dst, words, sentence_keep=0.45, inner_keep=0.25,
             mincut=0.20, near=0.35, threshold="-35dB", min_dur=0.15,
             bitrate="160k"):
    """Compress pauses in `src` into `dst`. Returns a stats dict.

    `words` are aligned word timings for `src` (used only to locate sentence
    boundaries). If nothing is worth cutting, `dst` is a plain copy so callers
    can rely on it always existing.
    """
    total = ffprobe_duration(src)
    silences = detect_silences(src, threshold=threshold, min_dur=min_dur)
    cuts, stats = plan_cuts(silences, sentence_end_times(words),
                            sentence_keep, inner_keep, mincut, near)
    if cuts:
        apply_cuts(src, dst, cuts, total, bitrate=bitrate)
    else:
        _run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-c", "copy", str(dst)])
    return {
        "duration_before": round(total, 2),
        "duration_after": round(ffprobe_duration(dst), 2),
        "removed_seconds": round(stats["removed"], 2),
        "silences_found": len(silences),
        "at_sentence_end": stats["sentence"],
        "inside_sentence": stats["inner"],
        "left_untouched": stats["untouched"],
    }
