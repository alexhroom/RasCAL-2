"""Console widget."""
from PyQt6 import QtWidgets
from qtconsole.jupyter_widget import JupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
import RATapi

class ConsoleWidget(JupyterWidget):
    def __init__(self):
        super().__init__()
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel_manager.kernel.gui = 'qt'
        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()
        self.addVars({"RAT": RATapi})

    def addVars(self, variables: dict):
        """Add variables to the Jupyter console environment.

        Parameters
        ----------
        variable : dict
            A dict of name-value pairs for variables.

        """
        self.kernel_manager.kernel.shell.push(variables)

    def executeCommand(self, command):
        """Execute a command in the console.

        Parameters
        ----------
        command : str
            The Python command to execute.

        """
        self._execute(command, False)

    def clear(self):
        """Clear the terminal."""
        self._control.clear()
