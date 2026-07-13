
-- Run this entire file in Supabase Dashboard > SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.cards (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    year integer not null check (year >= 2021),
    set_name text not null,
    card_number text default '',
    card_name text default '',
    category text default 'Base',
    parallel text default '',
    serial_number text default '',
    status text default 'Need',
    priority text default 'Core',
    condition text default 'Raw',
    grade text default '',
    price_paid numeric(12,2) default 0,
    estimated_value numeric(12,2) default 0,
    date_acquired date,
    seller text default '',
    storage_location text default '',
    image_path text default '',
    source_url text default '',
    favorite boolean default false,
    notes text default '',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

alter table public.cards enable row level security;

drop policy if exists "Users can read own cards" on public.cards;
create policy "Users can read own cards"
on public.cards for select
to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists "Users can insert own cards" on public.cards;
create policy "Users can insert own cards"
on public.cards for insert
to authenticated
with check ((select auth.uid()) = user_id);

drop policy if exists "Users can update own cards" on public.cards;
create policy "Users can update own cards"
on public.cards for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

drop policy if exists "Users can delete own cards" on public.cards;
create policy "Users can delete own cards"
on public.cards for delete
to authenticated
using ((select auth.uid()) = user_id);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists cards_set_updated_at on public.cards;
create trigger cards_set_updated_at
before update on public.cards
for each row execute function public.set_updated_at();

-- Private image bucket
insert into storage.buckets (id, name, public)
values ('card-images', 'card-images', false)
on conflict (id) do update set public = false;

-- Users may only access files inside a folder named with their own user ID.
drop policy if exists "Users can view own card images" on storage.objects;
create policy "Users can view own card images"
on storage.objects for select
to authenticated
using (
    bucket_id = 'card-images'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
);

drop policy if exists "Users can upload own card images" on storage.objects;
create policy "Users can upload own card images"
on storage.objects for insert
to authenticated
with check (
    bucket_id = 'card-images'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
);

drop policy if exists "Users can update own card images" on storage.objects;
create policy "Users can update own card images"
on storage.objects for update
to authenticated
using (
    bucket_id = 'card-images'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
)
with check (
    bucket_id = 'card-images'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
);

drop policy if exists "Users can delete own card images" on storage.objects;
create policy "Users can delete own card images"
on storage.objects for delete
to authenticated
using (
    bucket_id = 'card-images'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
);

-- Database API grants required in addition to Row Level Security policies.
grant usage on schema public to authenticated;
grant select, insert, update, delete on table public.cards to authenticated;
