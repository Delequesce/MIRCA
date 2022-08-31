import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename

class TestDialog:

    def __init__(self, appController, phase):

        self.appController = appController;
        self.root = appController.root;

        self.saveDataFilePath = None
        if phase == "Baseline":
            self.tdWindow, self.btn_start, self.ent_filePathIndicator, self.str_runT, \
                           self.chipVars, self.pumpText = self.createStartWindow(self.root, phase)
        else:
            self.tdWindow, self.btn_start, self.str_runT, self.pumpText = self.createContinueWindow(self.root, phase)

    # Creates Baseline window
    def createStartWindow(self, root, phase):
        tdWindow = tk.Toplevel(root)
        tdWindow.title(phase)

        # Create Frames
        fr_params = ttk.LabelFrame(tdWindow, text = "Test Parameters")
        fr_chipSelect = tk.Frame(fr_params)
        fr_button = tk.Frame(tdWindow)
        fr_pump = ttk.LabelFrame(tdWindow, text = "Pump Schedule \n(Time (min):Pressure(mBar))")

        # Set up run time entry and variable
        str_runT = tk.StringVar(value = "3")
        ent_runT = ttk.Entry(fr_params, textvariable = str_runT, width = 5)
        lbl_runT = ttk.Label(fr_params, text = "Run Time (min)")

        # Filepath
        lbl_filePathSelect = ttk.Label(fr_params, text="File Path")
        ent_filePathIndicator = ttk.Entry(fr_params, width = 30)
        btn_filePathSelect = ttk.Button(fr_params, text="Browse", style="AccentButton",
                                    command = self.filePathSelectCallback)
        
        # Pump Command Window
        pumpText = tk.Text(fr_pump, width = 10, height = 5)
        pumpText.insert(tk.END, "0:100")

        # Create Buttons
        btn_start = ttk.Button(fr_button, text = "START TEST", style = "AccentButton",
                                command = self.startButtonCallback)

        btn_cancel = ttk.Button(fr_button, text = "CANCEL", style = "AccentButton",
                                    command = self.cancelButtonCallback)

        # Create checkboxes and store variables
        chipVars = []
        for i in range(2):
            tempVar = tk.IntVar(value=1);
            chipVars.append(tempVar);
            ttk.Checkbutton(fr_chipSelect, text=f'Chip {i+1}',variable=tempVar, onvalue=1, offvalue=0).grid(row = 0, column = i, padx = 1, pady = 1)

        # Organize and Arrange Components
        # Parameter Frame
        # Row 0
        fr_params.grid(row = 0, column = 0, pady = 5)
        lbl_runT.grid(row = 0, column = 0)
        ent_runT.grid(row = 0, column = 1)
        fr_chipSelect.grid(row = 0, column = 2, pady = 5)
        # Row 1
        lbl_filePathSelect.grid(row = 1, column = 0)
        ent_filePathIndicator.grid(row = 1, column = 1, columnspan = 2)
        btn_filePathSelect.grid(row = 1, column = 3)

        # Pump Frame
        fr_pump.grid(row = 0, column = 1, rowspan = 2)
        pumpText.grid(row = 0, column = 0)

        # Button Frame
        fr_button.grid(row = 1, column = 0, pady = 5)
        btn_start.grid(row = 0, column = 0, padx = 2)
        btn_cancel.grid(row = 0, column = 1, padx = 2)


        # Size and open window
        # Center window
        w = tdWindow.winfo_reqwidth()
        h = tdWindow.winfo_reqheight()
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws/2) - (w/2)-250
        y = (hs/2) - (h/2)
        tdWindow.geometry('+%d+%d' % (x, y))
        
        return tdWindow, btn_start, ent_filePathIndicator, str_runT, chipVars, pumpText
    
    # Creates Perfusion window
    def createContinueWindow(self, root, phase):
        tdWindow = tk.Toplevel(root)
        tdWindow.title(phase)

        # Create Frames
        fr_params = ttk.LabelFrame(tdWindow, text = "Test Parameters")
        fr_chipSelect = tk.Frame(tdWindow)
        fr_button = tk.Frame(tdWindow)
        fr_pump = ttk.LabelFrame(tdWindow, text = "Pump Schedule \n(Time(min):Pressure(mBar))")

        # Set up run time entry and variable
        str_runT = tk.StringVar(value = "20")
        ent_runT = ttk.Entry(fr_params, textvariable = str_runT, width = 5)
        lbl_runT = ttk.Label(fr_params, text = "Run Time (min)")
        
        # Pump Command Window
        pumpText = tk.Text(fr_pump, width = 10, height = 5)
        pumpText.insert(tk.END, "0:200")
        pumpText.insert(tk.END, "\n2:100")

        # Create Buttons
        btn_start = ttk.Button(fr_button, text = "CONTINUE TEST", style = "AccentButton",
                                command = self.continueButtonCallback)
        btn_cancel = ttk.Button(fr_button, text = "CANCEL", style = "AccentButton",
                                    command = self.cancelButtonCallback)

        # Organize and Arrange Components
        fr_params.grid(row = 0, column = 0, pady = 5)
        lbl_runT.grid(row = 0, column = 0)
        ent_runT.grid(row = 0, column = 1)

        # Pump Frame
        fr_pump.grid(row = 0, column = 1, rowspan = 2)
        pumpText.grid(row = 0, column = 0)

        fr_button.grid(row = 1, column = 0, pady = 5)
        btn_start.grid(row = 0, column = 0, padx = 2)
        btn_cancel.grid(row = 0, column = 1, padx = 2)

        # Size and open window
        # Center window
        w = tdWindow.winfo_reqwidth()
        h = tdWindow.winfo_reqheight()
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws/2) - (w/2)-250
        y = (hs/2) - (h/2)
        tdWindow.geometry('+%d+%d' % (x, y))
        
        return tdWindow, btn_start, str_runT, pumpText

    # Sets variables and flags in appController for proceeding with test
    def startButtonCallback(self):
        # Check to see if valid save path
        proceed = True
        if not self.saveDataFilePath:
            proceed = tk.messagebox.askyesno(title = "Warning", message = \
                        "No save path detected.\n Are you sure you wish to proceed?")
        if proceed:
            temp = float(self.str_runT.get());
            pText = self.pumpText.get('1.0', 'end-1c');
            # Close window
            self.tdWindow.destroy()
            self.tdWindow.update()
            # Sets run time, chipVars, and filepath
            self.appController.newTest(temp, self.chipVars, pText, self.saveDataFilePath)
        else:
            return

    def continueButtonCallback(self):
        temp = float(self.str_runT.get());
        pText = self.pumpText.get('1.0', 'end-1c');
        # Close window
        self.tdWindow.destroy()
        self.tdWindow.update()
        
        self.appController.continueTest(temp, pText)

    def cancelButtonCallback(self):
        # Stop Test if active
        self.appController.stopTest("Canceled")
        # Close window
        self.tdWindow.destroy()
        self.tdWindow.update()
        return

    # Launches dialog box for selecting the save file
    def filePathSelectCallback(self):
        self.tdWindow.lower()
        self.saveDataFilePath = asksaveasfilename(defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        self.ent_filePathIndicator.insert(0, str(self.saveDataFilePath))
        self.tdWindow.lift()
        return