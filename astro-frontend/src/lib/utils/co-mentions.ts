/**
 * Co-mentions Utility
 *
 * Frontend implementation of entity co-mention detection.
 * Scans article titles for mentions of players/teams from the same sport.
 *
 * Matching algorithm:
 * - Requires 2+ name parts to match (reduces false positives)
 * - Handles accents/special characters via normalization
 * - Uses word boundaries to avoid partial matches
 */

export interface Entity {
  id: string;
  name: string;
  type: 'player' | 'team';
  team?: string;
}

export interface CoMention {
  entity: Entity;
  mentionCount: number;
}

export interface Article {
  title: string;
  link: string;
  pub_date?: string;
  source?: string;
}

/**
 * Normalize text for matching:
 * - Remove accents/diacritics (é → e, ñ → n)
 * - Convert to lowercase
 * - Remove non-alphanumeric characters (except spaces)
 * - Collapse multiple spaces
 */
export function normalizeText(text: string): string {
  if (!text) return '';

  // Remove accents/diacritics using Unicode normalization
  const normalized = text.normalize('NFD').replace(/[\u0300-\u036f]/g, '');

  // Lowercase, remove non-alphanumeric (keep spaces), collapse spaces
  return normalized
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Tokenize a name into individual parts.
 * Filters out common suffixes and short tokens.
 */
function tokenizeName(name: string): string[] {
  const normalized = normalizeText(name);
  const tokens = normalized.split(' ').filter(t => t.length > 0);

  // Filter out common suffixes that shouldn't count as name parts
  const suffixes = new Set(['jr', 'sr', 'ii', 'iii', 'iv', 'v']);

  return tokens.filter(t => !suffixes.has(t) && t.length >= 2);
}

/**
 * Check if an entity name matches text using 2-part matching.
 *
 * Rules:
 * - For single-word names (e.g., "Cowboys"): require exact word match
 * - For multi-word names: require at least 2 distinct tokens to match
 * - Tokens must appear as whole words (word boundaries)
 *
 * Examples:
 * - "Patrick Mahomes" matches "Mahomes threw to Patrick" (2 parts match)
 * - "Patrick Mahomes" does NOT match "Mahomes threw" (only 1 part)
 * - "Cowboys" matches "Cowboys win" (single-word, exact match)
 * - "AJ Brown" matches "AJ Brown caught" (2 parts match)
 */
export function entityMatchesText(entityName: string, text: string): boolean {
  const entityTokens = tokenizeName(entityName);
  const normalizedText = normalizeText(text);

  if (entityTokens.length === 0) return false;

  // For single-word names, require exact word match
  if (entityTokens.length === 1) {
    const token = entityTokens[0];
    // Require minimum 4 chars for single-word to avoid false positives
    if (token.length < 4) return false;
    const regex = new RegExp(`\\b${escapeRegex(token)}\\b`);
    return regex.test(normalizedText);
  }

  // For multi-word names, count how many tokens match
  let matchCount = 0;
  for (const token of entityTokens) {
    // Skip very short tokens (< 3 chars) to reduce false positives
    if (token.length < 3) continue;

    const regex = new RegExp(`\\b${escapeRegex(token)}\\b`);
    if (regex.test(normalizedText)) {
      matchCount++;
    }
  }

  // Require at least 2 tokens to match
  return matchCount >= 2;
}

/**
 * Escape special regex characters in a string.
 */
function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Find all entities mentioned in a list of articles.
 *
 * @param articles - Articles to scan
 * @param entities - All entities to check for
 * @param excludeEntityId - Entity ID to exclude (the searched entity)
 * @param excludeEntityType - Entity type to exclude
 * @returns Sorted list of co-mentions with counts
 */
export function findCoMentions(
  articles: Article[],
  entities: Entity[],
  excludeEntityId?: string,
  excludeEntityType?: string
): CoMention[] {
  // Track mention counts per entity
  const mentionCounts = new Map<string, { entity: Entity; count: number }>();

  for (const article of articles) {
    const text = article.title || '';
    if (!text) continue;

    // Track which entities we've already counted for this article
    // (avoid counting same entity multiple times per article)
    const countedInArticle = new Set<string>();

    for (const entity of entities) {
      // Skip the entity being searched for
      if (excludeEntityId && excludeEntityType) {
        if (entity.id === excludeEntityId && entity.type === excludeEntityType) {
          continue;
        }
      }

      const entityKey = `${entity.type}:${entity.id}`;

      // Skip if already counted in this article
      if (countedInArticle.has(entityKey)) continue;

      // Check if entity matches
      if (entityMatchesText(entity.name, text)) {
        countedInArticle.add(entityKey);

        const existing = mentionCounts.get(entityKey);
        if (existing) {
          existing.count++;
        } else {
          mentionCounts.set(entityKey, { entity, count: 1 });
        }
      }
    }
  }

  // Convert to array and sort by count (descending)
  const results: CoMention[] = Array.from(mentionCounts.values())
    .map(({ entity, count }) => ({ entity, mentionCount: count }))
    .sort((a, b) => b.mentionCount - a.mentionCount);

  return results;
}

/**
 * Load entity data for a sport from the static JSON files.
 * Uses localStorage cache if available and fresh.
 */
export async function loadEntitiesForSport(sport: string): Promise<Entity[]> {
  const sportLower = sport.toLowerCase();
  const cacheKey = 'scoracle_autocomplete_cache';
  const cacheExpiry = 24 * 60 * 60 * 1000; // 24 hours

  // Check localStorage cache first
  try {
    const cache = localStorage.getItem(cacheKey);
    if (cache) {
      const cachedData = JSON.parse(cache);
      if (cachedData[sportLower]) {
        const { data, timestamp } = cachedData[sportLower];
        if (Date.now() - timestamp < cacheExpiry) {
          return data;
        }
      }
    }
  } catch {
    // Cache read failed, continue to fetch
  }

  // Fetch from static JSON
  const response = await fetch(`/data/${sportLower}.json`);
  if (!response.ok) {
    throw new Error(`Failed to load entity data for ${sport}`);
  }

  const json = await response.json();
  const items: Entity[] = [];

  // Handle players
  if (json.players?.items) {
    items.push(
      ...json.players.items.map((p: any) => ({
        id: String(p.id),
        name: p.name,
        type: 'player' as const,
        team: p.currentTeam || p.team,
      }))
    );
  } else if (Array.isArray(json.players)) {
    items.push(
      ...json.players.map((p: any) => ({
        id: String(p.id),
        name: p.name,
        type: 'player' as const,
        team: p.currentTeam || p.team,
      }))
    );
  }

  // Handle teams
  if (json.teams?.items) {
    items.push(
      ...json.teams.items.map((t: any) => ({
        id: String(t.id),
        name: t.name,
        type: 'team' as const,
      }))
    );
  } else if (Array.isArray(json.teams)) {
    items.push(
      ...json.teams.map((t: any) => ({
        id: String(t.id),
        name: t.name,
        type: 'team' as const,
      }))
    );
  }

  // Update localStorage cache
  try {
    const cache = localStorage.getItem(cacheKey);
    const newCache = cache ? JSON.parse(cache) : {};
    newCache[sportLower] = { data: items, timestamp: Date.now() };
    localStorage.setItem(cacheKey, JSON.stringify(newCache));
  } catch {
    // Cache write failed, continue anyway
  }

  return items;
}

/**
 * Fetch news articles for an entity.
 */
export async function fetchArticles(
  entityName: string,
  apiUrl: string,
  hours: number = 48
): Promise<Article[]> {
  const response = await fetch(
    `${apiUrl}/news/${encodeURIComponent(entityName)}?hours=${hours}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch articles: ${response.status}`);
  }

  const data = await response.json();
  return data.articles || [];
}

/**
 * Main function to get co-mentions for an entity.
 *
 * @param entityName - Name of the entity to search for
 * @param entityId - ID of the entity (to exclude from results)
 * @param entityType - Type of the entity (to exclude from results)
 * @param sport - Sport code (FOOTBALL, NBA, NFL)
 * @param apiUrl - Base API URL
 * @param hours - Hours to look back for news
 * @returns List of co-mentioned entities with counts
 */
export async function getCoMentions(
  entityName: string,
  entityId: string,
  entityType: 'player' | 'team',
  sport: string,
  apiUrl: string,
  hours: number = 48
): Promise<CoMention[]> {
  // Fetch articles and entities in parallel
  const [articles, entities] = await Promise.all([
    fetchArticles(entityName, apiUrl, hours),
    loadEntitiesForSport(sport),
  ]);

  if (articles.length === 0) {
    return [];
  }

  // Find co-mentions
  return findCoMentions(articles, entities, entityId, entityType);
}
