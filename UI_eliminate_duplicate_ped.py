#!/usr/bin/env python
from sys import argv, exit
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import QtCore, QtWidgets
from EliminateDuplicateDataUi import Ui_EliminateDuplicateData
from Generate_Figs import *  # 绘图函数


class UiEliminateDuplicatePed(QDialog, Ui_EliminateDuplicateData):
    message = QtCore.pyqtSignal(list)

    def __init__(self, ped_array, rawdata, parent=None):
        super(UiEliminateDuplicatePed, self).__init__(parent)
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.ok_clicked_callback)
        self.buttonBox.rejected.connect(self.cancel_clicked_callback)
        self.ped_array = ped_array

        posi = ['0,0,1,1', '0,1,1,1', '0,2,1,1', '0,3,1,1', '0,4,1,1',
                '1,0,1,1', '1,1,1,1', '1,2,1,1', '1,3,1,1', '1,4,1,1',
                '2,0,1,1', '2,1,1,1', '2,2,1,1', '2,3,1,1', '2,4,1,1',
                '3,0,1,1', '3,1,1,1', '3,2,1,1', '3,3,1,1', '3,4,1,1',
                '4,0,1,1', '4,1,1,1', '4,2,1,1', '4,3,1,1', '4,4,1,1']

        last_item = -10
        self.record_list = []
        for i, item in enumerate(ped_array):
            if abs(last_item - item) < 3:
                self.record_list.append(i)
            last_item = item
        real_duplicate_ped = self.duplicate_record(self.record_list)  # 具体是哪几个pedal重复了 (index)

        for i, ch in enumerate(ped_array):  # 添加新CheckBox
            exec('self.checkBox' + str(i) + '= QtWidgets.QCheckBox(self.groupBox)')
            eval('self.checkBox' + str(i) + '.setObjectName("' + str(i) + '")')
            eval('self.gridLayout.addWidget(self.checkBox' + str(i) + ',' + posi[i] + ')')
            eval('self.checkBox' + str(i) + '.setText("' + str(ch.__round__(1)) + '")')
            if i not in real_duplicate_ped:
                eval('self.checkBox' + str(i) + '.setDisabled(True)')

        dr_raw_data = MyFigureCanvas(width=15, height=8, plot_type='2d-multi')
        PicToolBar = NavigationBar(dr_raw_data, self)
        self.verticalLayout.addWidget(PicToolBar)
        self.verticalLayout.addWidget(dr_raw_data)
        dr_raw_data.plot_raw_data(time=range(rawdata.shape[0]), df=rawdata)

    @staticmethod
    def duplicate_record(record_list):
        real_duplicate_ped = []
        for i in record_list:
            real_duplicate_ped.append(i-1)
            real_duplicate_ped.append(i)
        real_duplicate_ped = list(set(real_duplicate_ped))
        return real_duplicate_ped

    def ok_clicked_callback(self):
        checked_list = []
        for i in range(self.gridLayout.count()):
            try:
                checked_list.append(self.gridLayout.itemAt(i).widget().isChecked())
            except AttributeError:
                pass

        self.message.emit(checked_list)
        self.close()

    def cancel_clicked_callback(self):
        self.close()


if __name__ == '__main__':
    app = QApplication(argv)
    dlg = UiEliminateDuplicatePed([0, 2.42, 5.32, 20.0, 33.03], rawdata=[])
    dlg.show()
    exit(app.exec())
