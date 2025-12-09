import React, { useState, useEffect } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { Container, Title, Card, Button, Text, Stack, ActionIcon, Tooltip, SimpleGrid, Group, Flex } from '@mantine/core';
import { IconChartBar, IconTable } from '@tabler/icons-react';
import Widget from '../../components/Widget';
import { useTranslation } from 'react-i18next';
import { useSportContext } from '../../context/SportContext';
import { useThemeMode, getThemeColors } from '../../theme';
import { getEntityNameFromUrl, buildEntityUrl } from '../../utils/entityName';
import { useEntity } from '../../features/entities/hooks/useEntity';
import './EntityPage.css';

export default function EntityPage() {
  const { entityType, entityId } = useParams();
  const { search } = useLocation();
  const type = (entityType || '').toLowerCase() === 'team' ? 'team' : 'player';
  const { t } = useTranslation();
  const { activeSport } = useSportContext();
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);

  const [entityName, setEntityName] = useState<string>('');
  const [viewModes, setViewModes] = useState<Record<string, 'graph' | 'table'>>({
    topLeft: 'graph',
    topRight: 'graph',
    bottomLeft: 'graph',
    bottomRight: 'graph',
  });

  // Use unified entity API with enhanced data (photos, etc.)
  const { data: entityData, isLoading, error } = useEntity({
    entityType: type,
    entityId: entityId || '',
    includeWidget: true,
    includeEnhanced: true,  // Get photos, positions from API-Sports
    includeNews: false,     // News is shown on MentionsPage
    enabled: !!entityId,
  });

  useEffect(() => {
    const name = getEntityNameFromUrl(search);
    if (name) setEntityName(name);
  }, [search]);

  // Use entity name from API if available
  const displayName = entityData?.entity?.name || entityName || `${entityType} ${entityId}`;

  // Determine card titles based on sport
  const isFootball = activeSport?.toUpperCase() === 'FOOTBALL';
  const isNFL = activeSport?.toLowerCase() === 'nfl';
  const cardTitles = {
    topLeft: isFootball ? 'Attacking' : 'Offense',
    topRight: 'Defensive',
    bottomLeft: isNFL ? 'Special Teams' : 'Dead Ball',
    bottomRight: 'Discipline',
  };

  const toggleView = (key: keyof typeof viewModes) => {
    setViewModes((prev) => ({
      ...prev,
      [key]: prev[key] === 'graph' ? 'table' : 'graph',
    }));
  };

  const renderCard = (key: keyof typeof viewModes, title: string) => {
    const isGraph = viewModes[key] === 'graph';
    const icon = isGraph ? <IconTable size={18} /> : <IconChartBar size={18} />;
    const tooltip = isGraph ? t('entityPage.switchToTable', 'Switch to table view') : t('entityPage.switchToGraph', 'Switch to graph view');

    return (
      <div className={`entity-flip-card-shell ${isGraph ? '' : 'is-flipped'}`} key={key}>
        <div className="entity-flip-card-inner">
          <Card shadow="sm" p="lg" radius="md" withBorder className="entity-flip-card-face entity-flip-card-front">
            <Group justify="space-between" align="center" pb="xs">
              <Title
                order={4}
                c={colorScheme === 'dark' ? colors.text.accent : undefined}
              >
                {title}
              </Title>
              <Tooltip label={tooltip} withArrow>
                <ActionIcon
                  variant="light"
                  aria-label={tooltip}
                  onClick={() => toggleView(key)}
                  size="sm"
                >
                  {icon}
                </ActionIcon>
              </Tooltip>
            </Group>
            <Text size="sm" c="dimmed">
              {t('entityPage.graphComingSoon', 'Graph view coming soon')}
            </Text>
          </Card>

          <Card shadow="sm" p="lg" radius="md" withBorder className="entity-flip-card-face entity-flip-card-back">
            <Group justify="space-between" align="center" pb="xs">
              <Title
                order={4}
                c={colorScheme === 'dark' ? colors.text.accent : undefined}
              >
                {title}
              </Title>
              <Tooltip label={tooltip} withArrow>
                <ActionIcon
                  variant="light"
                  aria-label={tooltip}
                  onClick={() => toggleView(key)}
                  size="sm"
                >
                  {icon}
                </ActionIcon>
              </Tooltip>
            </Group>
            <Text size="sm" c="dimmed">
              {t('entityPage.tableComingSoon', 'Table view coming soon')}
            </Text>
          </Card>
        </div>
      </div>
    );
  };

  return (
    <Container size="lg" py="xl">
      <div className="entity-page-columns">
        {/* Entity Info Card */}
        <Card shadow="sm" p="lg" radius="md" withBorder>
          <Stack gap="lg" align="center">
            <Title order={2} c={colors.text.primary} ta="center">{displayName}</Title>
            <Flex w="100%" justify="center">
              <Widget 
                data={entityData?.widget} 
                loading={isLoading}
                error={error?.message}
              />
            </Flex>
            <Button
              component={Link}
              to={buildEntityUrl('/mentions', type, entityId || '', activeSport, displayName)}
              bg={colors.ui.primary}
              c="white"
              size="md"
              fullWidth
            >
              {t('mentions.mentions', 'Mentions')}
            </Button>
          </Stack>
        </Card>

        {/* Advanced Stats Widgets - 2x2 grid */}
        <SimpleGrid cols={2} spacing="md" mt="md">
          {renderCard('topLeft', cardTitles.topLeft)}
          {renderCard('topRight', cardTitles.topRight)}
          {renderCard('bottomLeft', cardTitles.bottomLeft)}
          {renderCard('bottomRight', cardTitles.bottomRight)}
        </SimpleGrid>
      </div>
    </Container>
  );
}
