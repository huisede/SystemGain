# -*- coding: utf-8 -*-

import numpy as np
from pandas import read_csv, read_excel
from scipy import interpolate
import matplotlib.pyplot as plt
import re
import pickle


class SystemGain(object):
    """
    Main class of system gain, contains all the thing needed to be calculated or plotted.

    Created By Lvhuijia 20180202
    Edited By Luchao 20180204

    Contains：
    ******
    fun sg_main————Main function of calculating system gain, save  'self.sysGain_class'  to be called from UI.
    ******
    fun acc_response————Prepare acceleration response fig data
    fun launch————Prepare launch fig data
    fun max_acc————Prepare maximum acceleration fig data
    fun pedal_map————Prepare pedal map fig data
    fun shift_map————Prepare shift map fig data
    stc fun cut_sg_data_pedal————Data cutting function
    stc fun arm_interpolate————2-D interpolation method to generate system gain arm fig
    ******
    class AccResponse/Launch/MaxAcc/PedalMap/ShiftMap————Wrapper class of the corresponding fig
    class SystemGainDocker————A class that used to wrap all raw data and results
    ******
    fun plot_max_acc————Plotting method of generating maximum acceleration fig. NEED TO BE REWRITE IN Generate_Figs.py
    fun plot_pedal_map————Plotting method of generating pedal map fig. NEED TO BE REWRITE IN Generate_Figs.py
    fun plot_shift_map————Plotting method of generating shift map fig. NEED TO BE REWRITE IN Generate_Figs.py
    """

    def __init__(self, raw_data, feature_array, pt_type, **kwargs):
        """
        Initial function of system gain.

        :param
        """
        self.raw_data = raw_data
        self.feature_array = feature_array
        self.pt_type = pt_type
        self.sysGain_class = {}
        if 'replace' in kwargs:
            self.replace_cs = True
            self.cs_table = kwargs['cs_table']
        else:
            self.replace_cs = False

    def sg_main(self):
        '''
        Main function of calculating system gain, save  'self.sysGain_class'  to be called from UI.

        '''

        # *******1-GetSysGainData******
        # 获取数据，判断数据类型，不同读取，获取文件名信息，
        # SG_csv_Data_ful = read_csv(file_path)
        SG_csv_Data_ful = self.raw_data
        # *******2-GetSGColumn*********
        # 获取列号，标准变量及面板输入，数据预处理
        SG_csv_Data_Selc = SG_csv_Data_ful.loc[:, self.feature_array]
        # SG_csv_Data = SG_csv_Data_Selc.drop_duplicates()    # 先不去重
        SG_csv_Data = SG_csv_Data_Selc  # 选到重复的会报错 ！！！！！所以修改了以下索引格式
        time_Data = SG_csv_Data.iloc[:, 0].tolist()
        vehSpd_Data = SG_csv_Data.iloc[:, 1].tolist()
        pedal_Data = SG_csv_Data.iloc[:, 2].tolist()
        acc_Data = SG_csv_Data.iloc[:, 3].tolist()
        gear_Data = SG_csv_Data.iloc[:, 4].tolist()
        torq_Data = SG_csv_Data.iloc[:, 5].tolist()
        fuel_Data = SG_csv_Data.iloc[:, 6].tolist()
        enSpd_Data = SG_csv_Data.iloc[:, 7].tolist()
        turbSpd_Data = SG_csv_Data.iloc[:, 8].tolist()

        colour_Bar = ['orange', 'lightgreen', 'c', 'royalblue', 'lightcoral', 'yellow', 'red', 'brown',
                      'teal', 'blue', 'coral', 'gold', 'lime', 'olive']
        # 加速度修正
        acc_offset = ((vehSpd_Data[-1] - vehSpd_Data[0]) / 3.6 / (time_Data[-1] - time_Data[0]) - np.average(
            acc_Data[:]) * 9.8) / 9.8
        acc_Data = [x + acc_offset for x in acc_Data]
        # acc_check = (vehSpd_Data[-1]-vehSpd_Data[0])/3.6-np.average(acc_Data)*9.8*(time_Data[-1]-time_Data[0])
        # 数据切分
        pedal_cut_index, pedal_avg = self.cut_sg_data_pedal(pedal_Data, vehSpd_Data)
        # fig1三维图，增加最大加速度连线以及稳态车速线
        obj_AccResponse = self.acc_response(vehSpd_Data, acc_Data, pedal_cut_index, pedal_avg)  # 数据封装
        # # obj_AccResponse.plot_acc_response()
        # # fig2起步图，[5,10,20,30,40,50,100],后续补充判断大油门不是100也画出来,粗细
        obj_Launch = self.launch(acc_Data, pedal_Data, pedal_cut_index, pedal_avg)
        # # obj_Launch.plot_launch()
        obj_MaxAcc = self.max_acc(acc_Data, pedal_cut_index, pedal_avg)
        # obj_MaxAcc.plot_maxacc()
        # fig4 PedalMap-Gear
        obj_PedalMap = self.pedal_map(pedal_Data, enSpd_Data, torq_Data, pedal_cut_index, pedal_avg, colour_Bar)
        # obj_PedalMap.plot_pedal_map()
        # fig5 ShiftMap
        obj_ShiftMap = self.shift_map(pedal_Data, gear_Data, vehSpd_Data, pedal_cut_index, pedal_avg, colour_Bar,
                                      enSpd_Data, turbSpd_Data, kind=self.pt_type)
        # obj_ShiftMap.plot_shift_map()
        obj_SystemGain = self.systemgain_curve(pedal_Data, vehSpd_Data, acc_Data, pedal_cut_index, pedal_avg)
        self.sysGain_class = self.SystemGainDocker(self.pt_type, obj_AccResponse, obj_Launch, obj_MaxAcc, obj_PedalMap,
                                                   obj_ShiftMap, SG_csv_Data_ful, obj_SystemGain)

    def acc_response(self, vehspd_data, acc_data, pedal_cut_index, pedal_avg):
        try:
            acc_ped_map = [[], [], []]
            for i in range(0, len(pedal_avg)):
                iVehSpd = vehspd_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]
                iPed = [pedal_avg[i] * ix / ix for ix in range(pedal_cut_index[0][i], pedal_cut_index[1][i])]
                iAcc = acc_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]

                # 删除加速度小于0.05g的数据，认为是踩了制动
                data_len = len(iAcc)
                j = 0
                while j < data_len:
                    if iAcc[j] < 0.0:  # 20180211 0.05->0.0
                        del iVehSpd[j]
                        del iPed[j]
                        del iAcc[j]
                        data_len = data_len - 1
                        j = j - 1
                    j = j + 1

                acc_ped_map[0].append(iPed)
                acc_ped_map[1].append(iVehSpd)
                acc_ped_map[2].append(iAcc)
            obj = self.AccResponse(acc_ped_map, pedal_avg)
        except Exception:
            acc_ped_map = [[], [], []]
            print('Error From acc_response Cal!')
            obj = self.AccResponse(acc_ped_map, pedal_avg)
        return obj

    def launch(self, acc_data, pedal_data, pedal_cut_index, pedal_avg):
        try:
            launch_map = [[], [], []]
            for i in range(0, len(pedal_avg)):
                if int(round(pedal_avg[i] / 5) * 5) in [10, 20, 30, 50, 100]:
                    iTime = [0.05 * (ix - pedal_cut_index[0][i]) for ix in
                             range(pedal_cut_index[0][i], pedal_cut_index[0][i] + 100)]
                    iAcc = acc_data[pedal_cut_index[0][i]:pedal_cut_index[0][i] + 100]
                    launch_map[0].append(pedal_data[pedal_cut_index[0][i]:pedal_cut_index[0][i] + 100])
                    launch_map[1].append(iAcc)
                    launch_map[2].append(iTime)
                elif pedal_avg[i] == max(pedal_avg):
                    iTime = [0.05 * (ix - pedal_cut_index[0][i]) for ix in
                             range(pedal_cut_index[0][i], pedal_cut_index[0][i] + 100)]
                    iAcc = acc_data[pedal_cut_index[0][i]:pedal_cut_index[0][i] + 100]
                    launch_map[0].append(pedal_data[pedal_cut_index[0][i]:pedal_cut_index[0][i] + 100])
                    launch_map[1].append(iAcc)
                    launch_map[2].append(iTime)
            obj = self.Launch(launch_map)
        except Exception:
            launch_map = [[], [], []]
            print('Error From acc_launch Cal!')
            obj = self.Launch(launch_map)
        return obj

    def max_acc(self, acc_data, pedal_cut_index, pedal_avg):
        try:
            acc_Ped_Max = []
            for i in range(0, len(pedal_avg)):
                acc_Ped_Max.append(max(acc_data[pedal_cut_index[0][i]:pedal_cut_index[0][i] + 1000]))
            obj = self.MaxAcc(pedal_avg, acc_Ped_Max)
        except Exception:
            acc_Ped_Max = []
            print('Error From max_acc Cal!')
            obj = self.MaxAcc(pedal_avg, acc_Ped_Max)
        return obj

    def pedal_map(self, pedal_data, enSpd_data, torq_data, pedal_cut_index, pedal_avg, colour):
        try:
            pedal_map = [[], [], []]
            for i in range(0, len(pedal_avg)):
                iTorq = torq_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]
                iEnSpd = enSpd_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]
                pedal_map[0].extend(pedal_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]])
                pedal_map[1].extend(iEnSpd)
                pedal_map[2].extend(iTorq)
            obj = self.PedalMap(pedal_map)
        except Exception:
            pedal_map = [[], [], []]
            print('Error From pedal_map Cal!')
            obj = self.PedalMap(pedal_map)
        return obj

    def shift_map(self, pedal_data, gear_data, vehspd_data, pedal_cut_index, pedal_avg, colour,
                  enSpd_Data, turbSpd_Data, kind):
        try:
            shiftMap = [[], [], []]
            if kind == 'AT/DCT':
                for i in range(1, max(gear_data)):
                    # Gear上升沿下降沿
                    for j in range(1, len(gear_data) - 1):
                        if gear_data[j - 1] == i and gear_data[j] == i + 1:
                            for k in range(0, len(pedal_avg)):
                                if j > pedal_cut_index[0][k] and j < pedal_cut_index[1][k]:
                                    shiftMap[0].append(gear_data[j - 1])
                                    shiftMap[1].append(pedal_data[j - 1])
                                    shiftMap[2].append(vehspd_data[j - 1])
                # 按档位油门车速排序
                shiftMap_Sort = sorted(np.transpose(shiftMap), key=lambda x: [x[0], x[1], x[2]])
                shiftMap_Data = np.transpose(shiftMap_Sort)
                obj = self.ShiftMap(shiftMap_Data)
            elif kind == 'CVT':
                for i in range(len(pedal_avg)):
                    shiftMap[0].append(enSpd_Data[pedal_cut_index[0][i]:pedal_cut_index[1][i]])
                    shiftMap[1].append(turbSpd_Data[pedal_cut_index[0][i]:pedal_cut_index[1][i]])
                    shiftMap[2].append(vehspd_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]])
                obj = self.ShiftMap(shiftMap, pedal_avg=pedal_avg)
            elif kind == 'AT':
                pass
        except Exception:
            shiftMap = [[], [], []]
            print('Error From shift_map Cal!')
            obj = self.ShiftMap(shiftMap)
        return obj

    def systemgain_curve(self, pedal_data, vehspd_data, acc_data, pedal_cut_index, pedal_avg):
        try:
            vehspd, ped, acc = [], [], []
            vehspd_sg_for_inter = []
            vehspd_steady_for_inter = []

            for i in range(0, len(pedal_avg)):
                ivehspd = vehspd_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]
                iped = [pedal_avg[i]] * (pedal_cut_index[1][i] - pedal_cut_index[0][i])
                iacc = acc_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]

                vehspd = vehspd + ivehspd
                ped = ped + iped
                acc = acc + iacc
                vehspd_sg_for_inter.append(max(ivehspd))

            if self.replace_cs:  # 如果有稳态车速实验数据输入
                cs_ary = self.cs_table[:, 1:3]  # 索引所得第一列为车速，第二列为油门
                cs_vspd = cs_ary[:, 0]
                cs_ped = cs_ary[:, 1]
                if pedal_avg[0] == 0:  # 如果原始数据中有怠速数据，则替换
                    cs_ped[0] = 0
                    cs_vspd[1] = vehspd_sg_for_inter[0]  # 怠速车速
                else:
                    cs_ped = cs_ped[1:]  # 去掉传递过来不对的怠速转速
                    cs_vspd = cs_vspd[1:]

                cs_interp = interpolate.interp1d(cs_ped, cs_vspd)
                for i, content in enumerate(pedal_avg):
                    if min(cs_ped) < content < max(cs_ped):
                        vehspd_steady_for_inter.append(cs_interp(content))
                    else:
                        vehspd_steady_for_inter.append(vehspd_sg_for_inter[i])
            else:
                vehspd_steady_for_inter = vehspd_sg_for_inter

            points_for_inter = np.zeros((len(acc), 2))
            points_for_inter[:, 0] = vehspd
            points_for_inter[:, 1] = ped
            points_for_inter[:, 1] = points_for_inter[:, 1] / 100 * 51
            acc_for_inter = np.array(acc)

            pedal_steady_for_inter = [x / 100 * 51 + 12.7 for x in pedal_avg]
            vehspd_steady_tb_inter = np.linspace(min(vehspd_steady_for_inter), 120, 200)
            pedal_steady_function = interpolate.interp1d(vehspd_steady_for_inter, pedal_steady_for_inter)
            pedal_steady_tb_inter = pedal_steady_function(vehspd_steady_tb_inter)
            points_tb_inter = np.zeros((len(pedal_steady_tb_inter), 2))
            points_tb_inter[:, 0] = vehspd_steady_tb_inter
            points_tb_inter[:, 1] = pedal_steady_tb_inter

            '# steady velocity & pedal checked: same with matlab'
            # np.savetxt('vehspd_steady_for_inter.csv', vehspd_steady_for_inter, delimiter=',')
            # np.savetxt('pedal_steady_for_inter.csv', pedal_steady_for_inter, delimiter=',')
            # np.savetxt('pedal_steady_tb_inter.csv', pedal_steady_tb_inter, delimiter=',')
            # np.savetxt('vehspd_steady_tb_inter.csv', vehspd_steady_tb_inter, delimiter=',')

            grid_z1 = interpolate.griddata(points_for_inter, acc_for_inter, points_tb_inter, method='linear')
            grid_z1 = grid_z1 / 12.7
            grid_z1 = self.smooth(grid_z1, 5)

            '#  function "griddata" checked: same with matlab'
            # np.savetxt('points_for_inter.csv', points_for_inter, delimiter=',')
            # np.savetxt('acc_for_inter.csv', acc_for_inter, delimiter=',')
            # np.savetxt('points_tb_inter.csv', points_tb_inter, delimiter=',')
            # np.savetxt('grid_z1.csv', points_tb_inter, delimiter=',')

            # obj = SystemGainPlot()
            obj = self.SystemGainCurve(vehspd_steady_tb_inter, grid_z1, vehspd_steady_for_inter, pedal_avg)
        except Exception:
            obj = self.SystemGainCurve([], [], [], [])
            print('Error From systemgain_curve Cal!')
        return obj

    @staticmethod
    def cut_sg_data_pedal(pedal_data, vehspd_data):
        # 数据切分
        # edges detection initialize to avoid additional detection of rising edges/trailing edges
        pedal_data[0], pedal_data[-1] = 0, 0
        vehspd_data[0], vehspd_data[-1] = 0, 0
        # end of edges detection initialize

        for i in range(len(vehspd_data)):  # GPS 车速置零   20180213 LuChao
            if vehspd_data[i] < 0.5:
                vehspd_data[i] = 0

        r_edge_pedal, t_edge_pedal = [], []
        r_edge_vehspd, t_edge_vehspd = [], []

        # Pedal,vehspd上升沿下降沿
        for i in range(1, len(pedal_data) - 1):

            if pedal_data[i - 1] == 0 and pedal_data[i] > 0:
                r_edge_pedal.append(i)
            if pedal_data[i + 1] == 0 and pedal_data[i] > 0:
                t_edge_pedal.append(i)
            if vehspd_data[i - 1] == 0 and vehspd_data[i] > 0:
                r_edge_vehspd.append(i)
            if vehspd_data[i + 1] == 0 and vehspd_data[i] > 0:
                t_edge_vehspd.append(i)
        # 判断个数大于1000个，去重未做！！
        pedal_cut_index, pedal_avg = [[], []], []

        # creep auto detection
        for j in range(0, len(t_edge_vehspd)):
            if (t_edge_vehspd[j] - r_edge_vehspd[j] > 500) & (
                            3.5 < np.average(vehspd_data[r_edge_vehspd[j] + 200:t_edge_vehspd[j] - 200]) < 8.5) & (
                        np.average(pedal_data[r_edge_vehspd[j]:t_edge_vehspd[j]]) < 0.01):
                pedal_cut_index[0].append(r_edge_vehspd[j] - 40)  # 车速信号相对于加速度信号有迟滞
                pedal_cut_index[1].append(t_edge_vehspd[j] - 40)
                pedal_avg.append(np.mean(pedal_data[r_edge_vehspd[j]:t_edge_vehspd[j]]))

        for j in range(0, len(r_edge_pedal)):
            if t_edge_pedal[j] - r_edge_pedal[j] > 400:  # 时间长度
                if np.cov(pedal_data[r_edge_pedal[j] + 20:t_edge_pedal[j] - 20]) < 3:
                    pedal_cut_index[0].append(r_edge_pedal[j])
                    pedal_cut_index[1].append(t_edge_pedal[j])
                    pedal_avg.append(np.mean(pedal_data[r_edge_pedal[j]:t_edge_pedal[j]]))

        return pedal_cut_index, pedal_avg

    class AccResponse:
        def __init__(self, matrix, para1):
            self.xdata = matrix[1]
            self.ydata = matrix[0]
            self.zdata = matrix[2]
            self.data = matrix
            self.pedal_avg = para1

    class Launch:
        def __init__(self, matrix):
            self.xdata = matrix[2]
            self.ydata = matrix[1]
            self.pedal = matrix[0]
            self.data = matrix

    class MaxAcc:
        def __init__(self, x, y):
            self.xdata = x
            self.ydata = y
            self.data = [x, y]

    class PedalMap:
        def __init__(self, matrix):
            self.xdata = matrix[1]
            self.ydata = matrix[2]
            self.zdata = matrix[0]
            self.data = matrix

    class ShiftMap:
        def __init__(self, matrix, **kwargs):
            self.xdata = matrix[2]
            self.ydata = matrix[1]
            self.gear = matrix[0]
            self.data = matrix
            self.kwargs = kwargs

    class SystemGainCurve:
        def __init__(self, vehspd_sg, acc_sg, vehspd_cs, pedal_cs):
            self.vehspd_sg = vehspd_sg
            self.acc_sg = acc_sg
            self.vehspd_cs = vehspd_cs
            self.pedal_cs = pedal_cs

    class SystemGainDocker:

        def __init__(self, pt_type, accresponce, launch, maxacc, pedalmap, shiftmap, rawdata, systemgain):
            self.pt_type = pt_type
            self.accresponce = accresponce
            self.launch = launch
            self.maxacc = maxacc
            self.pedalmap = pedalmap
            self.shiftmap = shiftmap
            self.rawdata = rawdata
            self.systemgain = systemgain

    @staticmethod
    def smooth(data, window):
        # a: 1-D array containing the data to be smoothed by sliding method
        # WSZ: smoothing window size
        out0 = np.convolve(data, np.ones(window, dtype=int), 'valid') / window
        r = np.arange(1, window - 1, 2)
        start = np.cumsum(data[:window - 1])[::2] / r
        stop = (np.cumsum(data[:-window:-1])[::2] / r)[::-1]
        return np.concatenate((start, out0, stop))


class ReadFile(object):

    def __init__(self, file_path):
        """
        Initial function of Read File.

        :param file_path: path of system gain file in local disc
        """
        self.file_path = file_path
        self.file_columns_orig = []
        self.file_columns = []
        self.csv_data_ful = []
        self.start_read()

    def start_read(self):
        try:
            self.csv_data_ful = read_csv(self.file_path, low_memory=False)  # utf-8默认编码
        except UnicodeDecodeError:
            self.csv_data_ful = read_csv(self.file_path, encoding='gb18030')  # gb18030中文编码

        self.file_columns_orig = self.csv_data_ful.columns
        back_up_counter = 0
        for i in self.csv_data_ful.columns:  # 去除'[]'号，防止控件命名问题
            try:
                ma = re.match(r'^([0-9a-zA-Z/:_.%\u4e00-\u9fa5\-]+)(\[?)([0-9a-zA-Z/:_.%\u4e00-\u9fa5\[\]\-]*)$', i)
                self.file_columns.append(ma.group(1))
            except AttributeError:
                back_up_counter += 1
                self.file_columns.append('signal' + str(back_up_counter) + '_with_unknown_char')


class SaveAndLoad(object):
    def __init__(self):
        pass

    @staticmethod
    def store_result(file_path, store_data):
        output_file = open(file_path, 'wb')
        pickle.dump(store_data, output_file)
        output_file.close()
        return

    @staticmethod
    def reload_result(file_path_list):
        data_reload = []
        for i in file_path_list:
            input_file = open(i, 'rb')
            data_reload.append(pickle.load(input_file))
            input_file.close()
        return data_reload

    @staticmethod
    def store_feature_index(store_index):
        output_file = open('./bin/feature_index.pkl', 'wb')
        pickle.dump(store_index, output_file)
        output_file.close()
        return

    @staticmethod
    def reload_feature_index():
        input_file = open('./bin/feature_index.pkl', 'rb')
        data_reload = pickle.load(input_file)
        input_file.close()
        return data_reload


class ConstantSpeed(object):
    def __init__(self, raw_data, feature_list):
        self.raw_data = raw_data
        self.feature_list = feature_list
        self.frequency = 20
        self.time_block = 15

        self.cs_csv_data = self.raw_data.loc[:, feature_list]
        self.veh_spd = self.cs_csv_data.iloc[:, 1].tolist()
        self.pedal = self.cs_csv_data.iloc[:, 2].tolist()
        self.acc = self.cs_csv_data.iloc[:, 3].tolist()
        self.gear = self.cs_csv_data.iloc[:, 4].tolist()
        self.en_spd = self.cs_csv_data.iloc[:, 7].tolist()

        self.acc_smo = self.smooth(self.acc, 1.5 * self.frequency)
        self.cs_table = []

    def cs_main(self):
        k = 0
        self.cs_table.append([0, 5, 0, 0, 0, 800, 1, 0])
        try:
            for i in range(0, len(self.veh_spd) - self.frequency * self.time_block, self.frequency):
                if self.veh_std_cal(i) < 0.7 and self.gear_std_cal(i) == 0 and self.mean_speed_cal(i) > 5:
                    if k == 0:
                        self.cs_table.append([i,
                                              self.mean_speed_cal(i),
                                              self.mean_ped_cal(i),
                                              self.mean_acc_cal(i),
                                              self.acc_smooth_rate_std_cal(i),
                                              self.mean_rpm_cal(i),
                                              self.gear[i],
                                              self.veh_std_cal(i)])
                        k = k + 1
                    elif self.veh_std_cal(i) < self.cs_table[k][5] and np.abs(
                                    self.mean_speed_cal(i) - self.cs_table[k][1]) < 5:
                        self.cs_table[k] = [i,
                                            self.mean_speed_cal(i),
                                            self.mean_ped_cal(i),
                                            self.mean_acc_cal(i),
                                            self.acc_smooth_rate_std_cal(i),
                                            self.mean_rpm_cal(i),
                                            self.gear[i],
                                            self.veh_std_cal(i)]
                    elif np.abs(self.mean_speed_cal(i) - self.cs_table[k][1]) >= 5:
                        k = k + 1
                        self.cs_table.append([i,
                                              self.mean_speed_cal(i),
                                              self.mean_ped_cal(i),
                                              self.mean_acc_cal(i),
                                              self.acc_smooth_rate_std_cal(i),
                                              self.mean_rpm_cal(i),
                                              self.gear[i],
                                              self.veh_std_cal(i)])
            self.cs_table = np.array(self.cs_table)
        except Exception as e:
            print('From cs_main')
            print(e)

    @staticmethod
    def smooth(data, window):
        # a: 1-D array containing the data to be smoothed by sliding method
        # WSZ: smoothing window size
        if not isinstance(window, int):
            window = int(window)
        if np.mod(window, 2) == 0:
            window = window+1

        out0 = np.convolve(data, np.ones(window, dtype=int), 'valid') / window
        r = np.arange(1, window - 1, 2)
        start = np.cumsum(data[:window - 1])[::2] / r
        stop = (np.cumsum(data[:-window:-1])[::2] / r)[::-1]
        return np.concatenate((start, out0, stop))

    def veh_std_cal(self, i):
        return np.std(self.veh_spd[i:i + self.frequency * self.time_block])

    def gear_std_cal(self, i):
        return np.std(self.gear[i:i + self.frequency * self.time_block])

    def acc_smooth_rate_std_cal(self, i):
        return np.std(self.acc[i:i + self.frequency * self.time_block] -
                      self.acc_smo[i:i + self.frequency * self.time_block])

    def mean_speed_cal(self, i):
        return np.mean(self.veh_spd[i:i + self.frequency * self.time_block])

    def mean_ped_cal(self, i):
        return np.mean(self.pedal[i:i + self.frequency * self.time_block])

    def mean_acc_cal(self, i):
        return np.mean(self.acc[i:i + self.frequency * self.time_block])

    def mean_rpm_cal(self, i):
        return np.mean(self.en_spd[i:i + self.frequency * self.time_block])


if __name__ == '__main__':
    a = SystemGain('./IP31_L16UOV055_Ride_SyGa_20160225_SL.csv')
    a.sg_main()
    plt.show()

    print('Finish!')
