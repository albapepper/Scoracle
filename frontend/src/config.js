// Global frontend configuration and feature flags
// Note: CRA only exposes env vars prefixed with REACT_APP_

export const FEATURES = {
  ENABLE_WIDGETS: (process.env.REACT_APP_ENABLE_WIDGETS || 'false').toLowerCase() === 'true',
  USE_SERVER_WIDGETS: (process.env.REACT_APP_USE_SERVER_WIDGETS || 'true').toLowerCase() === 'true', // pivot flag
};

// Centralized API-Sports widget key (frontend-only). Do NOT commit real keys.
// Set in a .env file as REACT_APP_APISPORTS_KEY=your_key
export const APISPORTS_KEY = process.env.REACT_APP_APISPORTS_KEY || process.env.REACT_APP_APISPORTS_WIDGET_KEY || process.env.REACT_APP_API_SPORTS_KEY || '';

export default FEATURES;
