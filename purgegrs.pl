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
    $flag = shift @ARGV;
    if ( $flag eq '-w' ) {
	$week = shift @ARGV;
    }
    if ( $flag eq '-h' ) {
	$home = shift @ARGV;
	$home =~ tr/a-z/A-Z/;
    }
    if ( $flag eq '-a' ) {
	$away = shift @ARGV;
	$away =~ tr/a-z/A-Z/;
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

