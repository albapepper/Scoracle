import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '@mantine/core';
import theme from './theme';

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
// No global widget config needed for the minimal template

function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
      <SportContextProvider>
        <AppShell
          header={{ height: 60 }}
          footer={{ height: 60 }}
          padding="md"
          styles={{ main: { backgroundColor: theme.colors.background.primary } }}
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
    </SportContextProvider>
  </LanguageProvider>
  </ThemeProvider>
  );
}

export default App;