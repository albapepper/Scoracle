import React, { createContext, useContext, useEffect, useState } from 'react';
import i18n from '../i18n';

const LanguageContext = createContext();

const LANGUAGES = [
  { id: 'en', label: 'English', display: 'EN' },
  { id: 'es', label: 'Español', display: 'ES' },
  { id: 'de', label: 'Deutsch', display: 'DE' },
  { id: 'fr', label: 'Français', display: 'FR' },
  { id: 'it', label: 'Italiano', display: 'IT' },
];

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState('en');

  useEffect(() => {
    const saved = localStorage.getItem('language');
    if (saved && LANGUAGES.some(l => l.id === saved)) setLanguage(saved);
  }, []);

  useEffect(() => {
    localStorage.setItem('language', language);
    try { i18n.changeLanguage(language); } catch (e) { /* no-op */ }
  }, [language]);

  const changeLanguage = (langId) => {
    if (LANGUAGES.some(l => l.id === langId)) setLanguage(langId);
  };

  return (
    <LanguageContext.Provider value={{ language, changeLanguage, languages: LANGUAGES }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
