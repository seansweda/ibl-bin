#!/usr/local/bin/perl
#
# $Id$

$host = 'localhost';
$dbname = ibl_stats;
$username = tig;
$password = p1aZZa;

$startsdb = starts2004;

# constants
$BCOLS = 17;
$PCOLS = 10;
$SCOLS = 4;
$ICOLS = 5;

# initialize variables
$batters = 0;
$pitchers = 0;
$starts = 0;
$injuries = 0;
$wins = 0;
$losses = 0;
$lines = 0;

use DBI;

$dbh = DBI->connect("dbi:Pg:dbname=$dbname;host=$host", "$username", "$password", {AutoCommit => 0});

sub find {
    $mlb = shift;
    $name = shift;
    $where = shift;
    @s = $dbh->selectrow_array("select * from $startsdb 
    		where mlb = '$mlb' and trim(name) ~* '\^$name\$';");
    if ($#s == -1 ) {
	printf("%-3s %s line %s not found, perhaps:\n", $mlb, $name, $where);
	$loop = $dbh->prepare("select mlb, name from $startsdb
		where name ~* ? order by mlb, name desc;");
	$loop->execute($name);
	while ( @f = $loop->fetchrow_array ) {
	    printf("%-3s %s\n", $f[0], $f[1]);
	}
    }
    return @s;
}

while (<>) {

    $lines++;
    $keyword = (split)[0];
    $team = (split)[1];
    $keyword =~ tr/a-z/A-Z/;
    $team =~ tr/a-z/A-Z/;

    if ( $keyword eq 'BATTERS' ) {
	$batters++;
	$order = 1;
	$start = 0;
	$sc = $s1b = $s2b = $s3b = $sss = $slf = $scf = $srf = 0;
	while (<>) {
	    $lines++;
	    @line = split;
	    if ( $#line == -1 ) {
		last;
	    }
	    elsif ( $#line != $BCOLS ) {
		print "BATTERS format error, line $lines\n";
	    }
	    else {
		( $slot, $pos, $ibl, $mlb, $name, $ab, $r, $h, $bi, $d, $t, $hr, $sb, $cs, $bb, $k, $pl, $pr ) = @line;
		@starts = find( $mlb, $name, $lines);
		if ( @starts ) {
		    if ( $starts[2] == 0 ) {
			printf("%-3s %s illegal appearance, line %s\n", $mlb, $name, $lines);
		    }
		    if ( defined($starts[13]) ) {
			if ( $pl > 0 && $starts[13] == 0 ) {
			    printf("%-3s %s illegal PA vLHP, line %s\n", $mlb, $name, $lines);
			}
		    }
		    if ( defined($starts[14]) ) {
			if ( $pr > 0 && $starts[14] == 0 ) {
			    printf("%-3s %s illegal PA vRHP, line %s\n", $mlb, $name, $lines);
			}
		    }
		}

		$pos =~ tr/A-Z/a-z/;
		$pos =~ s/\-.*$//;
		if ($order == $slot) {
		    $start = 1;
		    $order++;
		}
		else {
		    $start = 0;
		}
		if ( $start && @starts ) {
		    #printf("%-3s %s start @ %s\n", $mlb, $name, $pos);
		    if ( $pos eq 'c' ) {
			if ( $starts[4] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    $sc = 1;
			}
		    }
		    elsif ( $pos eq '1b' ) {
			if ( $starts[5] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    $s1b = 1;
			}
		    }
		    elsif ( $pos eq '2b' ) {
			if ( $starts[6] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    $s2b = 1;
			}
		    }
		    elsif ( $pos eq '3b' ) {
			if ( $starts[7] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    $s3b = 1;
			}
		    }
		    elsif ( $pos eq 'ss' ) {
			if ( $starts[8] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    $sss = 1;
			}
		    }
		    elsif ( $pos eq 'lf' ) {
			if ( $starts[9] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    $slf = 1;
			}
		    }
		    elsif ( $pos eq 'cf' ) {
			if ( $starts[10] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    $scf = 1;
			}
		    }
		    elsif ( $pos eq 'rf' ) {
			if ( $starts[11] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    $srf = 1;
			}
		    }
		}
	    }
	}
	
	if ( !($sc && $s1b && $s2b && $s3b && $sss && $slf && $scf && $srf) ) {
	    print "$team line $lines missing starters: ";
	    if ( $sc == 0 ) {
		print "c ";
	    }
	    if ( $s1b == 0 ) {
		print "1b ";
	    }
	    if ( $s2b == 0 ) {
		print "2b ";
	    }
	    if ( $s3b == 0 ) {
		print "3b ";
	    }
	    if ( $sss == 0 ) {
		print "ss ";
	    }
	    if ( $slf == 0 ) {
		print "lf ";
	    }
	    if ( $scf == 0 ) {
		print "cf ";
	    }
	    if ( $srf == 0 ) {
		print "rf ";
	    }
	    print "\n";
	}
    }

    elsif ( $keyword eq 'PITCHERS') {
	$pitchers++;
	$w = $l = $s = 0;
	$start = 1;
	while (<>) {
	    $lines++;
	    @line = split;
	    if ( $#line == -1 ) {
		last;
	    }
	    elsif ( $#line != $PCOLS ) {
		print "PITCHERS format error, line $lines\n";
	    }
	    else {
		( $dec, $ibl, $mlb, $name, $ip, $h, $r, $er, $bb, $k, $hr ) = @line;
		@starts = find( $mlb, $name, $lines);
		if ( @starts && $starts[2] == 0) {
		    printf("%-3s %s illegal appearance, line %s\n", $mlb, $name, $lines);
		}
		$dec =~ tr/a-z/A-Z/;
		if ( @starts && $start ) {
		    if ( $starts[3] == 0 ) {
			printf("%-3s %s illegal start @ p, line %s\n", $mlb, $name, $lines);
		    }
		    $start = 0;
		}
		if ( $dec eq 'W' ) {
		    $wins++;
		    $w = 1;
		}
		elsif ( $dec eq 'L' ) {
		    $losses++;
		    $l = 1;
		}
		elsif ( $dec eq 'S' ) {
		    $s = 1;
		}
	    }
	}
    }
    
    elsif ( $keyword eq 'STARTS' ) {
	print "STARTS\n";
	while (<>) {
	    $lines++;
	    @line = split;
	    if ( $#line == -1 ) {
		last;
	    }
	    elsif ( $#line < $SCOLS ) {
		print "STARTS format error, line $lines\n";
	    }
	    else {
		( $slot, $pos, $ibl, $mlb, $name ) = @line;
		@starts = find( $mlb, $name, $lines);
		$pos =~ tr/A-Z/a-z/;
		$pos =~ s/\-.*$//;
		if ( @starts ) {
		    if ( $pos eq 'c' ) {
			if ( $starts[4] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			}
		    }
		    elsif ( $pos eq '1b' ) {
			if ( $starts[5] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			}
		    }
		    elsif ( $pos eq '2b' ) {
			if ( $starts[6] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			}
		    }
		    elsif ( $pos eq '3b' ) {
			if ( $starts[7] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			}
		    }
		    elsif ( $pos eq 'ss' ) {
			if ( $starts[8] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			}
		    }
		    elsif ( $pos eq 'lf' ) {
			if ( $starts[9] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			}
		    }
		    elsif ( $pos eq 'cf' ) {
			if ( $starts[10] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			}
		    }
		    elsif ( $pos eq 'rf' ) {
			if ( $starts[11] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			}
		    }
		}
	    }
	}
	print "\n";
    }

    elsif ( $keyword eq 'INJURIES' ) {
	print "INJURIES\n";
	while (<>) {
	    $lines++;
	    @line = split;
	    if ( $#line == -1 ) {
		last;
	    }
	    elsif ( $#line < $ICOLS ) {
		print "INJURIES format error, line $lines\n";
	    }
	    else {
		( $slot, $pos, $ibl, $mlb, $name, $inj ) = @line;
		@starts = find( $mlb, $name, $lines);

		if ( @starts ) {
		    printf("%-3s %s injured for %s day(s)\n", $mlb, $name, $inj);
		}
	    }
	}
	print "\n";
    }
}

print "\n";
printf ("lines: %s\n", $lines);
printf ("Total BATTERS: %s\n", $batters);
printf ("Total PITCHERS: %s\n", $pitchers);
printf ("Total WINS: %s\n", $wins);
printf ("Total LOSSES: %s\n", $losses);

