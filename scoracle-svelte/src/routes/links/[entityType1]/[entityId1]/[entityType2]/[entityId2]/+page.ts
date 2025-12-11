/**
 * Links page data loader - loads two entities and their shared articles
 */
import type { PageLoad } from './$types';
import { getEntity } from '$lib/data/entityApi';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

export const load: PageLoad = async ({ params, url }) => {
  const { entityType1, entityId1, entityType2, entityId2 } = params;
  const sport = url.searchParams.get('sport') || 'football';
  const name1FromUrl = url.searchParams.get('name') || '';
  const name2FromUrl = url.searchParams.get('name2') || '';

  try {
    // Fetch both entities in parallel
    const [entity1Response, entity2Response] = await Promise.all([
      getEntity(entityType1, entityId1, sport, {
        includeWidget: true,
        includeNews: true,
        includeEnhanced: true,
      }),
      getEntity(entityType2, entityId2, sport, {
        includeWidget: true,
        includeNews: true,
        includeEnhanced: true,
      })
    ]);

    // Use URL names if provided, otherwise fall back to API response
    const entity1Name = name1FromUrl || entity1Response.entity?.name || `${entityType1} ${entityId1}`;
    const entity2Name = name2FromUrl || entity2Response.entity?.name || `${entityType2} ${entityId2}`;
    
    // Override widget display_names
    if (entity1Response.widget) {
      entity1Response.widget.display_name = entity1Name;
    }
    if (entity2Response.widget) {
      entity2Response.widget.display_name = entity2Name;
    }

    // Get articles from both entities
    const articles1Raw = entity1Response.news?.articles || [];
    const articles1 = articles1Raw.map((article: Record<string, unknown>) => ({
      id: String(article.link || Math.random()),
      title: String(article.title || ''),
      url: String(article.link || ''),
      source: String(article.source || ''),
      published_at: String(article.pub_date || ''),
      summary: '',
      image_url: '',
    }));

    const articles2Raw = entity2Response.news?.articles || [];
    const articles2 = articles2Raw.map((article: Record<string, unknown>) => ({
      id: String(article.link || Math.random()),
      title: String(article.title || ''),
      url: String(article.link || ''),
      source: String(article.source || ''),
      published_at: String(article.pub_date || ''),
      summary: '',
      image_url: '',
    }));

    // Find shared articles (by URL)
    const articles1Urls = new Set(articles1.map(a => a.url));
    const sharedArticles = articles2.filter(a => articles1Urls.has(a.url));

    return {
      entity1: {
        type: entityType1,
        id: entityId1,
        name: entity1Name,
        data: entity1Response,
      },
      entity2: {
        type: entityType2,
        id: entityId2,
        name: entity2Name,
        data: entity2Response,
      },
      sport,
      sharedArticles,
      error: null,
    };
  } catch (err) {
    console.error('Failed to load links data:', err);
    return {
      entity1: {
        type: entityType1,
        id: entityId1,
        name: name1FromUrl || `${entityType1} ${entityId1}`,
        data: null,
      },
      entity2: {
        type: entityType2,
        id: entityId2,
        name: name2FromUrl || `${entityType2} ${entityId2}`,
        data: null,
      },
      sport,
      sharedArticles: [],
      error: err instanceof Error ? err.message : 'Failed to load data',
    };
  }
};
