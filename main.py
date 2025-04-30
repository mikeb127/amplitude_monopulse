import time
import numpy as np
import adi

offset_angle = 10
hp_beamwidth = 80

# Quick and dirty median queue for filtering.
class MedianQueue:

    def __init__(self, max_length):

        self.values = []
        self.max_length = max_length

    def add(self, value):

        self.values.append(value)
        if len(self.values) > self.max_length:
            self.values.pop(0)

    def get_median(self):

        ret_vals = self.values.copy()
        ret_vals.sort()
        return ret_vals[int(len(self.values)/2)]


my_queue = MedianQueue(5)

sample_rate = 20e6 # Hz
center_freq = 2.395e9 # Hz - 2.395 ghz for test
NumSamples = 2**12
rx_mode = "manual"  # can be "manual" or "slow_attack"
rx_gain0 = 30
rx_gain1 = 30

sdr = adi.ad9361(uri='ip:192.168.2.1')
sdr.rx_enabled_channels = [0, 1]
##sdr.tx_enabled_channels = [0]
sdr.gain_control_mode_chan0 = 'manual'
sdr.rx_hardwaregain_chan0 = rx_gain0 # dB
sdr.gain_control_mode_chan1 = 'manual'
sdr.rx_hardwaregain_chan1 = rx_gain1 # dB
sdr.rx_lo = int(center_freq)
sdr.sample_rate = int(sample_rate)
sdr.rx_rf_bandwidth = int(sample_rate)
sdr.rx_buffer_size = int(NumSamples)
sdr._rxadc.set_kernel_buffers_count(1)   # set buffers to 1 (instead of the default 4) to avoid stale data on Pluto


# Simulated IQ data generation with 50° 3 dB beamwidth
def generate_iq_data(true_angle, num_samples=1000, noise_level=0.05, beamwidth_3db=hp_beamwidth):
    """
    Simulate IQ data for two antennas with 10° offset and 50° 3 dB beamwidth.
    true_angle: Angle of arrival in degrees
    beamwidth_3db: 3 dB beamwidth in degrees
    """

    # Currently called every calculation where it doesn't need to be. Will stop repetitive calls for performance at
    # some point, but letting Grok cook for now.

    # Antenna positions
    theta1 = np.radians(offset_angle)  # Antenna 1 at +10°
    theta2 = np.radians(-1 * offset_angle)  # Antenna 2 at -10°
    target_theta = np.radians(true_angle)

    # Gaussian beam pattern: exp(-theta^2 / (2 * sigma^2))
    # Full width half maximum = 2sqrt(2 ln 2)sigma
    # re-arranging this give the equation below:
    sigma = np.radians(beamwidth_3db / 2) / np.sqrt(2 * np.log(2))  # Sigma for 3 dB point

    norm_factor = 1 / (sigma * np.sqrt(2 * np.pi))

    # Signal amplitude based on Gaussian pattern
    amp1 = norm_factor * np.exp(-((target_theta - theta1) ** 2) / (2 * sigma ** 2))
    amp2 = norm_factor * np.exp(-((target_theta - theta2) ** 2) / (2 * sigma ** 2))

    # Generate complex IQ samples with noise
    iq1 = amp1 * np.ones(num_samples) + noise_level * (np.random.randn(num_samples) + 1j * np.random.randn(num_samples))
    iq2 = amp2 * np.ones(num_samples) + noise_level * (np.random.randn(num_samples) + 1j * np.random.randn(num_samples))

    return iq1, iq2, amp1, amp2  # Return amplitudes for debugging


# Calculate angle of arrival from IQ data
def calculate_aoa(iq1, iq2, beamwidth_3db=hp_beamwidth):
    """
    Compute angle of arrival from IQ data using amplitude monopulse.
    iq1, iq2: Complex IQ samples from antenna 1 and 2
    antenna_offset_deg: Offset of each antenna from boresight (degrees)
    beamwidth_3db: 3 dB beamwidth of each antenna (degrees)
    """

    # Compute amplitudes from IQ data
  #  amp1 = np.abs(iq1)
  #  amp2 = np.abs(iq2)
    amp1 = np.sqrt(np.power(iq1.real, 2) + np.power(iq1.imag, 2))
    amp2 = np.sqrt(np.power(iq2.real, 2) + np.power(iq2.imag, 2))

    amp1_mean = np.mean(amp1)
    amp2_mean = np.mean(amp2)

    # Sum and difference signals
    sum_signal = amp1_mean + amp2_mean
    diff_signal = amp1_mean - amp2_mean

    # Error signal (normalized difference)
    error_signal = diff_signal / sum_signal if sum_signal != 0 else 0

    # Calibrate slope: Compute error signal at 10° to determine scaling
    # For Gaussian pattern, error_signal at 10° is smaller due to wide beamwidth
    # TODO: Move this outside the loop.
    iq1_cal, iq2_cal, amp1_cal, amp2_cal = generate_iq_data(10, num_samples=1000, beamwidth_3db=beamwidth_3db)
   # amp1_cal_mean = np.mean(np.abs(iq1_cal))
   # amp2_cal_mean = np.mean(np.abs(iq2_cal))
    amp1_cal_mean = np.mean(np.sqrt(np.power(iq1_cal.real,2) + np.power(iq1_cal.imag,2)))
    amp2_cal_mean = np.mean(np.sqrt(np.power(iq2_cal.real,2) + np.power(iq2_cal.imag,2)))
    error_cal = (amp1_cal_mean - amp2_cal_mean) / (amp1_cal_mean + amp2_cal_mean)
    slope_factor = offset_angle / error_cal  # Scale so error_signal at 10° maps to 10°

    # Map error signal to angle
    aoa = error_signal * slope_factor

    return aoa, error_signal, slope_factor

'''Collect Data'''
for i in range(20):
    # let Pluto run for a bit, to do all its calibrations, then get a buffer
    data = sdr.rx()

# Let's calculate angle as below:
while True:

    data = sdr.rx()
    iq1 = data[0]
    iq2 = data[1]

    # Calculate AoA
    estimated_angle, error, slope = calculate_aoa(iq1, iq2)
    my_queue.add(estimated_angle)
    print(f"Estimated Angle: {my_queue.get_median():.2f}°")
    time.sleep(.025)# Just add sleep to save console overloading

