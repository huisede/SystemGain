# -*- coding: utf8 -*-
# THIS IS IN BRANCH "READANDLOAD"!
import glob
import xlrd
import csv
import numpy as np
import scipy as sp
import re
import pandas as pd
import warnings
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.cm as cm
from scipy import interpolate


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import matplotlib
matplotlib.use("Qt5Agg")

warnings.filterwarnings("ignore")
# ----------------------------
# class definition


class SystemGain(object):
    pass


class SystemGainDocker:
    def __init__(self, accresponce, launch, maxacc, pedalmap, shiftmap):
        self.accresponce = accresponce
        self.launch = launch
        self.maxacc = maxacc
        self.pedalmap = pedalmap
        self.shiftmap = shiftmap


class MyFigureCanvas(FigureCanvas):

    def __init__(self, parent=None, width=10, height=10, dpi=100, plot_type='3d', data=[], para1=[]):
        fig = Figure(figsize=(width, height), dpi=100)
        super(MyFigureCanvas, self).__init__(fig)
        self.data = data
        self.parameter1 = para1
        # FigureCanvas.__init__(self, fig)  # 初始化父类   堆栈溢出问题！
        # self.setParent(parent)
        if plot_type == '2d':
            self.axes = fig.add_subplot(111)
        elif plot_type == '3d':
            self.axes = fig.add_subplot(111, projection='3d')

    def plot_acc_response_(self):
        self.xdata = self.data[1]
        self.ydata = self.data[0]
        self.zdata = self.data[2]
        self.pedal_avg = self.parameter1
        for i in range(0, len(self.xdata)):
            self.axes.plot(self.xdata[i], self.ydata[i], self.zdata[i], label=int(round(self.pedal_avg[i] / 5) * 5))
            self.axes.legend(bbox_to_anchor=(1.02, 1), loc=1, borderaxespad=0)
        self.axes.set_xlabel('Vehicle Speed (km/h)', fontsize=12)
        self.axes.set_ylabel('Pedal(%)', fontsize=12)
        self.axes.set_zlabel('Acc (g)', fontsize=12)
        self.axes.set_title('Acc-3D Map', fontsize=12)

    def plot_launch_(self):
        self.xdata = self.data[2]
        self.ydata = self.data[1]
        self.pedal = self.data[0]
        for i in range(0, len(self.xdata)):
            self.axes.plot(self.xdata[i], self.ydata[i], label=int(round(np.mean(self.pedal[i]) / 5) * 5))
            self.axes.legend()
        self.axes.grid(True, linestyle="--", color="k", linewidth="0.4")
        self.axes.set_xlabel('Time (s)', fontsize=12)
        self.axes.set_ylabel('Acc (g)', fontsize=12)
        self.axes.set_title('Launch', fontsize=12)

    def plot_max_acc_(self):
        colormap = ['green', 'blue', 'red', 'green', 'blue', 'red']
        colorindex = 0
        for key, item in self.data.items():
            colorselected = colormap[colorindex]
            self.xdata = item.xdata
            self.ydata = item.ydata
            self.axes.plot(self.xdata, self.ydata, color=colorselected, linestyle='dashed', marker='o', markerfacecolor=colorselected,
                           markersize=8)
            self.axes.grid(True, linestyle="--", color="k", linewidth="0.4")
            self.axes.legend()
            self.axes.set_xlabel('Pedal (%)', fontsize=12)
            self.axes.set_ylabel('Acc (g)', fontsize=12)
            self.axes.set_title('Acc-Pedal', fontsize=12)
            colorindex = colorindex+1

    def plot_pedal_map_(self):
        self.xdata = self.data[1]
        self.ydata = self.data[2]
        self.zdata = self.data[0]
        self.axes.scatter(self.xdata, self.ydata, c=self.zdata, marker='o', linewidths=0.1,
                          s=6, cmap=cm.get_cmap('RdYlBu_r'))
        self.axes.grid(True, linestyle="--", color="k", linewidth="0.4")
        self.axes.set_xlabel('Engine Speed (rpm)', fontsize=12)
        self.axes.set_ylabel('Torque (Nm)', fontsize=12)
        self.axes.set_title('PedalMap', fontsize=12)


    def test(self):
        x = [1, 2, 3]
        y = [2, 3, 5]
        z = [2, 1, 4]
        self.axes.scatter(x, y, z)


class AccResponse(FigureCanvas):
    def __init__(self, matrix, para1, parent=None, width=10, height=10, dpi=100, plot_type='3d'):
        self.fig = Figure(figsize=(width, height), dpi=100)
        super(AccResponse, self).__init__(self.fig)
        self.xdata = matrix[1]
        self.ydata = matrix[0]
        self.zdata = matrix[2]
        self.data = matrix
        self.pedal_avg = para1
        self.plot_type = plot_type

    def plot_acc_response(self):
        if self.plot_type == '2d':
            self.axes = self.fig.add_subplot(111)
        elif self.plot_type == '3d':
            self.axes = self.fig.add_subplot(111, projection='3d')
        for i in range(0, len(self.xdata)):
            self.axes.plot(self.xdata[i], self.ydata[i], self.zdata[i], label=int(round(self.pedal_avg[i] / 5) * 5))
            self.axes.legend()


class Launch(SystemGain):
    def __init__(self, matrix):
        self.xdata = matrix[2]
        self.ydata = matrix[1]
        self.pedal = matrix[0]
        self.data = matrix
        # dlg.name = self.__class__.__name__


    def plot_launch(self):
        fig2 = plt.figure()
        ax2 = fig2.add_subplot(111)
        for i in range(0, len(self.xdata)):
            ax2.plot(self.xdata[i], self.ydata[i], label=int(round(np.mean(self.pedal[i]) / 5) * 5))
            ax2.legend()
        ax2.grid(True, linestyle="--", color="k", linewidth="0.4")
        axg2 = plt.gca()
        axg2.set_xlabel('Time (s)', fontsize=12)
        axg2.set_ylabel('Acc (g)', fontsize=12)
        axg2.set_title('Launch', fontsize=12)


class MaxAcc(SystemGain):
    def __init__(self, x, y):
        self.xdata = x
        self.ydata = y


    def plot_maxacc(self):
        fig3 = plt.figure()
        ax3 = fig3.add_subplot(111)
        ax3.plot(self.xdata, self.ydata, color='green', linestyle='dashed', marker='o', markerfacecolor='blue',
                 markersize=8)
        ax3.grid(True, linestyle="--", color="k", linewidth="0.4")
        ax3.legend()
        axg3 = plt.gca()
        axg3.set_xlabel('Pedal (%)', fontsize=12)
        axg3.set_ylabel('Acc (g)', fontsize=12)
        axg3.set_title('Acc-Pedal', fontsize=12)


class PedalMap(SystemGain):
    def __init__(self, matrix):
        self.xdata = matrix[1]
        self.ydata = matrix[2]
        self.zdata = matrix[0]
        self.data = matrix

    def plot_pedal_map(self):
        fig4 = plt.figure()
        ax4 = fig4.add_subplot(111)
        ax4.legend()
        fig_pedalmap = ax4.scatter(self.xdata, self.ydata, c=self.zdata, marker='o', linewidths=0.1,
                                   s=6, cmap=plt.cm.get_cmap('RdYlBu_r'))
        plt.colorbar(fig_pedalmap)
        ax4.grid(True, linestyle="--", color="k", linewidth="0.4")
        axg4 = plt.gca()
        axg4.set_xlabel('Engine Speed (rpm)', fontsize=12)
        axg4.set_ylabel('Torque (Nm)', fontsize=12)
        axg4.set_title('PedalMap', fontsize=12)


class ShiftMap(SystemGain):
    def __init__(self, matrix):
        self.xdata = matrix[2]
        self.ydata = matrix[1]
        self.gear = matrix[0]

    def plot_shift_map(self):
        fig5 = plt.figure()
        ax5 = fig5.add_subplot(111)
        strLable = ['1->2', '2->3', '3->4', '4->5', '5->6', '6->7', '7->8', '8->9', '9->10']
        for i in range(1, int(max(self.gear)) + 1):
            # 选择当前Gear, color=colour[i]
            ax5.plot(self.xdata[np.where(self.gear == i)], self.ydata[np.where(self.gear == i)]
                     , marker='o', linestyle='-', linewidth=3, markerfacecolor='blue', markersize=4
                     , label=strLable[i - 1])
            ax5.legend()
        ax5.grid(True, linestyle="--", color="k", linewidth="0.4")
        axg5 = plt.gca()
        axg5.set_xlabel('Vehicle Speed (km/h)', fontsize=12)
        axg5.set_ylabel('Pedal (%)', fontsize=12)
        axg5.set_title('ShiftMap', fontsize=12)

# ----------------------------
# end of class definition

# ----------------------------
# function definition


def acc_response(vehspd_data, acc_data, pedal_cut_index, pedal_avg):
    acc_ped_map = [[], [], []]
    for i in range(0, len(pedal_avg)):
        iVehSpd = vehspd_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]
        iPed = [pedal_avg[i] * ix / ix for ix in range(pedal_cut_index[0][i], pedal_cut_index[1][i])]
        iAcc = acc_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]

        # 删除加速度小于0.05g的数据，认为是踩了制动
        data_len = len(iAcc)
        j = 0
        while j < data_len:
            if iAcc[j] < 0.05:
                del iVehSpd[j]
                del iPed[j]
                del iAcc[j]
                data_len = data_len - 1
                j = j - 1
            j = j + 1

        acc_ped_map[0].append(iPed)
        acc_ped_map[1].append(iVehSpd)
        acc_ped_map[2].append(iAcc)
    obj = AccResponse(acc_ped_map, pedal_avg)
    return obj


def launch(acc_data, pedal_data, pedal_cut_index, pedal_avg):
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
    obj = Launch(launch_map)
    return obj


def maxacc(acc_data, pedal_cut_index, pedal_avg):
    acc_Ped_Max = []
    for i in range(0, len(pedal_avg)):
        acc_Ped_Max.append(max(acc_data[pedal_cut_index[0][i]:pedal_cut_index[0][i] + 1000]))
    obj = MaxAcc(pedal_avg, acc_Ped_Max)
    return obj


def pedal_map(pedal_data, enSpd_data, torq_data, pedal_cut_index, pedal_avg,colour):
    pedal_map = [[], [], []]
    for i in range(0, len(pedal_avg)):
        iTorq = torq_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]
        iEnSpd = enSpd_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]
        pedal_map[0].extend(pedal_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]])
        pedal_map[1].extend(iEnSpd)
        pedal_map[2].extend(iTorq)
    obj = PedalMap(pedal_map)
    return obj


def shift_map(pedal_data, gear_data, vehspd_data, pedal_cut_index, pedal_avg,colour):
    shiftMap = [[], [], []]
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
    obj = ShiftMap(shiftMap_Data)
    return obj


def system_gain(pedal_data, vehspd_data, acc_data, pedal_cut_index, pedal_avg):
    speedIndex = np.arange(10, 170, 10)
    speedIndex = speedIndex.tolist()
    acc_banana = np.zeros((5, len(speedIndex)))
    acc_banana[0, :] = [0.0144, 0.0126, 0.0111, 0.0097, 0.0084, 0.0073, 0.0064, 0.0056, 0.0048,
    0.0042, 0.0037, 0.0032, 0.0028, 0.0024, 0.0021, 0.0018]
    acc_banana[1, :] = [0.0172, 0.0152, 0.0134, 0.0119, 0.0104, 0.0092, 0.0081, 0.0071, 0.0063,
    0.0055, 0.0049, 0.0043, 0.0038, 0.0034, 0.0030, 0.0026]
    acc_banana[2, :] = [0.0200, 0.0178, 0.0158, 0.0141, 0.0125, 0.0111, 0.0098, 0.0087, 0.0078,
    0.0069, 0.0062, 0.0055, 0.0049, 0.0043, 0.0038, 0.0033]
    acc_banana[3, :] = [0.0228, 0.0204, 0.0182, 0.0163, 0.0145, 0.0129, 0.0115, 0.0103, 0.0092,
    0.0082, 0.0074, 0.0066, 0.0059, 0.0053, 0.0047, 0.0042]
    acc_banana[4, :] = [0.0256, 0.0230, 0.0206, 0.0185, 0.0166, 0.0149, 0.0133, 0.0119, 0.0107,
    0.0096, 0.0086, 0.0077, 0.0069, 0.0062, 0.0055, 0.0049]

    vehspd, ped, acc = [], [], []
    vehspd_steady_for_inter = []
    for i in range(0, len(pedal_avg)):
        ivehspd = vehspd_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]
        iped = [pedal_avg[i]]*(pedal_cut_index[1][i] - pedal_cut_index[0][i])
        iacc = acc_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]

        vehspd = vehspd + ivehspd
        ped = ped + iped
        acc = acc + iacc
        vehspd_steady_for_inter.append(max(ivehspd))

    points_for_inter = np.zeros((len(acc), 2))
    points_for_inter[:, 0] = vehspd
    points_for_inter[:, 1] = ped
    points_for_inter[:, 1] = points_for_inter[:, 1]/100*51
    acc_for_inter = np.array(acc)

    pedal_steady_for_inter = [x/100*51+12.7 for x in pedal_avg]
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
    grid_z1 = grid_z1/12.7
    grid_z1 = smooth(grid_z1, 5)

    fig1 = plt.figure()
    ax1 = fig1.add_subplot(111)
    ax1.plot(vehspd_steady_tb_inter, grid_z1, color='green', linestyle='-')
    ax1.plot(speedIndex, acc_banana[0, :], color='blue', linestyle='--')
    ax1.plot(speedIndex, acc_banana[1, :], color='red', linestyle='--')
    ax1.plot(speedIndex, acc_banana[2, :], color='black', linestyle='--')
    ax1.plot(speedIndex, acc_banana[3, :], color='blue', linestyle='--')
    ax1.plot(speedIndex, acc_banana[4, :], color='red', linestyle='--')
    ax1.plot([speedIndex[0]]*5, acc_banana[:, 0], color='blue', linestyle='-')
    ax1.set_xlabel('车速(km/h)')
    ax1.set_ylabel('加速度(g/mm)')
    ax1.set_xlim(0, 120)
    ax1.set_ylim(0, 0.03)
    ax1.grid(True, linestyle="-", color="grey", linewidth="0.4")


    '#  function "griddata" checked: same with matlab'
    # np.savetxt('points_for_inter.csv', points_for_inter, delimiter=',')
    # np.savetxt('acc_for_inter.csv', acc_for_inter, delimiter=',')
    # np.savetxt('points_tb_inter.csv', points_tb_inter, delimiter=',')
    # np.savetxt('grid_z1.csv', points_tb_inter, delimiter=',')


    # obj = SystemGainPlot()
    return


def smooth(a, WSZ):
    # a: NumPy 1-D array containing the data to be smoothed
    # WSZ: smoothing window size needs, which must be odd number,
    # as in the original MATLAB implementation
    out0 = np.convolve(a, np.ones(WSZ, dtype=int), 'valid')/WSZ
    r = np.arange(1, WSZ-1, 2)
    start = np.cumsum(a[:WSZ-1])[::2]/r
    stop = (np.cumsum(a[:-WSZ:-1])[::2]/r)[::-1]
    return np.concatenate((start, out0, stop))


'# *******3-MainCalculation*********'
def cut_sg_data_pedal(pedal_data,vehspd_data):
    # 数据切分
    # edges detection initialize to avoid additional detection of rising edges/trailing edges
    pedal_data[0], pedal_data[-1] = 0, 0
    vehspd_data[0], vehspd_data[-1] = 0, 0
    # end of edges detection initialize
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
        if (t_edge_vehspd[j] - r_edge_vehspd[j] > 500) & (3.5 < np.average(vehspd_data[r_edge_vehspd[j]+200:t_edge_vehspd[j]-200]) < 8.5) & (np.average(pedal_data[r_edge_vehspd[j]:t_edge_vehspd[j]]) < 0.01):
            pedal_cut_index[0].append(r_edge_vehspd[j]-40)  # 车速信号相对于加速度信号有迟滞
            pedal_cut_index[1].append(t_edge_vehspd[j]-40)
            pedal_avg.append(np.mean(pedal_data[r_edge_vehspd[j]:t_edge_vehspd[j]]))

    for j in range(0, len(r_edge_pedal)):
        if (t_edge_pedal[j] - r_edge_pedal[j] > 1000) & (np.cov(pedal_data[r_edge_pedal[j]+20:t_edge_pedal[j]-20]) < 3):
            pedal_cut_index[0].append(r_edge_pedal[j])
            pedal_cut_index[1].append(t_edge_pedal[j])
            pedal_avg.append(np.mean(pedal_data[r_edge_pedal[j]:t_edge_pedal[j]]))

    return pedal_cut_index, pedal_avg


def plot_maxacc( acc_data, pedal_cut_index, pedal_avg):
    # fig3起步特性图
    # acc_start=[0 0 0 0 7.5*100/51 7.5*100/51 7.5*100/51 7.5*100/51;0.02062 0.02709 0.03495 0.04371 0.14767 0.19659 0.24435 0.29176];
    # plot([acc_start(1,4),acc_start(1,5)],[acc_start(2,1),acc_start(2,5)],'b-');
    # plot([acc_start(1,4),acc_start(1,5)],[acc_start(2,2),acc_start(2,6)],'r-');
    # plot([acc_start(1,4),acc_start(1,5)],[acc_start(2,3),acc_start(2,7)],'g-');
    # plot([acc_start(1,4),acc_start(1,5)],[acc_start(2,4),acc_start(2,8)],'r-');
    # plot([7.5*100/51 7.5*100/51 7.5*100/51 7.5*100/51],acc_start(2,5:8),'r-');
    fig3 = plt.figure()
    ax3 = fig3.add_subplot(111)
    acc_Ped_Max = []
    for i in range(0, len(pedal_avg)):
        acc_Ped_Max.append(max(acc_data[pedal_cut_index[0][i]:pedal_cut_index[0][i] + 1000]))
    ax3.plot(pedal_avg, acc_Ped_Max, color='green', linestyle='dashed', marker='o', markerfacecolor='blue',
             markersize=8)
    # , alpha="0.75"
    ax3.grid(True, linestyle="--", color="k", linewidth="0.4")
    ax3.legend()
    axg3 = plt.gca()
    axg3.set_xlabel('Pedal (%)', fontsize=12)
    axg3.set_ylabel('Acc (g)', fontsize=12)
    axg3.set_title('Acc-Pedal', fontsize=12)
    return pedal_avg, acc_Ped_Max

def plot_pedal_map(pedal_data, enSpd_data, torq_data, pedal_cut_index, pedal_avg,colour):
    # fig4 PedalMap-Gear
    fig4 = plt.figure()
    ax4 = fig4.add_subplot(111)
    pedal_map = [[], [], []]
    #sc = plt.scatter(xy, xy, c=z, vmin=0, vmax=20, s=35, cmap=plt.cm.get_cmap('RdYlBu'))
    #plt.colorbar(sc)

    for i in range(0, len(pedal_avg)):
        iTorq = torq_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]
        iEnSpd = enSpd_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]]
        # pedal_map[0].append(pedal_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]])
        # pedal_map[1].append(iEnSpd)
        # pedal_map[2].append(iTorq)
        pedal_map[0].extend(pedal_data[pedal_cut_index[0][i]:pedal_cut_index[1][i]])
        pedal_map[1].extend(iEnSpd)
        pedal_map[2].extend(iTorq)
        # ax4.scatter(iEnSpd, iTorq, marker='o', linewidths=0.1, label=int(round(pedal_avg[i] / 5) * 5), s=10,
        #             c=colour[i])
        ax4.legend()
    fig_pedalmap = ax4.scatter(pedal_map[1], pedal_map[2], c=pedal_map[0], marker='o', linewidths=0.1,
                               s=6, cmap=plt.cm.get_cmap('RdYlBu_r'))
    plt.colorbar(fig_pedalmap)
    ax4.grid(True, linestyle="--", color="k", linewidth="0.4")
    axg4 = plt.gca()
    axg4.set_xlabel('Engine Speed (rpm)', fontsize=12)
    axg4.set_ylabel('Torque (Nm)', fontsize=12)
    axg4.set_title('PedalMap', fontsize=12)
    # cm12 = plt.cm.get_cmap('RdYlBu')
    # xy = range(20)
    # z = xy
    # sc = plt.scatter(pedal_map[1], pedal_map[2], c=pedal_map[0], vmin=0, vmax=20, s=35, cmap=cm12)
    # plt.colorbar(sc)
    # plt.show()
    return pedal_map

def plot_shift_map(pedal_data, gear_data, vehspd_data, pedal_cut_index, pedal_avg,colour):
    # fig5 ShiftMap
    shiftMap = [[], [], []]
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
    fig5 = plt.figure()
    ax5 = fig5.add_subplot(111)
    strLable = ['1->2', '2->3', '3->4', '4->5', '5->6', '6->7', '7->8', '8->9', '9->10']

    for i in range(1, max(gear_data)):
        # 选择当前Gear, color=colour[i]
        ax5.plot(shiftMap_Data[2][np.where(shiftMap_Data[0] == i)], shiftMap_Data[1][np.where(shiftMap_Data[0] == i)]
                 , marker='o', linestyle='-', linewidth=3, markerfacecolor='blue', markersize=4
                 , label=strLable[i - 1])
        ax5.legend()
    ax5.grid(True, linestyle="--", color="k", linewidth="0.4")
    axg5 = plt.gca()
    axg5.set_xlabel('Vehicle Speed (km/h)', fontsize=12)
    axg5.set_ylabel('Pedal (%)', fontsize=12)
    axg5.set_title('ShiftMap', fontsize=12)
    return shiftMap_Data


def main_(file_path,feature_index_array=['Time_abs', 'AccelActuPosHSC1', 'LongAccelG_M', 'VehSpdAvgNonDrvnHSC1','TrEstdGear_TCMHSC1', 'EnSpdHSC1', 'EnToqDrvrReqdExtdRngHSC1']):
    # *******1-GetSysGainData******
    # 获取数据，判断数据类型，不同读取，获取文件名信息，
    SG_csv_Data_ful = pd.read_csv(file_path)
    # *******2-GetSGColumn*********
    # 获取列号，标准变量及面板输入，数据预处理
    SG_csv_Data_Selc = SG_csv_Data_ful.loc[:, ['Time_abs', 'AccelActuPosHSC1', 'LongAccelG_M', 'VehSpdAvgNonDrvnHSC1',
                                               'TrEstdGear_TCMHSC1', 'EnSpdHSC1', 'EnToqDrvrReqdExtdRngHSC1']]
    SG_csv_Data = SG_csv_Data_Selc.drop_duplicates()

    time_Data = SG_csv_Data['Time_abs'].tolist()
    pedal_Data = SG_csv_Data['AccelActuPosHSC1'].tolist()
    acc_Data = SG_csv_Data['LongAccelG_M'].tolist()
    vehSpd_Data = SG_csv_Data['VehSpdAvgNonDrvnHSC1'].tolist()
    gear_Data = SG_csv_Data['TrEstdGear_TCMHSC1'].tolist()
    enSpd_Data = SG_csv_Data['EnSpdHSC1'].tolist()
    torq_Data = SG_csv_Data['EnToqDrvrReqdExtdRngHSC1'].tolist()
    colour_Bar = ['orange', 'lightgreen', 'c', 'royalblue', 'lightcoral', 'yellow', 'red', 'brown',
                  'teal', 'blue', 'coral', 'gold', 'lime', 'olive']
    # 加速度修正
    acc_offset = ((vehSpd_Data[-1]-vehSpd_Data[0])/3.6/(time_Data[-1]-time_Data[0])-np.average(acc_Data[:])*9.8)/9.8
    acc_Data = [x + acc_offset for x in acc_Data]
    # acc_check = (vehSpd_Data[-1]-vehSpd_Data[0])/3.6-np.average(acc_Data)*9.8*(time_Data[-1]-time_Data[0])
    # 数据切分
    pedal_cut_index, pedal_avg = cut_sg_data_pedal(pedal_Data, vehSpd_Data)
    # fig1三维图，增加最大加速度连线以及稳态车速线
    obj_AccResponse = acc_response(vehSpd_Data, acc_Data, pedal_cut_index, pedal_avg)
    # # obj_AccResponse.plot_acc_response()
    # # fig2起步图，[5,10,20,30,40,50,100],后续补充判断大油门不是100也画出来,粗细
    obj_Launch = launch(acc_Data, pedal_Data, pedal_cut_index, pedal_avg)
    # # obj_Launch.plot_launch()
    obj_MaxAcc = maxacc(acc_Data, pedal_cut_index, pedal_avg)
    dic_MaxAcc = {file_path: obj_MaxAcc}
    # obj_MaxAcc.plot_maxacc()
    # fig4 PedalMap-Gear
    obj_PedalMap = pedal_map(pedal_Data, enSpd_Data, torq_Data, pedal_cut_index, pedal_avg, colour_Bar)
    # obj_PedalMap.plot_pedal_map()
    # fig5 ShiftMap
    obj_ShiftMap = shift_map(pedal_Data, gear_Data, vehSpd_Data, pedal_cut_index, pedal_avg, colour_Bar)
    # obj_ShiftMap.plot_shift_map()
    obj_SystemGain = system_gain(pedal_Data, vehSpd_Data, acc_Data, pedal_cut_index, pedal_avg)
    sysGain_class = SystemGainDocker(obj_AccResponse, obj_Launch, dic_MaxAcc, obj_PedalMap, obj_ShiftMap)



    return sysGain_class   #, obj_Launch, max_acc_map, pedal_map, shift_map


if __name__ == '__main__':
    # *******1-GetSysGainData****** AS22_C16UVV016_SystemGain_20160925_D_M_SL, IP31_L16UOV055_10T_SystemGain_20160225
    main_('./IP31_L16UOV055_Ride_SyGa_20160225_SL.csv')
    plt.show()

    print('Finish!')