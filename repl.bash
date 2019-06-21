#!/bin/bash

# Watches script for changes
#  - kills running instance
#  - starts new one
#  - focus back on window matching $EDITOR
# Requirements: inotify-tools wmctrl

EDITOR=emacs

./mviz.py&

while inotifywait -e close_write mviz.py;
do
	killall "mviz.py";
	./mviz.py& sleep 1.0;
	wmctrl -a $EDITOR &
done
