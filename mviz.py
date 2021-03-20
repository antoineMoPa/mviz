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

sep_hz = 1024

rolling_spectra = np.zeros((sep_hz,sep_hz))

def build_quad(vertex, fragment):
    quad = gloo.Program(vertex, fragment, count=4)

    quad['position'] = [(-1.0, -1.0),
                        (-1.0, +1.0),
                        (+1.0, -1.0),
                        (+1.0, +1.0)]

    quad['color'] = 1,0,0,1  # red

    # Dummy values to initiate uniforms
    quad['volume'] = 0.0
    quad['basses'] = 0.0
    quad['treble'] = 0.0
    quad['spectra'] = rolling_spectra / 4e6
    quad['time'] = 0.0
    quad['width'] = 10
    quad['height'] = 10
    quad['ratio'] = 1

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

observer = Observer()
event_handler = FileModifiedEvent("fragment.glsl")

def dispatch(event):
  global should_reload_fragment
  should_reload_fragment = True

event_handler.dispatch = dispatch

observer.schedule(event_handler, "fragment.glsl")
observer.start()

should_reload_fragment = True

import objgraph
import gc

def reload_fragment():
  global quad, should_reload_fragment
  should_reload_fragment = False

  with open("fragment.glsl") as fragment_file:
    fragment = fragment_file.read()

    # TODO fix memory leak :)
    new_quad = build_quad(vertex, fragment)

    quad.deactivate()
    quad.delete()
    del quad
    quad = new_quad

    gc.collect()
    print("Reloaded fragment shader")

@window.event
def on_draw(dt):
    global time, rolling_spectra, sep_hz
    #window.clear()
    time += dt

    if should_reload_fragment:
      reload_fragment()

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

    win_size = window.get_size()
    quad['width'] = win_size[0]
    quad['height'] = win_size[1]
    quad['ratio'] = win_size[1] / win_size[0]

quad['spectra'] = rolling_spectra
app.run()
