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

// Removed legacy /full aggregate helpers (use lean summary endpoints and widgets instead)

// Widgets (server-rendered) services
export const getWidgetEnvelope = async (type, id, { sport, season, debug } = {}) => {
  const params = { ...(sport && { sport }), ...(season && { season }), ...(debug && { debug: 1 }) };
  if (type === 'player') {
    const response = await apiClient.get(`/widgets/player/${id}`, { params });
    return response.data;
  }
  if (type === 'team') {
    const response = await apiClient.get(`/widgets/team/${id}`, { params });
    return response.data;
  }
  throw new Error(`Unsupported widget type: ${type}`);
};