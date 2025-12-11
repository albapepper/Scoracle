/**
 * MentionsPage data loader
 */
import type { PageLoad } from './$types';
import { getEntity } from '$lib/data/entityApi';

export const load: PageLoad = async ({ params, url }) => {
  const { entityType, entityId } = params;
  const sport = url.searchParams.get('sport') || 'football';
  const nameFromUrl = url.searchParams.get('name') || '';

  try {
    const response = await getEntity(entityType, entityId, sport, {
      includeWidget: true,
      includeNews: true,
      includeEnhanced: true,
    });

    // Map backend response to expected format
    const mentions = Array.isArray(response.news) 
      ? response.news.map((article: Record<string, unknown>) => ({
          id: article.link || String(Math.random()),
          title: article.title || '',
          url: article.link || '',
          source: article.source || '',
          published_at: article.pub_date || '',
          summary: '',
          image_url: '',
        }))
      : [];

    // Use URL name if provided (from search), otherwise fall back to API response
    const displayName = nameFromUrl || response.entity?.name || `${entityType} ${entityId}`;
    
    // Override widget display_name with the better name
    if (response.widget) {
      response.widget.display_name = displayName;
    }

    return {
      entityType,
      entityId,
      sport,
      entity: response,
      mentions,
      entityName: displayName,
      error: null,
    };
  } catch (err) {
    console.error('Failed to load entity data:', err);
    return {
      entityType,
      entityId,
      sport,
      entity: null,
      mentions: [],
      entityName: nameFromUrl || `${entityType} ${entityId}`,
      error: err instanceof Error ? err.message : 'Failed to load data',
    };
  }
};
