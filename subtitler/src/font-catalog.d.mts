export type FontDescriptor = Readonly<{family: string; file: string}>

export const FONT_CATALOG: Readonly<Record<string, FontDescriptor>>
export function fontDescriptor(key: string): FontDescriptor | null
