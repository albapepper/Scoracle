# Frontend Streamlining Action Plan

## Overview
This document outlines opportunities to streamline the frontend codebase and remove redundancies after the JS→TS migration.

---

## 🔴 Critical Redundancies (High Priority)

### 1. **Duplicate ThemeProvider Implementation**
**Issue**: `App.tsx` has an inline `ThemeProvider` implementation (lines 16-49), but a proper one exists in `theme/provider.tsx`.

**Impact**: 
- Duplicate code (~35 lines)
- Confusion about which provider to use
- The inline version is less feature-rich (no localStorage persistence, no MantineProvider integration)

**Action**: 
- ✅ Remove inline ThemeProvider from `App.tsx`
- ✅ Import and use `ThemeProvider` from `theme/provider.tsx`
- ✅ Update imports to use `useThemeMode` and `getThemeColors` from `theme/index.ts`

**Files affected**:
- `frontend/src/app/App.tsx` (remove ~35 lines, add 1 import)

---

### 2. **Unused Layout Component Re-exports**
**Issue**: `components/layout/Header.tsx` and `components/layout/Footer.tsx` are just re-exports that point to the main components. Nothing imports from these files.

**Impact**: 
- Unnecessary directory structure
- Confusion about which files to use

**Action**:
- ✅ Delete `components/layout/` directory entirely
- ✅ All imports already use `components/Header` and `components/Footer` (verified)

**Files to delete**:
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/components/layout/Footer.tsx`

---

### 3. **Redundant Type Definition File**
**Issue**: `context/SportContext.d.ts` exists but `SportContext.tsx` already exports all the types.

**Impact**: 
- Redundant type definitions
- Potential for type drift

**Action**:
- ✅ Delete `SportContext.d.ts`
- ✅ All types are properly exported from `SportContext.tsx`

**Files to delete**:
- `frontend/src/context/SportContext.d.ts`

---

## 🟡 Medium Priority Cleanups

### 4. **Unused Router Placeholder**
**Issue**: `app/router.ts` is a placeholder file with empty routes array. Comment says "Not wired yet; existing App.tsx routes remain the source of truth."

**Impact**: 
- Dead code
- Misleading file that suggests future use

**Action**:
- ✅ Delete `app/router.ts` if not planning to use it soon
- ⚠️ OR: Document if this is planned for lazy loading boundaries

**Files to delete**:
- `frontend/src/app/router.ts`

---

### 5. **Empty Directory**
**Issue**: `components/SearchForm/` directory exists but is empty. `SearchForm.tsx` is in the parent directory.

**Impact**: 
- Unnecessary directory structure

**Action**:
- ✅ Delete empty `components/SearchForm/` directory

**Files to delete**:
- `frontend/src/components/SearchForm/` (empty directory)

---

### 6. **Unused Configuration Module**
**Issue**: `app/config/index.ts` exists but nothing imports it. Contains widget feature flags.

**Impact**: 
- Dead code
- Configuration that's not being used

**Action**:
- ✅ Delete `app/config/index.ts` if not needed
- ⚠️ OR: Wire it up if feature flags are planned

**Files to delete**:
- `frontend/src/app/config/index.ts`

---

### 7. **Unused Hook Facade**
**Issue**: `features/widgets/hooks/useWidget.ts` is a facade that re-exports `useWidgetEnvelope` as `useWidget`, but nothing uses it.

**Impact**: 
- Unnecessary abstraction layer

**Action**:
- ✅ Delete `useWidget.ts` if not planning to use the facade pattern
- ⚠️ OR: Keep if planning to add wrapper logic later

**Files to delete**:
- `frontend/src/features/widgets/hooks/useWidget.ts`

---

## 🟢 Low Priority / Review Needed

### 8. **Duplicate Widget Components**
**Issue**: Two similar player widget components exist:
- `components/PlayerWidgetServer.tsx` - Used in EntityPage, uses Mantine components, more polished
- `features/widgets/components/PlayerWidget.tsx` - Simpler, basic HTML, not used anywhere

**Impact**: 
- Code duplication
- Confusion about which to use

**Action**:
- ⚠️ **Review**: Determine if `PlayerWidget.tsx` is legacy code or planned for future use
- ✅ If legacy: Delete `features/widgets/components/PlayerWidget.tsx`
- ⚠️ If needed: Document why both exist or consolidate

**Files to review**:
- `frontend/src/components/PlayerWidgetServer.tsx` (actively used)
- `frontend/src/features/widgets/components/PlayerWidget.tsx` (unused)

---

### 9. **HTTP Client Re-export Pattern**
**Issue**: `features/_shared/http.ts` re-exports `app/http.ts`. This is actually fine for organization, but could be consolidated.

**Impact**: 
- Minor - this is a valid pattern for feature isolation

**Action**:
- ⚠️ **Keep as-is** - This is a reasonable pattern for feature modules to have their own HTTP access point
- ✅ OR: If consolidating, update all imports to use `app/http` directly

**Status**: Low priority - current pattern is acceptable

---

## 📊 Summary Statistics

### Files to Delete (Confirmed Safe):
1. `components/layout/Header.tsx` (re-export)
2. `components/layout/Footer.tsx` (re-export)
3. `context/SportContext.d.ts` (redundant types)
4. `app/router.ts` (unused placeholder)
5. `components/SearchForm/` (empty directory)
6. `app/config/index.ts` (unused config)
7. `features/widgets/hooks/useWidget.ts` (unused facade)

### Code to Refactor:
1. `app/App.tsx` - Remove inline ThemeProvider (~35 lines)

### Files to Review:
1. `features/widgets/components/PlayerWidget.tsx` - Determine if legacy or needed

### Estimated Impact:
- **Lines of code removed**: ~150-200 lines
- **Files deleted**: 7-8 files
- **Directories cleaned**: 2 directories
- **Complexity reduced**: Eliminates duplicate ThemeProvider logic

---

## 🚀 Implementation Order

1. **Phase 1** (Quick wins - 5 min):
   - Delete empty `SearchForm/` directory
   - Delete `SportContext.d.ts`
   - Delete `router.ts`

2. **Phase 2** (Medium effort - 10 min):
   - Delete layout re-exports
   - Delete unused config
   - Delete unused useWidget hook

3. **Phase 3** (Refactor - 15 min):
   - Replace inline ThemeProvider with proper import
   - Test theme switching still works

4. **Phase 4** (Review - 5 min):
   - Review PlayerWidget vs PlayerWidgetServer
   - Delete PlayerWidget if confirmed unused

---

## ✅ Verification Checklist

After implementing changes:
- [ ] Theme switching still works (light/dark mode)
- [ ] Header and Footer render correctly
- [ ] All imports resolve correctly
- [ ] No TypeScript errors
- [ ] No runtime errors
- [ ] Build succeeds

---

## 📝 Notes

- All changes are safe deletions/refactors - no breaking API changes
- The ThemeProvider consolidation is the most impactful change
- Most deletions are dead code that won't affect functionality
- Consider running tests after Phase 3 to ensure theme functionality works

