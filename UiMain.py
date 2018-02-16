from sys import argv, exit
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets

from SystemGainUi import Ui_MainWindow  # 界面源码
from Generate_Figs import *  # 绘图函数
from Calculation_function import *  # 计算函数
from re import match  # 正则表达式
from ctypes import windll


try:
    temp1 = windll.LoadLibrary('DLL\\Qt5Core.dll')
    temp2 = windll.LoadLibrary('DLL\\Qt5Gui.dll')
    temp3 = windll.LoadLibrary('DLL\\Qt5Widgets.dll')
    temp4 = windll.LoadLibrary('DLL\\msvcp140.dll')
    temp5 = windll.LoadLibrary('DLL\\Qt5PrintSupport.dll')
except OSError as e:
    pass


class MainUiWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainUiWindow, self).__init__(parent)
        self.setupUi(self)
        self.initial()

        self.menu_InputData.triggered.connect(self.load_sys_gain_data)
        self.menu_Save.triggered.connect(self.save_sys_gain_data)
        self.action_Data_Viewer.triggered.connect(lambda: self.change_main_page(0))
        self.action_System_Gain.triggered.connect(lambda: self.change_main_page(1))
        self.action_Compare_Result.triggered.connect(lambda: self.change_main_page(2))
        self.SysGain_Cal.clicked.connect(self.cal_sys_gain_data)
        self.History_Data_Choose_PushButton.clicked.connect(self.history_data_reload)

        self.info_list = []
        self.MainProcess_thread = []
        # self.createContextMenu_RawDataView()
        self.combo_box_names = ['System_Gain_AT_DCT_Time',
                                'System_Gain_AT_DCT_Vspd',
                                'System_Gain_AT_DCT_Ped',
                                'System_Gain_AT_DCT_Acc',
                                'System_Gain_AT_DCT_Gear',
                                'System_Gain_AT_DCT_Toq',
                                'System_Gain_AT_DCT_Fuel',
                                'System_Gain_AT_DCT_EnSpd',
                                'System_Gain_AT_DCT_TbSpd']

        self.dr_acc_curve = MyFigureCanvas(width=6, height=4, plot_type='3d')
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(self.dr_acc_curve)
        self.PicToolBar_1 = NavigationBar(self.dr_acc_curve, self)
        self.System_Gain_AT_DCT_Fig_LayG1.addWidget(self.PicToolBar_1)
        self.System_Gain_AT_DCT_Fig_1.setScene(self.scene)
        self.System_Gain_AT_DCT_Fig_1.show()

        self.dr_sg_curve = MyFigureCanvas(width=6, height=4, plot_type='2d')
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(self.dr_sg_curve)
        self.PicToolBar_2 = NavigationBar(self.dr_sg_curve, self)
        self.System_Gain_AT_DCT_Fig_LayG2.addWidget(self.PicToolBar_2)
        self.System_Gain_AT_DCT_Fig_2.setScene(self.scene)
        self.System_Gain_AT_DCT_Fig_2.show()

        self.dr_cons_spd = MyFigureCanvas(width=6, height=4, plot_type='2d')
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(self.dr_cons_spd)
        self.PicToolBar_3 = NavigationBar(self.dr_cons_spd, self)
        self.System_Gain_AT_DCT_Fig_LayG3.addWidget(self.PicToolBar_3)
        self.System_Gain_AT_DCT_Fig_3.setScene(self.scene)
        self.System_Gain_AT_DCT_Fig_3.show()

        self.dr_shift_map = MyFigureCanvas(width=6, height=4, plot_type='2d')
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(self.dr_shift_map)
        self.PicToolBar_4 = NavigationBar(self.dr_shift_map, self)
        self.System_Gain_AT_DCT_Fig_LayG4.addWidget(self.PicToolBar_4)
        self.System_Gain_AT_DCT_Fig_4.setScene(self.scene)
        self.System_Gain_AT_DCT_Fig_4.show()

        self.dr_launch = MyFigureCanvas(width=6, height=4, plot_type='2d')
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(self.dr_launch)
        self.PicToolBar_5 = NavigationBar(self.dr_launch, self)
        self.System_Gain_AT_DCT_Fig_LayG5.addWidget(self.PicToolBar_5)
        self.System_Gain_AT_DCT_Fig_5.setScene(self.scene)
        self.System_Gain_AT_DCT_Fig_5.show()

        self.dr_ped_map = MyFigureCanvas(width=6, height=4, plot_type='2d')
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(self.dr_ped_map)
        self.PicToolBar_6 = NavigationBar(self.dr_ped_map, self)
        self.System_Gain_AT_DCT_Fig_LayG6.addWidget(self.PicToolBar_6)
        self.System_Gain_AT_DCT_Fig_6.setScene(self.scene)
        self.System_Gain_AT_DCT_Fig_6.show()

    # ---------------------------- 初始化 -----------------------------------------
    def initial(self):
        self.data_viewer_graphics_view = MyQtGraphicView(self.Data_Viewer_page)
        self.data_viewer_graphics_view.setObjectName("data_viewer_graphics_view")
        self.Data_Viewer_graphicsView_LayG.addWidget(self.data_viewer_graphics_view)
        # self.data_viewer_graphics_view.Message_Drag_accept.connect(self.show_data_edit_drag_pictures)  # 拖拽重绘
        self.data_viewer_graphics_view.Message_DoubleClick.connect(self.highlight_signal)  # 双击高亮
        # self.initial_data_edit()

    # ---------------------------- 右键菜单 -----------------------------------------

    def createContextMenu_RawDataView(self):
        '''

        :return:
        '''
        self.graphicsView_2.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.graphicsView_2.customContextMenuRequested.connect(lambda: self.showContextMenu('graphicsView_2'))
        self.graphicsView_2.contextMenu = QtWidgets.QMenu(self)
        self.graphicsView_2.actionA = self.graphicsView_2.contextMenu.addAction(QtGui.QIcon("images/0.png"), u'|  标记')
        self.graphicsView_2.actionA.triggered.connect(self.select_marker)

        # 添加二级菜单
        self.graphicsView_2.second = self.graphicsView_2.contextMenu.addMenu(QtGui.QIcon("images/0.png"), u"|  二级菜单")
        self.graphicsView_2.actionD = self.graphicsView_2.second.addAction(QtGui.QIcon("images/0.png"), u'|  动作A')
        self.graphicsView_2.actionE = self.graphicsView_2.second.addAction(QtGui.QIcon("images/0.png"), u'|  动作B')
        self.graphicsView_2.actionF = self.graphicsView_2.second.addAction(QtGui.QIcon("images/0.png"), u'|  动作C')

        return

    # def createContextMenu_sg_fig_view(self):
    #     '''
    #
    #     :return:
    #     '''
    #     self.graphicsView_3.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    #     self.graphicsView_3.customContextMenuRequested.connect(lambda: self.showContextMenu('graphicsView_3'))
    #     self.graphicsView_3.contextMenu = QtWidgets.QMenu(self)
    #     self.graphicsView_3.actionA = self.graphicsView_3.contextMenu.addAction(QtGui.QIcon("./Image/DataIcon.png"),
    #                                                                             u'| 加速度相应曲面')
    #     self.graphicsView_3.actionB = self.graphicsView_3.contextMenu.addAction(QtGui.QIcon("./Image/DataIcon.png"),
    #                                                                             u"| 起步特性")
    #     self.graphicsView_3.actionC = self.graphicsView_3.contextMenu.addAction(QtGui.QIcon("./Image/DataIcon.png"),
    #                                                                             u"| Pedal Map")
    #     self.graphicsView_3.actionD = self.graphicsView_3.contextMenu.addAction(QtGui.QIcon("./Image/DataIcon.png"),
    #                                                                             u"| Shift Map")
    #     self.graphicsView_3.actionE = self.graphicsView_3.contextMenu.addAction(QtGui.QIcon("./Image/DataIcon.png"),
    #                                                                             u"| 香蕉图")
    #     self.graphicsView_3.actionF = self.graphicsView_3.contextMenu.addAction(QtGui.QIcon("./Image/DataIcon.png"),
    #                                                                             u"| 稳态车速")
    #     self.graphicsView_3.actionA.triggered.connect(lambda: self.change_handle_pictures('Acceleration Curve',
    #                                                                                       'PicToolBar_1',
    #                                                                                       'graphicsView_3',
    #                                                                                       'gridLayout_5'))
    #     self.graphicsView_3.actionB.triggered.connect(lambda: self.change_handle_pictures('Launch',
    #                                                                                       'PicToolBar_1',
    #                                                                                       'graphicsView_3',
    #                                                                                       'gridLayout_5'))
    #     self.graphicsView_3.actionC.triggered.connect(lambda: self.change_handle_pictures('Pedal Map',
    #                                                                                       'PicToolBar_1',
    #                                                                                       'graphicsView_3',
    #                                                                                       'gridLayout_5'))
    #     self.graphicsView_3.actionD.triggered.connect(lambda: self.change_handle_pictures('Shift Map',
    #                                                                                       'PicToolBar_1',
    #                                                                                       'graphicsView_3',
    #                                                                                       'gridLayout_5'))
    #     self.graphicsView_3.actionE.triggered.connect(lambda: self.change_handle_pictures('SystemGain Curve',
    #                                                                                       'PicToolBar_1',
    #                                                                                       'graphicsView_3',
    #                                                                                       'gridLayout_5'))
    #     self.graphicsView_3.actionF.triggered.connect(lambda: self.change_handle_pictures('Constant Speed',
    #                                                                                       'PicToolBar_1',
    #                                                                                       'graphicsView_3',
    #                                                                                       'gridLayout_5'))
    #
    #     self.graphicsView_4.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    #     self.graphicsView_4.customContextMenuRequested.connect(lambda: self.showContextMenu('graphicsView_4'))
    #     self.graphicsView_4.contextMenu = QtWidgets.QMenu(self)
    #     self.graphicsView_4.actionA = self.graphicsView_4.contextMenu.addAction(QtGui.QIcon("./Image/DataIcon.png"),
    #                                                                             u'| 加速度相应曲面')
    #     self.graphicsView_4.actionB = self.graphicsView_4.contextMenu.addAction(QtGui.QIcon("./Image/DataIcon.png"),
    #                                                                             u"| 起步特性")
    #     self.graphicsView_4.actionC = self.graphicsView_4.contextMenu.addAction(QtGui.QIcon("./Image/DataIcon.png"),
    #                                                                             u"| Pedal Map")
    #     self.graphicsView_4.actionD = self.graphicsView_4.contextMenu.addAction(QtGui.QIcon("./Image/DataIcon.png"),
    #                                                                             u"| Shift Map")
    #     self.graphicsView_4.actionE = self.graphicsView_4.contextMenu.addAction(QtGui.QIcon("./Image/DataIcon.png"),
    #                                                                             u"| 香蕉图")
    #     self.graphicsView_4.actionF = self.graphicsView_4.contextMenu.addAction(QtGui.QIcon("./Image/DataIcon.png"),
    #                                                                             u"| 稳态车速")
    #     self.graphicsView_4.actionA.triggered.connect(lambda: self.change_handle_pictures('Acceleration Curve',
    #                                                                                       'PicToolBar_2',
    #                                                                                       'graphicsView_4',
    #                                                                                       'gridLayout_17'))
    #     self.graphicsView_4.actionB.triggered.connect(lambda: self.change_handle_pictures('Launch',
    #                                                                                       'PicToolBar_2',
    #                                                                                       'graphicsView_4',
    #                                                                                       'gridLayout_17'))
    #     self.graphicsView_4.actionC.triggered.connect(lambda: self.change_handle_pictures('Pedal Map',
    #                                                                                       'PicToolBar_2',
    #                                                                                       'graphicsView_4',
    #                                                                                       'gridLayout_17'))
    #     self.graphicsView_4.actionD.triggered.connect(lambda: self.change_handle_pictures('Shift Map',
    #                                                                                       'PicToolBar_2',
    #                                                                                       'graphicsView_4',
    #                                                                                       'gridLayout_17'))
    #     self.graphicsView_4.actionE.triggered.connect(lambda: self.change_handle_pictures('SystemGain Curve',
    #                                                                                       'PicToolBar_2',
    #                                                                                       'graphicsView_4',
    #                                                                                       'gridLayout_17'))
    #     self.graphicsView_4.actionF.triggered.connect(lambda: self.change_handle_pictures('Constant Speed',
    #                                                                                       'PicToolBar_2',
    #                                                                                       'graphicsView_4',
    #                                                                                       'gridLayout_17'))

    def showContextMenu(self, handle):
        '''''
        右键点击时调用的函数
        '''
        # 菜单显示前，将它移动到鼠标点击的位置
        eval('self.' + handle + '.contextMenu.exec_(QtGui.QCursor.pos())')  # 在鼠标位置显示
        print(QtGui.QCursor.pos())
        # self.contextMenu.show()

    # ---------------------------- 回调函数 -----------------------------------------
    # -----|主菜单

    def load_sys_gain_data(self):
        file = QFileDialog.getOpenFileName(self, filter='*.csv')
        file_path = file[0]
        self.MainProcess_thread_rd = ThreadProcess(method='sg_read_thread', filepath=file_path)
        self.MainProcess_thread_rd.Message_Finish.connect(self.initial_data_edit)
        self.MainProcess_thread_rd.Message_Finish.connect(lambda: self.combobox_index_initial(self.MainProcess_thread_rd.ax_holder_rd.file_columns_orig))
        self.MainProcess_thread_rd.start()

    def save_sys_gain_data(self):
        file = QFileDialog.getSaveFileName(self, filter='.pkl')
        file_path = file[0] + file[1]
        try:
            self.sl = SaveAndLoad()
            self.sl.store_result(file_path=file_path, store_data=self.MainProcess_thread_cal.ax_holder_SG)
        except Exception:
            pass

    # -----|--|主页面
    def change_main_page(self, index_page):
        self.MainStackedWidget.setCurrentIndex(index_page)

    # -----|--|Data Edit 页面
    def initial_data_edit(self):
        while self.verticalLayout.itemAt(0) is not None:  # 删除当前Lay中的元素
            try:
                self.verticalLayout.itemAt(0).widget().setParent(None)   # 删除当前Lay中widget元素，在此为CheckBox
                self.verticalLayout.itemAt(0).widget().deleteLater()
                self.verticalLayout.removeWidget(self.verticalLayout.itemAt(0).widget())
            except AttributeError:
                self.verticalLayout.removeItem(self.verticalLayout.itemAt(0))  # 删除当前Lay中spacer元素

        for i, ch in enumerate(self.MainProcess_thread_rd.ax_holder_rd.file_columns):  # 添加新CheckBox
            exec('self.checkBox' + ch + '= QtWidgets.QCheckBox(self.Data_Viewer_CheckBox_groupBox)')
            eval('self.checkBox' + ch + '.setObjectName("' + ch + '")')
            eval('self.verticalLayout.addWidget(self.checkBox' + ch + ')')
            eval('self.checkBox' + ch + '.setText("' + self.MainProcess_thread_rd.ax_holder_rd.file_columns_orig[i] + '")')

        spacer_item = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacer_item)  # 添加新spacer排版占位

    @QtCore.pyqtSlot(dict)
    def show_data_edit_common(self, dict_in):  # 原始数据编辑界面
        '''

        :param dict_in: Contains the specific input of the signal to plot
                        [fig_name(mostly same as signal_name), signal_name, Navigation bar needed? T/F]
        :return:
        '''
        raw_index = {'VehicleSpd': 'VehSpdAvgNonDrvnHSC1',
                     'AccPed': 'AccelActuPosHSC1',
                     'LongtiAcc': 'LongAccelG_M',
                     'time': 'Time_abs'}
        try:
            self.dr.fig.clear()
            self.dr.reset_i()
        except Exception as e:
            print(e)

        try:
            self.PicToolBar.press(self.PicToolBar.home())
            self.dr.plot_raw_data(
                time=self.MainProcess_thread.ax_holder_SG.sysGain_class.rawdata[raw_index['time']].tolist(),
                raw_data=self.MainProcess_thread.ax_holder_SG.sysGain_class.rawdata[
                    raw_index[dict_in['data']]].tolist(),
                legend=[dict_in['data']])
            self.dr.axes.set_title('Launch', fontsize=14)  # 这句话想办法写到Generate_Figs里面
            self.PicToolBar.dynamic_update()

            self.dr.mpl_connect('button_press_event', self.get_mouse_xy_plot)
        except Exception as e:
            print(e)

    @QtCore.pyqtSlot(dict)
    def show_data_edit_drag_pictures(self, dict_in):
        raw_index = {'VehicleSpd': 'VehSpdAvgNonDrvnHSC1',
                     'AccPed': 'AccelActuPosHSC1',
                     'LongtiAcc': 'LongAccelG_M',
                     'time': 'Time_abs'}
        try:
            self.PicToolBar.press(self.PicToolBar.home())
            self.dr.plot_raw_data(
                time=self.MainProcess_thread.ax_holder_SG.sysGain_class.rawdata[raw_index['time']].tolist(),
                raw_data=self.MainProcess_thread.ax_holder_SG.sysGain_class.rawdata[
                    raw_index[dict_in['data']]].tolist(),
                legend=[dict_in['data']])
            self.PicToolBar.dynamic_update()
        except Exception as e:
            print(e)
            print('from show_data_edit_drag_pictures')

    def select_marker(self):
        QtCore.Qt.Key_Left
        pass

    def highlight_signal(self):

        pass

    def get_mouse_xy_plot(self, event):
        self.xyCoordinates = [event.xdata, event.ydata]  # 捕捉鼠标点击的坐标
        print(self.xyCoordinates)

    # -----|--|System Gain
    def combobox_index_initial(self, item_list):  # 将文件中的所有字段写入列表
        for i in self.combo_box_names:  # 编号
            eval('self.' + i + '.clear()')  # 清空当前列表
            for j in item_list:
                eval('self.' + i + ".addItem('" + j + "')")
        self.combobox_index_pre_select(self.MainProcess_thread_rd.ax_holder_rd.pre_select_features())

    def combobox_index_pre_select(self, pre_select_item_index_list):  # 自动预选字段
        for i in range(self.combo_box_names.__len__()):  # 编号
            eval('self.' + self.combo_box_names[i] + '.setCurrentIndex('+str(pre_select_item_index_list[i])+')')

    def cal_sys_gain_data(self):
        feature_array = []
        for i in self.combo_box_names:  # 编号
            eval('feature_array.append(self.' + i + '.currentText())')
        self.MainProcess_thread_cal = ThreadProcess(method='sg_cal_thread',
                                                    raw_data=self.MainProcess_thread_rd.ax_holder_rd.sg_csv_data_ful,
                                                    feature_array=feature_array)
        self.MainProcess_thread_cal.Message_Finish.connect(self.show_ax_pictures_sg)
        self.MainProcess_thread_cal.start()

    def show_ax_pictures_sg(self):  # System Gain 绘图函数
        """
        
        :return:
        """

        # self.createContextMenu_sg_fig_view()

        self.dr_acc_curve.axes.clear()
        self.dr_acc_curve.plot_acc_response(data=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.accresponce.data,
                                            ped_avg=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.accresponce.pedal_avg)
        self.PicToolBar_1.press(self.PicToolBar_1.home())
        self.PicToolBar_1.dynamic_update()

        self.dr_sg_curve.axes.clear()
        self.dr_sg_curve.plot_systemgain_curve(vehspd_sg=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.vehspd_sg,
                                               acc_sg=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.acc_sg)
        self.PicToolBar_2.press(self.PicToolBar_2.home())
        self.PicToolBar_2.dynamic_update()

        self.dr_cons_spd.axes.clear()
        self.dr_cons_spd.plot_constant_speed(vehspd_cs=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.vehspd_cs,
                                             pedal_cs=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.pedal_cs)
        self.PicToolBar_3.press(self.PicToolBar_3.home())
        self.PicToolBar_3.dynamic_update()

        self.dr_shift_map.axes.clear()
        self.dr_shift_map.plot_shift_map(data=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.shiftmap.data)
        self.PicToolBar_4.press(self.PicToolBar_4.home())
        self.PicToolBar_4.dynamic_update()

        self.dr_launch.axes.clear()
        self.dr_launch.plot_launch(data=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.launch.data)
        self.PicToolBar_5.press(self.PicToolBar_5.home())
        self.PicToolBar_5.dynamic_update()

        self.dr_ped_map.axes.clear()
        self.dr_ped_map.plot_pedal_map(data=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.pedalmap.data)
        self.PicToolBar_6.press(self.PicToolBar_6.home())
        self.PicToolBar_6.dynamic_update()

    # -----|--|Comparison 页面
    def history_data_reload(self):
        file = QFileDialog.getOpenFileNames(self, filter='*.pkl')
        file_path_list = file[0]
        try:
            self.sl = SaveAndLoad()
            self.history_data = self.sl.reload_result(file_path_list=file_path_list)
            self.info_list.append('Import OK!')
            # self.InfoWidget.insertItem(1, self.info_list[0])
            self.InfoWidget.addItem(self.info_list[-1])
            self.InfoWidget.setCurrentRow(self.InfoWidget.count() - 1)  # 滚动条最下方
            self.history_data_plot()
        except Exception as e:
            print('From Reload History Data')
            print(e)

    def history_data_plot(self):

        dr_history_sg_curve = MyFigureCanvas(width=6, height=4, plot_type='2d')
        for i in range(len(self.history_data)):   # 将每次画一根线
            dr_history_sg_curve.plot_systemgain_curve(vehspd_sg=self.history_data[i].sysGain_class.systemgain.vehspd_sg,
                                                      acc_sg=self.history_data[i].sysGain_class.systemgain.acc_sg)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(dr_history_sg_curve)
        try:
            if self.History_Data_Comp_graphicsView_LayG1.itemAt(0):  # 如果已经有NVbar,删掉后重新捆绑
                self.History_Data_Comp_graphicsView_LayG1.itemAt(0).widget().deleteLater()
                self.History_Data_Comp_graphicsView_LayG1.removeWidget(self.History_Data_Comp_graphicsView_LayG1.itemAt(0).widget())
            else:
                # self.createContextMenu_sg_fig_view()  # 第一次初始化右键菜单，一次把两个canvas的菜单都初始化了  ！！！
                pass
            self.PicToolBar_history1 = NavigationBar(dr_history_sg_curve, self)
            self.History_Data_Comp_graphicsView_LayG1.addWidget(self.PicToolBar_history1)
            self.History_Data_Comp_graphicsView_1.setScene(self.scene)
            self.History_Data_Comp_graphicsView_1.show()
        except Exception as e:
            print(e)

        dr_history_cons_spd = MyFigureCanvas(width=6, height=4, plot_type='2d')
        for i in range(len(self.history_data)):   # 将每次画一根线
            dr_history_cons_spd.plot_constant_speed(vehspd_cs=self.history_data[i].sysGain_class.systemgain.vehspd_cs,
                                                    pedal_cs=self.history_data[i].sysGain_class.systemgain.pedal_cs)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(dr_history_cons_spd)
        try:
            if self.History_Data_Comp_graphicsView_LayG2.itemAt(0):  # 如果已经有NVbar,删掉后重新捆绑
                self.History_Data_Comp_graphicsView_LayG2.itemAt(0).widget().deleteLater()
                self.History_Data_Comp_graphicsView_LayG2.removeWidget(self.History_Data_Comp_graphicsView_LayG2.itemAt(0).widget())
            else:
                # self.createContextMenu_sg_fig_view()  # 第一次初始化右键菜单，一次把两个canvas的菜单都初始化了  ！！！
                pass
            self.PicToolBar_history2 = NavigationBar(dr_history_cons_spd, self)
            self.History_Data_Comp_graphicsView_LayG2.addWidget(self.PicToolBar_history2)
            self.History_Data_Comp_graphicsView_2.setScene(self.scene)
            self.History_Data_Comp_graphicsView_2.show()
        except Exception as e:
            print(e)

        dr_history_max_acc = MyFigureCanvas(width=6, height=4, plot_type='2d')
        for i in range(len(self.history_data)):   # 将每次画一根线
            dr_history_max_acc.plot_max_acc(data=self.history_data[i].sysGain_class.maxacc.data)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(dr_history_max_acc)
        try:
            if self.History_Data_Comp_graphicsView_LayG3.itemAt(0):  # 如果已经有NVbar,删掉后重新捆绑
                self.History_Data_Comp_graphicsView_LayG3.itemAt(0).widget().deleteLater()
                self.History_Data_Comp_graphicsView_LayG3.removeWidget(self.History_Data_Comp_graphicsView_LayG3.itemAt(0).widget())
            else:
                # self.createContextMenu_sg_fig_view()  # 第一次初始化右键菜单，一次把两个canvas的菜单都初始化了  ！！！
                pass
            self.PicToolBar_history3 = NavigationBar(dr_history_cons_spd, self)
            self.History_Data_Comp_graphicsView_LayG3.addWidget(self.PicToolBar_history3)
            self.History_Data_Comp_graphicsView_3.setScene(self.scene)
            self.History_Data_Comp_graphicsView_3.show()
        except Exception as e:
            print(e)

        dr_history_acc_curve = MyFigureCanvas(width=18, height=5, plot_type='3d-subplot')
        dr_history_acc_curve.plot_acc_response_subplot(history_data=self.history_data)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(dr_history_acc_curve)
        try:
            if self.History_Data_Comp_graphicsView_LayG4.itemAt(0):  # 如果已经有NVbar,删掉后重新捆绑
                self.History_Data_Comp_graphicsView_LayG4.itemAt(0).widget().deleteLater()
                self.History_Data_Comp_graphicsView_LayG4.removeWidget(
                    self.History_Data_Comp_graphicsView_LayG4.itemAt(0).widget())
            else:
                # self.createContextMenu_sg_fig_view()  # 第一次初始化右键菜单，一次把两个canvas的菜单都初始化了  ！！！
                pass
            self.PicToolBar_history4 = NavigationBar(dr_history_acc_curve, self)
            self.History_Data_Comp_graphicsView_LayG4.addWidget(self.PicToolBar_history4)
            self.History_Data_Comp_graphicsView_4.setScene(self.scene)
            self.History_Data_Comp_graphicsView_4.show()
        except Exception as e:
            print('From dr_history_acc_curve')
            print(e)

        dr_history_launch = MyFigureCanvas(width=18, height=5, plot_type='2d-subplot')
        dr_history_launch.plot_launch_subplot(history_data=self.history_data)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(dr_history_launch)
        try:
            if self.History_Data_Comp_graphicsView_LayG5.itemAt(0):  # 如果已经有NVbar,删掉后重新捆绑
                self.History_Data_Comp_graphicsView_LayG5.itemAt(0).widget().deleteLater()
                self.History_Data_Comp_graphicsView_LayG5.removeWidget(
                    self.History_Data_Comp_graphicsView_LayG5.itemAt(0).widget())
            else:
                # self.createContextMenu_sg_fig_view()  # 第一次初始化右键菜单，一次把两个canvas的菜单都初始化了  ！！！
                pass
            self.PicToolBar_history5 = NavigationBar(dr_history_launch, self)
            self.History_Data_Comp_graphicsView_LayG5.addWidget(self.PicToolBar_history5)
            self.History_Data_Comp_graphicsView_5.setScene(self.scene)
            self.History_Data_Comp_graphicsView_5.show()
        except Exception as e:
            print('From dr_history_launch')
            print(e)

        dr_history_shift_map = MyFigureCanvas(width=18, height=5, plot_type='2d-subplot')
        dr_history_shift_map.plot_shift_map_subplot(history_data=self.history_data)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(dr_history_shift_map)
        try:
            if self.History_Data_Comp_graphicsView_LayG6.itemAt(0):  # 如果已经有NVbar,删掉后重新捆绑
                self.History_Data_Comp_graphicsView_LayG6.itemAt(0).widget().deleteLater()
                self.History_Data_Comp_graphicsView_LayG6.removeWidget(
                    self.History_Data_Comp_graphicsView_LayG6.itemAt(0).widget())
            else:
                # self.createContextMenu_sg_fig_view()  # 第一次初始化右键菜单，一次把两个canvas的菜单都初始化了  ！！！
                pass
            self.PicToolBar_history6 = NavigationBar(dr_history_shift_map, self)
            self.History_Data_Comp_graphicsView_LayG6.addWidget(self.PicToolBar_history6)
            self.History_Data_Comp_graphicsView_6.setScene(self.scene)
            self.History_Data_Comp_graphicsView_6.show()
        except Exception as e:
            print('From dr_history_shift_map')
            print(e)

        dr_history_pedal_map = MyFigureCanvas(width=18, height=5, plot_type='2d-subplot')
        dr_history_pedal_map.plot_pedal_map_subplot(history_data=self.history_data)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(dr_history_pedal_map)
        try:
            if self.History_Data_Comp_graphicsView_LayG7.itemAt(0):  # 如果已经有NVbar,删掉后重新捆绑
                self.History_Data_Comp_graphicsView_LayG7.itemAt(0).widget().deleteLater()
                self.History_Data_Comp_graphicsView_LayG7.removeWidget(
                    self.History_Data_Comp_graphicsView_LayG7.itemAt(0).widget())
            else:
                # self.createContextMenu_sg_fig_view()  # 第一次初始化右键菜单，一次把两个canvas的菜单都初始化了  ！！！
                pass
            self.PicToolBar_history7 = NavigationBar(dr_history_pedal_map, self)
            self.History_Data_Comp_graphicsView_LayG7.addWidget(self.PicToolBar_history7)
            self.History_Data_Comp_graphicsView_7.setScene(self.scene)
            self.History_Data_Comp_graphicsView_7.show()
        except Exception as e:
            print('From dr_history_pedal_map')
            print(e)

    def datatableview_show(self, data_list):
        """
        Function of showing calculation results in data_table

        :param : data_list   List of result data to show (list)
        :return: -
        __author__ = 'Lu chao'
        __revised__ = 20171012
        """
        self.model = QtGui.QStandardItemModel(self.DatatableView)
        # self.model.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant('HH'))
        # self.model.setHeaderData(2, QtCore.Qt.Horizontal, QtCore.QVariant("FF"))
        for i in range(data_list.__len__()):
            for j in range(data_list[0].__len__()):
                self.model.setItem(i, j, QtGui.QStandardItem(data_list[i][j]))
        self.DatatableView.setModel(self.model)
        self.DatatableView.resizeColumnsToContents()


class ThreadProcess(QtCore.QThread):
    Message_Finish = QtCore.pyqtSignal(str)
    Message_Finish_2 = QtCore.pyqtSignal(str)

    def __init__(self, method, **kwargs):
        super(ThreadProcess, self).__init__()
        self.method = method
        self.kwargs = kwargs

    def run(self):
        try:
            getattr(self, self.method, 'nothing')()
        except BaseException as e:
            print(e)

    def sg_read_thread(self):
        self.ax_holder_rd = ReadFile(file_path=self.kwargs['filepath'])
        self.Message_Finish.emit("计算完成！")

    def sg_cal_thread(self):
        self.ax_holder_SG = SystemGain(raw_data=self.kwargs['raw_data'], feature_array=self.kwargs['feature_array'])
        self.ax_holder_SG.sg_main()
        self.Message_Finish.emit("计算完成！")

    def show_raw_data(self):
        pass


class MyQtGraphicView(QtWidgets.QGraphicsView):
    Message_Drag_accept = QtCore.pyqtSignal(dict)
    Message_DoubleClick = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(MyQtGraphicView, self).__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        e.accept()

    def dragMoveEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        print(e.mimeData().text())
        self.Message_Drag_accept.emit({'title': e.mimeData().text(),
                                       'data': e.mimeData().text(),
                                       'Nvbar': False})

    def mouseDoubleClickEvent(self, e):
        self.Message_DoubleClick.emit(1)


class MyTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super(MyTreeWidget, self).__init__(parent)
        self.setDragEnabled(True)

    def mouseMoveEvent(self, e):
        mimeData = QtCore.QMimeData()
        drag = QtGui.QDrag(self)
        mimeData.setText(self.currentItem().text(0))
        drag.setMimeData(mimeData)
        drag.setHotSpot(e.pos() - self.rect().topLeft())
        dropAction = drag.exec_(QtCore.Qt.MoveAction)


if __name__ == '__main__':
    app = QApplication(argv)
    # ---------------QSS导入-------------------
    # file = QtCore.QFile('css.qss')
    # file.open(QtCore.QFile.ReadOnly)
    # stylesheet = file.readAll()
    # QtWidgets.QApplication.setStyleSheet(app, stylesheet.data().decode('utf-8'))  # utf-8  byte编码为String
    # ---------------实例化---------------------
    dlg = MainUiWindow()
    dlg.show()
    exit(app.exec())
