#!/usr/bin/perl
#
# $Id$

$END = 60;

$line1 = <>;
while ( $line2 = <> ) {
    if ( ( $line2 !~ /^(\s)+$/ ) && ($line2[0] ne '\n') && (length($line2) <= 80-$END) && (length($line1) >= $END) ) {
	if ( (length($line1) >= $END ) ) {
	    print substr $line1,0,-1;
	    print $line2;
	    $line1 = "";
	}
    }
    else {
	print $line1;
	$line1 = $line2;
    }

}

