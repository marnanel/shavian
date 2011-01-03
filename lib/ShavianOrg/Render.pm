package ShavianOrg::Render;

use strict;
use warnings;

use ShavianOrg::Database;

sub _render_latn {
    my ($document) = @_;

    my $db = ShavianOrg::Database->new();

    my $dbh = $db->dbh();

    my $sth = $dbh->prepare('select latn, suffix from triangledocs where docid=?');

    $sth->execute($document);

    my @result = ('');

    for my $word (@{ $sth->fetchall_arrayref() }) {
        $result[-1] .= $word->[0] if $word->[0];
        if ($word->[1]) {
            my ($before, $after) = $word->[1] =~ m/^(.*)\n\n(.*)$/;

            if (defined $after) {
                # there is a paragraph break
                $result[-1] .= $before if $before;
                push @result, '';
                $result[-1] .= $after if $after;
            } else {
                # no paragraph break
                $result[-1] .= $word->[1];
            }
        }
    }

    return \@result;
}

# Returns a listref of hashrefs.  Each one contains at least two fields, "type" and "value".
# *** The following is out of date ***
# If type is "f" (filler), the value is a literal string such as a space.
# If type is "s", the value is a Shavian string.
# If type is "u", the value is the Latin-alphabet string because the word was unknown.
# If type is "d", the word was ambiguous, the value is the word, and there is an extra field "d", a hash of possibilities.
sub render {
    my ($document, $debug) = @_;

    my $db = ShavianOrg::Database->new();

    my $dbh = $db->dbh();

    my $sth = $dbh->prepare('select suffix, latn, lemma, old_text from triangledocs left outer join page on lemma=page_title left outer join revision on page_latest=rev_id left outer join pagecontent on rev_text_id=old_id where docid=? and (page_namespace=0 or page_namespace is null)');

    $sth->execute($document);

    my @result = ([]);

    for my $word (@{ $sth->fetchall_arrayref() }) {

        if ($word->[1]) {
            if (!defined $word->[3]) {
                push @{$result[-1]}, { type=>'u', latn=>$word->[1] };
            } elsif ($word->[3] =~ /{{dab}}/i) {
                my %dabs = $word->[3] =~ m/^\*\s*\[\[([a-z_]*)\]\][ -]*([a-z0-9_ -]*)/mig;
                push @{$result[-1]}, { type=>'d', d => \%dabs, latn=>$word->[1] };
            } else {
                my ($shaw) = $word->[3] =~ m/{{Shaw\|([^|}]*)/i;
                if (defined $shaw) {
                    push @{$result[-1]}, { type=>'s', shaw=>$shaw, latn=>$word->[1] };
                } else {
                    # weird; fall back
                    push @{$result[-1]}, { type=>'u', latn=>$word->[1] };
                }
            }
        }

        # Suffix?
        if ($word->[0]) {
            my $suffix = $word->[0];

            # I suppose we might have two, but it would be rare
            # and make the code far more complicated, and it doesn't
            # really cause any difficulties to ignore that case.

            my ($before, $after) = $suffix =~ m/^(.*)\n\n(.*)/;

            if (defined $after) {
                # there is a paragraph break
                push @{$result[-1]}, { type=>'f', value=>$before } if $before;
                push @result, [];
                push @{$result[-1]}, { type=>'f', value=>$after } if $after;
            } else {
                # there is no paragraph break
                push @{$result[-1]}, { type=>'f', value=>$suffix };
            }
        }
    }

    return {paras=>\@result};
}

1;
