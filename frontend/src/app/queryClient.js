import { QueryClient } from '@tanstack/react-query';

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        staleTime: 30_000, // 30s baseline
        gcTime: 10 * 60 * 1000,
        retry: (failureCount, error) => {
          if (error?.response?.status === 404) return false;
            // Avoid hammering if repeatedly rate limited
          if (error?.response?.status === 429) return failureCount < 1;
          return failureCount < 2;
        },
      },
    },
  });
}
