import React, { useMemo } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { Container, Title, Card, Button, Text, Stack, Group, Badge, Loader } from '@mantine/core';
import Widget from '../../components/Widget';
import { useTranslation } from 'react-i18next';
import { useSportContext } from '../../context/SportContext';
import { useFastNews } from '../../features/news/useFastNews';

export default function EntityPage() {
	const { entityType, entityId } = useParams();
	const { search } = useLocation();
	const type = (entityType || '').toLowerCase() === 'team' ? 'team' : 'player';
	const { t } = useTranslation();
	const { activeSport } = useSportContext();
	const season = useMemo(() => String(new Date().getFullYear()), []);

	const usp = new URLSearchParams(search);
	const qName = usp.get('name') || '';
	const { data: fastNews, isLoading: fastLoading } = useFastNews({
		query: qName,
		mode: type as any,
		enabled: !!qName,
		hours: 48,
	});

	// Build widget URLs
	const baseUrl = `/api/v1/${activeSport}/${type}s/${entityId}/widget`;
	const widgetUrls = {
		offense: `${baseUrl}/offense${season ? `?season=${season}` : ''}`,
		defensive: `${baseUrl}/defensive${season ? `?season=${season}` : ''}`,
		specialTeams: `${baseUrl}/special-teams${season ? `?season=${season}` : ''}`,
		discipline: `${baseUrl}/discipline${season ? `?season=${season}` : ''}`,
	};

	return (
		<Container size="lg" py="xl">
							<div className="entity-page-columns">
				<Card withBorder p="lg">
									<div className="entity-page-header-row">
						<Title order={2}>{t('entityPage.title', 'Statistical Profile')}</Title>
						<Button
							component={Link}
							to={`/mentions/${type}/${entityId}?sport=${encodeURIComponent(activeSport)}`}
							variant="light"
						>
							{t('entityPage.recentMentions', 'Recent Mentions')}
						</Button>
							</div>
				</Card>

				<Card withBorder p="lg">
					<Stack gap="md">
						<Widget url={widgetUrls.offense} />
						<Widget url={widgetUrls.defensive} />
						<Widget url={widgetUrls.specialTeams} />
						<Widget url={widgetUrls.discipline} />
					</Stack>
				</Card>
				<Card withBorder p="lg">
					<Title order={4}>Fast Mentions</Title>
					{fastLoading && <Loader size="sm" />}
					{!fastLoading && fastNews && (
						<Stack gap={6} mt="sm">
							{type === 'player' && (
								<Stack gap={4}>
									<Title order={6}>Linked Teams</Title>
									{(fastNews as any).linked_teams?.slice(0,10).map((row: any) => (
										<Group key={row[0]} justify="space-between">
											<Text>{row[0]}</Text>
											<Badge>{row[1]}</Badge>
										</Group>
									)) || <Text size="xs" c="dimmed">None</Text>}
								</Stack>
							)}
							{type === 'team' && (
								<Stack gap={4}>
									<Title order={6}>Linked Players</Title>
									{(fastNews as any).linked_players?.slice(0,10).map((row: any) => (
										<Group key={row[0]} justify="space-between">
											<Text>{row[0]}</Text>
											<Badge>{row[1]}</Badge>
										</Group>
									)) || <Text size="xs" c="dimmed">None</Text>}
								</Stack>
							)}
						</Stack>
					)}
				</Card>
			</div>
		</Container>
	);
}
