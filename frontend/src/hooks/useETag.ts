// Minimal ETag hook placeholder. In practice, this could pull the last known ETag for a key from http cache.
export default function useETag(_key?: string) {
  return null as string | null;
}
