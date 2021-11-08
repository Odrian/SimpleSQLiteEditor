import sys
from PyQt5 import uic
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import \
    (QApplication, QMainWindow, QAbstractItemView, QTableView, QFileDialog,
     QTreeWidgetItem, QHeaderView, QTreeWidget)
import sqlite3

class SimpleException(Exception):
    pass

class MyWidget(QMainWindow):
    def __init__(self):
        # чтобы pycharm видел классы
        self.table1 = QTableView()
        self.table2 = QTableView()
        self.treeDBWidget = QTreeWidget()

        super().__init__()
        uic.loadUi('main.ui', self)

        self.dbs = []  # dbs = [[name, path, widget, con, cur, tables], ...]
        self.selected = None
        self.model1 = QStandardItemModel()
        self.model2 = QStandardItemModel()

        self.menuSetup()
        self.setup_DB_tree()
        self.setupTables()

#        self.addDb("C:/$.another/Git/films_db.sqlite")

    def menuSetup(self):
        self.qCreateDB.triggered.connect(self.newDb)
        self.qOpenDB.triggered.connect(self.openDb)

    def setupTables(self):
        self.table1.setModel(self.model1)
        self.table2.setModel(self.model2)
        cols = ["Имя", "Тип Данных", "Первичный ключ", "Non null", "По умолчанию"]
        self.model1.setHorizontalHeaderLabels(cols)
        header = self.table1.horizontalHeader()
        n = 5
        for i in range(0, n - 1):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(n - 1, QHeaderView.Stretch)
    def clearTables(self):
        self.model1.setRowCount(0)
        self.model2.setRowCount(0)
        self.model2.setColumnCount(0)

    def setup_DB_tree(self):
        self.treeDBWidget.itemClicked.connect(self.treeItemClick)
        self.treeDBWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.treeDBWidget.setUniformRowHeights(True)
    def treeItemClick(self, it):
        try:
            db = it.parent()
            self.clearTables()
            if db is None:
                dbInfo = self.getDbInfoByWidget(it)
                self.selected = dbInfo
            else:
                dbInfo = self.getDbInfoByWidget(db)
                self.selected = dbInfo

                table = it.text(0)
                tex = f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'"
                request = dbInfo[4].execute(tex).fetchall()[0][0]
                request = request.removeprefix(f"CREATE TABLE {table} (").removesuffix(")")
                colums = []
                for req in request.split(', '):
                    req = req.split()
                    # create structure
                #print(req)
                #print(colums)
                # update table1 and table2
        except SimpleException:
            pass  # error message
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
        tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        tables = list(map(lambda x: x[0], tables))
        for table in tables:
            widget.addChild(QTreeWidgetItem([table]))

        k = [name, path, widget, con, cur, tables]
        self.dbs.append(k)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())
