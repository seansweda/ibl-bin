#!/usr/bin/perl
#
# $Id$

# flags
#   -i: print start of season starts/limits

$host = 'phantasm.ibl.org';
$dbname = ibl_stats;
$username = 'stats';
$password = 'st@ts=Fun';

$startsdb = starts2005;
$batdb = bat2005;
$pitdb = pit2005;
$teamdb = teams2005;
$scheddb = sched2005;

$init = 0;

use DBI;

while (@ARGV) {
    if ( $ARGV[0] eq '-i' ) {
	# initial starts/limits
	$init = 1;
    }
    shift @ARGV;
}

$dbh = DBI->connect("dbi:Pg:dbname=$dbname;host=$host", "$username", "$password");

if ( $init ) {
    $sth = $dbh->prepare("select mlb, trim(name), sum(g), sum(p), sum(c), 
	    sum(\"1b\"), sum(\"2b\"), sum(\"3b\"), sum(ss), sum(lf), sum(cf),
	    sum(rf), sum(inj), nullif(sum(vl), 0), nullif(sum(vr), 0),
	    count(*), count(vl), count(vr) from $startsdb 
	    group by mlb, name, week having week is null
	    order by mlb asc, name asc;");
}
else {
    $sth = $dbh->prepare("select mlb, trim(name), sum(g), sum(p), sum(c), 
	    sum(\"1b\"), sum(\"2b\"), sum(\"3b\"), sum(ss), sum(lf), sum(cf),
	    sum(rf), sum(inj), nullif(sum(vl), 0), nullif(sum(vr), 0),
	    count(*), count(vl), count(vr) from $startsdb 
	    group by mlb, name order by mlb asc, name asc;");
}

$sth->execute;

print "RTM Name             GP  SP   C  1B  2B  3B  SS  LF  CF  RF INJ  vL  vR\n";

while ( @s = $sth->fetchrow_array ) {
    if ( $s[15] == $s[16] && !defined($s[13]) ) {
	$s[13] = 0;
    }
    if ( $s[15] == $s[17] && !defined($s[14]) ) {
	$s[14] = 0;
    }

    printf "%-3s ", shift @s;
    printf "%-15s ", shift @s;
    for $i ( 1 .. 11 ) {
	printf "%3i ", shift @s;
    }
    if ( defined($s[0]) ) {
	printf "%3i ", shift @s;
    }
    else {
	printf " -- ";
	shift @s;
    }
    if ( defined($s[0]) ) {
	printf "%3i ", shift @s;
    }
    else {
	printf " -- ";
	shift @s;
    }
    printf "\n";
}

$dbh->disconnect;

