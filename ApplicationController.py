from MainGUI import *
from IAController import *
from PumpController import *
import threading, queue
import tkinter as tk
import time

class ApplicationController:
    
    def __init__(self, root):

        # Create queues 
        self.statusQueue = queue.Queue()
        self.impedanceQueue = queue.Queue()
        self.pumpQueue = queue.Queue()

        # Create Main Objects
        self.gui = MainGUI(self, root); # GUI Object
        self.root = root
        self.IAController = IAController(self);
        self.PumpController = PumpController(self);
        self.PumpController.locateAndPower();
        self.IAProc = None

        # Assign Channels
        self.chip1Channels, self.chip2Channels = self.assignChannels();

        # Polling Variables
        self.pollTask = None
        self.pollCounter = 0;

        self.nextPhase = "Baseline"
        self.t_phaseStart = float('inf')
        self.t_p = []; self.p = []
        self.bn = []

    # Assign Channels
    def assignChannels(self):
        chip1Channels = []
        ## Chip 1
        chip1Channels.append(np.array([0, 0, 1, 0, 1, 0], dtype=np.int8)) # Channel 1: A4 A2
        chip1Channels.append(np.array([0, 0, 1, 1, 0, 0], dtype=np.int8)) # Channel 2: A4 A1
        chip1Channels.append(np.array([0, 1, 1, 1, 0, 0], dtype=np.int8)) # Channel 3: A6 A1
        chip1Channels.append(np.array([0, 1, 1, 0, 0, 0], dtype=np.int8)) # Channel 4: A6 A0
        chip1Channels.append(np.array([1, 1, 1, 0, 0, 0], dtype=np.int8)) # Channel 5: A7 A0
        chip1Channels.append(np.array([1, 1, 1, 1, 1, 0], dtype=np.int8)) # Channel 6: A7 A3
        
        ## Chip 2
        chip2Channels = []
        chip2Channels.append(np.array([1, 1, 0, 0, 1, 1], dtype=np.int8)) # Channel 1: A3 A6
        chip2Channels.append(np.array([0, 0, 0, 0, 1, 1], dtype=np.int8)) # Channel 2: A0 A6
        chip2Channels.append(np.array([0, 0, 0, 1, 1, 1], dtype=np.int8)) # Channel 3: A0 A7
        chip2Channels.append(np.array([1, 0, 0, 1, 1, 1], dtype=np.int8)) # Channel 4: A1 A7
        chip2Channels.append(np.array([1, 0, 0, 1, 0, 1], dtype=np.int8)) # Channel 5: A1 A5
        chip2Channels.append(np.array([0, 1, 0, 1, 0, 1], dtype=np.int8)) # Channel 6: A2 A5

        return chip1Channels, chip2Channels
    
    def newQC(self, chipVars):
        # Set Channel Information
        self.chipVars = chipVars
        self.setChannels()
        # Starts IA Controller run
        IAController = self.IAController
        IAController.initTest(0.5, self.digLevels, self.channelList)
        self.gui.reinitPlot(6, 6)
        # Starts data collection
        self.IAController.QC = True # Tells controller qulaity check is running
        self.IAProc = threading.Thread(target=IAController.runTest, args=[time.perf_counter()])
        self.IAProc.start()

    # Initiates a new test based on testDialog window
    def startBaseline(self, chipVars, saveDataFilePath = None):
        # Delete testDialog
        del self.testDialog
        # Parameters from testDialog
        self.nextPhase = "Perfusion"
        self.chipVars = chipVars
        self.saveDataFilePath = saveDataFilePath
        self.setChannels()
        
        # Set Pump Command Schedule
        pumpText = "0:200"
        run_T = 2;
        self.pumpTextDecode(pumpText)
       
        # Starts IA Controller run
        IAController = self.IAController
        IAController.initTest(run_T, self.digLevels, self.channelList, self.numChips, saveDataFilePath)
        self.gui.reinitPlot(6, 6)

        # Starts data collection
        self.t_phaseStart = time.perf_counter()
        self.CheckAndSetPressure() # Immediately check pump schedule for start pressure
        self.IAProc = threading.Thread(target=IAController.runTest, args=[self.t_phaseStart])
        self.statusQueue.put("Running Test...")
        self.IAProc.start()
        # After this, main loop returns to gui control and polling while IAController collects data.
        # IA Controller will initiate next test phase by calling continueTest()
        return

    def continueTest(self):
        # Parameters
        pumpText = "0:200"
        run_T = 15;
        
        # Update nextPhase
        self.nextPhase = "Completion"

        # Update activeTest with new runTime
        self.IAController.updateTest(run_T)
        
        # Set Pump Command Schedule
        self.pumpTextDecode(pumpText)
        self.t_phaseStart = time.perf_counter()
        self.CheckAndSetPressure()

        # Release break on IAController
        self.IAController.testPaused = False
        return

    def stopTest(self, reason = None):
        self.gui.btn_start['text'] = "New Test"
        self.isFinished = True
        self.nextPhase = "Baseline"
        # self.PumpController.setPressure(0, 0); # Comment out for microscope imaging
        self.IAController.stopTest()
        # Log appropriate status to window
        if reason == "Connection":
            self.statusQueue.put("Sensor misaligned or not connected. Please check connection and retry")
        elif reason == "Canceled":
            self.statusQueue.put("Test canceled by user")
        elif reason == "Completed":
            self.statusQueue.put("Test Complete")
            self.IAController.printREI()
            #self.IAController.calculateStats()
        elif reason == "QC":
            # Determine if system is working properly
            if self.IAController.finishQC():
                self.statusQueue.put("Quality Check Complete. No issues detected.")
            else:
                self.statusQueue.put("Quality Check Failed. Please check system and try again.")
        
        # Let IAProc Finish its routine
        if self.IAProc:
            #print("IA Proc Join")
            self.IAProc.join()

    def polling(self, pollState):
        
        # Check for collected Measurements
        while self.impedanceQueue.qsize():
            try:
                dataTuple = self.impedanceQueue.get(0);
                self.gui.updatePlot(*dataTuple)
            except queue.Empty:
                pass

        # Check for status messages
        while self.statusQueue.qsize():
            try:
                msg = self.statusQueue.get(0);
                self.gui.writeStatus(msg)
            except queue.Empty:
                pass
            
        # Calibrate Pump        
        # If pump is not available, check every second to see if it is
        if not self.PumpController.isAvailable and self.pollCounter % 10 < 1:
            if self.PumpController.isReady():
                if not self.PumpController.isCalibrated:
                    self.PumpController.calibratePressureChannels()
                else:
                    self.PumpController.allSet = True
                    self.statusQueue.put("Pump Ready")
                    
        # Check time for pump scheduling
        if self.pollCounter % 5 < 1 and self.PumpController.allSet:
            if len(self.t_p) > 0:
                self.CheckAndSetPressure()
            elif len(self.bn) > 0:
                self.bloodNeedlePressureChange()
        
        
        # Polling repeats every 100ms
        self.pollTask = self.root.after(100, lambda: self.polling(pollState))
        self.pollCounter += 1

    def setChannels(self):
        digLevels = []
        channelList = []
        numChips = 0;
        if self.chipVars[0].get() == 1:
            for chan in self.chip1Channels:
                digLevels.append(chan)
            channelList += [0, 1, 2, 3, 4, 5]
            numChips +=1

        if self.chipVars[1].get() == 1:
            for chan in self.chip2Channels:
                digLevels.append(chan)
            channelList += [6, 7, 8, 9, 10, 11]
            numChips +=1

        self.digLevels = digLevels
        self.channelList = channelList
        self.numChips = numChips
        self.desiredPressureChannels = range(round(len(channelList)/6))
        return
    
    # Opens new testDialog and returns to main loop to wait for callback
    def openTestDialog(self):
        if not self.nextPhase == "Completion":
            self.testDialog = TestDialog(self, self.nextPhase)
        else:
            self.stopTest()
        return

    def openQCDialog(self):
        self.testDialog = QCDialog(self)
        return
    
    def pumpTextDecode(self, pumpText):
        self.t_p = []; self.p = [];
        for command in pumpText.split("\n"):
            b = command.split(":")
            self.t_p.append(60*float(b[0])); self.p.append(float(b[1]));
            
        return
    
    # Sets pressure to 100mBar on a given pump when 
    def bloodNeedlePressureChange(self):
        self.PumpController.setPressure(self.bn, 100)
        self.bn = []
    
    def CheckAndSetPressure(self):
        #print(f"Time: {time.perf_counter() - self.t_phaseStart}")
        #print(f"Target: {self.t_p[0]}")
        if time.perf_counter() - self.t_phaseStart > self.t_p[0]:
            msg = self.PumpController.setPressure(self.desiredPressureChannels, self.p[0])
            self.statusQueue.put(str(msg))
            self.t_p.pop(0); self.p.pop(0);
            
    def setBaselineCollect(self, j):
        #self.baselineCollect[j] = True;
        self.IAController.baselineCount[j] = 1;

    def on_close(self):
        if tk.messagebox.askokcancel("Quit", "Do you want to quit the program?"):
            if self.pollTask:
                self.root.after_cancel(self.pollTask)
            self.PumpController.closeSession()
            self.IAController.onClose()
            self.gui.onClose()
            self.root.destroy()


# Main program execution
if __name__ == "__main__":
    root = tk.Tk()
    app = ApplicationController(root);
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    app.polling(0)
    # Let GUI run in UI mode
    app.root.mainloop()
