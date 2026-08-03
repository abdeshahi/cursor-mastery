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

drop policy if exists "Authenticated staff can view profiles" on public.profiles;
create policy "Authenticated staff can view profiles"
on public.profiles for select
to authenticated
using (true);

drop policy if exists "Authenticated staff can view store data" on public.store_data;
create policy "Authenticated staff can view store data"
on public.store_data for select
to authenticated
using (true);

create or replace function public.current_user_role()
returns text
language sql
stable
security definer
set search_path = ''
as $$
  select role from public.profiles where id = auth.uid()
$$;

revoke all on function public.current_user_role() from public;
grant execute on function public.current_user_role() to authenticated;

drop policy if exists "Authenticated staff can insert store data" on public.store_data;
drop policy if exists "Authenticated staff can update store data" on public.store_data;
drop policy if exists "Authorized staff can insert store data" on public.store_data;
drop policy if exists "Authorized staff can update store data" on public.store_data;

create policy "Authorized staff can insert store data"
on public.store_data for insert
to authenticated
with check (
  auth.uid() = updated_by
  and (
    public.current_user_role() = 'admin'
    or (public.current_user_role() = 'sales' and key in ('cttel-products', 'cttel-sales', 'cttel-customers'))
    or (public.current_user_role() = 'technician' and key = 'cttel-repairs')
  )
);

create policy "Authorized staff can update store data"
on public.store_data for update
to authenticated
using (
  public.current_user_role() = 'admin'
  or (public.current_user_role() = 'sales' and key in ('cttel-products', 'cttel-sales', 'cttel-customers'))
  or (public.current_user_role() = 'technician' and key = 'cttel-repairs')
)
with check (
  auth.uid() = updated_by
  and (
    public.current_user_role() = 'admin'
    or (public.current_user_role() = 'sales' and key in ('cttel-products', 'cttel-sales', 'cttel-customers'))
    or (public.current_user_role() = 'technician' and key = 'cttel-repairs')
  )
);

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
