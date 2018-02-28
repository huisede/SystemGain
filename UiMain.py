from sys import argv, exit
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets

from SystemGainUi import Ui_MainWindow  # 界面源码
from Generate_Figs import *  # 绘图函数
from Calculation_function import *  # 计算函数
from re import match  # 正则表达式
from ctypes import windll
from UiSetIndexName import UiSetIndexName

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
        # self.initial()

        self.menu_InputData.triggered.connect(self.load_sys_gain_data)
        self.menu_Save.triggered.connect(self.save_sys_gain_data)
        self.action_Data_Viewer.triggered.connect(lambda: self.change_main_page(0))
        self.action_System_Gain.triggered.connect(lambda: self.change_main_page(1))
        self.action_Cal_Result.triggered.connect(lambda: self.change_main_page(2))
        self.action_Compare_Result.triggered.connect(lambda: self.change_main_page(3))
        self.action_Data_Base.triggered.connect(lambda: self.change_main_page(4))
        self.action_Cal_Setting.triggered.connect(lambda: self.change_main_page(5))
        self.SysGain_Cal.clicked.connect(self.cal_sys_gain_data_pre)
        self.History_Data_Choose_PushButton.clicked.connect(self.history_data_reload)

        self.menu_Engine_Working_Dist.triggered.connect(self.data_view_check_box_list)
        self.menu_Shifting_Strategy.triggered.connect(self.resize_figs)

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

        # self.buttonGroup_data_viewer = QtWidgets.QButtonGroup(self.verticalLayout)

        self.dr_acc_curve = MyFigureCanvas(width=6, height=4, plot_type='3d')
        self.PicToolBar_1 = NavigationBar(self.dr_acc_curve, self)
        self.gridLayout_2.addWidget(self.PicToolBar_1, 0, 0, 1, 1)
        self.gridLayout_2.addWidget(self.dr_acc_curve, 1, 0, 1, 1)
        self.dr_acc_curve.setMinimumSize(QtCore.QSize(0, 600))

        self.dr_sg_curve = MyFigureCanvas(width=6, height=4, plot_type='2d')
        self.PicToolBar_2 = NavigationBar(self.dr_sg_curve, self)
        self.gridLayout_2.addWidget(self.PicToolBar_2, 0, 1, 1, 1)
        self.gridLayout_2.addWidget(self.dr_sg_curve, 1, 1, 1, 1)
        self.dr_sg_curve.setMinimumSize(QtCore.QSize(0, 600))

        self.dr_cons_spd = MyFigureCanvas(width=6, height=4, plot_type='2d')
        self.PicToolBar_3 = NavigationBar(self.dr_cons_spd, self)
        self.gridLayout_2.addWidget(self.PicToolBar_3, 2, 0, 1, 1)
        self.gridLayout_2.addWidget(self.dr_cons_spd, 3, 0, 1, 1)
        self.dr_cons_spd.setMinimumSize(QtCore.QSize(0, 600))

        self.dr_shift_map = MyFigureCanvas(width=6, height=4, plot_type='2d')
        self.PicToolBar_4 = NavigationBar(self.dr_shift_map, self)
        self.gridLayout_2.addWidget(self.PicToolBar_4, 2, 1, 1, 1)
        self.gridLayout_2.addWidget(self.dr_shift_map, 3, 1, 1, 1)
        self.dr_shift_map.setMinimumSize(QtCore.QSize(0, 600))

        self.dr_launch = MyFigureCanvas(width=6, height=4, plot_type='2d')
        self.PicToolBar_5 = NavigationBar(self.dr_launch, self)
        self.gridLayout_2.addWidget(self.PicToolBar_5, 4, 0, 1, 1)
        self.gridLayout_2.addWidget(self.dr_launch, 5, 0, 1, 1)
        self.dr_launch.setMinimumSize(QtCore.QSize(0, 600))

        self.dr_ped_map = MyFigureCanvas(width=6, height=4, plot_type='2d')
        self.PicToolBar_6 = NavigationBar(self.dr_ped_map, self)
        self.gridLayout_2.addWidget(self.PicToolBar_6, 4, 1, 1, 1)
        self.gridLayout_2.addWidget(self.dr_ped_map, 5, 1, 1, 1)
        self.dr_ped_map.setMinimumSize(QtCore.QSize(0, 600))

        self.dr_max_acc = MyFigureCanvas(width=6, height=4, plot_type='2d')
        self.PicToolBar_7 = NavigationBar(self.dr_max_acc, self)
        self.gridLayout_2.addWidget(self.PicToolBar_7, 6, 0, 1, 1)
        self.gridLayout_2.addWidget(self.dr_max_acc, 7, 0, 1, 1)
        self.dr_max_acc.setMinimumSize(QtCore.QSize(0, 600))

        self.dr_raw = MyFigureCanvas(width=15, height=8, plot_type='2d-multi')
        self.PicToolBar_raw = NavigationBar(self.dr_raw, self)
        self.Data_Viewer_page_graphicsView_LayV.addWidget(self.PicToolBar_raw)
        self.Data_Viewer_page_graphicsView_LayV.addWidget(self.dr_raw)

        # ---------------------------- 初始化 -----------------------------------------
        # def initial(self):
        # self.data_viewer_graphics_view = MyQtGraphicView(self.Data_Viewer_page)
        # self.data_viewer_graphics_view.setObjectName("data_viewer_graphics_view")
        # self.Data_Viewer_graphicsView_LayG.addWidget(self.data_viewer_graphics_view)
        # self.data_viewer_graphics_view.Message_Drag_accept.connect(self.show_data_edit_drag_pictures)  # 拖拽重绘
        # self.data_viewer_graphics_view.Message_DoubleClick.connect(self.highlight_signal)  # 双击高亮
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
        # self.MainProcess_thread_rd.Message_Finish.connect(
        #     lambda: self.combobox_index_initial(self.MainProcess_thread_rd.ax_holder_rd.file_columns_orig))

        # self.MainProcess_thread_rd.Message_Finish.connect(self.combobox_index_features_initial)
        self.MainProcess_thread_rd.start()
        message_str = 'Message: Importing ' + file_path + ' ...'
        self.info_widget_update(message_str)

    def save_sys_gain_data(self):
        file = QFileDialog.getSaveFileName(self, filter='.pkl')
        file_path = file[0] + file[1]
        try:
            self.sl = SaveAndLoad()
            self.sl.store_result(file_path=file_path, store_data=self.MainProcess_thread_cal.ax_holder_SG)
        except Exception:
            pass

    def resize_figs(self):
        self.dr_acc_curve.fig.set_size_inches(self.System_Gain_AT_DCT_Fig_1.size().width() / 100 * 0.9,
                                              self.System_Gain_AT_DCT_Fig_1.size().height() / 100 * 0.9)
        self.dr_sg_curve.fig.set_size_inches(self.System_Gain_AT_DCT_Fig_2.size().width() / 100 * 0.9,
                                             self.System_Gain_AT_DCT_Fig_2.size().height() / 100 * 0.9)
        self.dr_cons_spd.fig.set_size_inches(self.System_Gain_AT_DCT_Fig_3.size().width() / 100 * 0.9,
                                             self.System_Gain_AT_DCT_Fig_3.size().height() / 100 * 0.9)
        self.dr_shift_map.fig.set_size_inches(self.System_Gain_AT_DCT_Fig_4.size().width() / 100 * 0.9,
                                              self.System_Gain_AT_DCT_Fig_4.size().height() / 100 * 0.9)
        self.dr_launch.fig.set_size_inches(self.System_Gain_AT_DCT_Fig_5.size().width() / 100 * 0.9,
                                           self.System_Gain_AT_DCT_Fig_5.size().height() / 100 * 0.9)
        self.dr_ped_map.fig.set_size_inches(self.System_Gain_AT_DCT_Fig_6.size().width() / 100 * 0.9,
                                            self.System_Gain_AT_DCT_Fig_6.size().height() / 100 * 0.9)
        self.dr_raw.fig.set_size_inches(self.Data_Viewer_page_graphicsView.size().width() / 100 * 0.9,
                                        self.Data_Viewer_page_graphicsView.size().height() / 100)
        self.PicToolBar_raw.dynamic_update()
        message_str = 'Message: Figs have been resized!'
        self.info_widget_update(message_str)

    # -----|--|主页面
    def change_main_page(self, index_page):
        self.MainStackedWidget.setCurrentIndex(index_page)

    def info_widget_update(self, message_str):
        self.info_list.append(message_str)
        self.InfoWidget.addItem(self.info_list[-1])
        self.InfoWidget.setCurrentRow(self.InfoWidget.count() - 1)  # 滚动条置为最下方

    # -----|--|Data Edit 页面
    def initial_data_edit(self):
        while self.verticalLayout.itemAt(0) is not None:  # 删除当前Lay中的元素
            try:
                self.verticalLayout.itemAt(0).widget().setParent(None)  # 删除当前Lay中widget元素，在此为CheckBox
                self.verticalLayout.itemAt(0).widget().deleteLater()
                self.verticalLayout.removeWidget(self.verticalLayout.itemAt(0).widget())
            except AttributeError:
                self.verticalLayout.removeItem(self.verticalLayout.itemAt(0))  # 删除当前Lay中spacer元素

        for i, ch in enumerate(self.MainProcess_thread_rd.ax_holder_rd.file_columns):  # 添加新CheckBox
            exec('self.checkBox' + ch + '= QtWidgets.QCheckBox(self.Data_Viewer_CheckBox_groupBox)')
            eval('self.checkBox' + ch + '.setObjectName("' + ch + '")')
            eval('self.verticalLayout.addWidget(self.checkBox' + ch + ')')
            eval('self.checkBox' + ch + '.setText("' + self.MainProcess_thread_rd.ax_holder_rd.file_columns_orig[
                i] + '")')

        spacer_item = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacer_item)  # 添加新spacer排版占位

        message_str = 'Message: Finished data import!'
        self.info_widget_update(message_str)

        self.combobox_index_features_initial()

    def data_view_check_box_list(self):
        checked_list = []
        for i in range(self.verticalLayout.count()):
            try:
                checked_list.append(self.verticalLayout.itemAt(i).widget().isChecked())
            except AttributeError as e:
                print('Error From data_view_check_box_list!')
        self.data_view_signal_plot(checked_list)

    def data_view_signal_plot(self, signal_list):

        self.dr_raw.fig.clear()
        self.dr_raw.plot_raw_data(time=self.MainProcess_thread_rd.ax_holder_rd.sg_csv_data_ful.iloc[:, 0],
                                  # 时间序列不一定是第一列！！！后续修改
                                  df=self.MainProcess_thread_rd.ax_holder_rd.sg_csv_data_ful.iloc[:, signal_list])
        self.PicToolBar_raw.press(self.PicToolBar_raw.home())
        self.PicToolBar_raw.dynamic_update()

    def select_marker(self):
        QtCore.Qt.Key_Left
        pass

    def highlight_signal(self):

        pass

    def get_mouse_xy_plot(self, event):
        self.xyCoordinates = [event.xdata, event.ydata]  # 捕捉鼠标点击的坐标
        print(self.xyCoordinates)

    # -----|--|System Gain
    def combobox_index_features_initial(self):  # 将字段规则导入
        try:
            self.System_Gain_AT_DCT_Index_comboBox.activated.disconnect(self.combobox_index_features_initial_callback)
            # 1、防止多次连接导致的提示信息重复 2、先行断开作为双保险，防止第一遍连接时留下的触发开关由clear()等动作带来的误触发跳转
        except TypeError:
            pass

        try:
            self.slfi = SaveAndLoad()
            self.history_index = self.slfi.reload_feature_index()
            self.System_Gain_AT_DCT_Index_comboBox.clear()  # ????第二次导入数据时运行报错   问题已解决 20180226
            self.System_Gain_AT_DCT_Index_comboBox.addItem('请选择')
            for i in self.history_index:
                self.System_Gain_AT_DCT_Index_comboBox.addItem(i)  # 配合下面的注释
        except Exception:
            message_str = 'Error: from combobox_index_features_initial!'
            self.info_widget_update(message_str)

        self.System_Gain_AT_DCT_Index_comboBox.activated.connect(
            self.combobox_index_features_initial_callback)    # 写在这里是为了防止上面addItem改变了currentIndex导致误触发
        # 20180226 交互类性的触发请选择activated而不是currentIndexChanged!!!!!!
        self.combobox_index_initial(self.MainProcess_thread_rd.ax_holder_rd.file_columns_orig)

    def combobox_index_features_initial_callback(self):
        columns = self.MainProcess_thread_rd.ax_holder_rd.file_columns_orig.tolist()
        columns_to_pre_select = []
        err = True
        for i in self.history_index[self.System_Gain_AT_DCT_Index_comboBox.currentText()]:
            try:
                columns_to_pre_select.append(columns.index(i))
            except ValueError:  # 如果需要索引的信号名不含在目前的数据中
                err = False
                columns_to_pre_select.append(0)  # 默认选0
        self.combobox_index_pre_select(columns_to_pre_select)

        if err:
            message_str = 'Message: Features selected!'
        else:
            message_str = 'Error: Signal not in Current data!'
        self.info_widget_update(message_str)

    def combobox_index_initial(self, item_list):  # 将文件中的所有字段写入列表
        for i in self.combo_box_names:  # 编号
            eval('self.' + i + '.clear()')  # 清空当前列表
            for j in item_list:
                eval('self.' + i + ".addItem('" + j + "')")
        # self.combobox_index_pre_select(self.MainProcess_thread_rd.ax_holder_rd.pre_select_features())

    def combobox_index_pre_select(self, pre_select_item_index_list):  # 自动预选字段
        for i in range(self.combo_box_names.__len__()):  # 编号
            eval('self.' + self.combo_box_names[i] + '.setCurrentIndex(' + str(pre_select_item_index_list[i]) + ')')

    def cal_sys_gain_data_pre(self):
        try:
            if self.System_Gain_AT_DCT_New_Index.isChecked():
                self.UiSetIndexName = UiSetIndexName()
                self.UiSetIndexName.show()
                self.UiSetIndexName.message.connect(self.save_feature_index)
            self.cal_sys_gain_data()
        except Exception:
            message_str = 'Error: Please INPUT DATA and CHOOSE SIGNALS!'
            self.info_widget_update(message_str)

    def save_feature_index(self, feature_save_name):
        feature_array = []
        for i in self.combo_box_names:  # 编号
            eval('feature_array.append(self.' + i + '.currentText())')
        self.slfi = SaveAndLoad()
        self.history_index[feature_save_name] = feature_array  # 追加
        self.slfi.store_feature_index(store_index=self.history_index)  # 重新替换feature_index.pkl中所有数据
        message_str = 'Message: Feature index ' + feature_save_name + ' added!'
        self.info_widget_update(message_str)

    def cal_sys_gain_data(self):
        feature_array = []
        for i in self.combo_box_names:  # 编号
            eval('feature_array.append(self.' + i + '.currentText())')

        self.MainProcess_thread_cal = ThreadProcess(method='sg_cal_thread',
                                                    raw_data=self.MainProcess_thread_rd.ax_holder_rd.sg_csv_data_ful,
                                                    feature_array=feature_array,
                                                    pt_type=self.buttonGroup.checkedButton().text())
        self.MainProcess_thread_cal.Message_Finish.connect(self.show_ax_pictures_sg)
        self.MainProcess_thread_cal.start()

        message_str = 'Message: Start calculating system gain data ...'
        self.info_widget_update(message_str)

    def show_ax_pictures_sg(self):  # System Gain 绘图函数
        """

        :return:
        """

        # self.createContextMenu_sg_fig_view()

        self.dr_acc_curve.axes.clear()
        self.dr_acc_curve.plot_acc_response(
            data=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.accresponce.data,
            ped_avg=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.accresponce.pedal_avg)
        self.PicToolBar_1.press(self.PicToolBar_1.home())
        self.PicToolBar_1.dynamic_update()

        self.dr_sg_curve.axes.clear()
        self.dr_sg_curve.plot_systemgain_curve(
            vehspd_sg=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.vehspd_sg,
            acc_sg=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.acc_sg)
        self.PicToolBar_2.press(self.PicToolBar_2.home())
        self.PicToolBar_2.dynamic_update()

        self.dr_cons_spd.axes.clear()
        self.dr_cons_spd.plot_constant_speed(
            vehspd_cs=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.vehspd_cs,
            pedal_cs=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.pedal_cs)
        self.PicToolBar_3.press(self.PicToolBar_3.home())
        self.PicToolBar_3.dynamic_update()

        self.dr_shift_map.axes.clear()
        if self.System_Gain_AT_DCT.isChecked():
            self.dr_shift_map.plot_shift_map(data=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.shiftmap.data,
                                             kind='AT/DCT')
        elif self.System_Gain_CVT.isChecked():
            self.dr_shift_map.plot_shift_map(data=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.shiftmap.data,
                                             kind='CVT',
                                             pedal_avg=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.shiftmap.kwargs['pedal_avg'])
        elif self.System_Gain_MT.isChecked():
            pass
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

        self.dr_max_acc.axes.clear()
        self.dr_max_acc.plot_max_acc(data=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.maxacc.data)
        self.PicToolBar_7.press(self.PicToolBar_7.home())
        self.PicToolBar_7.dynamic_update()

        message_str = 'Message: System gain calculation finished!'
        self.info_widget_update(message_str)

    # -----|--|Comparison 页面
    def history_data_reload(self):
        file = QFileDialog.getOpenFileNames(self, filter='*.pkl')
        file_path_list = file[0]
        try:
            self.sl = SaveAndLoad()
            self.history_data = self.sl.reload_result(file_path_list=file_path_list)
            message_str = 'Message: History data --' + str(file_path_list) + ' import finished!'
            self.info_widget_update(message_str)
            self.history_data_plot()
        except Exception as e:
            print('From Reload History Data')
            print(e)

    def history_data_plot(self):
        while self.gridLayout_4.itemAt(0) is not None:  # 删除当前Lay中的元素
            try:
                self.gridLayout_4.itemAt(0).widget().setParent(None)  # 删除当前Lay中widget元素，在此为CheckBox
                self.gridLayout_4.itemAt(0).widget().deleteLater()
                self.gridLayout_4.removeWidget(self.gridLayout_4.itemAt(0).widget())
            except AttributeError:
                self.gridLayout_4.removeItem(self.gridLayout_4.itemAt(0))  # 删除当前Lay中spacer元素

        dr_history_sg_curve = MyFigureCanvas(width=6, height=4, plot_type='2d')
        for i in range(len(self.history_data)):  # 将每次画一根线
            dr_history_sg_curve.plot_systemgain_curve(vehspd_sg=self.history_data[i].sysGain_class.systemgain.vehspd_sg,
                                                      acc_sg=self.history_data[i].sysGain_class.systemgain.acc_sg)
        self.PicToolBar_history1 = NavigationBar(dr_history_sg_curve, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history1,0,0,1,1)
        self.gridLayout_4.addWidget(dr_history_sg_curve,1,0,1,1)
        dr_history_sg_curve.setMinimumSize(QtCore.QSize(0, 600))

        dr_history_cons_spd = MyFigureCanvas(width=6, height=4, plot_type='2d')
        for i in range(len(self.history_data)):  # 将每次画一根线
            dr_history_cons_spd.plot_constant_speed(vehspd_cs=self.history_data[i].sysGain_class.systemgain.vehspd_cs,
                                                    pedal_cs=self.history_data[i].sysGain_class.systemgain.pedal_cs)
        self.PicToolBar_history2 = NavigationBar(dr_history_cons_spd, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history2,0,1,1,1)
        self.gridLayout_4.addWidget(dr_history_cons_spd,1,1,1,1)
        dr_history_cons_spd.setMinimumSize(QtCore.QSize(0, 600))

        dr_history_max_acc = MyFigureCanvas(width=6, height=4, plot_type='2d')
        for i in range(len(self.history_data)):  # 将每次画一根线
            dr_history_max_acc.plot_max_acc(data=self.history_data[i].sysGain_class.maxacc.data)
        self.PicToolBar_history3 = NavigationBar(dr_history_max_acc, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history3,0,2,1,1)
        self.gridLayout_4.addWidget(dr_history_max_acc,1,2,1,1)
        dr_history_max_acc.setMinimumSize(QtCore.QSize(0, 600))

        dr_history_acc_curve = MyFigureCanvas(width=18, height=5, plot_type='3d-subplot')
        dr_history_acc_curve.plot_acc_response_subplot(history_data=self.history_data)
        self.PicToolBar_history4 = NavigationBar(dr_history_acc_curve, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history4,2,0,1,3)
        self.gridLayout_4.addWidget(dr_history_acc_curve,3,0,1,3)
        dr_history_acc_curve.setMinimumSize(QtCore.QSize(0, 600))

        dr_history_launch = MyFigureCanvas(width=18, height=5, plot_type='2d-subplot')
        dr_history_launch.plot_launch_subplot(history_data=self.history_data)
        self.PicToolBar_history5 = NavigationBar(dr_history_launch, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history5,4,0,1,3)
        self.gridLayout_4.addWidget(dr_history_launch,5,0,1,3)
        dr_history_launch.setMinimumSize(QtCore.QSize(0, 600))


        dr_history_shift_map = MyFigureCanvas(width=18, height=5, plot_type='2d-subplot')
        dr_history_shift_map.plot_shift_map_subplot(history_data=self.history_data)
        self.PicToolBar_history6 = NavigationBar(dr_history_shift_map, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history6,6,0,1,3)
        self.gridLayout_4.addWidget(dr_history_shift_map,7,0,1,3)
        dr_history_shift_map.setMinimumSize(QtCore.QSize(0, 600))


        dr_history_pedal_map = MyFigureCanvas(width=18, height=5, plot_type='2d-subplot')
        dr_history_pedal_map.plot_pedal_map_subplot(history_data=self.history_data)
        self.PicToolBar_history7 = NavigationBar(dr_history_pedal_map, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history7,8,0,1,3)
        self.gridLayout_4.addWidget(dr_history_pedal_map,9,0,1,3)
        dr_history_pedal_map.setMinimumSize(QtCore.QSize(0, 600))


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
        self.ax_holder_SG = SystemGain(raw_data=self.kwargs['raw_data'], feature_array=self.kwargs['feature_array'],
                                       pt_type=self.kwargs['pt_type'])
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
