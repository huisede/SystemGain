from sys import argv, exit
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import QtCore
from SetIndexName import Ui_Dialog


class UiSetIndexName(QDialog, Ui_Dialog):
    message = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(UiSetIndexName, self).__init__(parent)
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.ok_clicked_callback)
        self.buttonBox.rejected.connect(self.cancel_clicked_callback)

    def ok_clicked_callback(self):
        if self.textEdit.toPlainText() is not '':
            self.message.emit(self.textEdit.toPlainText())

    def cancel_clicked_callback(self):
        self.close()


if __name__ == '__main__':
    app = QApplication(argv)
    dlg = UiSetIndexName()
    dlg.show()
    exit(app.exec())
