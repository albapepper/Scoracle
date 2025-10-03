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
  const params = sport ? { sport } : {};
  const response = await apiClient.get('/', { params });
  return response.data;
};

export const searchEntities = async (query, entityType, sport) => {
  const params = {
    query,
    ...(entityType && { entity_type: entityType }),
    ...(sport && { sport }),
  };
  
  const response = await apiClient.get('/search', { params });
  return response.data;
};

// Mentions services
export const getEntityMentions = async (entityType, entityId, sport) => {
  const params = sport ? { sport } : {};
  // Backend route now namespaced under /mentions
  const response = await apiClient.get(`/mentions/${entityType}/${entityId}`, { params });
  return response.data;
};

// Player services
export const getPlayerDetails = async (playerId, season, sport) => {
  const params = {
    ...(season && { season }),
    ...(sport && { sport }),
  };
  
  const response = await apiClient.get(`/player/${playerId}`, { params });
  return response.data;
};

export const getPlayerPercentiles = async (playerId, season, sport) => {
  const params = {
    ...(season && { season }),
    ...(sport && { sport }),
  };
  
  const response = await apiClient.get(`/player/${playerId}/percentiles`, { params });
  return response.data;
};

export const getPlayerSeasons = async (playerId, sport) => {
  const params = sport ? { sport } : {};
  const response = await apiClient.get(`/player/${playerId}/seasons`, { params });
  return response.data;
};

// Team services
export const getTeamDetails = async (teamId, season, sport) => {
  const params = {
    ...(season && { season }),
    ...(sport && { sport }),
  };
  
  const response = await apiClient.get(`/team/${teamId}`, { params });
  return response.data;
};

export const getTeamPercentiles = async (teamId, season, sport) => {
  const params = {
    ...(season && { season }),
    ...(sport && { sport }),
  };
  
  const response = await apiClient.get(`/team/${teamId}/percentiles`, { params });
  return response.data;
};

export const getTeamRoster = async (teamId, season, sport) => {
  const params = {
    ...(season && { season }),
    ...(sport && { sport }),
  };
  
  const response = await apiClient.get(`/team/${teamId}/roster`, { params });
  return response.data;
};