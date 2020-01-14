#!/usr/bin/env python2
import numpy as np
import pyaudio
from datetime import datetime, timedelta

class Ringer:
	p = pyaudio.PyAudio()
	fs = 44100
	volume = 1
	duration = 2.0
	f = 440.0
	stream = None
	ring_time = None

	def __init__(self):
		if Ringer.stream is None:
			samples = (np.sin(2*np.pi*np.arange(Ringer.fs*Ringer.duration)*Ringer.f/Ringer.fs)).astype(np.float32).tobytes()
			Ringer.ring_data = Ringer.volume*samples
			Ringer.stream = Ringer.p.open(format=pyaudio.paFloat32, channels=1, rate=Ringer.fs, output=True, start=False, stream_callback=self.ring_callback)

	@classmethod
	def ring_callback(cls, in_data, frame_count, time_info, status):
		end_time = datetime.now() - timedelta(seconds=cls.duration)

		# after x seconds STOP RINGING
		if cls.ring_time and end_time >= cls.ring_time:
			print('Stopping ring...')
			cls.ring_time = None
			return (cls.ring_data, pyaudio.paComplete)

		if not cls.ring_time:
			cls.ring_time = datetime.now()
			print('Started ring ' + cls.ring_time.strftime("%Y-%m-%d %H:%M:%S") + ' ending at ' + end_time.strftime("%Y-%m-%d %H:%M:%S"))

		return (cls.ring_data, pyaudio.paContinue)

	@classmethod
	def ring(cls):
		if not cls.ring_time:
			print('Stopping stream before starting...')
			cls.stream.stop_stream()

		if not cls.stream.is_active():
			cls.stream.start_stream()
			print("...STAY FOREVER!!!")

	@classmethod
	def destroy(cls):
		if cls.stream is not None:
			cls.stream.stop_stream()
			cls.stream.close()
