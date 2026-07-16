-- CardVault: allow Rangers-era Adolis Garcia cards beginning in 2020.
-- Safe, in-place migration: no table recreation, data changes, index changes,
-- authentication changes, or policy changes are performed.

begin;

alter table public.cards
drop constraint if exists cards_year_check;

alter table public.cards
add constraint cards_year_check
check (year >= 2020);

commit;
