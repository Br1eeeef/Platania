create extension if not exists pgcrypto;

create type public.membership_plan as enum ('free', 'pro');
create type public.membership_status as enum ('pending', 'active', 'expired', 'suspended', 'banned');
create type public.strategy_visibility as enum ('private', 'public');

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null check (char_length(display_name) between 2 and 40),
  avatar_url text,
  bio text check (char_length(bio) <= 300),
  is_admin boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.memberships (
  user_id uuid primary key references auth.users(id) on delete cascade,
  plan public.membership_plan not null default 'free',
  status public.membership_status not null default 'pending',
  starts_at timestamptz not null default now(),
  expires_at timestamptz not null default (now() + interval '30 days'),
  ai_quota integer not null default 3 check (ai_quota >= 0),
  backtest_quota integer not null default 10 check (backtest_quota >= 0),
  payment_note text check (char_length(payment_note) <= 500),
  external_payment_reference text check (char_length(external_payment_reference) <= 120),
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.admin_audit_logs (
  id uuid primary key default gen_random_uuid(),
  admin_user_id uuid not null references auth.users(id) on delete restrict,
  target_user_id uuid references auth.users(id) on delete set null,
  action text not null,
  before_state jsonb,
  after_state jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table public.watchlists (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (char_length(name) between 1 and 40),
  created_at timestamptz not null default now(),
  unique (user_id, name)
);

create table public.watchlist_items (
  id uuid primary key default gen_random_uuid(),
  watchlist_id uuid references public.watchlists(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  symbol text not null check (symbol ~ '^[0-9]{6}\.(SH|SZ)$'),
  added_at timestamptz not null default now(),
  unique (user_id, symbol)
);

create table public.strategies (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (char_length(name) between 2 and 80),
  visibility public.strategy_visibility not null default 'private',
  current_version integer not null default 1 check (current_version > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.strategy_versions (
  id uuid primary key default gen_random_uuid(),
  strategy_id uuid not null references public.strategies(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  version integer not null check (version > 0),
  spec jsonb not null,
  readable_code text,
  created_at timestamptz not null default now(),
  unique (strategy_id, version)
);

create table public.backtest_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  strategy_version_id uuid references public.strategy_versions(id) on delete set null,
  symbol text not null,
  status text not null check (status in ('queued', 'running', 'completed', 'failed')),
  parameters jsonb not null default '{}'::jsonb,
  metrics jsonb,
  data_source text,
  is_demo boolean not null default false,
  error_message text,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create table public.signals (
  id uuid primary key default gen_random_uuid(),
  strategy_id uuid references public.strategies(id) on delete cascade,
  symbol text not null,
  state text not null,
  reasons jsonb not null default '[]'::jsonb,
  generated_at date not null,
  data_source text not null,
  is_demo boolean not null default false,
  unique (strategy_id, symbol, generated_at)
);

create table public.posts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null check (char_length(title) between 3 and 120),
  content text not null check (char_length(content) between 20 and 20000),
  symbol text,
  backtest_run_id uuid references public.backtest_runs(id) on delete set null,
  is_public boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.follows (
  follower_id uuid not null references auth.users(id) on delete cascade,
  following_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (follower_id, following_id),
  check (follower_id <> following_id)
);

create table public.likes (
  user_id uuid not null references auth.users(id) on delete cascade,
  post_id uuid not null references public.posts(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, post_id)
);

create table public.comments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  post_id uuid not null references public.posts(id) on delete cascade,
  content text not null check (char_length(content) between 1 and 2000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  type text not null,
  payload jsonb not null default '{}'::jsonb,
  read_at timestamptz,
  created_at timestamptz not null default now()
);

create table public.ai_usage (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  request_id uuid not null unique,
  usage_date date not null default current_date,
  status text not null check (status in ('reserved', 'completed', 'refunded')),
  input_tokens integer not null default 0 check (input_tokens >= 0),
  output_tokens integer not null default 0 check (output_tokens >= 0),
  model text,
  created_at timestamptz not null default now()
);

create index posts_public_created_idx on public.posts (created_at desc) where is_public;
create index signals_symbol_date_idx on public.signals (symbol, generated_at desc);
create index backtest_runs_user_created_idx on public.backtest_runs (user_id, created_at desc);
create index notifications_user_unread_idx on public.notifications (user_id, created_at desc) where read_at is null;
create index ai_usage_user_date_idx on public.ai_usage (user_id, usage_date);
create index memberships_expiry_idx on public.memberships (status, expires_at);
create index admin_audit_created_idx on public.admin_audit_logs (created_at desc);

create or replace function public.set_updated_at() returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace function public.handle_new_user() returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'display_name', split_part(new.email, '@', 1)));
  insert into public.memberships (user_id) values (new.id);
  insert into public.watchlists (user_id, name) values (new.id, '默认自选');
  return new;
end;
$$;

create or replace function public.current_user_is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.profiles where id = auth.uid() and is_admin = true);
$$;

create or replace function public.current_user_has_active_membership() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.memberships
    where user_id = auth.uid()
      and status = 'active'
      and starts_at <= now()
      and expires_at > now()
  );
$$;

create or replace function public.enforce_feature_quota() returns trigger
language plpgsql security definer set search_path = public as $$
declare
  member public.memberships%rowtype;
  used_count integer;
begin
  select * into member from public.memberships where user_id = new.user_id for update;
  if not found or member.status <> 'active' or member.starts_at > now() or member.expires_at <= now() then
    raise exception 'active membership required' using errcode = '42501';
  end if;

  if tg_table_name = 'ai_usage' and new.status = 'completed' then
    select count(*) into used_count from public.ai_usage
      where user_id = new.user_id and usage_date = current_date and status = 'completed';
    if used_count >= member.ai_quota then
      raise exception 'AI quota exhausted' using errcode = '42501';
    end if;
  elsif tg_table_name = 'backtest_runs' and new.status = 'completed' then
    select count(*) into used_count from public.backtest_runs
      where user_id = new.user_id and created_at >= date_trunc('day', now()) and status = 'completed';
    if used_count >= member.backtest_quota then
      raise exception 'backtest quota exhausted' using errcode = '42501';
    end if;
  end if;
  return new;
end;
$$;

create trigger on_auth_user_created after insert on auth.users
for each row execute function public.handle_new_user();

create trigger profiles_updated before update on public.profiles for each row execute function public.set_updated_at();
create trigger memberships_updated before update on public.memberships for each row execute function public.set_updated_at();
create trigger strategies_updated before update on public.strategies for each row execute function public.set_updated_at();
create trigger posts_updated before update on public.posts for each row execute function public.set_updated_at();
create trigger comments_updated before update on public.comments for each row execute function public.set_updated_at();
create trigger ai_usage_quota before insert on public.ai_usage for each row execute function public.enforce_feature_quota();
create trigger backtest_runs_quota before insert on public.backtest_runs for each row execute function public.enforce_feature_quota();

alter table public.profiles enable row level security;
alter table public.memberships enable row level security;
alter table public.watchlists enable row level security;
alter table public.watchlist_items enable row level security;
alter table public.strategies enable row level security;
alter table public.strategy_versions enable row level security;
alter table public.backtest_runs enable row level security;
alter table public.signals enable row level security;
alter table public.posts enable row level security;
alter table public.follows enable row level security;
alter table public.likes enable row level security;
alter table public.comments enable row level security;
alter table public.notifications enable row level security;
alter table public.ai_usage enable row level security;
alter table public.admin_audit_logs enable row level security;

create policy "profiles readable by signed-in users" on public.profiles for select to authenticated using (true);
create policy "users update own profile" on public.profiles for update to authenticated using (auth.uid() = id) with check (auth.uid() = id);
revoke update on public.profiles from authenticated;
grant update (display_name, avatar_url, bio) on public.profiles to authenticated;
create policy "users read own membership" on public.memberships for select to authenticated using (auth.uid() = user_id);
create policy "admins manage memberships" on public.memberships for all to authenticated using (public.current_user_is_admin()) with check (public.current_user_is_admin());

create policy "active membership required" on public.watchlists as restrictive for all to authenticated using (public.current_user_has_active_membership()) with check (public.current_user_has_active_membership());
create policy "active membership required" on public.watchlist_items as restrictive for all to authenticated using (public.current_user_has_active_membership()) with check (public.current_user_has_active_membership());
create policy "active membership required" on public.strategies as restrictive for all to authenticated using (public.current_user_has_active_membership()) with check (public.current_user_has_active_membership());
create policy "active membership required" on public.strategy_versions as restrictive for all to authenticated using (public.current_user_has_active_membership()) with check (public.current_user_has_active_membership());
create policy "active membership required" on public.backtest_runs as restrictive for all to authenticated using (public.current_user_has_active_membership()) with check (public.current_user_has_active_membership());
create policy "active membership required" on public.signals as restrictive for all to authenticated using (public.current_user_has_active_membership()) with check (public.current_user_has_active_membership());
create policy "active membership required" on public.posts as restrictive for all to authenticated using (public.current_user_has_active_membership()) with check (public.current_user_has_active_membership());
create policy "active membership required" on public.follows as restrictive for all to authenticated using (public.current_user_has_active_membership()) with check (public.current_user_has_active_membership());
create policy "active membership required" on public.likes as restrictive for all to authenticated using (public.current_user_has_active_membership()) with check (public.current_user_has_active_membership());
create policy "active membership required" on public.comments as restrictive for all to authenticated using (public.current_user_has_active_membership()) with check (public.current_user_has_active_membership());
create policy "active membership required" on public.notifications as restrictive for all to authenticated using (public.current_user_has_active_membership()) with check (public.current_user_has_active_membership());
create policy "active membership required" on public.ai_usage as restrictive for all to authenticated using (public.current_user_has_active_membership()) with check (public.current_user_has_active_membership());

create policy "users manage own watchlists" on public.watchlists for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users manage own watchlist items" on public.watchlist_items for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "owners and public read strategies" on public.strategies for select to authenticated using (auth.uid() = user_id or visibility = 'public');
create policy "owners insert strategies" on public.strategies for insert to authenticated with check (auth.uid() = user_id);
create policy "owners update strategies" on public.strategies for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owners delete strategies" on public.strategies for delete to authenticated using (auth.uid() = user_id);
create policy "owners manage strategy versions" on public.strategy_versions for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "users manage own backtests" on public.backtest_runs for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "signals visible for owned or public strategies" on public.signals for select to authenticated using (
  exists (select 1 from public.strategies s where s.id = strategy_id and (s.user_id = auth.uid() or s.visibility = 'public'))
);

create policy "public or owner reads posts" on public.posts for select to authenticated using (is_public or auth.uid() = user_id);
create policy "users insert own posts" on public.posts for insert to authenticated with check (auth.uid() = user_id);
create policy "users update own posts" on public.posts for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users delete own posts" on public.posts for delete to authenticated using (auth.uid() = user_id);

create policy "follows visible to signed-in users" on public.follows for select to authenticated using (true);
create policy "users manage own follows" on public.follows for all to authenticated using (auth.uid() = follower_id) with check (auth.uid() = follower_id);
create policy "likes visible to signed-in users" on public.likes for select to authenticated using (true);
create policy "users manage own likes" on public.likes for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "comments on public posts readable" on public.comments for select to authenticated using (
  exists (select 1 from public.posts p where p.id = post_id and (p.is_public or p.user_id = auth.uid()))
);
create policy "users insert own comments" on public.comments for insert to authenticated with check (auth.uid() = user_id);
create policy "users update own comments" on public.comments for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users delete own comments" on public.comments for delete to authenticated using (auth.uid() = user_id);

create policy "users manage own notifications" on public.notifications for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users read own ai usage" on public.ai_usage for select to authenticated using (auth.uid() = user_id);
create policy "admins read ai usage" on public.ai_usage for select to authenticated using (public.current_user_is_admin());
create policy "admins read audit log" on public.admin_audit_logs for select to authenticated using (public.current_user_is_admin());

revoke all on public.memberships, public.ai_usage, public.notifications, public.admin_audit_logs from anon;
