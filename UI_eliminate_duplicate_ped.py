#!/usr/bin/env python
from sys import argv, exit
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import QtCore, QtWidgets, QtGui
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

        color_array = ['#FFA500',  # 橙色
                       '#3CB371',  # 春绿
                       '#4169E1',  # 皇家蓝
                       '#DF12ED',  # 紫
                       '#FD143C',  # 鲜红
                       '#D2691E',  # 巧克力
                       '#696969',  # 暗灰
                       '#40E0D0',  # 绿宝石
                       '#9400D3',  # 紫罗兰
                       ]
        color_array_rgb = [(255, 165, 0, 0.3),
                           (60, 179, 113, 0.3),
                           (65, 105, 225, 0.3),
                           (223, 18, 237, 0.3),
                           (253, 20, 60, 0.3),
                           (210, 105, 30, 0.3),
                           (105, 105, 105, 0.3),
                           (64, 224, 208, 0.3),
                           (148, 0, 211, 0.3)]
        # last_item = -10
        # for i, item in enumerate(ped_array):
        #     if abs(last_item - item) < 3:
        #         self.record_list.append(i)
        #     last_item = item
        # real_duplicate_ped = self.duplicate_record(self.record_list)  # 具体是哪几个pedal重复了 (index)

        real_duplicate_ped = self.mark_duplicate_group(ped_array)

        for i, ch in enumerate(ped_array):  # 添加新CheckBox
            exec('self.checkBox' + str(i) + '= QtWidgets.QCheckBox(self.groupBox)')
            eval('self.checkBox' + str(i) + '.setObjectName("' + str(i) + '")')
            eval('self.gridLayout.addWidget(self.checkBox' + str(i) + ',' + posi[i] + ')')
            eval('self.checkBox' + str(i) + '.setText("' + str(ch.__round__(1)) + '")')
            if real_duplicate_ped[i] == 0:
                eval('self.checkBox' + str(i) + '.setDisabled(True)')
            else:
                # eval('self.checkBox' + str(i) + ".setStyleSheet('QCheckBox{background-color:" + color_array[
                #     real_duplicate_ped[i]] + " }')")
                eval('self.checkBox' + str(i) + ".setStyleSheet('QCheckBox{background-color: rgba" + str(color_array_rgb[
                    real_duplicate_ped[i]]) + " }')")

        dr_raw_data = MyFigureCanvas(width=15, height=8, plot_type='2d-multi')
        PicToolBar = NavigationBar(dr_raw_data, self)
        self.verticalLayout.addWidget(PicToolBar)
        self.verticalLayout.addWidget(dr_raw_data)
        dr_raw_data.plot_raw_data(time=range(rawdata.shape[0]), df=rawdata)

    @staticmethod
    def mark_duplicate_group(ped_array):
        record_list = [int(i) for i in zeros(len(ped_array))]
        color = 1
        trigger = False
        for i, item in enumerate(ped_array):
            if record_list[i] > 0:  # 若已被标记
                continue
            for j, item_ in enumerate(ped_array[i + 1:]):
                if abs(item - item_) < 2.5:
                    record_list[i] = color  # 被重复组本身标记颜色
                    record_list[i + 1 + j] = color  # 重复组标记颜色
                    trigger = True
            if trigger:  # 若本次循环出现过标记，下次配色更换
                color += 1
                trigger = False
        return record_list

    @staticmethod
    def duplicate_record(record_list):
        real_duplicate_ped = []
        for i in record_list:
            real_duplicate_ped.append(i - 1)
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
