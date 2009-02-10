#!/usr/bin/perl

# flags
# -a: active roster
# -i: inactive roster
# -p: picks
# -f: find player

$host = 'phantasm.ibl.org';
$dbname = ibl_stats;
$username = 'iblwww';
$password = 'l1dstr0m';

use DBI;

$dbh = DBI->connect("dbi:Pg:dbname=$dbname;host=$host", "$username", "$password");

$loop = $dbh->prepare("select tig_name, comments, status, item_type
	    from teams where ibl_team = ? and item_type > 0 
	    order by item_type, tig_name;");

if ( $#ARGV == -1 ) {
    @ARGV = ( "BOW", "BUF", "BUZ", "CAJ", "COL", "COU", "CSP", "DTR", "GAS", "HAG", "LAW", "MAD", "MCM", "MIN", "PAD", "PHI", "POR", "SCS", "SDQ", "SEA", "SPO", "STL", "TRI", "WMS" );
}

while (@ARGV) {
    if ( $last > 0 ) {
	$last = 0;
	printf "\n";
    }

    $team = shift @ARGV;
    if ( $team eq '-a' ) {
	$loop = $dbh->prepare("select tig_name, comments, status, item_type
		    from teams where ibl_team = ? and item_type > 0 
		    and status = 1 order by item_type, tig_name;");
	next;
    }
    elsif ( $team eq '-i' ) {
	$loop = $dbh->prepare("select tig_name, comments, status, item_type
		    from teams where ibl_team = ? and item_type > 0 
		    and status > 1 order by item_type, tig_name;");
	next;
    }
    elsif ( $team eq '-p' ) {
	$loop = $dbh->prepare("select tig_name, comments, status, item_type
		    from teams where ibl_team = ? and item_type = 0 
		    order by tig_name;");
	next;
    }
    elsif ( $team eq '-f' ) {
	$player = shift @ARGV;
	$loop = $dbh->prepare("select ibl_team, tig_name, comments, status
		    from teams where tig_name ~* ?");
	$loop->execute($player);
	while ( @line = $loop->fetchrow_array ) {
	    ( $team, $tigname, $how, $status ) = @line;
	    ( $mlb, $name ) = split /\s/, $tigname, 2;
	    $name =~ s/ *$//;
	    $how =~ s/ *$//;
	    printf "%s %-3s %-3s %-20s %-40s\n", 
		($status == 1) ? '*' : ' ', $team, $mlb, $name, $how;
	}
	$last = 1;
	next;
    }
    elsif ( $team eq '-c' ) {
	$cards = 1;
	next;
    }

    $team =~ tr/a-z/A-Z/;
    $loop->execute($team);
    while ( @line = $loop->fetchrow_array ) {
	( $tigname, $how, $status, $type ) = @line;
	( $mlb, $name ) = split /\s/, $tigname, 2;
	$name =~ s/ *$//;
	$how =~ s/ *$//;
	if ( $type > $last ) {
	    if ( $type == 1 ) { print "$team PITCHERS\n"; }
	    elsif ( $type == 2 ) { print "\n$team BATTERS\n"; }
	    $last = $type
	}
	if ( $cards ) {
	    printf "%-3s %-15s ", $mlb, $name;
	    if ( $type == 1 ) {
		open( CARD, "card -p $mlb.$name | grep -v ^Player | cut -c 54- |" );
	    }
	    elsif ( $type == 2 ) {
		open( CARD, "card -b $mlb.$name | grep -v ^Player | cut -c 50- |" );
	    }
	    while ( <CARD> ) {
		( $h, $ob, $xb, $pwr ) = split;
		printf "%4s%4s%4s%4s  .", $h, $ob, $xb, $pwr;
	    }
	    close( CARD );
	    print "\n";
	} else {
	    printf "%s %-3s %-20s %-40s\n", 
		($status == 1) ? '*' : ' ', $mlb, $name, $how;
	}
    }
}

QUIT:
$dbh->disconnect;