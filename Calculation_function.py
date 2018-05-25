# -*- coding: utf-8 -*-

from numpy import average, transpose, zeros, array, linspace, mean, cov, convolve, arange, cumsum, concatenate, abs, \
    mod, std, ones, diff , interp
from pandas import read_csv, read_excel, Timedelta ,DataFrame
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

    @staticmethod
    def search_feature(cols_to_search, feature):
        if not isinstance(cols_to_search, list):
            try:
                cols_to_search = cols_to_search.tolist()
            except AttributeError:
                return
        for i in feature:
            for j in cols_to_search:
                _match_result = match(i, j)
                try:
                    match_result = _match_result.group(0)
                    match_result_index = cols_to_search.index(match_result)
                    return match_result_index
                except AttributeError:
                    pass
        return 0   # 什么都没找到的时候返回0

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


class RealRoadFc(object):
    def __init__(self):
        pass

    def real_road_main(self):

        for i in range(target_driver_travel_date.shape[0]):  # 样本数据个数
            driver_id = target_driver_travel_date.iloc[i][0]
            travel_date = target_driver_travel_date.iloc[i][1]
            travel_id = target_driver_travel_date.iloc[i][2]
            target_driver = csvdata[(csvdata['Travel_ID'] == travel_id)]  # 筛出的样本集

            if target_driver.shape[0] > 1000:  # 太短的样本选择丢弃

                # target_driver = target_driver[1000:-1]   # 切掉冷启动的

                fuel_csump = target_driver['fuel_csump[uL/100ms]']
                # vspd = ((target_driver['WhlSpd_RR[kph]'] + target_driver['WhlSpd_RL[kph]']) / 2)
                vspd = target_driver['Vspd[kph]']
                strg_whl_ang = target_driver['strg_whl_ang']
                acc_ped = target_driver['Acc_Actu_Pos[%]']
                # time = target_driver['time[s]']

                x_acc = self.five_points_avg_acc(vspd.tolist(), frequency=10)
                # x_acc = target_driver['x_acc[m/s^2]']
                y_acc = target_driver['y_acc[m/s^2]']
                # x_acc = five_points_avg(x_acc.tolist())
                y_acc = self.five_points_avg(y_acc.tolist())

                # gen_load_toq = target_driver['gen_load_toq[Nm]']
                engine_toq = target_driver['engine_toq[Nm]']
                engine_spd = target_driver['En_Spd[rpm]']
                turbo_speed = target_driver['turbo_speed[rpm]']
                # TC_state = target_driver['TC_state']
                gen_load_toq = target_driver['gen_load_toq[Nm]']
                ac_toq_req = target_driver['ac_toq_req[Nm]'] * engine_spd / 9550  # kw

                target_driver['Delta_TC_speed[rpm]'] = engine_spd - turbo_speed
                target_driver['Veh_spd[kph]'] = vspd
                tc_run_data = target_driver[vspd > 1]
                tc_open_data = target_driver[(target_driver['TrRealGear'] > 0) &
                                             (abs(target_driver['Delta_TC_speed[rpm]']) > 200)]
                tc_close_data = tc_run_data[(tc_run_data['TrRealGear'] > 0) &
                                            (abs(tc_run_data['Delta_TC_speed[rpm]']) < 50)]
                # ------------------- Style features ---------------------
                odemeter = self.odometer_cal(vspd)
                fuel_cons = sum(fuel_csump) / odemeter * 100 / 1e6  # L/100km
                fuel_csump_run = target_driver[vspd > 0]['fuel_csump[uL/100ms]']
                fuel_cons_run = sum(fuel_csump_run) / odemeter * 100 / 1e6  # L/100km

                sudden_acc_times = self.sudden_acc(x_acc, vspd.tolist(), CarName)
                sudden_brake_times = self.sudden_brake(x_acc, CarName)
                sudden_steering_times = self.sudden_steering(y_acc.tolist(), CarName)
                tip_in_times = self.tip_in(acc_ped.tolist())

                # ----------------- Statistics features ------------------
                # soc_start = target_driver['BMSPackSOC'].tolist()[0]
                # soc_end = target_driver['BMSPackSOC'].tolist()[-1]
                # soc_balance_ratio = soc_balance_time_ratio(target_driver['BMSPackSOC'])
                mean_spd = vspd.mean()
                mean_spd_run = vspd[vspd > 0].mean()
                std_spd = vspd.std()
                mean_strg_whl_ang = strg_whl_ang.mean()
                std_strg_whl_ang = strg_whl_ang.std()
                mean_strg_whl_ang_pos = target_driver[target_driver['strg_whl_ang'] > 0].strg_whl_ang.mean()
                mean_strg_whl_ang_neg = target_driver[target_driver['strg_whl_ang'] < 0].strg_whl_ang.mean()
                mean_x_acc = x_acc.mean()
                std_x_acc = x_acc.std()
                mean_x_acc_pos = x_acc[x_acc > 0].mean()
                mean_x_acc_neg = x_acc[x_acc < 0].mean()
                mean_acc_ped = acc_ped.mean()
                std_acc_ped = acc_ped.std()
                idle_time = target_driver[(vspd == 0) & (engine_spd > 0)].shape[0] / 10
                run_time = target_driver[vspd > 0].shape[0] / 10
                total_time = target_driver.shape[0] / 10
                fuel_csump_idle = target_driver[(vspd == 0) & (engine_spd > 0)]['fuel_csump[uL/100ms]']
                fuel_cons_idle = 0.1 * sum(fuel_csump_idle) / idle_time / 100

                start_times = self.start_times_cal(vspd)

                print(driver_id, travel_date, travel_id, '....finish')

                sudden_acc_times = array(sudden_acc_times) / odemeter
                sudden_brake_times = array(sudden_brake_times) / odemeter
                sudden_steering_times = array(sudden_steering_times) / odemeter
                # ------------------- Plot Data --------------------------
                fuel_distri = self.spd_distribution_array(vspd, fuel_csump, type='sum')
                portion_distri = self.spd_distribution_array(vspd, vspd, type='weight')

                resultarray.append([driver_id, travel_date])
                backup_data.append([travel_id, sudden_acc_times[0], sudden_acc_times[1], sudden_acc_times[2],
                                    sudden_brake_times[0], sudden_brake_times[1], sudden_brake_times[2],
                                    sudden_steering_times[0], sudden_steering_times[1], sudden_steering_times[2],
                                    tip_in_times[0] / odemeter, odemeter, idle_time, fuel_cons_idle, run_time,
                                    total_time,
                                    start_times, mean_spd_run,
                                    mean_spd, mean_strg_whl_ang, mean_strg_whl_ang_pos, mean_strg_whl_ang_neg,
                                    mean_x_acc, mean_x_acc_pos, mean_x_acc_neg, mean_acc_ped,
                                    std_spd, std_strg_whl_ang, std_x_acc, std_acc_ped,
                                    fuel_cons, fuel_cons_run])

                docker1 = docker1.append(DataFrame([fuel_distri], columns=docker1.columns), ignore_index=True)
                docker2 = docker2.append(DataFrame([portion_distri], columns=docker2.columns), ignore_index=True)

                print(tc_run_data.shape[0], tc_close_data.shape[0])

                # heatmap_plot(target_driver[['En_Spd[rpm]', 'engine_toq[Nm]']], tc_open_data[['En_Spd[rpm]', 'engine_toq[Nm]']],
                #              driver_id, seg_size=[50, 50], xlim=5000, ylim=250)     # 发动机工作点热力图

                self.heatmap_plot(target_driver[['En_Spd[rpm]', 'engine_toq[Nm]']], target_driver, seg_size=[50, 50],
                                  xlim=5000, ylim=250)
                self.heatmap_plot_shift(target_driver[['Veh_spd[kph]', 'Acc_Actu_Pos[%]']], target_driver,
                                        seg_size=[50, 50], xlim=250, ylim=100)
        pass

    @staticmethod
    def find_3_level_times(series, base=0, a1=1, a2=2, a3=3, delta_t=20):  # Passed Test 20170526
        count_1 = count_2 = count_3 = 0
        up_1 = up_2 = up_3 = 0
        down_1 = down_2 = down_3 = 0
        l = len(series)
        for j in range(l - 1):
            if series[j] == base and series[j + 1] == a1:
                up_1 = j + 1
            if series[j] == a1 and series[j + 1] == a2:
                up_2 = j + 1
            if series[j] == a2 and series[j + 1] == a3:
                up_3 = j + 1
            if series[j] == a1 and series[j + 1] == base:
                down_1 = j + 1
            if series[j] == a2 and series[j + 1] == a1:
                down_2 = j + 1
            if series[j] == a3 and series[j + 1] == a2:
                down_3 = j + 1
            if series[j] > series[j + 1]:
                if down_3 - up_3 < delta_t <= down_2 - up_2:
                    count_2 = count_2 + 1
                    down_1 = down_2 = down_3 = -l * 2
                    up_1 = up_2 = up_3 = l * 2
                if down_3 - up_3 >= delta_t:
                    count_3 = count_3 + 1
                    down_1 = down_2 = down_3 = -l * 2
                    up_1 = up_2 = up_3 = l * 2
                if down_2 - up_2 < delta_t <= down_1 - up_1:
                    count_1 = count_1 + 1
                    down_1 = down_2 = down_3 = -l * 2
                    up_1 = up_2 = up_3 = l * 2
        return count_1, count_2, count_3

    @staticmethod
    def five_points_avg(series):
        l = len(series)
        avg_series = zeros(l)
        avg_series[0] = (series[1] + series[0]) / 2
        avg_series[1] = (series[2] + series[1] + series[0]) / 3
        for i in range(2, l - 2, 1):
            avg_series[i] = (series[i + 2] + series[i + 1] + series[i] + series[i - 1] + series[i - 2]) / 5
        avg_series[-2] = (series[-1] + series[-2] + series[-3]) / 3
        avg_series[-1] = (series[-1] + series[-2]) / 2
        return avg_series

    @staticmethod
    def five_points_avg_acc(series, g=9.8, frequency=10):
        l = len(series)
        avg_acc = zeros(l)
        avg_acc[0] = (series[1] - series[0]) * frequency / 3.6 / g
        avg_acc[1] = (series[2] - series[0]) * frequency / 2 / 3.6 / g
        for i in range(2, l - 2, 1):
            avg_acc[i] = (series[i + 2] - series[i - 2]) * frequency / 4 / 3.6 / g
        avg_acc[-2] = (series[-1] - series[-3]) * frequency / 2 / 3.6 / g
        avg_acc[-1] = (series[-1] - series[-2]) * frequency / 3.6 / g
        return avg_acc

    @staticmethod
    def fuel_cal(series, buffer_size=65535):
        l = len(series)
        fuel_count = 0
        bug_fc = []
        for i in range(1, l, 1):
            if (series[i] - series[i - 1]) < 0:
                if series[i - 1] > (buffer_size - 500):
                    fuel_count = fuel_count + 1
                else:
                    bug_fc.append(series[i - 1])
        fuel_sum = fuel_count * buffer_size + series[-1] - series[0] + sum(bug_fc)
        return fuel_sum / 1e6  # unit L

    @staticmethod
    def signal_times_cal(series):  # 数上升沿个数  Passed Test
        l = len(series)
        times_counter = 0
        for i in range(1, l, 1):
            if (not series[i - 1]) and series[i]:
                times_counter = times_counter + 1
            else:
                continue
        return

    # ----------------------  Calculation functions  --------------------------
    @staticmethod
    def odometer_cal(vspd, frequency=10):
        odometer = sum(vspd) / frequency / 3.6 / 1000  # km
        return odometer

    def sudden_brake(self, series, car_type='ZS11'):
        style_brk = {'ZS11': [-0.5, -0.35, -0.1],
                     'AS24': [-0.5, -0.35, -0.15],
                     'N330': [-0.5, -0.35, -0.15]}
        l = len(series)
        brk_lab = zeros(l)
        for i in range(l):
            if series[i] < style_brk[car_type][0]:
                brk_lab[i] = 3
            elif style_brk[car_type][0] < series[i] < style_brk[car_type][1]:
                brk_lab[i] = 2
            elif style_brk[car_type][1] < series[i] < style_brk[car_type][2]:
                brk_lab[i] = 1
        brk_times = self.find_3_level_times(brk_lab)
        return brk_times

    def sudden_acc(self, series_xacc, series_vspd, car_type='ZS11'):
        style_acc = {'ZS11': [0.04, 0.31, 0.36, 0.35, 0.22, 0.23, 0.16, 0.12, 0.08],
                     'AS24': [0.2, 0.38, 0.41, 0.41, 0.39, 0.43, 0.36, 0.30, 0.22],
                     'N330': [0.2, 0.38, 0.41, 0.41, 0.39, 0.43, 0.36, 0.30, 0.22]}
        vspd_interp = [0, 10, 20, 30, 40, 60, 80, 100, 120]
        l = len(series_xacc)
        acc_lab = zeros(l)
        style_acc_current = array(style_acc[car_type])
        for i in range(l):
            if series_xacc[i] > interp(series_vspd[i], vspd_interp, 0.5 * style_acc_current):
                acc_lab[i] = 3
            elif interp(series_vspd[i], vspd_interp, 0.3 * style_acc_current) < series_xacc[i] < \
                    interp(series_vspd[i], vspd_interp, 0.5 * style_acc_current):
                acc_lab[i] = 2
            elif interp(series_vspd[i], vspd_interp, 0.15 * style_acc_current) < series_xacc[i] < \
                    interp(series_vspd[i], vspd_interp, 0.3 * style_acc_current):
                acc_lab[i] = 1
        acc_times = self.find_3_level_times(acc_lab)
        return acc_times
    
    def sudden_steering(self, series, car_type='ZS11'):
        style_steer = {'ZS11': [0.35, 0.2, 0.1],
                       'AS24': [0.35, 0.2, 0.15],
                       'N330': [0.35, 0.2, 0.15]}
        l = len(series)
        str_lab = zeros(l)
        for i in range(l):
            if series[i] > style_steer[car_type][0]:
                str_lab[i] = 3
            elif style_steer[car_type][0] > series[i] > style_steer[car_type][1]:
                str_lab[i] = 2
            elif style_steer[car_type][1] > series[i] > style_steer[car_type][2]:
                str_lab[i] = 1
        str_times = self.find_3_level_times(str_lab)
        return str_times

    @staticmethod
    def brake_skill(series_xacc, v_spd):
        l = len(v_spd)
        vel_spd_lab = zeros(l)
        brake_skill_cal = []
        for i in range(l):
            if not v_spd[i]:
                vel_spd_lab[i] = 1

        for i in range(15, l - 1, 1):  # 防止max_acc出错
            if not vel_spd_lab[i] and vel_spd_lab[i + 1]:
                max_acc = max(series_xacc[i - 15:i])
                I = series_xacc[i - 15:i].index(max_acc)
                # I = np.where(series_xacc[i - 15:i] == max_acc)
                start_ = I + i - 15 - 1
                for j in range(start_, start_ + 5, 1):
                    if series_xacc[j] > series_xacc[j + 1] and series_xacc[j + 1] <= series_xacc[j + 2]:
                        min_acc = series_xacc[j + 1]
                        brake_skill_cal = concatenate((brake_skill_cal, [max_acc - min_acc]))
                        break

        return array(brake_skill_cal).mean()

    @staticmethod
    def tip_in(series_acc_ped, frequency=10):
        l = len(series_acc_ped)
        delta_acc_ped = []
        result_array = []
        for i in range(1, l, 1):
            delta_acc_ped.append(series_acc_ped[i] - series_acc_ped[i - 1])
        delta_accped = array(delta_acc_ped) * frequency
        tip_in_times = 0
        for i in range(1, l - 5, 1):
            sum_of_acc = 0
            if delta_acc_ped[i] > 0 and delta_acc_ped[i - 1] <= 0:
                sum_of_acc = delta_accped[i]
                j = i + 1
                while delta_acc_ped[j] > 0 and delta_acc_ped[j + 3] >= 0 and j < l - 5:
                    sum_of_acc = sum_of_acc + delta_acc_ped[j]
                    j = j + 1
                if sum_of_acc / (j - i) > 80 and series_acc_ped[j - 1] > 10:
                    tip_in_times = tip_in_times + 1
                    result_array.append([series_acc_ped[i], series_acc_ped[j], (j - i) / frequency])
        return tip_in_times, result_array

    @staticmethod
    def soc_balance_time_ratio(series_soc_df, balance_position=33):
        time_ratio = series_soc_df[series_soc_df < balance_position].shape[0] / series_soc_df.shape[0]
        return time_ratio

    @staticmethod
    def spd_distribution_array(vspd, input_series, cal_type='sum'):
        output_array = []
        for i in range(1, 13, 1):
            if cal_type == 'sum':
                output_array.append(sum(input_series[(vspd < (i * 10)) & (vspd > ((i - 1) * 10))]))
            elif cal_type == 'avg':
                output_array.append(input_series[(vspd < (i * 10)) & (vspd > ((i - 1) * 10))].mean())
            elif cal_type == 'weight':
                output_array.append(input_series[(vspd < (i * 10)) & (vspd > ((i - 1) * 10))].size / input_series.size)

        return output_array

    @staticmethod
    def start_times_cal(vspd):
        start_times = 0
        l = vspd.shape[0]
        for i in range(1, l - 1):
            if vspd.iloc[i] == 0 and vspd.iloc[i + 1] > 0:
                start_times = start_times + 1
        return start_times


if __name__ == '__main__':
    a = SystemGain('./IP31_L16UOV055_Ride_SyGa_20160225_SL.csv')
    a.sg_main()
    plt.show()

    print('Finish!')
