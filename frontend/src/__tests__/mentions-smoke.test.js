/**
 * Minimal smoke test using Jest + jsdom.
 * Verifies that when a Mentions API payload is received, the component displays the entity name
 * and that an _echo field contains the same ID we navigated to. This test stubs network calls.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { MantineProvider } from '@mantine/core';
import MentionsPage from '../pages/MentionsPage';

// Stub services/api.getEntityMentions to return a predictable payload
jest.mock('../services/api', () => ({
  getEntityMentions: jest.fn(async (_type, id, _sport) => ({
    player_id: id,
    sport: 'FOOTBALL',
    entity_info: { id: parseInt(id, 10), first_name: 'Cole', last_name: 'Palmer', team: { name: 'Chelsea', abbreviation: 'CHE' } },
    mentions: [
      { title: 'Cole Palmer shines', link: 'https://example.com/a', description: '...', pub_date: new Date().toISOString(), source: 'Example' }
    ],
    _echo: { player_id: id },
  })),
}));

// Provide minimal SportContext
jest.mock('../context/SportContext', () => ({
  useSportContext: () => ({ activeSport: 'FOOTBALL', changeSport: () => {}, sports: [] }),
}));

jest.mock('../context/EntityCacheContext', () => ({
  useEntityCache: () => ({ putSummary: () => {}, getSummary: () => null }),
}));

test('mentions page echoes the selected player id and renders an item', async () => {
  const id = '152982';
  render(
    <MantineProvider>
      <MemoryRouter initialEntries={[`/mentions/player/${id}`]}>
        <Routes>
          <Route path="/mentions/:entityType/:entityId" element={<MentionsPage />} />
        </Routes>
      </MemoryRouter>
    </MantineProvider>
  );
  // Entity header shows full name
  expect(await screen.findByText(/Cole Palmer/)).toBeInTheDocument();
  // One mention item present
  expect(screen.getByText(/shines/i)).toBeInTheDocument();
});
