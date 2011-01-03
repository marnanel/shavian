package ShavianOrg::Triangle::Docs;

use strict;
use warnings;
use ShavianOrg::Database;

use Data::Dumper;

use ShavianOrg::Convert::MediaWikiToHtml;

# (docid integer, wordid integer, lemma text, latn text, suffix text, caps smallint)

sub convert_doc {

    my ($dbh, $docid) = @_;

    my $sth = $dbh->prepare("SELECT old_text FROM pagecontent WHERE old_id=?");

    $sth->execute($docid);

    my ($r) = $sth->fetchrow_array();

    my $html = ShavianOrg::Convert::MediaWikiToHtml::convert($r);

    my %holding;

    my $wordid = 0;

    my $insert = $dbh->prepare("INSERT INTO triangledocs (docid, wordid, lemma, latn, suffix, caps) VALUES (?,?,?,?,?,?)");

    my $flush = sub {
	$wordid++;

	$holding{'lemma'} = '' unless $holding{'lemma'};
	$holding{'latn'} = '' unless $holding{'latn'};
	$holding{'suffix'} = '' unless $holding{'suffix'};
	$holding{'caps'} = 0 unless $holding{'caps'};

	$insert->execute($docid, $wordid,
			 $holding{'lemma'},
			 $holding{'latn'},
			 $holding{'suffix'},
			 $holding{'caps'});
			 
	%holding = ();
    };

    my $emit_word = sub {
	my ($text) = @_;

	$flush->();

	my $caps = 0;

	$holding{'latn'} = $text;
	$holding{'lemma'} = ucfirst(lc($text));

	if ($text eq $holding{'lemma'}) {
	    $caps = 1;
	} elsif ($text ne lc($text)) {
	    $caps = 2;
	}

	$holding{'caps'} = $caps;
    };

    my $emit_nonword = sub {
	my ($text) = @_;

	$holding{'suffix'} = '' unless $holding{'suffix'};

	$holding{'suffix'} .= $text;
    };

    my @by_tags = split /(<[^>]*>|&[^;]*;)/, $html;

    for my $t (@by_tags) {

	next if $t eq '';

	if ($t =~ /^[<&]/) {
	    # a tag
	    $emit_nonword->($t);
	} else {
	    my @by_text = split /([a-z][a-z\'_]*)/i, $t;

	    for my $u (@by_text) {
		if ($u =~ /^[a-z]/i) {
		    $emit_word->($u);
		} else {
		    $emit_nonword->($u);
		}
	    }
	}
    }

    $flush->();
}

sub convert_all {
    my ($dbh, $verbose) = @_;

    # pick out just the documents which aren't
    # already dealt with

    my $sth = $dbh->prepare('select page_title, rev_text_id from page, revision left outer join triangledocs on (rev_text_id=docid) where page_namespace=100 and page_latest=rev_id and docid is null order by page_title');

    $sth->execute();

    for my $doc (@{$sth->fetchall_arrayref()}) {
        print $doc->[0], "\n" if $verbose;
        convert_doc($dbh, $doc->[1]);
    }

    print "All done.\n" if $verbose;
}

sub handle {

    my $db = ShavianOrg::Database->new();
    my $dbh = $db->dbh();

    # weird pattern, but it's an actual document
    #convert_doc($dbh, 12121);
    convert_all($dbh, 1);
}

1;
