import os
import pandas as pd
import numpy as np
from scipy.integrate import cumulative_trapezoid, trapz, cumtrapz

# from scipy.signal import medfilt
from scipy.signal import butter, lfilter, filtfilt
import sys
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings("ignore")


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
    # print("avg_sr", sampling_rate)
    return time_diffs, sampling_rate


def get_data(file):
    # loc = args["data_loc"]

    try:
        data = pd.read_excel(file)
    except:
        try:
            data = pd.read_csv(file)
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
    # print("data", data.shape)
    # print("data col", data.columns)
    _, sr = get_sampling_rate(data)
    # print("sr", sr)
    accel_data = data[["AccelerationX", "AccelerationY", "AccelerationZ"]]
    # print(accel_data.shape)
    # filtered_data = butter_lowpass_filter(accel_data, 50, 97, 6)
    accel_data = np.array(accel_data)
    # filtered_data = butter_highpass_filter(accel_data, 0.05, 97)
    # accel_data = filtered_data
    accel_magnitude = np.linalg.norm(accel_data, axis=1)
    # max = np.max(accel_magnitude)
    # print("max", max)
    # threshold = max / 2
    # print("threshold", threshold)
    # threshold = 0.01
    # print(threshold)
    # print(np.max(accel_magnitude))

    return accel_data


def to_pace_time(pace):
    tempPace = pace
    tempPace = tempPace * 2.23694
    if tempPace == 0:
        tempPace = 0.0001
    tempPace = tempPace * 2.23694
    tempPace = 60 / tempPace
    return tempPace


def process_windows(accel_data):
    v = []
    accel_data = np.array(accel_data)
    sr = 25
    dt = 1.0 / sr
    magnitude = np.linalg.norm(accel_data, axis=1)

    # 2. Optional: smooth the signal (moving average filter)
    window_size = int(0.1 * sr)  # 200 ms window
    smooth_magnitude = np.convolve(
        magnitude, np.ones(window_size) / window_size, mode="same"
    )

    # 3. Find peaks (each peak = 1 step)
    peaks, _ = find_peaks(smooth_magnitude, distance=sr*0.25, height=1.65*np.mean(smooth_magnitude))
    # indices = np.arange(0, accel_data.shape[0], 1)
    indices = peaks
    # indices.insert(0, 0)
    for i in range(0, len(indices) - 1, 1):
        start_idx = indices[i]
        end_idx = indices[i + 1]

        accel_win = accel_data[start_idx:end_idx, :]
        # print("accel_win shape", accel_win.shape)
        #         if accel_win.shape[0] <= 2 or end_idx >= len(accel_data):
        #             continue
        # print(end_idx)
        # print(start_idx)
        # dt = (end_idx - start_idx) / 25
        dt = (end_idx - start_idx) /25
        # Calculate the speed (magnitude of velocity)
        speed_x = cumtrapz(accel_win[:, 0], dx=dt, initial=0)[-1]
        speed_y = cumtrapz(accel_win[:, 1], dx=dt, initial=0)[-1]
        speed_z = cumtrapz(accel_win[:, 2], dx=dt, initial=0)[-1]
        # speed_x = np.abs(speed_x)
        # speed_y = np.abs(speed_y)
        # speed_z = np.abs(speed_z)

        # Combine the velocity components to get the speed at each point
        speed_magnitude = np.sqrt(speed_x**2 + speed_y**2 + speed_z**2)
        # print("speed magnitude", speed_magnitude)
        # The cumulative speed (total distance traveled) would be the final value of the magnitude
        


        v.append(speed_magnitude)
    # print(v_x)
    # print(v_y)
    if len(v) == 0:
        speed = 0
    else:
        v = np.array(v)
        # v_x = v_x[np.where(v_x > np.median(v_x))]

        # print("max", np.max(v))
        # print("min", np.min(v))
        # print("med", np.median(v))
        # print(v_x)
        speed = np.average(v)

    return round(speed, 5)


def predict(file):
    # args = {
    #     "data_loc": filename
    #     # "data_loc": "data/general_phone.csv"
    # }
    accel_data = get_data(file)
    speed = process_windows(accel_data)
    return speed


if __name__ == "__main__":
    """
    Usage:
        python split_csv_into_windows.py <path_to_your_CSV_file> [lines_per_window]

    Example:
        python split_csv_into_windows.py motion_data.csv 6000
    """

    # input_csv_file = sys.argv[1]
    for file in os.listdir("../split_csv_files_still"):
        print(file)
        spx = predict("../split_csv_files_still/" + file)
        print("min per mile", to_pace_time(spx))
        print(" -- - -- - -- - ")
