from sys import argv, exit
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
# from SystemGainUi import Ui_MainWindow  # 界面源码
from TestSolverUi import Ui_MainWindow
from Generate_Figs import *  # 绘图函数
from Calculation_function import *  # 计算函数
from re import match  # 正则表达式
# from ctypes import windll
from UiSetIndexName import UiSetIndexName
from UI_eliminate_duplicate_ped import UiEliminateDuplicatePed

# try:
#     temp1 = windll.LoadLibrary('DLL\\Qt5Core.dll')
#     temp2 = windll.LoadLibrary('DLL\\Qt5Gui.dll')
#     temp3 = windll.LoadLibrary('DLL\\Qt5Widgets.dll')
#     temp4 = windll.LoadLibrary('DLL\\msvcp140.dll')
#     temp5 = windll.LoadLibrary('DLL\\Qt5PrintSupport.dll')
# except OSError as e:
#     pass


class MainUiWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainUiWindow, self).__init__(parent)
        self.setupUi(self)
        # self.initial()

        self.triggers()

        self.info_list = []
        self.MainProcess_thread = []
        # self.createContextMenu_RawDataView()
        self.combo_box_names = ['Select_Features_Time',         # 0
                                'Select_Features_Vspd',         # 1
                                'Select_Features_Ped',          # 2
                                'Select_Features_Acc',          # 3
                                'Select_Features_Gear',         # 4
                                'Select_Features_Toq',          # 5
                                'Select_Features_Fuel',         # 6
                                'Select_Features_EnSpd',        # 7
                                'Select_Features_TbSpd',        # 8
                                'Select_Features_Brk',          # 9
                                'Select_Features_Latitude',     #10
                                'Select_Features_Longitude',    #11
                                'Select_Features_StrWhlAng',    #12
                                'Select_Features_Acc_y',        #13
                                'Select_Features_CoolingTemp',  #14
                                'Select_Features_CryHeat',      #15
                                ]   # 更改后记得同步修改
                                    # system_gain_index_pre_fit,
                                    # real_road_fc_index_pre_fit,
                                    # emission_cal_index_pre_fit 中的表格

        self.dbc_search_list = {'SystemGain': {'Vspd': [r'^.*VehSpdAvgNonDrvn.*$', r'^.*VehicleSpeed.*$', ],  # 编辑此处的正则表达式即可
                                               'Acc': [r'^.*LongtAcc.*$', r'^.*LongAccelG.*$', ],
                                               'Ped': [r'^.*AccelActuPos.*$', ],
                                               'Gear': [r'^.*Gear.*$', ],
                                               'Toq': [r'^.*EnActuStdyStaToq.*$', r'^.*Toq.*$', ],
                                               'EnSpd': [r'^.*EnSpd.*$', ],
                                               'TbSpd': [r'^.*TrTurbAngulVel.*$', r'^.*Turb.*$', ],
                                               },
                                'Emission': {'Fuel': [r'^.*vsksml.*$', ],
                                             'Vspd': [r'^.*vfzg.*$', r'^.*VehV_v.*$'],
                                             },
                                'RealRoadFC': {'Vspd': [r'^.*VehSpdAvgNonDrvn.*$', ],
                                               'EnSpd': [r'^.*EnSpd.*$', ],
                                               'Fuel': [r'^.*FuelCsump.*$', ],
                                               },
                                }

        self.color_array = ['#FFA500',  # 橙色
                            '#3CB371',  # 春绿
                            '#4169E1',  # 皇家蓝
                            '#DF12ED',  # 紫
                            '#FD143C',  # 鲜红
                            '#D2691E',  # 巧克力
                            '#696969',  # 暗灰
                            '#40E0D0',  # 绿宝石
                            '#9400D3',  # 紫罗兰
                            ]
        self.color_array_rgb = [(255, 165, 0, 0.3),
                                (60, 179, 113, 0.3),
                                (65, 105, 225, 0.3),
                                (223, 18, 237, 0.3),
                                (253, 20, 60, 0.3),
                                (210, 105, 30, 0.3),
                                (105, 105, 105, 0.3),
                                (64, 224, 208, 0.3),
                                (148, 0, 211, 0.3)]

        self.replace_cs_content = False

        # 右键菜单初始化
        self.createContextMenu_Data_Base_tableWidget()
        self.createContextMenu_Constant_Speed_tableWidget()

        self.dr_raw = MyFigureCanvas(width=15, height=8, plot_type='2d-multi')
        self.PicToolBar_raw = NavigationBar(self.dr_raw, self)
        self.Data_Viewer_page_graphicsView_LayV.addWidget(self.PicToolBar_raw)
        self.Data_Viewer_page_graphicsView_LayV.addWidget(self.dr_raw)
        # self.buttonGroup_data_viewer = QtWidgets.QButtonGroup(self.verticalLayout)

        # ---------------------------- 初始化 -----------------------------------------
        # def initial(self):
        # self.data_viewer_graphics_view = MyQtGraphicView(self.Data_Viewer_page)
        # self.data_viewer_graphics_view.setObjectName("data_viewer_graphics_view")
        # self.Data_Viewer_graphicsView_LayG.addWidget(self.data_viewer_graphics_view)
        # self.data_viewer_graphics_view.Message_Drag_accept.connect(self.show_data_edit_drag_pictures)  # 拖拽重绘
        # self.data_viewer_graphics_view.Message_DoubleClick.connect(self.highlight_signal)  # 双击高亮
        # self.initial_data_edit()

    def _set_resolution(self):
        return self.frameSize()

    def _draw_canvas(self, width=800, height=600):
        width_for_sg = (width-350)/2/1.2
        height_for_sg = width_for_sg

        self.dr_acc_curve = MyFigureCanvas(width=2, height=2, plot_type='3d')
        self.PicToolBar_1 = NavigationBar(self.dr_acc_curve, self)
        self.gridLayout_2.addWidget(self.PicToolBar_1, 0, 0, 1, 1)
        self.gridLayout_2.addWidget(self.dr_acc_curve, 1, 0, 1, 1)
        self.dr_acc_curve.setMinimumSize(QtCore.QSize(width_for_sg, height_for_sg))

        self.dr_sg_curve = MyFigureCanvas(width=2, height=2, plot_type='2d')
        self.PicToolBar_2 = NavigationBar(self.dr_sg_curve, self)
        self.gridLayout_2.addWidget(self.PicToolBar_2, 0, 1, 1, 1)
        self.gridLayout_2.addWidget(self.dr_sg_curve, 1, 1, 1, 1)
        self.dr_sg_curve.setMinimumSize(QtCore.QSize(width_for_sg, height_for_sg))

        self.dr_cons_spd = MyFigureCanvas(width=2, height=2, plot_type='2d')
        self.PicToolBar_3 = NavigationBar(self.dr_cons_spd, self)
        self.gridLayout_2.addWidget(self.PicToolBar_3, 2, 0, 1, 1)
        self.gridLayout_2.addWidget(self.dr_cons_spd, 3, 0, 1, 1)
        self.dr_cons_spd.setMinimumSize(QtCore.QSize(width_for_sg, height_for_sg))

        self.dr_shift_map = MyFigureCanvas(width=2, height=2, plot_type='2d')
        self.PicToolBar_4 = NavigationBar(self.dr_shift_map, self)
        self.gridLayout_2.addWidget(self.PicToolBar_4, 2, 1, 1, 1)
        self.gridLayout_2.addWidget(self.dr_shift_map, 3, 1, 1, 1)
        self.dr_shift_map.setMinimumSize(QtCore.QSize(width_for_sg, height_for_sg))

        self.dr_launch = MyFigureCanvas(width=2, height=2, plot_type='2d')
        self.PicToolBar_5 = NavigationBar(self.dr_launch, self)
        self.gridLayout_2.addWidget(self.PicToolBar_5, 4, 0, 1, 1)
        self.gridLayout_2.addWidget(self.dr_launch, 5, 0, 1, 1)
        self.dr_launch.setMinimumSize(QtCore.QSize(width_for_sg, height_for_sg))

        self.dr_pedal_map = MyFigureCanvas(width=2, height=2, plot_type='2d')
        self.PicToolBar_6 = NavigationBar(self.dr_pedal_map, self)
        self.gridLayout_2.addWidget(self.PicToolBar_6, 4, 1, 1, 1)
        self.gridLayout_2.addWidget(self.dr_pedal_map, 5, 1, 1, 1)
        self.dr_pedal_map.setMinimumSize(QtCore.QSize(width_for_sg, height_for_sg))

        self.dr_max_acc = MyFigureCanvas(width=2, height=2, plot_type='2d')
        self.PicToolBar_7 = NavigationBar(self.dr_max_acc, self)
        self.gridLayout_2.addWidget(self.PicToolBar_7, 6, 0, 1, 1)
        self.gridLayout_2.addWidget(self.dr_max_acc, 7, 0, 1, 1)
        self.dr_max_acc.setMinimumSize(QtCore.QSize(width_for_sg, height_for_sg))

    def triggers(self):
        self.menu_InputData.triggered.connect(self.load_data)
        self.menu_Save.triggered.connect(self.save_sys_gain_data)
        # menu_Output_Report_ppt
        self.menu_Output_Report.triggered.connect(lambda: self.output_data_ppt('initial_ppt'))
        # New Add ppt
        self.menu_Output_Histtory_Report.triggered.connect(lambda: self.output_data_ppt('analysis_ppt'))
        # Main Page Change
        self.action_Data_Viewer.triggered.connect(lambda: self.change_main_page(0))
        self.action_Select_Features.triggered.connect(lambda: self.change_main_page(1))
        self.action_System_Gain.triggered.connect(lambda: self.change_main_page(2))
        self.action_Emission_Test.triggered.connect(lambda: self.change_main_page(3))
        self.action_Real_Road_Fc.triggered.connect(lambda: self.change_main_page(4))
        self.action_Compare_Result.triggered.connect(lambda: self.change_main_page(5))
        self.action_Data_Base.triggered.connect(lambda: self.change_main_page(6))
        self.action_Cal_Setting.triggered.connect(lambda: self.change_main_page(7))
        self.SysGain_Cal.clicked.connect(self.cal_sys_gain_data)
        self.History_Data_Choose_PushButton.clicked.connect(self.history_data_reload)
        self.Constant_Speed_Input_button.clicked.connect(self.constant_speed_input_callback)
        self.Select_Features_DB_Data_Base_Select_Commit_pushButton.clicked.connect(self.show_feature_index)
        # self.menu_Engine_Working_Dist.triggered.connect(self.data_view_check_box_list)
        self.Select_Features_New_Index_PushButton.clicked.connect(self.create_feature_index)
        self.Select_Features_SystemGain.clicked.connect(self.system_gain_index_pre_fit)
        self.Select_Features_EmissionCal.clicked.connect(self.emission_cal_index_pre_fit)
        self.Select_Features_RealRoadFC.clicked.connect(self.real_road_fc_index_pre_fit)
        # 设置界面的显示逻辑
        self.DataViewer_setting_Rawdata_mdf_res_RB.toggled.connect(self.enable_disable_set_data_viewer_data_source_dat_mdf)
        self.DataViewer_setting_Rawdata_Intest_RB.toggled.connect(self.enable_disable_set_data_viewer_data_source_intest)
        self.DataViewer_setting_Time_axis_Samples_RB.toggled.connect(self.enable_disable_set_data_viewer_setting_time_axis_fs_base)
        self.DataViewer_setting_Time_axis_Signal_RB.toggled.connect(self.enable_disable_set_data_viewer_setting_time_axis_signal_base)
        self.buttonGroup_BSFC_Need.buttonClicked.connect(self.enable_disable_set_real_road_fc_button_group_bsfc)
        self.RealRoadFc_Engine_Working_Points_X_Range_slider.valueChanged.connect(lambda: self.set_real_road_fc_xy_range_qslider_value_change(1))
        self.RealRoadFc_Engine_Working_Points_Y_Range_slider.valueChanged.connect(lambda: self.set_real_road_fc_xy_range_qslider_value_change(2))

    # ---------------------------- 右键菜单 -----------------------------------------

    def createContextMenu_Data_Base_tableWidget(self):
        '''

        :return:
        '''
        self.Data_Base_tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.Data_Base_tableWidget.customContextMenuRequested.connect(lambda: self.showContextMenu('Data_Base_tableWidget'))
        self.Data_Base_tableWidget.contextMenu = QtWidgets.QMenu(self)
        self.Data_Base_tableWidget.actionA = self.Data_Base_tableWidget.contextMenu.addAction(QtGui.QIcon("images/0.png"), u'|  删除记录')
        self.Data_Base_tableWidget.actionA.triggered.connect(self.delete_index_item)
        self.Data_Base_tableWidget.actionB = self.Data_Base_tableWidget.contextMenu.addAction(QtGui.QIcon("images/0.png"), u"|  提交修改")
        self.Data_Base_tableWidget.actionB.triggered.connect(self.edit_index_item)
        # 添加二级菜单
        # self.Data_Base_tableWidget.second = self.Data_Base_tableWidget.contextMenu.addMenu(QtGui.QIcon("images/0.png"), u"|  提交修改")
        # self.Data_Base_tableWidget.actionD = self.Data_Base_tableWidget.second.addAction(QtGui.QIcon("images/0.png"), u'|  动作A')
        # self.Data_Base_tableWidget.actionE = self.Data_Base_tableWidget.second.addAction(QtGui.QIcon("images/0.png"), u'|  动作B')
        # self.Data_Base_tableWidget.actionF = self.Data_Base_tableWidget.second.addAction(QtGui.QIcon("images/0.png"), u'|  动作C')

        return

    def createContextMenu_Constant_Speed_tableWidget(self):
        '''

        :return:
        '''
        self.System_Gain_AT_DCT_StablePed_tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.System_Gain_AT_DCT_StablePed_tableWidget.customContextMenuRequested.connect(lambda: self.showContextMenu('System_Gain_AT_DCT_StablePed_tableWidget'))
        self.System_Gain_AT_DCT_StablePed_tableWidget.contextMenu = QtWidgets.QMenu(self)
        self.System_Gain_AT_DCT_StablePed_tableWidget.actionA = self.System_Gain_AT_DCT_StablePed_tableWidget.contextMenu.addAction(QtGui.QIcon("images/0.png"), u'|  删除记录')
        self.System_Gain_AT_DCT_StablePed_tableWidget.actionA.triggered.connect(self.constant_speed_data_table_view_delete_cs)
        self.System_Gain_AT_DCT_StablePed_tableWidget.actionB = self.System_Gain_AT_DCT_StablePed_tableWidget.contextMenu.addAction(QtGui.QIcon("images/0.png"), u"|  提交修改")
        self.System_Gain_AT_DCT_StablePed_tableWidget.actionB.triggered.connect(self.constant_speed_data_table_view_change_cs)

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

    def load_data(self):
        file = QFileDialog.getOpenFileName(self, filter='*.csv *.xls *.xlsx *.mdf *.dat')
        self.rawdata_filepath = file[0]
        if self.rawdata_filepath != '':
            self.MainProcess_thread_rd = ThreadProcess(method='read_thread',
                                                       filepath=self.rawdata_filepath,
                                                       resample_rate=self.DataViewer_setting_Rawdata_mdf_res_TE.toPlainText(),
                                                       intest_data=self.DataViewer_setting_Rawdata_Intest_RB.isChecked(),
                                                       feature_row=self.DataViewer_setting_Rawdata_Intest_hang_data_TE.toPlainText(),
                                                       data_row=self.DataViewer_setting_Rawdata_Intest_hang_feature_TE.toPlainText()
                                                       )
            self.MainProcess_thread_rd.Message_Finish.connect(self.load_data_judgement)
            # self.MainProcess_thread_rd.Message_Finish.connect(
            #     lambda: self.combobox_index_initial(self.MainProcess_thread_rd.ax_holder_rd.file_columns_orig))

            # self.MainProcess_thread_rd.Message_Finish.connect(self.combobox_index_features_initial)
            self.MainProcess_thread_rd.start()

            message_str = 'Message: Importing ' + self.rawdata_filepath + '...PLEASE WAIT...'
            self.info_widget_update(message_str)

            self.refresh_raw_data_pic()
            self.refresh_cs_data()  # 新导入数据后清空Constant Speed数据
            self.refresh_sg_pics()
            self.enable_pre_select()

    def load_data_judgement(self, message):
        if message == '导入完成':
            self.initial_data_edit()
        elif message == '导入失败':
            message_str = 'Message: Importing failure, PLEASE CHECK YOUR DATA or Cal Settings！'
            self.info_widget_update(message_str)

    def save_sys_gain_data(self):
        file = QFileDialog.getSaveFileName(self, filter='.pkl')
        file_path = file[0] + file[1]
        try:
            self.sl = SaveAndLoad()
            self.sl.store_result(file_path=file_path, store_data=self.MainProcess_thread_cal.ax_holder_SG)
            message_str = 'Message: ' + file_path + ' has been saved successfully!'
            self.info_widget_update(message_str)
        except Exception:
            pass

    # PPT
    def output_data_ppt(self, ppt_type):
        try:
            rawdata_path = self.rawdata_filepath
        except AttributeError:
            self.info_widget_update('Error: the path of rawdata is empty')
            rawdata_path = ''

        list_figs, rawdata_name, title_ppt = SaveAndLoad.get_fig_name(ppt_type, rawdata_path)
        pic_path = argv[0].replace(argv[0].split("/")[-1], 'bin/')  # 当前路径，避免相对路径'./bin/'问题

        try:
            for i in range(0, len(list_figs)):
                # self.dr_acc_curve.fig.savefig(pic_path + 'Acc Response.png', dpi=200)
                eval('self.' + list_figs[i][0] + ".fig.savefig('" + pic_path + list_figs[i][1] + "', dpi=200)")
            prs = SaveAndLoad.save_pic_ppt(list_figs, rawdata_name, title_ppt, pic_path)
            # Delete saved Pics
            file_ppt = QFileDialog.getSaveFileName(self, filter='.pptx')
            file_ppt_path = file_ppt[0] + file_ppt[1]
            try:
                prs.save(file_ppt_path)
                message_str = 'Message: Saving PPT in ' + file_ppt_path + ' ...'
                self.info_widget_update(message_str)
            except Exception:
                pass
        except AttributeError:
            message_str = 'Error: No comparison results were obtained '
            self.info_widget_update(message_str)

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
        self.dr_pedal_map.fig.set_size_inches(self.System_Gain_AT_DCT_Fig_6.size().width() / 100 * 0.9,
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

    # -----|--|Data viewer 页面
    def initial_data_edit(self):
        while self.verticalLayout.itemAt(0) is not None:  # 删除当前Lay中的元素
            try:
                self.verticalLayout.itemAt(0).widget().setParent(None)  # 删除当前Lay中widget元素，在此为CheckBox
                self.verticalLayout.itemAt(0).widget().deleteLater()
                self.verticalLayout.removeWidget(self.verticalLayout.itemAt(0).widget())
            except AttributeError:
                self.verticalLayout.removeItem(self.verticalLayout.itemAt(0))  # 删除当前Lay中spacer元素

        for i, ch in enumerate(self.MainProcess_thread_rd.ax_holder_rd.file_columns):  # 添加新CheckBox
            # ——————————————————————————————————————————BUG FIX————————————————————————————————————————————————
            # 为了命名问题，万一原始数据中存在字段含有加减乘除和非法命名字符，会生成不了checkbox，因此将ch替换为str(i)  ---20180411 LC
            exec('self.checkBox' + str(i) + '= QtWidgets.QCheckBox(self.Data_Viewer_CheckBox_groupBox)')
            eval('self.checkBox' + str(i) + '.setObjectName("' + ch + '")')
            eval('self.verticalLayout.addWidget(self.checkBox' + str(i) + ')')
            eval('self.checkBox' + str(i) + '.setText("' + self.MainProcess_thread_rd.ax_holder_rd.file_columns_orig[
                i] + '")')
            eval('self.checkBox' + str(i) + '.clicked.connect(self.data_view_check_box_list)')  # 捆绑点击触发绘图
            # ——————————————————————————————————————————BUG FIX————————————————————————————————————————————————

        spacer_item = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacer_item)  # 添加新spacer排版占位

        self.combobox_index_features_initial()   # 初始化在库的车型Features
        self.combobox_index_initial(self.MainProcess_thread_rd.ax_holder_rd.file_columns_orig)  # 初始化每一个下拉菜单

        message_str = 'Message: Finish data import!'
        self.info_widget_update(message_str)

    def data_view_check_box_list(self):
        checked_list = []
        for i in range(self.verticalLayout.count()):
            try:
                checked_list.append(self.verticalLayout.itemAt(i).widget().isChecked())
            except AttributeError as e:
                # print('Error From data_view_check_box_list!')
                pass
        self.data_view_signal_plot(checked_list)

    def data_view_signal_plot(self, signal_list):  # 时间序列不一定是第一列！！！后续修改      ---已换成3种选项

        self.dr_raw.fig.clear()
        try:
            if self.DataViewer_setting_Time_axis_Dots_RB.isChecked():
                self.dr_raw.plot_raw_data(time=range(self.MainProcess_thread_rd.ax_holder_rd.import_data_ful_.shape[0]),
                                          df=self.MainProcess_thread_rd.ax_holder_rd.import_data_ful_.iloc[:, signal_list])
            elif self.DataViewer_setting_Time_axis_Samples_RB.isChecked():
                self.dr_raw.plot_raw_data(time=[x/float(self.DataViewer_setting_Time_axis_Samples_TE.toPlainText()) for x in
                                                range(self.MainProcess_thread_rd.ax_holder_rd.import_data_ful_.shape[0])],
                                          df=self.MainProcess_thread_rd.ax_holder_rd.import_data_ful_.iloc[:, signal_list])
            elif self.DataViewer_setting_Time_axis_Signal_RB.isChecked():
                self.dr_raw.plot_raw_data(time=self.MainProcess_thread_rd.ax_holder_rd.import_data_ful_.iloc[:, self.DataViewer_setting_Time_axis_Samples_comboBox.currentIndex()],
                                          df=self.MainProcess_thread_rd.ax_holder_rd.import_data_ful_.iloc[:, signal_list])
        except Exception:
            message_str = 'Error: Wrong Signal TYPE! Please Check!'
            self.info_widget_update(message_str)

        self.PicToolBar_raw.press(self.PicToolBar_raw.home())
        self.PicToolBar_raw.dynamic_update()

    def get_mouse_xy_plot(self, event):
        self.xyCoordinates = [event.xdata, event.ydata]  # 捕捉鼠标点击的坐标
        print(self.xyCoordinates)

    def refresh_raw_data_pic(self):
        self.dr_raw.fig.clear()
        self.PicToolBar_raw.dynamic_update()

    # -----|--|Select Features 页面
    # -----|--|Select Features --|Features Selection
    def enable_pre_select(self):
        self.Select_Features_SystemGain.setEnabled(True)
        self.Select_Features_RealRoadFC.setEnabled(True)
        self.Select_Features_EmissionCal.setEnabled(True)
        self.Select_Features_New_Index_PushButton.setEnabled(True)

    def refresh_all_combo_box(self):
        for i in self.combo_box_names:
            eval('self.' + i + "_lab.setStyleSheet('')")

    def system_gain_index_pre_fit(self):
        self.refresh_all_combo_box()
        target_combo_box_names = sorted([
                                'Select_Features_Vspd',
                                'Select_Features_Ped',
                                'Select_Features_Acc',
                                'Select_Features_Gear',
                                'Select_Features_Toq',
                                'Select_Features_EnSpd',
                                'Select_Features_TbSpd',
                                 ])

        for i in range(target_combo_box_names.__len__()):
            eval('self.' + target_combo_box_names[i] + '.setCurrentIndex('
                 +
                 str("SaveAndLoad.search_feature(self.MainProcess_thread_rd.ax_holder_rd."
                                         "file_columns_orig,self.dbc_search_list['SystemGain']['"
                                         + sorted(self.dbc_search_list['SystemGain'])[i] + "'])"
                     )
                 +
                 ")")
            # 例句
            # self.Select_Features_Acc.setCurrentIndex(SaveAndLoad.search_feature(self.MainProcess_thread_rd.ax_holder_rd.file_columns_orig,
            #                                  self.dbc_search_list['SystemGain']['Acc']))

            eval('self.' + target_combo_box_names[i] + "_lab.setStyleSheet('QLabel{background-color: rgba"
                 + str(self.color_array_rgb[0]) + " }')")
            # 例句
            # self.Select_Features_Acc_lab.setStyleSheet('QLabel{background-color: rgba[0]}')

    def real_road_fc_index_pre_fit(self):
        self.refresh_all_combo_box()
        target_combo_box_names = sorted([
                                        'Select_Features_Vspd',
                                        'Select_Features_Fuel',
                                        'Select_Features_EnSpd',
                                        ])

        for i in range(target_combo_box_names.__len__()):
            eval('self.' + target_combo_box_names[i] + '.setCurrentIndex('
                 +
                 str("SaveAndLoad.search_feature(self.MainProcess_thread_rd.ax_holder_rd."
                     "file_columns_orig,self.dbc_search_list['RealRoadFC']['"
                     + sorted(self.dbc_search_list['RealRoadFC'])[i] + "'])"
                     )
                 +
                 ")")

            eval('self.' + target_combo_box_names[i] + "_lab.setStyleSheet('QLabel{background-color: rgba"
                 + str(self.color_array_rgb[1]) + " }')")

    def emission_cal_index_pre_fit(self):

        pass

    def create_feature_index(self):
        try:
            self.UiSetIndexName = UiSetIndexName()
            self.UiSetIndexName.show()
            self.UiSetIndexName.setModal(True)  # 模态显示窗口，即先处理后方可返回主窗体
            self.UiSetIndexName.message.connect(self.save_feature_index)
        except Exception:
            message_str = 'Error: Please INPUT DATA and CHOOSE SIGNALS!'
            self.info_widget_update(message_str)

    def combobox_index_features_initial(self):  # 将字段规则导入
        try:
            self.Select_Features_Index_comboBox.activated.disconnect(self.combobox_index_features_initial_callback)
            # 1、防止多次连接导致的提示信息重复 2、先行断开作为双保险，防止第一遍连接时留下的触发开关由clear()等动作带来的误触发跳转
        except TypeError:
            pass

        try:
            self.slfi = SaveAndLoad()
            self.history_index = self.slfi.reload_feature_index()
            self.Select_Features_Index_comboBox.clear()  # ????第二次导入数据时运行报错   问题已解决 20180226
            self.Select_Features_Index_comboBox.addItem('请选择')
            for i in self.history_index:
                self.Select_Features_Index_comboBox.addItem(i)  # 配合下面的注释
        except Exception:
            message_str = 'Error: from combobox_index_features_initial!'
            self.info_widget_update(message_str)

        self.Select_Features_Index_comboBox.activated.connect(
            self.combobox_index_features_initial_callback)  # 写在这里是为了防止上面addItem改变了currentIndex导致误触发
        # 20180226 交互类性的触发请选择activated而不是currentIndexChanged!!!!!!

    def combobox_index_initial(self, item_list):  # 将文件中的所有字段写入列表
        for i in self.combo_box_names:  # 编号
            eval('self.' + i + '.clear()')  # 清空当前列表
            for j in item_list:
                eval('self.' + i + ".addItem('" + j + "')")

        for i in item_list:  # Setting页面的初始化暂时写在这里!!后续需要挪位置到initial_setting_value()
            self.DataViewer_setting_Time_axis_Samples_comboBox.addItem(i)

    def combobox_index_features_initial_callback(self):
        columns = self.MainProcess_thread_rd.ax_holder_rd.file_columns_orig.tolist()
        columns_to_pre_select = []
        err = True
        if self.Select_Features_Index_comboBox.currentText() in self.history_index:  # 排除用户误选择到“请选择”
            for i in self.history_index[self.Select_Features_Index_comboBox.currentText()]:
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
        else:
            message_str = 'Message: Please Choose the correct feature index!'

        self.info_widget_update(message_str)

    def combobox_index_pre_select(self, pre_select_item_index_list):  # 根据索引预选字段    老数据只有7个字段，目前会报错！
        for i in range(self.combo_box_names.__len__()):  # 编号
            eval('self.' + self.combo_box_names[i] + '.setCurrentIndex(' + str(pre_select_item_index_list[i]) + ')')

    def save_feature_index(self, feature_save_name):
        feature_array = []
        for i in self.combo_box_names:  # 编号
            eval('feature_array.append(self.' + i + '.currentText())')
        self.slfi = SaveAndLoad()
        self.history_index[feature_save_name] = feature_array  # 追加
        self.slfi.store_feature_index(store_index=self.history_index)  # 重新替换feature_index.pkl中所有数据
        message_str = 'Message: Feature index ' + feature_save_name + ' added!'
        self.info_widget_update(message_str)
        # 刷新页面
        self.combobox_index_features_initial()

    # -----|--|Select Features --|Features DB
    def show_feature_index(self):
        self.slfi = SaveAndLoad()
        self.history_index = self.slfi.reload_feature_index()
        self.Data_Base_tableWidget.setColumnCount(16)
        self.Data_Base_tableWidget.setRowCount(len(self.history_index))
        self.Data_Base_tableWidget.setHorizontalHeaderLabels(['车型名称', '时间s', '车速km/h', '油门',
                                                              '加速度g', '档位', '扭矩Nm',
                                                              '喷油量ul/s', '发动机转速rpm', '涡轮转速rpm',
                                                              '制动', '纬度°', '经度°', '方向盘转角°',
                                                              '侧向加速度', '水温℃', '催化器加热',])
        for i, car_index in enumerate(self.history_index):
            car_index_item = QtWidgets.QTableWidgetItem(car_index)
            text_font = QtGui.QFont("Yahei", 8, QtGui.QFont.Bold)
            # car_index_item.setBackground(QtGui.QColor(245, 222, 222))
            car_index_item.setFont(text_font)
            self.Data_Base_tableWidget.setItem(i, 0, car_index_item)
            for j, feature_name in enumerate(self.history_index[car_index]):
                self.Data_Base_tableWidget.setItem(i, j+1, QtWidgets.QTableWidgetItem(feature_name))

    def delete_index_item(self):
        feature_car_name = self.Data_Base_tableWidget.item(self.Data_Base_tableWidget.currentIndex().row(), 0).text()
        self.history_index.pop(feature_car_name)
        SaveAndLoad.store_feature_index(store_index=self.history_index)
        self.show_feature_index()
        message_str = 'Message: Feature index ' + feature_car_name + ' deleted!'
        self.info_widget_update(message_str)
        # 刷新页面
        try:
            self.combobox_index_features_initial() # 刷新下拉菜单
        except Exception:
            pass
        return

    def edit_index_item(self):
        self.history_index.clear()
        for i in range(self.Data_Base_tableWidget.rowCount()):
            feature = []
            for j in range(1, self.Data_Base_tableWidget.columnCount()):
                feature.append(self.Data_Base_tableWidget.item(i, j).text())
            self.history_index[self.Data_Base_tableWidget.item(i, 0).text()] = feature
        message_str = 'Message: Feature item has been changed!'
        SaveAndLoad.store_feature_index(store_index=self.history_index)
        self.show_feature_index()
        self.info_widget_update(message_str)
        try:
            self.combobox_index_features_initial()  # 刷新下拉菜单
        except Exception:
            pass
        return

    # -----|--|System Gain 页面
    # -----|--|System Gain --|Calculation

    def constant_speed_input_callback(self):
        file = QFileDialog.getOpenFileName(self, filter='*.csv *.xls *.xlsx *.mdf *.dat')
        file_path = file[0]
        if file_path != '':
            self.MainProcess_thread_cs = ThreadProcess(method='cs_read_thread',
                                                       filepath=file_path,
                                                       resample_rate=self.DataViewer_setting_Rawdata_mdf_res_TE.toPlainText(),
                                                       intest_data=self.DataViewer_setting_Rawdata_Intest_RB.isChecked(),
                                                       feature_row=self.DataViewer_setting_Rawdata_Intest_hang_data_TE.toPlainText(),
                                                       data_row=self.DataViewer_setting_Rawdata_Intest_hang_feature_TE.toPlainText()
                                                       )
            self.MainProcess_thread_cs.Message_Finish.connect(self.constant_speed_cal)
            self.MainProcess_thread_cs.start()

            message_str = 'Message: Importing ' + file_path + ' ...'
            self.info_widget_update(message_str)

    def constant_speed_cal(self):
        feature_array = []
        for i in self.combo_box_names:  # 编号
            eval('feature_array.append(self.' + i + '.currentText())')

        self.MainProcess_thread_cs_cal = ThreadProcess(method='cs_cal_thread',
                                                       raw_data=self.MainProcess_thread_cs.ax_holder_cs.import_data_ful_,
                                                       feature_list=feature_array,
                                                       frequency=int(self.Constant_Speed_frequency_text_TE.toPlainText()),
                                                       time_block=int(self.Constant_Speed_time_block_text_TE.toPlainText())
                                                       )
        self.MainProcess_thread_cs_cal.Message_Finish.connect(self.constant_speed_replace)
        self.MainProcess_thread_cs_cal.start()

    def constant_speed_replace(self):
        self.replace_cs_content = True

        # str_speed = str(self.MainProcess_thread_cs_cal.ax_holder_cs_cal.cs_table[:, 1].round(0))[1:-1]
        # str_speed = str_speed.replace('.', '')
        # str_speed = ' '.join(str_speed.split())
        # self.Constant_Speed_Show_Speed_text.setText(str_speed)
        # self.Constant_Speed_Show_Speed_text.setFontPointSize(5)
        # str_ped = str(self.MainProcess_thread_cs_cal.ax_holder_cs_cal.cs_table[:, 2].round(0))[1:-1]
        # str_ped = str_ped.replace('.', '')
        # str_ped = ' '.join(str_ped.split())
        # self.Constant_Speed_Show_Ped_text.setText(str_ped)
        # print(self.MainProcess_thread_cs_cal.ax_holder_cs_cal.cs_table)
        self.System_Gain_AT_DCT_StablePed_tableWidget.clear()
        self.System_Gain_AT_DCT_StablePed_tableWidget.setColumnCount(3)
        self.System_Gain_AT_DCT_StablePed_tableWidget.setRowCount(self.MainProcess_thread_cs_cal.ax_holder_cs_cal.cs_table.shape[0])
        self.System_Gain_AT_DCT_StablePed_tableWidget.setHorizontalHeaderLabels(['稳态车速 Km/h', '稳态油门 %', '有问题啊'])
        for i in range(self.MainProcess_thread_cs_cal.ax_holder_cs_cal.cs_table.shape[0]):
            self.System_Gain_AT_DCT_StablePed_tableWidget.setItem(i, 0, QtWidgets.QTableWidgetItem(
                str(self.MainProcess_thread_cs_cal.ax_holder_cs_cal.cs_table['meanspd'].iloc[i].round(1))
            ))
            self.System_Gain_AT_DCT_StablePed_tableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(
                str(self.MainProcess_thread_cs_cal.ax_holder_cs_cal.cs_table['meanped'].iloc[i].round(1))
            ))

    def constant_speed_data_table_view_delete_cs(self):
        current_row = self.System_Gain_AT_DCT_StablePed_tableWidget.currentRow()
        name_to_delete = self.MainProcess_thread_cs_cal.ax_holder_cs_cal.cs_table.iloc[current_row].name
        self.MainProcess_thread_cs_cal.ax_holder_cs_cal.cs_table.drop(name_to_delete, inplace=True)
        self.constant_speed_replace()

    def constant_speed_data_table_view_change_cs(self):
        current_row = self.System_Gain_AT_DCT_StablePed_tableWidget.currentRow()
        # current_col = self.System_Gain_AT_DCT_StablePed_tableWidget.currentColumn()
        self.MainProcess_thread_cs_cal.ax_holder_cs_cal.cs_table.iloc[current_row, 1] = float(
            self.System_Gain_AT_DCT_StablePed_tableWidget.item(current_row, 0).text())
        self.MainProcess_thread_cs_cal.ax_holder_cs_cal.cs_table.iloc[current_row, 2] = float(
            self.System_Gain_AT_DCT_StablePed_tableWidget.item(current_row, 1).text())
        self.constant_speed_replace()

    def cal_sys_gain_data(self):  # Canvas往大调整的时候没问题，重算尺寸自适配，再缩小却不会变回来……目前查不出为什么 20180528 ——LC
        frame_size = self._set_resolution()
        self._draw_canvas(frame_size.width(), frame_size.height())

        feature_array = []
        for i in self.combo_box_names:  # 编号
            eval('feature_array.append(self.' + i + '.currentText())')

        if self.replace_cs_content:
            self.MainProcess_thread_cal = ThreadProcess(method='sg_cal_thread',
                                                        raw_data=self.MainProcess_thread_rd.ax_holder_rd.import_data_ful_,
                                                        feature_array=feature_array,
                                                        pt_type=self.buttonGroup_PT_Type.checkedButton().text(),
                                                        frequency=int(self.DataViewer_setting_Time_axis_Samples_TE.toPlainText()),
                                                        data_cut_time_of_creep=int(self.SystemGain_Cal_setting_creep_time_TE.toPlainText()),
                                                        data_cut_time_of_pedal=int(self.SystemGain_Cal_setting_pedal_time_TE.toPlainText()),
                                                        replace=True,
                                                        cs_table=self.MainProcess_thread_cs_cal.ax_holder_cs_cal.cs_table)
        else:
            self.MainProcess_thread_cal = ThreadProcess(method='sg_cal_thread',
                                                        raw_data=self.MainProcess_thread_rd.ax_holder_rd.import_data_ful_,
                                                        feature_array=feature_array,
                                                        pt_type=self.buttonGroup_PT_Type.checkedButton().text(),
                                                        frequency=int(
                                                            self.DataViewer_setting_Time_axis_Samples_TE.toPlainText()),
                                                        data_cut_time_of_creep=int(
                                                            self.SystemGain_Cal_setting_creep_time_TE.toPlainText()),
                                                        data_cut_time_of_pedal=int(
                                                            self.SystemGain_Cal_setting_pedal_time_TE.toPlainText()),
                                                        replace=False)

        self.MainProcess_thread_cal.Message_Finish.connect(self.show_ax_pictures_sg_del_du)
        self.MainProcess_thread_cal.start()

        message_str = 'Message: Start calculating system gain data ...'
        self.info_widget_update(message_str)

    def show_ax_pictures_sg_del_du(self, message):
        if message == '计算完成':
            self.show_ax_pictures_sg()
        elif message == '删除重复':
            eli_du_ped = UiEliminateDuplicatePed(ped_array=self.MainProcess_thread_cal.ax_holder_SG.pedal_avg,
                                                 rawdata=self.MainProcess_thread_cal.ax_holder_SG.SG_csv_Data_Selc.iloc[:, 1:3])  # 展现给用户的是车速和Pedal
            # eli_du_ped.setModal(True)  # 模态显示窗口，即先处理后方可返回主窗体
            eli_du_ped.show()
            eli_du_ped.message.connect(self.sg_cal_thread_edp)
        elif message == '数据问题':
            message_str = 'Error: Please Check your data or feature correspondence！'
            self.info_widget_update(message_str)

    def sg_cal_thread_edp(self, remove_list):
        self.MainProcess_thread_cal.ax_holder_SG.eliminate_duplicate_ped(remove_list)
        self.show_ax_pictures_sg()

    def show_ax_pictures_sg(self):  # System Gain 绘图函数
        """

        :return:
        """
        try:
            self.dr_acc_curve.axes.clear()
            self.dr_acc_curve.plot_acc_response(
                data=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.accresponce.data,
                ped_avg=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.accresponce.pedal_avg,
                ped_maxacc=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.accresponce.max_acc_ped,
                vehspd_cs=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.vehspd_cs,
                pedal_cs=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.pedal_cs)
            self.PicToolBar_1.press(self.PicToolBar_1.home())
            self.PicToolBar_1.dynamic_update()
        except ValueError or AttributeError:
            message_str = 'Warning: Acc Curve-3D plot failed!'
            self.info_widget_update(message_str)

        try:
            self.dr_sg_curve.axes.clear()
            self.dr_sg_curve.plot_systemgain_curve(
                vehspd_sg=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.vehspd_sg,
                acc_sg=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.acc_sg)
            self.PicToolBar_2.press(self.PicToolBar_2.home())
            self.PicToolBar_2.dynamic_update()
        except ValueError or AttributeError:
            message_str = 'Warning: SystemGain Curve plot failed!'
            self.info_widget_update(message_str)

        try:
            self.dr_cons_spd.axes.clear()
            self.dr_cons_spd.plot_constant_speed(
                vehspd_cs=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.vehspd_cs,
                pedal_cs=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.systemgain.pedal_cs)
            self.PicToolBar_3.press(self.PicToolBar_3.home())
            self.PicToolBar_3.dynamic_update()
        except ValueError or AttributeError:
            message_str = 'Warning:Constant Speed plot failed!'
            self.info_widget_update(message_str)

        try:
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
        except ValueError or AttributeError:
            message_str = 'Warning: Shift Map plot failed!'
            self.info_widget_update(message_str)

        try:
            self.dr_launch.axes.clear()
            self.dr_launch.plot_launch(data=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.launch.data)
            self.PicToolBar_5.press(self.PicToolBar_5.home())
            self.PicToolBar_5.dynamic_update()
        except ValueError or AttributeError:
            message_str = 'Warning: Launch Map plot failed!'
            self.info_widget_update(message_str)

        try:
            self.dr_pedal_map.axes.clear()
            self.dr_pedal_map.plot_pedal_map(data=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.pedalmap.data)
            self.PicToolBar_6.press(self.PicToolBar_6.home())
            self.PicToolBar_6.dynamic_update()
        except ValueError or AttributeError:
            message_str = 'Warning: Pedal Map plot failed!'
            self.info_widget_update(message_str)

        try:
            self.dr_max_acc.axes.clear()
            self.dr_max_acc.plot_max_acc(data=self.MainProcess_thread_cal.ax_holder_SG.sysGain_class.maxacc.data)
            self.PicToolBar_7.press(self.PicToolBar_7.home())
            self.PicToolBar_7.dynamic_update()
        except ValueError or AttributeError:
            message_str = 'Warning: Max Acc Map plot failed!'
            self.info_widget_update(message_str)

        message_str = 'Message: System gain calculation finished!'
        self.info_widget_update(message_str)

    def refresh_cs_data(self):
        self.replace_cs_content = False
        self.Constant_Speed_Show_Speed_text.setText('----')
        self.Constant_Speed_Show_Ped_text.setText('----')

    def refresh_sg_pics(self):
        try:
            # self.dr_acc_curve.axes.clear()
            # self.PicToolBar_1.dynamic_update()
            # self.dr_sg_curve.axes.clear()
            # self.PicToolBar_2.dynamic_update()
            # self.dr_cons_spd.axes.clear()
            # self.PicToolBar_3.dynamic_update()
            # self.dr_shift_map.axes.clear()
            # self.PicToolBar_4.dynamic_update()
            # self.dr_launch.axes.clear()
            # self.PicToolBar_5.dynamic_update()
            # self.dr_pedal_map.axes.clear()
            # self.PicToolBar_6.dynamic_update()
            # self.dr_max_acc.axes.clear()
            # self.PicToolBar_7.dynamic_update()

            while self.gridLayout_2.itemAt(0) is not None:  # 删除当前Lay中的元素
                try:
                    self.gridLayout_2.itemAt(0).widget().setParent(None)  # 删除当前Lay中widget元素，在此为CheckBox
                    self.gridLayout_2.itemAt(0).widget().deleteLater()
                    self.gridLayout_2.removeWidget(self.gridLayout_2.itemAt(0).widget())
                except AttributeError:
                    self.gridLayout_2.removeItem(self.gridLayout_2.itemAt(0))  # 删除当前Lay中spacer元素

        except:
            pass

    # -----|--|System Gain --|Compare Results
    def history_data_reload(self):
        file = QFileDialog.getOpenFileNames(self, filter='*.pkl')
        self.history_file_path_list = file[0]
        try:
            self.sl = SaveAndLoad()
            self.history_data = self.sl.reload_result(file_path_list=self.history_file_path_list)
            message_str = 'Message: History data --' + str(self.history_file_path_list) + ' import finished!'
            self.info_widget_update(message_str)
            self.history_data_plot()
        except Exception as e:
            print('From Reload History Data')
            print(e)

    def history_data_plot(self):

        legend_list = []

        for i in self.history_file_path_list:
            file_name = match(r'^(.+)(/)(.+)(.pkl)$', i)
            legend_list.append(file_name.group(3))

        number_of_history_data = len(self.history_data)
        frame_size = self._set_resolution()
        width = frame_size.width()
        width_fig = width/3/1.2   # 考虑到图之间的间隔等，以系数1.2代替
        height_fig = width_fig
        height_fig_for_subplot = width/number_of_history_data/1.3

        while self.gridLayout_4.itemAt(0) is not None:  # 删除当前Lay中的元素
            try:
                self.gridLayout_4.itemAt(0).widget().setParent(None)  # 删除当前Lay中widget元素，在此为CheckBox
                self.gridLayout_4.itemAt(0).widget().deleteLater()
                self.gridLayout_4.removeWidget(self.gridLayout_4.itemAt(0).widget())
            except AttributeError:
                self.gridLayout_4.removeItem(self.gridLayout_4.itemAt(0))  # 删除当前Lay中spacer元素

        self.dr_history_sg_curve = MyFigureCanvas(width=6, height=4, plot_type='2d')
        curve_list = []
        for i in range(number_of_history_data):  # 将每次画一根线
            self.dr_history_sg_curve.plot_systemgain_curve(vehspd_sg=self.history_data[i].sysGain_class.systemgain.
                                                           vehspd_sg, acc_sg=self.history_data[i].sysGain_class.
                                                           systemgain.acc_sg)
            curve_list.append(self.dr_history_sg_curve.axes.get_lines()[i*7])
        self.dr_history_sg_curve.axes.legend(curve_list, legend_list)  # 第1、8、15……为需求的SG Curve
        self.PicToolBar_history1 = NavigationBar(self.dr_history_sg_curve, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history1, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.dr_history_sg_curve, 1, 0, 1, 1)
        self.dr_history_sg_curve.setMinimumSize(QtCore.QSize(width_fig, height_fig))

        self.dr_history_cons_spd = MyFigureCanvas(width=6, height=4, plot_type='2d')
        for i in range(number_of_history_data):  # 将每次画一根线
            self.dr_history_cons_spd.plot_constant_speed(vehspd_cs=self.history_data[i].sysGain_class.systemgain.
                                                         vehspd_cs, pedal_cs=self.history_data[i].sysGain_class.
                                                         systemgain.pedal_cs)
        self.dr_history_cons_spd.axes.legend(legend_list)
        self.PicToolBar_history2 = NavigationBar(self.dr_history_cons_spd, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history2, 0, 1, 1, 1)
        self.gridLayout_4.addWidget(self.dr_history_cons_spd, 1, 1, 1, 1)
        self.dr_history_cons_spd.setMinimumSize(QtCore.QSize(width_fig, height_fig))

        self.dr_history_max_acc = MyFigureCanvas(width=6, height=4, plot_type='2d')
        for i in range(number_of_history_data):  # 将每次画一根线
            self.dr_history_max_acc.plot_max_acc(data=self.history_data[i].sysGain_class.maxacc.data)
        self.dr_history_max_acc.axes.legend(legend_list)
        self.PicToolBar_history3 = NavigationBar(self.dr_history_max_acc, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history3, 0, 2, 1, 1)
        self.gridLayout_4.addWidget(self.dr_history_max_acc, 1, 2, 1, 1)
        self.dr_history_max_acc.setMinimumSize(QtCore.QSize(width_fig, height_fig))

        self.dr_history_acc_curve = MyFigureCanvas(width=18, height=5, plot_type='3d-subplot')
        self.dr_history_acc_curve.plot_acc_response_subplot(history_data=self.history_data, legend_name=legend_list)
        self.PicToolBar_history4 = NavigationBar(self.dr_history_acc_curve, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history4, 2, 0, 1, 3)
        self.gridLayout_4.addWidget(self.dr_history_acc_curve, 3, 0, 1, 3)
        self.dr_history_acc_curve.setMinimumSize(QtCore.QSize(width_fig, height_fig_for_subplot))

        self.dr_history_launch = MyFigureCanvas(width=18, height=5, plot_type='2d-subplot')
        self.dr_history_launch.plot_launch_subplot(history_data=self.history_data, legend_name=legend_list)
        self.PicToolBar_history5 = NavigationBar(self.dr_history_launch, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history5, 4, 0, 1, 3)
        self.gridLayout_4.addWidget(self.dr_history_launch, 5, 0, 1, 3)
        self.dr_history_launch.setMinimumSize(QtCore.QSize(width_fig, height_fig_for_subplot))

        self.dr_history_shift_map = MyFigureCanvas(width=18, height=5, plot_type='2d-subplot')
        self.dr_history_shift_map.plot_shift_map_subplot(history_data=self.history_data, legend_name=legend_list)
        self.PicToolBar_history6 = NavigationBar(self.dr_history_shift_map, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history6, 6, 0, 1, 3)
        self.gridLayout_4.addWidget(self.dr_history_shift_map, 7, 0, 1, 3)
        self.dr_history_shift_map.setMinimumSize(QtCore.QSize(width_fig, height_fig_for_subplot))

        self.dr_history_pedal_map = MyFigureCanvas(width=18, height=5, plot_type='2d-subplot')
        self.dr_history_pedal_map.plot_pedal_map_subplot(history_data=self.history_data, legend_name=legend_list)
        self.PicToolBar_history7 = NavigationBar(self.dr_history_pedal_map, self)
        self.gridLayout_4.addWidget(self.PicToolBar_history7, 8, 0, 1, 3)
        self.gridLayout_4.addWidget(self.dr_history_pedal_map, 9, 0, 1, 3)
        self.dr_history_pedal_map.setMinimumSize(QtCore.QSize(width_fig, height_fig_for_subplot))

    def data_table_view_show(self, data_list):
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

    # -----|--|RealRoadFC 页面
    def real_road_fc_cal(self):
        feature_array = []
        for i in self.combo_box_names:  # 编号
            eval('feature_array.append(self.' + i + '.currentText())')

        self.MainProcess_thread_rrc_cal = ThreadProcess(method='real_road_cal_thread',
                                                        raw_data=self.MainProcess_thread_rd.ax_holder_rd.import_data_ful_,
                                                        feature_array=feature_array,)
        self.MainProcess_thread_rrc_cal.Message_Finish.connect()
        self.MainProcess_thread_rrc_cal.start()
        message_str = 'Message: Start calculating real road fuel consumption data ...'
        self.info_widget_update(message_str)

    def real_road_fc_show(self):
        pass
        
    # -----|--|Setting 页面
    def initial_setting_value(self):
        pass

    def enable_disable_set_data_viewer_data_source_dat_mdf(self):
        if self.DataViewer_setting_Rawdata_mdf_res_RB.isChecked():
            self.DataViewer_setting_Rawdata_mdf_res_HZ.setEnabled(True)
            self.DataViewer_setting_Rawdata_mdf_res_TE.setEnabled(True)
            self.DataViewer_setting_Rawdata_mdf_HZ.setEnabled(True)
        else:
            self.DataViewer_setting_Rawdata_mdf_res_HZ.setEnabled(False)
            self.DataViewer_setting_Rawdata_mdf_res_TE.setEnabled(False)
            self.DataViewer_setting_Rawdata_mdf_HZ.setEnabled(False)

    def enable_disable_set_data_viewer_data_source_intest(self):
        if self.DataViewer_setting_Rawdata_Intest_RB.isChecked():
            self.DataViewer_setting_Rawdata_Intest_feature.setEnabled(True)
            self.DataViewer_setting_Rawdata_Intest_hang_data_TE.setEnabled(True)
            self.DataViewer_setting_Rawdata_Intest_hang_feature.setEnabled(True)
            self.DataViewer_setting_Rawdata_Intest_data.setEnabled(True)
            self.DataViewer_setting_Rawdata_Intest_hang_feature_TE.setEnabled(True)
            self.DataViewer_setting_Rawdata_Intest_hang_data.setEnabled(True)
        else:
            self.DataViewer_setting_Rawdata_Intest_feature.setEnabled(False)
            self.DataViewer_setting_Rawdata_Intest_hang_data_TE.setEnabled(False)
            self.DataViewer_setting_Rawdata_Intest_hang_feature.setEnabled(False)
            self.DataViewer_setting_Rawdata_Intest_data.setEnabled(False)
            self.DataViewer_setting_Rawdata_Intest_hang_feature_TE.setEnabled(False)
            self.DataViewer_setting_Rawdata_Intest_hang_data.setEnabled(False)

    def enable_disable_set_data_viewer_setting_time_axis_fs_base(self):

        if self.DataViewer_setting_Time_axis_Samples_RB.isChecked():
            self.DataViewer_setting_Time_axis_Samples_TE.setEnabled(True)
        else:
            self.DataViewer_setting_Time_axis_Samples_TE.setEnabled(False)

    def enable_disable_set_data_viewer_setting_time_axis_signal_base(self):
        if self.DataViewer_setting_Time_axis_Signal_RB.isChecked():
            self.DataViewer_setting_Time_axis_Samples_comboBox.setEnabled(True)
        else:
            self.DataViewer_setting_Time_axis_Samples_comboBox.setEnabled(False)

    def enable_disable_set_real_road_fc_button_group_bsfc(self):
        if self.RealRoadFc_Engine_Working_Points_BSFC_Y_RB.isChecked():
            self.RealRoadFc_Engine_Working_Points_BSFC_pushbutton.setEnabled(True)
            self.RealRoadFc_Engine_Working_Points_BSFC_TE.setEnabled(True)
        elif self.RealRoadFc_Engine_Working_Points_BSFC_N_RB.isChecked():
            self.RealRoadFc_Engine_Working_Points_BSFC_pushbutton.setEnabled(False)
            self.RealRoadFc_Engine_Working_Points_BSFC_TE.setEnabled(False)

    def set_real_road_fc_xy_range_qslider_value_change(self, index):
        if index == 1:
            text_1 = 5000 + 20 * (self.RealRoadFc_Engine_Working_Points_X_Range_slider.value() - 50)
            self.RealRoadFc_Engine_Working_Points_X_Range_Show_TE.setPlainText(str(text_1))
        elif index == 2:
            text_2 = 350 + 5 * (self.RealRoadFc_Engine_Working_Points_Y_Range_slider.value() - 50)
            self.RealRoadFc_Engine_Working_Points_Y_Range_Show_TE.setPlainText(str(text_2))


class ThreadProcess(QtCore.QThread):
    Message_Finish = QtCore.pyqtSignal(str)

    def __init__(self, method, **kwargs):
        super(ThreadProcess, self).__init__()
        self.method = method
        self.kwargs = kwargs

    def run(self):
        try:
            getattr(self, self.method, 'nothing')()
        except BaseException as e:
            print(e)
            message_str = 'Error: Error occurred in calculating SG data!'
            self.info_widget_update(message_str)

    def read_thread(self):
        self.ax_holder_rd = ReadFile(file_path=self.kwargs['filepath'], resample_rate=self.kwargs['resample_rate'],
                                     intest_data=self.kwargs['intest_data'],
                                     feature_row=self.kwargs['feature_row'], data_row=self.kwargs['data_row'])
        if self.ax_holder_rd.import_status == 'Error':
            self.Message_Finish.emit("导入失败")
        else:
            self.Message_Finish.emit("导入完成")

    def sg_cal_thread(self):
        if self.kwargs['replace']:
            self.ax_holder_SG = SystemGain(raw_data=self.kwargs['raw_data'], feature_array=self.kwargs['feature_array'],
                                           pt_type=self.kwargs['pt_type'],
                                           data_cut_time_of_creep=self.kwargs['data_cut_time_of_creep'],
                                           data_cut_time_of_pedal=self.kwargs['data_cut_time_of_pedal'],
                                           replace=True, cs_table=self.kwargs['cs_table'])
        else:
            self.ax_holder_SG = SystemGain(raw_data=self.kwargs['raw_data'], feature_array=self.kwargs['feature_array'],
                                           pt_type=self.kwargs['pt_type'],
                                           data_cut_time_of_creep=self.kwargs['data_cut_time_of_creep'],
                                           data_cut_time_of_pedal=self.kwargs['data_cut_time_of_pedal'],)
        try:
            ret = self.ax_holder_SG.sg_main()
        except Exception:
            ret = "Error"

        if ret == 'eliminate_duplicate_ped':
            self.Message_Finish.emit("删除重复")
        elif ret == "Error":
            self.Message_Finish.emit("数据问题")
        else:
            self.Message_Finish.emit("计算完成")

    def cs_read_thread(self):
        self.ax_holder_cs = ReadFile(file_path=self.kwargs['filepath'], resample_rate=self.kwargs['resample_rate'],
                                     intest_data=self.kwargs['intest_data'],
                                     feature_row=self.kwargs['feature_row'], data_row=self.kwargs['data_row']
                                     )
        self.Message_Finish.emit("计算完成！")

    def cs_cal_thread(self):
        self.ax_holder_cs_cal = ConstantSpeed(raw_data=self.kwargs['raw_data'],
                                              feature_list=self.kwargs['feature_list'],
                                              frequency=self.kwargs['frequency'],
                                              time_block=self.kwargs['time_block'])
        self.ax_holder_cs_cal.cs_main()
        self.Message_Finish.emit("计算完成！")

    def show_raw_data(self):
        pass
    
    def real_road_cal_thread(self):
        self.ax_holder_rrc = RealRoadFc(raw_data=self.kwargs['raw_data'], feature_array=self.kwargs['feature_array'],
                                        pt_type=self.kwargs['pt_type'],)
        self.ax_holder_rrc.real_road_main()
        self.Message_Finish.emit("计算完成！")


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
