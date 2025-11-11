import type React from 'react';

export interface LanguageInfo { id: string; display: string; label: string }
export interface LanguageContextValue { language: string; languages: LanguageInfo[]; changeLanguage: (lang: string) => void }

export declare const LanguageContext: React.Context<LanguageContextValue | null>;
export declare function LanguageProvider(props: { children: React.ReactNode }): JSX.Element;
export declare function useLanguage(): LanguageContextValue;
export default LanguageContext;
