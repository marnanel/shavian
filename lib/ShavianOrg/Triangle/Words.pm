package ShavianOrg::Triangle::Words;

use strict;
use warnings;
use ShavianOrg::Database;

use Data::Dumper;

sub handle {

    die "Don't use ShavianOrg::Triangle::Words for the moment.";
    
    my $db = ShavianOrg::Database->new();
    my $dbh = $db->dbh();

    print Dumper($dbh->selectall_arrayref('select page_title, old_text from page, revision, pagecontent where page_namespace=0 and page_latest=rev_id and rev_text_id=old_id order by page_title'));

    $dbh->disconnect();
}

1;
