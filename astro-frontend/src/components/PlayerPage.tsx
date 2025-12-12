import { useState, useEffect } from 'react';
import { getEntity } from '../lib/api/entities';
import type { SportId, EntityResponse } from '../lib/types';

export default function PlayerPage() {
  const [data, setData] = useState<EntityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Extract sport and playerId from URL path
    const pathParts = window.location.pathname.split('/').filter(Boolean);
    const sport = pathParts[0] as SportId;
    const playerId = pathParts[2];

    if (!sport || !playerId) {
      setError('Invalid URL');
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await getEntity('player', playerId, sport, {
          includeWidget: true,
          includeNews: true,
        });
        setData(result);
        setError(null);
        
        // Update page title
        if (result.entity?.name) {
          document.title = `${result.entity.name} - Scoracle`;
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
        <div className="text-lg">Loading player data...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container-custom py-12 text-center">
        <div className="text-lg text-red-600 dark:text-red-400">
          {error || 'Player not found'}
        </div>
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
