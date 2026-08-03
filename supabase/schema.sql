-- Run this file once in Supabase Dashboard > SQL Editor.

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null default 'کاربر سی‌تی‌تل',
  role text not null default 'sales' check (role in ('admin', 'sales', 'technician')),
  created_at timestamptz not null default now()
);

create table if not exists public.store_data (
  key text primary key,
  payload jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now(),
  updated_by uuid references auth.users(id)
);

alter table public.profiles enable row level security;
alter table public.store_data enable row level security;

create policy "Authenticated staff can view profiles"
on public.profiles for select
to authenticated
using (true);

create policy "Authenticated staff can view store data"
on public.store_data for select
to authenticated
using (true);

create policy "Authenticated staff can insert store data"
on public.store_data for insert
to authenticated
with check (auth.uid() = updated_by);

create policy "Authenticated staff can update store data"
on public.store_data for update
to authenticated
using (true)
with check (auth.uid() = updated_by);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = ''
as $$
begin
  insert into public.profiles (id, full_name, role)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'full_name', split_part(new.email, '@', 1)),
    coalesce(new.raw_app_meta_data ->> 'role', 'sales')
  );
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

do $$
begin
  if not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'store_data'
  ) then
    alter publication supabase_realtime add table public.store_data;
  end if;
end
$$;
