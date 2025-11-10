// Actual HomePage implementation (previously JS). Reconstructed after JS removal.
import React from 'react';
import { Container, Title, Text, Stack, Paper, SegmentedControl, Box } from '@mantine/core';
import SearchForm from '../../components/SearchForm';
import { useSportContext } from '../../context/SportContext';
import { useThemeMode, getThemeColors } from '../../theme';
import { useTranslation } from 'react-i18next';
import { useIndexedDBSync } from '../../hooks/useIndexedDBSync';

const HomePage: React.FC = () => {
	const { activeSport, sports, changeSport } = useSportContext();
	const { colorScheme } = useThemeMode();
	const colors = getThemeColors(colorScheme);
	const { t } = useTranslation();
	const activeSportDisplay = sports.find((s) => s.id === activeSport)?.display || activeSport;
	useIndexedDBSync(activeSport);

	return (
		<Container size="lg" py="xl">
			<Stack gap="xl" align="center">
				<Box style={{ width: '100%', maxWidth: 600 }}>
					<Paper
						shadow="xs"
						p="md"
						radius="md"
						withBorder
						style={{ backgroundColor: colors.background.secondary, borderColor: colors.ui.border }}
					>
						<Title order={2} ta="center" mb="md" style={{ color: colors.text.accent }}>
							{t('home.title')}
						</Title>
						<Text ta="center" size="md" c="dimmed" mb="lg">
							{t('home.selectSport')}
						</Text>
						<SegmentedControl
							value={activeSport}
							onChange={changeSport as any}
							data={(sports as any[]).map((s) => ({ label: s.display, value: s.id }))}
							fullWidth
							mb="md"
							color={colors.ui.primary}
							styles={{
								root: { backgroundColor: colors.background.tertiary, border: `1px solid ${colors.ui.border}` },
								label: { fontSize: '1rem', padding: '8px 0' },
							}}
						/>
						<Text ta="center" size="sm" mt="md" mb="xl" c="dimmed">
							{t('home.findLatest', { sport: activeSportDisplay })}
						</Text>
					</Paper>
				</Box>
				<Box style={{ width: '100%', maxWidth: 600 }}>
					<SearchForm />
				</Box>
			</Stack>
		</Container>
	);
};

export default HomePage;

