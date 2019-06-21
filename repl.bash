#!/bin/bash

# Watches script for changes
#  - kills running instance
#  - starts new one
#  - focus back on window matching $EDITOR
# Requirements: inotify-tools wmctrl

EDITOR=emacs

# TODO: Remove
killall inotifywait

while inotifywait -e close_write mviz.py; do
	killall "mviz.py";
	./mviz.py& sleep 2.0;
	wmctrl -a $EDITOR;
	sleep 1
done
