# Checklist Audit deployment

CardVault 4.2 introduces an isolated staging table for verified external
checklist files. Candidate rows never enter `public.cards` until a collector
marks them **Verified**, selects them, and confirms promotion.

## Existing Supabase projects

1. Back up the Supabase project or confirm a recent backup.
2. Run `cardvault_year_2020_migration.sql` if the project still restricts years
   to 2021 or later.
3. In **Supabase Dashboard → SQL Editor**, run the complete contents of
   `cardvault_checklist_staging_migration.sql` once.
4. Confirm these objects exist:

   ```sql
   select column_name
   from information_schema.columns
   where table_schema = 'public'
     and table_name = 'checklist_staging';

   select indexname
   from pg_indexes
   where schemaname = 'public'
     and tablename = 'checklist_staging';
   ```

5. Deploy the updated Streamlit files. Existing secrets are unchanged.
6. Open **Checklist Audit** and upload a verified CSV into staging.

## Verified CSV columns

Required: `year`, `set_name`, `card_number`.

Supported: `manufacturer`, `card_name`, `category`, `variation` (or
`parallel`), `serial_number`, `priority`, `source_url`,
`verification_status`, and `verification_notes`.

Imported candidates default to `Pending`. A candidate needs a source URL before
the UI permits `Verified`. Promotion re-fetches both staging and live cards and
rechecks identity duplicates immediately before each additive insert.

## Safety guarantees

- No staging operation deletes or updates `public.cards`.
- Promotion inserts new `Need` rows only.
- Exact staged duplicates and identities already present live are blocked.
- Rejected, Pending, Needs Review, Promoted, or source-less rows are blocked.
- Existing authentication, Row Level Security, storage, indexes, imports, and
  card images remain unchanged.
