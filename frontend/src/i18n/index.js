import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      header: {
        settings: 'Settings',
        appearance: 'Appearance',
        darkMode: 'Dark mode',
        language: 'Language',
        menu: 'Menu',
      },
      common: {
        home: 'Home',
        returnHome: 'Return to Home',
        loading: 'Loading...',
        failedLoad: 'Failed to load. Please try again later.',
        search: 'Search',
        go: 'Go',
        link: 'Link',
        viewStats: 'View Stats',
        yes: 'Yes',
        no: 'No',
        entity: {
          player: 'Player',
          team: 'Team'
        }
      },
      home: {
        title: 'Welcome to Scoracle',
        selectSport: 'Select your sport to get started',
        findLatest: 'Find the latest news and statistics for your favorite {{sport}} players and teams'
      },
      search: {
        title: 'Find a {{sport}} {{entity}}',
        placeholder: 'Start typing a {{entity}} name...',
        enterTerm: 'Please enter a search term',
        noneFound: 'No {{entity}}s found matching "{{query}}"',
        errorGeneric: 'An error occurred during search',
        autocompleteFailed: 'Autocomplete failed',
        noMatches: 'No matches'
      },
      mentions: {
        loading: 'Loading mentions...',
        failedLoad: 'Failed to load mentions. Please try again later.',
        widgetPreview: 'Widget Preview',
        noApisportsId: 'No API-Sports ID mapped for this {{entityType}}. Add apisports_id to enable widgets.',
        recent: 'Recent Mentions',
        newsMentioning: 'News articles mentioning {{name}}',
        none: 'No recent mentions found.',
        alsoMentioned: 'Also mentioned',
        otherEntities: 'Other entities from {{sport}} that appeared in these articles',
        noComentions: 'No co-mentions detected.',
        statisticalProfile: 'Statistical Profile',
        hits: 'hits'
      },
      footer: {
        allRightsReserved: 'All rights reserved.',
        terms: 'Terms of Service',
        privacy: 'Privacy Policy'
      },
      entity: {
        age: 'Age',
        nationality: 'Nationality',
        currentTeam: 'Current Team',
        league: 'League',
        yearsPro: 'Years Pro',
        city: 'City',
        conference: 'Conference',
        division: 'Division'
      },
      notFound: {
        title: 'Page Not Found',
        message: "The page you're looking for doesn't exist or has been moved.",
        backHome: 'Back to Home'
      },
      player: {
        loading: 'Loading player data...',
        failedLoad: 'Failed to load player data. Please try again later.',
        widget: 'Player Widget',
        statistics: 'Player Statistics',
        season: 'Season',
        selectSeason: 'Select season',
        tabs: {
          overview: 'Overview',
          metrics: 'Metrics',
          shooting: 'Shooting',
          advanced: 'Advanced',
          rawGroups: 'Raw Groups'
        },
        noAdditionalMetrics: 'No additional metrics available.',
        metricGroup: 'Metric Group',
        noDataForGroup: 'No data for the selected group.',
        noStatsForSeason: 'No statistics available for this player in the selected season.'
      },
      team: {
        loading: 'Loading team data...',
        failedLoad: 'Failed to load team data. Please try again later.',
        widget: 'Team Widget',
        statistics: 'Team Statistics',
        season: 'Season',
        selectSeason: 'Select season',
        record: 'Record',
        winPercentage: 'Win Percentage',
        statsAbbr: { ppg: 'PPG', rpg: 'RPG', apg: 'APG' },
        tabs: {
          overview: 'Overview',
          roster: 'Roster',
          metrics: 'Metrics',
          advanced: 'Advanced',
          rawGroups: 'Raw Groups'
        },
        noAdditionalMetrics: 'No additional metrics available.',
        metricGroup: 'Metric Group',
        noDataForGroup: 'No data for the selected group.',
        noStatsForSeason: 'No statistics available for this team in the selected season.',
        noRosterInfo: 'No roster information available for this team in the selected season.'
      },
    },
  },
  es: {
    translation: {
      header: {
        settings: 'Ajustes',
        appearance: 'Apariencia',
        darkMode: 'Modo oscuro',
        language: 'Idioma',
        menu: 'Menú',
      },
      common: {
        home: 'Inicio',
        returnHome: 'Volver al inicio',
        loading: 'Cargando...',
        failedLoad: 'Error al cargar. Inténtalo de nuevo más tarde.',
        search: 'Buscar',
        go: 'Ir',
        link: 'Enlace',
        viewStats: 'Ver estadísticas',
        yes: 'Sí',
        no: 'No',
        entity: {
          player: 'Jugador',
          team: 'Equipo'
        }
      },
      home: {
        title: 'Bienvenido a Scoracle',
        selectSport: 'Selecciona tu deporte para comenzar',
        findLatest: 'Encuentra las últimas noticias y estadísticas de tus jugadores y equipos favoritos de {{sport}}'
      },
      search: {
        title: 'Encuentra un {{entity}} de {{sport}}',
        placeholder: 'Empieza a escribir el nombre de un {{entity}}...',
        enterTerm: 'Por favor, introduce un término de búsqueda',
        noneFound: 'No se encontraron {{entity}}s que coincidan con "{{query}}"',
        errorGeneric: 'Se produjo un error durante la búsqueda',
        autocompleteFailed: 'Autocompletar falló',
        noMatches: 'Sin coincidencias'
      },
      mentions: {
        loading: 'Cargando menciones...',
        failedLoad: 'Error al cargar las menciones. Inténtalo de nuevo más tarde.',
        widgetPreview: 'Vista previa del widget',
        noApisportsId: 'No hay ID de API-Sports para este {{entityType}}. Agrega apisports_id para habilitar widgets.',
        recent: 'Menciones recientes',
        newsMentioning: 'Artículos mencionando a {{name}}',
        none: 'No se encontraron menciones recientes.',
        alsoMentioned: 'También mencionado',
        otherEntities: 'Otras entidades de {{sport}} que aparecen en estos artículos',
        noComentions: 'No se detectaron co-menciones.',
        statisticalProfile: 'Perfil estadístico',
        hits: 'apariciones'
      },
      footer: {
        allRightsReserved: 'Todos los derechos reservados.',
        terms: 'Términos de servicio',
        privacy: 'Política de privacidad'
      },
      entity: {
        age: 'Edad',
        nationality: 'Nacionalidad',
        currentTeam: 'Equipo actual',
        league: 'Liga',
        yearsPro: 'Años como profesional',
        city: 'Ciudad',
        conference: 'Conferencia',
        division: 'División'
      },
      notFound: {
        title: 'Página no encontrada',
        message: 'La página que buscas no existe o ha sido movida.',
        backHome: 'Volver al inicio'
      },
      player: {
        loading: 'Cargando datos del jugador...',
        failedLoad: 'Error al cargar datos del jugador. Inténtalo más tarde.',
        widget: 'Widget de jugador',
        statistics: 'Estadísticas del jugador',
        season: 'Temporada',
        selectSeason: 'Selecciona temporada',
        tabs: {
          overview: 'Resumen',
          metrics: 'Métricas',
          shooting: 'Tiro',
          advanced: 'Avanzado',
          rawGroups: 'Grupos crudos'
        },
        noAdditionalMetrics: 'No hay métricas adicionales disponibles.',
        metricGroup: 'Grupo de métricas',
        noDataForGroup: 'No hay datos para el grupo seleccionado.',
        noStatsForSeason: 'No hay estadísticas disponibles para este jugador en la temporada seleccionada.'
      },
      team: {
        loading: 'Cargando datos del equipo...',
        failedLoad: 'Error al cargar datos del equipo. Inténtalo más tarde.',
        widget: 'Widget de equipo',
        statistics: 'Estadísticas del equipo',
        season: 'Temporada',
        selectSeason: 'Selecciona temporada',
        record: 'Balance',
        winPercentage: 'Porcentaje de victorias',
        statsAbbr: { ppg: 'PPG', rpg: 'RPG', apg: 'APG' },
        tabs: {
          overview: 'Resumen',
          roster: 'Plantilla',
          metrics: 'Métricas',
          advanced: 'Avanzado',
          rawGroups: 'Grupos crudos'
        },
        noAdditionalMetrics: 'No hay métricas adicionales disponibles.',
        metricGroup: 'Grupo de métricas',
        noDataForGroup: 'No hay datos para el grupo seleccionado.',
        noStatsForSeason: 'No hay estadísticas disponibles para este equipo en la temporada seleccionada.',
        noRosterInfo: 'No hay información de la plantilla disponible para este equipo en la temporada seleccionada.'
      },
    },
  },
  de: {
    translation: {
      header: {
        settings: 'Einstellungen',
        appearance: 'Erscheinungsbild',
        darkMode: 'Dunkelmodus',
        language: 'Sprache',
        menu: 'Menü',
      },
      common: {
        home: 'Startseite',
        returnHome: 'Zur Startseite',
        loading: 'Wird geladen...',
        failedLoad: 'Laden fehlgeschlagen. Bitte später erneut versuchen.',
        search: 'Suche',
        go: 'Los',
        link: 'Link',
        viewStats: 'Statistiken ansehen',
        yes: 'Ja',
        no: 'Nein',
        entity: {
          player: 'Spieler',
          team: 'Team'
        }
      },
      home: {
        title: 'Willkommen bei Scoracle',
        selectSport: 'Wähle deinen Sport, um zu starten',
        findLatest: 'Finde die neuesten Nachrichten und Statistiken für deine Lieblingsspieler und -teams im {{sport}}'
      },
      search: {
        title: 'Finde ein(e) {{entity}} im {{sport}}',
        placeholder: 'Gib den Namen eines {{entity}} ein...',
        enterTerm: 'Bitte gib einen Suchbegriff ein',
        noneFound: 'Keine {{entity}}s gefunden, die "{{query}}" entsprechen',
        errorGeneric: 'Bei der Suche ist ein Fehler aufgetreten',
        autocompleteFailed: 'Autovervollständigung fehlgeschlagen',
        noMatches: 'Keine Treffer'
      },
      mentions: {
        loading: 'Meldungen werden geladen...',
        failedLoad: 'Meldungen konnten nicht geladen werden. Bitte später erneut versuchen.',
        widgetPreview: 'Widget-Vorschau',
        noApisportsId: 'Keine API-Sports-ID für diesen {{entityType}}. Füge apisports_id hinzu, um Widgets zu aktivieren.',
        recent: 'Aktuelle Meldungen',
        newsMentioning: 'Artikel, die {{name}} erwähnen',
        none: 'Keine aktuellen Meldungen gefunden.',
        alsoMentioned: 'Ebenfalls erwähnt',
        otherEntities: 'Weitere Einträge aus {{sport}}, die in diesen Artikeln vorkommen',
        noComentions: 'Keine gemeinsamen Erwähnungen gefunden.',
        statisticalProfile: 'Statistikprofil',
        hits: 'Treffer'
      },
      footer: {
        allRightsReserved: 'Alle Rechte vorbehalten.',
        terms: 'Nutzungsbedingungen',
        privacy: 'Datenschutz'
      },
      entity: {
        age: 'Alter',
        nationality: 'Nationalität',
        currentTeam: 'Aktuelles Team',
        league: 'Liga',
        yearsPro: 'Jahre als Profi',
        city: 'Stadt',
        conference: 'Konferenz',
        division: 'Division'
      },
      notFound: {
        title: 'Seite nicht gefunden',
        message: 'Die gesuchte Seite existiert nicht oder wurde verschoben.',
        backHome: 'Zur Startseite'
      },
      player: {
        loading: 'Spielerdaten werden geladen...',
        failedLoad: 'Spielerdaten konnten nicht geladen werden. Bitte später erneut versuchen.',
        widget: 'Spieler-Widget',
        statistics: 'Spielerstatistiken',
        season: 'Saison',
        selectSeason: 'Saison auswählen',
        tabs: {
          overview: 'Übersicht',
          metrics: 'Metriken',
          shooting: 'Wurf',
          advanced: 'Erweitert',
          rawGroups: 'Rohgruppen'
        },
        noAdditionalMetrics: 'Keine zusätzlichen Metriken verfügbar.',
        metricGroup: 'Metrik-Gruppe',
        noDataForGroup: 'Keine Daten für die ausgewählte Gruppe.',
        noStatsForSeason: 'Keine Statistiken für diese Saison verfügbar.'
      },
      team: {
        loading: 'Teamdaten werden geladen...',
        failedLoad: 'Teamdaten konnten nicht geladen werden. Bitte später erneut versuchen.',
        widget: 'Team-Widget',
        statistics: 'Teamstatistiken',
        season: 'Saison',
        selectSeason: 'Saison auswählen',
        record: 'Bilanz',
        winPercentage: 'Siegquote',
        statsAbbr: { ppg: 'PPG', rpg: 'RPG', apg: 'APG' },
        tabs: {
          overview: 'Übersicht',
          roster: 'Kader',
          metrics: 'Metriken',
          advanced: 'Erweitert',
          rawGroups: 'Rohgruppen'
        },
        noAdditionalMetrics: 'Keine zusätzlichen Metriken verfügbar.',
        metricGroup: 'Metrik-Gruppe',
        noDataForGroup: 'Keine Daten für die ausgewählte Gruppe.',
        noStatsForSeason: 'Keine Statistiken für diese Saison verfügbar.',
        noRosterInfo: 'Keine Kaderinformationen für dieses Team in der ausgewählten Saison verfügbar.'
      },
    },
  },
  fr: {
    translation: {
      header: {
        settings: 'Paramètres',
        appearance: 'Apparence',
        darkMode: 'Mode sombre',
        language: 'Langue',
        menu: 'Menu',
      },
      common: {
        home: 'Accueil',
        returnHome: 'Retour à l\'accueil',
        loading: 'Chargement...',
        failedLoad: 'Échec du chargement. Veuillez réessayer plus tard.',
        search: 'Rechercher',
        go: 'Aller',
        link: 'Lien',
        viewStats: 'Voir les statistiques',
        yes: 'Oui',
        no: 'Non',
        entity: {
          player: 'Joueur',
          team: 'Équipe'
        }
      },
      home: {
        title: 'Bienvenue sur Scoracle',
        selectSport: 'Sélectionnez votre sport pour commencer',
        findLatest: 'Trouvez les dernières actualités et statistiques de vos joueurs et équipes préférés en {{sport}}'
      },
      search: {
        title: 'Trouver un {{entity}} en {{sport}}',
        placeholder: 'Commencez à taper le nom d\'un {{entity}}...',
        enterTerm: 'Veuillez saisir un terme de recherche',
        noneFound: 'Aucun {{entity}} correspondant à "{{query}}"',
        errorGeneric: 'Une erreur s\'est produite lors de la recherche',
        autocompleteFailed: 'La saisie semi-automatique a échoué',
        noMatches: 'Aucune correspondance'
      },
      mentions: {
        loading: 'Chargement des mentions...',
        failedLoad: 'Échec du chargement des mentions. Veuillez réessayer plus tard.',
        widgetPreview: 'Aperçu du widget',
        noApisportsId: 'Aucun identifiant API-Sports pour ce {{entityType}}. Ajoutez apisports_id pour activer les widgets.',
        recent: 'Mentions récentes',
        newsMentioning: 'Articles mentionnant {{name}}',
        none: 'Aucune mention récente trouvée.',
        alsoMentioned: 'Également mentionné',
        otherEntities: 'Autres entités de {{sport}} apparues dans ces articles',
        noComentions: 'Aucune co-mention détectée.',
        statisticalProfile: 'Profil statistique',
        hits: 'occurrences'
      },
      footer: {
        allRightsReserved: 'Tous droits réservés.',
        terms: 'Conditions d\'utilisation',
        privacy: 'Politique de confidentialité'
      },
      entity: {
        age: 'Âge',
        nationality: 'Nationalité',
        currentTeam: 'Équipe actuelle',
        league: 'Ligue',
        yearsPro: 'Années pro',
        city: 'Ville',
        conference: 'Conférence',
        division: 'Division'
      },
      notFound: {
        title: 'Page non trouvée',
        message: 'La page que vous recherchez n\'existe pas ou a été déplacée.',
        backHome: 'Retour à l\'accueil'
      },
      player: {
        loading: 'Chargement des données du joueur...',
        failedLoad: 'Échec du chargement des données du joueur. Veuillez réessayer plus tard.',
        widget: 'Widget du joueur',
        statistics: 'Statistiques du joueur',
        season: 'Saison',
        selectSeason: 'Sélectionnez la saison',
        tabs: {
          overview: 'Aperçu',
          metrics: 'Métriques',
          shooting: 'Tir',
          advanced: 'Avancé',
          rawGroups: 'Groupes bruts'
        },
        noAdditionalMetrics: 'Aucune métrique supplémentaire disponible.',
        metricGroup: 'Groupe de métriques',
        noDataForGroup: 'Aucune donnée pour le groupe sélectionné.',
        noStatsForSeason: 'Aucune statistique disponible pour ce joueur cette saison.'
      },
      team: {
        loading: 'Chargement des données de l\'équipe...',
        failedLoad: 'Échec du chargement des données de l\'équipe. Veuillez réessayer plus tard.',
        widget: 'Widget d\'équipe',
        statistics: 'Statistiques de l\'équipe',
        season: 'Saison',
        selectSeason: 'Sélectionnez la saison',
        record: 'Bilan',
        winPercentage: 'Pourcentage de victoires',
        statsAbbr: { ppg: 'PPG', rpg: 'RPG', apg: 'APG' },
        tabs: {
          overview: 'Aperçu',
          roster: 'Effectif',
          metrics: 'Métriques',
          advanced: 'Avancé',
          rawGroups: 'Groupes bruts'
        },
        noAdditionalMetrics: 'Aucune métrique supplémentaire disponible.',
        metricGroup: 'Groupe de métriques',
        noDataForGroup: 'Aucune donnée pour le groupe sélectionné.',
        noStatsForSeason: 'Aucune statistique disponible pour cette équipe cette saison.',
        noRosterInfo: 'Aucune information d’effectif disponible pour cette équipe pour la saison sélectionnée.'
      },
    },
  },
  it: {
    translation: {
      header: {
        settings: 'Impostazioni',
        appearance: 'Aspetto',
        darkMode: 'Modalità scura',
        language: 'Lingua',
        menu: 'Menu',
      },
      common: {
        home: 'Home',
        returnHome: 'Torna alla Home',
        loading: 'Caricamento...',
        failedLoad: 'Caricamento non riuscito. Riprova più tardi.',
        search: 'Cerca',
        go: 'Vai',
        link: 'Link',
        viewStats: 'Vedi statistiche',
        yes: 'Sì',
        no: 'No',
        entity: {
          player: 'Giocatore',
          team: 'Squadra'
        }
      },
      home: {
        title: 'Benvenuto su Scoracle',
        selectSport: 'Seleziona il tuo sport per iniziare',
        findLatest: 'Trova le ultime notizie e statistiche dei tuoi giocatori e squadre preferiti di {{sport}}'
      },
      search: {
        title: 'Trova un {{entity}} di {{sport}}',
        placeholder: 'Inizia a digitare il nome di un {{entity}}...',
        enterTerm: 'Inserisci un termine di ricerca',
        noneFound: 'Nessun {{entity}} trovato corrispondente a "{{query}}"',
        errorGeneric: 'Si è verificato un errore durante la ricerca',
        autocompleteFailed: 'Completamento automatico non riuscito',
        noMatches: 'Nessuna corrispondenza'
      },
      mentions: {
        loading: 'Caricamento menzioni...',
        failedLoad: 'Impossibile caricare le menzioni. Riprova più tardi.',
        widgetPreview: 'Anteprima widget',
        noApisportsId: 'Nessun ID API-Sports per questo {{entityType}}. Aggiungi apisports_id per abilitare i widget.',
        recent: 'Menzioni recenti',
        newsMentioning: 'Articoli che menzionano {{name}}',
        none: 'Nessuna menzione recente trovata.',
        alsoMentioned: 'Menzionati anche',
        otherEntities: 'Altre entità di {{sport}} apparse in questi articoli',
        noComentions: 'Nessuna co-menzione rilevata.',
        statisticalProfile: 'Profilo statistico',
        hits: 'citazioni'
      },
      footer: {
        allRightsReserved: 'Tutti i diritti riservati.',
        terms: 'Termini di servizio',
        privacy: 'Informativa sulla privacy'
      },
      entity: {
        age: 'Età',
        nationality: 'Nazionalità',
        currentTeam: 'Squadra attuale',
        league: 'Lega',
        yearsPro: 'Anni da professionista',
        city: 'Città',
        conference: 'Conference',
        division: 'Divisione'
      },
      notFound: {
        title: 'Pagina non trovata',
        message: 'La pagina che stai cercando non esiste o è stata spostata.',
        backHome: 'Torna alla Home'
      },
      player: {
        loading: 'Caricamento dati giocatore...',
        failedLoad: 'Impossibile caricare i dati del giocatore. Riprova più tardi.',
        widget: 'Widget giocatore',
        statistics: 'Statistiche giocatore',
        season: 'Stagione',
        selectSeason: 'Seleziona stagione',
        tabs: {
          overview: 'Panoramica',
          metrics: 'Metriche',
          shooting: 'Tiro',
          advanced: 'Avanzate',
          rawGroups: 'Gruppi grezzi'
        },
        noAdditionalMetrics: 'Nessuna metrica aggiuntiva disponibile.',
        metricGroup: 'Gruppo di metriche',
        noDataForGroup: 'Nessun dato per il gruppo selezionato.',
        noStatsForSeason: 'Nessuna statistica disponibile per questo giocatore nella stagione selezionata.'
      },
      team: {
        loading: 'Caricamento dati squadra...',
        failedLoad: 'Impossibile caricare i dati della squadra. Riprova più tardi.',
        widget: 'Widget squadra',
        statistics: 'Statistiche squadra',
        season: 'Stagione',
        selectSeason: 'Seleziona stagione',
        record: 'Bilancio',
        winPercentage: 'Percentuale di vittorie',
        statsAbbr: { ppg: 'PPG', rpg: 'RPG', apg: 'APG' },
        tabs: {
          overview: 'Panoramica',
          roster: 'Rosa',
          metrics: 'Metriche',
          advanced: 'Avanzate',
          rawGroups: 'Gruppi grezzi'
        },
        noAdditionalMetrics: 'Nessuna metrica aggiuntiva disponibile.',
        metricGroup: 'Gruppo di metriche',
        noDataForGroup: 'Nessun dato per il gruppo selezionato.',
        noStatsForSeason: 'Nessuna statistica disponibile per questa squadra nella stagione selezionata.',
        noRosterInfo: 'Nessuna informazione sulla rosa disponibile per questa squadra nella stagione selezionata.'
      },
    },
  },
};

// Initialize i18n
i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en',
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
  });

export default i18n;
