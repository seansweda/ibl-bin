#!/usr/local/bin/perl
#
# $Id$

$host = 'localhost';
$dbname = ibl_stats;
$username = tig;
$password = p1aZZa;

$startsdb = starts2004;
$batdb = bat2004;
$pitdb = pit2004;

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
$errors = 0;
$week = 0;
$home = '';
$away = '';
$updates = 0;

use DBI;

if ( $#ARGV > 0 ) {
    if ( $ARGV[0] eq '-u' ) {
	shift @ARGV;
	$updates = 1;
    }
}

$dbh = DBI->connect("dbi:Pg:dbname=$dbname;host=$host", "$username", "$password", {AutoCommit => 0});

sub find {
    $mlb = shift;
    $name = shift;
    $where = shift;
    @s = $dbh->selectrow_array("select mlb, name, sum(g), sum(p), sum(c), 
    		sum(\"1b\"), sum(\"2b\"), sum(\"3b\"), sum(ss), sum(lf), sum(cf),
		sum(rf), sum(inj), nullif(sum(vl), 0), nullif(sum(vr), 0),
		count(*), count(vl), count(vr) from $startsdb 
    		where mlb = '$mlb' and trim(name) ~* '\^$name\$'
		group by mlb, name;");
    if ($#s == -1 ) {
	printf("%-3s %s line %s not found, perhaps:\n", $mlb, $name, $where);
	$loop = $dbh->prepare("select mlb, name from $startsdb
		where name ~* ? order by mlb, name desc;");
	$loop->execute($name);
	while ( @f = $loop->fetchrow_array ) {
	    printf("%-3s %s\n", $f[0], $f[1]);
	}
    }
    if ( $s[15] == $s[16] && !defined($s[13]) ) {
	$s[13] = 0;
    }
    if ( $s[15] == $s[17] && !defined($s[14]) ) {
	$s[14] = 0;
    }

    return @s;
}

sub outs {
    $ip = shift;
    $whole = int($ip);
    $thirds = ($ip - $whole) * 10;
    return ( $whole * 3 + $thirds );
}

while (<>) {

    $lines++;
    $keyword = (split)[0];

    if ( $keyword eq 'WEEK' ) {
	$week = (split)[1];
	if ( $week >= 1 && $week <= 27 ) {
	    print "WEEK: $week\n";
	}
	else {
	    print "WEEK format error: $week\n";
	    $errors++;
	    $week = '';
	}
    }
    elsif ( $keyword eq 'HOME' ) {
	$home = (split)[1];
	$home =~ tr/a-z/A-Z/;
	if ( length($home) == 2 || length($home) == 3 ) {
	    print "HOME: $home\n";
	}
	else {
	    print "HOME format error: $home\n";
	    $errors++;
	    $home = '';
	}
    }
    elsif ( $keyword eq 'AWAY' ) {
	$away = (split)[1];
	$away =~ tr/a-z/A-Z/;
	if ( length($away) == 2 || length($away) == 3 ) {
	    print "AWAY: $away\n";
	}
	else {
	    print "AWAY format error: $away\n";
	    $errors++;
	    $away = '';
	}
    }
    else {
	$team = (split)[1];
	$team =~ tr/a-z/A-Z/;
    }

    $keyword =~ tr/a-z/A-Z/;

    if ( $keyword eq 'BATTERS' ) {
	$batters++;
	$order = 1;
	$start = 0;
	$sc = $s1b = $s2b = $s3b = $sss = $slf = $scf = $srf = 0;
	while (<>) {
	    $g = $psc = $ps1b = $ps2b = $ps3b = $psss = $pslf = $pscf = $psrf = 0;
	    $lines++;
	    @line = split;
	    if ( $#line == -1 ) {
		last;
	    }
	    elsif ( $#line != $BCOLS ) {
		print "BATTERS format error, line $lines\n";
		$errors++;
	    }
	    else {
		( $slot, $pos, $ibl, $mlb, $name, $ab, $r, $h, $bi, $d, $t, $hr, $sb, $cs, $bb, $k, $pl, $pr ) = @line;
		@starts = find( $mlb, $name, $lines);
		if ( @starts ) {
		    if ( $starts[2] == 0 ) {
			printf("%-3s %s illegal appearance, line %s\n", $mlb, $name, $lines);
			$errors++;
		    }
		    if ( defined($starts[13]) ) {
			if ( $pl > 0 && $starts[13] < 1 ) {
			    printf("%-3s %s illegal PA vLHP, line %s\n", $mlb, $name, $lines);
			    $errors++;
			}
		    }
		    if ( defined($starts[14]) ) {
			if ( $pr > 0 && $starts[14] < 1 ) {
			    printf("%-3s %s illegal PA vRHP, line %s\n", $mlb, $name, $lines);
			    $errors++;
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
			    $errors++;
			}
			else {
			    $psc = $sc = -1;
			}
		    }
		    elsif ( $pos eq '1b' ) {
			if ( $starts[5] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    $ps1b = $s1b = -1;
			}
		    }
		    elsif ( $pos eq '2b' ) {
			if ( $starts[6] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    $ps2b = $s2b = -1;
			}
		    }
		    elsif ( $pos eq '3b' ) {
			if ( $starts[7] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    $ps3b = $s3b = -1;
			}
		    }
		    elsif ( $pos eq 'ss' ) {
			if ( $starts[8] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    $psss = $sss = -1;
			}
		    }
		    elsif ( $pos eq 'lf' ) {
			if ( $starts[9] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    $pslf = $slf = -1;
			}
		    }
		    elsif ( $pos eq 'cf' ) {
			if ( $starts[10] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    $pscf = $scf = -1;
			}
		    }
		    elsif ( $pos eq 'rf' ) {
			if ( $starts[11] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    $psrf = $srf = -1;
			}
		    }
		}
	    }

	    if ( $updates && $week && $home && $away ) {
		# assign pitcher games in PITCHERS block
		if ( $pos eq 'p' ) {
		    $g = 0;
		}
		else {
		    $g = -1;
		}
		if ( defined($starts[13]) ) {
		    $pl *= -1;
		}
		else {
		    $pl = 0;
		}
		if ( defined($starts[14]) ) {
		    $pr *= -1;
		}
		else {
		    $pr = 0;
		}

		$dbh->do( "insert into $batdb values ( $week, '$home', '$away', '$ibl', '$mlb', '$name', 1, $ab, $r, $h, $bi, $d, $t, $hr, $sb, $cs, $bb, $k );" );
		$dbh->do( "insert into $startsdb values ( '$mlb', '$name', $g, 0, $psc, $ps1b, $ps2b, $ps3b, $psss, $pslf, $pscf, $psrf, 0, $pl, $pr, $week, '$home', '$away' );" );
	    }
	    elsif ( $updates ) {
	    	$errors++;
	    }

	}
	
	if ( !($sc && $s1b && $s2b && $s3b && $sss && $slf && $scf && $srf) ) {
	    print "$team line $lines missing starters: ";
	    $errors++;
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
	}
    }

    elsif ( $keyword eq 'PITCHERS') {
	$pitchers++;
	$start = 1;
	while (<>) {
	    $pgs = $pw = $pl = $ps = 0;
	    $lines++;
	    @line = split;
	    if ( $#line == -1 ) {
		last;
	    }
	    elsif ( $#line != $PCOLS ) {
		print "PITCHERS format error, line $lines\n";
		$errors++;
	    }
	    else {
		( $dec, $ibl, $mlb, $name, $ip, $h, $r, $er, $bb, $k, $hr ) = @line;
		@starts = find( $mlb, $name, $lines);
		if ( @starts && $starts[2] == 0) {
		    printf("%-3s %s illegal appearance, line %s\n", $mlb, $name, $lines);
		    $errors++;
		}
		$dec =~ tr/a-z/A-Z/;
		if ( @starts && $start ) {
		    if ( $starts[3] == 0 ) {
			printf("%-3s %s illegal start @ p, line %s\n", $mlb, $name, $lines);
			$errors++;
		    }
		    $start = 0;
		    $pgs = 1;
		}
		if ( $dec eq 'W' ) {
		    $wins++;
		    $pw = 1;
		}
		elsif ( $dec eq 'L' ) {
		    $losses++;
		    $pl = 1;
		}
		elsif ( $dec eq 'S' ) {
		    $ps = 1;
		}
	    }

	    if ( $updates && $week && $home && $away ) {
		$ip = outs($ip);
		$dbh->do( "insert into $pitdb values ( $week, '$home', '$away', '$ibl', '$mlb', '$name', $pw, $pl, $ps, 1, $pgs, $ip, $h, $r, $er, $bb, $k, $hr );" );
		$dbh->do( "insert into $startsdb values ( '$mlb', '$name', 1, $pgs, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, $week, '$home', '$away' );" );
	    }
	    elsif ( $updates ) {
	    	$errors++;
	    }
	}
    }
    
    elsif ( $keyword eq 'STARTS' ) {
	#print "STARTS\n";
	while (<>) {
	    $psc = $ps1b = $ps2b = $ps3b = $psss = $pslf = $pscf = $psrf = 0;
	    $lines++;
	    @line = split;
	    if ( $#line == -1 ) {
		last;
	    }
	    elsif ( $#line < $SCOLS ) {
		print "STARTS format error, line $lines\n";
		$errors++;
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
			    $errors++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $psc = -1;
			}
		    }
		    elsif ( $pos eq '1b' ) {
			if ( $starts[5] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $ps1b = -1;
			}
		    }
		    elsif ( $pos eq '2b' ) {
			if ( $starts[6] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $ps2b = -1;
			}
		    }
		    elsif ( $pos eq '3b' ) {
			if ( $starts[7] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $ps3b = -1;
			}
		    }
		    elsif ( $pos eq 'ss' ) {
			if ( $starts[8] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $psss = -1;
			}
		    }
		    elsif ( $pos eq 'lf' ) {
			if ( $starts[9] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $pslf = -1;
			}
		    }
		    elsif ( $pos eq 'cf' ) {
			if ( $starts[10] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $pscf = -1;
			}
		    }
		    elsif ( $pos eq 'rf' ) {
			if ( $starts[11] == 0 ) {
			    printf("%-3s %s illegal start @ %s, line %s\n", $mlb, $name, $pos, $lines);
			    $errors++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $psrf = -1;
			}
		    }
		}
	    }

	    if ( $updates && $week && $home && $away ) {
		$dbh->do( "insert into $startsdb values ( '$mlb', '$name', 0, 0, $psc, $ps1b, $ps2b, $ps3b, $psss, $pslf, $pscf, $psrf, 0, 0, 0, $week, '$home', '$away' );" );
	    }
	    elsif ( $updates ) {
	    	$errors++;
	    }
	}
    }

    elsif ( $keyword eq 'INJURIES' ) {
	#print "INJURIES\n";
	while (<>) {
	    $lines++;
	    @line = split;
	    if ( $#line == -1 ) {
		last;
	    }
	    elsif ( $#line < $ICOLS ) {
		print "INJURIES format error, line $lines\n";
		$errors++;
	    }
	    else {
		( $slot, $pos, $ibl, $mlb, $name, $inj ) = @line;
		@starts = find( $mlb, $name, $lines);

		if ( @starts ) {
		    printf("%-3s %s injured for %s day(s)\n", $mlb, $name, $inj);
		}
	    }

	    if ( $updates && $week && $home && $away ) {
		$dbh->do( "insert into $startsdb values ( '$mlb', '$name', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, $inj, 0, 0, $week, '$home', '$away' );" );
	    }
	    elsif ( $updates ) {
	    	$errors++;
	    }
	}
    }
}

print "\n";
printf ("lines: %s\n", $lines);
printf ("Total BATTERS: %s\n", $batters);
printf ("Total PITCHERS: %s\n", $pitchers);
printf ("Total WINS: %s\n", $wins);
printf ("Total LOSSES: %s\n", $losses);
print "\n";

if ( $updates && !($week && $home && $away) ) {
    print "missing or invalid WEEK/HOME/AWAY info, cannot update\n";
}

if ( $errors ) {
    $dbh->rollback;
    print "stats database not updated due to errors\n";
    exit 1;
}
elsif ( $updates) {
    $dbh->commit;
    print "stats database updated successfully!\n";
    exit 0;
}

$dbh->disconnect;

