# Contains variables and parameters related to the actual experiment, including test frequency, run time, and any recorded data
import numpy as np

class Test: 

    #R_OFFSET = np.array([20.3, 20.3, 20.6, 20.3]);
    #R_OFFSET = np.zeros((1, 4)); 

    def __init__(self, IAController, runT, numChips):

        self.manager = IAController

        # Test setup parameters
        self.Fc = 10000
        self.Fm = 0.2
        self.runT = runT # In minutes
        self.delay = int(1000/self.Fm) # In seconds
        self.setLength(runT)
        self.collectedMeasurements = 0
        self.numChips = numChips
        self.N_channels = numChips*6;

     # Test data output parameters
        self.rawDataMatrix = []
        self.Z = np.empty((self.N_meas, self.N_channels))
        self.Z[:] = np.NaN
        self.t = np.zeros(self.N_meas)
        self.baseline = np.ones(self.N_channels)*200
        self.REI = np.zeros((self.N_meas, self.numChips))

        self.ZMean = np.zeros(self.N_channels)

        # Flags
        self.isInitialized = False
        self.bloodHasEnteredChip = [False, False]

        # Calibration Data
        self.M_calib = np.zeros((1, 12));
        
    def setLength(self, T):
        self.runT = T;
        self.N_meas = int(T*self.Fm*60) + 1
        
    def updateLength(self, addT):
        self.runT += addT;
        addedN_meas = int(addT*self.Fm*60) + 1
        self.N_meas += addedN_meas
        
        # Update length of current variables
        temp = np.empty((addedN_meas, self.N_channels))
        temp[:] = np.NaN
        self.Z = np.append(self.Z, temp, axis = 0)
        temp = np.zeros(addedN_meas)
        self.t = np.append(self.t, temp, axis = 0)
        temp = np.zeros((addedN_meas, self.numChips))
        self.REI = np.append(self.REI, temp, axis = 0)
        
    def trimData(self):
        N = self.N_meas -2
        self.t = self.t[0:N]
        self.Z = self.Z[0:N, :]
        self.REI = self.REI[:, 0:N]
        