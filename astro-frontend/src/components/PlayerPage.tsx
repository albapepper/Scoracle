import React, { useState, useEffect } from 'react';
import { getEntity } from '../lib/api/entities';
import { parseEntityUrl } from '../lib/utils/useEntityFromUrl';
import type { EntityResponse } from '../lib/types';
import type { ReactNode } from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends React.Component<{ children: ReactNode }, ErrorBoundaryState> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    console.error('PlayerPage error:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="container-custom py-12 text-center">
          <h1 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">Error Loading Player</h1>
          <p className="text-slate-600 dark:text-slate-400">
            Failed to load player data. Please try again later.
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}

function PlayerPageContent() {
  const [data, setData] = useState<EntityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const { sport, id } = parseEntityUrl();

    if (!sport || !id) {
      setError('Invalid URL');
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await getEntity('player', id, sport, {
          includeWidget: true,
          includeNews: true,
        });
        setData(result);
        setError(null);
        
        // Update page title and meta tags
        if (result.entity?.name) {
          document.title = `${result.entity.name} - Scoracle`;
          document.querySelector('meta[property="og:title"]')?.setAttribute('content', result.entity.name);
        }
      } catch (e) {
        console.error('Failed to fetch player data:', e);
        setError('Failed to load player data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="container-custom py-12 text-center">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-48 mx-auto mb-4" />
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-96 mx-auto" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container-custom py-12 text-center">
        <h1 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">
          {error ? 'Error Loading Player' : 'Player Not Found'}
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          {error || 'The player you\'re looking for could not be found.'}
        </p>
        <a href="/" className="mt-4 inline-block text-blue-600 dark:text-blue-400 hover:underline">
          Back to Home
        </a>
      </div>
    );
  }

  const { widget, news } = data;

  return (
    <div className="container-custom">
      {/* Widget */}
      {widget && (
        <div className="card mb-8">
          <div className="flex flex-col md:flex-row gap-6">
            {widget.photo_url && (
              <div className="flex-shrink-0">
                <img
                  src={widget.photo_url}
                  alt={widget.display_name}
                  className="w-32 h-32 rounded-full object-cover mx-auto md:mx-0"
                  loading="eager"
                  decoding="auto"
                />
              </div>
            )}
            <div className="flex-grow">
              <h1 className="text-3xl font-bold mb-2">{widget.display_name}</h1>
              {widget.subtitle && (
                <p className="text-xl text-slate-600 dark:text-slate-400 mb-4">
                  {widget.subtitle}
                </p>
              )}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                {widget.position && (
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Position:</span>{' '}
                    <span className="font-medium">{widget.position}</span>
                  </div>
                )}
                {widget.age && (
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Age:</span>{' '}
                    <span className="font-medium">{widget.age}</span>
                  </div>
                )}
                {widget.height && (
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Height:</span>{' '}
                    <span className="font-medium">{widget.height}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* News Section */}
      {news && news.length > 0 && (
        <section className="mt-8">
          <h2 className="text-3xl font-bold mb-6">Latest News</h2>
          <div className="grid gap-6">
            {news.map((article) => (
              <article key={article.id} className="card">
                <div className="flex flex-col md:flex-row gap-4">
                  {article.image_url && (
                    <div className="flex-shrink-0">
                      <img
                        src={article.image_url}
                        alt={article.title}
                        className="w-full md:w-48 h-32 object-cover rounded-lg"
                        loading="lazy"
                        decoding="async"
                      />
                    </div>
                  )}
                  <div className="flex-grow">
                    <h3 className="text-xl font-semibold mb-2">
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                      >
                        {article.title}
                      </a>
                    </h3>
                    {article.summary && (
                      <p className="text-slate-600 dark:text-slate-400 mb-2">
                        {article.summary}
                      </p>
                    )}
                    <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
                      <span>{article.source}</span>
                      <span>•</span>
                      <time dateTime={article.published_at}>
                        {new Date(article.published_at).toLocaleDateString()}
                      </time>
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {(!news || news.length === 0) && (
        <div className="mt-8 text-center text-slate-500 dark:text-slate-400">
          <p>No news articles available at this time.</p>
        </div>
      )}
    </div>
  );
}

export default function PlayerPage() {
  return (
    <ErrorBoundary>
      <PlayerPageContent />
    </ErrorBoundary>
  );
}
