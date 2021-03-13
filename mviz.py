#!/usr/bin/python3

import math
import scipy.io.wavfile
import scipy.fftpack
import numpy as np
from glumpy import app, gloo, gl
import pyaudio
import wave
from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent

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

fragment = ""

with open("fragment.glsl") as fragment_file:
  fragment = fragment_file.read()

def build_quad(vertex, fragment):
    quad = gloo.Program(vertex, fragment, count=4)

    quad['position'] = [(-1.0, -1.0),
                        (-1.0, +1.0),
                        (+1.0, -1.0),
                        (+1.0, +1.0)]

    quad['color'] = 1,0,0,1  # red

    return quad

quad = build_quad(vertex, fragment)

window = app.Window(width=960, height=1000)
window.set_position(1600,0)

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

observer = Observer()
event_handler = FileModifiedEvent("fragment.glsl")
observer.schedule(event_handler, "fragment.glsl")
observer.start()

def dispatch(event):
  global quad # ouch..... global variables.........
  with open("fragment.glsl") as fragment_file:
    fragment = fragment_file.read()
    quad = build_quad(vertex, fragment)
    quad['volume'] = 0.0
    quad['basses'] = 0.0
    quad['treble'] = 0.0
    quad['spectra'] = rolling_spectra / 4e6
    quad['time'] = 0.0
    print("Reloaded fragment shader")

event_handler.dispatch = dispatch

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
