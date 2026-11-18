-- SAP MM + SD Trainer v2.0.0
-- Run once in the SQL Editor of your Supabase project.
-- In Authentication > Providers enable "Allow anonymous sign-ins".
-- Never publish service_role keys. Publishable / anon key is safe for frontend with RLS.

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  fio text not null check (char_length(trim(fio)) between 5 and 120),
  created_at timestamptz not null default now()
);

create table if not exists public.test_results (
  id bigint generated always as identity primary key,
  participant_id uuid not null references public.profiles(id) on delete cascade,
  test_no integer not null check (test_no between 1 and 25),
  score integer not null check (score between 0 and 20),
  errors integer not null check (errors between 0 and 20),
  completed_at timestamptz not null default now(),
  unique (participant_id,test_no),
  constraint score_errors_add_up_to_20 check (score + errors = 20)
);

create index if not exists idx_test_results_participant on public.test_results(participant_id);

alter table public.profiles enable row level security;
alter table public.test_results enable row level security;

-- Everyone may read the ranking. This deliberately publishes entered names and scores.
drop policy if exists "public_read_profiles" on public.profiles;
create policy "public_read_profiles" on public.profiles for select to anon, authenticated using (true);
drop policy if exists "public_read_scores" on public.test_results;
create policy "public_read_scores" on public.test_results for select to anon, authenticated using (true);

-- An anonymous Auth identity may only register or rename itself.
drop policy if exists "insert_own_profile" on public.profiles;
create policy "insert_own_profile" on public.profiles for insert to authenticated with check (id = auth.uid());
drop policy if exists "update_own_profile" on public.profiles;
create policy "update_own_profile" on public.profiles for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- One immutable submitted score for each participant and test. No client UPDATE/DELETE.
drop policy if exists "insert_own_result" on public.test_results;
create policy "insert_own_result" on public.test_results for insert to authenticated
  with check (participant_id = auth.uid());

-- Invoker-rights view respects table RLS; public profiles/results have SELECT policies.
create or replace view public.leaderboard with (security_invoker = true) as
select
  p.id,
  p.fio,
  coalesce(sum(r.score),0)::integer as total_score,
  count(r.test_no)::integer as tests_completed,
  coalesce(sum(r.errors),0)::integer as total_errors
from public.profiles p
left join public.test_results r on r.participant_id = p.id
group by p.id,p.fio;

grant select on public.profiles,public.test_results,public.leaderboard to anon,authenticated;
grant insert,update on public.profiles to authenticated;
grant insert on public.test_results to authenticated;
grant usage on schema public to anon,authenticated;
grant usage,select on sequence public.test_results_id_seq to authenticated;

-- Privacy: FIO is public by design. For a real high-stakes exam, enforce score
-- validation in a server-side Edge Function; client-side scores can be forged.
