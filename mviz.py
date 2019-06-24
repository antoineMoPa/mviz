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
CHUNK_SIZE = 2048

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

  float get_spectra(float p, float past){
    return texture2D(spectra, vec2(p/2.0+0.5, past)).r;
  }

  void main() {
    vec2 p = v_position;
    p *= 1.2;
    vec4 col = vec4(0.0);
    float l = length(p);
    float a = atan(p.y, p.x);

    float t = mod(time * 0.1, 0.1);

    float s = 1.0 - clamp(get_spectra(a / 6.28 - 0.5 + t, 0.0), 0.0, 0.5);

    col += 1.0;
    float radius_1 = (1.0 - clamp((l - 1.0)/0.01, 0.0, 1.0));
    col *= clamp((abs(l)-s)/0.01, 0.0, 1.0) * radius_1;

    float rolling = get_spectra(a / 6.28 - 0.0, (1.0-l)/4.0) * (2.0 + a * 0.1);
    rolling = pow(4.0 * rolling, 4.0);

    rolling *= 10.0 * radius_1;
    col.r += rolling;
    col.a = 0.8;


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

sep_hz = 1024
rolling_spectra = np.zeros((sep_hz,sep_hz))

@window.event
def on_draw(dt):
    global time, rolling_spectra, sep_hz
    #window.clear()
    time += dt
    quad.draw(gl.GL_TRIANGLE_STRIP)

    chunk = np.frombuffer(data, dtype=np.int16)
    dct = scipy.fftpack.dct(chunk)

    volume_scale = 1.0 / CHUNK_SIZE / 1000

    sep = math.floor(sep_hz * dct.size/RATE * fmax)

    volume = np.sum(np.abs(chunk)) * volume_scale
    basses = np.sum(dct[0:sep]) * volume_scale / 2.0
    treble = np.sum(dct[sep:-1]) * volume_scale * 0.2
    step = math.floor(CHUNK_SIZE/sep_hz)
    spectra = np.convolve(dct, np.ones(step))[0:CHUNK_SIZE:step]

    spectra *= 1 + np.arange(0,len(spectra)) * 0.1

    rolling_spectra[-1,:] = spectra[0:sep_hz]
    rolling_spectra = np.roll(rolling_spectra, 1, axis=0)

    quad['volume'] = volume
    quad['basses'] = basses
    quad['treble'] = treble
    quad['spectra'] = rolling_spectra / 4e6
    quad['time'] = time

quad['spectra'] = rolling_spectra
app.run()
