# CardVault 4.0

A polished Streamlit collection manager for an Adolis García Texas Rangers
sports-card collection. CardVault uses the existing Supabase schema and never
creates placeholder collection data.

## Architecture

- `app.py` — session orchestration and routing
- `components/` — reusable visual components
- `pages/` — page-level renderers
- `utils/` — database, statistics, filters, imports, and diagnostics
- `assets/` — shared visual theme

## Install

1. Back up your current `adoliscards` folder.
2. Extract this ZIP.
3. Copy the files into the existing GitHub repository folder.
4. Replace matching files.
5. Keep `.streamlit/secrets.toml`.
6. No Supabase migration is required.
7. Commit and push in GitHub Desktop.
8. Streamlit Cloud will redeploy automatically.

## Added

- Larger CardVault branding
- Sidebar icons
- Stronger metric-card icons
- Premium card placeholders
- Visual card tiles
- Auto/relic/numbered/parallel badges
- Improved search and filters
- Better Set Progress drill-down
- Better Need It shopping cards
- Cleaner mobile presentation
