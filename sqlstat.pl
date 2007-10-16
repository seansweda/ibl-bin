#!/usr/bin/perl
#
# $Id$

# flags
#   -u: update
#   -U: update ignoring soft errors

use FindBin;
do "$FindBin::Bin/DBconfig.pl";
do "$FindBin::Bin/DBpasswd.pl";

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
$redo = 0;
$updates = 0;
$input = '';
$xteam = '';

# err flags
$softerr = 0;
$fatalerr = 0;

use DBI;

sub find {
    my $mlb = shift;
    my $name = shift;
    $name =~ s/'/''/g;
    my $where = shift;
    @s = $dbh->selectrow_array("select mlb, name, sum(g), sum(p), sum(c), 
    		sum(\"1b\"), sum(\"2b\"), sum(\"3b\"), sum(ss), sum(lf), sum(cf),
		sum(rf), sum(inj), nullif(sum(vl), 0), nullif(sum(vr), 0),
		count(*), count(vl), count(vr) from $startsdb 
    		where mlb = '$mlb' and trim(name) ~* '\^$name\$'
		group by mlb, name;");
    if ($#s == -1 ) {
	printf("line %s %-3s %s not found, perhaps:\n", $where, $mlb, $name);
	$loop = $dbh->prepare("select mlb, name from $startsdb
		where name ~* ? and week is null order by mlb, name desc;");
	$loop->execute($name);
	while ( @f = $loop->fetchrow_array ) {
	    printf("%-3s %s\n", $f[0], $f[1]);
	}
	return;
    }
    else {
	if ( $s[15] == $s[16] && !defined($s[13]) ) {
	    $s[13] = 0;
	}
	if ( $s[15] == $s[17] && !defined($s[14]) ) {
	    $s[14] = 0;
	}
    }

    $s[1] =~ s/'/''/g;
    return @s;
}

sub outs {
    my $ip = shift;
    my $whole = int($ip);
    my $thirds = ($ip - $whole) * 10;
    return ( $whole * 3 + $thirds );
}

sub iblck {
    my $team = shift;
    @s = $dbh->selectrow_array("select code from $teamdb where ibl = '$team';");
    if ( @s ) {
	return 0;
    }
    else {
	return 1;
    }
}

sub iblcode {
    my $team = shift;
    @s = $dbh->selectrow_array("select code from $teamdb where ibl = '$team';");
    return @s;
}

sub schedck {
    my $week = shift;
    my $home = shift;
    my $away = shift;
    my $redo = shift;

    my $fatalerr = 0;

    if ( !($week && $home && $away) ) {
	print "line $lines missing or invalid WEEK/HOME/AWAY info, cannot update\n";
	$fatalerr++;
    }
    else {
	@hcode = iblcode($home);
	@acode = iblcode($away);
	if ( @hcode && @acode ) {
	    @status = $dbh->selectrow_array("select status from $scheddb where 
	    		week = $week and home = '$hcode[0]' and away = '$acode[0]';");
	    if ( @status ) {
		if ( shift @status && !$redo ) {
		    print "week $week, $away @ $home already submitted (use REDO)\n";
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
    return $fatalerr;
}

while (@ARGV) {
    if ( $ARGV[0] eq '-u' ) {
	# update if no errors (for auto update)
	$updates = 1;
    }
    elsif ( $ARGV[0] eq '-U' ) {
	# update, ignore soft errors (for statistician)
	$updates = 2;
    }
    elsif ( $ARGV[0] eq '-r' ) {
	# re-do if stats have already been run
	$redo = 1;
    }
    else {
    	if ( -r $ARGV[0] ) {
	    $input = $ARGV[0];
	}
    }
    shift @ARGV;
}

$dbh = DBI->connect("dbi:Pg:dbname=$dbname;host=$host", "$username", "$password", {AutoCommit => 0});

if ( $input) {
    open (DATA, "$input") || die ("can't open: $datafile\n$!");
}
else {
    open (DATA, "-");
}

while (<DATA>) {

    $lines++;
    $keyword = (split)[0];

    if ( $keyword eq 'REDO' ) {
	$redo = 1;
    }
    elsif ( $keyword eq 'WEEK' ) {
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

    if ( $keyword eq 'BATTERS' && !$team ) {
	print "line $lines BATTERS missing IBL team designation\n";
	$fatalerr++;
	$batters++;
    }

    if ( $keyword eq 'PITCHERS' && !$team ) {
	print "line $lines PITCHERS missing IBL team designation\n";
	$fatalerr++;
	$pitchers++;
    }

    if ( $keyword eq 'BATTERS' && $team ) {
	$batters++;
	$order = 1;
	$start = 0;
	$sc = $s1b = $s2b = $s3b = $sss = $slf = $scf = $srf = 0;
	if ( $updates && !($week && $home && $away) ) {
	    print "line $lines missing or invalid WEEK/HOME/AWAY info, cannot update\n";
	    $fatalerr++;
	}
	if ( iblck($team) ) {
	    print "line $lines invalid IBL team designation: $team\n";
	    $fatalerr++;
	}
	while (<DATA>) {
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
		if ( $updates && $team ne $ibl ) {
		    print "line $lines team mismatch: $team != $ibl\n";
		    $fatalerr++;
		}
		if ( $updates && $ibl ne $home && $ibl ne $away ) {
		    print "line $lines team mismatch: $team != ($home/$away)\n";
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
		else {
		    #print "line $lines find error\n";
		    $fatalerr++;
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
			    $psc = -1;
			}
			$sc++;
		    }
		    elsif ( $pos eq '1b' ) {
			if ( $starts[5] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $ps1b = -1;
			}
			$s1b++;
		    }
		    elsif ( $pos eq '2b' ) {
			if ( $starts[6] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $ps2b = -1;
			}
			$s2b++;
		    }
		    elsif ( $pos eq '3b' ) {
			if ( $starts[7] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $ps3b = -1;
			}
			$s3b++;
		    }
		    elsif ( $pos eq 'ss' ) {
			if ( $starts[8] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $psss = -1;
			}
			$sss++;
		    }
		    elsif ( $pos eq 'lf' ) {
			if ( $starts[9] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $pslf = -1;
			}
			$slf++;
		    }
		    elsif ( $pos eq 'cf' ) {
			if ( $starts[10] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $pscf = -1;
			}
			$scf++;
		    }
		    elsif ( $pos eq 'rf' ) {
			if ( $starts[11] == 0 ) {
			    printf("line %s %-3s %s illegal start @ %s\n", $lines, $mlb, $name, $pos);
			    $softerr++;
			}
			else {
			    $psrf = -1;
			}
			$srf++;
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

		$dbh->do( "insert into $batdb values ( $week, '$home', '$away', '$ibl', '$starts[0]', '$starts[1]', 1, $ab, $r, $h, $bi, $d, $t, $hr, $sb, $cs, $bb, $k );" );
		$dbh->do( "insert into $startsdb values ( '$starts[0]', '$starts[1]', $g, 0, $psc, $ps1b, $ps2b, $ps3b, $psss, $pslf, $pscf, $psrf, 0, $pl, $pr, $week, '$home', '$away' );" );
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

	if ( $sc > 1 || $s1b > 1 || $s2b > 1 || $s3b > 1 || $sss > 1 || $slf > 1 || $scf > 1 || $srf > 1 ) {
	    print "line $lines $team multiple starters: ";
	    $fatalerr++;
	    if ( $sc > 1 ) {
		print "c ";
	    }
	    if ( $s1b > 1 ) {
		print "1b ";
	    }
	    if ( $s2b > 1 ) {
		print "2b ";
	    }
	    if ( $s3b > 1 ) {
		print "3b ";
	    }
	    if ( $sss > 1 ) {
		print "ss ";
	    }
	    if ( $slf > 1 ) {
		print "lf ";
	    }
	    if ( $scf > 1 ) {
		print "cf ";
	    }
	    if ( $srf > 1 ) {
		print "rf ";
	    }
	    print "\n";
	}

    }

    elsif ( $keyword eq 'PITCHERS' && $team ) {
	$pitchers++;
	$start = 1;
	if ( $updates && !($week && $home && $away) ) {
	    print "line $lines missing or invalid WEEK/HOME/AWAY info, cannot update\n";
	    $fatalerr++;
	}
	if ( iblck($team) ) {
	    print "line $lines invalid IBL team designation: $team\n";
	    $fatalerr++;
	}
	while (<DATA>) {
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
		if ( $updates && $team ne $ibl ) {
		    print "line $lines team mismatch: $team != $ibl\n";
		    $fatalerr++;
		}
		if ( $updates && $ibl ne $home && $ibl ne $away ) {
		    print "line $lines team mismatch: $team != ($home/$away)\n";
		    $fatalerr++;
		}
		@starts = find( $mlb, $name, $lines);
		if ( @starts ) {
		    if ( $starts[2] == 0) {
			printf("line %s %-3s %s illegal appearance\n", $lines, $mlb, $name);
			$softerr++;
		    }
		    $dec =~ tr/a-z/A-Z/;
		    if ( $start ) {
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
		else {
		    #print "line $lines find error\n";
		    $fatalerr++;
		}

		if ( $updates && !$fatalerr ) {
		    $ip = outs($ip);
		    $dbh->do( "insert into $pitdb values ( $week, '$home', '$away', '$ibl', '$starts[0]', '$starts[1]', $pw, $pl, $ps, 1, $pgs, $ip, $h, $r, $er, $hr, $bb, $k );" );
		    $dbh->do( "insert into $startsdb values ( '$starts[0]', '$starts[1]', -1, $pgs * -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, $week, '$home', '$away' );" );
		}
	    }
	}
    }
    
    elsif ( $keyword eq 'STARTS' ) {
	print "STARTS\n";
	if ( $updates && !($week && $home && $away) ) {
	    print "line $lines missing or invalid WEEK/HOME/AWAY info, cannot update\n";
	    $fatalerr++;
	}
	while (<DATA>) {
	    $psp = $psc = $ps1b = $ps2b = $ps3b = $psss = $pslf = $pscf = $psrf = 0;
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
			    $psp = -1;
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
		else {
		    #print "line $lines find error\n";
		    $fatalerr++;
		}
	    }

	    if ( iblck($ibl) ) {
		print "line $lines invalid IBL team designation: $ibl\n";
		$fatalerr++;
	    }
	    if ( $updates && !$fatalerr ) {
		$dbh->do( "insert into $startsdb values ( '$starts[0]', '$starts[1]', 0, $psp, $psc, $ps1b, $ps2b, $ps3b, $psss, $pslf, $pscf, $psrf, 0, 0, 0, $week, '$home', '$away' );" );
	    }
	}
    }

    elsif ( $keyword eq 'INJURIES' ) {
	print "INJURIES\n";
	if ( $updates && !($week && $home && $away) ) {
	    print "line $lines missing or invalid WEEK/HOME/AWAY info, cannot update\n";
	    $fatalerr++;
	}
	while (<DATA>) {
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

		if ( $inj !~ /^\d+$/ ) {
		    print "line $lines \"$inj\" not valid injury days\n";
		    $fatalerr++;
		}
		elsif ( @starts ) {
		    printf("%-3s %s injured for %s day(s)\n", $mlb, $name, $inj);
		}
		else {
		    #print "line $lines find error\n";
		    $fatalerr++;
		}
	    }

	    if ( iblck($ibl) ) {
		print "line $lines invalid IBL team designation: $ibl\n";
		$fatalerr++;
	    }
	    if ( $updates && !$fatalerr ) {
		$dbh->do( "insert into $startsdb values ( '$starts[0]', '$starts[1]', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, $inj, 0, 0, $week, '$home', '$away' );" );
	    }
	}
    }

    elsif ( $keyword eq 'TOTALS' ) {
	@line = split;
	if ( iblck($ibl) == 0 ) {
	    $xteam = $line[2];
	}
    }
    elsif ( $keyword eq 'E:' && $xteam ) {
	@line = split;
	if ( $line[1] > 0 ) {
	    $xe{$xteam} += $line[1];
	}
    }
    elsif ( $keyword eq 'PB:' && $xteam ) {
	@line = split;
	if ( $line[1] > 0 ) {
	    $xpb{$xteam} += $line[1];
	}
    }
    elsif ( $keyword eq 'GIDP:' && $xteam ) {
	@line = split;
	if ( $line[1] > 0 ) {
	    $xdp{$xteam} += $line[1];
	}
    }
    elsif ( $keyword eq 'SF:' && $xteam ) {
	@line = split;
	if ( $line[1] > 0 ) {
	    $xsf{$xteam} += $line[1];
	}
    }
    elsif ( $keyword eq 'HBP:' && $xteam ) {
	@line = split;
	if ( $line[1] > 0 ) {
	    $xhb{$xteam} += $line[1];
	}
    }
    elsif ( $keyword eq 'WP:' && $xteam ) {
	@line = split;
	if ( $line[1] > 0 ) {
	    $xwp{$xteam} += $line[1];
	}
    }
    elsif ( $keyword eq 'BALK:' && $xteam ) {
	@line = split;
	if ( $line[1] > 0 ) {
	    $xbk{$xteam} += $line[1];
	}
    }

    if ( $week && $home && $away && $redo ) {
	print "removing week $week, $away @ $home\n";
	@hcode = iblcode($home);
	@acode = iblcode($away);
	$dbh->do( "update $scheddb set status = 0 where
		week = $week and home = '$hcode[0]' and away = '$acode[0]';");
	$dbh->do( "delete from $startsdb where
		week = $week and home = '$home' and away = '$away';");
	$dbh->do( "delete from $batdb where
		week = $week and home = '$home' and away = '$away';");
	$dbh->do( "delete from $pitdb where
		week = $week and home = '$home' and away = '$away';");
	$dbh->do( "delete from $extradb where
		week = $week and home = '$home' and away = '$away';");
	$redo = 0;
    }
}

print "\n";
printf ("lines: %s\n", $lines);
printf ("Total BATTERS: %s\n", $batters);
printf ("Total PITCHERS: %s\n", $pitchers);
printf ("Total WINS: %s\n", $wins);
printf ("Total LOSSES: %s\n", $losses);
print "\n";

# printf "%s E: %d\n", $index, $xe{$index};
# printf "%s PB: %d\n", $index, $xpb{$index};
# printf "%s GIDP: %d\n", $index, $xdp{$index};
# printf "%s SF: %d\n", $index, $xsf{$index};
# printf "%s HBP: %d\n", $index, $xhb{$index};
# printf "%s WP: %d\n", $index, $xwp{$index};
# printf "%s BALK: %d\n", $index, $xbk{$index};
if ( $updates && !$fatalerr ) {
    foreach $index ( $away, $home ) {
	$sth = $dbh->prepare( "insert into $extradb values ( $week, '$home', '$away', '$index', ?, ?, ?, ?, ?, ?, ? );" );
	$sth->execute( int($xe{$index}), int($xpb{$index}), int($xdp{$index}), int($xsf{$index}), int($xhb{$index}), int($xwp{$index}), int($xbk{$index}) );
    }
}

if ( $batters == 0 && $pitchers == 0 ) {
    $dbh->rollback;
    $dbh->disconnect;
    exit 3;
}
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
    $fatalerr += (schedck( $week, $home, $away, $redo ));
    if ( $fatalerr ) {
	$dbh->rollback;
	print "stats database not updated, boxscore needs correction ($fatalerr errors)\n";
	$dbh->disconnect;
	exit 2;
    }
    elsif ( $softerr && $updates != 2 ) {
	$dbh->rollback;
	print "stats database not updated, illegal usage\n";
	$dbh->disconnect;
	exit 1;
    }
    else {
	@hcode = iblcode($home);
	@acode = iblcode($away);
	$dbh->do( "update $scheddb set status = 1 where
		week = $week and home = '$hcode[0]' and away = '$acode[0]';");
	$dbh->commit;
	print "stats database updated successfully!\n";
	$dbh->disconnect;
	exit 0;
    }
}

$dbh->disconnect;

if ( $fatalerr ) {
    exit 2;
}
elsif ( $softerr ) {
    exit 1;
}
else {
    exit 0;
}

