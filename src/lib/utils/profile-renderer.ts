/**
 * Profile Renderer
 *
 * Utility for extracting and formatting profile data for display.
 * Consolidates the profile rendering logic used in ProfileWidget and ProfileWidgetComparison.
 *
 * Usage:
 * ```typescript
 * const profileData = formatProfileData(response.info, response.entity_type);
 * console.log(profileData.name, profileData.subtitle, profileData.details);
 * ```
 */

import { escapeHtml } from './dom';

export interface ProfileInfo {
  // Common fields
  full_name?: string;
  first_name?: string;
  last_name?: string;
  name?: string;
  logo_url?: string;
  photo_url?: string;

  // Team fields
  venue_name?: string;
  city?: string;
  country?: string;
  founded?: number;
  venue_capacity?: number;

  // Player fields
  team?: { name: string };
  position?: string;
  jersey_number?: number | string;
  height_inches?: number;
  weight_lbs?: number;
  college?: string;
  experience_years?: number;
  birth_country?: string;
  nationality?: string;
}

export interface ProfileDetail {
  label: string;
  value: string;
}

export interface FormattedProfile {
  name: string;
  logo: string;
  subtitle: string;
  details: ProfileDetail[];
}

/**
 * Format profile data for display
 * Extracts and formats name, logo, subtitle, and details from raw profile info
 */
export function formatProfileData(
  info: ProfileInfo | null | undefined,
  entityType: 'player' | 'team'
): FormattedProfile {
  if (!info) {
    return {
      name: 'Unknown',
      logo: '',
      subtitle: '',
      details: [],
    };
  }

  let name = '';
  let logo = '';
  let subtitle = '';
  const details: ProfileDetail[] = [];

  if (entityType === 'team') {
    // Team profile
    name = info.name || info.full_name || 'Unknown';
    logo = info.logo_url || '';
    subtitle = info.venue_name || info.city || '';

    if (info.country) {
      details.push({ label: 'Country', value: info.country });
    }
    if (info.founded) {
      details.push({ label: 'Founded', value: String(info.founded) });
    }
    if (info.venue_capacity) {
      details.push({ label: 'Capacity', value: info.venue_capacity.toLocaleString() });
    }
  } else {
    // Player profile
    name = info.full_name || `${info.first_name || ''} ${info.last_name || ''}`.trim() || 'Unknown';
    logo = info.photo_url || '';
    subtitle = info.team?.name || '';

    if (info.position) {
      details.push({ label: 'Position', value: info.position });
    }
    if (info.jersey_number) {
      details.push({ label: 'Number', value: `#${info.jersey_number}` });
    }
    if (info.height_inches) {
      const feet = Math.floor(info.height_inches / 12);
      const inches = info.height_inches % 12;
      details.push({ label: 'Height', value: `${feet}'${inches}"` });
    }
    if (info.weight_lbs) {
      details.push({ label: 'Weight', value: `${info.weight_lbs} lbs` });
    }
    if (info.college) {
      details.push({ label: 'College', value: info.college });
    }
    if (info.experience_years) {
      details.push({ label: 'Experience', value: `${info.experience_years} yrs` });
    }
    if (info.birth_country) {
      details.push({ label: 'Country', value: info.birth_country });
    } else if (info.nationality) {
      details.push({ label: 'Nationality', value: info.nationality });
    }
  }

  return { name, logo, subtitle, details };
}

/**
 * Render profile details as HTML
 * Creates HTML string for profile detail items
 */
export function renderProfileDetails(
  details: ProfileDetail[],
  options: {
    itemClass?: string;
    labelClass?: string;
    valueClass?: string;
  } = {}
): string {
  const {
    itemClass = 'pw-detail-item',
    labelClass = 'pw-detail-label',
    valueClass = 'pw-detail-value',
  } = options;

  return details.map(d => `
    <div class="${itemClass}">
      <span class="${labelClass}">${escapeHtml(d.label)}</span>
      <span class="${valueClass}">${escapeHtml(d.value)}</span>
    </div>
  `).join('');
}

/**
 * Format height from inches to feet and inches string
 */
export function formatHeight(inches: number): string {
  const feet = Math.floor(inches / 12);
  const remainingInches = inches % 12;
  return `${feet}'${remainingInches}"`;
}

/**
 * Format weight with unit
 */
export function formatWeight(lbs: number): string {
  return `${lbs} lbs`;
}
