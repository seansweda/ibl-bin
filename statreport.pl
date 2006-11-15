#!/usr/bin/perl
#
# $Id$

# flags
# -t: team totals
# -h: home stats
# -a: away stats
# -w: through week #

use FindBin;
do "$FindBin::Bin/DBconfig.pl";

$totals = 0;
$home = 0;
$away = 0;
$week = 27;
$groupby = "ibl";
$split = "";
$having = "";
$where = "";
$versus = "";

use DBI;

sub pconv {
    my $rate = shift;
    my $retval = '';
    if ( $rate < 1.0 ) {
	$retval = sprintf "%5.3f", $rate;
	$retval =~ s|^0||;
	return $retval;
    }
    else {
	$retval = sprintf "%4.2f", $rate;
	return $retval;
    }
}

sub ipconv {
    my $outs = shift;
    my $inn = int ( $outs / 3 );
    my $frac = $outs - ( $inn * 3);
    my $retval = sprintf "%s.%s", $inn, $frac;
    return $retval;
}

while (@ARGV) {
    if ( $ARGV[0] eq '-t' ) {
	$totals = 1;
	shift @ARGV;
    }
    elsif ( $ARGV[0] eq '-h' ) {
	if ( $away ) {
	    print "usage: statreport [-a | -h ] [ -t ] [ -v opponent ] (team1 team2 ...)\n";
	    exit(1);
	}
	$home = 1;
	$groupby = "ibl, home";
	$split = "ibl = home";
	shift @ARGV;
    }
    elsif ( $ARGV[0] eq '-a' ) {
	if ( $home ) {
	    print "usage: statreport [-a | -h ] [ -t ] [ -v opponent ] (team1 team2 ...)\n";
	    exit(1);
	}
	$away = 1;
	$groupby = "ibl, away";
	$split = "ibl = away";
	shift @ARGV;
    }
    elsif ( $ARGV[0] eq '-w' ) {
	shift @ARGV;
	$week = shift @ARGV;
    }
    elsif ( $ARGV[0] eq '-v' ) {
	if ( $versus ) {
	    print "usage: statreport [-a | -h ] [ -t ] [ -v opponent ] (team1 team2 ...)\n";
	    exit(1);
	}
	shift @ARGV;
	$versus = shift @ARGV;
	$versus =~ tr/a-z/A-Z/;
	$where = sprintf "(home = '%s' or away = '%s') and", $versus, $versus;
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
    elsif ( length($ARGV[0]) == 3 ) {
    	push @teams, shift @ARGV;
    }
    else {
	print "usage: statreport [-a | -h ] [ -t ] [ -v opponent ] (team1 team2 ...)\n";
	exit(1);
    }
}

$dbh = DBI->connect("dbi:Pg:dbname=$dbname;host=$host", "$username", "$password");

if ( $totals ) {
    if ( @teams ) {
	print "-t does all teams\n";
	exit(1);
    }
    else {
	if ( $split ) {
	    $having = "having " . $split;
	    $where = $split . " and ";
	}
	if ( $home ) {
	    print "HOME\n";
	}
	if ( $away ) {
	    print "AWAY\n";
	}
	print "BATTING STATISTICS\n";
	print "IBL     AB    R    H   BI  2B  3B  HR   BB   SO  SB  CS   AVG  OBP  SLG\n";
	$loop = $dbh->prepare("select ibl, sum(ab), sum(r), sum(h), sum(bi),
		sum(d), sum(t), sum(hr), sum(bb), sum(k), sum(sb), sum(cs)
		from $batdb where week <= $week group by $groupby $having 
		order by sum(r) desc;");
	$loop->execute;
	while ( @line = $loop->fetchrow_array ) {
	    ( $ibl, $ab, $r, $h, $bi, $d, $t, $hr, $bb, $k, $sb, $cs ) = @line;
	    printf "%-5s %4i %4i %4i %4i %3i %3i %3i %4i %4i %3i %3i  %s %s %s\n",
		$ibl, $ab, $r, $h, $bi, $d, $t, $hr, $bb, $k, $sb, $cs,
		( $ab > 0 ) ? pconv( $h / $ab ) : pconv(0), 
		( $ab + $bb > 0 ) ? pconv (( $h + $bb ) / ( $ab + $bb )) : pconv(0),
		( $ab > 0 ) ? pconv (( $h + $d + $t * 2 + $hr * 3 ) / $ab ) : pconv(0);
	}
	@line = $dbh->selectrow_array("select sum(ab), sum(r), sum(h), sum(bi),
		sum(d), sum(t), sum(hr), sum(bb), sum(k), sum(sb), sum(cs)
		from $batdb where $where week <= $week;");
	( $ab, $r, $h, $bi, $d, $t, $hr, $bb, $k, $sb, $cs ) = @line;
	printf "%-56s %s %s %s\n",
	    "AVG",
	    ( $ab > 0 ) ? pconv( $h / $ab ) : pconv(0), 
	    ( $ab + $bb > 0 ) ? pconv (( $h + $bb ) / ( $ab + $bb )) : pconv(0),
	    ( $ab > 0 ) ? pconv (( $h + $d + $t * 2 + $hr * 3 ) / $ab ) : pconv(0);
	print "\n";

	if ( $home ) {
	    print "HOME\n";
	}
	if ( $away ) {
	    print "AWAY\n";
	}
	print "PITCHING STATISTICS\n";
	print "IBL      G   W   L   PCT  SV     IP    H    R   ER  HR   BB   SO    ERA\n";
	$loop = $dbh->prepare("select ibl, sum(w), sum(l), sum(sv), sum(gs),
		sum(ip), sum(h), sum(r), sum(er), sum(hr), sum(bb), sum(so)
		from $pitdb where week <= $week group by $groupby $having 
		order by sum(r) asc;");
	$loop->execute;
	while ( @line = $loop->fetchrow_array ) {
	    ( $ibl, $w, $l, $sv, $gs, $ip, $h, $r, $er, $hr, $bb, $so ) = @line;
	    printf "%-6s %3i %3i %3i %5s %3i %6s %4i %4i %4i %3i %4i %4i %6.2f\n",
		$ibl, $gs, $w, $l, 
		( $w + $l > 0 ) ? pconv( $w / ( $w + $l )) : pconv(0),
		$sv, ipconv($ip), $h, $r, $er, $hr, $bb, $so,
		( $ip > 0 ) ? $er * 9 / $ip * 3 : 999.99;
	}
	@line = $dbh->selectrow_array("select sum(w), sum(l), sum(sv), sum(gs),
		sum(ip), sum(h), sum(r), sum(er), sum(hr), sum(bb), sum(so)
		from $pitdb where $where week <= $week;");
	( $w, $l, $sv, $gs, $ip, $h, $r, $er, $hr, $bb, $so ) = @line;
	printf "%-64s %6.2f\n",
	    "AVG", ( $ip > 0 ) ? $er * 9 / $ip * 3 : 999.99;
    }
}

else {
    if ( !@teams ) {
	$sth = $dbh->selectcol_arrayref("select ibl, name from $teamdb order by ibl;");
	@teams = @$sth;
    }

    if ( $split ) {
	$having = " and " . $split;
    }
    @bat = @teams;
    if ( $home ) {
	print "HOME\n";
    }
    if ( $away ) {
	print "AWAY\n";
    }
    if ( $versus) {
	print "vs $versus\n";
    }
    print "BATTING STATISTICS\n";
    while (@bat) {
	$team = shift @bat;
	$team =~ tr/a-z/A-Z/;
	print "$team\t";
	$sth = $dbh->selectcol_arrayref("select name from $teamdb where ibl = '$team';");
	printf "%s\n", shift @$sth;
	print "MLB NAME            G  AB   R   H  BI  2B  3B  HR  BB  SO  SB CS  AVG  OBP  SLG\n";
	$loop = $dbh->prepare("select mlb, trim(name), sum(g), sum(ab), sum(r), sum(h),
		sum(bi), sum(d), sum(t), sum(hr), sum(bb), sum(k), sum(sb), sum(cs)
		from $batdb where $where week <= $week group by $groupby, mlb, name
		having ibl = ? $having order by mlb, name;");
	$loop->execute($team);
	while ( @line = $loop->fetchrow_array ) {
	    ( $mlb, $name, $gp, $ab, $r, $h, $bi, $d, $t, $hr, $bb, $k, $sb, $cs ) = @line;
	    printf "%-3s %-13s %3i %3i %3i %3i %3i %3i %3i %3i %3i %3i %3i %2i %s %s %s\n",
		$mlb, $name, $gp, $ab, $r, $h, $bi, $d, $t, $hr, $bb, $k, $sb, $cs,
		( $ab > 0 ) ? pconv( $h / $ab ) : pconv(0), 
		( $ab + $bb > 0 ) ? pconv (( $h + $bb ) / ( $ab + $bb )) : pconv(0),
		( $ab > 0 ) ? pconv (( $h + $d + $t * 2 + $hr * 3 ) / $ab ) : pconv(0);
	}
	print "\n";
    }

    @pit = @teams;
    if ( $home ) {
	print "HOME\n";
    }
    if ( $away ) {
	print "AWAY\n";
    }
    if ( $versus) {
	print "vs $versus\n";
    }
    print "PITCHING STATISTICS\n";
    while (@pit) {
	$team = shift @pit;
	$team =~ tr/a-z/A-Z/;
	print "$team\t";
	$sth = $dbh->selectcol_arrayref("select name from $teamdb where ibl = '$team';");
	printf "%s\n", shift @$sth;
	print "MLB NAME            W   L  PCT  SV   G  GS    IP   H   R  ER  HR  BB  SO    ERA\n";
	$loop = $dbh->prepare("select mlb, trim(name), sum(w), sum(l), sum(sv), sum(g),
		sum(gs), sum(ip), sum(h), sum(r), sum(er), sum(hr), sum(bb), sum(so)
		from $pitdb where $where week <= $week group by $groupby, mlb, name 
		having ibl = ? $having order by mlb, name;");
	$loop->execute($team);
	while ( @line = $loop->fetchrow_array ) {
	    ( $mlb, $name, $w, $l, $sv, $g, $gs, $ip, $h, $r, $er, $hr, $bb, $so ) = @line;
	    printf "%-3s %-13s %3i %3i %s %3i %3i %3i %5s %3i %3i %3i %3i %3i %3i %6.2f\n",
		$mlb, $name, $w, $l, 
		( $w + $l > 0 ) ? pconv( $w / ( $w + $l )) : pconv(0),
		$sv, $g, $gs, ipconv($ip), $h, $r, $er, $hr, $bb, $so,
		( $ip > 0 ) ? $er * 9 / $ip * 3 : 999.99;
	}
	print "\n";
    }
}
