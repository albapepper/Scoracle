/**
 * Date Utilities
 *
 * Shared helper functions for date formatting.
 */

/**
 * Format a date string for display (e.g., "Dec 25").
 * Returns empty string if date is invalid or not provided.
 */
export function formatDate(dateStr?: string): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}
