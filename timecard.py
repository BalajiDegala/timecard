import os
import sys
from dotenv import load_dotenv

from PyQt5.QtWidgets import QCalendarWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout, QMenu, QAction, QStatusBar, QMessageBox
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QLabel, QSplitter, QSizePolicy,  QPushButton, QLineEdit, QMenuBar, QApplication, QComboBox, QCompleter

from PyQt5.QtCore import Qt, QTimer, QDate, QPoint, QRect
from PyQt5.QtGui import QColor, QPixmap, QFont,  QPen
import pymongo
import getpass
from datetime import date, datetime, timedelta
from time import strftime, sleep
from pathlib import Path
import socket
import time

load_dotenv()
sys.path.append(os.getcwd())


PORT = int(os.environ["port"])
MONGO_URL = os.environ["mongo_url"]

connection = pymongo.MongoClient(MONGO_URL, PORT)
database = connection['ddConnect']
projects = database['projects']
time_data = database['time_data']
users = database['users']
userid = getpass.getuser()
tmpuser = time_data.find({'login': userid})
documents = []
for document in tmpuser:
    documents.append(document)


class Calendar(QCalendarWidget):

    def paintCell(self, painter, rect, date):
        super(Calendar, self).paintCell(painter, rect, date)

        for document in documents:
            if date == QDate.fromString(document['date'], Qt.ISODate):

                font = QFont("Times")
                font.setPixelSize(12)
                painter.setFont(font)
                pen = QPen()
                try:
                    if int(document['work_time'][:-3]) <= 8:
                        pen.setColor(QColor(250, 100, 100))
                    else:
                        pen.setColor(QColor(199, 219, 50))
                except:
                    pen.setColor(QColor(100, 100, 200))

                painter.setPen(pen)

                painter.drawText(rect.topLeft() + QPoint(0, 7),
                                 document['work_time'])


class MainPage(QMainWindow):
    def __init__(self, userid):

        super().__init__()

        self.setObjectName("MainWindow")
        self.setWindowTitle("TimeCard")
        self.center()
        self.today = str(date.today())
        self.start_time = None
        self.stop_time = None

        self.db_connect()
        try:
            self.widget(userid)

            self.statusBar().showMessage(
                "Lets begin your day with TIMECARD")
            self.statusBar().setToolTip(
                "Hello DDIAN")

            self.time_compare = datetime.now().replace(microsecond=0) + timedelta(hours=-7)
            self.setWindowFlag(Qt.WindowCloseButtonHint, False)

            try:
                self.get_document()
                self.set_data()

            except IndexError:
                self.start_Button.setDisabled(False)
        except TypeError:
            self.statusBar().showMessage(
                "username  = {} , check if user name is localhost & Please reach out to Production or IT ".format(userid))
        except Exception as error:
            self.statusBar().showMessage(
                "Error : {} , Please reach out to Production or IT ".format(error))

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def get_document(self):
        tmpouser = self.time_data.find({"$and": [{'login': self.user_id}, {'query_date': self.time_compare.strftime("%Y:%m:%d")}]}
                                       ).sort('start_time', direction=-1)[0]

        return tmpouser

    def db_connect(self):
        self.connection = pymongo.MongoClient(MONGO_URL, PORT)
        self.database = self.connection['ddConnect']
        self.projects = self.database['projects']
        self.time_data = self.database['time_data']
        self.users = self.database['users']

    def widget(self, userid):

        self.user = self.users.find_one({'login': userid})
        self.user_id = self.user["login"]

        # Vertical layout
        self.mainLayout = QVBoxLayout()
        self.mainLayout_2 = QVBoxLayout()

        container1 = QWidget()
        container1.setLayout(self.mainLayout)
        container2 = QWidget()
        container2.setLayout(self.mainLayout_2)
        container2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(container1)
        splitter.addWidget(container2)

        # layout

        self.header()
        self.user_detail_header()
        self.user_details()
        self.start_stop_details()
        self.project_task_details()
        # self.table_details()
        self.setCentralWidget(splitter)

        self.menu()
        # self.calender_details()

    def header(self):

        # Horizontal layout

        self.logo = QLabel()
        pixmap = QPixmap('dd.png')

        x = pixmap.scaled(200, 100, Qt.KeepAspectRatio,
                          Qt.SmoothTransformation)

        self.logo.setPixmap(x)
        self.logo.setStyleSheet('background-color: #3A3A3A')

        self.full_name = QPushButton("     " +
                                     self.user['firstname'].upper() + " " + self.user['lastname'].upper() + "    ")

        self.full_name.setStyleSheet('background-color: #3A3A3A')
        self.full_name.setStyleSheet(
            'background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646); ')

        self.full_name.setMinimumSize(100, 50)

        self.current_date = QPushButton()
        self.current_date.setMinimumSize(100, 50)

        self.current_date.setText(self.today)

        # Time component

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.Time)
        self.timer.start(1000)
        self.current_time = QPushButton()
        self.current_time.setMinimumSize(100, 50)

        self.current_time.setText(strftime("%H"+":"+"%M"+":"+"%S"))

        self.header_layout = QHBoxLayout()
        self.header_layout.setObjectName("header_layout")
        self.header_layout.addWidget(self.logo)
        self.header_layout.addWidget(self.full_name)
        self.header_layout.addWidget(self.current_date)
        self.header_layout.addWidget(self.current_time)

        self.mainLayout.addLayout(self.header_layout)

    def user_detail_header(self):
        self.em_no = QLabel()
        self.em_no.setStyleSheet(
            'background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646); ')

        self.em_no.setFrameShape(QFrame.NoFrame)
        self.em_no.setLineWidth(1)
        self.em_no.setAlignment(Qt.AlignCenter)
        self.em_no.setText("Employee No")
        self.em_no.setMaximumSize(500, 30)

        self.em_name = QLabel()
        self.em_name.setStyleSheet(
            'background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);')

        self.em_name.setFrameShape(QFrame.NoFrame)
        self.em_name.setAlignment(Qt.AlignCenter)
        self.em_name.setText("Employee Name")
        self.em_name.setMaximumSize(500, 30)

        self.em_department = QLabel()
        self.em_department.setStyleSheet(
            'background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);')

        self.em_department.setFrameShape(QFrame.NoFrame)
        self.em_department.setAlignment(Qt.AlignCenter)
        self.em_department.setText("Department")
        self.em_department.setMaximumSize(500, 30)

        self.em_email = QLabel()
        self.em_email.setStyleSheet(
            'background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);')

        self.em_email.setFrameShape(QFrame.NoFrame)
        self.em_email.setAlignment(Qt.AlignCenter)
        self.em_email.setText("Email")
        self.em_email.setMaximumSize(500, 30)

        self.user_detail_header = QHBoxLayout()
        self.user_detail_header.setSpacing(1)

        self.user_detail_header.addWidget(self.em_no)
        self.user_detail_header.addWidget(self.em_name)
        self.user_detail_header.addWidget(self.em_department)
        self.user_detail_header.addWidget(self.em_email)
        self.mainLayout.addLayout(self.user_detail_header)

    def user_details(self):

        self.sg_emp_id = QLabel()
        self.sg_emp_id.setEnabled(True)
        self.sg_emp_id.setLineWidth(1)
        self.sg_emp_id.setAlignment(Qt.AlignCenter)
        if self.user['sg_emp_id'] is not None:
            self.sg_emp_id.setText(self.user['sg_emp_id'])
        else:
            self.sg_emp_id.setText("update on shotgun")

        self.sg_emp_id.setMaximumSize(500, 50)

        self.login = QLabel()
        self.login.setFrameShadow(QFrame.Plain)
        self.login.setLineWidth(1)
        self.login.setAlignment(Qt.AlignCenter)
        self.login.setText(self.user["login"])

        self.login.setMaximumSize(500, 50)

        self.department = QLabel()
        self.department.setLineWidth(1)
        self.department.setAlignment(Qt.AlignCenter)
        if self.user['department'] is not None:
            self.department.setText(self.user['department']['name'])
        else:
            self.department.setText("update on shotgun")

        self.department.setMaximumSize(500, 50)

        self.email = QLabel()
        self.email.setLineWidth(1)
        self.email.setAlignment(Qt.AlignCenter)
        self.email.setText(self.user["email"])

        self.email.setMaximumSize(500, 50)

        self.user_layout = QHBoxLayout()

        self.user_layout.setSpacing(3)
        self.user_layout.addWidget(self.sg_emp_id)
        self.user_layout.addWidget(self.login)
        self.user_layout.addWidget(self.department)
        self.user_layout.addWidget(self.email)
        self.mainLayout.addLayout(self.user_layout)

    def start_stop_details(self):

        try:

            self.update_button = QPushButton()
            self.update_button.setToolTip("Click UPDATE --> update event")
            self.update_button.setText("Update")
            self.update_button.move(20, 20)
            self.update_button.setMinimumHeight(50)
            self.update_button.setShortcut('u')

            self.update_button.clicked.connect(self.update_details)

            self.start_Button = QPushButton()
            self.start_Button.setMinimumSize(100, 50)
            self.start_Button.setToolTip(" Click START --> Day event starts")
            self.start_Button.setDisabled(True)

            self.start_Button.clicked.connect(self.Timer)
            self.start_Button.setText("Start")

            self.intime = QLabel()
            self.intime.setFrameShape(QFrame.Box)
            self.intime.setAlignment(Qt.AlignCenter)

            self.intime.setMaximumHeight(48)

            self.stop_Button = QPushButton()
            self.stop_Button.setToolTip(" Click STOP --> Day event stops")
            self.stop_Button.setMinimumSize(100, 50)

            self.stop_Button.setText("Stop")

            self.outtime = QLabel()
            self.outtime.setFrameShape(QFrame.Box)
            self.outtime.setAlignment(Qt.AlignCenter)

            self.outtime.setMaximumHeight(48)

            self.start_stop_layout = QHBoxLayout()
            self.start_stop_layout.setObjectName("start_stop_layout")
            self.start_stop_layout.addWidget(self.start_Button)
            self.start_stop_layout.addWidget(self.intime)
            self.start_stop_layout.addWidget(self.update_button)
            self.start_stop_layout.addWidget(self.stop_Button)
            self.start_stop_layout.addWidget(self.outtime)
            self.mainLayout.addLayout(self.start_stop_layout)

            self.start_Button.clicked.connect(self.start_timer)
            self.stop_Button.clicked.connect(self.stop_timer)

        except:
            self.statusBar().showMessage("first start to update")

    def project_task_details(self):

        projects = self.projects.find()
        project_list = []
        for i in projects:
            project_list.append(i["name"])
        project_list.append("")
        project_list = project_list[::-1]
        self.project = QPushButton()
        self.project.setText("Project")
        self.project.setMinimumHeight(50)

        self.projectEdit_1 = QComboBox()
        self.projectEdit_1.addItems(project_list)
        self.projectEdit_1.setEditable(True)
        self.projectEdit_1.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.projectEdit_1.setMinimumHeight(50)

        self.projectEdit_2 = QComboBox()
        self.projectEdit_2.addItems(project_list)
        self.projectEdit_2.setEditable(True)
        self.projectEdit_2.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.projectEdit_2.setMinimumHeight(50)

        self.projectEdit_3 = QComboBox()
        self.projectEdit_3.addItems(project_list)
        self.projectEdit_3.setEditable(True)
        self.projectEdit_3.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.projectEdit_3.setMinimumHeight(50)

        self.projectEdit_4 = QComboBox()
        self.projectEdit_4.addItems(project_list)
        self.projectEdit_4.setEditable(True)
        self.projectEdit_4.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.projectEdit_4.setMinimumHeight(50)
        self.projectEdit_4.setMinimumWidth(260)

        self.projectEdit_1.currentIndexChanged.connect(self.project_name)
        self.projectEdit_2.currentIndexChanged.connect(self.project_name)
        self.projectEdit_3.currentIndexChanged.connect(self.project_name)
        self.projectEdit_4.currentIndexChanged.connect(self.project_name)

        self.task = QPushButton()
        self.task.setText("Task")
        self.task.setMaximumHeight(50)

        self.taskEdit_1 = QLineEdit()
        self.taskEdit_1.setMinimumHeight(50)

        self.taskEdit_2 = QLineEdit()
        self.taskEdit_2.setMinimumHeight(50)

        self.taskEdit_3 = QLineEdit()
        self.taskEdit_3.setMinimumHeight(50)

        self.taskEdit_4 = QLineEdit()
        self.taskEdit_4.setMinimumHeight(50)

        self.taskEdit_1.returnPressed.connect(self.task_details)
        self.taskEdit_2.returnPressed.connect(self.task_details)
        self.taskEdit_3.returnPressed.connect(self.task_details)
        self.taskEdit_4.returnPressed.connect(self.task_details)

        self.calendar = Calendar(self)
        self.calendar.setGeometry(50, 10, 400, 250)
        self.calendar.setCursor(Qt.PointingHandCursor)

        font = QFont('Calibre', 8)

        self.calendar.setFont(font)

        self.project_task_layout = QGridLayout()

        self.project_task_layout.addWidget(self.project, 0, 0, 2, 1)
        self.project_task_layout.addWidget(self.projectEdit_1, 1, 0, 2, 1)
        self.project_task_layout.addWidget(self.projectEdit_2, 2, 0, 2, 1)
        self.project_task_layout.addWidget(self.projectEdit_3, 3, 0, 2, 1)
        self.project_task_layout.addWidget(self.projectEdit_4, 4, 0, 2, 1)

        self.project_task_layout.addWidget(self.task, 0, 1, 2, 1)
        self.project_task_layout.addWidget(self.taskEdit_1, 1, 1, 2, 1)
        self.project_task_layout.addWidget(self.taskEdit_2, 2, 1, 2, 1)
        self.project_task_layout.addWidget(self.taskEdit_3, 3, 1, 2, 1)
        self.project_task_layout.addWidget(self.taskEdit_4, 4, 1, 2, 1)

        self.project_task_layout.addWidget(
            self.calendar, 0, 3, 6, 1)

        self.mainLayout_2.addLayout(self.project_task_layout)

        self.setTabOrder(self.projectEdit_1, self.taskEdit_1)
        self.setTabOrder(self.projectEdit_2, self.taskEdit_2)
        self.setTabOrder(self.projectEdit_3, self.taskEdit_3)
        self.setTabOrder(self.projectEdit_4, self.taskEdit_4)

    def menu(self):

        self.menubar = QMenuBar(self)

        self.menubar.setGeometry(QRect(0, 0, 1010, 22))
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)

        self.menuTIME_CARD = QMenu(self.menubar)
        self.menuTIME_CARD.setTitle("TIME CARD")

        self.actionAbout = QAction(self)
        self.actionAbout.setText("About")
        self.actionAbout.triggered.connect(self.show_info_messagebox)

        self.actionExit = QAction(self)
        self.actionExit.setText("Exit")
        self.actionExit.setShortcut('Esc')
        self.actionExit.triggered.connect(app.quit)

        self.actionDocumentation = QAction(self)
        self.actionDocumentation.setText("Documentation")
        self.actionDocumentation.setShortcut('F1')

        self.actionDocumentation.triggered.connect(
            self.show_documentation_messagebox)

        self.menuTIME_CARD.addAction(self.actionAbout)
        self.menuTIME_CARD.addAction(self.actionExit)
        self.menuTIME_CARD.addAction(self.actionDocumentation)
        self.menubar.addAction(self.menuTIME_CARD.menuAction())

        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.statusbar.setStyleSheet(
            'background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);color: #fff;')

        self.setStatusBar(self.statusbar)

    def show_info_messagebox(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(" \u00A92023 DDI, Version 1.0.1")
        msg.setWindowTitle("Timecard")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.exec_()

    def show_documentation_messagebox(self):

        file = open("documentation.txt", "r")
        content = file.read()

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(content)
        msg.setWindowTitle("Documentation")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.exec_()

    def Time(self):
        self.current_time.setText(strftime("%H"+":"+"%M"+":"+"%S"))

    def Timer(self):
        now = datetime.now()
        time = now.strftime("%H:%M:%S")
        return time

    def start_timer(self):
        try:

            self.time_delta = datetime.now().replace(microsecond=0) + timedelta(hours=-7)
            self.start_time = datetime.now().strftime("%H:%M:%S")

            self.intime.setText(self.start_time)
            self.outtime.setText("")
            time_sheets = {
                'login': self.user_id,
                'date': datetime.today().strftime("%Y:%m:%d"),
                'day': datetime.today().strftime('%A'),
                'project': [self.projectEdit_1.currentText(), self.projectEdit_2.currentText(), self.projectEdit_3.currentText(), self.projectEdit_4.currentText()],
                'task': {self.projectEdit_1.currentText(): self.taskEdit_1.text(), self.projectEdit_2.currentText(): self.taskEdit_2.text(), self.projectEdit_3.currentText(): self.taskEdit_3.text(), self.projectEdit_4.currentText(): self.taskEdit_4.text()},
                'start_time': self.start_time,
                'stop_time': "Working",
                'work_time': "00:00",
                'time_delta': self.time_delta,
                'query_date': self.time_delta.strftime("%Y:%m:%d"),
                'system_id':  socket.gethostname(),
                'department': self.user['department']['name']

            }

            filtered_projects = [
                project for project in time_sheets['project'] if project]
            filtered_tasks = {
                key: value for key, value in time_sheets['task'].items() if value}

            time_sheets['task'] = filtered_tasks
            time_sheets['project'] = filtered_projects

            self.id = self.time_data.insert_one(time_sheets)
            self.id = self.id.inserted_id

            self.statusBar().showMessage(
                f"TimeCard initiated {self.id}, Dont forget to Terminate the session by pressing stop in the evening")
            self.start_Button.setDisabled(True)
            self.update_button.setDisabled(False)

        except AttributeError:
            self.statusBar().showMessage("TimeCard session not initiated")

    def set_data(self):
        tmpouser = self.get_document()
        self.intime.setText(tmpouser['start_time'])

        projects = tmpouser["project"]
        tasks = tmpouser["task"]

        try:
            if len(projects) > 0:
                self.projectEdit_1.setCurrentIndex(
                    self.projectEdit_1.findText(projects[0]))
            if len(tasks) > 0:
                self.taskEdit_1.setText(tasks[projects[0]])

            if len(projects) > 1:
                self.projectEdit_2.setCurrentIndex(
                    self.projectEdit_2.findText(projects[1]))
            if len(tasks) > 1:
                self.taskEdit_2.setText(tasks[projects[1]])

            if len(projects) > 2:
                self.projectEdit_3.setCurrentIndex(
                    self.projectEdit_3.findText(projects[2]))
            if len(tasks) > 2:
                self.taskEdit_3.setText(tasks[projects[2]])

            if len(projects) > 3:
                self.projectEdit_4.setCurrentIndex(
                    self.projectEdit_4.findText(projects[3]))
            if len(tasks) > 3:
                self.taskEdit_4.setText(tasks[projects[3]])
        except IndexError:
            pass

    def update_details(self):
        try:
            if self.user_id:
                tmpouser = self.get_document()

                time_sheets = {
                    'project': [self.projectEdit_1.currentText(), self.projectEdit_2.currentText(), self.projectEdit_3.currentText(), self.projectEdit_4.currentText()],
                    'task': {self.projectEdit_1.currentText(): self.taskEdit_1.text(), self.projectEdit_2.currentText(): self.taskEdit_2.text(), self.projectEdit_3.currentText(): self.taskEdit_3.text(), self.projectEdit_4.currentText(): self.taskEdit_4.text()},
                    'stop_time': "Working",

                }

                filtered_projects = [
                    project for project in time_sheets['project'] if project]
                filtered_tasks = {
                    key: value for key, value in time_sheets['task'].items() if value}

                time_sheets['task'] = filtered_tasks
                time_sheets['project'] = filtered_projects

                self.id = tmpouser['_id']
                self.start_time = tmpouser['start_time']
                self.time_delta = tmpouser['time_delta']

                # self.time_data.update_one(
                #     {"$and": [{"login": self.user_id}, {"date": datetime.today().strftime("%Y:%m:%d")}]}, {'$set': time_sheets})

                self.time_data.update_one(
                    {"_id": self.id}, {'$set': time_sheets})
                self.statusBar().showMessage("updated your details")

                self.set_data()

            else:
                self.statusBar().showMessage("TimeCard session not initiated")
        except:
            self.statusBar().showMessage("TimeCard session not initiated")

    def stop_timer(self):
        try:
            if self.user_id and self.start_time:
                msg = QMessageBox()
                msg.setWindowTitle("warning call # 38")

                res = msg.question(self, 'warning call # 36', "Do you want to proceed ",
                                   msg.Yes | msg.No)

                if res == msg.Yes:

                    self.time_beta = datetime.now().replace(microsecond=0) + timedelta(hours=-7)

                    self.stop_time = datetime.now().strftime("%H:%M:%S")
                    self.statusBar().showMessage(
                        "TimeCard session Teminated, Please close all the applications before leaving ")

                    time_difference = str(self.time_beta - self.time_delta)
                    working_time = time_difference[:-3]

                    time_sheets = {
                        'project': [self.projectEdit_1.currentText(), self.projectEdit_2.currentText(), self.projectEdit_3.currentText(), self.projectEdit_4.currentText()],
                        'task': {self.projectEdit_1.currentText(): self.taskEdit_1.text(), self.projectEdit_2.currentText(): self.taskEdit_2.text(), self.projectEdit_3.currentText(): self.taskEdit_3.text(), self.projectEdit_4.currentText(): self.taskEdit_4.text()},
                        'stop_time': self.stop_time,
                        'work_time': working_time
                    }

                    filtered_projects = [
                        project for project in time_sheets['project'] if project]
                    filtered_tasks = {
                        key: value for key, value in time_sheets['task'].items() if value}

                    time_sheets['task'] = filtered_tasks
                    time_sheets['project'] = filtered_projects

                    self.time_data.update_one(
                        {"_id": self.id}, {'$set': time_sheets})

                    self.outtime.setText(self.stop_time)
                    self.intime.setText("")

                    self.start_time = None
                    self.projectEdit_1.setCurrentIndex(0)
                    self.projectEdit_2.setCurrentIndex(0)
                    self.projectEdit_3.setCurrentIndex(0)
                    self.projectEdit_4.setCurrentIndex(0)

                    self.taskEdit_1.setText("")
                    self.taskEdit_2.setText("")
                    self.taskEdit_3.setText("")
                    self.taskEdit_4.setText("")

                    self.update_button.setDisabled(True)

                else:
                    msg.information(self, '', "Nothing Changed")
            else:
                self.statusBar().showMessage("Press Update to stop the session")

        except AttributeError:
            self.statusBar().showMessage("TimeCard session not initiated")

    def project_name(self):

        self.statusBar().showMessage('updated')

    def task_details(self):
        self.statusBar().showMessage('updated')


if __name__ == "__main__":

    userid = getpass.getuser()

    app = QApplication(sys.argv)
    w = MainPage(userid)
    w.setFixedWidth(1012)
    w.setFixedHeight(600)
    w.show()
    app.setStyleSheet(
        open('login.qss').read())

    sys.exit(app.exec_())
