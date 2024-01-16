# newdb.sh {year} > /tmp/newdb.sql
eval pg_dump -s -t \'\*$(( ${1} - 1 ))\' ibl_stats | sed -e "s/$(( ${1} - 1 ))/${1}/g" 
