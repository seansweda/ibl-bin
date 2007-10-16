#!/usr/bin/perl
#
# $Id$

# flags
# -b: batters
# -p: pitchers
# -w: through week #

use FindBin;
do "$FindBin::Bin/DBconfig.pl";
$username = 'ibl';

$batters = 0;
$pitchers = 0;
$week = 27;

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
    if ( $ARGV[0] eq '-b' ) {
	if ( $pitchers ) {
	    print "usage: usagereport [-b | -p ] [ -w ]\n";
	    exit(1);
	}
	$batters = 1;
	shift @ARGV;
    }
    elsif ( $ARGV[0] eq '-p' ) {
	if ( $batters ) {
	    print "usage: usagereport [-b | -p ] [ -w ]\n";
	    exit(1);
	}
	$pitchers = 1;
	shift @ARGV;
    }
    elsif ( $ARGV[0] eq '-w' ) {
	shift @ARGV;
	$week = shift @ARGV;
    }
    else {
	print "usage: usagereport [-b | -p ] [ -w ]\n";
	exit(1);
    }
}

$dbh = DBI->connect("dbi:Pg:dbname=$dbname", "$username");

if ( $batters ) {
    $loop = $dbh->prepare("select mlb, trim(name), sum(g), sum(ab), sum(r), sum(h),
	    sum(bi), sum(d), sum(t), sum(hr), sum(bb), sum(k), sum(sb), sum(cs)
	    from $batdb where week <= $week group by mlb, name order by mlb, name;");
    $loop->execute();
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
elsif ( $pitchers ) {
    $loop = $dbh->prepare("select mlb, trim(name), sum(w), sum(l), sum(sv), sum(g),
	    sum(gs), sum(ip), sum(h), sum(r), sum(er), sum(hr), sum(bb), sum(so)
	    from $pitdb where week <= $week group by mlb, name order by mlb, name;");
    $loop->execute();
    while ( @line = $loop->fetchrow_array ) {
	( $mlb, $name, $w, $l, $sv, $g, $gs, $ip, $h, $r, $er, $hr, $bb, $so ) = @line;
	printf "%-3s %-13s %3i %3i %s %3i %3i %3i %5s %3i %3i %3i %3i %3i %3i %6.2f\n",
	    $mlb, $name, $w, $l, 
	    ( $w + $l > 0 ) ? pconv( $w / ( $w + $l )) : pconv(0),
	    $sv, $g, $gs, $ip, $h, $r, $er, $hr, $bb, $so,
	    ( $ip > 0 ) ? $er * 9 / $ip * 3 : 999.99;
    }
    print "\n";
}
