#!/bin/sh
#
# run this after checking out the repo to enable the hooks:
#
#   git-hooks/setup.sh

rm -rf .git/hooks
ln -sf ../git-hooks .git/hooks
