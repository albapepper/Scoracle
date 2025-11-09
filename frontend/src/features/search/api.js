import { http } from '../../app/http';

export const searchEntities = (query, entityType, sport) => {
  const params = { query, ...(entityType && { entity_type: entityType }) };
  return http.get(`/${sport}/search`, { params });
};

const api = { searchEntities };
export default api;
