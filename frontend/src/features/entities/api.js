import { http } from '../../app/http';

export const getEntityMentions = (entityType, entityId, sport) => {
  return http.get(`/${sport}/${entityType}s/${entityId}/mentions`);
};

export const getPlayerDetails = (playerId, season, sport) => {
  const params = { ...(season && { season }) };
  return http.get(`/${sport}/players/${playerId}`, { params });
};

export const getPlayerSeasons = (playerId, sport) => {
  return http.get(`/${sport}/players/${playerId}/seasons`);
};

export const getTeamDetails = (teamId, season, sport) => {
  const params = { ...(season && { season }) };
  return http.get(`/${sport}/teams/${teamId}`, { params });
};

export const getTeamRoster = (teamId, season, sport) => {
  const params = { ...(season && { season }) };
  return http.get(`/${sport}/teams/${teamId}/roster`, { params });
};

const api = {
  getEntityMentions,
  getPlayerDetails,
  getPlayerSeasons,
  getTeamDetails,
  getTeamRoster,
};

export default api;
