"""Console widget."""
from qtconsole.jupyter_widget import JupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager

class ConsoleWidget(JupyterWidget):
    def __init__(self):
        super().__init__()
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel_manager.kernel.gui = 'qt'
        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()

    def executeCommand(self, command):
        """Execute a command in the console.
        
        Parameters
        ----------
        command : 

        """
        self._execute(command, False)
