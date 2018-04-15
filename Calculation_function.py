# -*- coding: utf-8 -*-

from numpy import average, transpose, zeros, array, linspace, mean, cov, convolve, arange, cumsum, concatenate, abs, \
    mod, std, ones, diff
from pandas import read_csv, read_excel, Timedelta
from scipy import interpolate
import matplotlib.pyplot as plt
from re import match
from pickle import dump, load
from mdfreader import mdfreader
from pptx import Presentation
from pptx.util import Inches
from datetime import date


class SystemGain(object):
    """
    Main class of system gain, contains all the thing needed to be calculated or plotted.

    Created By Lvhuijia 20180202
    Edited By Luchao 20180204
    Edited By ShenLiang 20180313

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
    ****** SL
    Add constSpd IN class AccResponse————Wrapper class of the corresponding fig
    Add MaxAcc and conSpd in plot_acc_response_
    ******
    """

    def __init__(self, raw_data, feature_array, pt_type, frequency=20,
                 data_cut_time_of_creep=20, data_cut_time_of_pedal=20,
                 **kwargs):
        """
        Initial function of system gain.

        :param
        """
        self.raw_data = raw_data
        self.feature_array = feature_array
        self.pt_type = pt_type
        self.sysGain_class = {}
        self.frequency = frequency
        self.data_cut_time_of_creep = data_cut_time_of_creep
        self.data_cut_time_of_pedal = data_cut_time_of_pedal
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
        self.SG_csv_Data_ful = self.raw_data
        # *******2-GetSGColumn*********
        # 获取列号，标准变量及面板输入，数据预处理
        self.SG_csv_Data_Selc = self.SG_csv_Data_ful.loc[:, self.feature_array]
        # SG_csv_Data = SG_csv_Data_Selc.drop_duplicates()    # 先不去重
        SG_csv_Data = self.SG_csv_Data_Selc  # 选到重复的会报错 ！！！！！所以修改了以下索引格式
        self.time_Data = SG_csv_Data.iloc[:, 0].tolist()
        self.vehSpd_Data = SG_csv_Data.iloc[:, 1].tolist()
        self.pedal_Data = SG_csv_Data.iloc[:, 2].tolist()
        self.acc_Data = SG_csv_Data.iloc[:, 3].tolist()
        self.gear_Data = SG_csv_Data.iloc[:, 4].tolist()
        self.torq_Data = SG_csv_Data.iloc[:, 5].tolist()
        self.fuel_Data = SG_csv_Data.iloc[:, 6].tolist()
        self.enSpd_Data = SG_csv_Data.iloc[:, 7].tolist()
        self.turbSpd_Data = SG_csv_Data.iloc[:, 8].tolist()

        self.colour_Bar = ['orange', 'lightgreen', 'c', 'royalblue', 'lightcoral', 'yellow', 'red', 'brown',
                           'teal', 'blue', 'coral', 'gold', 'lime', 'olive']
        # 数据检查
        if isinstance(self.time_Data[0], int) or isinstance(self.time_Data[0], float):  # 如果时间序列为数字格式
            if sum([int(i <= 0) for i in diff(self.time_Data)]) > 0:   # 如果时间序列是非严格递增的，替换为人工生成的序列
                self.time_Data = arange(0, len(self.time_Data)/self.frequency, 1/self.frequency)
        else:  # 如果时间序列为非数字格式
            self.time_Data = arange(0, len(self.time_Data) / self.frequency, 1 / self.frequency)

        if not isinstance(self.gear_Data[0], int):  # 如果gear不是int类型的，尝试转换
            try:
                self.gear_Data = [int(i) for i in self.gear_Data]
            except ValueError:
                pass

        self.acc_offset = ((self.vehSpd_Data[-1] - self.vehSpd_Data[0]) / 3.6 / (self.time_Data[-1] - self.time_Data[0])
                           - average(self.acc_Data[:]) * 9.8) / 9.8
        self.acc_Data = [x + self.acc_offset for x in self.acc_Data]

        self.pedal_cut_index, self.pedal_avg = self.cut_sg_data_pedal(self.pedal_Data, self.vehSpd_Data, self.frequency,
                                                                      self.data_cut_time_of_creep,
                                                                      self.data_cut_time_of_pedal)

        # last_item = -10
        # trigger = False
        # for item in self.pedal_avg:
        #     if abs(last_item - item) < 3:
        #         trigger = True
        #     last_item = item

        trigger = False
        for i, item in enumerate(self.pedal_avg):
            for j, item_ in enumerate(self.pedal_avg):
                if i != j and abs(item-item_) < 3:
                    trigger = True
                    break

        if trigger:  # 挂起线程，等待eliminate_duplicate_ped()被触发
            return 'eliminate_duplicate_ped'
        else:
            self.sg_obj_cal()

    def eliminate_duplicate_ped(self, remove_ped_list):
        ped_h_index = []
        ped_t_index = []
        ped_re = []
        for i, checked in enumerate(remove_ped_list):
            if not checked:
                ped_h_index.append(self.pedal_cut_index[0][i])
                ped_t_index.append(self.pedal_cut_index[1][i])
                ped_re.append(self.pedal_avg[i])
        self.pedal_cut_index = [ped_h_index, ped_t_index]
        self.pedal_avg = ped_re
        self.sg_obj_cal()

    def sg_obj_cal(self):

        self.sort_ped()

        obj_Launch = self.launch(self.acc_Data, self.pedal_Data, self.pedal_cut_index, self.pedal_avg)

        obj_MaxAcc = self.max_acc(self.acc_Data, self.pedal_cut_index, self.pedal_avg)

        obj_PedalMap = self.pedal_map(self.pedal_Data, self.enSpd_Data, self.torq_Data, self.pedal_cut_index,
                                      self.pedal_avg, self.colour_Bar)

        obj_ShiftMap = self.shift_map(self.pedal_Data, self.gear_Data, self.vehSpd_Data, self.pedal_cut_index,
                                      self.pedal_avg, self.colour_Bar,
                                      self.enSpd_Data, self.turbSpd_Data, kind=self.pt_type)
        # # 加速响应曲面增加加速度线及稳车速线
        obj_AccResponse = self.acc_response(self.vehSpd_Data, self.acc_Data, self.pedal_cut_index, self.pedal_avg)

        obj_SystemGain = self.systemgain_curve(self.pedal_Data, self.vehSpd_Data, self.acc_Data, self.pedal_cut_index,
                                               self.pedal_avg)
        self.sysGain_class = self.SystemGainDocker(self.pt_type, obj_AccResponse, obj_Launch, obj_MaxAcc, obj_PedalMap,
                                                   obj_ShiftMap, self.SG_csv_Data_ful, obj_SystemGain)
        return

    def acc_response(self, vehspd_data, acc_data, pedal_cut_index, pedal_avg):
        try:
            acc_ped_map = [[], [], []]
            ped_maxacc = [[], [], []]
            for i in range(0, len(pedal_avg)):
                ivehspd = vehspd_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]
                iped = [pedal_avg[i] * ix / ix for ix in range(pedal_cut_index[0][i], pedal_cut_index[1][i])]
                iacc = acc_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]

                # 删除加速度小于0.05g的数据，认为是踩了制动
                data_len = len(iacc)
                j = 0
                while j < data_len:
                    if iacc[j] < 0.0:  # 20180211 0.05->0.0
                        del ivehspd[j]
                        del iped[j]
                        del iacc[j]
                        data_len = data_len - 1
                        j = j - 1
                    j = j + 1

                acc_ped_map[0].append(iped)
                acc_ped_map[1].append(ivehspd)
                acc_ped_map[2].append(iacc)

                ped_maxacc[0].append(pedal_avg[i])
                ped_maxacc[1].append(ivehspd[iacc.index(max(iacc))])
                ped_maxacc[2].append(max(iacc))

            obj = self.AccResponse(acc_ped_map, pedal_avg, ped_maxacc)
        except Exception:
            acc_ped_map = [[], [], []]
            ped_maxacc = [[], [], []]
            print('Error From acc_response Cal!')
            obj = self.AccResponse(acc_ped_map, pedal_avg, ped_maxacc)
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
                shiftMap_Sort = sorted(transpose(shiftMap), key=lambda x: [x[0], x[1], x[2]])
                shiftMap_Data = transpose(shiftMap_Sort)
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
                    cs_vspd[0] = vehspd_sg_for_inter[0]  # 怠速车速
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

            points_for_inter = zeros((len(acc), 2))
            points_for_inter[:, 0] = vehspd
            points_for_inter[:, 1] = ped
            points_for_inter[:, 1] = points_for_inter[:, 1] / 100 * 51
            acc_for_inter = array(acc)

            pedal_steady_for_inter = [x / 100 * 51 + 12.7 for x in pedal_avg]
            vehspd_steady_tb_inter = linspace(min(vehspd_steady_for_inter), 120, 200)
            pedal_steady_function = interpolate.interp1d(vehspd_steady_for_inter, pedal_steady_for_inter)
            pedal_steady_tb_inter = pedal_steady_function(vehspd_steady_tb_inter)
            points_tb_inter = zeros((len(pedal_steady_tb_inter), 2))
            points_tb_inter[:, 0] = vehspd_steady_tb_inter
            points_tb_inter[:, 1] = pedal_steady_tb_inter

            '# steady velocity & pedal checked: same with matlab'
            # savetxt('vehspd_steady_for_inter.csv', vehspd_steady_for_inter, delimiter=',')
            # savetxt('pedal_steady_for_inter.csv', pedal_steady_for_inter, delimiter=',')
            # savetxt('pedal_steady_tb_inter.csv', pedal_steady_tb_inter, delimiter=',')
            # savetxt('vehspd_steady_tb_inter.csv', vehspd_steady_tb_inter, delimiter=',')

            grid_z1 = interpolate.griddata(points_for_inter, acc_for_inter, points_tb_inter, method='linear')
            grid_z1 = grid_z1 / 12.7
            grid_z1 = self.smooth(grid_z1, 5)

            '#  function "griddata" checked: same with matlab'
            # savetxt('points_for_inter.csv', points_for_inter, delimiter=',')
            # savetxt('acc_for_inter.csv', acc_for_inter, delimiter=',')
            # savetxt('points_tb_inter.csv', points_tb_inter, delimiter=',')
            # savetxt('grid_z1.csv', points_tb_inter, delimiter=',')

            # obj = SystemGainPlot()
            obj = self.SystemGainCurve(vehspd_steady_tb_inter, grid_z1, vehspd_steady_for_inter, pedal_avg)
        except Exception:
            obj = self.SystemGainCurve([], [], [], [])
            print('Error From systemgain_curve Cal!')
        return obj

    @staticmethod
    def cut_sg_data_pedal(pedal_data, vehspd_data, frequency, data_cut_time_of_creep=20, data_cut_time_of_pedal=20):
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
            if (t_edge_vehspd[j] - r_edge_vehspd[j] > frequency*data_cut_time_of_creep) and (
                3.5 < average(vehspd_data[r_edge_vehspd[j] + int(frequency*data_cut_time_of_creep/2):t_edge_vehspd[j] -
                            int(frequency*data_cut_time_of_creep/2)]) < 8.5) and (
                        average(pedal_data[r_edge_vehspd[j]:t_edge_vehspd[j]]) < 0.01):
                pedal_cut_index[0].append(r_edge_vehspd[j] - frequency*2)  # 车速信号相对于加速度信号有迟滞
                pedal_cut_index[1].append(t_edge_vehspd[j] - frequency*2)
                pedal_avg.append(mean(pedal_data[r_edge_vehspd[j]:t_edge_vehspd[j]]))

        for j in range(0, len(r_edge_pedal)):
            if t_edge_pedal[j] - r_edge_pedal[j] > frequency*data_cut_time_of_pedal:  # 时间长度
                if cov(pedal_data[r_edge_pedal[j] + frequency*1:t_edge_pedal[j] - frequency*1]) < 3:
                    pedal_cut_index[0].append(r_edge_pedal[j])
                    pedal_cut_index[1].append(t_edge_pedal[j])
                    pedal_avg.append(mean(pedal_data[r_edge_pedal[j]:t_edge_pedal[j]]))

        return pedal_cut_index, pedal_avg

    def sort_ped(self):
        ped_h_index = []
        ped_t_index = []
        origin_ped = self.pedal_avg.copy()  # 浅拷贝
        self.pedal_avg.sort()
        for item in self.pedal_avg:
            ped_h_index.append(self.pedal_cut_index[0][origin_ped.index(item)])
            ped_t_index.append(self.pedal_cut_index[1][origin_ped.index(item)])
        self.pedal_cut_index = [ped_h_index, ped_t_index]

    class AccResponse:
        def __init__(self, matrix, para1, matrix_max_acc):
            self.xdata = matrix[1]
            self.ydata = matrix[0]
            self.zdata = matrix[2]
            self.data = matrix
            self.pedal_avg = para1
            self.max_acc_ped = matrix_max_acc
            # self.ped_const = pedal_const
            # self.velo_const = velocity_const

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
        out0 = convolve(data, ones(window, dtype=int), 'valid') / window
        r = arange(1, window - 1, 2)
        start = cumsum(data[:window - 1])[::2] / r
        stop = (cumsum(data[:-window:-1])[::2] / r)[::-1]
        return concatenate((start, out0, stop))


class ReadFile(object):

    def __init__(self, file_path, resample_rate):
        """
        Initial function of Read File.

        :param file_path: path of system gain file in local disc
        """
        self.file_path = file_path
        self.resample_rate = 1/int(resample_rate)
        self.file_columns_orig = []
        self.file_columns = []
        self.csv_data_ful = []
        self.mdf_data = []
        try:
            self.start_read()
        except AttributeError as e:
            print(e)

    def start_read(self):
        file_type_match = match(r'^(.+)(\.)(\w*)$', self.file_path)
        file_type = file_type_match.group(3)
        file_type = file_type.lower()  # 小写
        if file_type == 'csv':
            try:
                self.csv_data_ful = read_csv(self.file_path, low_memory=False)  # utf-8默认编码
            except UnicodeDecodeError:
                self.csv_data_ful = read_csv(self.file_path, encoding='gb18030')  # gb18030中文编码
        elif file_type == 'xls' or file_type == 'xlsx':
            self.csv_data_ful = read_excel(self.file_path)
        elif file_type == 'mdf' or file_type == 'dat':
            self.mdf_data = mdfreader.mdf(self.file_path)
            self.mdf_data.convertToPandas(self.resample_rate)
            data_ful = self.mdf_data['master_group']
            data_ful['time'] = (data_ful.index-data_ful.index[0]).astype('timedelta64[ms]')/1000
            self.csv_data_ful = data_ful

        self.file_columns_orig = self.csv_data_ful.columns
        back_up_counter = 0
        for i in self.csv_data_ful.columns:  # 去除'[]'号，防止控件命名问题
            try:
                ma = match(r'^([0-9a-zA-Z/:_.%\u4e00-\u9fa5\-]+)(\[?)([0-9a-zA-Z/:_.%\u4e00-\u9fa5\[\]\-]*)$', i)
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
        dump(store_data, output_file)
        output_file.close()
        return

    @staticmethod
    def store_result_in_excel(file_path, store_data):
        # output_file = open(file_path, 'wb')
        # dump(store_data, output_file)
        # output_file.close()
        return

    @staticmethod
    def reload_result(file_path_list):
        data_reload = []
        for i in file_path_list:
            input_file = open(i, 'rb')
            data_reload.append(load(input_file))
            input_file.close()
        return data_reload

    @staticmethod
    def store_feature_index(store_index):
        output_file = open('./bin/feature_index.pkl', 'wb')
        dump(store_index, output_file)
        output_file.close()
        return

    @staticmethod
    def reload_feature_index():
        input_file = open('./bin/feature_index.pkl', 'rb')
        data_reload = load(input_file)
        input_file.close()
        return data_reload

    # PPT
    @staticmethod
    def get_fig_name(type, rawdata_filepath):
        if type == "initial_ppt":
            list_figs = [['dr_sg_curve', 'System Gain Curve.png'], ['dr_max_acc', 'Max Acc.png'],
                         ['dr_cons_spd', 'Constant Speed.png'], ['dr_acc_curve', 'Acc Response.png'],
                         ['dr_launch', 'Launch.png'], ['dr_shift_map', 'Shift Map.png'],
                         ['dr_pedal_map', 'PedalMap.png']]
            rawdata_name = rawdata_filepath.split("/")[-1].split(".")[0]
            title_ppt = "Drive Quality Report"
        else:
            # type == "analysis_ppt"
            list_figs = [['dr_history_sg_curve', 'System Gain Curve.png'], ['dr_history_max_acc', 'Max Acc.png'],
                         ['dr_history_cons_spd', 'Constant Speed.png'], ['dr_history_acc_curve', 'Acc Response.png'],
                         ['dr_history_launch', 'Launch.png'], ['dr_history_shift_map', 'Shift Map.png'],
                         ['dr_history_pedal_map', 'PedalMap.png']]
            rawdata_name = ""
            title_ppt = "Drive Quality Compare Result"
        return list_figs, rawdata_name, title_ppt

        # PPT

    @staticmethod
    def save_pic_ppt(list_figs, rawdata_name, title_ppt, pic_path):
        # Input PowerPoint Template，default blank。
        try:
            prs = Presentation("SAIC_Temp.pptx")
        except Exception:
            prs = Presentation()

        date_pos = [5, 6.9, 3, 0.4]
        pic_pos = [1.95, 1.2, 5.7, 5.0]
        title_pos = [4, 6.15, 3, 0.3]
        data_pos = [4.8, 6.85, 3, 0.5]

        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        title = slide.shapes.title
        subtitle = slide.placeholders[1]
        title.text = title_ppt
        title.text_frame.paragraphs[0].font.size = Inches(0.6)
        subtitle.text = 'Data: ' + rawdata_name

        textbox = slide.shapes.add_textbox(Inches(date_pos[0]), Inches(date_pos[1]),
                                           Inches(date_pos[2]), Inches(date_pos[3]))
        textbox.text = "Generated on {:%Y-%m-%d}".format(date.today())

        try:
            for i in range(0, len(list_figs)):
                pic_name = list_figs[i][1].split(".")[0]
                graph_slide_layout = prs.slide_layouts[6]
                slide = prs.slides.add_slide(graph_slide_layout)
                textbox = slide.shapes.add_textbox(Inches(title_pos[0]), Inches(title_pos[1]),
                                                   Inches(title_pos[2]), Inches(title_pos[3]))
                textbox.text = pic_name
                if i > 2 and title_ppt == "Drive Quality Compare Result":
                    pic_pos = [0.12, 1.5, 9.7, 4.4]

                pic = slide.shapes.add_picture(pic_path + pic_name + '.png', Inches(pic_pos[0]),
                                               Inches(pic_pos[1]), Inches(pic_pos[2]), Inches(pic_pos[3]))
                # pic = placeholder.insert_picture(chart[i])
                textbox = slide.shapes.add_textbox(Inches(data_pos[0]), Inches(data_pos[1]),
                                                   Inches(data_pos[2]), Inches(data_pos[3]))
                textbox.text = rawdata_name
                textbox.text_frame.paragraphs[0].font.size = Inches(0.14)
            # Add the end of PPT
            end_slide_layout = prs.slide_layouts[6]
            slide = prs.slides.add_slide(end_slide_layout)
            textbox = slide.shapes.add_textbox(Inches(title_pos[0]-0.8), Inches(title_pos[1]-3),
                                               Inches(title_pos[2]), Inches(title_pos[3]))
            textbox.text = "Thank You"

            textbox.text_frame.paragraphs[0].font.size = Inches(0.8)
            textbox.text_frame.paragraphs[0].font.bold = True
        except FileNotFoundError as err:
            print('From save_pic_ppt')
            print(err)
        return prs


class ConstantSpeed(object):
    def __init__(self, raw_data, feature_list, frequency=20, time_block=15):
        self.raw_data = raw_data
        self.feature_list = feature_list
        self.frequency = frequency
        self.time_block = time_block

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
                    elif self.veh_std_cal(i) < self.cs_table[k][7] and abs(
                                    self.mean_speed_cal(i) - self.cs_table[k][1]) < 5:
                        self.cs_table[k] = [i,
                                            self.mean_speed_cal(i),
                                            self.mean_ped_cal(i),
                                            self.mean_acc_cal(i),
                                            self.acc_smooth_rate_std_cal(i),
                                            self.mean_rpm_cal(i),
                                            self.gear[i],
                                            self.veh_std_cal(i)]
                    elif abs(self.mean_speed_cal(i) - self.cs_table[k][1]) >= 5:
                        k = k + 1
                        self.cs_table.append([i,
                                              self.mean_speed_cal(i),
                                              self.mean_ped_cal(i),
                                              self.mean_acc_cal(i),
                                              self.acc_smooth_rate_std_cal(i),
                                              self.mean_rpm_cal(i),
                                              self.gear[i],
                                              self.veh_std_cal(i)])
            self.cs_table = array(self.cs_table)
        except Exception as e:
            print('From cs_main')
            print(e)

    @staticmethod
    def smooth(data, window):
        # a: 1-D array containing the data to be smoothed by sliding method
        # WSZ: smoothing window size
        if not isinstance(window, int):
            window = int(window)
        if mod(window, 2) == 0:
            window = window + 1

        out0 = convolve(data, ones(window, dtype=int), 'valid') / window
        r = arange(1, window - 1, 2)
        start = cumsum(data[:window - 1])[::2] / r
        stop = (cumsum(data[:-window:-1])[::2] / r)[::-1]
        return concatenate((start, out0, stop))

    def veh_std_cal(self, i):
        return std(self.veh_spd[i:i + self.frequency * self.time_block])

    def gear_std_cal(self, i):
        return std(self.gear[i:i + self.frequency * self.time_block])

    def acc_smooth_rate_std_cal(self, i):
        return std(self.acc[i:i + self.frequency * self.time_block] -
                   self.acc_smo[i:i + self.frequency * self.time_block])

    def mean_speed_cal(self, i):
        return mean(self.veh_spd[i:i + self.frequency * self.time_block])

    def mean_ped_cal(self, i):
        return mean(self.pedal[i:i + self.frequency * self.time_block])

    def mean_acc_cal(self, i):
        return mean(self.acc[i:i + self.frequency * self.time_block])

    def mean_rpm_cal(self, i):
        return mean(self.en_spd[i:i + self.frequency * self.time_block])


if __name__ == '__main__':
    a = SystemGain('./IP31_L16UOV055_Ride_SyGa_20160225_SL.csv')
    a.sg_main()
    plt.show()

    print('Finish!')
