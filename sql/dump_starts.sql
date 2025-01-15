\a
\t
\f ,
\o dump
-- select split_part(tig_name, ' ', 1), replace(substring(tig_name from ' .*$'),' ','' ), g, gs, c, b1, b2, b3, ss, lf, cf, rf, 0, case when vl = '--' then 'NULL' else vl end, case when vr = '--' then 'NULL' else vr end, 'NULL', 'NULL', 'NULL' from starts_limits_data;
select split_part(tig_name, ' ', 1), replace(substring(tig_name from ' .*$'),' ','' ), g, gs, c, b1, b2, b3, ss, lf, cf, rf, 0, 'NULL', 'NULL', 'NULL', 'NULL', 'NULL' from starts_limits_data order by tig_name;
-- copy starts2006 from '/tmp/dump' with delimiter ',' null as 'NULL';
