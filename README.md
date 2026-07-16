# CardVault 4.2

A polished Streamlit collection manager for an Adolis García Texas Rangers
sports-card collection. CardVault uses the existing Supabase schema and never
creates placeholder collection data.

## Architecture

- `app.py` — session orchestration and routing
- `components/` — reusable visual components
- `pages/` — page-level renderers
- `utils/` — database, statistics, filters, imports, and diagnostics
- `assets/` — shared visual theme

## 4.1 collector improvements

- Database Health reports with duplicate and incomplete-record CSV exports
- Expanded collection filters, sorts, quick actions, and mobile layouts
- Full selected-card editor using the existing Supabase row and storage object
- Related-card context and a purpose-built Need It shopping mode

## Database migrations

For existing Supabase projects created with the original `year >= 2021`
constraint, run `cardvault_year_2020_migration.sql` once before importing 2020
cards. See `YEAR_2020_MIGRATION.md` for deployment and verification steps.

Existing projects must also run `cardvault_checklist_staging_migration.sql`
before opening Checklist Audit. This additive migration creates the private
staging table and adds the live `manufacturer` identity field; it never rewrites
or deletes a collection card. See `CHECKLIST_AUDIT_DEPLOYMENT.md`.

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
