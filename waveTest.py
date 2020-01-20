import wave
import struct
import time

def get_loud_times(wav_path, threshold=10000, time_constant=0.1):
    '''Work out which parts of a WAV file are loud.
        - threshold: the variance threshold that is considered loud
        - time_constant: the approximate reaction time in seconds'''

    wav = wave.open(wav_path, 'r')
    length = wav.getnframes()
    samplerate = wav.getframerate()

    assert wav.getnchannels() == 1, 'wav must be mono'
    assert wav.getsampwidth() == 2, 'wav must be 16-bit'

    # Our result will be a list of (time, is_loud) giving the times when
    # when the audio switches from loud to quiet and back.
    is_loud = False
    result = [(0., is_loud)]

    # The following values track the mean and variance of the signal.
    # When the variance is large, the audio is loud.
    mean = 0
    variance = 0

    # If alpha is small, mean and variance change slower but are less noisy.
    alpha = 1 / (time_constant * float(sample_rate))

    for i in range(length):
        sample_time = float(i) / samplerate
        sample = struct.unpack('<h', wav.readframes(1))

        # mean is the average value of sample
        mean = (1-alpha) * mean + alpha * sample

        # variance is the average value of (sample - mean) ** 2
        variance = (1-alpha) * variance + alpha * (sample - mean) ** 2

        # check if we're loud, and record the time if this changes
        new_is_loud = variance > threshold
        if is_loud != new_is_loud:
            result.append((sample_time, new_is_loud))
        is_loud = new_is_loud

    return result

def play_sentence(wav_path):
    loud_times = get_loud_times(wav_path)
    pygame.mixer.music.load(wav_path)

    start_time = time.time()
    pygame.mixer.music.play()

    for (t, is_loud) in loud_times:
        # wait until the time described by this entry
        sleep_time = start_time + t - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)

        # do whatever
        print 'loud' if is_loud else 'quiet'

play_sentence("public/sounds/88miles.wav")