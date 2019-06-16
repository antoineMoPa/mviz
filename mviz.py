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
  #define cl(x) clamp(x, 0.0, 1.0)
  void main() {
    vec2 p = v_position;
    vec4 col = vec4(0.0);

    float l = length(p);

    float b = 1.0 - clamp(l - 0.2 - basses * 0.4, 0.0, 1.0)/0.02;
    float t = 1.0 - clamp(1.0 - l - 0.1 - treble, 0.0, 1.0)/0.02;

    vec2 c = vec2(cos(time * 2.0), sin(time * 2.0)) * 0.55;

    float center_circle = cl(volume * cl(1.0 - abs(length(p) - 0.2 - b * 0.2)/0.1));
    float outside_circle = cl(t + clamp(b, 0.0, 1.0));
    outside_circle *= 1.0 + 0.3 * cos(p.y * 200.0 + time + b * cos(time + p.x));
    col.r += center_circle * (1.0 + 0.8 * cos(time));
    col.b += center_circle * (1.0 + 0.8 * sin(time));

    col = clamp(col, 0.0, 1.0);

    col.r += outside_circle * (0.4 + 0.2 * cos(time));
    col.b += outside_circle * 0.2;

    col = clamp(col, 0.0, 1.0);

    float moving_circle = (0.13 + 0.2 * basses - length(c - p)) / 0.02;
    moving_circle = clamp(moving_circle, 0.0, 1.0);
    moving_circle *= 1.0 + 0.2 * cos(length(p) * 30.0 + 10.0  * cos(time * 2.0));

    col.r += moving_circle * (1.0 + 0.4 * cos(time + 0.3));
    col.b += moving_circle * (1.0 + 0.4 * sin(time * 1.1));

    col = cl(col);

    col.r = pow(col.r, 2.0 + 1.0 * cos(time + p.x));
    col.g = pow(col.g, 2.0);


    col.a = max(col.r + col.g + col.b, 0.1);

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

    volume_scale = 1.0 / CHUNK_SIZE / 5000

    sep_hz = 10

    sep = math.floor(sep_hz * dct.size/RATE * fmax)

    volume = np.sum(np.abs(chunk)) * volume_scale
    basses = np.sum(dct[0:sep]) * volume_scale / 2.0
    treble = np.sum(dct[sep:-1]) * volume_scale * 0.2

    quad['volume'] = volume
    quad['basses'] = basses
    quad['treble'] = treble
    quad['time'] = time


app.run()

play_obj.wait_done()
