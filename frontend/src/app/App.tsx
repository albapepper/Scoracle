import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '@mantine/core';
import { ThemeProvider, useThemeMode, getThemeColors } from '../theme';
import { LanguageProvider } from '../context/LanguageContext';
import HomePage from '../pages/HomePage/HomePage';
import MentionsPage from '../pages/MentionsPage/MentionsPage';
import EntityPage from '../pages/EntityPage/EntityPage';
import NotFoundPage from '../pages/NotFoundPage';
import Header from '../components/Header';
import Footer from '../components/Footer';
import ErrorToaster from '../components/dev/ErrorToaster';
// JS module export interop
// eslint-disable-next-line @typescript-eslint/no-var-requires
const SportContextProvider: React.ComponentType<any> = require('../context/SportContext').SportContextProvider;

function AppContent(): JSX.Element {
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);
  return (
    <AppShell
      header={{ height: 60 }}
      footer={{ height: 60 }}
      padding="md"
      styles={{ main: { backgroundColor: colors.background.primary } }}
    >
      <AppShell.Header>
        <Header />
      </AppShell.Header>
      <AppShell.Main>
        <div className="container">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/mentions/:entityType/:entityId" element={<MentionsPage />} />
            <Route path="/player/:playerId" element={<Navigate to={"/entity/player/" + window.location.pathname.split('/').pop()} replace />} />
            <Route path="/team/:teamId" element={<Navigate to={"/entity/team/" + window.location.pathname.split('/').pop()} replace />} />
            <Route path="/entity/:entityType/:entityId" element={<EntityPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </div>
        <ErrorToaster />
      </AppShell.Main>
      <AppShell.Footer>
        <Footer />
      </AppShell.Footer>
    </AppShell>
  );
}

function App(): JSX.Element {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <SportContextProvider>
          <AppContent />
        </SportContextProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}

export default App;