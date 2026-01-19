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
 * Normalize text for matching.
 *
 * IMPORTANT: This function must stay in sync with the backend version
 * in backend/app/utils/text.py:normalize_text(). Both implementations
 * should produce identical output for the same input.
 *
 * Algorithm:
 * 1. Strip accents/diacritics using Unicode NFD normalization (é → e, ñ → n)
 * 2. Convert to lowercase
 * 3. Remove non-alphanumeric characters (except spaces)
 * 4. Collapse multiple spaces
 * 5. Trim leading/trailing whitespace
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
 *
 * @param entityName - Entity name to match
 * @param text - Text to search in
 * @param requiredMatches - Minimum tokens required (default: 2 for multi-word)
 */
export function entityMatchesText(
  entityName: string,
  text: string,
  requiredMatches: number = 2
): boolean {
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

  // Require at least requiredMatches tokens to match
  return matchCount >= requiredMatches;
}

/**
 * Count how many meaningful tokens a name has after normalization.
 * Used to identify "long names" (3+ parts) common in South American/Portuguese names.
 */
export function getNameTokenCount(name: string): number {
  return tokenizeName(name).length;
}

/**
 * Escape special regex characters in a string.
 */
function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Build an index of surname tokens to player IDs.
 * Used to detect when multiple players share the same surname.
 *
 * A "surname" is defined as any token with 4+ characters from the player's name.
 * This helps identify common surnames like "Fernandes", "Silva", "Santos".
 */
function buildSurnameIndex(players: Entity[]): Map<string, string[]> {
  const index = new Map<string, string[]>();

  for (const player of players) {
    const tokens = tokenizeName(player.name);
    for (const token of tokens) {
      // Only index substantial tokens (4+ chars) as potential surnames
      if (token.length >= 4) {
        const existing = index.get(token) || [];
        existing.push(player.id);
        index.set(token, existing);
      }
    }
  }

  return index;
}

/**
 * Get which tokens from a name match in the text.
 * Returns only tokens with 3+ characters that appear as whole words.
 */
function getMatchingTokens(name: string, normalizedText: string): string[] {
  const tokens = tokenizeName(name);
  return tokens.filter(token => {
    if (token.length < 3) return false;
    const regex = new RegExp(`\\b${escapeRegex(token)}\\b`);
    return regex.test(normalizedText);
  });
}

/**
 * Check if a player's team is mentioned in the article.
 * Compares normalized team names for flexible matching.
 */
function isPlayerTeamInArticle(
  player: Entity,
  teamNamesInArticle: Set<string>
): boolean {
  if (!player.team) return false;
  const normalizedPlayerTeam = normalizeText(player.team);
  return teamNamesInArticle.has(normalizedPlayerTeam);
}

/**
 * Find all entities mentioned in a list of articles.
 *
 * Matching rules:
 * - Teams: standard 2-token or single-word matching
 * - Players with 2+ tokens matching: always valid
 * - Players with 1 token matching (long names only):
 *   - If surname is unique: allow the match
 *   - If surname is shared by multiple players: "Best Match Wins"
 *     - Player whose team is in the article wins the surname
 *     - Only 1 player per shared surname per article
 *     - If no player's team is mentioned, require 2+ tokens
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
  // Separate teams and players for efficient lookup
  const teams = entities.filter(e => e.type === 'team');
  const players = entities.filter(e => e.type === 'player');

  // Build surname collision index
  const surnameIndex = buildSurnameIndex(players);

  // Track mention counts per entity
  const mentionCounts = new Map<string, { entity: Entity; count: number }>();

  for (const article of articles) {
    const text = article.title || '';
    if (!text) continue;

    const normalizedText = normalizeText(text);

    // Track which entities we've already counted for this article
    const countedInArticle = new Set<string>();

    // Track which shared surnames have been claimed by a player in this article
    const claimedSurnames = new Set<string>();

    // First pass: find all teams mentioned in this article
    const teamsInArticle: Entity[] = [];
    const teamNamesInArticle = new Set<string>();

    for (const team of teams) {
      if (excludeEntityId && excludeEntityType) {
        if (team.id === excludeEntityId && team.type === excludeEntityType) {
          continue;
        }
      }

      if (entityMatchesText(team.name, text)) {
        teamsInArticle.push(team);
        teamNamesInArticle.add(normalizeText(team.name));

        const teamKey = `team:${team.id}`;
        countedInArticle.add(teamKey);

        const existing = mentionCounts.get(teamKey);
        if (existing) {
          existing.count++;
        } else {
          mentionCounts.set(teamKey, { entity: team, count: 1 });
        }
      }
    }

    const hasTeamContext = teamsInArticle.length > 0;

    // Helper to count a player match
    const countPlayer = (player: Entity) => {
      const playerKey = `player:${player.id}`;
      countedInArticle.add(playerKey);
      const existing = mentionCounts.get(playerKey);
      if (existing) {
        existing.count++;
      } else {
        mentionCounts.set(playerKey, { entity: player, count: 1 });
      }
    };

    // Second pass: find players
    for (const player of players) {
      if (excludeEntityId && excludeEntityType) {
        if (player.id === excludeEntityId && player.type === excludeEntityType) {
          continue;
        }
      }

      const playerKey = `player:${player.id}`;
      if (countedInArticle.has(playerKey)) continue;

      const nameTokenCount = getNameTokenCount(player.name);
      const isLongName = nameTokenCount >= 3;
      const matchingTokens = getMatchingTokens(player.name, normalizedText);

      // Case 1: Strong match (2+ tokens) - always valid
      if (matchingTokens.length >= 2) {
        countPlayer(player);
        continue;
      }

      // Case 2: Weak match (1 token) - only for long names with team context
      if (matchingTokens.length === 1 && isLongName && hasTeamContext) {
        const matchedToken = matchingTokens[0];

        // Check if this token is a shared surname
        const playersWithToken = surnameIndex.get(matchedToken) || [];
        const isSharedSurname = playersWithToken.length > 1;

        if (isSharedSurname) {
          // Shared surname: "Best Match Wins" logic
          // Only allow if this player's team is mentioned AND surname not claimed

          if (claimedSurnames.has(matchedToken)) {
            // Another player already claimed this surname for this article
            continue;
          }

          const playerTeamMentioned = isPlayerTeamInArticle(
            player,
            teamNamesInArticle
          );

          if (playerTeamMentioned) {
            // This player's team is mentioned - they win the surname
            claimedSurnames.add(matchedToken);
            countPlayer(player);
          }
          // If player's team not mentioned, skip (no match for shared surnames)
        } else {
          // Unique surname - safe to match with 1 token
          countPlayer(player);
        }
      }
      // Case 3: No match or insufficient tokens - skip
    }
  }

  // Convert to array and sort by count (descending)
  const results: CoMention[] = Array.from(mentionCounts.values())
    .map(({ entity, count }) => ({ entity, mentionCount: count }))
    .sort((a, b) => b.mentionCount - a.mentionCount);

  return results;
}

/**
 * Load entity data for a sport from the preloaded EntityDataStore.
 * Falls back to direct fetch if store not initialized.
 */
export async function loadEntitiesForSport(sport: string): Promise<Entity[]> {
  const { entityDataStore } = await import('./entity-data-store');

  // Get from preloaded store (instant if already loaded)
  const entities = await entityDataStore.getEntities(sport);

  // EntityDataStore returns AutocompleteEntity[], which is compatible with Entity[]
  return entities as Entity[];
}

/**
 * Fetch news articles for an entity.
 *
 * Uses the unified news endpoint which resolves entity name on the backend.
 */
export async function fetchArticles(
  entityType: 'player' | 'team',
  entityId: string,
  apiUrl: string,
  sport: string,
  limit: number = 20
): Promise<Article[]> {
  const params = new URLSearchParams();
  params.set('sport', sport.toUpperCase());
  params.set('limit', limit.toString());

  const response = await fetch(
    `${apiUrl}/news/${entityType}/${entityId}?${params.toString()}`
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
 * @param entityId - ID of the entity (to exclude from results)
 * @param entityType - Type of the entity (to exclude from results)
 * @param sport - Sport code (FOOTBALL, NBA, NFL)
 * @param apiUrl - Base API URL
 * @param limit - Max articles to fetch
 * @returns List of co-mentioned entities with counts
 */
export async function getCoMentions(
  entityId: string,
  entityType: 'player' | 'team',
  sport: string,
  apiUrl: string,
  limit: number = 20
): Promise<CoMention[]> {
  // Fetch articles and entities in parallel
  const [articles, entities] = await Promise.all([
    fetchArticles(entityType, entityId, apiUrl, sport, limit),
    loadEntitiesForSport(sport),
  ]);

  if (articles.length === 0) {
    return [];
  }

  // Find co-mentions
  return findCoMentions(articles, entities, entityId, entityType);
}
