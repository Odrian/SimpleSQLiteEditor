import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeView
from PyQt5.QtWidgets import QTreeWidgetItem, QAbstractItemView, QFileDialog

import sqlite3

class SimpleException(Exception):
    pass

class MyWidget(QMainWindow):
    def __init__(self):
        self.treeDBWidget: QTreeWidget  # чтобы pycharm видел, что treeDBWidget имеет класс QTreeWidget

        super().__init__()
        uic.loadUi('main.ui', self)

        self.menuSetup()
        self.setup_DB_tree()
        self.dbs = []  # dbs = [[name, path, widget, con, cur, tables], ...]
        self.selected = None

#        self.addDb("C:/$.another/Git/films_db.sqlite")

    def menuSetup(self):
        self.qCreateDB.triggered.connect(self.newDb)
        self.qOpenDB.triggered.connect(self.openDb)

    def setup_DB_tree(self):
        self.treeDBWidget.itemClicked.connect(self.treeItemClick)
        self.treeDBWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.treeDBWidget.setUniformRowHeights(True)
    def treeItemClick(self, it):
        try:
            db = it.parent()
            if db is None:
                dbInfo = self.getDbInfoByWidget(it)
                pass
            else:
                dbInfo = self.getDbInfoByWidget(db)
                table = it
                pass
        except SimpleException:
            pass  # ERROR WINDOW
    def getDbInfoByWidget(self, widget):
        for dbInfo1 in self.dbs:
            if dbInfo1[2] == widget:
                return dbInfo1
        raise SimpleException

    def newDb(self):
        fileName = QFileDialog.getSaveFileName(
            self, "Save Database", "/home", "SQLite (*.sqlite *.db3)")[0]
        if fileName:
            with open(fileName, 'w'):
                pass
            self.addDb(fileName)
    def openDb(self):
        fileNames = QFileDialog.getOpenFileNames(
            self, "Open DataBase", "/home", "SQLite (*.sqlite *.db3)")[0]
        for fileName in fileNames:
            self.addDb(fileName)

    def addDb(self, path):
        name = path.split('/')[-1]
        widget = QTreeWidgetItem([name])
        widget.setToolTip(0, path)
        self.treeDBWidget.addTopLevelItem(widget)
        con = sqlite3.connect(path)
        cur = con.cursor()
        tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        tables = list(map(lambda x: x[0], tables))
        for table in tables:
            widget.addChild(QTreeWidgetItem([table]))

        k = [name, path, widget, con, cur, tables]
        self.dbs.append(k)

    def selectDb(self):
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())
