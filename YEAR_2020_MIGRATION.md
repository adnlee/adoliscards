# CardVault 2020 Year Migration

This migration expands the existing `cards.year` constraint to include the full
Texas Rangers-era Adolis García checklist beginning in 2020. It does not recreate
the table or modify rows, indexes, authentication, Row Level Security, storage,
or other constraints.

## Deploy

1. Back up the Supabase project or confirm a recent backup is available.
2. Open **Supabase Dashboard → SQL Editor → New query**.
3. Paste the complete contents of `cardvault_year_2020_migration.sql`.
4. Run the query once. The transaction drops only `cards_year_check` and adds the
   replacement `CHECK (year >= 2020)` constraint.
5. Verify the constraint:

   ```sql
   select pg_get_constraintdef(oid)
   from pg_constraint
   where conrelid = 'public.cards'::regclass
     and conname = 'cards_year_check';
   ```

   Expected result: `CHECK ((year >= 2020))`.

6. Redeploy the updated Streamlit files. No new secrets or environment variables
   are required.
7. Import the 2020 Topps Update `U-166` row. The CSV preview and insert should
   complete without a year validation or database constraint error.

## Rollback

Rollback to `year >= 2021` is safe only when no 2020 rows exist. Check first:

```sql
select count(*) from public.cards where year = 2020;
```

Do not restore the older constraint while this count is greater than zero.
