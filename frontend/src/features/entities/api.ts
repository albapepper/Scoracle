import { http } from '../_shared/http';

export const getEntityMentions = (entityType: string, entityId: string|number, sport: string) => {
  return http.get(`${sport}/${entityType}s/${entityId}/mentions`);
};

export const getPlayerDetails = (playerId: string|number, season: string|undefined, sport: string) => {
  const params = { ...(season && { season }) } as any;
  return http.get(`${sport}/players/${playerId}`, { params });
};

export const getPlayerSeasons = (playerId: string|number, sport: string) => {
  return http.get(`${sport}/players/${playerId}/seasons`);
};

export const getTeamDetails = (teamId: string|number, season: string|undefined, sport: string) => {
  const params = { ...(season && { season }) } as any;
  return http.get(`${sport}/teams/${teamId}`, { params });
};

export const getTeamRoster = (teamId: string|number, season: string|undefined, sport: string) => {
  const params = { ...(season && { season }) } as any;
  return http.get(`${sport}/teams/${teamId}/roster`, { params });
};

export const api = {
  getEntityMentions,
  getPlayerDetails,
  getPlayerSeasons,
  getTeamDetails,
  getTeamRoster,
};

export default api;
