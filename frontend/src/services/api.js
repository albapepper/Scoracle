import axios from 'axios';

// Create API client with defaults
const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Home/search services
export const getHomeInfo = async (sport) => {
  const response = await apiClient.get(`/${sport}`);
  return response.data;
};

export const searchEntities = async (query, entityType, sport) => {
  const params = { query, ...(entityType && { entity_type: entityType }) };
  const response = await apiClient.get(`/${sport}/search`, { params });
  return response.data;
};

// Mentions services
export const getEntityMentions = async (entityType, entityId, sport) => {
  const response = await apiClient.get(`/${sport}/${entityType}s/${entityId}/mentions`);
  return response.data;
};

// Player services
export const getPlayerDetails = async (playerId, season, sport) => {
  const params = { ...(season && { season }) };
  const response = await apiClient.get(`/${sport}/players/${playerId}`, { params });
  return response.data;
};


export const getPlayerSeasons = async (playerId, sport) => {
  const response = await apiClient.get(`/${sport}/players/${playerId}/seasons`);
  return response.data;
};

// Player full aggregate
export const getPlayerFull = async (playerId, season, sport, options = {}) => {
  const params = { ...(season && { season }), ...(options.includeMentions === false ? { include_mentions: false } : {}) };
  const response = await apiClient.get(`/${sport}/players/${playerId}/full`, { params });
  return response.data;
};

// Team services
export const getTeamDetails = async (teamId, season, sport) => {
  const params = { ...(season && { season }) };
  const response = await apiClient.get(`/${sport}/teams/${teamId}`, { params });
  return response.data;
};


export const getTeamRoster = async (teamId, season, sport) => {
  const params = { ...(season && { season }) };
  const response = await apiClient.get(`/${sport}/teams/${teamId}/roster`, { params });
  return response.data;
};

// Team full aggregate
export const getTeamFull = async (teamId, season, sport, options = {}) => {
  const params = { ...(season && { season }), ...(options.includeMentions === false ? { include_mentions: false } : {}) };
  const response = await apiClient.get(`/${sport}/teams/${teamId}/full`, { params });
  return response.data;
};