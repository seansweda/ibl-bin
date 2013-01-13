select case when is_batter = 'Y' then 'bat' else 'pit' end, sum(days) from dl d, players p where d.player_id = p.player_id and (is_batter = 'Y' or is_pitcher = 'Y') group by is_batter;
