import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem, QAbstractItemView, QFileDialog

import sqlite3

# con = sqlite3.connect('')
# cur = con.cursor()


class MyWidget(QMainWindow):
    def __init__(self):
        self.treeDBWidget = QTreeWidget()  # чтобы pycharm видел, что treeDBWidget имеет класс QTreeWidget

        super().__init__()
        uic.loadUi('main.ui', self)
        self.menuSetup()
        self.setup_DB_tree()
        self.dbs = []  # dbs = [[id, name, path, QWidget], ...]
        self.selected = None

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

    def addDB(self, path):  # editing
        pk = self.treeDBWidget.topLevelItemCount()
        name = path.split('/')[-1]
        widget = QTreeWidgetItem(['1: ' + name])
        self.treeDBWidget.addTopLevelItem(widget)
        k = [pk, name, path, widget]
        self.dbs.append(k)

    def setup_DB_tree(self):
        self.treeDBWidget.itemClicked.connect(self.treeItemClick)
        self.treeDBWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.treeDBWidget.setUniformRowHeights(True)
        top = QTreeWidgetItem(['data.sqlite3'])
        self.treeDBWidget.addTopLevelItem(top)
        top.addChild(QTreeWidgetItem(['table1']))

    def treeItemClick(self, it):
        print(it, type(it))
        help(it)
        db = it.parent()
        if db is None:
            db = it.text(0)
            pass  # like db
        else:
            db = db.text(0)
            table = it.text(0)
            pass  # like table

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())
