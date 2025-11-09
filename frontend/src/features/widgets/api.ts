import { http } from '../../app/http';

export const getWidgetEnvelope = (type: string, id: string|number, { sport, season, debug }: { sport?: string; season?: string; debug?: boolean } = {}) => {
	const params: any = { ...(sport && { sport }), ...(season && { season }), ...(debug && { debug: 1 }) };
	if (type === 'player') {
		return http.get(`/widgets/player/${id}`, { params });
	}
	if (type === 'team') {
		return http.get(`/widgets/team/${id}`, { params });
	}
	throw new Error(`Unsupported widget type: ${type}`);
};

export const api = { getWidgetEnvelope };
export default api;
