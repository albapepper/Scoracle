# Vanilla JS Refactor - Frontend Cleanup

**Date:** 2026-02-23
**Scope:** `astro-frontend/src/`
**Commit:** `b53cdcf`

## Goal

Refactor the Astro frontend's client-side JavaScript to be leaner and more Astro-idiomatic. The original plan considered adopting petite-vue or Alpine.js, but both were rejected (petite-vue is unmaintained since 2021; Alpine.js adds 17kb for minimal benefit). The final decision was to keep vanilla JS and simply clean it up.

### Constraints

- Only UI interaction code was refactored — data/API modules (`api-fetcher.ts`, `autocomplete.ts`, `component-bus.ts`, `entity-data-store.ts`, pizza chart, SSR hydration) were left untouched.
- Zero new dependencies added.
- Component bus API surface kept identical so all inter-component communication continues to work.

## What Was Done

### 1. Shared DOM helpers (`src/lib/utils/dom.ts`)

Added two utility functions to eliminate repetitive show/hide boilerplate across the codebase:

- **`showState(container, prefix, activeState, allStates)`** — toggles `hidden` class on elements with IDs like `{prefix}-{state}`. Used by tabs, comparison components, and content cards.
- **`showWidgetState(loadingEl, contentEl, errorEl, state)`** — toggles `display` style for profile widgets that use `display: none/flex` instead of the `hidden` class.

### 2. Native HTML elements replacing JS-heavy patterns

- **`ComparisonSearchModal.astro`** — Replaced `<div class="comparison-modal hidden">` with native `<dialog>`. Gains free backdrop, Escape-to-close, focus trapping, and scroll lock. Reduced ~200-line `ComparisonModalManager` class to ~60 lines of module-level functions.
- **`HamburgerMenu.astro`** — Replaced `<div>` + `<button id="menu-toggle">` with `<details>`/`<summary>`. Icon switching (hamburger vs X) now handled entirely via CSS `[open]` attribute — zero JS for that concern. 78-line class reduced to ~20 lines of flat JS.

### 3. Classes flattened to module-level functions

- **`CrystalBallSelector.astro`** — Class replaced with top-level `const` declarations and standalone functions. Same functionality, ~20 lines shorter.
- **`news.astro`** — 60-line `NewsPageManager` class replaced with ~15 lines of flat code.
- **`stats.astro`** — `EntityPageManager` class replaced with module-level functions and flat state variables.

### 4. Tab controller modernized (`src/lib/utils/tab-controller.ts`)

Added a new `initTabs()` function export alongside the existing `TabController` class for backward compatibility. All three content card consumers updated to use the simpler function:

- `NewsContentCard.astro`
- `PlayerStatsContentCard.astro`
- `TeamStatsContentCard.astro`

### 5. `showState` applied across all components

**Tab modules** (`src/lib/tabs/`):
- `co-mentions-tab.ts`, `twitter-tab.ts`, `momentum-tab.ts`, `strengths-weaknesses-tab.ts`, `similarity-tab.ts`

**Tab components** (`src/components/tabs/`):
- `NewsTab.astro`, `PredictionsTab.astro`, `TransfersTab.astro`, `VibesTab.astro`, `PlayerStatsTab.astro`, `TeamStatsTab.astro`

**Profile widgets**:
- `PlayerProfileWidget.astro`, `TeamProfileWidget.astro`, `ProfileWidgetComparison.astro`

**Comparison components**:
- `StatsComparisonContent.astro`, `StatsComparison.astro`, `StrengthsWeaknessesComparison.astro`

## Files Changed (27 total)

| File | Change |
|------|--------|
| `src/lib/utils/dom.ts` | Added `showState()` and `showWidgetState()` |
| `src/lib/utils/tab-controller.ts` | Added `initTabs()` function |
| `src/components/HamburgerMenu.astro` | Full rewrite with `<details>` |
| `src/components/ComparisonSearchModal.astro` | Full rewrite with `<dialog>` |
| `src/components/CrystalBallSelector.astro` | Script block rewritten |
| `src/components/NewsContentCard.astro` | Simplified script |
| `src/components/PlayerStatsContentCard.astro` | Simplified script |
| `src/components/TeamStatsContentCard.astro` | Simplified script |
| `src/components/PlayerProfileWidget.astro` | Show/hide replaced |
| `src/components/TeamProfileWidget.astro` | Show/hide replaced |
| `src/components/ProfileWidgetComparison.astro` | Show/hide replaced |
| `src/components/StatsComparisonContent.astro` | Show/hide replaced |
| `src/components/StatsComparison.astro` | Show/hide replaced |
| `src/components/StrengthsWeaknessesComparison.astro` | Show/hide replaced |
| `src/components/tabs/NewsTab.astro` | Show/hide replaced |
| `src/components/tabs/PredictionsTab.astro` | Show/hide replaced |
| `src/components/tabs/TransfersTab.astro` | Show/hide replaced |
| `src/components/tabs/VibesTab.astro` | Show/hide replaced |
| `src/components/tabs/PlayerStatsTab.astro` | Show/hide replaced |
| `src/components/tabs/TeamStatsTab.astro` | Show/hide replaced |
| `src/lib/tabs/co-mentions-tab.ts` | Show/hide replaced |
| `src/lib/tabs/twitter-tab.ts` | Show/hide replaced |
| `src/lib/tabs/momentum-tab.ts` | Show/hide replaced |
| `src/lib/tabs/strengths-weaknesses-tab.ts` | Show/hide replaced |
| `src/lib/tabs/similarity-tab.ts` | Show/hide replaced |
| `src/pages/news.astro` | Script simplified |
| `src/pages/stats.astro` | Script simplified |

## Result

- **551 insertions, 1,077 deletions** — net reduction of **526 lines**
- Build passes cleanly (`astro check && astro build`): 0 errors, 0 warnings
- No new dependencies
- All component bus contracts preserved
