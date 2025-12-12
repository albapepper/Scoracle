import { useState, useEffect } from 'react';
import { getEntity } from '../lib/api/entities';
import type { EntityResponse, SportId, EntityType } from '../lib/types';

interface EntityParams {
  sport: SportId | null;
  type: EntityType | null;
  id: string | null;
}

// Skeleton loader for better UX
function LoadingSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-slate-300 dark:bg-slate-700 rounded w-48 mb-4"></div>
      <div className="h-4 bg-slate-300 dark:bg-slate-700 rounded w-full mb-2"></div>
      <div className="h-4 bg-slate-300 dark:bg-slate-700 rounded w-3/4 mb-8"></div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="h-48 bg-slate-300 dark:bg-slate-700 rounded"></div>
        <div className="h-48 bg-slate-300 dark:bg-slate-700 rounded"></div>
      </div>
    </div>
  );
}

// Parse query params from URL
function getEntityParams(): EntityParams {
  if (typeof window === 'undefined') {
    return { sport: null, type: null, id: null };
  }
  
  const urlParams = new URLSearchParams(window.location.search);
  return {
    sport: urlParams.get('sport') as SportId | null,
    type: urlParams.get('type') as EntityType | null,
    id: urlParams.get('id'),
  };
}

export default function EntityWidget() {
  const [params, setParams] = useState<EntityParams>({ sport: null, type: null, id: null });
  const [data, setData] = useState<EntityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Parse URL params on mount
  useEffect(() => {
    setParams(getEntityParams());
  }, []);

  // Fetch entity data when params are available
  useEffect(() => {
    const { sport, type, id } = params;
    
    if (!sport || !type || !id) {
      if (params.sport !== null || params.type !== null || params.id !== null) {
        setError('Missing required parameters. Please select an entity from the search.');
      }
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const result = await getEntity(type, id, sport, {
          includeWidget: true,
          includeNews: true,
        });

        if (!result || !result.entity) {
          setError('Entity not found');
          setLoading(false);
          return;
        }

        setData(result);
        updatePageMeta(result.entity.name);
      } catch (e) {
        console.error('Failed to fetch entity data:', e);
        setError('Failed to load entity data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [params]);

  const updatePageMeta = (name: string) => {
    if (typeof document !== 'undefined') {
      document.title = `${name} - Scoracle`;
      document.querySelector('meta[property="og:title"]')?.setAttribute('content', name);
      document.querySelector('meta[property="og:description"]')?.setAttribute(
        'content',
        `View detailed statistics, news, and information about ${name}`
      );
    }
  };

  if (loading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">Error</h1>
        <p className="text-slate-600 dark:text-slate-400 mb-6">{error}</p>
        <a 
          href="/" 
          className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Back to Search
        </a>
      </div>
    );
  }

  if (!params.sport || !params.type || !params.id) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold mb-4">No Entity Selected</h1>
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          Please search for a player or team to view their profile.
        </p>
        <a 
          href="/" 
          className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Go to Search
        </a>
      </div>
    );
  }

  if (!data || !data.entity) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold mb-4">Entity Not Found</h1>
        <p className="text-slate-600 dark:text-slate-400 mb-6">The requested entity could not be found.</p>
        <a 
          href="/" 
          className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Back to Search
        </a>
      </div>
    );
  }

  const entity = data.entity;
  const widget = data.widget;

  return (
    <div>
      {/* Entity Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          <h1 className="text-4xl font-bold">{entity.name}</h1>
          {entity.sport && (
            <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm uppercase">
              {entity.sport}
            </span>
          )}
        </div>
        <div className="flex gap-4">
          <a 
            href={`/mentions?sport=${params.sport}&type=${params.type}&id=${params.id}`}
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            ← View Mentions
          </a>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Widget Section (Left) */}
        <div className="lg:col-span-2">
          {widget && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
              <h2 className="text-2xl font-semibold mb-4">Statistics</h2>
              <div className="space-y-4">
                {widget.display_name && (
                  <div>
                    <p className="font-semibold text-lg">{widget.display_name}</p>
                    {widget.subtitle && <p className="text-slate-600 dark:text-slate-400">{widget.subtitle}</p>}
                  </div>
                )}
                {widget.position && (
                  <div>
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Position</p>
                    <p className="text-slate-600 dark:text-slate-400">{widget.position}</p>
                  </div>
                )}
                {widget.age && (
                  <div>
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Age</p>
                    <p className="text-slate-600 dark:text-slate-400">{widget.age}</p>
                  </div>
                )}
                {widget.height && (
                  <div>
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Height</p>
                    <p className="text-slate-600 dark:text-slate-400">{widget.height}</p>
                  </div>
                )}
                {widget.conference && (
                  <div>
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Conference</p>
                    <p className="text-slate-600 dark:text-slate-400">{widget.conference}</p>
                  </div>
                )}
                {widget.division && (
                  <div>
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Division</p>
                    <p className="text-slate-600 dark:text-slate-400">{widget.division}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* News Section */}
          {data.news && data.news.length > 0 && (
            <div className="mt-8 bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
              <h2 className="text-2xl font-semibold mb-4">Latest News</h2>
              <div className="space-y-4">
                {data.news.map((article) => (
                  <div
                    key={article.id}
                    className="border-b border-slate-200 dark:border-slate-700 pb-4 last:border-b-0"
                  >
                    <h3 className="font-semibold mb-1">
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        {article.title}
                      </a>
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{article.source}</p>
                    <p className="text-xs text-slate-500 mt-1">{article.published_at}</p>
                    {article.summary && (
                      <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">{article.summary}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar (Right) */}
        <div className="lg:col-span-1">
          {widget && (
            <div className="space-y-6">
              <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
                <h3 className="text-lg font-semibold mb-4">Overview</h3>
                <dl className="space-y-3 text-sm">
                  <div>
                    <dt className="font-medium text-slate-700 dark:text-slate-300">Type</dt>
                    <dd className="text-slate-600 dark:text-slate-400 capitalize">{widget.type}</dd>
                  </div>
                </dl>
              </div>

              {widget.photo_url && (
                <div className="bg-white dark:bg-slate-800 rounded-lg overflow-hidden shadow-sm border border-slate-200 dark:border-slate-700">
                  <img
                    src={widget.photo_url}
                    alt={entity.name}
                    className="w-full h-auto object-cover"
                  />
                </div>
              )}

              {widget.logo_url && (
                <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 flex items-center justify-center">
                  <img
                    src={widget.logo_url}
                    alt={`${entity.name} logo`}
                    className="w-full h-auto object-contain max-h-24"
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
