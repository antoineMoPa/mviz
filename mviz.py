#!/usr/bin/python3

import math
import scipy.io.wavfile
import scipy.fftpack
import numpy as np
from glumpy import app, gloo, gl
import pyaudio
import wave

SAMPLING_TIME = 1

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK_SIZE = 1024

fmax = RATE

vertex = """
  attribute vec2 position;
  varying vec2 v_position;

  void main()
  {
      gl_Position = vec4(position, 0.0, 1.0);
      v_position = position;
  } """

fragment = """
  varying vec2 v_position;
  uniform vec4 color;
  uniform float volume, treble, basses, time;
  uniform sampler2D spectra;

  #define cl(x) clamp(x, 0.0, 1.0)
  void main() {
    vec2 p = v_position;
    vec4 col = vec4(0.0);
    float l = length(p);

    float s = texture2D(spectra, vec2(p.x + 0.5) + 0.5).r;

    float height = s;

    col.r += cos(time * 0.3 + 1.0) * 0.5 + 0.9;
    col.g += cos(time * 0.3 + 2.0) * 0.5 + 0.9;
    col.b += cos(time * 0.3 + 3.0) * 0.5 + 0.9;
    
    col *= 1.0 - clamp((abs(p.y)-height)/0.01, 0.0, 1.0);
    
    float circle = 0.0;
    float circle_spectra = texture2D(spectra, vec2(floor(l*10.0)/10.0)/2.0 + 0.5).r;
    col.r += circle_spectra/0.01 * (0.5 * cos(time + l + 0.4) + 0.5);
    col.g += circle_spectra/0.01 * (0.5 * cos(time + l + 1.0) + 0.5);
    col.b += circle_spectra/0.01 * (0.5 * cos(time + l + 2.0) + 0.5);

    col.a = 0.2;

    gl_FragColor = col;
  } """

quad = gloo.Program(vertex, fragment, count=4)

quad['position'] = [(-1.0, -1.0),
                    (-1.0, +1.0),
                    (+1.0, -1.0),
                    (+1.0, +1.0)]

quad['color'] = 1,0,0,1  # red

window = app.Window(width=400, height=400)
window.set_position(200,300)

time = 0

data = np.zeros(CHUNK_SIZE)

def audio_callback(in_data, frame_count, time_info, status):
    global data
    data = in_data
    return (None, pyaudio.paContinue)

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                stream_callback=audio_callback,
                frames_per_buffer=CHUNK_SIZE)

@window.event
def on_draw(dt):
    global time
    #window.clear()
    time += dt
    quad.draw(gl.GL_TRIANGLE_STRIP)

    chunk = np.frombuffer(data, dtype=np.int16)
    dct = scipy.fftpack.dct(chunk)

    volume_scale = 1.0 / CHUNK_SIZE / 1000

    sep_hz = 100

    sep = math.floor(sep_hz * dct.size/RATE * fmax)

    volume = np.sum(np.abs(chunk)) * volume_scale
    basses = np.sum(dct[0:sep]) * volume_scale / 2.0
    treble = np.sum(dct[sep:-1]) * volume_scale * 0.2
    spectra = np.tile(np.convolve(dct, np.ones(10))[0:1000:10], 1)

    quad['volume'] = volume
    quad['basses'] = basses
    quad['treble'] = treble
    quad['spectra'] = spectra / 10e5
    quad['time'] = time

quad['spectra'] = np.ones((100,1))
app.run()

play_obj.wait_done()
