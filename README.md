# amplitude_monopulse
Azimuth Monopulse Tracking with Pluto SDR

This repo contains the python code necessary to run your Pluto SDR (must have 2 RX channels available, so modified Rev-C) as an amplitude comparison monopulse system.

![IMG_0820](https://github.com/user-attachments/assets/68d87f3b-1067-481e-a981-758b06727614)

Design parameters:
Antennas - Helical antennas with a gain of roughly 6.5db and a HPBW of 80 degrees. Mounted 10 degrees/-10 degrees off boresight.

If you want to modify the included hardware design (you probably should, the HPBW is too wide to work really well), you will need to change the following parameters at the top of the script:
1. offset_angle - this is the offset angle/beam squint for the two antennas in your monopulse system. Change to whatever angle you have them mounted at.
2. hp_beamwidth - this is the -3db beamwidth of an individual antenna in the system. Change to match whatever the HPBW of your chosen antennas are.

Note here: Antenna gain patterns are modelled as Gaussian approximation only really considering the main lobe. This may not be appropriate in all cases (particularly with Yagis). I will implement more models in the future for more accurate approximations.

Note on the note: Cosine approximation works better for these antennas (even if they are still very noisy). Updates to the code coming.
