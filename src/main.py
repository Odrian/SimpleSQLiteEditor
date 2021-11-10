import sys
from PyQt5 import uic
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import \
    (QApplication, QMainWindow, QAbstractItemView, QTableView, QFileDialog,
     QTreeWidgetItem, QHeaderView, QTreeWidget)
import sqlite3


class SimpleException(Exception):
    pass


class Column:
    def __init__(self, name):
        self.name = name
        self.type = ""
        self.primary_key = False
        self.unique = False
        self.notNull = False
        self.default = ""
        self.references = None

    def str(self):
        data = f"Column({self.name}, {self.type}"
        if self.references is not None:
            data += f", References='{self.references}'"
        if self.primary_key:
            data += ", Primary_key"
        if self.unique:
            data += ", Unique"
        if self.notNull:
            data += ", Not_Null"
        if self.default is not None:
            data += f", Default='{self.default}'"
        return data + ")"

    def __repr__(self):
        return self.str()

    def __str__(self):
        return self.str()

    def get_list(self):
        return [
            self.name,
            self.type,
            self._bool_converter(self.references is not None),
            self._bool_converter(self.primary_key),
            self._bool_converter(self.unique),
            self._bool_converter(self.notNull),
            self.default
        ]

    def _bool_converter(self, boolean):
        return "+" if boolean else ""


class MyWidget(QMainWindow):
    def __init__(self):
        # чтобы PyCharm видел классы
        self.table1 = QTableView()
        self.table2 = QTableView()
        self.treeDBWidget = QTreeWidget()

        super().__init__()
        uic.loadUi('main.ui', self)

        self.dbs = []  # dbs = [[name, path, widget, con, cur, tables], ...]
        self.selected = None
        self.model1 = QStandardItemModel()
        self.model2 = QStandardItemModel()
        self.supported_types = [
            "BIGINT", "BLOB", "BOOLEAN", "CHAR", "DATE", "DATETIME", "DECIMAL", "DOUBLE",
            "INTEGER", "INT", "NONE", "NUMERIC", "REAL", "STRING", "TEXT", "TIME", "VARCHAR",
        ]

        self.menu_setup()
        self.setup_db_tree()
        self.setup_tables()
        self.open_recent_db()

    def open_recent_db(self):
        pass
        # self.add_db("C:/$.another/Git/films_db.sqlite")

    def menu_setup(self):
        self.qCreateDB.triggered.connect(self.new_db)
        self.qOpenDB.triggered.connect(self.open_db)

    def setup_tables(self):
        self.table1.setModel(self.model1)
        self.table2.setModel(self.model2)

        cols = ["Имя", "Тип Данных", "Внешний ключ", "Первичный ключ",
                "Уникальность", "не Null", "По умолчанию"]
        self.model1.setHorizontalHeaderLabels(cols)
        header = self.table1.horizontalHeader()
        n = len(cols)
        for i in range(0, n - 1):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(n - 1, QHeaderView.Stretch)

    def clear_tables(self):
        self.model1.setRowCount(0)
        self.model2.setRowCount(0)
        self.model2.setColumnCount(0)

    def setup_db_tree(self):
        self.treeDBWidget.itemClicked.connect(self.tree_item_click)
        self.treeDBWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.treeDBWidget.setUniformRowHeights(True)

    def tree_item_click(self, it):
        try:
            db = it.parent()
            self.clear_tables()
            if db is None:
                db_info = self.get_db_info_by_widget(it)
                self.selected = db_info
            else:
                db_info = self.get_db_info_by_widget(db)
                self.selected = db_info
                table = it.text(0)
                columns = self.get_all_columns(db_info, table)

                for column in columns:
                    self.model1.appendRow(map(QStandardItem, column.get_list()))

                self.model2.setHorizontalHeaderLabels(map(lambda x: x.name, columns))

                # update table2
        except SimpleException:
            pass  # error message

    def get_db_info_by_widget(self, widget):
        for db_info1 in self.dbs:
            if db_info1[2] == widget:
                return db_info1
        raise SimpleException

    def get_all_columns(self, db_info, table):
        tex = f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'"
        request = db_info[4].execute(tex).fetchall()[0][0]
        request = request.removeprefix(f"CREATE TABLE {table} (").removesuffix(")")
        columns = []
        for req in request.split(', '):
            columns.append(self.create_column(req))
        return columns

    def create_column(self, req):
        req = req.split()
        name = req[0]
        column = Column(name)
        i = 1
        if req[i] in self.supported_types:
            column.type = req[i]
            i = 2
        n = len(req)
        while i < n:
            if req[i] == "UNIQUE":
                column.unique = True
            elif i != n - 1:
                if req[i] == "PRIMARY" and req[i + 1] == "KEY":
                    column.primary_key = True
                    i += 1
                elif req[i] == "NOT" and req[i + 1] == "NULL":
                    column.notNull = True
                    i += 1
                elif req[i] == "DEFAULT":
                    column.default = req[i+1]
                    i += 1
                elif i != n - 2 and req[i] == "REFERENCES":
                    link_table = req[i + 1]
                    link_col = req[i + 2][1:-1]
                    column.references = (link_table, link_col)
                    i += 2
            i += 1
        return column

    def new_db(self):
        file_name = QFileDialog.getSaveFileName(
            self, "Save Database", "/home", "SQLite (*.sqlite *.db3)")[0]
        if file_name:
            with open(file_name, 'w'):
                pass
            self.add_db(file_name)

    def open_db(self):
        file_names = QFileDialog.getOpenFileNames(
            self, "Open DataBase", "/home", "SQLite (*.sqlite *.db3)")[0]
        for fileName in file_names:
            self.add_db(fileName)

    def add_db(self, path):
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


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())
