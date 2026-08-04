export function captionWidthLimitPct(safeMarginPct) {
  return 100 - safeMarginPct * 2;
}

export function constrainedCaptionWidthPct(captionMaxWidthPct, safeMarginPct) {
  return Number.isFinite(captionMaxWidthPct)
    ? Math.min(captionMaxWidthPct, captionWidthLimitPct(safeMarginPct))
    : null;
}

export function stripCaptionHighlightPunctuation(value) {
  return value.replace(/[.,!?…·"'“”‘’()]/g, '');
}

export function captionHighlightColor(token, {
  highlightWords1,
  highlightWords2,
  highlightColor1,
  highlightColor2,
}) {
  const stripped = stripCaptionHighlightPunctuation(token);
  if (stripped && highlightWords2.some((word) => word && stripped.includes(word))) return highlightColor2;
  if (stripped && highlightWords1.some((word) => word && stripped.includes(word))) return highlightColor1;
  return null;
}

function phraseContainsToken(tokens, tokenIndex, phrase) {
  const parts = phrase.split(/\s+/).filter(Boolean);
  if (parts.length < 2) return false;
  return parts.some((_, phraseIndex) => {
    const start = tokenIndex - phraseIndex;
    if (start < 0 || start + parts.length > tokens.length) return false;
    return parts.every((part, offset) => {
      const stripped = stripCaptionHighlightPunctuation(tokens[start + offset]);
      return stripped.includes(part);
    });
  });
}

export function captionHighlightColorAt(tokens, tokenIndex, options) {
  const token = tokens[tokenIndex] ?? '';
  const phraseColor = (words, color) => words.some((word) => (
    word.includes(' ') ? phraseContainsToken(tokens, tokenIndex, word) : false
  )) ? color : null;
  return phraseColor(options.highlightWords2, options.highlightColor2)
    ?? phraseColor(options.highlightWords1, options.highlightColor1)
    ?? captionHighlightColor(token, options);
}

export function highlightBoxTextColor(hex) {
  const compact = hex.replace('#', '');
  const expanded = compact.length === 3
    ? compact.split('').map((character) => character + character).join('')
    : compact;
  const numeric = Number.parseInt(expanded, 16);
  const luma = 0.299 * ((numeric >> 16) & 255)
    + 0.587 * ((numeric >> 8) & 255)
    + 0.114 * (numeric & 255);
  return luma > 150 ? '#111111' : '#ffffff';
}

export function captionHighlightBoxStyle(hex) {
  return {
    color: highlightBoxTextColor(hex),
    backgroundColor: hex,
    WebkitTextStroke: '0px transparent',
    textShadow: 'none',
    padding: '0.02em 0.14em',
    borderRadius: '0.12em',
  };
}
