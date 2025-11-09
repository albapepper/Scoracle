// Thin re-export/adapter around existing IndexedDB service to allow gradual migration
export { initializeIndexedDB, upsertPlayers, upsertTeams, searchPlayers, searchTeams, getPlayerById, getTeamById, getStats } from '../../../services/indexedDB';
