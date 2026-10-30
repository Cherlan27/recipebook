/** Splits stored free text into its non-empty, trimmed lines. */
export function toLines(text: string | null): string[] {
  if (text === null) return []
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line !== '')
}
