#!/usr/bin/perl
#
# $Id$

use FindBin;
do "$FindBin::Bin/DBconfig.pl";

# initialize variables
$week = 0;
$home = '';
$away = '';

use DBI;

sub iblcode {
    $team = shift;
    @s = $dbh->selectrow_array("select code from $teamdb where ibl = '$team';");
    return @s;
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
    @hcode = iblcode($home);
    @acode = iblcode($away);
    $dbh->do( "update $scheddb set status = 0 where
	    week = $week and home = '$hcode[0]' and away = '$acode[0]';");
    $dbh->do( "delete from $startsdb where
	    week = $week and home = '$home' and away = '$away';");
    $dbh->do( "delete from $batdb where
	    week = $week and home = '$home' and away = '$away';");
    $dbh->do( "delete from $pitdb where
	    week = $week and home = '$home' and away = '$away';");
    $redo = 0;
}

$dbh->disconnect;

