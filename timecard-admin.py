import os
from dotenv import load_dotenv

import sys
from PyQt5.QtWidgets import QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem, QMainWindow, QMessageBox
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QApplication, QWidget, QLabel, QDialog, QDesktopWidget, QComboBox, QCompleter
from PyQt5.QtCore import Qt

from PyQt5.QtGui import QColor, QLinearGradient, QPixmap

from pymongo import MongoClient, DESCENDING, ASCENDING
from datetime import datetime, timedelta
import csv
from time import sleep


load_dotenv()
sys.path.append(os.getcwd())


PORT = int(os.environ["port"])
MONGO_URL = os.environ["mongo_url"]
PASSWORD = os.environ["password"]

# Pagination parameters
items_per_page = 20
current_page = 1


class PasswordDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Password Protection")
        self.setGeometry(100, 100, 300, 150)
        self.center()
        layout = QVBoxLayout()
        self.password_label = QLabel("Enter password:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.check_password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.submit_button)
        self.setLayout(layout)

    def check_password(self):
        entered_password = self.password_edit.text()
        if entered_password == PASSWORD:
            self.accept()
            return True
        else:
            return False

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class Timesheet(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.setMinimumWidth(1920)
        self.setMinimumHeight(1050)
        self.center()

        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setText("press YES if Admin ")
        msgBox.addButton(QMessageBox.Yes)
        msgBox.addButton(QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        reply = msgBox.exec_()
        if reply == QMessageBox.Yes:
            # Ask for password
            self.password = PasswordDialog()
            self.password.exec_()
            if self.password.check_password() is True:
                self.role = 'admin'
            else:
                sys.exit()
        else:
            self.role = 'user'

        # Initialize the database connection

        self.connection = MongoClient(MONGO_URL, PORT)
        self.database = self.connection['ddConnect']
        self.collection = self.database['time_data']
        self.user = self.database['users']
        self.project = self.database["projects"]
        self.department = self.database["departments"]

        users_list = self.user.distinct("login", {})
        projects_list = self.project.distinct("name", {})
        departments_list = self.department.distinct("name", {})

        # Create the search widgets

        self.logo = QLabel()
        pixmap = QPixmap('dd.png')

        pixmap = pixmap.scaled(120, 60, Qt.KeepAspectRatio,
                               Qt.SmoothTransformation)

        self.logo.setPixmap(pixmap)
        self.logo.setStyleSheet('background-color: #3A3A3A')

        self.projectLabel = QLabel('Project:')
        self.projectLabel.setMinimumSize(100, 50)

        self.projectLineEdit = QComboBox()
        self.projectLineEdit.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.projectLineEdit.setEditable(True)
        self.projectLineEdit.setInsertPolicy(QComboBox.NoInsert)
        self.projectLineEdit.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.projectLineEdit.clear()
        self.projectLineEdit.addItem("")
        self.projectLineEdit.setMinimumSize(200, 50)
        self.projectLineEdit.addItems(projects_list)

        self.taskLabel = QLabel('Task:')
        self.taskLabel.setMinimumSize(100, 50)
        self.taskLabel.setAlignment(Qt.AlignCenter)

        self.departmentLabel = QLabel('Department:')
        self.departmentLabel.setMinimumSize(100, 50)
        self.departmentLabel.setAlignment(Qt.AlignCenter)

        self.departmentLineEdit = QComboBox()
        self.departmentLineEdit.setStyleSheet(
            "QComboBox { combobox-popup: 0; }")
        self.departmentLineEdit.setEditable(True)
        self.departmentLineEdit.setInsertPolicy(QComboBox.NoInsert)
        self.departmentLineEdit.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.departmentLineEdit.clear()
        self.departmentLineEdit.addItem("")
        self.departmentLineEdit.setMinimumSize(200, 50)
        self.departmentLineEdit.addItems(departments_list)

        self.userLabel = QLabel('User:')
        self.userLabel.setMinimumSize(100, 50)
        self.userLabel.setAlignment(Qt.AlignCenter)

        self.userLineEdit = QComboBox()
        self.userLineEdit.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.userLineEdit.setEditable(True)
        self.userLineEdit.setInsertPolicy(QComboBox.NoInsert)
        self.userLineEdit.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.userLineEdit.clear()
        self.userLineEdit.addItem("")
        self.userLineEdit.setMinimumSize(200, 50)
        self.userLineEdit.addItems(users_list)

        self.dateLabel = QLabel('Date:')
        self.dateLabel.setMinimumSize(100, 50)
        self.dateLabel.setAlignment(Qt.AlignCenter)

        self.current_day = datetime.now().strftime("%Y:%m:%d")

        self.dateLineEdit = QLineEdit()
        self.dateLineEdit.setText(self.current_day)
        self.dateLineEdit.setMinimumSize(100, 50)

        self.csv_create = QPushButton('create CSV')
        self.dateLineEdit.returnPressed.connect(self.search)
        self.userLineEdit.activated.connect(self.search)
        self.projectLineEdit.activated.connect(self.search)
        self.departmentLineEdit.activated.connect(self.search)

        self.refresh = QPushButton('Refresh')
        self.refresh.pressed.connect(self.search_all)

        self.next_button = QPushButton("Next")
        self.next_button.setShortcut(Qt.Key_Right)
        self.prev_button = QPushButton("Previous")
        self.prev_button.setShortcut(Qt.Key_Left)
        self.page_button = QPushButton(str(current_page))
        self.page_button.clicked.connect(self.show_first_page)

        self.next_button.clicked.connect(self.show_next_page)
        self.prev_button.clicked.connect(self.show_previous_page)

        self.csv_create.clicked.connect(self.export_csv)

        if self.role == 'admin':
            self.tableWidget = QTableWidget()
            self.tableWidget.resizeRowsToContents()
            self.tableWidget.setColumnCount(11)
            self.tableWidget.setColumnWidth(0, 100)
            self.tableWidget.setColumnWidth(1, 100)
            self.tableWidget.setColumnWidth(2, 150)
            self.tableWidget.setColumnWidth(3, 150)
            self.tableWidget.setColumnWidth(4, 350)
            self.tableWidget.setColumnWidth(5, 200)
            self.tableWidget.setColumnWidth(6, 200)
            self.tableWidget.setColumnWidth(7, 150)
            self.tableWidget.setColumnWidth(8, 150)
            self.tableWidget.setColumnWidth(9, 150)
            self.tableWidget.setColumnWidth(10, 100)

            self.tableWidget.setHorizontalHeaderLabels(
                ['Name', 'Date', 'Day', 'Projects', 'Tasks', 'Department', 'System Id', 'Status', 'In Time', 'Out Time', 'Working Time'])

        if self.role == 'user':
            self.tableWidget = QTableWidget()
            self.tableWidget.resizeRowsToContents()
            self.tableWidget.setColumnCount(8)
            self.tableWidget.setColumnWidth(0, 150)
            self.tableWidget.setColumnWidth(1, 150)
            self.tableWidget.setColumnWidth(2, 150)
            self.tableWidget.setColumnWidth(3, 150)
            self.tableWidget.setColumnWidth(4, 500)
            self.tableWidget.setColumnWidth(5, 250)
            self.tableWidget.setColumnWidth(6, 250)
            self.tableWidget.setColumnWidth(7, 250)

            self.tableWidget.setHorizontalHeaderLabels(
                ['Name', 'Date', 'Day', 'Projects', 'Tasks', 'Department', 'System Id', 'Status'])

        # Create the layout
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.logo)
        hbox1.addWidget(self.projectLabel)
        hbox1.addWidget(self.projectLineEdit)
        hbox1.addWidget(self.departmentLabel)
        hbox1.addWidget(self.departmentLineEdit)
        hbox1.addWidget(self.userLabel)
        hbox1.addWidget(self.userLineEdit)
        hbox1.addWidget(self.dateLabel)
        hbox1.addWidget(self.dateLineEdit)
        hbox1.addWidget(self.refresh)
        hbox1.addWidget(self.csv_create)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.tableWidget)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.prev_button)
        hbox3.addWidget(self.page_button)
        hbox3.addWidget(self.next_button)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        widget = QWidget()
        widget.setLayout(vbox)
        self.setCentralWidget(widget)

        self.setWindowTitle('Timesheet')
        self.results_data(current_page)

        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def show_first_page(self):
        global current_page
        current_page = 1
        self.page_button.setText(str(current_page))
        self.search()

    def show_next_page(self):
        global current_page
        current_page += 1
        self.page_button.setText(str(current_page))
        self.search()

    def show_previous_page(self):
        global current_page
        if current_page > 1:
            current_page -= 1
            self.page_button.setText(str(current_page))
            self.search()

    def get_still_working(self, result):

        if result["date"] == datetime.now().strftime("%Y:%m:%d") and result['stop_time'] == "working":
            return "Available"
        else:

            return "Left"

    def results_data(self, page_num, query={}):
        # Execute the search query
        skip_items = (page_num - 1) * items_per_page
        self.data = []
        self.results = self.collection.find(query)

        for document in self.results:
            self.data.append(document)

        # self.results = self.collection.find(query).sort("date", DESCENDING)
        self.results = self.collection.find(query).skip(
            skip_items).limit(items_per_page).sort([("date", DESCENDING), ("login", 1)])

        # Display the results in the table widget
        self.tableWidget.setRowCount(0)
        for row, result in enumerate(self.results):

            projects = '\n'.join(result['project'])
            x = self.get_still_working(result)
            task_data = str()
            for key in result['task']:
                task_data += key + ":" + result['task'][key] + "\n"
            self.tableWidget.insertRow(row)
            self.tableWidget.setRowHeight(row, 70)
            department_align = QTableWidgetItem(
                result['department'])
            department_align.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(
                row, 5, QTableWidgetItem(department_align))

            user_id_align = QTableWidgetItem(result['login'])
            user_id_align.setTextAlignment(Qt.AlignCenter)

            self.tableWidget.setItem(row, 0, user_id_align)

            date_align = QTableWidgetItem(result['date'])
            date_align.setTextAlignment(Qt.AlignCenter)

            self.tableWidget.setItem(
                row, 1, QTableWidgetItem(date_align))

            day_align = QTableWidgetItem(result['day'])
            day_align.setTextAlignment(Qt.AlignCenter)

            self.tableWidget.setItem(
                row, 2, QTableWidgetItem(day_align))

            self.tableWidget.setItem(row, 3, QTableWidgetItem(projects))
            self.tableWidget.setItem(row, 4, QTableWidgetItem(task_data))

            stop_time_align = QTableWidgetItem(result['stop_time'])
            stop_time_align.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(
                row, 9, stop_time_align)

            work_time_align = QTableWidgetItem(result['work_time'])
            work_time_align.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(
                row, 10, work_time_align)

            system_id_align = QTableWidgetItem(result['system_id'])
            system_id_align.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(
                row, 6, system_id_align)

            self.tableWidget.setItem(
                row, 7, QTableWidgetItem(x))
            item = QTableWidgetItem(x)
            if x == 'Available':
                gradient = QLinearGradient(0, 0, 0, 1)
                gradient.setStart(0, 10)
                gradient.setFinalStop(0, 90)
                gradient.setColorAt(0, QColor(33, 188, 86))
                gradient.setColorAt(1, QColor(164, 216, 158))
                item.setBackground(gradient)
                item.setTextAlignment(Qt.AlignCenter)
            else:
                gradient = QLinearGradient(0, 0, 0, 1)
                gradient.setStart(0, 10)
                gradient.setFinalStop(0, 90)
                gradient.setColorAt(0, QColor(188, 98, 86))
                gradient.setColorAt(1, QColor(216, 164, 158))
                item.setBackground(gradient)
                item.setTextAlignment(Qt.AlignCenter)

            self.tableWidget.setItem(row, 7, item)

            start_time_align = QTableWidgetItem(result['start_time'])
            start_time_align.setTextAlignment(Qt.AlignCenter)

            self.tableWidget.setItem(
                row, 8, QTableWidgetItem(start_time_align))

    def search_all(self):

        query = {}
        self.results_data(current_page, query)

    def search(self):
        # Get the search criteria
        project = self.projectLineEdit.currentText()
        user = self.userLineEdit.currentText()
        date_str = self.dateLineEdit.text()
        department = self.departmentLineEdit.currentText()

        # Build the search query
        query = {}
        if project:
            query['project'] = project
        if user:
            query['login'] = user
        if date_str:
            query['date'] = date_str
        if department:
            query['department'] = department

        self.results_data(current_page, query)

    def export_csv(self):
        # Prompt user for file save location
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to CSV", "", "CSV Files (*.csv)", options=options)
        if not file_path:
            return

        # Write data to CSV file
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(list(self.data[0].keys()))
            for row in self.data:
                writer.writerow(row.values())


if __name__ == '__main__':

    app = QApplication(sys.argv)

    app.setStyleSheet(
        open('login.qss').read())

    ex = Timesheet()
    ex.show()
    sys.exit(app.exec_())
