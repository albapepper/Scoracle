import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

interface BaseTranslation {
  // Header
  header: {
    menu: string;
    language: string;
    settings: string;
    appearance: string;
    darkMode: string;
  };
  // Home page
  home: {
    title: string;
    selectSport: string;
    findLatest: string; // interpolation {{sport}}
  };
  // Search
  search: {
    title: string; // interpolation {{sport}}, {{entity}}
    placeholder: string; // interpolation {{entity}}
    enterTerm: string;
    noneFound: string; // interpolation {{entity}}, {{query}}
    errorGeneric: string;
    searchEntity: string; // interpolation {{entity}}
    noMatches: string;
  };
  // Common
  common: {
    entity: {
      player: string;
      team: string;
    };
    go: string;
    search: string;
    returnHome: string;
    link: string;
  };
  // Entity page
  entityPage: {
    title: string;
    recentMentions: string;
  };
  // Mentions
  mentions: {
    failedLoad: string;
    loading: string;
    statisticalProfile: string;
    articlesTab: string;
    rankingsTab: string;
    tweetsTab: string;
    redditTab: string;
    none: string;
    linkedTeams: string;
    linkedPlayers: string;
    tweetsComingSoon: string;
    redditComingSoon: string;
  };
  // Footer
  footer: {
    allRightsReserved: string;
    terms: string;
    privacy: string;
  };
  // Not found
  notFound: {
    title: string;
    message: string;
    backHome: string;
  };
  // Legacy (keeping for backwards compatibility)
  search_placeholder: string;
  mentions_heading: string;
  entity_heading: string;
  not_found_message: string;
  language_changed: string; // interpolation {{lng}}
}

export interface ResourcesShape {
  en: { translation: BaseTranslation };
  es: { translation: BaseTranslation };
  de: { translation: BaseTranslation };
  pt: { translation: BaseTranslation };
  it: { translation: BaseTranslation };
}

const resources: ResourcesShape & Record<string, any> = {
  en: {
    translation: {
      header: {
        menu: 'Menu',
        language: 'Language',
        settings: 'Settings',
        appearance: 'Appearance',
        darkMode: 'Dark mode',
      },
      home: {
        title: 'Welcome to Scoracle',
        selectSport: 'Select a sport to get started',
        findLatest: 'Find the latest mentions for {{sport}}',
      },
      search: {
        title: 'Search {{sport}} {{entity}}',
        placeholder: 'Search for a {{entity}}...',
        enterTerm: 'Please enter a search term',
        noneFound: 'No {{entity}} found matching "{{query}}"',
        errorGeneric: 'An error occurred while searching',
        searchEntity: 'Search {{entity}}',
        noMatches: 'No matches found',
      },
      common: {
        entity: {
          player: 'Player',
          team: 'Team',
        },
        go: 'Go',
        search: 'Search',
        returnHome: 'Return Home',
        link: 'Link',
      },
      entityPage: {
        title: 'Statistical Profile',
        recentMentions: 'Recent Mentions',
      },
      mentions: {
        failedLoad: 'Failed to load mentions',
        loading: 'Loading mentions...',
        statisticalProfile: 'Statistical Profile',
        articlesTab: 'Articles',
        rankingsTab: 'Rankings',
        tweetsTab: 'Tweets',
        redditTab: 'Reddit',
        none: 'No mentions found',
        linkedTeams: 'Linked Teams',
        linkedPlayers: 'Linked Players',
        tweetsComingSoon: 'Twitter feed coming soon.',
        redditComingSoon: 'Reddit feed coming soon.',
      },
      footer: {
        allRightsReserved: 'All rights reserved.',
        terms: 'Terms',
        privacy: 'Privacy',
      },
      notFound: {
        title: 'Page Not Found',
        message: 'The page you are looking for does not exist.',
        backHome: 'Back to Home',
      },
      // Legacy (keeping for backwards compatibility)
      search_placeholder: 'Search entities...',
      mentions_heading: 'Mentions',
      entity_heading: 'Entity',
      not_found_message: 'Page not found',
      language_changed: 'Language changed to {{lng}}',
    },
  },
  es: {
    translation: {
      header: {
        menu: 'Menú',
        language: 'Idioma',
        settings: 'Configuración',
        appearance: 'Apariencia',
        darkMode: 'Modo oscuro',
      },
      home: {
        title: 'Bienvenido a Scoracle',
        selectSport: 'Selecciona un deporte para comenzar',
        findLatest: 'Encuentra las últimas menciones para {{sport}}',
      },
      search: {
        title: 'Buscar {{sport}} {{entity}}',
        placeholder: 'Buscar un {{entity}}...',
        enterTerm: 'Por favor ingresa un término de búsqueda',
        noneFound: 'No se encontró {{entity}} que coincida con "{{query}}"',
        errorGeneric: 'Ocurrió un error al buscar',
        searchEntity: 'Buscar {{entity}}',
        noMatches: 'No se encontraron coincidencias',
      },
      common: {
        entity: {
          player: 'Jugador',
          team: 'Equipo',
        },
        go: 'Ir',
        search: 'Buscar',
        returnHome: 'Volver al Inicio',
        link: 'Enlace',
      },
      entityPage: {
        title: 'Perfil Estadístico',
        recentMentions: 'Menciones Recientes',
      },
      mentions: {
        failedLoad: 'Error al cargar menciones',
        loading: 'Cargando menciones...',
        statisticalProfile: 'Perfil Estadístico',
        articlesTab: 'Artículos',
        rankingsTab: 'Rankings',
        tweetsTab: 'Tweets',
        redditTab: 'Reddit',
        none: 'No se encontraron menciones',
        linkedTeams: 'Equipos Relacionados',
        linkedPlayers: 'Jugadores Relacionados',
        tweetsComingSoon: 'Feed de Twitter próximamente.',
        redditComingSoon: 'Feed de Reddit próximamente.',
      },
      footer: {
        allRightsReserved: 'Todos los derechos reservados.',
        terms: 'Términos',
        privacy: 'Privacidad',
      },
      notFound: {
        title: 'Página No Encontrada',
        message: 'La página que buscas no existe.',
        backHome: 'Volver al Inicio',
      },
      // Legacy (keeping for backwards compatibility)
      search_placeholder: 'Buscar entidades...',
      mentions_heading: 'Menciones',
      entity_heading: 'Entidad',
      not_found_message: 'Página no encontrada',
      language_changed: 'Idioma cambiado a {{lng}}',
    },
  },
  de: {
    translation: {
      header: {
        menu: 'Menü',
        language: 'Sprache',
        settings: 'Einstellungen',
        appearance: 'Erscheinungsbild',
        darkMode: 'Dunkler Modus',
      },
      home: {
        title: 'Willkommen bei Scoracle',
        selectSport: 'Wählen Sie eine Sportart aus, um zu beginnen',
        findLatest: 'Finden Sie die neuesten Erwähnungen für {{sport}}',
      },
      search: {
        title: '{{sport}} {{entity}} suchen',
        placeholder: 'Nach einem {{entity}} suchen...',
        enterTerm: 'Bitte geben Sie einen Suchbegriff ein',
        noneFound: 'Kein {{entity}} gefunden, der mit "{{query}}" übereinstimmt',
        errorGeneric: 'Beim Suchen ist ein Fehler aufgetreten',
        searchEntity: '{{entity}} suchen',
        noMatches: 'Keine Übereinstimmungen gefunden',
      },
      common: {
        entity: {
          player: 'Spieler',
          team: 'Mannschaft',
        },
        go: 'Gehen',
        search: 'Suchen',
        returnHome: 'Zurück zur Startseite',
        link: 'Link',
      },
      entityPage: {
        title: 'Statistisches Profil',
        recentMentions: 'Aktuelle Erwähnungen',
      },
      mentions: {
        failedLoad: 'Erwähnungen konnten nicht geladen werden',
        loading: 'Erwähnungen werden geladen...',
        statisticalProfile: 'Statistisches Profil',
        articlesTab: 'Artikel',
        rankingsTab: 'Ranglisten',
        tweetsTab: 'Tweets',
        redditTab: 'Reddit',
        none: 'Keine Erwähnungen gefunden',
        linkedTeams: 'Verknüpfte Mannschaften',
        linkedPlayers: 'Verknüpfte Spieler',
        tweetsComingSoon: 'Twitter-Feed kommt bald.',
        redditComingSoon: 'Reddit-Feed kommt bald.',
      },
      footer: {
        allRightsReserved: 'Alle Rechte vorbehalten.',
        terms: 'Bedingungen',
        privacy: 'Datenschutz',
      },
      notFound: {
        title: 'Seite nicht gefunden',
        message: 'Die gesuchte Seite existiert nicht.',
        backHome: 'Zurück zur Startseite',
      },
      // Legacy (keeping for backwards compatibility)
      search_placeholder: 'Entitäten suchen...',
      mentions_heading: 'Erwähnungen',
      entity_heading: 'Entität',
      not_found_message: 'Seite nicht gefunden',
      language_changed: 'Sprache geändert zu {{lng}}',
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
      home: {
        title: 'Bem-vindo ao Scoracle',
        selectSport: 'Selecione um esporte para começar',
        findLatest: 'Encontre as menções mais recentes para {{sport}}',
      },
      search: {
        title: 'Pesquisar {{sport}} {{entity}}',
        placeholder: 'Pesquisar por um {{entity}}...',
        enterTerm: 'Por favor, insira um termo de pesquisa',
        noneFound: 'Nenhum {{entity}} encontrado correspondendo a "{{query}}"',
        errorGeneric: 'Ocorreu um erro ao pesquisar',
        searchEntity: 'Pesquisar {{entity}}',
        noMatches: 'Nenhuma correspondência encontrada',
      },
      common: {
        entity: {
          player: 'Jogador',
          team: 'Time',
        },
        go: 'Ir',
        search: 'Pesquisar',
        returnHome: 'Voltar ao Início',
        link: 'Link',
      },
      entityPage: {
        title: 'Perfil Estatístico',
        recentMentions: 'Menções Recentes',
      },
      mentions: {
        failedLoad: 'Falha ao carregar menções',
        loading: 'Carregando menções...',
        statisticalProfile: 'Perfil Estatístico',
        articlesTab: 'Artigos',
        rankingsTab: 'Classificações',
        tweetsTab: 'Tweets',
        redditTab: 'Reddit',
        none: 'Nenhuma menção encontrada',
        linkedTeams: 'Times Relacionados',
        linkedPlayers: 'Jogadores Relacionados',
        tweetsComingSoon: 'Feed do Twitter em breve.',
        redditComingSoon: 'Feed do Reddit em breve.',
      },
      footer: {
        allRightsReserved: 'Todos os direitos reservados.',
        terms: 'Termos',
        privacy: 'Privacidade',
      },
      notFound: {
        title: 'Página Não Encontrada',
        message: 'A página que você está procurando não existe.',
        backHome: 'Voltar ao Início',
      },
      // Legacy (keeping for backwards compatibility)
      search_placeholder: 'Pesquisar entidades...',
      mentions_heading: 'Menções',
      entity_heading: 'Entidade',
      not_found_message: 'Página não encontrada',
      language_changed: 'Idioma alterado para {{lng}}',
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
      home: {
        title: 'Benvenuto su Scoracle',
        selectSport: 'Seleziona uno sport per iniziare',
        findLatest: 'Trova le ultime menzioni per {{sport}}',
      },
      search: {
        title: 'Cerca {{sport}} {{entity}}',
        placeholder: 'Cerca un {{entity}}...',
        enterTerm: 'Inserisci un termine di ricerca',
        noneFound: 'Nessun {{entity}} trovato corrispondente a "{{query}}"',
        errorGeneric: 'Si è verificato un errore durante la ricerca',
        searchEntity: 'Cerca {{entity}}',
        noMatches: 'Nessun risultato trovato',
      },
      common: {
        entity: {
          player: 'Giocatore',
          team: 'Squadra',
        },
        go: 'Vai',
        search: 'Cerca',
        returnHome: 'Torna alla Home',
        link: 'Collegamento',
      },
      entityPage: {
        title: 'Profilo Statistico',
        recentMentions: 'Menzioni Recenti',
      },
      mentions: {
        failedLoad: 'Impossibile caricare le menzioni',
        loading: 'Caricamento menzioni...',
        statisticalProfile: 'Profilo Statistico',
        articlesTab: 'Articoli',
        rankingsTab: 'Classifiche',
        tweetsTab: 'Tweet',
        redditTab: 'Reddit',
        none: 'Nessuna menzione trovata',
        linkedTeams: 'Squadre Collegate',
        linkedPlayers: 'Giocatori Collegati',
        tweetsComingSoon: 'Feed Twitter in arrivo.',
        redditComingSoon: 'Feed Reddit in arrivo.',
      },
      footer: {
        allRightsReserved: 'Tutti i diritti riservati.',
        terms: 'Termini',
        privacy: 'Privacy',
      },
      notFound: {
        title: 'Pagina Non Trovata',
        message: 'La pagina che stai cercando non esiste.',
        backHome: 'Torna alla Home',
      },
      // Legacy (keeping for backwards compatibility)
      search_placeholder: 'Cerca entità...',
      mentions_heading: 'Menzioni',
      entity_heading: 'Entità',
      not_found_message: 'Pagina non trovata',
      language_changed: 'Lingua cambiata in {{lng}}',
    },
  },
};

void i18n
  .use(initReactI18next)
  .init({
    resources: resources as any,
    lng: 'en',
    fallbackLng: 'en',
    fallbackNS: 'translation',
    defaultNS: 'translation',
    interpolation: { escapeValue: false },
    react: { useSuspense: false },
  });

export default i18n;