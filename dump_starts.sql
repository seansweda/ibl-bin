\a
\t
\f ,
\o dump
select split_part(tig_name, ' ', 1), split_part(tig_name, ' ', 2), g, gs, c, b1, b2, b3, ss, lf, cf, rf, 0, case when vl > 0 then btrim(vl,' ') else 'NULL' end, case when vr > 0 then btrim(vr,' ') else 'NULL' end, 'NULL', 'NULL', 'NULL' from starts_limits_data;
-- copy starts2006 from '/tmp/dump' with delimiter ',' null as 'NULL';
