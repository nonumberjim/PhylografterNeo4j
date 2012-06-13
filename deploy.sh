#!/bin/sh
SRC=/home/rree/src/phylografter
DEST=rickroll:/home/rree/src/
rsync -auiz --delete \
    --exclude cache --exclude sessions --exclude errors --exclude .svn \
    --exclude private \
    --exclude \*.~ \
    --exclude httpd.pid \
    $SRC $DEST
