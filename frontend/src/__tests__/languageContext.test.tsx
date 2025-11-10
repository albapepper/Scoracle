import React from 'react';
import { render, screen } from '@testing-library/react';
import { LanguageProvider, useLanguage } from '../context/LanguageContext';

function TestComp() {
  const { language, languages } = useLanguage();
  return <div role="status" aria-label={`lang-${language}`}>{languages[0].display}</div>;
}

describe('LanguageContext', () => {
  it('provides default language', () => {
    render(<LanguageProvider><TestComp /></LanguageProvider>);
  const el = screen.getByRole('status', { name: /lang-en/i });
  expect(el).toBeInTheDocument();
  });
});
