import { useState, useEffect } from 'react';
import type { SportId, EntityType } from '../lib/types';

interface EntityParams {
  sport: SportId | null;
  type: EntityType | null;
  id: string | null;
}

interface Mention {
  id: string;
  title: string;
  url: string;
  source: string;
  published_at: string;
  summary?: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
}

interface MentionsResponse {
  entity: {
    id: string;
    name: string;
    type: EntityType;
    sport: SportId;
  };
  mentions: Mention[];
}

// Skeleton loader
function LoadingSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-slate-300 dark:bg-slate-700 rounded w-64 mb-4"></div>
      <div className="h-4 bg-slate-300 dark:bg-slate-700 rounded w-48 mb-8"></div>
      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
            <div className="h-5 bg-slate-300 dark:bg-slate-700 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-slate-300 dark:bg-slate-700 rounded w-1/2 mb-2"></div>
            <div className="h-3 bg-slate-300 dark:bg-slate-700 rounded w-1/4"></div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Parse query params from URL
function getEntityParams(): EntityParams {
  if (typeof window === 'undefined') {
    return { sport: null, type: null, id: null };
  }
  
  const params = new URLSearchParams(window.location.search);
  return {
    sport: params.get('sport') as SportId | null,
    type: params.get('type') as EntityType | null,
    id: params.get('id'),
  };
}

export default function MentionsWidget() {
  const [params, setParams] = useState<EntityParams>({ sport: null, type: null, id: null });
  const [data, setData] = useState<MentionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Parse URL params on mount
  useEffect(() => {
    setParams(getEntityParams());
  }, []);

  // Fetch mentions when params are available
  useEffect(() => {
    const { sport, type, id } = params;
    
    if (!sport || !type || !id) {
      if (params.sport !== null || params.type !== null || params.id !== null) {
        // Only show error if some params are present but incomplete
        setError('Missing required parameters. Please select an entity from the search.');
      }
      setLoading(false);
      return;
    }

    const fetchMentions = async () => {
      try {
        setLoading(true);
        setError(null);

        // TODO: Replace with actual API endpoint
        // For now, simulate a response
        const mockData: MentionsResponse = {
          entity: {
            id,
            name: 'Loading...', // Will be replaced by actual API
            type,
            sport,
          },
          mentions: [],
        };

        // Simulated delay for demo
        await new Promise(resolve => setTimeout(resolve, 500));
        
        setData(mockData);
        
        // Update page title
        if (typeof document !== 'undefined') {
          document.title = `Mentions - Scoracle`;
        }
      } catch (e) {
        console.error('Failed to fetch mentions:', e);
        setError('Failed to load mentions. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchMentions();
  }, [params]);

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
          Please search for a player or team to view their mentions.
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

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <h1 className="text-4xl font-bold">
            {data?.entity.name || 'Entity'} Mentions
          </h1>
          <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm uppercase">
            {params.sport}
          </span>
        </div>
        <div className="flex gap-4">
          <a 
            href={`/entity?sport=${params.sport}&type=${params.type}&id=${params.id}`}
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            View Full Profile →
          </a>
        </div>
      </div>

      {/* Mentions List */}
      <div className="space-y-4">
        {data?.mentions && data.mentions.length > 0 ? (
          data.mentions.map((mention) => (
            <article 
              key={mention.id}
              className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700"
            >
              <h3 className="text-lg font-semibold mb-2">
                <a 
                  href={mention.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  {mention.title}
                </a>
              </h3>
              <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400 mb-3">
                <span>{mention.source}</span>
                <span>•</span>
                <span>{mention.published_at}</span>
                {mention.sentiment && (
                  <>
                    <span>•</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      mention.sentiment === 'positive' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                      mention.sentiment === 'negative' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                      'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200'
                    }`}>
                      {mention.sentiment}
                    </span>
                  </>
                )}
              </div>
              {mention.summary && (
                <p className="text-slate-600 dark:text-slate-400">{mention.summary}</p>
              )}
            </article>
          ))
        ) : (
          <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
            <p className="text-slate-600 dark:text-slate-400">
              No recent mentions found for this entity.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
