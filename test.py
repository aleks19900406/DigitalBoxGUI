import sys
from PyQt5 import QtCore, QtGui, QtWidgets


class Widget(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        self.setFont(QtGui.QFont("Helvetica", 8, QtGui.QFont.Normal, italic=False))
        self.setWindowTitle("Getting selected item")
        lay = QtWidgets.QVBoxLayout(self)
        self.button = QtWidgets.QPushButton("Okay")
        self.button.clicked.connect(self.accept)
        self.listView = QtWidgets.QListView()
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(self.listView)

        self.entry = QtGui.QStandardItemModel()
        self.listView.setModel(self.entry)
        self.listView.setSpacing(4)
        self.listView.setFont(
            QtGui.QFont("Helvetica", 9, QtGui.QFont.Normal, italic=False)
        )
        self.listView.setUniformItemSizes(True)
        self.listView.setFixedSize(300, 150)

        Code_Group = QtWidgets.QGroupBox()
        Code_Group.setTitle("&Selecting and deselecting")
        Code_Group.setLayout(lay)

        Vlay = QtWidgets.QVBoxLayout(self)
        Vlay.addWidget(Code_Group)
        Vlay.addWidget(self.button, alignment=QtCore.Qt.AlignCenter)
        Vlay.setSizeConstraint(Vlay.SetFixedSize)

        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
        self.read_settings()
        self.listView.selectionModel().currentChanged.connect(self.on_row_changed)

        self.accepted.connect(self.write_settings)

    def on_row_changed(self, current, previous):
        self._INDEX = current.row()
        print('Row %d selected' % current.row())

    def closeEvent(self, event):
        print("closeEvent")
        self.write_settings()
        super(Widget, self).closeEvent(event)

    def read_settings(self):
        settings = QtCore.QSettings("file.ini", QtCore.QSettings.IniFormat)
        settings.beginGroup("listView")
        model = self.listView.model()
        if settings.contains("items"):

            editTriggers = settings.value(
                "editTriggers", type=QtWidgets.QAbstractItemView.EditTriggers
            )
            selectionMode = settings.value(
                "selectionMode", type=QtWidgets.QAbstractItemView.SelectionMode
            )
            selectionBehavior = settings.value(
                "selectionBehavior", type=QtWidgets.QAbstractItemView.SelectionBehavior
            )
            self.listView.setEditTriggers(editTriggers)
            self.listView.setSelectionMode(selectionMode)
            self.listView.setSelectionBehavior(selectionBehavior)

            items = settings.value("items", type=QtCore.QByteArray)
            stream = QtCore.QDataStream(items, QtCore.QIODevice.ReadOnly)
            while not stream.atEnd():
                it = QtGui.QStandardItem()
                stream >> it
                model.appendRow(it)
            selecteditems = settings.value("selecteditems", type=list)
            for row in selecteditems:
                index = model.index(row, 0)
                self.listView.selectionModel().select(
                    index, QtCore.QItemSelectionModel.Select
                )
        else:
            for text in [
                "Itemname1",
                "Itemname2",
                "Itemname3",
                "Itemname4",
                "Itemname5",
            ]:
                it = QtGui.QStandardItem(text)
                model.appendRow(it)
                self.listView.setEditTriggers(
                    QtWidgets.QAbstractItemView.NoEditTriggers
                )
                self.listView.setSelectionMode(
                    QtWidgets.QAbstractItemView.SingleSelection
                )
                self.listView.setSelectionBehavior(
                    QtWidgets.QAbstractItemView.SelectRows
                )
        settings.endGroup()

    def write_settings(self):
        settings = QtCore.QSettings("file.ini", QtCore.QSettings.IniFormat)
        settings.beginGroup("listView")
        model = self.listView.model()

        settings.setValue("editTriggers", self.listView.editTriggers())
        settings.setValue("selectionMode", self.listView.selectionMode())
        settings.setValue("selectionBehavior", self.listView.selectionBehavior())

        items = QtCore.QByteArray()
        stream = QtCore.QDataStream(items, QtCore.QIODevice.WriteOnly)
        for i in range(model.rowCount()):
            it = model.item(i)
            stream << it
        settings.setValue("items", items)

        selecteditems = []
        for index in self.listView.selectionModel().selectedRows():
            selecteditems.append(index.row())
        settings.setValue("selecteditems", selecteditems)
        settings.endGroup()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())