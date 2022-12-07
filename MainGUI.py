from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,  
NavigationToolbar2Tk)
from mpl_toolkits.axisartist.axislines import Subplot
from tkinter.scrolledtext import *
import tkinter as tk
import tkinter.ttk as ttk
import numpy as np
from TestDialog import *
from QCDialog import *

class MainGUI:
    # Class contains variables pertaining to the status window, data plot, and button callbacks. It also contains functions for updating
    # plots and labels which get called by the ApplicationController

    def __init__(self, appController, root):

        self.appController = appController;
        self.root = root
        self.labels = ['12um', '10um', '8um', '6um', '4um', '3um'];
        self.statusWindow, self.fr_left, self.btn_start = self.createTopWindow();
        self.fig, self.plot1, self.plot2, self.canvas = self.setUpVisualization();
    
    def onClose(self):
        return

    # Initializes plot
    def setUpVisualization(self):
        # Plot (8, 2.5)
        fig = Figure(figsize=(5.2, 3.9), dpi = 100)
        plot1 = fig.add_subplot(211, frame_on = False);
        plot2 = fig.add_subplot(212, frame_on = False);
        plot1.set_xlabel("Time (min)")
        plot1.set_ylabel("Impedance (kΩ)")
        plot1.set_title('Chip 1')
        plot2.set_xlabel("Time (min)")
        plot2.set_ylabel("Impedance (kΩ)")
        plot2.set_title('Chip 2')
        
        fig.set_tight_layout(True)

        # Visual Frame
        canvas = FigureCanvasTkAgg(fig, master = self.fr_left)
        canvas.draw()
        canvas.get_tk_widget().pack()
        
        # Resize window
        self.root.geometry("800x400")

        return fig, plot1, plot2, canvas

    # Creates the main window and all necessary components
    def createTopWindow(self):
        root = self.root
        root.title("MIRCA Interface")
        style = ttk.Style(root)
        root.tk.call('source', 'Azure-ttk-theme-main/azure.tcl')
        style.theme_use('azure')
        style.configure("AccentButton", foreground = 'white')

        root.rowconfigure(1, minsize = 400, weight=1)
        root.columnconfigure(0, minsize = 400, weight=1)

        # Create Frames
        fr_left = tk.Frame(root)
        fr_right = tk.Frame(root)

        fr_status = ttk.LabelFrame(fr_right, text = "Status Window")
        fr_button = tk.Frame(fr_right)
        
        fr_bloodNeedle = ttk.LabelFrame(fr_right, text="Has blood reached the needle?")
        
        # Create Status Window
        statusWindow = ScrolledText(fr_status, height = 13, width = 30, wrap = 'word', font=("Helvetica", 8))
        statusWindow.bind("<Key>", lambda e: "break") # Make Read-only

        # Create Buttons
        btn_start = ttk.Button(fr_button, text = "New Test", style = "AccentButton",
                                    command = self.startButtonCallback)
        btn_QC = ttk.Button(fr_button, text = "Quality Check", style = "AccentButton",
                                    command = self.qcCallback)
        
        needleVars = []
        for i in range(2):
            tempVar = tk.IntVar(value=0)
            needleVars.append(tempVar)
            ttk.Checkbutton(fr_bloodNeedle, text = f'Chip {i+1}', variable=tempVar,
                offvalue = 0, onvalue = 1, command = lambda j=i: self.bnToggle(j)).grid(
                row = 0, column = i, padx = 1, pady = 1);
                                                                
        
        ## Organize and Arrange Components
        fr_left.grid(row = 0, column = 0, padx = 2)
        fr_right.grid(row = 0, column = 1, padx = 2)

        # Right Side
        fr_button.grid(row = 0, column = 0, pady = 5)
        fr_status.grid(row = 1, column = 0, pady = 5)
        fr_bloodNeedle.grid(row = 2, column = 0, pady = 5)
        btn_start.grid(row = 0, column = 0)
        btn_QC.grid(row = 1, column = 0)
        statusWindow.pack()

        return statusWindow, fr_left, btn_start
    
    def reinitPlot(self, N_channels1, N_channels2):
        plot1 = self.plot1; plot2 = self.plot2;
        plot1.cla(); plot2.cla()
        for i in range(N_channels1):
            plot1.plot([], [], 'o-', label=self.labels[i], markersize=2)
        for i in range(N_channels2):
            plot2.plot([], [], 'o-', label=self.labels[i], markersize=2)
        self.lines1 = plot1.get_lines(); self.lines2 = plot2.get_lines();
        plot1.set_xlabel("Time (min)"); plot2.set_xlabel("Time (min)"); 
        plot1.set_ylabel("Impedance (kΩ)"); plot2.set_ylabel("Impedance (kΩ)")
        plot1.set_title("Chip 1"); plot2.set_title("Chip 2")
        #plot1.legend(loc='upper left'); #plot2.legend(loc='upper left')

    # Updates the plot with new data
    def updatePlot(self, xdata, ydata):
        #print(f"XData: {xdata}")
        #print(f"YData: {ydata}")
        # Update the Canvas with the new data 
        q = 0
        min1 = 200; min2 = 200; max1 = 0; max2 = 0;
        for l in self.lines1:
            d = ydata[q]
            mind = np.min(d);
            maxd = np.max(d);
            if mind < min1:
                min1 = mind;
            if maxd > max1:
                max1 = maxd;

            # Plot    
            l.set_xdata(xdata)
            l.set_ydata(d)
            q+=1
            
        for l in self.lines2:
            d = ydata[q]
            mind = np.min(d);
            maxd = np.max(d);
            if mind < min2:
                min2 = mind;
            if maxd > max2:
                max2 = maxd;
             # Plot
            l.set_xdata(xdata)
            l.set_ydata(d)
            q+=1
        

        self.plot1.set_xlim(-0.1, np.max(xdata)*1.1+0.1)
        self.plot1.set_ylim(min1-20, max1+20)
        #self.plot1.legend(handles = self.lines1, bbox_to_anchor=(1.2, 0),
                          #ncol = 1, fancybox=True, shadow=True)
        self.plot2.set_xlim(-0.1, np.max(xdata)*1.1+0.1)
        self.plot2.set_ylim(min2-20, max2+20)
        #self.plot2.legend(handles = self.lines2, loc='upper center', bbox_to_anchor=(0.5, 1.05),
                          #ncol = 3, fancybox=True, shadow=True)
        self.canvas.draw()

    # Writes to status window
    def writeStatus(self, status):
        numLines = int(self.statusWindow.index('end -1 line').split('.')[0])
        self.statusWindow.insert('end', status + '\n')
        self.statusWindow.yview('end')
        return
    
    # Start/Stop Button Callback
    def startButtonCallback(self):
        if self.btn_start['text'] == 'New Test':
            self.btn_start['text'] = "STOP"
            self.appController.openTestDialog()
        else:
            print("callback")
            self.btn_start['text'] = "New Test"
            self.appController.stopTest("Canceled")
            
    def qcCallback(self):
        self.appController.openQCDialog()
        return
    
    def bnToggle(self, j):
        print(j)
        self.appController.bn.append(j)
        self.appController.setBaselineCollect(j)