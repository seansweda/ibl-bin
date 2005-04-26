#!/usr/bin/perl
#
# $Id$

$END = 55;

$line1 = <>;
while ( $line2 = <> ) {
    if ( (length($line2) <= 80-$END) && (length($line1) >= $END) ) {
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

