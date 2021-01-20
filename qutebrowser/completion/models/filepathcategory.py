# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Completion category for filesystem paths."""

import glob
import os
import pathlib
from typing import List, Optional, Iterable

from PyQt5.QtCore import QAbstractListModel, QModelIndex, QObject, Qt, QUrl

from qutebrowser.config import config


class FilePathCategory(QAbstractListModel):
    """Represent filesystem paths matching a pattern."""

    def __init__(self, name: str, parent: QObject = None) -> None:
        super().__init__(parent)
        self._paths: List[str] = []
        self.name = name
        self.columns_to_filter = [0]

    def _contract_user(self, val: str, path: str) -> str:
        """Contract ~/... and ~user/... in results.

        Arguments:
            val: The user's partially typed path.
            path: The found path based on the input.
        """
        if not val.startswith('~'):
            return path
        head = pathlib.Path(pathlib.Path(val).parts[0])
        return str(head / pathlib.Path(path).relative_to(head.expanduser()))

    def _glob(self, val: str) -> Iterable[str]:
        """Find paths based on the given pattern."""
        if not os.path.isabs(val):
            return []
        return glob.glob(glob.escape(val) + '*')

    def _url_to_path(self, val: str) -> str:
        """Get a path from a file:/// URL."""
        url = QUrl(val)
        assert url.isValid(), url
        assert url.scheme() == 'file', url
        return url.toLocalFile()

    def set_pattern(self, val: str) -> None:
        """Compute list of suggested paths (called from `CompletionModel`).

        Args:
            val: The user's partially typed URL/path.
        """
        if not val:
            self._paths = config.val.completion.favorite_paths or []
        elif val.startswith('file:///'):
            url_path = self._url_to_path(val)
            self._paths = sorted(
                QUrl.fromLocalFile(path).toString()
                for path in self._glob(url_path)
            )
        else:
            paths = self._glob(os.path.expanduser(val))
            self._paths = sorted(self._contract_user(val, path) for path in paths)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Optional[str]:
        """Implement abstract method in QAbstractListModel."""
        if role == Qt.DisplayRole and index.column() == 0:
            return self._paths[index.row()]
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Implement abstract method in QAbstractListModel."""
        if parent.isValid():
            return 0
        return len(self._paths)
