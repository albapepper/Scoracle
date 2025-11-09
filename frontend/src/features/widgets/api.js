import { http } from '../../app/http';

export const getWidgetEnvelope = (entityType, id, { sport, season, debug } = {}) => {
  const params = { ...(season && { season }), ...(debug ? { debug: 1 } : {}) };
  return http.get(`/${sport}/${entityType}s/${id}/widget`, { params });
};

const api = { getWidgetEnvelope };
export default api;
