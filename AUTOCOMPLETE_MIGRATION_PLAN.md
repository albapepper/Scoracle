# Autocomplete Migration Plan: Backend JSON → Frontend IndexedDB

## 🎯 Goal
Migrate autofill from backend JSON calls to local IndexedDB searches for instant, zero-latency autocomplete while maintaining backend control over entity data via Python seeding.

---

## 📊 Current State Analysis

### ✅ What Already Exists

**Frontend Infrastructure:**
- ✅ IndexedDB service (`services/indexedDB.ts`) with:
  - `searchPlayers()` and `searchTeams()` functions
  - Normalization and scoring logic
  - Sport-scoped queries
- ✅ Web Worker (`features/autocomplete/worker/autocomplete.worker.ts`) that:
  - Searches IndexedDB locally
  - Returns results in `AutocompleteResult` format
- ✅ `useAutocomplete` hook that uses the worker
- ✅ `EntityAutocomplete` component that displays results

**Backend Infrastructure:**
- ✅ `/api/v1/{sport}/sync/players` - Returns players for seeding
- ✅ `/api/v1/{sport}/sync/teams` - Returns teams for seeding
- ✅ `/api/v1/{sport}/bootstrap` - Unified endpoint (players + teams) with ETag support
- ✅ `/api/v1/{sport}/entities` - Entity dump endpoint
- ✅ Python seeding scripts (`database/seed_local_dbs.py`)

### ❌ What's Missing

1. **Frontend seeding mechanism** - No code to fetch from backend and populate IndexedDB
2. **Sport change handler** - No automatic sync when user switches sports
3. **Initial load sync** - No check/seed on app startup
4. **Update mechanism** - No way to refresh stale data

---

## 🏗️ Migration Architecture

### Data Flow

```
Backend (Python/SQLite)
    ↓ (HTTP GET /api/v1/{sport}/bootstrap)
Frontend Seeding Service
    ↓ (upsertPlayers/upsertTeams)
IndexedDB (Browser)
    ↓ (searchPlayers/searchTeams via Worker)
Autocomplete Results
    ↓ (onSelect)
Entity ID + Sport → Widget Calls
```

### Key Components

1. **Sync Service** (`services/syncService.ts`) - NEW
   - Fetches data from backend bootstrap endpoint
   - Handles ETag/304 Not Modified for efficient updates
   - Manages sport-specific syncing
   - Tracks last sync timestamp per sport

2. **Sync Hook** (`hooks/useIndexedDBSync.ts`) - NEW
   - React hook for automatic syncing
   - Triggers on sport change
   - Handles initial load
   - Manages loading/error states

3. **Enhanced IndexedDB Service** - MODIFY
   - Already has search functions ✅
   - Already has upsert functions ✅
   - May need minor adjustments for data format

4. **Backend Bootstrap Endpoint** - EXISTS ✅
   - Already returns proper format
   - Has ETag support for caching
   - Returns `datasetVersion` for change detection

---

## 📋 Implementation Plan

### Phase 1: Create Sync Service (Backend → IndexedDB)

**File: `frontend/src/services/syncService.ts`**

```typescript
// Responsibilities:
// - Fetch bootstrap data from backend
// - Handle ETag/304 responses
// - Transform backend format to IndexedDB format
// - Call IndexedDB upsert functions
// - Track sync state per sport
```

**Key Functions:**
- `syncSport(sport: string, force?: boolean): Promise<SyncResult>`
- `getLastSyncTimestamp(sport: string): Promise<number | null>`
- `shouldSync(sport: string, maxAge?: number): Promise<boolean>`

**Data Transformation:**
- Backend format: `{ id, firstName, lastName, currentTeam }`
- IndexedDB format: `PlayerRecord` (already compatible ✅)

---

### Phase 2: Create Sync Hook

**File: `frontend/src/hooks/useIndexedDBSync.ts`**

```typescript
// Responsibilities:
// - Auto-sync on sport change
// - Sync on initial mount
// - Provide loading/error states
// - Expose manual sync function
```

**Hook API:**
```typescript
const { 
  isSyncing, 
  lastSyncTime, 
  syncError, 
  syncSport 
} = useIndexedDBSync();
```

**Integration Points:**
- Use in `SportContext` or `App.tsx` to trigger on sport change
- Initialize IndexedDB on app startup

---

### Phase 3: Update Autocomplete to Use Local Search

**Current State:**
- ✅ Worker already searches IndexedDB
- ✅ `useAutocomplete` already uses worker
- ⚠️ Need to ensure IndexedDB is initialized before searches

**Changes Needed:**
- Ensure IndexedDB is initialized before first search
- Add fallback to backend if IndexedDB is empty (graceful degradation)
- Handle case where sport changes mid-search

---

### Phase 4: Backend Seeding (Python Control)

**Current State:**
- ✅ Backend has seeding scripts
- ✅ Bootstrap endpoint exists
- ✅ Python can manipulate SQLite directly

**Enhancements:**
- Document seeding workflow
- Add cron/scheduled seeding option (optional)
- Ensure bootstrap endpoint handles large datasets efficiently

---

## 🔄 Migration Steps

### Step 1: Create Sync Service
1. Create `services/syncService.ts`
2. Implement `syncSport()` function
3. Handle ETag/304 responses
4. Transform and upsert to IndexedDB
5. Add error handling

### Step 2: Create Sync Hook
1. Create `hooks/useIndexedDBSync.ts`
2. Implement auto-sync on sport change
3. Add initial load sync
4. Expose sync state to components

### Step 3: Integrate Sync into App
1. Add sync hook to `App.tsx` or `SportContext`
2. Trigger sync when sport changes
3. Initialize IndexedDB on app startup
4. Show sync status in UI (optional)

### Step 4: Verify Autocomplete Works
1. Ensure IndexedDB is populated before searches
2. Test autocomplete with local data
3. Verify entity selection passes ID + sport downstream
4. Test widget calls with selected entity

### Step 5: Add Fallback (Optional)
1. If IndexedDB empty, fallback to backend search
2. Log warnings when fallback is used
3. Auto-trigger sync if fallback is needed

---

## 📐 Technical Details

### Backend Bootstrap Response Format

```json
{
  "sport": "NBA",
  "datasetVersion": "nba-500p-30t-2025-01-15",
  "generatedAt": "2025-01-15T10:30:00Z",
  "players": {
    "count": 500,
    "items": [
      {
        "id": 237,
        "firstName": "LeBron",
        "lastName": "James",
        "currentTeam": "LAL"
      }
    ]
  },
  "teams": {
    "count": 30,
    "items": [
      {
        "id": 14,
        "name": "Los Angeles Lakers"
      }
    ]
  }
}
```

### IndexedDB Record Format (Already Compatible)

```typescript
interface PlayerRecord {
  id: string; // `${sport}-${player.id}`
  playerId: string | number;
  sport: SportCode;
  firstName?: string;
  lastName?: string;
  fullName: string;
  currentTeam?: string;
  normalized_name: string;
  updatedAt: number;
}
```

### Sync Strategy

1. **Initial Load:**
   - Check if IndexedDB has data for active sport
   - If empty or stale (>24 hours), sync from backend
   - Show loading state during sync

2. **Sport Change:**
   - Check if IndexedDB has data for new sport
   - If empty, sync immediately
   - If exists but stale, sync in background

3. **Update Frequency:**
   - Default: Sync if data >24 hours old
   - Force sync: Manual refresh button (optional)
   - ETag support: Only download if changed

---

## 🧪 Testing Strategy

### Unit Tests
- Sync service: Transform backend → IndexedDB format
- Sync hook: Trigger sync on sport change
- IndexedDB search: Verify results match backend

### Integration Tests
- Full flow: Backend → Sync → IndexedDB → Search → Results
- Sport switching: Verify data loads for new sport
- Offline: Verify local search works without backend

### Performance Tests
- Measure sync time for large datasets (500+ players)
- Measure search latency (should be <10ms)
- Compare to current backend search latency

---

## 🚀 Performance Benefits

### Current (Backend JSON)
- Network latency: 50-200ms per keystroke
- Backend load: Every search hits API
- Rate limiting: Subject to backend limits

### After Migration (IndexedDB)
- Search latency: <10ms (local)
- Backend load: Only on sync (once per sport per day)
- Rate limiting: No impact on autocomplete
- Offline capable: Works without backend

---

## 📝 Implementation Checklist

- [ ] Create `services/syncService.ts`
  - [ ] Implement `syncSport()` function
  - [ ] Handle ETag/304 responses
  - [ ] Transform backend format
  - [ ] Upsert to IndexedDB
  - [ ] Error handling

- [ ] Create `hooks/useIndexedDBSync.ts`
  - [ ] Auto-sync on sport change
  - [ ] Initial load sync
  - [ ] Loading/error states
  - [ ] Manual sync function

- [ ] Integrate sync into app
  - [ ] Add to `SportContext` or `App.tsx`
  - [ ] Initialize IndexedDB on startup
  - [ ] Handle sport changes

- [ ] Verify autocomplete
  - [ ] Ensure IndexedDB populated before search
  - [ ] Test entity selection
  - [ ] Verify ID + sport passed downstream

- [ ] Add fallback (optional)
  - [ ] Backend search if IndexedDB empty
  - [ ] Auto-trigger sync on fallback

- [ ] Documentation
  - [ ] Update README with sync process
  - [ ] Document backend seeding workflow
  - [ ] Add troubleshooting guide

---

## 🔍 Risk Mitigation

### Risk: IndexedDB Not Populated
**Mitigation:** 
- Check on app startup
- Auto-sync if empty
- Fallback to backend search

### Risk: Large Dataset Sync Time
**Mitigation:**
- Show loading indicator
- Sync in background
- Use ETag to skip unchanged data

### Risk: Stale Data
**Mitigation:**
- Track last sync timestamp
- Sync if >24 hours old
- Manual refresh option

### Risk: Browser Storage Limits
**Mitigation:**
- Monitor IndexedDB size
- Clear old sport data if needed
- Warn if approaching limits

---

## 📈 Success Metrics

1. **Search Latency:** <10ms (vs 50-200ms currently)
2. **Backend Load:** 95% reduction (sync vs search)
3. **User Experience:** Instant autocomplete results
4. **Offline Support:** Works without backend connection

---

## 🎓 Next Steps

1. Review and approve this plan
2. Implement Phase 1 (Sync Service)
3. Implement Phase 2 (Sync Hook)
4. Integrate and test
5. Deploy and monitor

---

## 📚 References

- Existing IndexedDB service: `frontend/src/services/indexedDB.ts`
- Existing autocomplete worker: `frontend/src/features/autocomplete/worker/autocomplete.worker.ts`
- Backend bootstrap endpoint: `backend/app/routers/sport.py` (line 374)
- Backend seeding script: `backend/app/database/seed_local_dbs.py`

