/**
 * MentionsPage data loader
 */
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, url, fetch }) => {
  const { entityType, entityId } = params;
  const sport = url.searchParams.get('sport') || 'football';
  const nameFromUrl = url.searchParams.get('name') || '';

  // For now, return the basic data without API calls
  // API integration will work once backend is running
  return {
    entityType,
    entityId,
    sport,
    entity: null,
    mentions: [],
    entityName: nameFromUrl || `${entityType} ${entityId}`,
    error: null,
  };
};

