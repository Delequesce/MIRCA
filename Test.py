# Contains variables and parameters related to the actual experiment, including test frequency, run time, and any recorded data
import numpy as np

class Test: 

    #R_OFFSET = np.array([20.3, 20.3, 20.6, 20.3]);
    #R_OFFSET = np.zeros((1, 4)); 

    def __init__(self, IAController, runT, N_channels):

        self.manager = IAController

        # Test setup parameters
        self.Fc = 10000
        self.Fm = 0.2
        self.runT = runT # In minutes
        self.delay = int(1000/self.Fm) # In seconds
        self.N_meas = int(self.runT*self.Fm*60) + 1
        self.collectedMeasurements = 0
        self.N_channels = N_channels

     # Test data output parameters
        self.N_channels = N_channels
        self.rawDataMatrix = []
        self.Z = np.empty((self.N_meas, N_channels))
        self.Z[:] = np.NaN
        self.t = np.zeros(self.N_meas)

        self.ZMean = np.zeros(N_channels)

        # Flags
        self.isInitialized = False

        # Calibration Data
        self.M_calib = np.zeros((1, 12));
