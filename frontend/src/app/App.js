import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { createQueryClient } from './queryClient';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '@mantine/core';
import { ThemeProvider, useThemeMode, getThemeColors } from '../theme';

// Theme provider

// Context provider
import { SportContextProvider } from '../context/SportContext';
import { LanguageProvider } from '../context/LanguageContext';

// Pages (use JS implementations to avoid TS build dependency)
import HomePage from '../pages/HomePage.js';
import MentionsPage from '../pages/MentionsPage.js';
import EntityPage from '../pages/EntityPage.js';
import NotFoundPage from '../pages/NotFoundPage.js';

// Components (using direct JS versions; layout wrappers require TS tooling not yet installed)
import Header from '../components/Header';
import Footer from '../components/Footer';
import ErrorToaster from '../components/dev/ErrorToaster';

function AppContent() {
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
            {/* Back-compat redirects from legacy routes */}
            <Route path="/player/:playerId" element={<Navigate to={location => `/entity/player/${location.pathname.split('/').pop()}`} replace />} />
            <Route path="/team/:teamId" element={<Navigate to={location => `/entity/team/${location.pathname.split('/').pop()}`} replace />} />
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

function App() {
  const [client] = React.useState(() => createQueryClient());
  return (
    <ThemeProvider>
      <LanguageProvider>
        <SportContextProvider>
          <QueryClientProvider client={client}>
            <AppContent />
          </QueryClientProvider>
        </SportContextProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}

export default App;
