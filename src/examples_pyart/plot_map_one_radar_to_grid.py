"""
======================================
Map a single radar to a Cartesian grid
======================================

Map the reflectivity field of a single radar from Antenna coordinates to a
Cartesian grid.

"""
print (__doc__)

# Author: Jonathan J. Helmus (jhelmus@anl.gov)
# License: BSD 3 clause
# 2016.05.10 fvj tested. It works

import numpy as np
import matplotlib.pyplot as plt
import pyart

# read in the data
RADAR_PATH = '/data/pyart_examples/'
RADAR_FILE = '110635.mdv'

radar = pyart.io.read_mdv(RADAR_PATH+RADAR_FILE)

# mask out last 10 gates of each ray, this removes the "ring" around th radar.
radar.fields['reflectivity']['data'][:, -10:] = np.ma.masked

# exclude masked gates from the gridding
gatefilter = pyart.filters.GateFilter(radar)
gatefilter.exclude_masked('reflectivity')

# perform Cartesian mapping, limit to the reflectivity field.
grid = pyart.map.grid_from_radars(
    (radar,), gatefilters=(gatefilter, ),
    grid_shape=(1, 241, 241),
    grid_limits=((2000, 2000), (-123000.0, 123000.0), (-123000.0, 123000.0)),
    fields=['reflectivity'])

# create the plot
fig = plt.figure()
ax = fig.add_subplot(111)
ax.imshow(grid.fields['reflectivity']['data'][0], origin='lower')
plt.show()
