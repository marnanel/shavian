package ShavianOrg::Skin;

use strict;
use warnings;

use File::ShareDir qw(dist_file);
use Template;

sub handle {
  my ($details) = @_;

  my $template = Template->new({
      ABSOLUTE => 1,
    });

  $template->process(dist_file('ShavianOrg', 'skin.tt'), $details)
  || die $template->error();

}

1;

