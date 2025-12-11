/**
 * Layout load function - runs on both server and client
 */
import type { LayoutLoad } from './$types';

// Disable SSR - client-side rendering only (SPA mode)
export const ssr = false;

export const load: LayoutLoad = async () => {
  return {};
};

