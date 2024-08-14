from .model import MainWindowModel


class MainWindowPresenter:
    """Facilitates interaction between View and Model

    Parameters
    ----------
    view : MainWindow
        main window view instance.
    """

    def __init__(self, view):
        self.view = view
        self.model = MainWindowModel()

    def createProject(self, name: str, save_path: str):
        """Creates a new RAT project and controls object then initialise UI.

        Parameters
        ----------
        name : str
            The name of the project.
        save_path : str
            The save path of the project.
        """

        self.model.createProject(name, save_path)
        # TODO if the view's central widget is the startup one then setup MDI else reset the widgets.
        self.view.setupMDI()

    def run(self):
        """Run the optimisation."""
        self.view.terminal_widget.addVars({'controls': self.model.controls, 'project': self.model.project})
        self.view.terminal_widget.executeCommand("RAT.run(project, controls)")
