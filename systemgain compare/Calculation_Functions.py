# -*- coding: utf8 -*-
# THIS IS BRANCH "READANDLOAD"!
import glob
import csv
import re
import numpy as np
import pandas as pd
import xlrd
import scipy as sp
import requests
import pickle
import os
from get_API_information import GPS_to_road_information
from INTEST_GPS_trans_API import GPS_FIX_WGS84
from Time_to_UTC import *

# warnings.filterwarnings("ignore")


# from statsmodels.nonparametric.smoothers_lowess import lowess


# ----------------------  DataProcessing functions  --------------------------

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


def five_points_avg(series):
    l = len(series)
    avg_series = np.zeros(l)
    avg_series[0] = (series[1] + series[0]) / 2
    avg_series[1] = (series[2] + series[1] + series[0]) / 3
    for i in range(2, l - 2, 1):
        avg_series[i] = (series[i + 2] + series[i + 1] + series[i] + series[i - 1] + series[i - 2]) / 5
    avg_series[-2] = (series[-1] + series[-2] + series[-3]) / 3
    avg_series[-1] = (series[-1] + series[-2]) / 2
    return avg_series


def five_points_avg_acc(series, g=9.8, frequency=10):
    l = len(series)
    avg_acc = np.zeros(l)
    avg_acc[0] = (series[1] - series[0]) * frequency / 3.6 / g
    avg_acc[1] = (series[2] - series[0]) * frequency / 2 / 3.6 / g
    for i in range(2, l - 2, 1):
        avg_acc[i] = (series[i + 2] - series[i - 2]) * frequency / 4 / 3.6 / g
    avg_acc[-2] = (series[-1] - series[-3]) * frequency / 2 / 3.6 / g
    avg_acc[-1] = (series[-1] - series[-2]) * frequency / 3.6 / g
    return avg_acc


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


def signal_times_cal(series):  # 数上升沿个数  Passed Test
    l = len(series)
    times_counter = 0
    for i in range(1, l, 1):
        if (not series[i - 1]) and series[i]:
            times_counter = times_counter + 1
        else:
            continue
    return


def turnlight_fix(series):  # Passed Test 20170527
    l = len(series)
    turn_lab = series
    for i in range(l - 1):
        if series[i] and (not series[i + 1]):
            j = i + 1
            while (not series[j]) and j < l - 1:
                j = j + 1
            if j - i < 7:  # 最多间隔0.5-0.6s不闪烁
                for m in range(i + 1, j):
                    turn_lab[m] = 1
    return turn_lab


# def GPS_fix(longitude, latitude):  # array type  Passed Test
#     initial_point_lgt = 121.192362
#     initial_point_lat = 31.27878
#     fix_ratio = 1.671765504
#     lgt = fix_ratio * (longitude / 100 + 0.079602 - initial_point_lgt) + initial_point_lgt
#     lat = fix_ratio * (latitude / 100 + 0.110331 - initial_point_lat) + initial_point_lat
#     return lgt, lat


def vector_2_360(vector):  # Passed test 20170602
    ang_head = 0
    if vector[0] > 0:
        ang_head = np.arctan(vector[1] / vector[0])
    elif vector[0] < 0:
        ang_head = np.arctan(vector[1] / vector[0]) + np.pi
    else:
        if vector[1] > 0:
            ang_head = np.pi / 2
        elif vector[1] < 0:
            ang_head = np.pi / 2 + np.pi
        else:
            ang_head = 0
    if ang_head < 0:
        ang_head = ang_head + 2 * np.pi
    return ang_head * 180 / np.pi


def heading_angle(longitude, latitude):  # Need to be modified
    l = len(longitude)
    ang = np.zeros(l)
    # ang_delta = ang  # 指针赋值,联动
    ang_delta = np.zeros(l)
    start_position = 0
    Cal_GPS_len = 2e-4
    for i in range(l):  # 找到开始记录GPS的点
        if longitude[i] > 0:
            start_position = i
            break

    for i in range(start_position + 1, l, 1):
        if longitude[i] > 0 and latitude[i] > 0:
            j = i
            iterable_step = 1
            while start_position < j < l - 1:
                j = j - iterable_step
                if j < start_position:
                    j = start_position
                pass_ver_test = np.array([longitude[i] - longitude[j], latitude[i] - latitude[j]])
                if np.linalg.norm(pass_ver_test) > Cal_GPS_len or j == start_position:
                    pass_ver = pass_ver_test
                    break
                elif np.linalg.norm(pass_ver_test) < 0.35 * Cal_GPS_len:
                    iterable_step = iterable_step + 2
                elif 0.35 * Cal_GPS_len < np.linalg.norm(pass_ver_test) <= 0.75 * Cal_GPS_len:
                    iterable_step = iterable_step + 1
                elif 0.75 * Cal_GPS_len < np.linalg.norm(pass_ver_test) <= Cal_GPS_len:
                    if iterable_step > 2:
                        iterable_step = iterable_step - 1

            ang[i] = vector_2_360(pass_ver)

    for i in range(l):  # 0-360°之间的跳变需要考虑 好像没什么用
        if i:
            if ang[i] - ang[i - 1] > 350:
                ang_delta[i] = ang[i] - ang[i - 1] - 360
            elif ang[i] - ang[i - 1] < -350:
                ang_delta[i] = ang[i] - ang[i - 1] + 360
            else:
                ang_delta[i] = ang[i] - ang[i - 1]
        else:
            ang_delta[i] = 0

    return ang, ang_delta


def heading_angle_cal(longitude, latitude):  # 考虑变步长搜索   Need to be modified       已修改20170610
    l = len(longitude)
    ang = np.zeros(l)
    start_position = 0
    Cal_GPS_len = 3e-4
    for i in range(l):  # 找到开始记录GPS的点
        if longitude[i] > 0:
            start_position = i
            break

    for i in range(start_position + 1, l, 1):
        if longitude[i] > 0 and latitude[i] > 0:
            j = i
            iterable_step = 1
            while start_position < j < l - 1:
                j = j - iterable_step
                if j < start_position:
                    j = start_position
                pass_ver_test = np.array([longitude[i] - longitude[j], latitude[i] - latitude[j]])
                if np.linalg.norm(
                        pass_ver_test) > Cal_GPS_len or j == start_position:  # 标准化后的识别精度，约30m间隔取一点(逐点搜索计算效率太低，有待改善)
                    pass_ver = pass_ver_test
                    break
                elif np.linalg.norm(pass_ver_test) < 0.35 * Cal_GPS_len:
                    iterable_step = iterable_step + 2
                elif 0.35 * Cal_GPS_len < np.linalg.norm(pass_ver_test) <= 0.75 * Cal_GPS_len:
                    iterable_step = iterable_step + 1
                elif 0.75 * Cal_GPS_len < np.linalg.norm(pass_ver_test) <= Cal_GPS_len:
                    if iterable_step > 2:
                        iterable_step = iterable_step - 1

            iterable_step = 1
            k = i
            while start_position < k < l - 1:
                k = k + iterable_step
                if k > l - 1:
                    k = l - 1
                forw_ver_test = np.array([longitude[k] - longitude[i], latitude[k] - latitude[i]])
                if np.linalg.norm(forw_ver_test) > 3e-4 or k == l - 1:
                    forw_ver = forw_ver_test
                    break
                elif np.linalg.norm(forw_ver_test) < 0.35 * Cal_GPS_len:
                    iterable_step = iterable_step + 2
                elif 0.35 * Cal_GPS_len < np.linalg.norm(forw_ver_test) <= 0.75 * Cal_GPS_len:
                    iterable_step = iterable_step + 1
                elif 0.75 * Cal_GPS_len < np.linalg.norm(forw_ver_test) <= Cal_GPS_len:
                    if iterable_step > 2:
                        iterable_step = iterable_step - 1

            try:
                cos_ang = pass_ver.dot(forw_ver) / (np.sqrt(pass_ver.dot(pass_ver)) * np.sqrt(forw_ver.dot(forw_ver)))
                ang[i] = np.arccos(cos_ang) * 180 / np.pi
            except:
                ang[i] = 0
        else:  # GPS中间丢失
            ang[i] = 0
        ang[np.isnan(ang)] = 0
    return ang


def angle_delta(angle_A, angle_B):
    if angle_A - angle_B > 180:
        angle_del = 360 - (angle_A - angle_B)
    elif angle_A - angle_B < -180:
        angle_del = 360 + (angle_A - angle_B)
    else:
        angle_del = abs(angle_A - angle_B)

    return angle_del


def ignore_charging(dataframe):
    data = dataframe[(dataframe['Veh_Spd_NonDrvn'] == float(0)) & (dataframe['En_Spd'] == float(0))]
    data_soc = data['BMSPackSOC']
    if data_soc.iloc[-1] - data_soc.iloc[0] > 30:
        brake_icon = 1
        for i in range(1, data.shape[0], 1):
            if brake_icon:
                if data_soc.iloc[i] > data_soc.iloc[i - 1] and data_soc.index[i] - data_soc.index[i - 1] == 1:
                    for j in range(i + 2, data.shape[0], 1):
                        if data_soc.iloc[j] > data_soc.iloc[j - 1] and data_soc.index[j] - data_soc.index[j - 1] == 1:
                            if j - i < 150:
                                Charge_pos = data.index[i]
                                brake_icon = 0
                                break
                            else:
                                Charge_pos = data.index[-1]
                else:
                    Charge_pos = data.index[-1]
            else:
                break
    else:
        Charge_pos = data.index[-1]
    dataframe_new = dataframe.loc[dataframe.index[0]:Charge_pos]

    return dataframe_new


def date_reverse(date_in):
    if date_in.__class__ == str:
        revised_data = normal_time_stamp(int(date_in))
    elif date_in.__class__ == int:
        revised_data = normal_time_stamp(date_in)

    return revised_data


# ----------------------  Calculation functions  --------------------------
def odemeter_cal(Vspd, frequency=10):
    odemeter = sum(Vspd) / frequency / 3.6 / 1000  # km

    return odemeter


def sudden_brake(series, Car_type='ZS11'):
    style_brk = {'ZS11': [-0.5, -0.35, -0.1],
                 'AS24': [-0.5, -0.35, -0.15]}
    l = len(series)
    brk_lab = np.zeros(l)
    for i in range(l):
        if series[i] < style_brk[Car_type][0]:
            brk_lab[i] = 3
        elif style_brk[Car_type][0] < series[i] < style_brk[Car_type][1]:
            brk_lab[i] = 2
        elif style_brk[Car_type][1] < series[i] < style_brk[Car_type][2]:
            brk_lab[i] = 1
    brk_times = find_3_level_times(brk_lab)
    return brk_times


def sudden_acc(series_xacc, series_Vspd, Car_type='ZS11'):
    style_acc = {'ZS11': [0.04, 0.31, 0.36, 0.35, 0.22, 0.23, 0.16, 0.12, 0.08],
                 'AS24': [0.2, 0.38, 0.41, 0.41, 0.39, 0.43, 0.36, 0.30, 0.22]}
    vspd_interp = [0, 10, 20, 30, 40, 60, 80, 100, 120]
    l = len(series_xacc)
    acc_lab = np.zeros(l)
    style_acc_current = np.array(style_acc[Car_type])
    for i in range(l):
        if series_xacc[i] > np.interp(series_Vspd[i], vspd_interp, 0.5 * style_acc_current):
            acc_lab[i] = 3
        elif np.interp(series_Vspd[i], vspd_interp, 0.3 * style_acc_current) < series_xacc[i] < \
                np.interp(series_Vspd[i], vspd_interp, 0.5 * style_acc_current):
            acc_lab[i] = 2
        elif np.interp(series_Vspd[i], vspd_interp, 0.15 * style_acc_current) < series_xacc[i] < \
                np.interp(series_Vspd[i], vspd_interp, 0.3 * style_acc_current):
            acc_lab[i] = 1
    acc_times = find_3_level_times(acc_lab)
    return acc_times


def sudden_steering(series, Car_type='ZS11'):
    style_steer = {'ZS11': [0.35, 0.2, 0.1],
                   'AS24': [0.35, 0.2, 0.15]}
    l = len(series)
    str_lab = np.zeros(l)
    for i in range(l):
        if series[i] > style_steer[Car_type][0]:
            str_lab[i] = 3
        elif style_steer[Car_type][0] > series[i] > style_steer[Car_type][1]:
            str_lab[i] = 2
        elif style_steer[Car_type][1] > series[i] > style_steer[Car_type][2]:
            str_lab[i] = 1
    str_times = find_3_level_times(str_lab)
    return str_times


def overtake_cal(turn_lab, head_ang_abs, Steering_angle, v_spd, frequency=10, Steering_angle_limit=500):  # np.array输入
    l = len(v_spd)
    Steer_multi_vspd = Steering_angle * v_spd  # 以转向角度*车速来判定，但是存在弊端，车型不同可能有差异！！后期需要修改
    Steer_multi_vspd_lab = np.zeros(l)
    overtake_times = 0
    candidate_lab_index = []
    select_lab_index = []
    offset_of_time = int(0.5 * frequency)  # 判定过程中挑选出来的转向曲线需要补上前后曲线以保障完整的形态
    overtake_angle_change_limit = 15  # 角度差小于15°
    for i in range(l):
        if Steer_multi_vspd[i] > Steering_angle_limit:
            Steer_multi_vspd_lab[i] = 1
        elif Steer_multi_vspd[i] < -Steering_angle_limit:
            Steer_multi_vspd_lab[i] = -1

    i = 0
    while i < l:
        if Steer_multi_vspd_lab[i] != 0 and turn_lab[i] != 1:  # 注意！Intest的盒子初始段的GPS永远是缺失的，可能引起误判
            j = i
            while Steer_multi_vspd_lab[j] and turn_lab[j] != 1 and j < l - 1:
                j = j + 1
            if j - i >= 5:  # 0.5s 变道下界限时间
                candidate_lab_index = np.concatenate(
                    (candidate_lab_index, [i, j, Steer_multi_vspd_lab[j - 1]]))  # 选出的符合条件的点以[起 停 正/负]存入数组
            i = j + 1
        else:
            i = i + 1

    for i in range(3, len(candidate_lab_index), 3):
        if candidate_lab_index[i] - candidate_lab_index[i - 2] < 2 * frequency and candidate_lab_index[i + 2] * \
                candidate_lab_index[i - 1] < 0:
            select_lab_index = np.concatenate((select_lab_index, [i / 3]))  # 选出符合条件的有正负转向角却没有明显航向变化的连续段

    for i in range(len(select_lab_index)):
        if i < len(select_lab_index) - 1:
            if select_lab_index[i + 1] - select_lab_index[i] == 1:
                if angle_delta(head_ang_abs[int(candidate_lab_index[[select_lab_index[i] * 3 - 3]]) - offset_of_time],
                               head_ang_abs[int(candidate_lab_index[[select_lab_index[i] * 3 + 4]]) + offset_of_time]) \
                        < overtake_angle_change_limit:
                    overtake_times = overtake_times + 1
            else:
                if angle_delta(head_ang_abs[int(candidate_lab_index[[select_lab_index[i] * 3 - 3]]) - offset_of_time],
                               head_ang_abs[int(candidate_lab_index[[select_lab_index[i] * 3 + 1]]) + offset_of_time]) \
                        < overtake_angle_change_limit:
                    overtake_times = overtake_times + 1
        else:
            if angle_delta(head_ang_abs[int(candidate_lab_index[[select_lab_index[i] * 3 - 3]]) - offset_of_time],
                           head_ang_abs[int(candidate_lab_index[[select_lab_index[i] * 3 + 1]]) + offset_of_time]) \
                    < overtake_angle_change_limit:
                overtake_times = overtake_times + 1

    return overtake_times


def turnning_cal(angle, angle_lim_down=20, angle_lim_up=180):  # 定到10可以识别小弧线弯 heading_angle_cal配合
    l = len(angle)
    turn_lab = np.zeros(l)
    turn_lab_fix = turn_lab
    ang_array = np.array(angle)
    turn_lab[ang_array >= angle_lim_down] = 1
    turn_lab[ang_array > angle_lim_up] = 0
    for i in range(l - 1):
        if not turn_lab[i] and turn_lab[i + 1]:
            j = i + 1
            while turn_lab[j] and j < l - 1:
                j = j + 1
            if j - i < 10:
                turn_lab_fix[i + 1:j] = 0
    return turn_lab_fix


def brake_skill(series_xacc, v_spd):
    l = len(v_spd)
    vel_spd_lab = np.zeros(l)
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
                    brake_skill_cal = np.concatenate((brake_skill_cal, [max_acc - min_acc]))
                    break

    return np.array(brake_skill_cal).mean()


def tip_in(series_accped, frequency=10):
    l = len(series_accped)
    delta_accped = []
    result_array = []
    for i in range(1, l, 1):
        delta_accped.append(series_accped[i] - series_accped[i - 1])
    delta_accped = np.array(delta_accped) * frequency
    tip_in_times = 0
    for i in range(1, l - 5, 1):
        sum_of_acc = 0
        if delta_accped[i] > 0 and delta_accped[i - 1] <= 0:
            sum_of_acc = delta_accped[i]
            j = i + 1
            while delta_accped[j] > 0 and delta_accped[j + 3] >= 0 and j < l - 5:
                sum_of_acc = sum_of_acc + delta_accped[j]
                j = j + 1
            if sum_of_acc / (j - i) > 80 and series_accped[j - 1] > 10:
                tip_in_times = tip_in_times + 1
                result_array.append([series_accped[i], series_accped[j], (j - i) / frequency])
    return tip_in_times, result_array


def soc_balance_time_ratio(series_SOC_DF, balanceposition=33):
    time_ratio = series_SOC_DF[series_SOC_DF < balanceposition].shape[0] / series_SOC_DF.shape[0]
    return time_ratio


def over_speed_cal(df, vspd):
    l = df.shape[0]
    cal = 0
    maxspeed = 120
    csvfile = open('GPS_log.csv', 'a', newline='')
    csvwriter = csv.writer(csvfile)
    for i in range(0, l - 100, 20):
        if vspd[i] > 0:
            if i % 100 == 0:
                roadname, maxspeed, roadlevel = GPS_to_road_information(df, i)
                # data = [roadname+maxspeed+roadlevel]
                # csvwriter.writerows(data)
            if vspd[i] > 1.1 * float(maxspeed):
                cal = cal + 1
    over_speed_propotion = cal / l * 20

    return over_speed_propotion


# --------------------------- File IO -------------------------------------
def readfile(path, type='excel'):
    if type == 'excel':
        filename = re.match(r'^([0-9a-zA-Z/:_.\u4e00-\u9fa5]+)\\'  # 父文件夹
                                r'([0-9a-zA-Z]+)_([0-9a-zA-Z]+)_([a-z]+)_([0-9]?.xls|xlsx)$', path)  # 文件名
        CarName = filename.group(2)
        TestName = filename.group(3)
        DriverName = filename.group(4)
        print('Start Transform ' + DriverName + filename.group(5) + ' data.')
        bk = xlrd.open_workbook(path)
        shxrange = range(bk.nsheets)
        try:
            sh = bk.sheet_by_index(0)
        except:
            pass

        nrows = sh.nrows  # 获取行数
        ncols = sh.ncols  # 获取列数
        # print("nrows %d, ncols %d" % (nrows, ncols))
        initial_field = sh.row_values(14)  # 原始字段，供查找
        row_list = []  # 获取各行数据
        for j in range(17, nrows):  # 数据行的起点
            row_data = sh.row_values(j)
            row_list.append(row_data)
        row_array = np.array(row_list)  # 转换为 ndarray 格式

    elif type == 'csv':
        filename = re.match(r'^([0-9a-zA-Z/:_.\u4e00-\u9fa5]+)\\'  # 父文件夹
                                r'([0-9a-zA-Z]+)_([0-9a-zA-Z]+)_([0-9a-zA-Z]+)_([0-9]+)_([0-9]+).(csv)$', path)  # 文件名
        CarName = filename.group(2)
        TestName = filename.group(3)
        DriverName = filename.group(4)
        Testid_com = filename.group(6)
        csvdata = pd.read_csv(path)
        row_array = np.array(csvdata)
        initial_field = csvdata.columns.tolist()

    elif type == 'txt':
        filename = re.match(r'^([0-9a-zA-Z/:_.\u4e00-\u9fa5]+)\\'  # 父文件夹
                                r'([0-9a-zA-Z]+)_([0-9a-zA-Z]+)_([a-z]+)_([0-9]+)_([0-9]+).(txt)$', path)  # 文件名
        CarName = filename.group(2)
        TestName = filename.group(3)
        DriverName = filename.group(4)
        Testid_com = filename.group(6)
        # print('Start Transform ' + DriverName + filename.group(5) + ' data.')

        with open(path, 'r') as file_to_read:
            table = pd.read_table(file_to_read, sep='\t', header=12, index_col=False)  # 12行为表头，自动删除空行
            table.drop([0, 1], axis=0, inplace=True)
            row_array = np.array(table.iloc[:, 0:-1])  # 最后一列去掉
            initial_field = table.columns.tolist()[0:-1]
    return row_array, CarName, TestName, DriverName, initial_field, Testid_com, \
            [DriverName + filename.group(5) + ' data']


def readfile_new(path, type='csv'):
    if type == 'csv':
        filename = re.match(r'^([0-9a-zA-Z/:_.\u4e00-\u9fa5]+)/'  # 父文件夹
                                r'([0-9a-zA-Z]+)_([0-9a-zA-Z]+)_([a-zA-Z]+)_([a-zA-Z]+)_'
                                r'([0-9]+)_([a-zA-Z]+).(csv)$', path)  # 文件名
        CarName = filename.group(2)
        VINCode = filename.group(3)
        TestGroup = filename.group(4)
        TestName = filename.group(5)
        TestTime = filename.group(6)
        Operator = filename.group(7)

        csvdata = pd.read_csv(path)
        row_array = np.array(csvdata)
        initial_field = csvdata.columns.tolist()

    return initial_field


def id_to_name(data, path='Driver_index.csv', mode='r'):
    Dri_csv_Refer = open(path, mode)
    csvreader = csv.reader(Dri_csv_Refer)
    Dri_index_csv = []
    Dri_name = []
    for rows in csvreader:
        Dri_index_csv.append(rows)  # 驾驶员姓名索引
    Dri = pd.DataFrame(Dri_index_csv[1:], columns=Dri_index_csv[0])
    for i in range(len(data)):
        if int(data[i, 0]):  # 驾驶员ID非零
            Dri_name.append(Dri[Dri['DriverID'] == str(int(data[i, 0]))].iloc[0][1])
        else:
            Dri_name.append('Unknown')
    OutPut = np.concatenate((data, np.matrix(Dri_name).T), 1)
    return OutPut


def dropDupli(data):
    del_index = []
    for i in range(1, data.shape[0], 1):  # 从第三行开始循环
        for j in range(i + 1, data.shape[0], 1):
            delta = abs(data[j, 16:20:1].astype(float) - data[i, 16:20:1].astype(float))
            if delta.sum() < 0.01:
                del_index.append(i)
                break
    return np.delete(data, del_index, axis=0)


# ------------------------------ API ----------------------------------------

def static_map_request_url(Gps, step=400, pic_size=[500, 500]):
    url = 'http://restapi.amap.com/v3/staticmap?&' + 'size=' + str(pic_size[0]) + '*' + str(
        pic_size[1]) + '&paths=3,0xFF0000,1,,:'
    l = len(Gps)
    resampling = int(l / step)
    for i in range(resampling):
        Gps_fix = GPS_FIX_WGS84(Gps[i * step][0], Gps[i * step][1])
        if Gps_fix != [0, 0]:
            url = url + str(Gps_fix[0]) + ',' + str(Gps_fix[1]) + ';'

    Gps_fix = GPS_FIX_WGS84(Gps[-1][0], Gps[-1][1])  # 补最后一个点
    url = url + str(Gps_fix[0]) + ',' + str(Gps_fix[1])
    url = url + '&key=42f165dabcfcb28c1c0290058adee399'

    # Example
    # http: // restapi.amap.com / v3 / staticmap?zoom = 12
    # & size = 500 * 500 & paths = 10, 0x0000ff, 1,,:116.31604, 39.96491;
    # 116.320816, 39.966606;
    # 116.321785, 39.966827;
    # 116.32361, 39.9687;
    # 116.32361, 39.9684;
    # 116.32371, 39.969 & key = 42f165dabcfcb28c1c0290058adee399

    return url


# --------------------------- Main Function ---------------------------------


def read_file(file_path, DBC_index, Car_index, Driver_index, type='txt'):

    DBC_csv_Refer = open(DBC_index, 'r')
    csvreader = csv.reader(DBC_csv_Refer)
    DBC_field_csv = []
    for rows in csvreader:
        DBC_field_csv.append(rows)  # DBC定义的变量名

    Dri_csv_Refer = open(Driver_index, 'r')
    csvreader = csv.reader(Dri_csv_Refer)
    Dri_index_csv = []
    for rows in csvreader:
        Dri_index_csv.append(rows)  # 驾驶员姓名索引

    Car_csv_Refer = open(Car_index, 'r')
    csvreader = csv.reader(Car_csv_Refer)
    Car_index_csv = []
    for rows in csvreader:
        Car_index_csv.append(rows)  # 车辆索引

    path_list = glob.glob(file_path)  # 获取文件目录下所有的 .xls 文件
    Travel_ID = 0

    for i in path_list:
        row_array, CarName, TestName, DriverName, initial_field, Testid_com, message = readfile(i, type)
        DriverID = 0
        CarID = 0
        if int(Testid_com) == 1:
            Travel_ID = Travel_ID + 1

        for m in Dri_index_csv:
            if DriverName == m[1]:
                DriverID = m[0]
                break

        for m in Car_index_csv:
            if CarName == m[1]:
                CarID = m[0]
                break

        Intest_field = np.array(
            ['Travel_ID', 'Driver_ID', 'Car_ID', 'Data_ID', 'Date', 'Time', 'Longitude', 'Latitude', 'Altitude',
             'Direction', 'GPS_Vspd', 'X_acc', 'Y_acc', 'Z_acc', 'Tempeature', 'Box_odo', 'Alarm_spd'])  # Intest表头

        data_zeros = np.matrix(np.zeros(row_array.shape[0])).T
        data_TravelID = data_zeros.copy()
        data_TravelID[data_TravelID == 0] = Travel_ID
        data_driID = data_zeros.copy()
        data_driID[data_driID == 0] = DriverID
        data_car = data_zeros.copy()
        data_car[data_car == 0] = CarID
        data_null = data_zeros.copy()
        data_null[data_null == 0] = np.nan

        Intest_data = np.concatenate((data_TravelID, data_driID, data_car, row_array[:, 0:14]), axis=1)
        Intest_table_total = np.concatenate((np.matrix(Intest_field), Intest_data), axis=0)

        DBC_data = np.concatenate((data_zeros, data_zeros), axis=1)
        for Field_ID in DBC_field_csv:
            for field_id in Field_ID:
                try:
                    field_index_ = initial_field.index(field_id)
                    # kk = np.matrix(row_array[:, field_index_])
                    DBC_data = np.concatenate((DBC_data, np.matrix(row_array[:, field_index_]).T), axis=1)
                    break
                except ValueError as e:
                    pass
                if field_id == Field_ID[-1]:
                    # kkkk = np.array(data_null).tolist()
                    DBC_data = np.concatenate((DBC_data, np.array(data_null)), axis=1)

        DBC_data = sp.delete(DBC_data, 0, 1)
        DBC_data = sp.delete(DBC_data, 0, 1)
        DBC_field = np.matrix(DBC_field_csv)[:, 0]
        DBC_table_total = np.concatenate((DBC_field.T, DBC_data), axis=0)
        Total_table = np.concatenate((Intest_table_total, DBC_table_total), axis=1)
        Combine_file_name = CarName + '_' + TestName + '_data.csv'
        csvfile = open(Combine_file_name, 'a', newline='')  # 改成追加了 ‘a‘
        # reference "C:\Users\Lu\Desktop\AS24\python学习\CSV写入存在空行问题.pdf"
        csvwriter = csv.writer(csvfile)
        if i == path_list[0]:
            csvwriter.writerows(Total_table.tolist())
        else:
            del_head = Total_table.tolist()
            del_head.pop(0)
            csvwriter.writerows(del_head)
        yield message, path_list.__len__(), Combine_file_name


def data_process(file_path, save_name):
    # --------------------------- Main Scripts  -------------------------------
    data_file_name = file_path
    # data_file_name = "C:/Users/Lu/Desktop/驾驶行为工作/PYProject\\ZS11_Standard_data.csv"
    # data_file_name = "E:/驾驶行为工作/PYProject\\ZS11_Standard_data.csv"
    filename = re.match(r'^([0-9a-zA-Z/:_.\u4e00-\u9fa5]+)/'  # 父文件夹 相对路径
                        r'([0-9a-zA-Z]+)_([0-9a-zA-Z]+)_([a-z]+.csv)$', data_file_name)  # 文件名
    CarName = filename.group(2)
    csvdata = pd.read_csv(data_file_name)

    Target_Driver_Date_ful = csvdata.loc[:, ['Driver_ID', 'Date', 'Travel_ID']]
    Target_Driver_Date = Target_Driver_Date_ful.drop_duplicates()

    resultarray = []
    backup_data = []

    # print('DriverID', 'Date', 'TravelID')

    for i in range(Target_Driver_Date.shape[0]):  # 样本数据个数
        DriverID = Target_Driver_Date.iloc[i][0]
        Date = Target_Driver_Date.iloc[i][1]
        TravelID = Target_Driver_Date.iloc[i][2]
        Target_Driver = csvdata[(csvdata['Travel_ID'] == TravelID)]  # 筛出的样本集

        Time_index_start = Target_Driver['Time'].iloc[0]  # 标记开始时间
        # Target_Driver = ignore_charging(Target_Driver)
        try:
            charge_pos = ((Target_Driver['ElecVehSysMd'] == 8).tolist()).index(True)  # 找不到充电会出错
            Target_Driver = Target_Driver.iloc[0:charge_pos]  # 充电后的都不要，防止末电量出错
        except ValueError as ve:
            pass

        Target_Driver.drop(Target_Driver[(Target_Driver['ElecVehSysMd'] == 8) |
                                         (Target_Driver['BMSPackSOC'] == float(0))].index, axis=0, inplace=True)
        # Target_Driver.drop(Target_Driver[(Target_Driver['EPTDrvngMdSwSts'] == 0) |
        #                                  (Target_Driver['EPTDrvngMdSwSts'] == 2)].index, axis=0, inplace=True)
        Target_Driver = Target_Driver[Target_Driver['EPTDrvngMdSwSts'] == 1]
        # 删掉充电阶段的数据以及电量异常的数据，只取得N模式的数据（Eco\Normal\Sport）

        if Target_Driver.shape[0] > 1000:  # 太短的样本选择丢弃

            Fuel_Csump = Target_Driver['Fuel_Csump'].tolist()
            # X_acc = Target_Driver['X_acc'].tolist()
            vspd = five_points_avg(Target_Driver['Veh_Spd_NonDrvn'].tolist())
            Strg_Whl_Ang = Target_Driver['Strg_Whl_Ang'].tolist()
            str_multi_vspd = Target_Driver['Veh_Spd_NonDrvn'] * Target_Driver['Strg_Whl_Ang']
            acc_ped = Target_Driver['Acc_Actu_Pos'].tolist()
            L_Dir_lamp = Target_Driver['L_Dir_lamp'].tolist()
            R_Dir_lamp = Target_Driver['R_Dir_lamp'].tolist()
            VSE_Longt_Acc = (Target_Driver['VSE_Longt_Acc'] / 9.8).tolist()
            time = range(len(Fuel_Csump))
            X_acc = five_points_avg_acc(vspd)
            Y_acc = Target_Driver['Y_acc'].tolist()

            # longitude, latitude = GPS_fix(Target_Driver['Longitude'], Target_Driver['Latitude'])
            # ang_abs, ang_delta = heading_angle(list(longitude), list(latitude))
            # ang = heading_angle_cal(list(longitude), list(latitude))
            # turn_lab = turnning_cal(ang)

            # ------------------- Style features ---------------------
            odemeter = odemeter_cal(vspd)
            fuel_cons = fuel_cal(Fuel_Csump) / odemeter * 100  # L/100km
            # overtake_times = overtake_cal(turn_lab, ang_abs, np.array(Strg_Whl_Ang), np.array(vspd))  # 计算速度还是太低 AS24跑不动
            overtake_times = 0
            brake_skill_score = brake_skill(VSE_Longt_Acc, vspd)
            sudden_acc_times = sudden_acc(X_acc, vspd, CarName)
            sudden_brake_times = sudden_brake(X_acc, CarName)
            sudden_steering_times = sudden_steering(Y_acc, CarName)
            tip_in_times = tip_in(acc_ped)
            over_speed_propotion = over_speed_cal(Target_Driver, vspd)

            # ----------------- Statistics features ------------------
            soc_start = Target_Driver['BMSPackSOC'].tolist()[0]
            soc_end = Target_Driver['BMSPackSOC'].tolist()[-1]
            soc_balance_ratio = soc_balance_time_ratio(Target_Driver['BMSPackSOC'])
            mean_spd = np.mean(vspd)
            std_spd = np.std(vspd)
            mean_Strg_Whl_Ang = np.mean(Strg_Whl_Ang)
            std_Strg_Whl_Ang = np.std(Strg_Whl_Ang)
            mean_Strg_Whl_Ang_pos = Target_Driver[Target_Driver['Strg_Whl_Ang'] > 0].Strg_Whl_Ang.mean()
            mean_Strg_Whl_Ang_neg = Target_Driver[Target_Driver['Strg_Whl_Ang'] < 0].Strg_Whl_Ang.mean()
            mean_X_acc = np.mean(X_acc)
            std_X_acc = np.std(X_acc)
            mean_X_acc_pos = np.array(X_acc)[np.array(X_acc) > 0].mean()
            mean_X_acc_neg = np.array(X_acc)[np.array(X_acc) < 0].mean()
            mean_acc_ped = np.mean(acc_ped)
            std_acc_ped = np.std(acc_ped)

            print(DriverID, Date, TravelID, '....finish')

            sudden_acc_score = (sudden_acc_times[0] + sudden_acc_times[1] * 3 + sudden_acc_times[2] * 7) / odemeter
            sudden_brake_score = (sudden_brake_times[0] + sudden_brake_times[1] * 3 + sudden_brake_times[
                2] * 7) / odemeter
            sudden_steering_score = (sudden_steering_times[0] + sudden_steering_times[1] * 3 + sudden_steering_times[
                2] * 7) / odemeter

            sudden_acc_times = np.array(sudden_acc_times) / odemeter
            sudden_brake_times = np.array(sudden_brake_times) / odemeter
            sudden_steering_times = np.array(sudden_steering_times) / odemeter

            DriverID = int(DriverID)
            Date = date_reverse(int(Date))

            resultarray.append([DriverID, Date, Time_index_start, brake_skill_score, sudden_acc_score,
                                sudden_brake_score, sudden_steering_score, overtake_times / odemeter])
            backup_data.append([TravelID, sudden_acc_times[0], sudden_acc_times[1], sudden_acc_times[2],
                                sudden_brake_times[0], sudden_brake_times[1], sudden_brake_times[2],
                                sudden_steering_times[0], sudden_steering_times[1], sudden_steering_times[2],
                                brake_skill_score, overtake_times / odemeter, tip_in_times[0] / odemeter,
                                odemeter, mean_spd, mean_Strg_Whl_Ang, mean_Strg_Whl_Ang_pos, mean_Strg_Whl_Ang_neg,
                                mean_X_acc, mean_X_acc_pos, mean_X_acc_neg, mean_acc_ped,
                                std_spd, std_Strg_Whl_Ang, std_X_acc, std_acc_ped, over_speed_propotion,
                                fuel_cons, soc_balance_ratio, soc_start, soc_end])

            rq = requests.get(static_map_request_url(Target_Driver[['Longitude', 'Latitude']].values.tolist()))
            file = open('./RoutinePic/' + str(CarName) + '_' + str(DriverID) + '_' + str(Date) + '_' +
                        str(int(Time_index_start)) + '.png', 'wb')
            file.write(rq.content)
            file.close()
        else:
            print(DriverID, Date, TravelID, '....Poor data to analyse')

    resultarray = np.array(resultarray)
    output_array = id_to_name(resultarray[:, 0:3])
    output_array = np.concatenate((output_array, backup_data), axis=1)
    field_name = np.array(['DriveID', 'Date', 'Time_start', 'Name',
                           'TravelID', 'SoftAcc', 'MidAcc', 'RadiAcc', 'SoftBrk', 'MidBrk',
                           'RadiBrk', 'SoftStr', 'MidStr', 'RadiStr', 'BrkSkill', 'OverTake', 'Tip_in', 'Odemeter',
                           'MeanSpd', 'Mean_Str_Whl_Ang', 'Mean_Str_Whl_Ang_Pos', 'Mean_Str_Whl_Ang_Neg',
                           'Mean_X_acc', 'Mean_X_acc_Pos', 'Mean_X_acc_Neg', 'Mean_acc_ped',
                           'Std_spd', 'Std_Strg_Whl_Ang', 'Std_X_acc', 'Std_acc_ped', 'OverSpeed_ratio',
                           'FuelCons', 'Soc_balance_ratio', 'Soc_start', 'Soc_end'])
    output_array = np.concatenate((np.matrix(field_name), output_array))
    output_array = dropDupli(output_array)
    save_name = save_name + '.csv'
    pd.DataFrame(output_array).to_csv(save_name, header=False, index=False, mode='a')
    # (pd.DataFrame(output_array).drop_duplicates()).to_csv('Drive_score.csv', header=None, index=None)
    return output_array.tolist()


def store_result(file_path, filename, store_data):
    os.chdir(file_path)
    outputfile = open(filename+'.pkl', 'wb')
    pickle.dump(store_data, outputfile)
    outputfile.close()
    return


def reload_result(file_path, file_name):
    # if len(file_path) > 2:
    os.chdir(file_path)
    inputfile = open(file_name, 'rb')
    data_reload = pickle.load(inputfile)
    inputfile.close()
    return data_reload

