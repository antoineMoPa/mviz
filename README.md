# mviz

Music Viz Playground

# Use on your speaker output

First, with pulseaudio running, create a loopback device:

    pacmd load-module module-loopback latency_msec=5

Then set the default (fallback) to this loopback device in pavucontrol.

Just see my answer here https://stackoverflow.com/questions/26573556/record-speakers-output-with-pyaudio