import time
from Fluigent.SDK import fgt_detect, fgt_init, fgt_close, fgt_set_power, fgt_get_power
from Fluigent.SDK import fgt_get_controllersInfo, fgt_calibratePressure
from Fluigent.SDK import fgt_get_pressureChannelCount, fgt_get_pressureChannelsInfo
from Fluigent.SDK import fgt_set_pressure, fgt_get_pressure, fgt_get_pressureRange

class PumpController:
    
    def __init__(self, parent):
        self.parent = parent;
        self.pressureIndices = [];
        self.waitTime = 0
        self.refTime = time.perf_counter();
        self.SNs = [];
        
        self.isCalibrated = False # True once pump has been calibrated
        self.isAvailable = True # True whenever pump is not powering on or calibrating
        self.allSet = False # True when both of the above are true and pump is ready for testing
    
    def locateAndPower(self):
        # Locate and power on pump
        SNs, types = fgt_detect()
        if len(SNs) < 1:
            self.parent.statusQueue.put('No pump detected')
            
        for i, sn in enumerate(SNs):
            self.parent.statusQueue.put('Detected instrument at index: {}, ControllerSN: {}, type: {}'\
              .format(i, sn, str(types[i])))
            if fgt_get_power(i) == 0:
                fgt_set_power(i, 1)
                self.waitTime = 15;
                self.refTime = time.perf_counter();
                self.parent.statusQueue.put("Powering On Pump")
                self.isAvailable = False
            else:
                self.getPressureChannels()
                self.calibratePressureChannels()
        self.SNs = SNs;
        
    def getPressureChannels(self):
        pressureInfoArray = fgt_get_pressureChannelsInfo()
        for i, pressureInfo in enumerate(pressureInfoArray):
            self.pressureIndices.append(i)
            self.parent.statusQueue.put(f'Pressure channel detected at index {i}')
            
    def calibratePressureChannels(self):
        for i in self.pressureIndices:
            fgt_calibratePressure(i); # This takes 8 seconds
            self.waitTime = 8;
            self.refTime = time.perf_counter();
        self.isCalibrated = True;
        self.isAvailable = False
        self.parent.statusQueue.put("Calibrating Pump")
    
    def setPressure(self, channelList, p):
        N = len(self.pressureIndices)
        for chan in channelList:
            if N >= chan: # Make sure enough pumps are available for each chip
                msg = fgt_set_pressure(chan, p);
            else:
                msg = "Not enough pressure channels available"
        return msg
    
    def isReady(self):
        self.isAvailable = time.perf_counter() > self.refTime+self.waitTime
        return self.isAvailable
    
    def closeSession(self):
        fgt_close()
            
            
        