import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { MantineProvider } from '@mantine/core';
import { SportContextProvider } from '../context/SportContext';
import { LanguageProvider } from '../context/LanguageContext';
import Header from '../components/Header';

// Mock API services to avoid importing axios ESM in tests
jest.mock('../services/api', () => ({
  searchEntities: jest.fn(async () => ({ results: [] })),
}));

// Mock axios used by EntityAutocomplete
jest.mock('axios', () => ({
  get: jest.fn(async () => ({ data: { results: [] } })),
  isCancel: jest.fn(() => false),
}));

function renderHeader() {
  return render(
    <BrowserRouter>
      <MantineProvider>
        <LanguageProvider>
          <SportContextProvider>
            <Header />
          </SportContextProvider>
        </LanguageProvider>
      </MantineProvider>
    </BrowserRouter>
  );
}

test('renders logo, language and sport selector', () => {
  renderHeader();
  expect(screen.getByAltText(/Scoracle/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Select language/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Select sport/i)).toBeInTheDocument();
});

test('opens search drawer when search icon clicked', () => {
  renderHeader();
  const searchButton = screen.getByLabelText(/Open search/i);
  fireEvent.click(searchButton);
  expect(screen.getByText(/Search/i)).toBeInTheDocument();
});
