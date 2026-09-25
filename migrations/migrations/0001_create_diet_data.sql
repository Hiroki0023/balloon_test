-- ダイエット応援アプリ: 設定と日々の体重を保存するテーブル（設計.md D-01 / D-03）。
-- Supabase の SQL Editor で 1 回だけ実行する。

create table public.diet_data (
  type       text        not null check (type in ('setting', 'log')),
  key        text        not null,
  value      text        not null,
  updated_at timestamptz not null default now(),
  primary key (type, key),
  constraint diet_data_log_format check (
    type <> 'log' or (
      key ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
      and case
            when value ~ '^[0-9]{2,3}(\.[0-9])?$'
            then value::numeric between 20 and 200
            else false
          end
    )
  )
);

-- 既定で全拒否にする。anon / authenticated は Data API から何も読み書きできない。
alter table public.diet_data enable row level security;
revoke all on table public.diet_data from anon, authenticated;
grant select, insert, update, delete on table public.diet_data to service_role;
