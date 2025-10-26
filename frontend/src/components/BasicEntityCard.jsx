import React from 'react';
import { Card, Group, Stack, Title, Text, Badge, Divider } from '@mantine/core';
import theme from '../theme';
import { useTranslation } from 'react-i18next';

/**
 * BasicEntityCard
 * Displays a cross-sport basic entity summary card.
 * Renders only available fields (graceful degradation across sports/providers).
 *
 * Props:
 * - entityType: 'player' | 'team'
 * - sport: string (e.g., 'NBA', 'EPL')
 * - summary: object with fields like
 *   - player: { id, full_name or first_name/last_name, position, team_name, team_id, team_abbreviation, nationality, age, league, years_pro }
 *   - team: { id, name, abbreviation, city, conference, division, league, founded }
 * - actions: optional React node to render primary action area (e.g., link to profile)
 * - footer: optional React node to render at bottom (e.g., recent mentions link)
 */
export default function BasicEntityCard({ entityType, sport, summary, actions, footer }) {
  const { t } = useTranslation();
  if (!summary) return null;

  const isPlayer = entityType === 'player';
  const displayName = isPlayer
    ? (summary.full_name || `${summary.first_name || ''} ${summary.last_name || ''}`.trim())
    : (summary.name || '');

  const subline = () => {
    if (isPlayer) {
      const parts = [];
      if (summary.position) parts.push(summary.position);
      if (summary.team_name) parts.push(summary.team_name);
      return parts.join(' | ');
    }
    // team
    const parts = [];
    if (summary.city) parts.push(summary.city);
    if (summary.conference) parts.push(summary.conference);
    if (summary.division) parts.push(summary.division);
    return parts.join(' | ');
  };

  const facts = [];
  // Common cross-sport facts for player
  if (isPlayer) {
    if (summary.age !== undefined && summary.age !== null) facts.push({ label: t('entity.age'), value: String(summary.age) });
    if (summary.nationality) facts.push({ label: t('entity.nationality'), value: summary.nationality });
    if (summary.team_name) facts.push({ label: t('entity.currentTeam'), value: summary.team_name });
    if (summary.league) facts.push({ label: t('entity.league'), value: summary.league });
    if (summary.years_pro !== undefined && summary.years_pro !== null) facts.push({ label: t('entity.yearsPro'), value: String(summary.years_pro) });
  } else {
    // Team facts
    if (summary.league) facts.push({ label: t('entity.league'), value: summary.league });
    if (summary.city) facts.push({ label: t('entity.city'), value: summary.city });
    if (summary.conference) facts.push({ label: t('entity.conference'), value: summary.conference });
    if (summary.division) facts.push({ label: t('entity.division'), value: summary.division });
  }

  return (
    <Card shadow="sm" p="lg" radius="md" withBorder>
      <Stack spacing="sm">
        <Group position="apart" align="center">
          <div>
            <Title order={2} style={{ color: theme.colors.text.primary }}>{displayName}</Title>
            {subline() && (
              <Text size="sm" c="dimmed">{subline()}</Text>
            )}
          </div>
          {sport && (
            <Badge variant="light" color="primary">{sport}</Badge>
          )}
        </Group>

        {facts.length > 0 && (
          <Group grow spacing="md" mt="xs">
            {facts.map((f) => (
              <Card key={f.label} withBorder p="md">
                <Text fw={700} size="sm" c="dimmed">{f.label}</Text>
                <Text fw={600}>{f.value}</Text>
              </Card>
            ))}
          </Group>
        )}

        {actions && (
          <div>
            <Divider my="sm" />
            {actions}
          </div>
        )}

        {footer && (
          <div>
            <Divider my="sm" />
            {footer}
          </div>
        )}
      </Stack>
    </Card>
  );
}
