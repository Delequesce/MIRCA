import libm2k
import math, time, csv, queue
import numpy as np
from Test import *
import os
import matplotlib.pyplot as plt

class IAController:

    #R_OFFSET = np.array([0,0,0,0,0,0,0,0,0,0,0,0]);
    #M_calib = np.array([1,1,1,1,1,1,1,1,1,1,1,1]);
    R_OFFSET = np.array([1.1549, 1.2981, 1.4715, 1.1934, 1.0283, 0.7628,
                         1.1864, 1.4598, 1.7311, 1.5055, 1.3891, 0.8961])
    M_calib = np.array([94.9493, 95.2701, 95.5543, 95.1260, 94.7738, 94.3509,
                        95.1100, 95.6686, 96.1677, 95.8655, 95.7560, 94.5343])
    SAMPLESPERMEASUREMENT = 2**14 #(16384)
    WEIGHTS = np.array([0, 0.167, 0.188, 0.2, 0.215, 0.231])
    REPSPERTP = 2; # Number of repeated measurements taken per time point
    ENDTIME = 10; # Minutes after blood enters chip at which test ends

    def __init__(self, appController):

        self.appController = appController;
        self.root = self.appController.root
        self.impedanceQueue = self.appController.impedanceQueue
        self.statusQueue = self.appController.statusQueue
        self.activeTest = None

        # Connect to ADALM2000
        self.ctx=libm2k.m2kOpen()
        self.ain = None
        self.aout = None
        self.dig = None
        self.pwr = None
        if self.ctx is None:
            self.statusQueue.put("Connection Error: No ADALM2000 device available/connected to your PC.")
        else:
            self.ain, self.aout, self.dig, self.pwr = self.connectDevice(self.ctx);
        
        # CSV Write Parameters
        self.output_file = None

        # Flags
        self.runTask = None
        self.testPaused = False
        self.testFinished = False
        self.QC = False
        self.testInitialized = False
        self.needlePassed = [False, False]
        #self.baselineCollect = [False, False]
        
        # Times
        self.t_start = 0;
        self.t_s = 0;

        # Misc
        self.baselineCount = [-1, -1];
        self.currCount = 0
        self.currentPhase = "Baseline"


    # Connects to ADALM2000
    def connectDevice(self, ctx):

        # Get Pointers to peripherals
        ain = ctx.getAnalogIn()
        aout = ctx.getAnalogOut()
        pwr = ctx.getPowerSupply()
        dig = ctx.getDigital()

        ain.setSampleRate(15e6) # Samples one of every 5 DAC samples (could also decimate after)
        ain.setOversamplingRatio(1)
        ain.setRange(0, -5,5); ain.setRange(1, -5,5)
        ain.enableChannel(0, True); ain.enableChannel(1, True)

        aout.setOversamplingRatio(0, 1)

        pwr.enableChannel(0,True)
        pwr.enableChannel(1,True)
        pwr.pushChannel(0,5)
        pwr.pushChannel(1,-5)

        for i in range(16):
            dig.setDirection(i, 1)
        dig.enableAllOut(True)
        
        return ain, aout, dig, pwr

    # Runs once prior to baseline
    def initTest(self, runT, digLevels, channelList, numChips, saveDataFilePath = None):
        self.statusQueue.put("Initializing Test...")
        self.currentPhase = "Baseline"
        # Calibrate ADC and DAC
        print(f"ADALM Temperature: {self.ctx.calibrateFromContext()}")

        # Create Test Object
        self.digLevels = digLevels
        self.channelList = channelList
        self.runT = runT
        self.N_channels = numChips*6;
        activeTest = Test(self, runT, numChips)

        # Set file output params
        self.saveDataFilePath = saveDataFilePath
        if saveDataFilePath:
            self.output_file = open(saveDataFilePath, 'w', newline = '')

        # Turn on power
        self.pwr.enableChannel(0,True)
        self.pwr.enableChannel(1,True)

        # Create Test Signal
        Fs_out = 75e6;  # Output Sample Rate
        aout = self.aout
        aout.setOversamplingRatio(0,1)
        aout.setSampleRate(0, Fs_out)

        # Create Buffer size of measurement window
        buff_size = int(1e-3*Fs_out);
        t_out = np.array(range(buff_size))/Fs_out
        Vinput = 1000e-3
        buffer = Vinput*np.sin(2*np.pi*activeTest.Fc*t_out) # 1V, 10kHz
        #plt.plot(buffer)
        #plt.show()
        aout.setCyclic(True)
        
        # Write Header Row
        if saveDataFilePath:
            csv_writer = csv.writer(self.output_file, delimiter = ' ')
            csv_writer.writerow(["Time", "Z", "REI"])
        
        # Store necessary local variables in object
        self.buffer = buffer
        
        aout.enableChannel(0, True)
        aout.push(0, buffer)
        activeTest.isInitialized = True
        self.testInitialized = True
        self.testFinished = False
        self.needlePassed = [False, False]
        
        self.baselineCount = [-1, -1];
        self.currCount = 0
        self.FSM_State = 0
        self.activeTest = activeTest
        self.statusQueue.put("Initialization Complete")
        return

    def runTest(self, t0):
        
        # State Machine
        FSM_State = self.FSM_State
        activeTest = self.activeTest
        t_m = time.perf_counter() - t0

        if FSM_State == 0:
            self.t_start = t_m
            FSM_State = 1

        if FSM_State == 1:
            # Determine if samples can be collected
            # If so, collect and store samples
            #if activeTest.delay - 2000 > 1e3*(t_m - self.t_start):
            if self.currCount < self.REPSPERTP: 
                self.activeTest.rawDataMatrix = self.collectData(activeTest)
                # Save first collection time
                activeTest.t[activeTest.collectedMeasurements] = round(self.t_start/60, 2)
                # Proceed to data processing
                self.FSM_State = 2
                self.runTask = self.root.after(100, lambda: self.runTest(t0))
            else:
                # Move on to storage
                self.currCount = 0
                FSM_State = 3

        if FSM_State == 2:
            # Extract parameters from data
            self.processData(activeTest, activeTest.collectedMeasurements, self.currCount)
            self.currCount +=1
            # Go back to collection state
            self.FSM_State = 1
            self.runTask = self.root.after(100, lambda: self.runTest(t0))

        if FSM_State == 3:
            activeTest.collectedMeasurements += 1
            self.sendAndStore(activeTest, activeTest.collectedMeasurements)
            FSM_State = 4

        if FSM_State == 4:
            if activeTest.collectedMeasurements < activeTest.N_meas:
                t_adj = round(activeTest.delay - 1e3*(t_m - self.t_start))
                self.FSM_State = 0
                self.runTask = self.root.after(t_adj, lambda: self.runTest(t0))
            else:
                # Get Stop time
                self.t_s = t_m;
                # Pause test and open next dialog box
                FSM_State = 5;
                self.testPaused = True
                
                # Calculate Baseline for Baseline Test
#                 if self.currentPhase == "Baseline":
#                     n = activeTest.collectedMeasurements
#                     for i in range(activeTest.numChips):
#                         b = np.arange((i)*6, (i+1)*6)
#                         Z_slice = activeTest.Z[n-4:n-1, b]
#                         self.activeTest.baseline[b] = np.mean(Z_slice, axis = 0)
#                     self.statusQueue.put(f"Baseline: {self.activeTest.baseline}")
                if not self.QC and not self.currentPhase == "Perfusion":
                    self.appController.openTestDialog()
                    
        if FSM_State == 5:
            # Maintain holding pattern (pause recording) until appropriate callback changes pause boolean
            if self.testFinished:
                self.appController.stopTest("Completed")
            elif self.QC:
                self.appController.stopTest("QC")
            else:
                if self.testPaused:
                    self.FSM_State = 5
                    self.runTask = self.root.after(100, lambda: self.runTest(t0))
                else:
                    # Resume testing with appropriate timing
                    self.FSM_State = 0
                    self.runTask = self.root.after(100, lambda: self.runTest(time.perf_counter() - self.t_s))
            
            
    def collectData(self, activeTest):
        dataOut = []
        ain = self.ain
        dig = self.dig

        # Loop through active channels and collect data for each
        for i in self.channelList:

            # Set MUX Output Values to Switch Active Channels
            for j in range(6):
                dig.setValueRaw(j, bool(self.digLevels[i][j]))
            
            # Acquire data from buffer
            ain.startAcquisition(self.SAMPLESPERMEASUREMENT)
            dataOut.append(ain.getSamples(self.SAMPLESPERMEASUREMENT));
            ain.stopAcquisition()
        
        #print("Collected")
        return dataOut

    def processData(self, activeTest, n, j):
        i = 0
        for chan in self.channelList:
            vin = np.array(activeTest.rawDataMatrix[i][0]);
            vout = np.array(activeTest.rawDataMatrix[i][1]);
            
            # Window for exactly 10 periods (based on 15MHz ain sampling)
            vin = vin[0:15000]
            vout = vout[0:15000]
            
            p = np.zeros(2, dtype=np.int16) # index for max of fft 
        
            FVin = np.abs(np.fft.rfft(vin)); FVout = np.abs(np.fft.rfft(vout))
            
            # Find index of FFT Max
            p[0] = 2+np.argmax(FVin[2:])
            p[1] = 2+np.argmax(FVout[2:])
            #print(f"p = {p}")
        
            if (p[0] != p[1] or (p[0] == 0 and p[1] == 0)):
                self.statusQueue.put("Error: FFT peaks misaligned")  

            # Calculate Output Parameters
            temp = activeTest.Z[n][i]
            if not np.isnan(temp):
                activeTest.Z[n][i] = ((FVin[p[0]]/FVout[p[1]]*self.M_calib[chan]-self.R_OFFSET[chan]) + temp*j)/(j+1);
            else:
                activeTest.Z[n][i] = FVin[p[0]]/FVout[p[1]]*self.M_calib[chan]-self.R_OFFSET[chan];
            #print(f"Channel {chan}: {activeTest.Z[n][i]}")
            i+=1
            
        #print("Processed")
        return

    def sendAndStore(self, activeTest, n):

        # Get data in convenient format
        xdata = np.single(activeTest.t[0:n])
        ZData = np.transpose(activeTest.Z)[:, 0:n].tolist()
        
        # Calculate baseline and find when blood enters chip
        if self.currentPhase == "Perfusion":
            for i in range(activeTest.numChips):
                c = self.baselineCount[i]
                print(c)
                if not c > 0: # Starts at 1 when set
                    continue
                if not c > 10:
                    self.baselineCount[i] +=1
                    continue
                b = np.arange((i)*6, (i+1)*6)
                Z_slice = activeTest.Z[n-5:n-1, b]
                bb = np.mean(Z_slice, axis = 0)
                self.activeTest.baseline[b] = bb
                self.statusQueue.put(f"Chip {i+1} Baseline: {bb}")
                # Reset counter
                self.baselineCount[i] = -1
                self.needlePassed[i] = True
            # Check if blood has entered the chip
            self.activeTest = self.hasBloodEnteredChip(activeTest, n)

        
        # Add plot data to data queue
        self.impedanceQueue.put((xdata, ZData))

        # Write data continuously to file
        output_file = self.output_file
        if output_file:
            output_file = open(output_file.name, 'a')
            csv_writer = csv.writer(output_file, delimiter = ' ')
            csv_writer.writerow([activeTest.t[n-1], activeTest.Z[n-1], activeTest.REI[n-1]]);
            output_file.close()

    def hasBloodEnteredChip(self, activeTest,n):
        for i in range(activeTest.numChips):
            if not self.needlePassed[i]:
                continue
            b = np.arange(i*6, (i+1)*6)
            REI_current = sum(activeTest.Z[n-1, b]/activeTest.baseline[b] * self.WEIGHTS);
            activeTest.REI[n-1, i] = REI_current
            if not activeTest.bloodHasEnteredChip[i]:
                #REI_prev = activeTest.REI[n-2, i]
                #REI_change = (REI_current-REI_prev)/REI_prev
                REI_change = REI_current-1; # Deviation from baseline
                if REI_change > 0.005: # 0.5% change
                    activeTest.bloodHasEnteredChip[i] = True
                    # Set end
                    currTime = n/12
                    activeTest.setLength(self.ENDTIME + currTime)
                    self.statusQueue.put(f"Blood detected on chip {i+1}")
    
        # Update variable in Test Object
        return activeTest

    def stopTest(self):
        self.testFinished = True
        self.FSM_State = 6 # Non-existant state that stops machine
        #print("IA Test Stopping")
        
        if self.testInitialized:
            self.aout.cancelBuffer()
            self.ain.stopAcquisition()
            self.aout.enableChannel(0, False)
            #print("Check good")

    def printREI(self):
        self.activeTest.trimData()
        self.statusQueue.put(f" REI = {self.activeTest.REI[-1, :]}")
        
        
    def calculateStats(self):
        x1 = self.activeTest; t = x1.t;
        for i in range(x1.Z.shape[1]):
            ZMean = round(np.mean(x1.Z[:, i]), 4); Zstd = round(np.std(x1.Z[:, i]), 4)

            #self.statusQueue.put(f"Z = {ZMean}+{Zstd}")
            x1.ZMean[i] = ZMean;
        return x1.ZMean

    def updateTest(self, T):
        self.currentPhase = "Perfusion"
        self.activeTest.updateLength(T)
        
        return
    
    def finishQC(self):
        self.QC = False # Turns off flag for next test
        ZMean = self.calculateStats()
        standards = np.array([33.95, 51.02, 80.30, 95.10, 123.49, 139.32, 33.94, 50.92, 80.19, 94.95, 123.5, 139.19])
        # Check rms channel error
        i = 0;
        j = 0;
        rmsd = 0;
        for chan in ZMean:
            if not np.isnan(chan):
                rmsd += (chan-standards[i])**2
                j+=1
            i+=1
        rmsd = np.sqrt(rmsd/j)
        print(f"RMSD = {np.round(rmsd, 2)}kOhms")
        return (rmsd < 3)


    def onClose(self):
        if self.runTask:
            self.appController.root.after_cancel(self.runTask)
        if self.ctx:
            self.pwr.enableChannel(0, False)
            libm2k.contextClose(self.ctx)