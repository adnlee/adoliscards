
-- CardVault V2 migration
-- Run once in Supabase SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.collections (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    name text not null,
    sport text default '',
    team text default '',
    player_name text default '',
    description text default '',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

alter table public.collections enable row level security;

drop policy if exists "Users can read own collections" on public.collections;
create policy "Users can read own collections"
on public.collections for select
to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists "Users can insert own collections" on public.collections;
create policy "Users can insert own collections"
on public.collections for insert
to authenticated
with check ((select auth.uid()) = user_id);

drop policy if exists "Users can update own collections" on public.collections;
create policy "Users can update own collections"
on public.collections for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

drop policy if exists "Users can delete own collections" on public.collections;
create policy "Users can delete own collections"
on public.collections for delete
to authenticated
using ((select auth.uid()) = user_id);

grant select, insert, update, delete
on public.collections
to authenticated;

alter table public.cards
add column if not exists collection_id uuid
references public.collections(id)
on delete cascade;

create index if not exists idx_cards_collection_id
on public.cards(collection_id);

create index if not exists idx_cards_collection_year
on public.cards(collection_id, year);

create index if not exists idx_cards_status
on public.cards(status);

grant select, insert, update, delete
on public.cards
to authenticated;
