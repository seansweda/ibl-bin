#!/usr/bin/perl -wT
# $Id: splits.pl,v 1.1 2011/02/09 03:47:27 sweda Exp sweda $
# my first cgi, just prints out environment and parameters

use strict;

use CGI;
use CGI::Pretty;
$CGI::POST_MAX=1024 * 100;  # max 100K posts
$CGI::DISABLE_UPLOADS = 1;  # no uploads

sub regrate {
    my $pa = shift;
    return ( .75 - .75 / 900 * $pa );
}

sub simplereg {
    my $lh = $_[0] / $_[1];
    my $rh = $_[2] / $_[3];
    my $ltarget = ( $lh + $rh ) / 2;
    my $rtarget = $ltarget;

    my $regpa;
    if ( $lh > $rh ) {
	$regpa = $_[1];
    } else {
	$regpa = $_[3];
    }

    my $lrate = ( $lh - ( regrate( $regpa ) * ( $lh - $ltarget ) ) * $_[3] / ( $_[1] + $_[3] ) * 2 );
    my $rrate = ( $rh - ( regrate( $regpa ) * ( $rh - $rtarget ) ) * $_[1] / ( $_[1] + $_[3] ) * 2 );

    $_[0] = $lrate * $_[1];
    $_[2] = $rrate * $_[3];
}

my $q = new CGI;

print $q->header, $q->start_html( 'splits.pl' );

# validate input
my $var;
foreach $var ( $q->param ) {
    if ( $q->param( $var ) !~ /^\d+$/ ) { 
	goto FORM; 
    }
}

$q->import_names('F');

if ( $F::abL > 0 && $F::abR > 0 ) {
    print "<pre>";
    print "original data\n";
    printf "     AB   H  2B  3B  HR  BB  HB       BA   OBP   SLG\n", $F::abL, $F::hL, $F::dL, $F::tL, $F::hrL, $F::bbL, $F::hbL;
    printf "vLH %3d %3d %3d %3d %3d %3d %3d   ", $F::abL, $F::hL, $F::dL, $F::tL, $F::hrL, $F::bbL, $F::hbL;
    printf " %5.3f", $F::hL / $F::abL;
    printf " %5.3f", ( $F::hL + $F::bbL + $F::hbL ) / ( $F::abL + $F::bbL + $F::hbL );
    printf " %5.3f\n", ( $F::hL + $F::dL + 2 * $F::tL + 3 * $F::hrL ) / $F::abL;
    printf "vRH %3d %3d %3d %3d %3d %3d %3d   ", $F::abR, $F::hR, $F::dR, $F::tR, $F::hrR, $F::bbR, $F::hbR;
    printf " %5.3f", $F::hR / $F::abR;
    printf " %5.3f", ( $F::hR + $F::bbR + $F::hbR ) / ( $F::abR + $F::bbR + $F::hbR );
    printf " %5.3f\n", ( $F::hR + $F::dR + 2 * $F::tR + 3 * $F::hrR ) / $F::abR;

    print $q->p;

    my @lh = ( $F::abL + $F::bbL + $F::hbL, $F::hL - $F::dL - $F::tL - $F::hrL, $F::dL, $F::tL, $F::hrL, $F::bbL, $F::hbL );
    my @rh = ( $F::abR + $F::bbR + $F::hbR, $F::hR - $F::dR - $F::tR - $F::hrR, $F::dR, $F::tR, $F::hrR, $F::bbR, $F::hbR );

    for ( my $i = 1; $i < 7; $i++ ) {
	#print "orig: $lh[$i] $rh[$i]\n";
	simplereg( $lh[$i], $lh[0], $rh[$i], $rh[0] );
	#print "new: $lh[$i] $rh[$i]\n";
    }

    print "simple split regression\n";
    printf "       AB    1B    2B    3B    HR    BB    HB       BA   OBP   SLG\n", $F::abL, $F::hL, $F::dL, $F::tL, $F::hrL, $F::bbL, $F::hbL;
    printf "vLH %5.1f %5.1f %5.1f %5.1f %5.1f %5.1f %5.1f   ", $F::abL, $lh[1], $lh[2], $lh[3], $lh[4], $lh[5], $lh[6];
    printf " %5.3f", ( $lh[1] + $lh[2] + $lh[3] + $lh[4] ) / $F::abL;
    printf " %5.3f", ( $lh[1] + $lh[2] + $lh[3] + $lh[4] + $lh[5] + $lh[6] ) / ( $F::abL + $lh[5] + $lh[6] );
    printf " %5.3f\n", ( $lh[1] + 2 * $lh[2] + 3 * $lh[3] + 4 * $lh[4] ) / $F::abL;
    printf "vRH %5.1f %5.1f %5.1f %5.1f %5.1f %5.1f %5.1f   ", $F::abR, $rh[1], $rh[2], $rh[3], $rh[4], $rh[5], $rh[6];
    printf " %5.3f", ( $rh[1] + $rh[2] + $rh[3] + $rh[4] ) / $F::abR;
    printf " %5.3f", ( $rh[1] + $rh[2] + $rh[3] + $rh[4] + $rh[5] + $rh[6] ) / ( $F::abR + $rh[5] + $rh[6] );
    printf " %5.3f\n", ( $rh[1] + 2 * $rh[2] + 3 * $rh[3] + 4 * $rh[4] ) / $F::abR;
    print $q->p;
    print "</pre>";
}

FORM:
print $q->p, "input split data";
print $q->start_form( 'POST', '/~sweda/cgi-bin/splits.pl' );
print $q->p, "vs LH\t";
print $q->textfield( 'abL','AB',3,3);
print $q->textfield( 'hL','H',3,3);
print $q->textfield( 'dL','2B',3,3);
print $q->textfield( 'tL','3B',3,3);
print $q->textfield( 'hrL','HR',3,3);
print $q->textfield( 'bbL','BB',3,3);
print $q->textfield( 'hbL','HB',3,3);
print $q->p, "vs RH\t";
print $q->textfield( 'abR','AB',3,3);
print $q->textfield( 'hR','H',3,3);
print $q->textfield( 'dR','2B',3,3);
print $q->textfield( 'tR','3B',3,3);
print $q->textfield( 'hrR','HR',3,3);
print $q->textfield( 'bbR','BB',3,3);
print $q->textfield( 'hbR','HB',3,3);
print $q->p, $q->submit, $q->end_form;
    
print $q->end_html;

