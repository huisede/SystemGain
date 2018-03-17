from matplotlib import use
from numpy import zeros, array, mean, arange, where, pi
use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationBar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.cm as cm

# ----------------------------
# class definition


class MyFigureCanvas(FigureCanvas):
    """
    Main class of generating figs in GUI using matplot.backend_qt5agg

    Contains:
    drawing functions

    """

    def __init__(self, parent=None, width=10, height=10, dpi=100, plot_type='3d', **kwargs):
        self.fig = Figure(figsize=(width, height), dpi=100)
        super(MyFigureCanvas, self).__init__(self.fig)
        self.kwargs = kwargs
        self.color_type = ['#FFA500',         # 橙色
                           '#3CB371',         # 春绿
                           '#4169E1',         # 皇家蓝
                           '#DF12ED',         # 紫
                           '#FD143C',         # 鲜红
                           '#D2691E',         # 巧克力
                           '#696969',         # 暗灰
                           '#40E0D0',         # 绿宝石
                           '#9400D3',         # 紫罗兰
                           ]

        if plot_type == '2d':
            self.axes = self.fig.add_axes([0.15, 0.1, 0.75, 0.8])
        elif plot_type == '3d':
            self.fig.subplots_adjust(left=0.08, top=0.92, right=0.95, bottom=0.1)
            # self.fig.subplots_adjust(left=0.08, top=0.92, right=0.95, bottom=0.1)
            self.axes = self.fig.add_subplot(111, projection='3d', facecolor='none')
        elif plot_type == '2d-poly':
            self.axes = self.fig.add_subplot(111, polar=True)
        elif plot_type == '2d-multi':
            pass
        elif plot_type == '3d-subplot':
            pass
        elif plot_type == '2d-subplot':
            pass

    def plot_acc_response(self, data, ped_avg, ped_maxacc, vehspd_cs, pedal_cs):  # 目前做不到先画图，后统一输出，只能在主线程里面同步画
        counter = -1
        for i in range(0, len(data[1])):
            i_acc_lab = int(round(ped_avg[i] / 5) * 5)
            if i_acc_lab in [10, 20, 30, 50, int(round(max(ped_avg)/5) * 5)]:
                counter += 1
                self.axes.plot(data[1][i], data[0][i], data[2][i], color=self.color_type[counter], label=i_acc_lab)
            else:
                self.axes.plot(data[1][i], data[0][i], data[2][i], color='darkgray')
        self.axes.legend(bbox_to_anchor=(0.85, 1.05), ncol=1, loc=2, borderaxespad=0, fontsize=8)
        self.axes.plot(ped_maxacc[1], ped_maxacc[0], ped_maxacc[2], 'ko--', markersize=4, alpha=.65)
        self.axes.plot(vehspd_cs, pedal_cs, zeros(len(pedal_cs)), 'ko--', markersize=4, alpha=.65)
        self.axes.grid(True, linestyle="--", color="k", linewidth="0.4")
        self.axes.set_xlabel('Velocity (kph)', fontsize=12)
        self.axes.set_ylabel('Pedal (%)', fontsize=12)
        self.axes.set_zlabel('Acc (g) ', fontsize=12)
        self.axes.set_title('Acc Response Map', fontsize=12)

    def plot_launch(self, data):

        for i in range(0, len(data[2])):
            self.axes.plot(data[2][i], data[1][i], color=self.color_type[i], label=int(round(max(data[0][i]) / 5) * 5))
            self.axes.legend()
            self.axes.grid(True, linestyle="--", color="k", linewidth="0.4")
        self.axes.set_xlabel('Time (s)', fontsize=12)
        self.axes.set_ylabel('Acc (g)', fontsize=12)
        self.axes.set_title('Launch', fontsize=12)

    def plot_max_acc(self, data):

        # self.axes.plot(data[0], data[1], color='green', linestyle='dashed', marker='o', markerfacecolor='blue',
        #                markersize=8)
        self.axes.plot(data[0], data[1], linestyle='dashed', marker='o', markersize=8)
        self.axes.grid(True, linestyle="--", color="k", linewidth="0.4")
        self.axes.set_xlabel('Pedal (%)', fontsize=12)
        self.axes.set_ylabel('Acc (g)', fontsize=12)
        self.axes.set_title('Max Acc', fontsize=12)

    def plot_pedal_map(self, data):
        pedalmap = self.axes.scatter(data[1], data[2], c=data[0], marker='o', linewidths=0.1,
                                     s=6, cmap=cm.get_cmap('RdYlBu_r'))
        self.axes.grid(True, linestyle="--", color="k", linewidth="0.4")
        self.axes.set_xlabel('Engine Speed (rpm)', fontsize=12)
        self.axes.set_ylabel('Torque (Nm)', fontsize=12)
        self.axes.set_title('PedalMap', fontsize=12)

    def plot_shift_map(self, data, kind, **kwargs):
        if kind == 'AT/DCT':
            str_label = ['1->2', '2->3', '3->4', '4->5', '5->6', '6->7', '7->8', '8->9', '9->10']
            for i in range(1, int(max(data[0])) + 1):
                # 选择当前Gear, color=colour[i]
                self.axes.plot(data[2][where(data[0] == i)], data[1][where(data[0] == i)]
                               , marker='o', linestyle='-', linewidth=3, markerfacecolor='blue', markersize=4
                               , color=self.color_type[i - 1], label=str_label[i - 1])
                self.axes.legend()
            self.axes.grid(True, linestyle="--", color="k", linewidth="0.4")
            self.axes.set_xlabel('Vehicle Speed (kph)', fontsize=12)
            self.axes.set_ylabel('Pedal (%)', fontsize=12)
            self.axes.set_title('Shift Map', fontsize=12)
        elif kind == 'CVT':
            for i in range(0, len(data[1])):
                self.axes.plot(data[2][i], data[0][i], color='#FD143C')
                self.axes.annotate(str(int(kwargs['pedal_avg'][i])), xy=(data[2][i][-100], data[0][i][-100]),
                                   xycoords='data', xytext=(+2, +2), textcoords='offset points', fontsize=10)
                self.axes.plot(data[2][i], data[1][i], color='#4169E1')
            self.axes.set_xlabel('Velocity (kph)', fontsize=12)
            self.axes.set_ylabel('Engine/Turbine Speed (rpm)', fontsize=12)
            self.axes.set_title('Shift Map', fontsize=12)

    def plot_systemgain_curve(self, vehspd_sg, acc_sg):
        speedIndex = arange(10, 170, 10)
        speedIndex = speedIndex.tolist()
        acc_banana = zeros((5, len(speedIndex)))
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

        # self.axes.plot(vehspd_sg, acc_sg, color='green', linestyle='-')
        self.axes.plot(vehspd_sg, acc_sg, linestyle='-', label='sg_cr', linewidth=3.0)

        self.axes.plot(speedIndex, acc_banana[0, :], color='#B0C4DE', linestyle='--')
        self.axes.plot(speedIndex, acc_banana[1, :], color='#FA8072', linestyle='--')
        self.axes.plot(speedIndex, acc_banana[2, :], color='696969', linestyle='--')
        self.axes.plot(speedIndex, acc_banana[3, :], color='#B0C4DE', linestyle='--')
        self.axes.plot(speedIndex, acc_banana[4, :], color='#FA8072', linestyle='--')
        self.axes.plot([speedIndex[0]] * 5, acc_banana[:, 0], color='696969', linestyle='-')
        self.axes.set_xlabel('Vehicle Speed(kph)', fontsize=12)
        self.axes.set_ylabel('Acc(g/mm)', fontsize=12)
        self.axes.set_xlim(0, 120)
        self.axes.set_ylim(0, 0.03)
        self.axes.grid(True, linestyle="--", color="grey", linewidth="0.4")
        self.axes.set_title('System Gain Curve')

    def plot_constant_speed(self, vehspd_cs, pedal_cs):

        # self.axes.plot(vehspd_cs, pedal_cs, color='green', linestyle='dashed', marker='o', markerfacecolor='blue',
                       # markersize=8)
        self.axes.plot(vehspd_cs, pedal_cs, linestyle='dashed', marker='o', markersize=8)
        self.axes.grid(True, linestyle="--", color="k", linewidth="0.4")
        self.axes.set_xlabel('Vehicle Speed (kph)', fontsize=12)
        self.axes.set_ylabel('Pedal (%)', fontsize=12)
        self.axes.set_title('Constant Speed', fontsize=12)

    def plot_raw_data(self, time, df, **kwargs):

        signal_num = df.shape[1]
        if signal_num < 3:
            font_size = 12
        elif signal_num < 5:
            font_size = 10
        else:
            font_size = 8

        pos = [0.02, 0.1, 1.0-signal_num*font_size/160, 0.8]

        colors = ['r', 'b', 'g', 'm', 'darkgray', 'orchid', 'orange', 'navy', 'purple', 'crimson', 'steelblue',
                  'sage', 'gold', 'tomato', 'brown']

        for i in range(signal_num):
            if i == 0:
                self.axes = self.fig.add_axes(pos, facecolor='w', label=str(df.columns[i]))  # 设置初始的图层底色为白色
                self.axes.tick_params(axis='x', colors='black', labelsize=10)
                self.axes.set_xlabel('time (s)', fontsize=12)
            else:
                self.axes = self.fig.add_axes(pos, facecolor='none', label=str(df.columns[i]))  # 设置随后的图层底色为透明
                self.axes.get_xaxis().set_visible(False)

            self.axes.spines['right'].set_position(('outward', font_size/10*70 * i))  # 图的右侧边框向外移动
            self.axes.spines['right'].set_color(colors[i])
            self.axes.spines['right'].set_linewidth(2)
            self.axes.plot(time, df.iloc[:, i], linewidth=1, color=colors[i])
            self.axes.yaxis.set_ticks_position('right')
            self.axes.tick_params(axis='y', colors=colors[i])
            self.axes.set_ylabel(str(df.columns[i]), fontsize=font_size, color=colors[i])
            self.axes.yaxis.set_label_position('right')

    def plot_acc_response_subplot(self, history_data, legend_name):
        pic_num = len(history_data)
        for m in range(pic_num):
            self.axes = self.fig.add_subplot(1, pic_num, m+1, projection='3d')
            data = history_data[m].sysGain_class.accresponce.data
            ped_avg = history_data[m].sysGain_class.accresponce.pedal_avg
            ped_maxacc = history_data[m].sysGain_class.accresponce.max_acc_ped
            vehspd_cs = history_data[m].sysGain_class.systemgain.vehspd_cs
            pedal_cs = history_data[m].sysGain_class.systemgain.pedal_cs
            counter = -1
            for i in range(0, len(data[1])):
                i_acc_lab = int(round(ped_avg[i] / 5) * 5)
                if i_acc_lab in [10, 20, 30, 50, int(round(max(ped_avg) / 5) * 5)]:
                    counter += 1
                    self.axes.plot(data[1][i], data[0][i], data[2][i], color=self.color_type[counter], label=i_acc_lab)
                else:
                    self.axes.plot(data[1][i], data[0][i], data[2][i], color='darkgray')
            self.axes.legend(bbox_to_anchor=(0.85, 1.05), ncol=1, loc=2, borderaxespad=0, fontsize=8)
            self.axes.plot(ped_maxacc[1], ped_maxacc[0], ped_maxacc[2], 'ko--', markersize=4, alpha=.65)
            self.axes.plot(vehspd_cs, pedal_cs, zeros(len(pedal_cs)), 'ko--', markersize=4, alpha=.65)
            self.axes.set_xlabel('Vehicle Speed (kph)', fontsize=12)
            self.axes.set_ylabel('Pedal (%)', fontsize=12)
            self.axes.set_zlabel('Acc (g) ', fontsize=12)
            self.axes.set_title('[' + legend_name[m] + '] - Acc Response Map', fontsize=12)

    def plot_launch_subplot(self, history_data, legend_name):
        pic_num = len(history_data)
        for m in range(pic_num):
            self.axes = self.fig.add_subplot(1, pic_num, m+1)
            data = history_data[m].sysGain_class.launch.data

            for i in range(0, len(data[2])):
                self.axes.plot(data[2][i], data[1][i], label=int(round(mean(data[0][i]) / 5) * 5))
                self.axes.legend()
                self.axes.grid(True, linestyle="--", color="k", linewidth="0.4")
            self.axes.set_xlabel('Time (s)', fontsize=12)
            self.axes.set_ylabel('Acc (g)', fontsize=12)
            self.axes.set_title('['+legend_name[m]+'] - Launch', fontsize=12)

    def plot_shift_map_subplot(self, history_data, legend_name):
        pic_num = len(history_data)
        for m in range(pic_num):
            self.axes = self.fig.add_subplot(1, pic_num, m + 1)
            data = history_data[m].sysGain_class.shiftmap.data
            pt_type = history_data[m].sysGain_class.pt_type
            kwargs = history_data[m].sysGain_class.shiftmap.kwargs
            if pt_type == 'AT/DCT':
                str_label = ['1->2', '2->3', '3->4', '4->5', '5->6', '6->7', '7->8', '8->9', '9->10']
                for i in range(1, int(max(data[0])) + 1):
                    # 选择当前Gear, color=colour[i]
                    self.axes.plot(data[2][where(data[0] == i)], data[1][where(data[0] == i)]
                                   , marker='o', linestyle='-', linewidth=3, markerfacecolor='blue', markersize=4
                                   , label=str_label[i - 1])
                    self.axes.legend()
                self.axes.grid(True, linestyle="--", color="k", linewidth="0.4")
                self.axes.set_xlabel('Vehicle Speed (kph)', fontsize=12)
                self.axes.set_ylabel('Pedal (%)', fontsize=12)
                self.axes.set_title('['+legend_name[m]+'] - Shift Map', fontsize=12)
            elif pt_type == 'CVT':
                for i in range(0, len(data[1])):
                    self.axes.plot(data[2][i], data[0][i], color='r')
                    self.axes.annotate(str(int(kwargs['pedal_avg'][i])), xy=(data[2][i][-100], data[0][i][-100]),
                                       xycoords='data', xytext=(+2, +2), textcoords='offset points')
                    self.axes.plot(data[2][i], data[1][i], color='b')
                self.axes.set_xlabel('Velocity (kph)', fontsize=12)
                self.axes.set_ylabel('Engine/Turbine Speed (rpm)', fontsize=12)
                self.axes.set_title('[' + legend_name[m] + '] - Shift Map', fontsize=12)

    def plot_pedal_map_subplot(self, history_data, legend_name):
        pic_num = len(history_data)
        for m in range(pic_num):
            self.axes = self.fig.add_subplot(1, pic_num, m + 1)
            data = history_data[m].sysGain_class.pedalmap.data

            pedalmap = self.axes.scatter(data[1], data[2], c=data[0], marker='o', linewidths=0.1,
                                         s=6, cmap=cm.get_cmap('RdYlBu_r'))
            self.axes.grid(True, linestyle="--", color="k", linewidth="0.4")
            self.axes.set_xlabel('Engine Speed (rpm)', fontsize=12)
            self.axes.set_ylabel('Torque (Nm)', fontsize=12)
            self.axes.set_title('[' + legend_name[m] + '] - Pedal Map', fontsize=12)
