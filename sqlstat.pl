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
$teamdb = teams2004;
$scheddb = sched2004;

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
$week = 0;
$home = '';
$away = '';
$updates = 0;

# err flags
$softerr = 0;
$fatalerr = 0;

use DBI;

if ( $#ARGV > 0 ) {
    if ( $ARGV[0] eq '-u' ) {
	shift @ARGV;
	# update if no errors (for auto update)
	$updates = 1;
    }
    if ( $ARGV[0] eq '-U' ) {
	shift @ARGV;
	# update, ignore soft errors (for statistician)
	$updates = 2;
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
	printf("line %s %-3s %s not found, perhaps:\n", $where, $mlb, $name);
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

sub iblck {
    $team = shift;
    @s = $dbh->selectrow_array("select code from $teamdb where ibl = '$team';");
    if ( @s ) {
	return 0;
    }
    else {
	return 1;
    }
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
	    print "line $lines WEEK format error: $week\n";
	    $fatalerr++;
	    $week = '';
	}
    }
    elsif ( $keyword eq 'HOME' ) {
	$home = (split)[1];
	$home =~ tr/a-z/A-Z/;
	if ( iblck($home) ) {
	    print "line $lines invalid IBL team designation: $home\n";
	    $fatalerr++;
	    $home = '';
	}
	else {
	    print "HOME: $home\n";
	}
    }
    elsif ( $keyword eq 'AWAY' ) {
	$away = (split)[1];
	$away =~ tr/a-z/A-Z/;
	if ( iblck($away) ) {
	    print "line $lines invalid IBL team designation: $away\n";
	    $fatalerr++;
	    $away = '';
	}
	else {
	    print "AWAY: $away\n";
	}
    }
    else {
	$team = (split)[1];
	$team =~ tr/a-z/A-Z/;
    }

    $keyword =~ tr/a-z/A-Z/;

    if ( $keyword eq 'BATTERS' && $team ) {
	$batters++;
	$order = 1;
	$start = 0;
	$sc = $s1b = $s2b = $s3b = $sss = $slf = $scf = $srf = 0;
	if ( $updates && !($week && $home && $away) ) {
	    $fatalerr++;
	}
	if ( iblck($team) ) {
	    print "line $lines invalid IBL team designation: $team\n";
	    $fatalerr++;
	}
	while (<>) {
	    $g = $psc = $ps1b = $ps2b = $ps3b = $psss = $pslf = $pscf = $psrf = 0;
	    $lines++;
	    @line = split;
	    if ( $#line == -1 ) {
		last;
	    }
	    elsif ( $#line != $BCOLS ) {
		print "line $lines BATTERS format error\n";
		$fatalerr++;
		last;
	    }
	    else {
		( $slot, $pos, $ibl, $mlb, $name, $ab, $r, $h, $bi, $d, $t, $hr, $sb, $cs, $bb, $k, $pl, $pr ) = @line;
		if ( $team ne $ibl ) {
		    print "line $lines team mismatch: $team != $ibl\n";
		    $fatalerr++;
		}
		@starts = find( $mlb, $name, $lines);
		if ( @starts ) {
		    if ( $starts[2] == 0 ) {
			printf("line %s %-3s %s illegal appearance\n", $lines, $mlb, $name);
			$softerr++;
		    }
		    if ( defined($starts[13]) ) {
			if ( $pl > 0 && $starts[13] < 1 ) {
			    printf("line %s %-3s %s illegal PA vLHP\n", $lines, $mlb, $name);
			    $softerr++;
			}
		    }
		    if ( defined($starts[14]) ) {
			if ( $pr > 0 && $starts[14] < 1 ) {
			    printf("line %s %-3s %s illegal PA vRHP\n", $lines, $mlb, $name);
			    $softerr++;
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
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $psc = $sc = -1;
			}
		    }
		    elsif ( $pos eq '1b' ) {
			if ( $starts[5] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $ps1b = $s1b = -1;
			}
		    }
		    elsif ( $pos eq '2b' ) {
			if ( $starts[6] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $ps2b = $s2b = -1;
			}
		    }
		    elsif ( $pos eq '3b' ) {
			if ( $starts[7] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $ps3b = $s3b = -1;
			}
		    }
		    elsif ( $pos eq 'ss' ) {
			if ( $starts[8] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $psss = $sss = -1;
			}
		    }
		    elsif ( $pos eq 'lf' ) {
			if ( $starts[9] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $pslf = $slf = -1;
			}
		    }
		    elsif ( $pos eq 'cf' ) {
			if ( $starts[10] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $pscf = $scf = -1;
			}
		    }
		    elsif ( $pos eq 'rf' ) {
			if ( $starts[11] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $psrf = $srf = -1;
			}
		    }
		}
	    }

	    if ( $updates && !$fatalerr ) {
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

	}
	
	if ( !($sc && $s1b && $s2b && $s3b && $sss && $slf && $scf && $srf) ) {
	    print "line $lines $team missing starters: ";
	    $fatalerr++;
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

    elsif ( $keyword eq 'PITCHERS' && $team ) {
	$pitchers++;
	$start = 1;
	if ( $updates && !($week && $home && $away) ) {
	    $fatalerr++;
	}
	if ( iblck($team) ) {
	    print "line $lines invalid IBL team designation: $team\n";
	    $fatalerr++;
	}
	while (<>) {
	    $pgs = $pw = $pl = $ps = 0;
	    $lines++;
	    @line = split;
	    if ( $#line == -1 ) {
		last;
	    }
	    elsif ( $#line != $PCOLS ) {
		print "line $lines PITCHERS format error\n";
		$fatalerr++;
		last;
	    }
	    else {
		( $dec, $ibl, $mlb, $name, $ip, $h, $r, $er, $bb, $k, $hr ) = @line;
		if ( $team ne $ibl ) {
		    print "line $lines team mismatch: $team != $ibl\n";
		    $fatalerr++;
		}
		@starts = find( $mlb, $name, $lines);
		if ( @starts && $starts[2] == 0) {
		    printf("line %s %-3s %s illegal appearance\n", $lines, $mlb, $name);
		    $softerr++;
		}
		$dec =~ tr/a-z/A-Z/;
		if ( @starts && $start ) {
		    if ( $starts[3] == 0 ) {
			printf("line %s %-3s %s illegal start @ p\n", $lines, $mlb, $name);
			$softerr++;
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

	    if ( $updates && !$fatalerr ) {
		$ip = outs($ip);
		$dbh->do( "insert into $pitdb values ( $week, '$home', '$away', '$ibl', '$mlb', '$name', $pw, $pl, $ps, 1, $pgs, $ip, $h, $r, $er, $bb, $k, $hr );" );
		$dbh->do( "insert into $startsdb values ( '$mlb', '$name', 1, $pgs, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, $week, '$home', '$away' );" );
	    }
	}
    }
    
    elsif ( $keyword eq 'STARTS' ) {
	#print "STARTS\n";
	if ( $updates && !($week && $home && $away) ) {
	    $fatalerr++;
	}
	while (<>) {
	    $psc = $ps1b = $ps2b = $ps3b = $psss = $pslf = $pscf = $psrf = 0;
	    $lines++;
	    @line = split;
	    if ( $#line == -1 ) {
		last;
	    }
	    elsif ( $#line < $SCOLS ) {
		print "line $lines STARTS format error\n";
		$fatalerr++;
		last;
	    }
	    else {
		( $slot, $pos, $ibl, $mlb, $name ) = @line;
		@starts = find( $mlb, $name, $lines);
		$pos =~ tr/A-Z/a-z/;
		$pos =~ s/\-.*$//;
		if ( @starts ) {
		    if ( $pos eq 'p' ) {
			if ( $starts[3] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $psc = -1;
			}
		    }
		    if ( $pos eq 'c' ) {
			if ( $starts[4] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $psc = -1;
			}
		    }
		    elsif ( $pos eq '1b' ) {
			if ( $starts[5] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $ps1b = -1;
			}
		    }
		    elsif ( $pos eq '2b' ) {
			if ( $starts[6] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $ps2b = -1;
			}
		    }
		    elsif ( $pos eq '3b' ) {
			if ( $starts[7] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $ps3b = -1;
			}
		    }
		    elsif ( $pos eq 'ss' ) {
			if ( $starts[8] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $psss = -1;
			}
		    }
		    elsif ( $pos eq 'lf' ) {
			if ( $starts[9] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $pslf = -1;
			}
		    }
		    elsif ( $pos eq 'cf' ) {
			if ( $starts[10] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $pscf = -1;
			}
		    }
		    elsif ( $pos eq 'rf' ) {
			if ( $starts[11] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    printf("%-3s %s extra start @ %s\n", $mlb, $name, $pos);
			    $psrf = -1;
			}
		    }
		}
	    }

	    if ( iblck($ibl) ) {
		print "line $lines invalid IBL team designation: $ibl\n";
		$fatalerr++;
	    }
	    if ( $updates && !$fatalerr ) {
		$dbh->do( "insert into $startsdb values ( '$mlb', '$name', 0, 0, $psc, $ps1b, $ps2b, $ps3b, $psss, $pslf, $pscf, $psrf, 0, 0, 0, $week, '$home', '$away' );" );
	    }
	}
    }

    elsif ( $keyword eq 'INJURIES' ) {
	#print "INJURIES\n";
	if ( $updates && !($week && $home && $away) ) {
	    $fatalerr++;
	}
	while (<>) {
	    $lines++;
	    @line = split;
	    if ( $#line == -1 ) {
		last;
	    }
	    elsif ( $#line < $ICOLS ) {
		print "line $lines INJURIES format error\n";
		$fatalerr++;
		last;
	    }
	    else {
		( $slot, $pos, $ibl, $mlb, $name, $inj ) = @line;
		@starts = find( $mlb, $name, $lines);

		if ( @starts ) {
		    printf("%-3s %s injured for %s day(s)\n", $mlb, $name, $inj);
		}
	    }

	    if ( iblck($ibl) ) {
		print "line $lines invalid IBL team designation: $ibl\n";
		$fatalerr++;
	    }
	    if ( $updates && !$fatalerr ) {
		$dbh->do( "insert into $startsdb values ( '$mlb', '$name', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, $inj, 0, 0, $week, '$home', '$away' );" );
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

if ( $wins != $losses ) {
    print "WINS & LOSSES not equal\n";
    $fatalerr++;
}
if ( $batters != $pitchers ) {
    print "BATTERS & PITCHERS not equal\n";
    $fatalerr++;
}
if ( (($batters / 2) - int($batters / 2)) != 0 ) {
    print "BATTERS imbalanced\n";
    $fatalerr++;
}
if ( (($pitchers / 2) - int($pitchers / 2)) != 0 ) {
    print "PITCHERS imbalanced\n";
    $fatalerr++;
}

if ( $updates ) {
    print "\n";
    if ( !($week && $home && $away) ) {
	print "missing or invalid WEEK/HOME/AWAY info, cannot update\n";
	$fatalerr++;
    }
    else {
	@hcode = $dbh->selectrow_array("select code from $teamdb where ibl = '$home';");
	@acode = $dbh->selectrow_array("select code from $teamdb where ibl = '$away';");
	if ( @hcode && @acode ) {
	    @status = $dbh->selectrow_array("select status from $scheddb where 
	    		week = $week and home = '$hcode[0]' and away = '$acode[0]';");
	    if ( @status ) {
		if ( shift @status ) {
		    print "week $week, $away @ $home already submitted\n";
		    $fatalerr++;
		}
	    }
	    else {
		print "$away @ $home not valid matchup for week $week\n";
		$fatalerr++;
	    }
	}
	else {
	    print "$away @ $home not valid matchup for week $week\n";
	    $fatalerr++;
	}
    }

    if ( $fatalerr ) {
	$dbh->rollback;
	print "stats database not updated, boxscore needs correction\n";
	exit 2;
    }
    elsif ( $softerr && $updates != 2 ) {
	$dbh->rollback;
	print "stats database not updated, illegal usage\n";
	exit 1;
    }
    elsif ( $softerr && $updates == 2 ) {
	$dbh->do( "update $scheddb set status = 1 where
		week = $week and home = '$hcode[0]' and away = '$acode[0]';");
	$dbh->commit;
	print "stats database updated successfully!\n";
	exit 0;
    }
    else {
	$dbh->do( "update $scheddb set status = 1 where
		week = $week and home = '$hcode[0]' and away = '$acode[0]';");
	$dbh->commit;
	print "stats database updated successfully!\n";
	exit 0;
    }
}

$dbh->disconnect;

