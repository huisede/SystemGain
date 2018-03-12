# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'EliminateDuplicateDataUi.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_EliminateDuplicateData(object):
    def setupUi(self, EliminateDuplicateData):
        EliminateDuplicateData.setObjectName("EliminateDuplicateData")
        EliminateDuplicateData.resize(829, 518)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(EliminateDuplicateData)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.groupBox = QtWidgets.QGroupBox(EliminateDuplicateData)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_2.addWidget(self.groupBox)
        self.buttonBox = QtWidgets.QDialogButtonBox(EliminateDuplicateData)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(EliminateDuplicateData)
        self.buttonBox.accepted.connect(EliminateDuplicateData.accept)
        self.buttonBox.rejected.connect(EliminateDuplicateData.reject)
        QtCore.QMetaObject.connectSlotsByName(EliminateDuplicateData)

    def retranslateUi(self, EliminateDuplicateData):
        _translate = QtCore.QCoreApplication.translate
        EliminateDuplicateData.setWindowTitle(_translate("EliminateDuplicateData", "剔除重复数据"))
        self.groupBox.setTitle(_translate("EliminateDuplicateData", "剔除信号选择"))

