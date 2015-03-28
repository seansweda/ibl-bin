#!/usr/bin/perl
# decode first text/plain MIME part
#
# $Id$

use MIME::Parser;

my $parser = new MIME::Parser;
$parser->output_to_core(1);

if (@ARGV) {
    $entity = $parser->parse_open("$ARGV[0]") or die "parse failed\n";
} else {
    $entity = $parser->parse(\*STDIN) or die "parse failed\n";
}
# $entity->dump_skeleton;

if ( $entity->is_multipart ) {
    @parts = $entity->parts;
    while ( @parts ) {
	if ( $parts[0]->effective_type eq "text/plain" ) {
	    $msg = $parts[0]->bodyhandle->as_string;
	    break;
	}
	shift @parts;
    }
} else {
    $msg = $entity->bodyhandle->as_string;
}

# strip out additional crap here
$msg =~ s/\xA0/ /g;	# hex A0 -> space
$msg =~ s/\xC2//g;	# hex C2 -> null

print $msg;

exit;

