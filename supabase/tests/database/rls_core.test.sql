begin;
select plan(7);

select ok(not has_table_privilege('anon', 'public.events', 'SELECT'), 'anon cannot read events');
select ok(has_table_privilege('authenticated', 'public.events', 'SELECT'), 'authenticated can read events');
select ok(not has_table_privilege('authenticated', 'public.events', 'INSERT'), 'authenticated cannot insert events');
select ok(has_table_privilege('authenticated', 'public.raw_items', 'SELECT'), 'authenticated can read raw item metadata');
select ok(not has_table_privilege('authenticated', 'public.raw_item_payloads', 'SELECT'), 'authenticated cannot read raw payloads');
select ok(has_table_privilege('service_role', 'public.raw_item_payloads', 'SELECT'), 'service_role can read raw payloads');
select ok(has_table_privilege('service_role', 'public.raw_item_payloads', 'INSERT'), 'service_role can insert raw payloads');

select * from finish();
rollback;
