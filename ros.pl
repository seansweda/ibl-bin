#!/usr/bin/perl

# flags
# -a: active roster
# -i: inactive roster
# -n: number of players
# -p: picks
# -f: find player
# -B: batters only
# -P: batters only
# -A: all teams
# -L: page breaks 

$username = 'ibl';
$dbname = ibl_stats;

$dobat = 1;
$dopit = 1;
$eol = '';

use DBI;

$dbh = DBI->connect("dbi:Pg:dbname=$dbname", "$username");

$loop = $dbh->prepare("select tig_name, comments, status, item_type
	    from teams where ibl_team = ? and item_type > 0 
	    order by item_type, tig_name;");

while (@ARGV) {
    if ( $last > 0 ) {
	$last = 0;
	printf "$eol\n";
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
    elsif ( $team eq '-n' ) {
	$num = 1;
	next;
    }
    elsif ( $team eq '-B' ) {
	$dopit = 0;
	next;
    }
    elsif ( $team eq '-P' ) {
	$dobat = 0;
	next;
    }
    elsif ( $team eq '-L' ) {
	$eol = '';
	next;
    }
    elsif ( $team eq '-A' ) {
	$allteams = $dbh->selectcol_arrayref("select distinct(ibl_team) from teams where ibl_team != 'FA';");
	push @ARGV, sort @$allteams;
	next;
    }

    $team =~ tr/a-z/A-Z/;
    $bnum = $pnum = 0;
    $count = $loop->execute($team);
    while ( @line = $loop->fetchrow_array ) {
	( $tigname, $how, $status, $type ) = @line;
	( $mlb, $name ) = split /\s/, $tigname, 2;
	$name =~ s/ *$//;
	$how =~ s/ *$//;
	if ( $type > $last ) {
	    if ( $type == 1 && $dobat && $dopit ) { print "$team PITCHERS\n"; }
	    elsif ( $type == 2 && $dobat && $dopit ) { print "\n$team BATTERS\n"; }
	    $last = $type;
	}
	if ( $cards ) {
	    if ( $type == 1 && $dopit || $type == 2 && $dobat ) {
		printf "%-3s %-15s ", $mlb, $name;
		( $pname = $name ) =~ s/'/\./g;
		if ( $type == 1 ) {
		    open( CARD, "card -wp $mlb.$pname | grep -v ^Player | cut -c 54- |" );
		}
		elsif ( $type == 2 ) {
		    open( CARD, "card -wb $mlb.$pname | grep -v ^Player | cut -c 50- |" );
		}
		while ( <CARD> ) {
		    ( $h, $ob, $xb, $pwr ) = split;
		    printf "%4s%4s%4s%4s  .", $h, $ob, $xb, $pwr;
		}
		close( CARD );
		print "\n";
	    }
	} else {
	    if ( $type == 0 || $type == 1 && $dopit || $type == 2 && $dobat ) {
		printf "%s %-3s %-20s %-40s\n", 
		    ($status == 1) ? '*' : ' ', $mlb, $name, $how;
	    }
	}
	if ( $type == 1 ) { $pnum++; }
	elsif ( $type == 2 ) { $bnum++; }
    }
    if ( $num == 1 && $count > 0 ) {
	print "$team players: $count ($pnum pitchers, $bnum batters)\n";
    }
}

QUIT:
$dbh->disconnect;