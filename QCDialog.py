import tkinter as tk
import tkinter.ttk as ttk

class QCDialog:

    def __init__(self, appController):

        self.appController = appController;
        self.root = appController.root;

        self.qcWindow, self.chipVars = self.createStartWindow(self.root)

    # Creates Baseline window
    def createStartWindow(self, root):
        qcWindow = tk.Toplevel(root)
        qcWindow.title("Quality Check")

        # Create Frames
        fr_chipSelect = ttk.LabelFrame(qcWindow, text = "Chip Select")
        fr_button = tk.Frame(qcWindow)
        
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
        fr_chipSelect.grid(row = 0, column = 0, pady = 5)

        # Button Frame
        fr_button.grid(row = 1, column = 0, pady = 5)
        btn_start.grid(row = 0, column = 0, padx = 2)
        btn_cancel.grid(row = 0, column = 1, padx = 2)


        # Size and open window
        # Center window
        w = qcWindow.winfo_reqwidth()
        h = qcWindow.winfo_reqheight()
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws/2) - (w/2)-250
        y = (hs/2) - (h/2)
        qcWindow.geometry('+%d+%d' % (x, y))
        
        return qcWindow, chipVars

    # Sets variables and flags in appController for proceeding with test
    def startButtonCallback(self):
        # Close window
        self.qcWindow.destroy()
        self.qcWindow.update()
        # Sets run time, chipVars, and filepath
        self.appController.newQC(self.chipVars)

    def cancelButtonCallback(self):
        # Close window
        self.qcWindow.destroy()
        self.qcWindow.update()
        return