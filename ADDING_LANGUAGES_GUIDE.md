# Guide: Adding German, Portuguese, and Italian

## Overview
i18next supports any language - you just need to provide the translations. The current setup makes it easy to add new languages.

## Steps to Add New Languages

### 1. Update the TypeScript Interface
In `frontend/src/i18n/index.ts`, add the new language codes to `ResourcesShape`:

```typescript
export interface ResourcesShape {
  en: { translation: BaseTranslation };
  es: { translation: BaseTranslation };
  de: { translation: BaseTranslation };  // German
  pt: { translation: BaseTranslation };   // Portuguese
  it: { translation: BaseTranslation };  // Italian
}
```

### 2. Add Translation Objects
Add a new entry in the `resources` object for each language:

```typescript
de: {
  translation: {
    header: {
      menu: 'Menü',
      language: 'Sprache',
      settings: 'Einstellungen',
      appearance: 'Erscheinungsbild',
      darkMode: 'Dunkler Modus',
    },
    // ... copy structure from English/Spanish and translate
  },
},
pt: {
  translation: {
    header: {
      menu: 'Menu',
      language: 'Idioma',
      settings: 'Configurações',
      appearance: 'Aparência',
      darkMode: 'Modo escuro',
    },
    // ... copy structure and translate
  },
},
it: {
  translation: {
    header: {
      menu: 'Menu',
      language: 'Lingua',
      settings: 'Impostazioni',
      appearance: 'Aspetto',
      darkMode: 'Modalità scura',
    },
    // ... copy structure and translate
  },
},
```

### 3. Add to Language Dropdown
In `frontend/src/context/LanguageContext.tsx`, add to the languages array:

```typescript
const languages = useMemo<LanguageInfo[]>(
  () => [
    { id: 'en', display: 'English', label: 'EN' },
    { id: 'es', display: 'Español', label: 'ES' },
    { id: 'de', display: 'Deutsch', label: 'DE' },
    { id: 'pt', display: 'Português', label: 'PT' },
    { id: 'it', display: 'Italiano', label: 'IT' },
  ],
  []
);
```

## Language Codes
- **German**: `de` (Deutsch)
- **Portuguese**: `pt` (Português) 
- **Italian**: `it` (Italiano)

## Tips
- Copy the English translation structure as a template
- Use a translation service or native speaker for accuracy
- Test each language thoroughly after adding
- Consider regional variants (e.g., `pt-BR` for Brazilian Portuguese)

## Current Status
- ✅ English (en) - Complete
- ✅ Spanish (es) - Complete
- ⏳ German (de) - Ready to add
- ⏳ Portuguese (pt) - Ready to add
- ⏳ Italian (it) - Ready to add

