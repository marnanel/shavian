package ShavianOrg::Convert::MediaWikiToHtml;

use strict;
use warnings;

# Takes a document in MediaWiki markup, and returns
# an HTML fragment.

# We could do this with HTML::WikiConverter::MediaWiki
# but we want to handle some of the funky templates
# in our own way.

# FIXME: very incomplete.

sub _handle_templates {
    my ($wikitext) = @_;

    my @text = split /(\{\{[^\}]\}\})/, $wikitext;

    my $result = '';
    for my $t (@text) {
	if ($t =~ /\{/) {
	    # FIXME
	    $result .= "<fury:template fixme=\"1\" />";
	} else {
	    $result .= $t;
	}
    }

    return $result;
}

sub _handle_apostrophes {
    my ($wikitext) = @_;

    my @text = split /(\'+)/, $wikitext;

    my %state = (
	'i' => 0,
	'b' => 0,
	);

    my $result = '';

    my $toggleStyle = sub {
	my ($style) = @_;
	if ($state{$style}) {
	    $result .= "</$style>";
	} else {
	    $result .= "<$style>";
	}
	$state{$style} = !($state{$style});
    };

    for my $t (@text) {
	if ($t =~ /^'/) {
	    if ($t eq "''") {
		$toggleStyle->('i');
	    } elsif ($t eq "'''") {
		$toggleStyle->('b');
	    } elsif ($t eq "'''''") {
		$toggleStyle->('i');
		$toggleStyle->('b');
	    } else {
		$result .= $t;
	    }
	} else {
	    $result .= $t;
	}
    }

    $toggleStyle->('b') if $state{'b'};
    $toggleStyle->('i') if $state{'i'};

    return $result;
}

sub convert {
    my ($wikitext) = @_;

    my @paras = split /\n\n+/, $wikitext;

    my $result = '';
    for my $para (@paras) {
	$para =~ s/^:*//; # lose indentation
	$para = _handle_templates($para);
	$para = _handle_apostrophes($para);
	$result .= "<p>$para</p>\n\n";
    }

    return $result;
}

1;
