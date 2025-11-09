import { http } from '../../app/http';

export const searchEntities = (query: string, entityType: 'player'|'team', sport: string) => {
  const params: any = { query, ...(entityType && { entity_type: entityType }) };
  return http.get(`/${sport}/search`, { params });
};

export const api = { searchEntities };
export default api;
