#!/usr/bin/perl
#
# $Id$

use FindBin;
do "$FindBin::Bin/DBconfig.pl";
do "$FindBin::Bin/DBpasswd.pl";

# initialize variables
$week = 0;
$home = '';
$away = '';

use DBI;

sub iblcode {
    my $team = shift;
    @s = $dbh->selectrow_array("
	    select code from $teamdb where ibl = '$team';
	    ");
    return $s[0];
}

sub gamescode {
    my $team = shift;
    @s = $dbh->selectrow_array("
	    select id from franchises where nickname = '$team';
	    ");
    return $s[0];
}

while (@ARGV) {
    if ( $ARGV[0] eq '-w' ) {
	shift @ARGV;
	$week = shift @ARGV;
    }
    elsif ( $ARGV[0] eq '-h' ) {
	shift @ARGV;
	$home = shift @ARGV;
	$home =~ tr/a-z/A-Z/;
    }
    elsif ( $ARGV[0] eq '-a' ) {
	shift @ARGV;
	$away = shift @ARGV;
	$away =~ tr/a-z/A-Z/;
    }
    elsif ( $ARGV[0] eq '-y' ) {
	# override db
	shift @ARGV;
	$year = shift @ARGV;
	$startsdb = 'starts' . $year;
	$batdb = 'bat' . $year;
	$pitdb = 'pit' . $year;
	$teamdb = 'teams' . $year;
	$scheddb = 'sched' . $year;
    }
    else {
	print "usage: purgegrs [-h home | -a away | -w week ]\n";
	exit(1);
    }
}

$dbh = DBI->connect("dbi:Pg:dbname=$dbname;host=$host", "$username", "$password");

if ( $week && $home && $away ) {
    print "removing week $week, $away @ $home\n";
    $hcode = iblcode($home);
    $acode = iblcode($away);
    $hgame = gamescode($home);
    $agame = gamescode($away);
    $dbh->do("
	update $scheddb set status = 0, scores = 0, inj = 0 where
	week = $week and home = '$hcode' and away = '$acode';
	");
    $dbh->do("
        delete from games where
        week = $week and
        home_team_id = $hgame and
        away_team_id = $agame;
        ");
    $dbh->do("
	delete from $startsdb where
	week = $week and home = '$home' and away = '$away';
	");
    $dbh->do("
	delete from $batdb where
	week = $week and home = '$home' and away = '$away';
	");
    $dbh->do("
	delete from $pitdb where
	week = $week and home = '$home' and away = '$away';
	");
    $dbh->do("
	delete from $extradb where
	week = $week and home = '$home' and away = '$away';
	");
    $redo = 0;
}

$dbh->disconnect;

