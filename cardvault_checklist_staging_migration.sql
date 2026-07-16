-- CardVault 4.2 verified master-checklist staging system.
-- Additive only: existing cards, indexes, authentication, and policies are preserved.

begin;

alter table public.cards
add column if not exists manufacturer text default '';

create table if not exists public.checklist_staging (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    collection_id uuid not null references public.collections(id) on delete cascade,
    year integer not null check (year >= 2020),
    manufacturer text default '',
    set_name text not null,
    card_number text default '',
    card_name text default 'Adolis Garcia',
    category text default 'Base',
    variation text default '',
    serial_number text default '',
    priority text default 'Core',
    source_url text default '',
    verification_status text not null default 'Pending'
        check (verification_status in ('Pending', 'Needs Review', 'Verified', 'Rejected', 'Promoted')),
    verified_at timestamptz,
    verification_notes text default '',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create index if not exists idx_checklist_staging_collection
on public.checklist_staging(collection_id);

create index if not exists idx_checklist_staging_review
on public.checklist_staging(collection_id, verification_status);

alter table public.checklist_staging enable row level security;

drop policy if exists "Users can read own checklist staging" on public.checklist_staging;
create policy "Users can read own checklist staging"
on public.checklist_staging for select to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists "Users can insert own checklist staging" on public.checklist_staging;
create policy "Users can insert own checklist staging"
on public.checklist_staging for insert to authenticated
with check ((select auth.uid()) = user_id);

drop policy if exists "Users can update own checklist staging" on public.checklist_staging;
create policy "Users can update own checklist staging"
on public.checklist_staging for update to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

grant select, insert, update on public.checklist_staging to authenticated;

commit;
