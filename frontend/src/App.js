import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { AppShell } from '@mantine/core';

// Context provider
import { SportContextProvider } from './context/SportContext';

// Pages
import HomePage from './pages/HomePage';
import MentionsPage from './pages/MentionsPage';
import PlayerPage from './pages/PlayerPage';
import TeamPage from './pages/TeamPage';
import NotFoundPage from './pages/NotFoundPage';

// Components
import Header from './components/Header';
import Footer from './components/Footer';

function App() {
  return (
    <SportContextProvider>
      <AppShell
        header={{ height: 60 }}
        footer={{ height: 60 }}
        padding="md"
      >
        <AppShell.Header>
          <Header />
        </AppShell.Header>
        
        <AppShell.Main>
          <div className="container">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/mentions/:entityType/:entityId" element={<MentionsPage />} />
              <Route path="/player/:playerId" element={<PlayerPage />} />
              <Route path="/team/:teamId" element={<TeamPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </div>
        </AppShell.Main>
        
        <AppShell.Footer>
          <Footer />
        </AppShell.Footer>
      </AppShell>
    </SportContextProvider>
  );
}

export default App;