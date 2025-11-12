/**
 * Sport ID mapping utilities
 * Maps frontend sport IDs to backend sport codes
 */

/**
 * Maps frontend sport ID to backend sport code
 * Frontend uses lowercase IDs (e.g., 'football', 'nba', 'nfl')
 * Backend uses uppercase codes (e.g., 'FOOTBALL', 'NBA', 'NFL')
 */
export function mapSportToBackendCode(sportId: string): string {
  const mapping: Record<string, string> = {
    'football': 'FOOTBALL',
    'soccer': 'FOOTBALL', // Legacy support
    'nba': 'NBA',
    'basketball': 'NBA', // Legacy support
    'nfl': 'NFL',
    'american-football': 'NFL', // Legacy support
  };
  
  // Normalize input
  const normalized = sportId.toLowerCase().trim();
  
  // Return mapped code or uppercase the input as fallback
  return mapping[normalized] || sportId.toUpperCase();
}

/**
 * Maps backend sport code to frontend sport ID
 */
export function mapBackendCodeToSport(backendCode: string): string {
  const mapping: Record<string, string> = {
    'FOOTBALL': 'football',
    'NBA': 'nba',
    'NFL': 'nfl',
  };
  
  const normalized = backendCode.toUpperCase().trim();
  return mapping[normalized] || normalized.toLowerCase();
}

