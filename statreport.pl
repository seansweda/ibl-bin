#!/usr/bin/perl
#
# $Id$

# flags
# -t: team totals
# -h: home stats
# -a: away stats

$host = 'phantasm.ibl.org';
$dbname = ibl_stats;
$username = 'stats';
$password = 'st@ts=Fun';

$startsdb = starts2005;
$batdb = bat2005;
$pitdb = pit2005;
$teamdb = teams2005;
$scheddb = sched2005;

$totals = 0;
$home = 0;
$away = 0;

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
	$home = 1;
	shift @ARGV;
    }
    elsif ( $ARGV[0] eq '-a' ) {
	$away = 1;
	shift @ARGV;
    }
    elsif ( length($ARGV[0]) == 3 ) {
    	push @teams, shift @ARGV;
    }
    else {
	print "usage: statreport [-a | -h | -t] team1 team2 ...\n";
	exit(1);
    }
}

$dbh = DBI->connect("dbi:Pg:dbname=$dbname;host=$host", "$username", "$password");

if (!@teams) {
    $sth = $dbh->selectcol_arrayref("select ibl, name from $teamdb order by ibl;");
    @teams = @$sth;
}

@bat = @teams;
print "BATTING STATISTICS\n";
while (@bat) {
    $team = shift @bat;
    print "$team\t";
    $sth = $dbh->selectcol_arrayref("select name from $teamdb where ibl = '$team';");
    printf "%s\n", shift @$sth;
    print "MLB NAME            G  AB   R   H  BI  2B  3B  HR  BB  SO  SB  CS  AVG  OBP  SLG\n";
    $loop = $dbh->prepare("select mlb, trim(name), sum(g), sum(ab), sum(r), sum(h),
	    sum(bi), sum(d), sum(t), sum(hr), sum(bb), sum(k), sum(sb), sum(cs)
	    from $batdb group by ibl, mlb, name having ibl = ? order by mlb, name;");
    $loop->execute($team);
    while ( @line = $loop->fetchrow_array ) {
	( $mlb, $name, $gp, $ab, $r, $h, $bi, $d, $t, $hr, $bb, $k, $sb, $cs ) = @line;
	printf "%-3s %-13s %3i %3i %3i %3i %3i %3i %3i %3i %3i %3i %3i %3i %s %s %s\n",
	    $mlb, $name, $gp, $ab, $r, $h, $bi, $d, $t, $hr, $bb, $k, $sb, $cs,
	    ( $ab > 0 ) ? pconv( $h / $ab ) : pconv(0), 
	    ( $ab + $bb > 0 ) ? pconv (( $h + $bb ) / ( $ab + $bb )) : pconv(0),
	    ( $ab > 0 ) ? pconv (( $h + $d + $t * 2 + $hr * 3 ) / $ab ) : pconv(0);
    }
    print "\n";
}

@pit = @teams;
print "PITCHING STATISTICS\n";
while (@pit) {
    $team = shift @pit;
    print "$team\t";
    $sth = $dbh->selectcol_arrayref("select name from $teamdb where ibl = '$team';");
    printf "%s\n", shift @$sth;
    print "RTM NAME            W   L  PCT  SV   G  GS    IP   H   R  ER  HR  BB  SO    ERA\n";
    $loop = $dbh->prepare("select mlb, trim(name), sum(w), sum(l), sum(sv), sum(g),
	    sum(gs), sum(ip), sum(h), sum(r), sum(er), sum(hr), sum(bb), sum(so)
	    from $pitdb group by ibl, mlb, name having ibl = ? order by mlb, name;");
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

