import os
import sys
from PyQt5 import uic
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt5.QtWidgets import \
    (QApplication, QMainWindow, QAbstractItemView, QTableView, QFileDialog,
     QTreeWidgetItem, QHeaderView, QTreeWidget, QInputDialog, QMessageBox,
     QDialog, QLineEdit, QComboBox, QCheckBox)
import sqlite3


class Column:
    def __init__(self, name):
        self.name = name
        self.type = None
        self.primary_key = False
        self.unique = False
        self.not_null = False
        self.default = None
        self.references = None

    def str(self):
        data = f"Column({self.name}, {self.type}"
        if self.references is not None:
            data += f", References='{self.references}'"
        if self.primary_key:
            data += ", Primary_key"
        if self.unique:
            data += ", Unique"
        if self.not_null:
            data += ", Not_Null"
        if self.default:
            data += f", Default='{self.default}'"
        return data + ")"

    def __repr__(self):
        return self.str()

    def __str__(self):
        return self.str()

    def get_list(self):
        return [
            self.name,
            self.type if self.type is not None else "",
            self._bool_converter(self.references is not None),
            self._bool_converter(self.primary_key),
            self._bool_converter(self.unique),
            self._bool_converter(self.not_null),
            self.default if self.default is not None else "",
        ]

    def _bool_converter(self, boolean):
        return "+" if boolean else ""

    def get_request(self):
        req = [self.name]
        if self.type is not None:
            req.append(self.type)
        if self.primary_key:
            req.append("PRIMARY")
            req.append("KEY")
        if self.unique:
            req.append("UNIQUE")
        if self.not_null:
            req.append("NOT")
            req.append("NULL")
        if self.default is not None and self.default != "":
            req.append("DEFAULT")
            req.append(self.default)
        if self.references is not None:
            req.append("REFERENCES")
            req.append(self.references[0])
            req.append(self.references[1])
        print(req)
        return " ".join(req)


class ColumnDialog(QDialog):
    def __init__(self, main):
        self.name = QLineEdit()
        self.type = QComboBox()
        self.primary_key = QCheckBox()
        self.unique = QCheckBox()
        self.not_null = QCheckBox()
        self.link0 = QCheckBox()
#        self.link1 = QComboBox()
#        self.link2 = QComboBox()
        self.default0 = QLineEdit()

        super().__init__()
        uic.loadUi("table_editing.ui", self)

        self.main = main
        self.type.addItem("")
        self.type.addItems(TYPES)
        self.link0.stateChanged.connect(self.link0_trigger)
        self.link1.currentIndexChanged.connect(self.link1_trigger)

    def link0_trigger(self):
        if self.link0.isChecked():
            self.link1.setDisabled(False)
            self.link2.setDisabled(False)
        else:
            self.link1.setDisabled(True)
            self.link2.setDisabled(True)

    def link1_trigger(self, value):
        pass

    def get_values(self, column):
        self.name.setText(column.name)
        if column.type is not None:
            self.type.setCurrentIndex(TYPES.index(column.type))
        self.primary_key.setChecked(column.primary_key)
        self.unique.setChecked(column.unique)
        self.not_null.setChecked(column.not_null)
        self.link1.addItem("")
        self.link1.addItems(self.main.sql_get_all_tables())
        link = column.references
        if link:
            print(1, link)
            link1, link2 = link
            self.link1.setCurrentIndex(self.link1.findText(link1))
            self.link2.setCurrentIndex(self.link2.findText(link2))
        if column.default is not None:
            self.default0.setText(column.default)

        self.link0_trigger()

        if self.exec_() == 0:
            return None

        column2 = Column(self.name.text())
        column2.type = str(self.type.currentText())
        column2.primary_key = self.primary_key.isChecked()
        column2.unique = self.unique.isChecked()
        column2.not_null = self.not_null.isChecked()
        if self.default0 != "":
            column2.default = self.default0.text()

        return column2


class MyWidget(QMainWindow):
    def __init__(self):
        # чтобы PyCharm видел классы
        self.table1: QTableView
        self.table2: QTableView
        self.model1: QStandardItemModel()
        self.model2: QStandardItemModel()
        self.treeDBWidget = QTreeWidget()

        super().__init__()
        uic.loadUi('main.ui', self)

        self.dbs = []  # dbs = [[name, path, widget, con, cur, tables], ...]
        self.selected_db = None
        self.selected_table = None
        self.model1 = QStandardItemModel()
        self.model2 = QStandardItemModel()

        self.setup()
        self.open_recent()

    def setup(self):
        # self.table2.doubleClicked.connect(lambda x: print(x))
        self.menu_create_db.clicked.connect(self.new_db)
        self.menu_open_db.clicked.connect(self.open_db)

        self.tab1_save.clicked.connect(self._tab1_save)
        self.tab1_not_save.clicked.connect(self._tab_not_save)
        self.tab1_add.clicked.connect(self._tab1_add)
        self.tab1_edit.clicked.connect(self._tab1_edit)
        self.tab1_del.clicked.connect(self._tab1_del)

        self.tab2_save.clicked.connect(self._tab2_save)
        self.tab2_not_save.clicked.connect(self._tab_not_save)
        self.tab2_add.clicked.connect(self._tab2_add)
        self.tab2_edit.clicked.connect(self._tab2_edit)
        self.tab2_del.clicked.connect(self._tab2_del)

        self.treeDBWidget.itemClicked.connect(self.tree_item_select)
        self.treeDBWidget.itemDoubleClicked.connect(self.tree_item_rename)
        self.treeDBWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.treeDBWidget.setUniformRowHeights(True)

        self.table1.setModel(self.model1)
        self.table2.setModel(self.model2)
        cols = ["Имя", "Тип Данных", "Внешний ключ", "Первичный ключ",
                "Уникальность", "не Null", "По умолчанию"]
        self.model1.setHorizontalHeaderLabels(cols)
        self.table1.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def open_recent(self):
        with open("recent.txt") as f:
            for path in f:
                self.add_db(path)

    def select_db_table(self, db=None, table=None):
        if self.selected_db is not None:
            self.selected_db[3].rollback()
        self.selected_db = db
        self.selected_table = table

    def clear_tables(self):
        self.model1.setRowCount(0)
        self.model2.setColumnCount(0)
        self.model2.setRowCount(0)

    def tree_item_rename(self, it):
        db = it.parent()
        self.clear_tables()
        if db is None:
            db_info = self.get_db_info_by_widget(it)
            path = db_info[1]
            new_name, flag = self.input_dialog(
                "Переименовать Базу данных",
                "Все не сохранённые данные будут утеряны.\nНовое имя:")
            if flag:
                i1 = path.rindex("/")
                i2 = path.rindex(".")
                path0 = path[:i1 + 1]
                path1 = path[i2:]
                new_path = path0 + new_name + path1
                if path != new_path:
                    if os.path.exists(new_path):
                        self.error(new_path + " already exists")
                    else:
                        self.select_db_table()

                        widget = db_info[2]
                        index = self.treeDBWidget.indexOfTopLevelItem(widget)
                        self.treeDBWidget.takeTopLevelItem(index)

                        del self.dbs[self.dbs.index(db_info)]

                        del db_info
                        try:
                            os.rename(path, new_path)
                            self.add_db(new_path)
                        except OSError as e:
                            print(e)
                            self.error("Не получилось переменовать\n" +
                                       path + "\nв\n" + new_path)
                            return
        else:
            db_info = self.get_db_info_by_widget(db)
            table0 = it.text(0)
            table1, flag = self.input_dialog(
                "Переименовать таблицу",
                "Все не сохранённые данные будут утеряны.\nНовое имя:")
            table1 = self.check_text_correct(table1)
            if flag and table1 != "" and table1 != table0:
                if table1 not in db_info[5]:
                    self.sql_rename_table(db_info, table0, table1)
                else:
                    self.error("уже существует другая таблица с таким именем: " + table1)

    def tree_item_select(self, it):
        db = it.parent()
        if db is None:
            db_info = self.get_db_info_by_widget(it)
            self.select_db_table(db_info)
            self.clear_tables()
        else:
            db_info = self.get_db_info_by_widget(db)
            table = it.text(0)
            self.select_table(db_info, table)

    def tree_top_item_delete(self, db_info):
        self.select_db_table()

        widget = db_info[2]
        index = self.treeDBWidget.indexOfTopLevelItem(widget)
        self.treeDBWidget.takeTopLevelItem(index)

        del self.dbs[self.dbs.index(db_info)]

    def select_table(self, db_info, table):
        self.clear_tables()
        self.select_db_table(db_info, table)

        cur = db_info[4]
        columns = self.sql_get_all_columns(cur, table)

        for column in columns:
            self.model1.appendRow(map(self.make_uneditable_item, column.get_list()))
        self.table1.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.model2.setHorizontalHeaderLabels(map(lambda x: x.name, columns))
        for row in self.sql_get_all_data(cur, table):
            self.model2.appendRow(map(lambda x: QStandardItem(str(x)), row))

    def make_uneditable_item(self, text):
        item = QStandardItem(text)
        item.setEditable(False)
        return item

    def get_db_info_by_widget(self, widget):
        for db_info1 in self.dbs:
            if db_info1[2] == widget:
                return db_info1
        self.error("err", True)

    def check_text_correct(self, text):
        chars = "\'\" "
        for ch in text:
            if ch in chars:
                return ""
        return text

    def _tab_not_save(self):
        self.select_table(self.selected_db, self.selected_table)

    def _tab1_save(self):
        self.selected_db[3].commit()

    def _tab1_add(self):
        name, flag = self.input_dialog("Ввод", "Введите имя нового слобца:")
        if not flag or self.check_text_correct(name) == "":
            self.error("Ошибка ввода имени")
        table = self.selected_table
        self.selected_db[4].execute(f"ALTER TABLE {table} ADD {name}")
        self.model1.appendRow([self.make_uneditable_item(name)] + [self.make_uneditable_item("") for _ in range(6)])

    def _tab1_edit(self):
        index = self.table1.selectedIndexes()
        if index:
            row = index[0].row()
            column0 = self.sql_get_all_columns(self.selected_db[4], self.selected_table)[row]
            column1 = ColumnDialog(self).get_values(column0)
            if column1 is None:
                return
            cur = self.selected_db[4]
            if self.selected_table is None:
                table0, flag = self.input_dialog("Ввод", "Введите имя новой таблицы:")
                if not flag or table0 == "":
                    self.error("Ошибка ввода имени")
                    return
                self.selected_table = table0
            table = self.selected_table
            text1 = f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'"
            request = cur.execute(text1).fetchall()[0][0]
            request = request.removeprefix(f"CREATE TABLE ").removeprefix("\"").removeprefix(table)\
                .removeprefix("\"").removeprefix(" (").removesuffix(")").split(", ")
            request[row] = column1.get_request()
            columns = ", ".join(map(lambda x: x.split()[0], request))
            print(request)
            text = f"""
            PRAGMA foreign_keys=off;
            BEGIN TRANSACTION;
            ALTER TABLE {table} RENAME TO _table11__old;
            CREATE TABLE {table} (
            {", ".join(request)}
            );
            INSERT INTO {table} ({columns}) SELECT {columns} FROM _table11__old;
            PRAGMA foreign_keys=on;
            DROP TABLE _table11__old
            """
            for req in text.split(";"):
                req = req.replace('\n', '')
                req = ' '.join(req.split())
                print(req)
                cur.execute(req)
            self.select_table(self.selected_db, self.selected_table)

    def _tab1_del(self):
        index = self.table1.selectedIndexes()
        if index:
            self.sql_delete_table(self.model1.data(self.model1.index(1, 0)))
            self.model1.removeRow(index[0].row())

    def _tab2_save(self):
        model2 = self.model2
        table = self.selected_table
        cur = self.selected_db[4]
        columns = self.sql_get_all_columns(cur, table)

        for x in range(model2.columnCount()):
            column = columns[x]
            for y in range(model2.rowCount()):
                val = model2.data(model2.index(y, x))
                cur.execute(f"UPDATE {table} SET {column} = {val} WHERE id={y}")
        self.selected_db[3].commit()

    def _tab2_add(self):
        self.model2.appendRow(QStandardItem(""))

    def _tab2_edit(self):
        pass

    def _tab2_del(self):
        index = self.table2.selectedIndexes()
        if index:
            row = index[0].row()
            self.model2.removeRow(row)

    def new_db(self):
        file_name = QFileDialog.getSaveFileName(
            self, "Создать Базу данных", "/home", "SQLite (*.sqlite *.db3)")[0]
        if file_name:
            with open(file_name, 'w'):
                pass
            self.add_db(file_name)

    def open_db(self):
        file_names = QFileDialog.getOpenFileNames(
            self, "Открыть Базу данных", "/home", "SQLite (*.sqlite3)")[0]
        for fileName in file_names:
            self.add_db(fileName)

    def add_db(self, path, recent=False):
        name = path.split('/')[-1]
        widget = QTreeWidgetItem([name])
        widget.setToolTip(0, path)
        self.treeDBWidget.addTopLevelItem(widget)
        con = sqlite3.connect(path)
        cur = con.cursor()
        tables = self.sql_get_all_tables(cur)
        for table in tables:
            widget.addChild(QTreeWidgetItem([table]))

        if recent:
            with open("recent.txt", "a") as f:
                f.write(path)
        k = [name, path, widget, con, cur, tables]
        self.dbs.append(k)

    def error(self, text="Some error", exit_out=False):
        msg = QMessageBox()
        msg.setWindowTitle("Error")
        msg.setFont(QFont("Arial"))
        if exit_out:
            msg.setIcon(QMessageBox.Critical)
        else:
            msg.setIcon(QMessageBox.Warning)
        msg.setText(text)
        msg.exec_()
        if exit_out:
            sys.exit()

    def input_dialog(self, title, text):
        dialog = QInputDialog()
        dialog.setWindowTitle(title)
        dialog.setLabelText(text)
        dialog.setFont(QFont("Arial", 11))

        flag = bool(dialog.exec_())
        text = dialog.textValue()
        return text, flag

    def sql_delete_table(self, column):
        self.selected_db[4].execute(f"ALTER TABLE {self.selected_table} DROP COLUMN {column}")

    def sql_rename_table(self, db_info, table0, table1):
        con = db_info[3]
        cur = db_info[4]

        con.rollback()
        cur.execute(f"ALTER TABLE {table0} RENAME TO {table1}")

        widget = db_info[2]
        for child in widget.takeChildren():
            if child.text(0) == table0:
                child.setText(0, table1)
            widget.addChild(child)

    def sql_get_all_tables(self, cur=None):
        cur = self.selected_db[4] if cur is None else cur
        tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        return list(map(lambda x: x[0], tables))

    def sql_get_all_columns(self, cur, table):
        tex = f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'"
        request = cur.execute(tex).fetchall()
        if not request:
            self.error(f"error: не удалось найти таблицу - {table}")
            return []
        request = request[0][0].removeprefix(f"CREATE TABLE ").removeprefix("\"").removeprefix(table)\
            .removeprefix("\"").removeprefix(" (").removesuffix(")")
        columns = []
        for req in request.split(', '):
            req = req.split()
            name = req[0]
            column = Column(name)
            i = 1
            n = len(req)
            if i == n:
                columns.append(column)
                continue
            if req[i] in TYPES:
                column.type = req[i]
                i = 2
            while i < n:
                if req[i] == "UNIQUE":
                    column.unique = True
                elif i != n - 1:
                    if req[i] == "PRIMARY" and req[i + 1] == "KEY":
                        column.primary_key = True
                        i += 1
                    elif req[i] == "NOT" and req[i + 1] == "NULL":
                        column.not_null = True
                        i += 1
                    elif req[i] == "DEFAULT":
                        column.default = req[i + 1]
                        i += 1
                    elif i != n - 2 and req[i] == "REFERENCES":
                        link_table = req[i + 1]
                        link_col = req[i + 2][1:-1]
                        column.references = (link_table, link_col)
                        i += 2
                i += 1
            columns.append(column)
        return columns

    def sql_get_all_data(self, cur, table):
        return cur.execute("SELECT * FROM " + table).fetchall()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


TYPES = [
    "BIGINT", "BLOB", "BOOLEAN", "CHAR", "DATE", "DATETIME",
    "DECIMAL", "DOUBLE", "INTEGER", "INT", "NONE", "NUMERIC",
    "REAL", "STRING", "TEXT", "TIME", "VARCHAR",
]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())
