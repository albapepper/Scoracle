import React, { createContext, useContext, useMemo, useState } from 'react';
import i18n from '../i18n';

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(i18n.language || 'en');

  const languages = useMemo(
    () => [
      { id: 'en', display: 'English', label: 'EN' },
      // Add more languages as you add resources to i18n
    ],
    []
  );

  const changeLanguage = (lang) => {
    setLanguage(lang);
    if (i18n.language !== lang) {
      void i18n.changeLanguage(lang);
    }
  };

  const value = useMemo(
    () => ({ language, languages, changeLanguage }),
    [language, languages]
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider');
  return ctx;
}

export default LanguageContext;
