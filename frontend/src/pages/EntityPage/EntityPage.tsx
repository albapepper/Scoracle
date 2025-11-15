import React, { useMemo, useState, useEffect } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { Container, Title, Card, Button, Text, Stack, Box } from '@mantine/core';
import Widget from '../../components/Widget';
import { useTranslation } from 'react-i18next';
import { useSportContext } from '../../context/SportContext';
import { useThemeMode, getThemeColors } from '../../theme';
import { getEntityNameFromUrl, buildEntityUrl } from '../../utils/entityName';

export default function EntityPage() {
	const { entityType, entityId } = useParams();
	const { search } = useLocation();
	const type = (entityType || '').toLowerCase() === 'team' ? 'team' : 'player';
	const { t } = useTranslation();
	const { activeSport } = useSportContext();
	const { colorScheme } = useThemeMode();
	const colors = getThemeColors(colorScheme);
	const season = useMemo(() => String(new Date().getFullYear()), []);

	const [entityName, setEntityName] = useState<string>('');

	useEffect(() => {
		const name = getEntityNameFromUrl(search);
		if (name) setEntityName(name);
	}, [search]);

	// Build widget URLs
	const basicWidgetUrl = `/api/v1/${activeSport}/${type}s/${entityId}/widget/basic`;
	const baseUrl = `/api/v1/${activeSport}/${type}s/${entityId}/widget`;
	const widgetUrls = {
		offense: `${baseUrl}/offense${season ? `?season=${season}` : ''}`,
		defensive: `${baseUrl}/defensive${season ? `?season=${season}` : ''}`,
		specialTeams: `${baseUrl}/special-teams${season ? `?season=${season}` : ''}`,
		discipline: `${baseUrl}/discipline${season ? `?season=${season}` : ''}`,
	};

	// Determine card titles based on sport
	const isFootball = activeSport?.toUpperCase() === 'FOOTBALL' || activeSport?.toUpperCase() === 'EPL';
	const cardTitles = {
		topLeft: isFootball ? 'Attacking' : 'Offense',
		topRight: 'Defensive',
		bottomLeft: isFootball ? 'Set Pieces/Dead Ball' : 'Special Teams',
		bottomRight: 'Discipline',
	};

	const displayName = entityName || `${entityType} ${entityId}`;

	return (
		<Container size="lg" py="xl">
							<div className="entity-page-columns">
				{/* Entity Info Card - Perfect duplicate of MentionsPage top card */}
				<Card shadow="sm" p="lg" radius="md" withBorder>
					<Stack gap="lg" align="center">
						<Title order={2} style={{ color: colors.text.primary, textAlign: 'center' }}>{displayName}</Title>
						<Box w="100%" style={{ display: 'flex', justifyContent: 'center' }}>
							{basicWidgetUrl && <Widget url={basicWidgetUrl} />}
						</Box>
						<Button
							component={Link}
							to={buildEntityUrl('/mentions', type, entityId || '', activeSport, displayName)}
							style={{ backgroundColor: colors.ui.primary, color: 'white' }}
							size="md"
							fullWidth
						>
							{t('mentions.mentions', 'Mentions')}
						</Button>
					</Stack>
				</Card>

				{/* Advanced Stats Widgets - 2x2 grid, separate cards */}
				<div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
					<Card shadow="sm" p="lg" radius="md" withBorder>
						<Stack gap="xs" align="center">
							<Title order={4}>{cardTitles.topLeft}</Title>
							<Text size="sm" c="dimmed">{t('entityPage.comingSoon', 'Coming soon')}</Text>
						</Stack>
					</Card>
					<Card shadow="sm" p="lg" radius="md" withBorder>
						<Stack gap="xs" align="center">
							<Title order={4}>{cardTitles.topRight}</Title>
							<Text size="sm" c="dimmed">{t('entityPage.comingSoon', 'Coming soon')}</Text>
						</Stack>
					</Card>
					<Card shadow="sm" p="lg" radius="md" withBorder>
						<Stack gap="xs" align="center">
							<Title order={4}>{cardTitles.bottomLeft}</Title>
							<Text size="sm" c="dimmed">{t('entityPage.comingSoon', 'Coming soon')}</Text>
						</Stack>
					</Card>
					<Card shadow="sm" p="lg" radius="md" withBorder>
						<Stack gap="xs" align="center">
							<Title order={4}>{cardTitles.bottomRight}</Title>
							<Text size="sm" c="dimmed">{t('entityPage.comingSoon', 'Coming soon')}</Text>
						</Stack>
					</Card>
				</div>
			</div>
		</Container>
	);
}
