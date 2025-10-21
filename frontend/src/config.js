// Global frontend configuration and feature flags
// Note: CRA only exposes env vars prefixed with REACT_APP_

export const FEATURES = {
  ENABLE_WIDGETS: (process.env.REACT_APP_ENABLE_WIDGETS || 'false').toLowerCase() === 'true',
};

export default FEATURES;
