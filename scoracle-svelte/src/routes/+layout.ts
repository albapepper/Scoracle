/**
 * Layout load function - runs on both server and client
 */
import type { LayoutLoad } from './$types';

// Disable SSR for now to avoid hydration issues with i18n and fetch
export const ssr = false;

export const load: LayoutLoad = async () => {
  return {};
};

