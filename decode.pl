#!/usr/bin/perl
# decode first text/plain MIME part
#
# $Id$

use MIME::Parser;

my $parser = new MIME::Parser;
$parser->output_to_core(1);

$entity = $parser->parse(\*STDIN) or die "parse failed\n";
# $entity->dump_skeleton;

if ( $entity->is_multipart ) {
    @parts = $entity->parts;
    while ( @parts ) {
	if ( $parts[0]->effective_type eq "text/plain" ) {
	    $parts[0]->bodyhandle->print;
	    break;
	}
	shift @parts;
    }
} else {
    $entity->bodyhandle->print;
}

exit;

