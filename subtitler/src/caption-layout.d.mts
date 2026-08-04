export type CaptionHighlightOptions = {
  highlightWords1: string[]
  highlightWords2: string[]
  highlightColor1: string
  highlightColor2: string
}

export function captionWidthLimitPct(safeMarginPct: number): number
export function constrainedCaptionWidthPct(captionMaxWidthPct: number | undefined, safeMarginPct: number): number | null
export function stripCaptionHighlightPunctuation(value: string): string
export function captionHighlightColor(token: string, options: CaptionHighlightOptions): string | null
export function captionHighlightColorAt(tokens: string[], tokenIndex: number, options: CaptionHighlightOptions): string | null
export function highlightBoxTextColor(hex: string): string
export function captionHighlightBoxStyle(hex: string): {
  color: string
  backgroundColor: string
  WebkitTextStroke: string
  textShadow: string
  padding: string
  borderRadius: string
}
