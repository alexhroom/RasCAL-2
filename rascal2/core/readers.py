"""File readers."""

import csv
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable
from itertools import count
from pathlib import Path

import numpy as np
from nexusformat.nexus import nxload
from orsopy.fileio import load_orso
from RATapi.models import Data


class AbstractDataReader(ABC):
    """Abstract base class for reading a data file."""

    @abstractmethod
    def read(self, filepath: str | Path) -> Iterable[Data]:
        """Read data to a list of Data objects.

        Parameters
        ----------
        filepath: str or Path
            The path to the data file.

        Returns
        -------
        Iterable[Data]
            An iterable of all data objects in the file.

        """
        raise NotImplementedError


class TextDataReader(AbstractDataReader):
    """Reader for plain text data files."""

    def read(self, filepath: str | Path) -> Iterable[Data]:
        with open(filepath) as datafile:
            sniffer = csv.Sniffer()
            has_header = sniffer.has_header(datafile.read(1024))
            datafile.seek(0)
            delimiter = sniffer.sniff(datafile.read(1024)).delimiter
            datafile.seek(0)

        data = np.loadtxt(filepath, delimiter=delimiter, skiprows=int(has_header))

        return [Data(name=Path(filepath).stem, data=data)]


class AscDataReader(AbstractDataReader):
    """Reader for ISIS Histogram data files."""

    def read(self, filepath: str | Path) -> Iterable[Data]:
        data = np.loadtxt(filepath, delimiter=",")

        # data processing from rascal-1:
        # https://github.com/arwelHughes/RasCAL_2019/blob/master/Rascal_functions/hist2xy.m
        for i, row in enumerate(data[:-1]):
            if row[1] != 0:
                row[0] += (data[i + 1, 0] - row[0]) / 2

        return [Data(name=Path(filepath).stem, data=data)]


class NexusDataReader(AbstractDataReader):
    """Reader for Nexus data files."""

    def read(self, filepath: str | Path) -> Iterable[Data]:
        datasets = []
        for entry in nxload(filepath, "r").NXentry:
            for data_group in entry.NXdata:
                q_values = np.array(data_group.plot_axes)
                # axes are bins so take centre of each bin
                q_values = (q_values[:, :-1] + q_values[:, 1:]) / 2
                signal = data_group.nxsignal.nxdata
                errors = data_group.nxerrors.nxdata
                
                data = np.vstack([q_values, signal, errors])
                data = data.transpose()

                datasets.append(Data(name=data_group.nxname, data=data))

        return datasets


class OrtDataReader(AbstractDataReader):
    """Reader for ORSO reflectivity data files."""

    def read(self, filepath: str | Path) -> Iterable[Data]:
        orso_data = load_orso(filepath)
        data = [Data(name=dataset.info.data_source.sample.name, data=dataset.data) for dataset in orso_data]
        # orso datasets in the same file can have repeated names!
        # but classlists do not allow this
        # use this dict to keep track of counts for repeated names
        name_counts = {d.name: count(1) for d in data}
        names = [d.name for d in data]
        if len(names) > len(list(set(names))):
            for i, dataset in enumerate(data):
                if dataset.name in names[:i]:
                    dataset.name += f"-{next(name_counts[dataset.name])}"

        return data


readers = defaultdict(
    lambda: TextDataReader,
    {
        ".asc": AscDataReader,
        ".nxs": NexusDataReader,
        ".ort": OrtDataReader,
    },
)
