import React, { useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Card, Button, Text } from '@mantine/core';
import PlayerWidgetServer from '../../components/PlayerWidgetServer';
import { useTranslation } from 'react-i18next';
// Using JS context without TS types; suppress type checking
// @ts-ignore
import { useSportContext } from '../../context/SportContext';

export default function EntityPage() {
	const { entityType, entityId } = useParams();
	const type = (entityType || '').toLowerCase() === 'team' ? 'team' : 'player';
	const { t } = useTranslation();
	const { activeSport } = useSportContext();
	const season = useMemo(() => String(new Date().getFullYear()), []);

	// We have removed legacy client-side widgets; always render server widget envelope

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
					<div id="widget-container">
						{type === 'player' ? (
							<PlayerWidgetServer playerId={entityId as any} season={season} />
						) : (
							<Text size="sm" color="dimmed">Team widget (server) coming soon.</Text>
						)}
					</div>
				</Card>
			</div>
		</Container>
	);
}
