#!/usr/bin/perl
#
# $Id$

use FindBin;
do "$FindBin::Bin/DBconfig.pl";
$username = 'ibl';

use DBI;

$dbh = DBI->connect("dbi:Pg:dbname=$dbname", "$username");

if ( $week == 0 ) {
    @row = $dbh->selectrow_array("select max(week) from $scheddb where status=1;");
    print shift @row;
    print "\n";
}

$dbh->disconnect;

