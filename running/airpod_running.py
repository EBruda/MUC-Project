import os
import pandas as pd
import numpy as np
from scipy.integrate import cumulative_trapezoid, trapz
from scipy.signal import medfilt
from scipy.signal import butter, lfilter, filtfilt


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    return b, a


def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y


def butter_highpass_filter(data, cutoff, fs, order=4):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype="high", analog=False)
    # Apply filtering to each column separately
    filtered_data = np.zeros_like(data)
    for i in range(data.shape[1]):  # Iterate over each axis (X, Y, Z)
        filtered_data[:, i] = filtfilt(b, a, data[:, i])

    return filtered_data


def get_sampling_rate(df):
    df = pd.DataFrame(df)

    df = df.sort_values(by="Timestamp")

    time_diffs = df["Timestamp"].diff()
    time_diffs = time_diffs[time_diffs > 0]

    avg_sampling_interval = time_diffs.mean()
    sampling_rate = 1 / avg_sampling_interval
    return time_diffs, sampling_rate


def get_data(args):
    loc = args["data_loc"]

    try:
        data = pd.read_excel(loc)
    except:
        try:
            data = pd.read_csv(loc)
        except Exception as e:
            raise e
    data.columns = [
        "Timestamp",
        "QuaternionX",
        "QuaternionY",
        "QuaternionZ",
        "QuaternionW",
        "AttitudePitch",
        "AttitudeRoll",
        "AttitudeYaw",
        "GravitationalAccelerationX",
        "GravitationalAccelerationY",
        "GravitationalAccelerationZ",
        "AccelerationX",
        "AccelerationY",
        "AccelerationZ",
        "RotationX",
        "RotationY",
        "RotationZ",
    ]
    print("data", data.shape)
    print("data col", data.columns)
    # _, sr = get_sampling_rate(data)
    # print("sr", sr)
    accel_data = data[["AccelerationX", "AccelerationY", "AccelerationZ"]]
    print(accel_data.shape)
    # filtered_data = butter_lowpass_filter(accel_data, 50, 97, 6)
    accel_data = np.array(accel_data)
    # filtered_data = butter_highpass_filter(accel_data, 0.05, 97)
    # accel_data = filtered_data
    accel_magnitude = np.linalg.norm(accel_data, axis=1)
    max = np.max(accel_magnitude)
    print(max)
    # threshold = max / 2.5
    threshold = 0.01
    print(threshold)
    print(np.max(accel_magnitude))
    indices = np.array(np.where(accel_magnitude > threshold))
    print("indices", indices.shape)
    indices = indices[0]
    return accel_data, indices


def process_windows(accel_data, indices):
    v_x = []
    v_y = []
    accel_data = np.array(accel_data)

    indices = list(indices)
    # if (indices[0] != 0):
    #     indices.insert(0, 0)
    speed_in_x_direction = 0
    speed_in_y_direction = 0
    indices.insert(0, 0)
    for i in range(0, len(indices) - 1, 1):
        start_idx = indices[i]
        end_idx = indices[i + 1]

        accel_win = accel_data[start_idx:end_idx, :]
        if accel_win.shape[0] <= 2 or end_idx >= len(accel_data):
            continue

        integral_linear_accel_x = cumulative_trapezoid(accel_win[0], axis=0, initial=0)[
            -1
        ]
        integral_linear_accel_y = cumulative_trapezoid(accel_win[1], axis=0, initial=0)[
            -1
        ]
        v_x.append(abs(integral_linear_accel_x))
        v_y.append(abs(integral_linear_accel_y))
    print(v_x)
    print(v_y)
    if (len(v_x) == 0):
        speed_in_x_direction = 0
        speed_in_y_direction = 0
    else:
        speed_in_x_direction = np.average(v_x)
        speed_in_y_direction = np.average(v_y)
        if speed_in_x_direction <= 0.16536719117642723:
            speed_in_x_direction = 0
        if speed_in_y_direction <= 0.11953063780577095:
            speed_in_y_direction = 0
        speed_in_x_direction = speed_in_x_direction * 2
        speed_in_y_direction = speed_in_y_direction * 2
    print(speed_in_x_direction, "m/s")
    print(speed_in_y_direction, "m/s")

    return speed_in_x_direction, speed_in_y_direction


def predict(filename):
    args = {
        "data_loc": filename
        # "data_loc": "data/general_phone.csv"
    }
    accel_data, indices = get_data(args)
    spx, spy = process_windows(accel_data, indices)
    return spx, spy
