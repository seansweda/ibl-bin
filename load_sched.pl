#!/usr/bin/perl
#
# $Id$

use FindBin;
do "$FindBin::Bin/DBconfig.pl";
do "$FindBin::Bin/DBpasswd.pl";

use DBI;
$dbh = DBI->connect("dbi:Pg:dbname=$dbname;host=$host", "$username", "$password");

sub code {
    $lg = shift;
    $num = shift;
    if ( $num < 10 ) {
	return( $lg . '0' . $num );
    } else {
	return( $lg . $num );
    }
}

while ( <> ) {
    chomp;
    if ( $_ =~ /^#/ ) { next; }
    @row = split;
    $week = shift @row;
    print "week $week\n";
    $home = 1;
    for $away ( @row ) {
	printf "%s @ %s\n", code( '', $away ), code ( '', $home);
	for $lg ( 'a', 'n' ) {
	    $sth = $dbh->prepare( "insert into $scheddb values ( $week, ?, ?, 0 );" );
	    $sth->execute( code( $lg, $home ), code( $lg, $away) );
	}
	$home++;
    }
    print "-------\n";
}

$dbh->disconnect;

