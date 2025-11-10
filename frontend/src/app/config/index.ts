// Typed environment configuration accessors
// CRA exposes env vars prefixed with REACT_APP_

type Bool = boolean;

type Config = {
  ENABLE_WIDGETS: Bool;
  USE_SERVER_WIDGETS: Bool;
  // Provider keys intentionally removed from client bundle
};

const getBool = (name: string, def = false): boolean => {
  const v = process.env[name];
  if (!v) return def;
  return v.toLowerCase() === 'true' || v === '1' || v.toLowerCase() === 'yes';
};

// Retained for potential future non-secret strings; currently unused.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const getString = (name: string, def = ''): string => process.env[name] ?? def;

export const config: Config = {
  ENABLE_WIDGETS: getBool('REACT_APP_ENABLE_WIDGETS', false),
  USE_SERVER_WIDGETS: getBool('REACT_APP_USE_SERVER_WIDGETS', true),
};

export default config;
