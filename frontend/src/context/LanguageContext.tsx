import React, { createContext, useContext, useMemo, useState } from 'react';
import i18n from '../i18n';

export interface LanguageInfo { id: string; display: string; label: string }
export interface LanguageContextValue { language: string; languages: LanguageInfo[]; changeLanguage: (lang: string) => void }

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<string>(i18n.language || 'en');

  const languages = useMemo<LanguageInfo[]>(
    () => [
      { id: 'en', display: 'English', label: 'EN' },
      // Extend with more locales as resources are added
    ],
    []
  );

  const changeLanguage = (lang: string) => {
    setLanguage(lang);
    if (i18n.language !== lang) {
      void i18n.changeLanguage(lang);
    }
  };

  const value = useMemo<LanguageContextValue>(() => ({ language, languages, changeLanguage }), [language, languages]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider');
  return ctx;
}

export default LanguageContext;
