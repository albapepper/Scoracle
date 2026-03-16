export function sanitizeUrl(input: string | null | undefined): string {
  if (!input) return '';
  try {
    const url = new URL(input, window.location.origin);
    const protocol = url.protocol.toLowerCase();
    if (protocol === 'http:' || protocol === 'https:') {
      return url.href;
    }
  } catch {
    return '';
  }
  return '';
}
