# Replace co-mentions page with reusable ComparisonWidget

**Date:** 2026-03-06
**Scope:** Remove /co-mentions page, create ComparisonWidget component, inline shared articles in co-mentions tab

## Goal

Eliminate the standalone `/co-mentions` page by replacing it with a compact, reusable `ComparisonWidget.astro` component and enhancing the co-mentions tab to show shared articles inline. This reduces page count, removes duplicated profile-rendering logic, and provides a better UX by keeping users on their current page.

## What Was Done

### Phase 1: Create ComparisonWidget.astro
Created a new compact profile card component that displays an entity's logo, name, subtitle, and split Stats/News navigation buttons. The component is purely presentational — the parent populates data via DOM IDs using a configurable `slot` prefix. Supports a color indicator bar (`primary`/`secondary` variant) and an optional remove button.

### Phase 2: Rewrite ProfileWidgetComparison.astro
Replaced the hardcoded dual-card HTML with two `<ComparisonWidget>` instances. Added logic to populate Stats and News button hrefs after profile data loads. Removed ~300 lines of duplicated CSS that now lives in ComparisonWidget. The component bus API remains unchanged.

### Phase 3: Enhance co-mentions tab with inline shared articles
Converted co-mention entity links from `<a>` tags (navigating to `/co-mentions`) to `<button>` elements with click handlers. Clicking a co-mentioned entity now filters articles inline and displays them in a drill-down view with a back button. Added the shared articles container to `CoMentionsTab.astro` and corresponding styles.

### Phase 4: Delete removed files and clean up
Removed `co-mentions.astro`, `EntityWidgetPair.astro`, `SharedContentCard.astro`, `SharedArticlesCard.astro`, and `parseCoMentionsParams()` from `dom.ts`. Updated CLAUDE.md project structure.

## Files Changed

**Created:**
- `src/components/ComparisonWidget.astro` — new reusable compact profile card

**Modified:**
- `src/components/ProfileWidgetComparison.astro` — uses ComparisonWidget, adds button hrefs
- `src/lib/tabs/co-mentions-tab.ts` — inline shared articles view with drill-down/back
- `src/components/tabs/CoMentionsTab.astro` — added shared articles container and styles
- `src/lib/utils/dom.ts` — removed `parseCoMentionsParams()`
- `CLAUDE.md` — updated project structure

**Deleted:**
- `src/pages/co-mentions.astro`
- `src/components/EntityWidgetPair.astro`
- `src/components/SharedContentCard.astro`
- `src/components/SharedArticlesCard.astro`

## Verification

- `npx astro check`: 0 errors, 0 warnings, 5 pre-existing hints
- `npm run build`: Production build succeeds (6.18s)
- No broken imports or references to deleted files

## Result

The `/co-mentions` page has been fully replaced. Entity comparisons on the stats page now use the reusable `ComparisonWidget` with Stats/News navigation buttons. Co-mentioned entities on the news page can be explored inline without leaving the page. Net reduction of ~1,127 lines across the codebase.
