import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename

class TestDialog:

    def __init__(self, appController, phase):

        self.appController = appController;
        self.root = appController.root;

        self.saveDataFilePath = None
        if phase == "Baseline":
            self.tdWindow, self.btn_start, self.ent_filePathIndicator, \
                           self.chipVars = self.createStartWindow(self.root, phase)
        else:
            self.tdWindow, self.btn_start = self.createContinueWindow(self.root, phase)

    # Creates Baseline window
    def createStartWindow(self, root, phase):
        tdWindow = tk.Toplevel(root)
        tdWindow.title(phase)

        # Create Frames
        fr_params = ttk.LabelFrame(tdWindow, text = "Test Parameters")
        fr_chipSelect = tk.Frame(fr_params)
        fr_helpText = tk.Frame(tdWindow)
        fr_button = tk.Frame(tdWindow)
        
        # Help Text
        lbl_helpText = ttk.Label(fr_helpText, text = "Remember to unclamp the inlet tubing before beginning the test")
        
        # Filepath
        lbl_filePathSelect = ttk.Label(fr_params, text="File Path")
        ent_filePathIndicator = ttk.Entry(fr_params, width = 30)
        btn_filePathSelect = ttk.Button(fr_params, text="Browse", style="AccentButton",
                                    command = self.filePathSelectCallback)

        # Create Buttons
        btn_start = ttk.Button(fr_button, text = "START BASELINE", style = "AccentButton",
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
        fr_chipSelect.grid(row = 0, column = 2, pady = 5)
        lbl_helpText.grid(row = 0, column = 0)
        # Row 1
        lbl_filePathSelect.grid(row = 1, column = 0)
        ent_filePathIndicator.grid(row = 1, column = 1, columnspan = 2)
        btn_filePathSelect.grid(row = 1, column = 3)
        # Row 2
        fr_helpText.grid(row = 2, column  = 0, pady = 5)

        # Button Frame (Row 3)
        fr_button.grid(row = 3, column = 0, pady = 5)
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
        
        return tdWindow, btn_start, ent_filePathIndicator, chipVars
    
    # Creates Perfusion window
    def createContinueWindow(self, root, phase):
        tdWindow = tk.Toplevel(root)
        tdWindow.title(phase)

        # Create Frames
        fr_params = ttk.LabelFrame(tdWindow, text = "Test Parameters")
        fr_helpText = tk.Frame(tdWindow)
        fr_button = tk.Frame(tdWindow)
        
        # Help Text
        lbl_helpText = ttk.Label(fr_helpText, text = "Remember to unclamp the inlet tubing before continuing the test")
        lbl_helpText.grid(row = 0, column = 0)
        
        # Create Buttons
        btn_start = ttk.Button(fr_button, text = "START PERFUSION", style = "AccentButton",
                                command = self.continueButtonCallback)
        btn_cancel = ttk.Button(fr_button, text = "CANCEL", style = "AccentButton",
                                    command = self.cancelButtonCallback)

        # Row 0
        fr_helpText.grid(row = 0, column  = 0, pady = 5)

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
        
        return tdWindow, btn_start

    # Sets variables and flags in appController for proceeding with test
    def startButtonCallback(self):
        # Check to see if valid save path
        proceed = True
        if not self.saveDataFilePath:
            proceed = tk.messagebox.askyesno(title = "Warning", message = \
                        "No save path detected.\n Are you sure you wish to proceed?")
        if proceed:
            # Close window
            self.tdWindow.destroy()
            self.tdWindow.update()
            # Sets run time, chipVars, and filepath
            self.appController.startBaseline(self.chipVars, self.saveDataFilePath)
        else:
            return

    def continueButtonCallback(self):
        # Close window
        self.tdWindow.destroy()
        self.tdWindow.update()
        
        self.appController.continueTest()

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