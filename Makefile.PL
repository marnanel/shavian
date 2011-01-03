use inc::Module::Install;

name 'ShavianOrg';
all_from 'lib/ShavianOrg.pm';

requires 'DBI';
requires 'File::ShareDir';
requires 'Template';

install_script 'scripts/shavian-triangle';

install_share 'share';

WriteAll;

