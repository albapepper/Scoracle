// Actual HomePage implementation (previously JS). Reconstructed after JS removal.
import React from 'react';
import { Container, Title, Text, Stack, Paper, SegmentedControl } from '@mantine/core';
import SearchForm from '../../components/SearchForm';
import { useSportContext } from '../../context/SportContext';
import { useThemeMode, getThemeColors } from '../../theme';
import { useTranslation } from 'react-i18next';

const HomePage: React.FC = () => {
	const { activeSport, sports, changeSport } = useSportContext();
	const { colorScheme } = useThemeMode();
	const colors = getThemeColors(colorScheme);
	const { t } = useTranslation();

	return (
		<Container size="lg" py="xl" style={{ 
			display: 'flex', 
			justifyContent: 'center', 
			alignItems: 'center',
			minHeight: 'calc(100vh - 200px)'
		}}>
			<Stack gap="xl" align="center" style={{ width: '100%', maxWidth: 600 }}>
				<Paper
					shadow="sm"
					p="md"
					radius="lg"
					withBorder={false}
					style={{ backgroundColor: colors.background.tertiary, width: '100%' }}
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
							mb="lg"
							color={colors.ui.primary}
							styles={{
								root: { backgroundColor: colors.background.tertiary, border: 'none' },
								control: {
									borderLeft: 'none !important',
									borderRight: 'none !important',
									'&:not(:first-of-type)': { borderLeft: 'none !important' },
									'&:not(:last-of-type)': { borderRight: 'none !important' },
									'&[data-active]': colorScheme === 'light' 
										? { 
											'& .mantine-SegmentedControl-label': { color: '#F5F5E8 !important' }
										} 
										: {},
								},
								label: { 
									fontSize: '1rem', 
									padding: '8px 0', 
									color: colors.text.primary,
									'&[data-active]': colorScheme === 'light' 
										? { color: '#F5F5E8 !important' } 
										: {},
								},
								indicator: { border: 'none' },
							}}
						/>
						<SearchForm inline />
					</Paper>
			</Stack>
		</Container>
	);
};

export default HomePage;

