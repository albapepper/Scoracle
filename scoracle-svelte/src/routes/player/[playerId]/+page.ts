/**
 * Legacy player route - redirects to new entity route
 */
import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = ({ params, url }) => {
  const sport = url.searchParams.get('sport') || 'football';
  const name = url.searchParams.get('name') || '';
  
  const newUrl = `/entity/player/${params.playerId}?sport=${sport}${name ? `&name=${encodeURIComponent(name)}` : ''}`;
  
  throw redirect(301, newUrl);
};

