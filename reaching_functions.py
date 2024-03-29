import numpy as np
import pandas as pd
from scipy import signal as sgn
import ctypes

import os


def write_header(r, vision, subID, day):
    # First check whether Practice folder exists. If not, create it

    # print(vision)
    # if vision == 'max':
    #     group = "CompleteVision"
    # elif vision == 'min':
    #     group = "MinimalVision"

    data_path = (r.path_log + "/" + vision + "/" + str(subID) + "/")
    if not os.path.exists(data_path):
        os.mkdir(data_path)

    data_file = data_path + "ResultsLogDay" + str(day) + ".txt"
    if os.path.exists(data_file):
        ctypes.windll.user32.MessageBoxW(0, "Overwrite is about to occur. Please make sure to check file names.", \
                                         "Overwrite File Protection", 2)
        exit()

    header = "time\treach_time\twrist_x\twrist_y\tthumb_cmc_x\tthumb_cmc_y\tthumb_mcp_x\tthumb_mcp_y\tthumb_ip_x\tthump_ip_y\t"\
             "thumb_tip_x\tthumb_tip_y\tindex_finger_mcp_x\tindex_finger_mcp_y\tindex_finger_pip_x\tindex_finger_pip_y"\
             "\tindex_finger_dip_x\tindex_finger_dip_y\tindex_finger_tip_x\tindex_finger_tip_y\tmiddle_finger_mcp_x\t"\
             "middle_finger_mcp_y\tmiddle_finger_pip_x\tmiddle_finger_pip_y\tmiddle_finger_dip_x\tmiddle_finger_dip_y"\
             "\tmiddle_finger_tip_x\tmiddle_finger_tip_y\tring_finger_mcp_x\tring_finger_mcp_y\tring_finger_pip_x\t"\
             "ring_finger_pip_y\tring_finger_dip_x\tring_finger_dip_y\tring_finger_tip_x\tring_finger_tip_y\t" \
             "pinky_mcp_x\tpinky_mcp_y\tpinky_pip_x\tpinky_pip_y\tpinky_dip_x\tpinky_dip_y\tpinky_tip_x\tpinky_tip_y\t"\
             "theta1\ttheta2\ttheta3\tomega1\tomega2\tomega3\tcursor_x\tcursor_y\ttarget\ttrial\tstate\tcomeback" \
             "\tat_home\tscore\tdistance\treach\n"
    with open(data_path + "ResultsLogDay" + str(day) + ".txt", "w+") as file_log:
        file_log.write(header)


def initialize_targets(r):
    """
    function that initializes list for target positions (x and y)
    :param r: object of the class Reaching. Use the class to change parameters of the reaching task
    :return:
    """
    r.empty_tgt_x_list()
    r.empty_tgt_y_list()
    for i in r.list_tgt:
        r.tgt_x_list.append(
            (r.width / 2) + r.tgt_dist * np.cos(i * np.pi / 4))
        r.tgt_y_list.append(
            (r.height / 2) + r.tgt_dist * np.sin(i * np.pi/4))


def set_target_reaching_customization(r):
    """
    set position of current targ
    :return:
    """
    if r.comeback == 0:
        r.tgt_x = r.tgt_x_list[r.list_tgt[r.trial - 1]]
        r.tgt_y = r.tgt_y_list[r.list_tgt[r.trial - 1]]
    else:
        # When returning to home target visual feedback is restored
        r.is_blind = 0
        r.tgt_x = r.width / 2
        r.tgt_y = r.height / 2  # Center of the screen


def set_target_reaching(r):
    """
    set position of current targ
    :return:
    """
    if r.comeback == 0:
        r.tgt_x = r.tgt_x_list[r.list_tgt[r.trial - 1]]
        r.tgt_y = r.tgt_y_list[r.list_tgt[r.trial - 1]]
        r.target = r.list_tgt[r.trial - 1]
    else:
        # When returning to home target visual feedback is restored
        r.is_blind = 0
        r.tgt_x = r.width / 2
        r.tgt_y = r.height / 2  # Center of the screen


def filter_cursor(r, filter_curs):

    filter_curs.update_cursor(r.crs_x, 0)
    filter_curs.update_cursor(r.crs_y, 1)

    return filter_curs.filtered_value[0], filter_curs.filtered_value[1]

def filter_links(r, filter_curs):

    filter_curs.update_cursor(r.crs_x, 0)
    filter_curs.update_cursor(r.crs_y, 1)
    filter_curs.update_cursor(r.crs_z, 2)

    return filter_curs.filtered_value[0], filter_curs.filtered_value[1], filter_curs.filtered_value[2]


def update_cursor_position_custom(body, map, rot, scale, off):

    if type(map) != tuple:
        cu = np.dot(body, map)
    else:
        h = np.tanh(np.dot(body, map[0][0]) + map[1][0])
        h = np.tanh(np.dot(h, map[0][1]) + map[1][1])
        cu = np.dot(h, map[0][2]) + map[1][2]

    # Applying rotation
    cu[0] = cu[0] * np.cos(np.pi / 180 * rot) - cu[1] * np.sin(np.pi / 180 * rot)
    cu[1] = cu[0] * np.sin(np.pi / 180 * rot) + cu[1] * np.cos(np.pi / 180 * rot)

    # Applying scale
    cu = cu * scale

    # Applying offset
    cu = cu + off

    return cu[0], cu[1]

def update_cursor_position_custom_3links(body, map, rot, scale, off):

    if type(map) != tuple:
        cu = np.dot(body, map)
    else:
        h = np.tanh(np.dot(body, map[0][0]) + map[1][0])
        h = np.tanh(np.dot(h, map[0][1]) + map[1][1])
        cu = np.dot(h, map[0][2]) + map[1][2]

    # Applying rotation
    cu[0] = cu[0] * np.cos(np.pi / 180 * rot) - cu[1] * np.sin(np.pi / 180 * rot)
    cu[1] = cu[0] * np.sin(np.pi / 180 * rot) + cu[1] * np.cos(np.pi / 180 * rot)

    # Applying scale
    cu = cu * scale

    # Applying offset
    cu = cu + off

    return cu[0], cu[1], cu[2]

## add cu[2]


def update_cursor_position(body, map, rot_ae, scale_ae, off_ae, rot_custom, scale_custom, off_custom):

    if type(map) != tuple:
        cu = np.dot(body, map)
    else:
        h = np.tanh(np.dot(body, map[0][0]) + map[1][0])
        h = np.tanh(np.dot(h, map[0][1]) + map[1][1])
        cu = np.dot(h, map[0][2]) + map[1][2]

    # Applying rotation, scale and offset computed after AE training
    # cu[0] = cu[0] * np.cos(np.pi / 180 * rot_ae) - cu[1] * np.sin(np.pi / 180 * rot_ae)
    # cu[1] = cu[0] * np.sin(np.pi / 180 * rot_ae) + cu[1] * np.cos(np.pi / 180 * rot_ae)
    cu = cu * scale_ae
    cu = cu + off_ae

    # Applying rotation, scale and offset computed after customization
    # cu[0] = cu[0] * np.cos(np.pi / 180 * rot_custom) - cu[1] * np.sin(np.pi / 180 * rot_custom)
    # cu[1] = cu[0] * np.sin(np.pi / 180 * rot_custom) + cu[1] * np.cos(np.pi / 180 * rot_custom)
    cu = cu * scale_custom
    cu = cu + off_custom

    return cu[0], cu[1]

def update_degrees(body, map, rot_ae, scale_ae, off_ae, rot_custom, scale_custom, off_custom):

    if type(map) != tuple:
        dg = np.dot(body, map)
    else:
        h = np.tanh(np.dot(body, map[0][0]) + map[1][0])
        h = np.tanh(np.dot(h, map[0][1]) + map[1][1])
        dg = np.dot(h, map[0][2]) + map[1][2]

    # Applying rotation, scale and offset computed after AE training
    # cu[0] = cu[0] * np.cos(np.pi / 180 * rot_ae) - cu[1] * np.sin(np.pi / 180 * rot_ae)
    # cu[1] = cu[0] * np.sin(np.pi / 180 * rot_ae) + cu[1] * np.cos(np.pi / 180 * rot_ae)
    dg = dg * scale_ae
    dg = dg + off_ae

    # Applying rotation, scale and offset computed after customization
    # cu[0] = cu[0] * np.cos(np.pi / 180 * rot_custom) - cu[1] * np.sin(np.pi / 180 * rot_custom)
    # cu[1] = cu[0] * np.sin(np.pi / 180 * rot_custom) + cu[1] * np.cos(np.pi / 180 * rot_custom)
    dg = dg * scale_custom
    dg = dg + off_custom

    return dg[0], dg[1], dg[2]


def write_practice_files(r, body, timer_practice):

    log = str(timer_practice.elapsed_time) + "\t" + str(r.reach_time) + '\t'.join(map(str, body)) + "\t" + str(r.theta1) + "\t" + \
          str(r.theta2) + "\t" + str(r.theta3) + "\t" + str(r.crs_x) + "\t" + \
          str(r.crs_y) + "\t" + str(r.crs_z) + "\t" + str(r.crs_anchor_x) + "\t" + str(r.crs_anchor_y) + "\t" + \
          str(r.block) + "\t" + str(r.repetition) + "\t" + \
          str(r.target) + "\t" + str(r.trial) + "\t" + str(r.state) + "\t" + str(r.comeback) + "\t" +\
          "\t" + str(r.at_home) + "\t" + "\t" + str(r.score) + "\n"

    if r.is_vision == 1:
        group = "CompleteVision"
    else:
        group = "MinimalVision"

    data_path = (r.path_log + "/" + group + "/" + str(r.subject_id) + "/")

    with open(data_path + "PracticeLog" + r.day + ".txt", "a") as file_log:
        file_log.write(log)


def check_target_reaching(r, timer_enter_tgt):
    """
    Check if cursor is inside the target
    """
    dist = np.sqrt((r.crs_x - r.tgt_x) ** 2 + (r.crs_y - r.tgt_y) ** 2)
    # If you are not in a blind trial
    if r.is_blind == 0:
        if dist < r.tgt_radius:
            # if cursor is inside the target: start the timer that will count for how long the cursor will stay in the
            # target, then change status (INSIDE target)
            if r.state == 0 or r.state == 1:
                timer_enter_tgt.start()
            r.state = 2
        # if cursor is inside the target (or if it used to be but currently is not) then go back at state 0
        # (OUT OF target, IN TIME) and reset timer
        else:
            r.state = 0
            # timer_enter_tgt.reset()  # Stops time interval measurement and resets the elapsed time to zero.
            timer_enter_tgt.start()

    # If blind trial -> stopping criterion is different
    # (cursor has to remain in a specific region for 2000 ms (50 Hz -> count_mouse == 100)
    else:
        if (r.old_crs_x + 10 > r.crs_x > r.old_crs_x - 10 and
                r.old_crs_y + 10 > r.crs_y > r.old_crs_y - 10 and r.at_home == 0):
            r.count_mouse += 1
        else:
            r.count_mouse = 0

    # Check here if the cursor is in the home target. In this case modify at_home to turn on/off the visual feedback
    # if the corresponding checkbox is selected
    if (r.repetition > 5 and
            (r.block == 2 or r.block == 3 or r.block == 4 or r.block == 5 or
             r.block == 7 or r.block == 8 or r.block == 9 or r.block == 10)):
        if (r.tgt_x_list[r.list_tgt[r.trial - 2]] - r.tgt_radius < r.crs_x < r.tgt_x_list[
            r.list_tgt[r.trial - 2]] + r.tgt_radius and
                r.tgt_y_list[r.list_tgt[r.trial - 2]] - r.tgt_radius < r.crs_y < r.tgt_y_list[
                    r.list_tgt[r.trial - 2]] + r.tgt_radius):
            r.at_home = 1
        else:
            r.at_home = 0

def check_target_reaching_links(r, timer_enter_tgt):
    """
    Check if cursor is inside the target
    """
    dist = np.sqrt((r.crs_anchor_x - r.tgt_x) ** 2 + (r.crs_anchor_y - r.tgt_y) ** 2)
    r.distance = dist
    # If you are not in a blind trial
    if r.is_blind == 0:
        if dist < r.tgt_radius:
            # if cursor is inside the target: start the timer that will count for how long the cursor will stay in the
            # target, then change status (INSIDE target)
            if r.state == 0 or r.state == 1:
                timer_enter_tgt.start()
            r.state = 2
        # if cursor is inside the target (or if it used to be but currently is not) then go back at state 0
        # (OUT OF target, IN TIME) and reset timer
        else:
            r.state = 0
            # timer_enter_tgt.reset()  # Stops time interval measurement and resets the elapsed time to zero.
            timer_enter_tgt.start()

    # If blind trial -> stopping criterion is different
    # (cursor has to remain in a specific region for 2000 ms (50 Hz -> count_mouse == 100)
    else:
        if (r.old_crs_x + 10 > r.crs_anchor_x > r.old_crs_x - 10 and
                r.old_crs_y + 10 > r.crs_anchor_y > r.old_crs_y - 10 and r.at_home == 0):
            r.count_mouse += 1
        else:
            r.count_mouse = 0

    # Check here if the cursor is in the home target. In this case modify at_home to turn on/off the visual feedback
    # if the corresponding checkbox is selected
    if (r.repetition > 5 and
            (r.block == 2 or r.block == 3 or r.block == 4 or r.block == 5 or
             r.block == 7 or r.block == 8 or r.block == 9 or r.block == 10)):
        if (r.tgt_x_list[r.list_tgt[r.trial - 2]] - r.tgt_radius < r.crs_anchor_x < r.tgt_x_list[
            r.list_tgt[r.trial - 2]] + r.tgt_radius and
                r.tgt_y_list[r.list_tgt[r.trial - 2]] - r.tgt_radius < r.crs_anchor_y < r.tgt_y_list[
                    r.list_tgt[r.trial - 2]] + r.tgt_radius):
            r.at_home = 1
        else:
            r.at_home = 0

def check_time_reaching(r, timer_enter_tgt, timer_start_trial, timer_practice):
    if r.state == 0:  # OUT OF target, IN TIME
        # if more than 1s is elapsed from beginning of the reaching:
        # change status(OUT OF target, OUT OF TIME) -> cursor red
        if timer_start_trial.elapsed_time > 1000:
            r.state = 1
    # BLIND TRIAL: cursor must stay in a specific region(+-50 pxl) for 100 ticks(100 * 20ms = 2000ms)
    if r.is_blind == 1 and r.count_mouse == 100:
        r.is_blind = 0

    # VISUAL FEEDBACK ON: cursor must stay inside the target for 250 ms.
    if r.is_blind == 0 and r.state == 2 and timer_enter_tgt.elapsed_time > 250:
        # timer_enter_tgt.reset()  # Stops time interval measurement and resets the elapsed time to zero.
        timer_enter_tgt.start()
        r.count_mouse = 0
        r.state = 0  # a new reaching will begin.state back to 0 (OUT OF target, IN TIME) -> cursor green


        # Random Walk
        if r.block == 2 or r.block == 3 or r.block == 4 or r.block == 5 or r.block == 7 or r.block == 8 or r.block == 9 or r.block == 10:
            if r.comeback == 0:  # going towards peripheral targets
                # Never comeback home
                # if you finished a repetition
                if r.target == r.tot_targets[r.block - 1] - 1:
                    r.target = 0
                    r.repetition += 1
                else:
                    r.target += 1

                # if you're entering the last repetition -> is_blind = true
                if r.repetition == r.tot_repetitions[r.block - 1]:
                    r.is_blind = 1
                r.trial += 1

            else:  # going towards home target (used just at the beginning of the experiment)
                r.comeback = 0

        # Center-Out
        else:
            if r.comeback == 0:  # going towards peripheral targets
                # next go to home tgt
                r.comeback = 1
                r.target += 1
                r.epoch += 1

                # if you finished a repetition
                # (last tgt don't come back home, just update trial and repetition and reset target)
                if r.target == r.tot_targets[r.block - 1]:
                    r.target = 0
                    r.repetition += 1
                    r.trial += 1
                    r.comeback = 1
                    r.score += 1
            else:  # going towards home target (used just at the beginning of the experiment)
                # next go to peripheral tgt
                r.comeback = 0
                if r.target != 0:
                    r.trial += 1

        # pause acquisition if you have finished all repetitions.
        if r.repetition > r.tot_repetitions[r.block - 1]:
            pause_acquisition(r, timer_practice)

            r.score = 0
            r.is_blind = 1
            r.target = 0
            r.comeback = 1
            r.repetition = 1

            # stop if you finished all the blocks
            if r.block == r.tot_blocks:
                stop_thread(r)
                print("Practice is finished!")

            else:
                r.block += 1
                initialize_targets(r)

        # timer_start_trial.restart()  # restart is a reset + start
        timer_start_trial.start()  # Restart timer that keeps track of time elapsed since the beginning of the reach


def check_time_reaching_links(r, timer_enter_tgt, timer_start_trial, timer_practice):
    """
    :param r: reaching function class
    :param timer_enter_tgt: time within the target
    :param timer_start_trial: time from when the trial started
    :param timer_practice:
    state 0: Cursor is out of target and less than 1 sec
    state 1: Cursor outside of target and > 1 sec
    state 2: Cursor within target
    state 3: Cursor out of target and 10 secs (maybe)
    :return:
    """

    if timer_start_trial.elapsed_time > timer_practice.elapsed_time:
        r.reach_time = timer_practice.elapsed_time
    else:
        r.reach_time = timer_start_trial.elapsed_time
    if r.state == 0:  # OUT OF target, IN TIME
        # if more than 1s is elapsed from beginning of the reaching:
        # change status(OUT OF target, OUT OF TIME) -> cursor red
        if timer_start_trial.elapsed_time > 1000:
            r.state = 1
    # BLIND TRIAL: cursor must stay in a specific region(+-50 pxl) for 100 ticks(100 * 20ms = 2000ms)
    if r.is_blind == 1 and r.count_mouse == 100:
        r.is_blind = 0

    # VISUAL FEEDBACK ON: cursor must stay inside the target for 250 ms or if time has gone over 10 secs
    if timer_start_trial.elapsed_time > 10000 and r.comeback == 0:
        r.comeback = 1
        r.epoch += 1
        timer_start_trial.start()

    elif r.is_blind == 0 and r.state == 2 and timer_enter_tgt.elapsed_time > 250:
        # timer_enter_tgt.reset()  # Stops time interval measurement and resets the elapsed time to zero.
        timer_enter_tgt.start()
        r.count_mouse = 0
        r.epoch += 1
        r.state = 0  # a new reaching will begin.state back to 0 (OUT OF target, IN TIME) -> cursor green



        # Random Walk
        if r.block == 2 or r.block == 3 or r.block == 4 or r.block == 5 or r.block == 7 or r.block == 8 or r.block == 9 or r.block == 10:
            if r.comeback == 0:  # going towards peripheral targets
                # Never comeback home
                # if you finished a repetition
                if r.target == r.tot_targets[r.block - 1] - 1:
                    r.target = 0
                    r.repetition += 1
                else:
                    r.target += 1

                # if you're entering the last repetition -> is_blind = true
                if r.repetition == r.tot_repetitions[r.block - 1]:
                    r.is_blind = 1
                r.trial += 1

            else:  # going towards home target (used just at the beginning of the experiment)
                r.comeback = 0

        # Center-Out
        else:
            if r.comeback == 0:  # going towards peripheral targets
                # next go to home tgt
                r.comeback = 1
                r.score += 1
                # # if you finished a repetition
                # # (last tgt don't come back home, just update trial and repetition and reset target)
                # if r.target == r.tot_targets[r.block - 1]:
                #     r.target = 0
                #     r.repetition += 1
                #     r.trial += 1
                #     r.comeback = 1
            else:  # going towards home target (used just at the beginning of the experiment)
                # next go to peripheral tgt
                r.comeback = 0
                r.trial += 1


        # pause acquisition if you have finished all repetitions.
        # if r.repetition > r.tot_repetitions[r.block - 1]:
        #     pause_acquisition(r, timer_practice)
        #
        #     r.score = 0
        #     r.is_blind = 1
        #     r.target = 0
        #     r.comeback = 1
        #     r.repetition = 1
        #
        #     # stop if you finished all the blocks
        #     if r.block == r.tot_blocks:
        #         stop_thread(r)
        #         print("Practice is finished!")
        #
        #     else:
        #         # r.block += 1 Not doing blocks so we won't increase them
        #         initialize_targets(r)

        # timer_start_trial.restart()  # restart is a reset + start
        timer_start_trial.start()  # Restart timer that keeps track of time elapsed since the beginning of the reach

def pause_acquisition(r, timer_practice):
    # If you are doing the reaching, stop the acquisition timer and sensors thread
    if not r.is_paused:
        timer_practice.pause()
        r.is_paused = True
        print("Pausing reaching...")

    # Resume reaching
    else:
        r.is_paused = False
        timer_practice.restart()
        print("Resuming reaching...")


def stop_thread(r):
    r.is_terminated = True
    print("main thread: Worker thread has terminated.")


def filt(N, fc, fs, btype, signal):
    """
        Function that filters an input signal (with Butterworth IIR)
        :param N: order of the filter
        :param fc: cutoff frequency
        :param fs: sampling frequency of input signal
        :param btype: type of filter {‘lowpass’, ‘highpass’, ‘bandpass’, ‘bandstop’}
        :param signal: input signal to be filtered
        :return: filtered signal
    """
    Wn = fc / (fs / 2)
    b, a = sgn.butter(N, Wn, btype)

    return pd.Series(sgn.lfilter(b, a, signal))











