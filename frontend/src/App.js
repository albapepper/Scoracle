import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '@mantine/core';
import { useThemeMode } from './ThemeProvider';
import { getThemeColors } from './theme';

// Theme provider
import { ThemeProvider } from './ThemeProvider';

// Context provider
import { SportContextProvider } from './context/SportContext';
import { LanguageProvider } from './context/LanguageContext';

// Pages
import HomePage from './pages/HomePage';
import MentionsPage from './pages/MentionsPage';
import EntityPage from './pages/EntityPage';
import NotFoundPage from './pages/NotFoundPage';

// Components
import Header from './components/Header';
import Footer from './components/Footer';

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
      </AppShell.Main>

      <AppShell.Footer>
        <Footer />
      </AppShell.Footer>
    </AppShell>
  );
}

function App() {
  const [client] = React.useState(() => new QueryClient());
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