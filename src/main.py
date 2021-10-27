import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem, QAbstractItemView, QFileDialog

import sqlite3

# con = sqlite3.connect('')
# cur = con.cursor()


class MyWidget(QMainWindow):
    def __init__(self):
        self.treeDBWidget = QTreeWidget()

        super().__init__()
        uic.loadUi('main.ui', self)
        self.menuSetup()
        self.setup_DB_tree()

    def menuSetup(self):
        self.qCreateDB.triggered.connect(self.newDB)
        self.qOpenDB.triggered.connect(self.openDB)

    def newDB(self):
        fileName = QFileDialog.getSaveFileName(
            self, "Save Database", "/home", "SQLite (*.sqlite *.db3)")[0]
        if fileName:
            with open(fileName, 'w'):
                pass
            self.addDB(fileName)

    def openDB(self):
        fileNames = QFileDialog.getOpenFileNames(
            self, "Open DataBase", "/home", "SQLite (*.sqlite *.db3)")[0]
        print(fileNames)
        for fileName in fileNames:
            self.addDB(fileName)

    def addDB(self, path):
        pass  # add db to system

    def setup_DB_tree(self):
        self.treeDBWidget.itemClicked.connect(self.treeItemClick)
        self.treeDBWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.treeDBWidget.setUniformRowHeights(True)
        top = QTreeWidgetItem(['data.sqlite3'])
        self.treeDBWidget.addTopLevelItem(top)
        top.addChild(QTreeWidgetItem(['table1']))

    def treeItemClick(self, it):
        name = it.text(0)
        if it.parent() is None:
            pass  # like db
        else:
            pass  # like table

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())
