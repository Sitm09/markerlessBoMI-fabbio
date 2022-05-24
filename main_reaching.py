# General imports
import numpy as np
import pandas as pd
import os
import time
import matplotlib.pyplot as plt
import math
# For multithreading
from threading import Thread, Lock
import queue
# For OpenCV
import cv2
# For GUI
import tkinter as tk
from tkinter import Label, Button, BooleanVar, Checkbutton, Text, Entry
# For pygame
import pygame
# For reaching task
from reaching import Reaching
from stopwatch import StopWatch
from filter_butter_online import FilterButter3
import reaching_functions
# For controlling computer cursor
import pyautogui
# For Mediapipe
import mediapipe as mp
# For training pca/autoencoder
from compute_bomi_map import Autoencoder, PrincipalComponentAnalysis, compute_vaf

pyautogui.PAUSE = 0.01  # set fps of cursor to 100Hz ish when mouse_enabled is True


class MainApplication(tk.Frame):
    """
    class that defines the main tkinter window
    """

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.drPath = ''

        self.num_joints = 0
        self.joints = np.zeros((5, 1))
        self.dr_mode = 'pca'
        self.vision = 'min'

        # set checkboxes for selecting joints
        self.check_nose = BooleanVar()
        self.check2 = Checkbutton(tk_window, font='Times 18 bold', text="nose", variable=self.check_nose)
        self.check2.place(relx=0.05, rely=0.1, anchor='sw')

        self.check_eyes = BooleanVar()
        self.check3 = Checkbutton(tk_window, font='Times 18 bold', text="eyes", variable=self.check_eyes)
        self.check3.place(relx=0.2, rely=0.1, anchor='sw')

        self.check_shoulders = BooleanVar()
        self.check4 = Checkbutton(tk_window, font='Times 18 bold', text="shoulders", variable=self.check_shoulders)
        self.check4.place(relx=0.35, rely=0.1, anchor='sw')

        self.check_forefinger = BooleanVar()
        self.check5 = Checkbutton(tk_window, font='Times 18 bold', text="right forefinger",
                                  variable=self.check_forefinger)
        self.check5.place(relx=0.5, rely=0.1, anchor='sw')

        self.check_fingers = BooleanVar()
        self.check6 = Checkbutton(tk_window, font='Times 18 bold', text="fingers", variable=self.check_fingers)
        self.check6.place(relx=0.7, rely=0.1, anchor='sw')

        self.btn_num_joints = Button(parent, font='Times 22 bold', text="Select Joints", command=self.select_joints)
        self.btn_num_joints.pack()
        self.btn_num_joints.place(relx=0.8, rely=0.1, anchor='sw')

        ##
        self.btn_calib = Button(parent, font='Times 22 bold', text="Start calibration", command=self.calibration)
        self.btn_calib.pack()
        self.btn_calib.place(relx=0.05, rely=0.25, anchor='sw')
        self.btn_calib["state"] = "disabled"
        self.calib_duration = 5000

        # set checkboxes for selecting BoMI map
        self.check_pca = BooleanVar(value=True)
        self.check_pca1 = Checkbutton(tk_window, font='Times 20 bold', text="PCA", variable=self.check_pca)
        self.check_pca1.place(relx=0.35, rely=0.3, anchor='sw')

        self.check_ae = BooleanVar()
        self.check_ae1 = Checkbutton(tk_window, font='Times 20 bold', text="Autoencoder", variable=self.check_ae)
        self.check_ae1.place(relx=0.35, rely=0.35, anchor='sw')

        self.check_vae = BooleanVar()
        self.check_vae1 = Checkbutton(tk_window, font='Times 20 bold', text="Variational AE", variable=self.check_vae)
        self.check_vae1.place(relx=0.35, rely=0.4, anchor='sw')

        ##
        self.btn_map = Button(parent, font='Times 22 bold', text="Calculate BoMI map", command=self.train_map)
        self.btn_map.pack()
        self.btn_map.place(relx=0.05, rely=0.4, anchor='sw')
        self.btn_map["state"] = "disabled"

        self.btn_custom = Button(parent, font='Times 22 bold', text="Start customization", command=self.customization)
        self.btn_custom.pack()
        self.btn_custom.place(relx=0.05, rely=0.55, anchor='sw')
        self.btn_custom["state"] = "disabled"

        self.btn_start = Button(parent, font='Times 22 bold', text="Start practice", command=self.start)
        self.btn_start.pack()
        self.btn_start.place(relx=0.05, rely=0.7, anchor='sw')
        self.btn_start["state"] = "disabled"

        self.btn_close = Button(parent, font='Times 22 bold', text="Close", command=parent.destroy)
        self.btn_close.pack()
        self.btn_close.place(relx=0.05, rely=0.85, anchor='sw')

        # set label for number of target remaining
        self.lbl_tgt = Label(tk_window, font='Times 22 bold', text='Number of target remaining: ')
        self.lbl_tgt.place(relx=0.55, rely=0.7, anchor='sw')

        # set label for calibration
        self.lbl_calib = Label(tk_window, font='Times 22 bold', text='Calibration time remaining: ')
        self.lbl_calib.place(relx=0.55, rely=0.9, anchor='sw')

        # set checkbox
        self.check_mouse = BooleanVar()
        self.check1 = Checkbutton(tk_window, font='Times 22 bold', text="Mouse control", variable=self.check_mouse)
        self.check1.place(relx=0.35, rely=0.5, anchor='sw')

        # setting toggle checkbox for vision (default is minimal vision)
        self.check_vision = BooleanVar()
        self.check_vision1 = Checkbutton(tk_window, font='Times 20 bold', text="Vision", variable=self.check_vision)
        self.check_vision1.place(relx=0.55, rely=0.3, anchor='sw')

        # set ID Entry Box for subject record keeping and identification
        self.subID = Entry(tk_window, font='Times 20 bold', width='3')
        self.subID.place(relx=0.35, rely=0.2, anchor='sw')

    def select_joints(self):
        nose_enabled = self.check_nose.get()
        eyes_enabled = self.check_eyes.get()
        shoulders_enabled = self.check_shoulders.get()
        forefinger_enabled = self.check_forefinger.get()
        fingers_enabled = self.check_fingers.get()
        if nose_enabled:
            self.num_joints += 2
            self.joints[0, 0] = 1
        if eyes_enabled:
            self.num_joints += 4
            self.joints[1, 0] = 1
        if shoulders_enabled:
            self.num_joints += 4
            self.joints[2, 0] = 1
        if forefinger_enabled:
            self.num_joints += 2
            self.joints[3, 0] = 1
        if fingers_enabled:
            self.num_joints += 42
            self.joints[4, 0] = 1

        # setting calibration pathway
        self.calibPath = os.path.dirname(os.path.abspath(__file__)) + "/" + self.vision.upper() + "/" + \
            self.subID.get() + "/calib/"

        # error checking to make sure all fields are filled in
        if np.sum(self.joints, axis=0) != 0 and self.subID.get() != "":
            self.btn_calib["state"] = "normal"
            self.btn_map["state"] = "normal"
            self.btn_custom["state"] = "normal"
            self.btn_start["state"] = "normal"
            print('Joints correctly selected.\nSubject ID: ' + self.subID.get())

        # check if minimal vision or complete vision. Will separate into folders later
        vision_enabled = self.check_vision.get()
        if vision_enabled:
            self.vision = 'max'
            print('Group Selected: CV)')
            print(self.calibPath)
        else:
            self.vision = 'min'
            print('Group Selected: MV')
            print(self.calibPath)

    def calibration(self):
        # start calibration dance - collect webcam data
        self.w = popupWindow(self.master, "You will now start calibration.")
        self.master.wait_window(self.w.top)
        compute_calibration(self.calibPath, self.calib_duration, self.lbl_calib, self.num_joints, self.joints)
        self.btn_map["state"] = "normal"

    def train_map(self):
        # check whether calibration file exists first
        if os.path.isfile(self.calibPath + "Calib.txt"):
            self.w = popupWindow(self.master, "You will now train BoMI map")
            self.master.wait_window(self.w.top)
            if self.check_pca.get():
                self.drPath = self.calibPath + 'PCA/'
                train_pca(self.calibPath, self.drPath)
                self.dr_mode = 'pca'
            elif self.check_ae.get():
                self.drPath = self.calibPath + 'AE/'
                train_ae(self.calibPath, self.drPath)
                self.dr_mode = 'ae'
            elif self.check_vae.get():
                self.drPath = self.calibPath + 'AE/'
                train_ae(self.calibPath, self.drPath)
                self.dr_mode = 'ae'
            self.btn_custom["state"] = "normal"
        else:
            self.w = popupWindow(self.master, "Perform calibration first.")
            self.master.wait_window(self.w.top)
            self.btn_map["state"] = "disabled"

    def customization(self):
        # check whether PCA/AE parameters have been saved
        if os.path.isfile(self.drPath + "weights1.txt"):
            # open customization window
            self.newWindow = tk.Toplevel(self.master)
            self.newWindow.geometry("1000x500")
            self.app = CustomizationApplication(self.newWindow, self, drPath=self.drPath, num_joints=self.num_joints,
                                                joints=self.joints, dr_mode=self.dr_mode, vision=self.vision)
        else:
            self.w = popupWindow(self.master, "Compute BoMI map first.")
            self.master.wait_window(self.w.top)
            self.btn_custom["state"] = "disabled"

    def start(self):
        # check whether customization parameters have been saved
        if os.path.isfile(self.drPath + "offset_custom.txt"):
            # open pygame and start reaching task
            self.w = popupWindow(self.master, "You will now start practice.")
            self.master.wait_window(self.w.top)
            start_reaching(self.drPath, self.check_mouse, self.lbl_tgt, self.num_joints, self.joints, self.dr_mode)
        else:
            self.w = popupWindow(self.master, "Perform customization first.")
            self.master.wait_window(self.w.top)
            self.btn_start["state"] = "disabled"


class CustomizationApplication(tk.Frame):
    """
    class that defines the customization tkinter window
    """

    def __init__(self, parent, mainTk, drPath, num_joints, joints, dr_mode, vision):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.mainTk = mainTk
        self.drPath = drPath
        self.num_joints = num_joints
        self.joints = joints
        self.dr_mode = dr_mode
        self.vision = vision

        self.lbl_rot = Label(parent, font='Times 22 bold', text='Rotation ')
        self.lbl_rot.pack()
        self.lbl_rot.place(relx=0.1, rely=0.2, anchor='sw')
        self.txt_rot = Text(parent, width=10, height=1)
        self.txt_rot.pack()
        self.txt_rot.place(relx=0.25, rely=0.18, anchor='sw')
        self.txt_rot.insert("1.0", '0')

        self.lbl_gx = Label(parent, font='Times 18 bold', text='Gain Velocity 1 ')
        self.lbl_gx.place(relx=0.02, rely=0.4, anchor='sw')
        self.txt_gx = Text(parent, width=10, height=1)
        self.txt_gx.pack()
        self.txt_gx.place(relx=0.20, rely=0.35, anchor='sw')
        self.txt_gx.insert("1.0", '1')

        self.lbl_gy = Label(parent, font='Times 18 bold', text='Gain Velocity 2 ')
        self.lbl_gy.place(relx=0.3, rely=0.4, anchor='sw')
        self.txt_gy = Text(parent, width=10, height=1)
        self.txt_gy.pack()
        self.txt_gy.place(relx=0.55, rely=0.35, anchor='sw')
        self.txt_gy.insert("1.0", '1')

        self.lbl_gz = Label(parent, font='Times 18 bold', text='Gain Velocity 3 ')
        self.lbl_gz.place(relx=0.7, rely=0.4, anchor='sw')
        self.txt_gz = Text(parent, width=10, height=1)
        self.txt_gz.pack()
        self.txt_gz.place(relx=0.85, rely=0.35, anchor='sw')
        self.txt_gz.insert("1.0", '1')

        self.lbl_ox = Label(parent, font='Times 18 bold', text='Offset X ')
        self.lbl_ox.place(relx=0.1, rely=0.55, anchor='sw')
        self.txt_ox = Text(parent, width=10, height=1)
        self.txt_ox.pack()
        self.txt_ox.place(relx=0.25, rely=0.55, anchor='sw')
        self.txt_ox.insert("1.0", '0')

        self.lbl_oy = Label(parent, font='Times 18 bold', text='Offset Y ')
        self.lbl_oy.place(relx=0.4, rely=0.55, anchor='sw')
        self.txt_oy = Text(parent, width=10, height=1)
        self.txt_oy.pack()
        self.txt_oy.place(relx=0.55, rely=0.55, anchor='sw')
        self.txt_oy.insert("1.0", '0')

        self.lbl_oz = Label(parent, font='Times 18 bold', text='Offset Z ')
        self.lbl_oz.place(relx=0.7, rely=0.55, anchor='sw')
        self.txt_oz = Text(parent, width=10, height=1)
        self.txt_oz.pack()
        self.txt_oz.place(relx=0.85, rely=0.55, anchor='sw')
        self.txt_oz.insert("1.0", '0')

        self.btn_start = Button(parent, font='Times 22 bold', text="Start", command=self.customization)
        self.btn_start.pack()
        self.btn_start.place(relx=0.85, rely=0.2, anchor='sw')

        self.btn_save = Button(parent, font='Times 22 bold', text="Save parameters", command=self.save_parameters)
        self.btn_save.pack()
        self.btn_save.place(relx=0.3, rely=0.75, anchor='sw')

        self.btn_close = Button(parent, font='Times 22 bold', text="Close", command=parent.destroy)
        self.btn_close.pack()
        self.btn_close.place(relx=0.3, rely=0.95, anchor='sw')

    # functions to retrieve values of textbox programmatically
    def retrieve_txt_rot(self):
        return self.txt_rot.get("1.0", "end-1c")

    def retrieve_txt_gx(self):
        return self.txt_gx.get("1.0", "end-1c")

    def retrieve_txt_gy(self):
        return self.txt_gy.get("1.0", "end-1c")

    def retrieve_txt_gz(self):
        return self.txt_gz.get("1.0", "end-1c")

    def retrieve_txt_ox(self):
        return self.txt_ox.get("1.0", "end-1c")

    def retrieve_txt_oy(self):
        return self.txt_oy.get("1.0", "end-1c")

    def retrieve_txt_oz(self):
        return self.txt_oz.get("1.0", "end-1c")

    def customization(self):
        initialize_customization(self, self.dr_mode, self.drPath, self.num_joints, self.joints, self.vision)

    def save_parameters(self):
        save_parameters(self, self.drPath)
        self.parent.destroy()
        self.mainTk.btn_start["state"] = "normal"


class popupWindow(object):
    """
    class that defines the popup tkinter window
    """

    def __init__(self, master, msg):
        top = self.top = tk.Toplevel(master)
        self.lbl = Label(top, text=msg)
        self.lbl.pack()
        self.btn = Button(top, text='Ok', command=self.cleanup)
        self.btn.pack()

    def cleanup(self):
        self.top.destroy()


def compute_calibration(drPath, calib_duration, lbl_calib, num_joints, joints):
    """
    function called to collect calibration data from webcam
    :param drPath: path to save calibration file
    :param calib_duration: duration of calibration as read by the textbox in the main window
    :param lbl_calib: label in the main window that shows calibration time remaining
    :return:
    """
    # Create object of openCV and Reaching (needed for terminating mediapipe thread)
    cap = cv2.VideoCapture(0)
    r = Reaching()

    # The clock will be used to control how fast the screen updates. Stopwatch to count calibration time elapsed
    clock = pygame.time.Clock()
    timer_calib = StopWatch()

    # initialize MediaPipe Pose
    # mp_pose = mp.solutions.pose
    # mp_hands = mp.solutions.hands
    # pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, upper_body_only=True, smooth_landmarks=False)
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5, max_num_hands=1)
    # mp_holistic = mp.solutions.holistic
    # holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5, upper_body_only=True,
    #                                 smooth_landmarks=False)

    # initialize lock for avoiding race conditions in threads
    lock = Lock()

    # global variable accessed by main and mediapipe threads that contains the current vector of body landmarks
    global body
    body = np.zeros((num_joints,))  # initialize global variable
    body_calib = []  # initialize local variable (list of body landmarks during calibration)

    # start thread for OpenCV. current frame will be appended in a queue in a separate thread
    q_frame = queue.Queue()
    opencv_thread = Thread(target=get_data_from_camera, args=(cap, q_frame, r))
    opencv_thread.start()
    print("openCV thread started in calibration.")

    # initialize thread for DLC/mediapipe operations
    mediapipe_thread = Thread(target=mediapipe_forwardpass,
                              args=(hands, mp_hands, lock, q_frame, r, num_joints, joints))
    mediapipe_thread.start()
    print("mediapipe thread started in calibration.")

    # start the timer for calibration
    timer_calib.start()

    print("main thread: Starting calibration...")

    # -------- Main Program Loop -----------
    while not r.is_terminated:

        if timer_calib.elapsed_time > calib_duration:
            r.is_terminated = True

        # get current value of body
        body_calib.append(np.copy(body))

        # update time elapsed label
        time_remaining = int((calib_duration - timer_calib.elapsed_time) / 1000)
        lbl_calib.configure(text='Calibration time remaining ' + str(time_remaining))
        lbl_calib.update()

        # --- Limit to 50 frames per second
        clock.tick(50)

    # Stop the game engine and release the capture
    # pose.close()
    hands.close()
    print("pose estimation object released in calibration.")
    cap.release()
    cv2.destroyAllWindows()
    print("openCV object released in calibration.")

    # print calibration file
    body_calib = np.array(body_calib)
    if not os.path.exists(drPath):
        os.makedirs(drPath)
    np.savetxt(drPath + "Calib.txt", body_calib)

    print('Calibration finished. You can now train BoMI forward map.')


def train_pca(calibPath, drPath):
    """
    function to train BoMI forward map - PCA
    :param drPath: path to save BoMI forward map
    :return:
    """

    # read calibration file and remove all the initial zero rows
    xp = list(pd.read_csv(calibPath + 'Calib.txt', sep=' ', header=None).values)
    x = [i for i in xp if all(i)]
    x = np.array(x)

    # # filter signal
    # N = 3
    # fc = 10
    # fs = 30
    # x = np.empty((x.shape[0], x.shape[1]))
    # for i in range(x.shape[1]):
    #     x[:, i] = reaching_functions.filt(N, fc, fs, 'lowpass', x[:, i])
    #     plt.figure()
    #     plt.plot(x[:, i])

    # randomly shuffle input
    np.random.shuffle(x)

    # define train/test split
    thr = 80
    split = int(len(x) * thr / 100)
    train_x = x[0:split, :]
    test_x = x[split:, :]

    # initialize object of class PCA
    n_pc = 3
    PCA = PrincipalComponentAnalysis(n_pc)

    # train AE network
    pca, train_x_rec, train_pc, test_x_rec, test_pc = PCA.train_pca(train_x, x_test=test_x)
    print('PCA has been trained.')
    # save weights and biases
    if not os.path.exists(drPath):
        os.makedirs(drPath)
    np.savetxt(drPath + "weights1.txt", pca.components_[:, :n_pc])

    print('BoMI forward map (PCA parameters) has been saved.')

    # compute train/test VAF
    print(f'Training VAF: {compute_vaf(train_x, train_x_rec)}')
    print(f'Test VAF: {compute_vaf(test_x, test_x_rec)}')

    # normalize latent space to fit the monitor coordinates
    # Applying rotation
    train_pc = np.dot(train_x, pca.components_[:, :n_pc])
    velocity_pc = train_pc
    rot = 0
    train_pc[0] = train_pc[0] * np.cos(np.pi / 180 * rot) - train_pc[1] * np.sin(np.pi / 180 * rot)
    train_pc[1] = train_pc[0] * np.sin(np.pi / 180 * rot) + train_pc[1] * np.cos(np.pi / 180 * rot)
    train_pc = train_pc[:, :2]


    # Applying scale
    scale = [1920 / np.ptp(train_pc[:, 0]), 1080 / np.ptp(train_pc[:, 1])]
    velocity_scale = [2 / np.ptp(velocity_pc[:, i]) for i in range(n_pc)]

    train_pc = train_pc * scale
    velocity_pc = velocity_pc * velocity_scale

    # Applying offset
    off = [1920 / 2 - np.mean(train_pc[:, 0]), 1080 / 2 - np.mean(train_pc[:, 1])]
    velocity_off = [0 - np.mean(velocity_pc[:, i]) for i in range(n_pc)]
    train_pc = train_pc + off
    velocity_pc = velocity_pc + velocity_off

    # Plot reconstructed signals
    # fs = 50
    # plot_reconstruction(test_x, test_x_rec_ae, fs, optional=test_x_rec_vae, opt_label="VAE")

    # Plot latent space
    plt.figure()
    plt.scatter(train_pc[:, 0], train_pc[:, 1], c='green', s=20)
    plt.title('Projections in workspace')
    plt.axis("equal")

    ''' 
    # save AE scaling values
    with open(drPath + "rotation_dr.txt", 'w') as f:
        print(rot, file=f)
    np.savetxt(drPath + "scale_dr.txt", scale)
    np.savetxt(drPath + "offset_dr.txt", off)
    '''

    # save AE scaling values w/ velocity
    with open(drPath + "rotation_dr.txt", 'w') as f:
        print(rot, file=f)
    np.savetxt(drPath + "scale_dr.txt", velocity_scale)
    np.savetxt(drPath + "offset_dr.txt", velocity_off)

    print('PCA scaling values has been saved. You can continue with customization.')


def train_ae(calibPath, drPath):
    """
    function to train BoMI forward map
    :param drPath: path to save BoMI forward map
    :return:
    """
    # Autoencoder parameters
    n_steps = 3001
    lr = 0.02
    cu = 2
    nh1 = 6
    activ = "tanh"

    # read calibration file and remove all the initial zero rows
    xp = list(pd.read_csv(calibPath + 'Calib.txt', sep=' ', header=None).values)
    x = [i for i in xp if all(i)]
    x = np.array(x)

    # # filter signal
    # N = 3
    # fc = 10
    # fs = 30
    # x = np.empty((x.shape[0], x.shape[1]))
    # for i in range(x.shape[1]):
    #     x[:, i] = reaching_functions.filt(N, fc, fs, 'lowpass', x[:, i])
    #     plt.figure()
    #     plt.plot(x[:, i])

    # randomly shuffle input
    np.random.shuffle(x)

    # define train/test split
    thr = 80
    split = int(len(x) * thr / 100)
    train_x = x[0:split, :]
    test_x = x[split:, :]

    # initialize object of class Autoencoder
    AE = Autoencoder(n_steps, lr, cu, activation=activ, nh1=nh1, seed=0)

    # train AE network
    history, ws, bs, train_x_rec, train_cu, test_x_rec, test_cu = AE.train_network(train_x, x_test=test_x)
    # history, ws, bs, train_x_rec, train_cu, test_x_rec, test_cu = AE.train_vae(train_x, beta=0.00035, x_test=test_x)
    print('AE has been trained.')

    # save weights and biases
    if not os.path.exists(drPath):
        os.makedirs(drPath)
    for layer in range(3):
        np.savetxt(drPath + "weights" + str(layer + 1) + ".txt", ws[layer])
        np.savetxt(drPath + "biases" + str(layer + 1) + ".txt", bs[layer])

    print('BoMI forward map (AE parameters) has been saved.')

    # compute train/test VAF
    print(f'Training VAF: {compute_vaf(train_x, train_x_rec)}')
    print(f'Test VAF: {compute_vaf(test_x, test_x_rec)}')

    # normalize latent space to fit the monitor coordinates
    # Applying rotation
    rot = 0
    train_cu[0] = train_cu[0] * np.cos(np.pi / 180 * rot) - train_cu[1] * np.sin(np.pi / 180 * rot)
    train_cu[1] = train_cu[0] * np.sin(np.pi / 180 * rot) + train_cu[1] * np.cos(np.pi / 180 * rot)
    # Applying scale
    scale = [1920 / np.ptp(train_cu[:, 0]), 1080 / np.ptp(train_cu[:, 1])]
    train_cu = train_cu * scale
    # Applying offset
    off = [1920 / 2 - np.mean(train_cu[:, 0]), 1080 / 2 - np.mean(train_cu[:, 1])]
    train_cu = train_cu + off

    # Plot reconstructed signals
    # fs = 50
    # plot_reconstruction(test_x, test_x_rec_ae, fs, optional=test_x_rec_vae, opt_label="VAE")

    # # MSE vs KLD loss term trend in VAE
    # plt.figure()
    # plt.plot(history_vae.history['loss'], color='red', label='loss')
    # plt.plot(history_vae.history['mse_loss'], color='blue', label='MSE')
    # plt.plot(history_vae.history['kld_loss'], color='green', label='KLD')
    # plt.legend()
    # plt.xlabel('epochs')

    # Plot latent space
    plt.figure()
    plt.scatter(train_cu[:, 0], train_cu[:, 1], c='green', s=20)
    plt.title('Projections in workspace')
    plt.axis("equal")

    # save AE scaling values
    with open(drPath + "rotation_dr.txt", 'w') as f:
        print(rot, file=f)
    np.savetxt(drPath + "scale_dr.txt", scale)
    np.savetxt(drPath + "offset_dr.txt", off)

    print('AE scaling values has been saved. You can continue with customization.')


def load_bomi_map(dr_mode, drPath):
    if dr_mode == 'pca':
        map = pd.read_csv(drPath + 'weights1.txt', sep=' ', header=None).values
    elif dr_mode == 'ae':
        ws = []
        bs = []
        ws.append(pd.read_csv(drPath + 'weights1.txt', sep=' ', header=None).values)
        ws.append(pd.read_csv(drPath + 'weights2.txt', sep=' ', header=None).values)
        ws.append(pd.read_csv(drPath + 'weights3.txt', sep=' ', header=None).values)
        bs.append(pd.read_csv(drPath + 'biases1.txt', sep=' ', header=None).values)
        bs[0] = bs[0].reshape((bs[0].size,))
        bs.append(pd.read_csv(drPath + 'biases2.txt', sep=' ', header=None).values)
        bs[1] = bs[1].reshape((bs[1].size,))
        bs.append(pd.read_csv(drPath + 'biases3.txt', sep=' ', header=None).values)
        bs[2] = bs[2].reshape((bs[2].size,))

        map = (ws, bs)

    return map


def initialize_customization(self, dr_mode, drPath, num_joints, joints, vision):
    """
    initialize objects needed for online cursor control. Start all the customization threads as well
    :param self: CustomizationApplication tkinter Frame. needed to retrieve textbox values programmatically
    :param drPath: path to load the BoMI forward map
    :return:
    """

    # Create object of openCV, Reaching class and filter_butter3
    cap = cv2.VideoCapture(0)
    r = Reaching()
    filter_curs = FilterButter3("lowpass_4")

    # initialize target position
    reaching_functions.initialize_targets(r)

    # Doing this for threading at the end of this function

    # load BoMI forward map parameters for converting body landmarks into cursor coordinates
    map = load_bomi_map(dr_mode, drPath)

    # initialize MediaPipe Pose
    # mp_pose = mp.solutions.pose
    # mp_hands = mp.solutions.hands
    # pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, upper_body_only=True, smooth_landmarks=False)
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5, max_num_hands=1)

    mp_holistic = mp.solutions.holistic
    holistic = mp_holistic.Holistic(min_detection_confidence=0.6, min_tracking_confidence=0.6, upper_body_only=True,
                                    smooth_landmarks=False)

    # load scaling values saved after training AE for covering entire monitor workspace
    rot = pd.read_csv(drPath + 'rotation_dr.txt', sep=' ', header=None).values
    scale = pd.read_csv(drPath + 'scale_dr.txt', sep=' ', header=None).values
    scale = np.reshape(scale, (scale.shape[0],))
    off = pd.read_csv(drPath + 'offset_dr.txt', sep=' ', header=None).values
    off = np.reshape(off, (off.shape[0],))

    # initialize lock for avoiding race conditions in threads
    lock = Lock()

    # global variable accessed by main and mediapipe threads that contains the current vector of body landmarks
    global body
    body = np.zeros((num_joints,))  # initialize global variable

    # start thread for OpenCV. current frame will be appended in a queue in a separate thread
    q_frame = queue.Queue()
    opencv_thread = Thread(target=get_data_from_camera, args=(cap, q_frame, r))
    opencv_thread.start()
    print("openCV thread started in customization.")

    # initialize thread for DLC/mediapipe operations
    mediapipe_thread = Thread(target=mediapipe_forwardpass,
                              args=(hands, mp_hands, lock, q_frame, r, num_joints, joints))
    mediapipe_thread.start()
    print("mediapipe thread started in customization.")

    # start thread for cursor control. in customization this is needed to programmatically change textbox values
    cursor_thread = Thread(target=cursor_customization,
                           args=(self, r, filter_curs, hands, cap, map, rot, scale, off, vision))
    cursor_thread.start()
    print("cursor control thread started in customization.")


def cursor_customization(self, r, filter_curs, hands, cap, map, rot, scale, off, vision):
    """
    Function that runs in a separate thread when customization is started. A separate thread allows to concurrently
    change the values of each custom textbox in the tkinter window programmatically
    :param self: CustomizationApplication tkinter Frame. needed to retrieve textbox values programmatically
    :param r: object of Reaching class
    :param pose: object of the Pose class for performing online pose estimation
    :param cap: object of the OpenCV class for collecting webcam data
    :param filter_curs: object of FilterButter3 for online filtering of the cursor
    :param hands: object of FilterButter3 for online filtering of the cursor
    :param vision: checks to see if links should be displayed or not
    :param ws: list of the AE weights
    :param bs: list of the AE biases
    :param rot: rotation of the latent space defined after AE training
    :param scale: scaling factor of the latent space defined after AE training
    :param off: offset of the latent space defined after AE training
    :return:
    """

    # Define some colors
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    CURSOR = (0.19 * 255, 0.65 * 255, 0.4 * 255)
    GREY = (0.50 * 255, 0.50 * 255, 0.50 * 255)

    pygame.init()

    # The clock will be used to control how fast the screen updates
    clock = pygame.time.Clock()

     # Open a new window
    size = (r.width, r.height)
    screen = pygame.display.set_mode(size)
    # screen = pygame.display.toggle_fullscreen()

    # Defining the initial angle of rotation
    link_rot1 = 0
    link_rot2 = 0
    link_rot3 = 0

    # Defining 3 link surfaces and length of links
    link1_orig = pygame.Surface((r.link_length, 75))
    link2_orig = pygame.Surface((r.link_length, 75))
    link3_orig = pygame.Surface((r.link_length, 75))

    # -------- Main Program Loop -----------
    while not r.is_terminated:
        # --- Main event loop
        for event in pygame.event.get():  # User did something
            if event.type == pygame.QUIT:  # If user clicked close
                r.is_terminated = True  # Flag that we are done so we exit this loop
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_x:  # Pressing the x Key will quit the game
                    r.is_terminated = True
                if event.key == pygame.K_SPACE:  # Pressing the space Key will click the mouse
                    pyautogui.click(r.crs_x, r.crs_y)

        if not r.is_paused:
            # Copy old cursor position
            r.old_crs_x = r.crs_x
            r.old_crs_y = r.crs_y
            r.old_crs_z = r.crs_z

            # get current value of body
            r.body = np.copy(body)

            # apply BoMI forward map to body vector to obtain cursor position
            r.crs_x, r.crs_y, r.crs_z = reaching_functions.update_cursor_position_custom_3links(r.body, map, rot, scale, off)

            # Apply extra customization according to textbox values (try/except allows to catch invalid inputs)
            try:
                rot_custom = int(self.retrieve_txt_rot())
            except:
                rot_custom = 0
            try:
                gx_custom = float(self.retrieve_txt_gx())
            except:
                gx_custom = 1.0
            try:
                gy_custom = float(self.retrieve_txt_gy())
            except:
                gy_custom = 1.0
            try:
                gz_custom = float(self.retrieve_txt_gz())
            except:
                gz_custom = 1.0
            try:
                ox_custom = int(self.retrieve_txt_ox())
            except:
                ox_custom = 0
            try:
                oy_custom = int(self.retrieve_txt_oy())
            except:
                oy_custom = 0
            try:
                oz_custom = int(self.retrieve_txt_oz())
            except:
                oz_custom = 0

            # Applying rotation
            r.crs_x = r.crs_x * np.cos(np.pi / 180 * rot_custom) - r.crs_y * np.sin(np.pi / 180 * rot_custom)
            r.crs_y = r.crs_x * np.sin(np.pi / 180 * rot_custom) + r.crs_y * np.cos(np.pi / 180 * rot_custom)
            # Applying scale
            r.crs_x = r.crs_x * gx_custom
            r.crs_y = r.crs_y * gy_custom
            r.crs_z = r.crs_z * gz_custom
            # Applying offset
            r.crs_x = r.crs_x + ox_custom
            r.crs_y = r.crs_y + oy_custom
            r.crs_z = r.crs_z + oz_custom

            # Moving the paddles when the user uses the arrow keys (in case cursor gets stuck)
            # keys = pygame.key.get_pressed()
            # if keys[pygame.K_w]:
            #     r.crs_y -= 75
            # if keys[pygame.K_a]:
            #     r.crs_x -= 75
            # if keys[pygame.K_s]:
            #     r.crs_y += 75
            # if keys[pygame.K_d]:
            #     r.crs_x += 75

            # Filter the cursor
            # r.crs_x, r.crs_y = reaching_functions.filter_cursor(r, filter_curs)

            # Set target position to update the GUI
            reaching_functions.set_target_reaching_customization(r)

            # First, clear the screen to black. In between screen.fill and pygame.display.flip() all the draw
            screen.fill(BLACK)

            # draw cursor
            # pygame.draw.circle(screen, CURSOR, (int(r.crs_x), int(r.crs_y)), r.crs_radius)

            # drawing the links

            # for making transparent background while rotating the image
            link1_orig.set_colorkey(BLACK)
            link2_orig.set_colorkey(BLACK)
            link3_orig.set_colorkey(BLACK)

            # fill the rectangle / surface with the color GREY
            link1_orig.fill(GREY)
            link2_orig.fill(GREY)
            link3_orig.fill(GREY)

            # creating a copy of original image for smooth rotation
            link1 = link1_orig.copy()
            link2 = link2_orig.copy()
            link3 = link3_orig.copy()

            # Assigning Anchor Points
            pos1 = (size[0] / 2, size[1] * 0.85)

            link1rect = link1.get_rect()
            link2rect = link2.get_rect()
            link3rect = link3.get_rect()

            link1_anchor = (size[0] / 2, size[1] * 0.85)
            link2_anchor = ((link1_anchor[0] + (math.cos(math.radians(link_rot1)) * link1rect.w)),
                            link1_anchor[1] - (math.sin(math.radians(link_rot1)) * link1rect.w))
            link3_anchor = (link2_anchor[0] + math.cos(math.radians(link_rot2)) * link2rect.w,
                            link2_anchor[1] - (math.sin(math.radians(link_rot2)) * link2rect.w))
            crs_anchor = (link3_anchor[0] + math.cos(math.radians(link_rot3)) * link3rect.w,
                          link3_anchor[1] - (math.sin(math.radians(link_rot3)) * link3rect.w))

            if vision == 'max':

                pygame.draw.line(screen, GREY, link1_anchor, link2_anchor, 4)
                pygame.draw.line(screen, GREY, link2_anchor, link3_anchor, 4)
                pygame.draw.line(screen, GREY, link3_anchor, crs_anchor, 4)

                # Drawing the joints
                pygame.draw.circle(screen, RED, link1_anchor, r.crs_radius)
                pygame.draw.circle(screen, RED, link2_anchor, r.crs_radius)
                pygame.draw.circle(screen, RED, link3_anchor, r.crs_radius)
                pygame.draw.circle(screen, CURSOR, crs_anchor, r.crs_radius * 1.25)
            elif vision == 'min':
                pygame.draw.circle(screen, CURSOR, crs_anchor, r.crs_radius * 1.25)

            # Drawing a hologram of the cursor if cursor currently outside the window boundaries
            if crs_anchor[1] > r.height:
                pygame.draw.circle(screen, GREY, (crs_anchor[0], r.height), r.crs_radius * 1.25, width=2)
            if crs_anchor[1] < 0:
                pygame.draw.circle(screen, GREY, (crs_anchor[0], 0), r.crs_radius * 1.25, width=2)
            if crs_anchor[0] > r.width:
                pygame.draw.circle(screen, GREY, (r.width, crs_anchor[1]), r.crs_radius * 1.25, width=2)
            if crs_anchor[0] < 0:
                pygame.draw.circle(screen, GREY, (0, crs_anchor[1]), r.crs_radius * 1.25, width=2)

            # Defining how much each link rotates. Will be set by PCA later.
            link_rot1 += r.crs_x
            link_rot2 += r.crs_y
            link_rot3 += r.crs_z

            if link_rot1 > 360: link_rot1 = link_rot1 - 360
            if link_rot2 > 360: link_rot2 = link_rot2 - 360
            if link_rot3 > 360: link_rot3 = link_rot3 - 360

            if link_rot1 < 0: link_rot1 = link_rot1 + 360
            if link_rot2 < 0: link_rot2 = link_rot2 + 360
            if link_rot3 < 0: link_rot3 = link_rot3 + 360

            # draw each test target
            for i in range(8):
                tgt_x = r.tgt_x_list[r.list_tgt[i]]
                tgt_y = r.tgt_y_list[r.list_tgt[i]]
                pygame.draw.circle(screen, GREEN, (int(tgt_x), int(tgt_y)), r.tgt_radius, 2)

            # Display scores:
            font = pygame.font.Font(None, 50)
            text = font.render(str(r.score), True, RED)
            screen.blit(text, (1250, 10))

            # Debugging purposes. Displaying information online
            vel1 = font.render("{:.3f}".format(r.crs_x), True, RED)
            vel2 = font.render("{:.3f}".format(r.crs_y), True, RED)
            vel3 = font.render("{:.3f}".format(r.crs_z), True, RED)
            deg1 = font.render("{:.3f}".format(link_rot1), True, RED)
            deg2 = font.render("{:.3f}".format(link_rot2), True, RED)
            deg3 = font.render("{:.3f}".format(link_rot3), True, RED)
            x_coord = font.render(str(r.crs_anchor_x), True, GREEN)
            y_coord = font.render(str(r.crs_anchor_y), True, GREEN)
            screen.blit(vel1, (15, 10))
            screen.blit(vel2, (15, 60))
            screen.blit(vel3, (15, 110))
            screen.blit(deg1, (15, 160))
            screen.blit(deg2, (15, 210))
            screen.blit(deg3, (15, 260))
            screen.blit(x_coord, (15, 310))
            screen.blit(y_coord, (15, 320))


            # --- update the screen with what we've drawn.
            pygame.display.flip()

            # --- Limit to 50 frames per second
            clock.tick(50)

    # Once we have exited the main program loop, stop the game engine and release the capture
    pygame.quit()
    print("game engine object released in customization.")
    hands.close()
    print("pose estimation object released terminated in customization.")
    cap.release()
    cv2.destroyAllWindows()
    print("openCV object released in customization.")


def save_parameters(self, drPath):
    """
    function to save customization values
    :param self: CustomizationApplication tkinter Frame. needed to retrieve textbox values programmatically
    :param drPath: path where to load the BoMI forward map
    :return:
    """
    # retrieve values stored in the textbox
    rot = int(self.retrieve_txt_rot())
    gx_custom = float(self.retrieve_txt_gx())
    gy_custom = float(self.retrieve_txt_gy())
    scale = [gx_custom, gy_custom, 1]
    ox_custom = int(self.retrieve_txt_ox())
    oy_custom = int(self.retrieve_txt_oy())
    off = [ox_custom, oy_custom, 1]

    # save customization values
    with open(drPath + "rotation_custom.txt", 'w') as f:
        print(rot, file=f)
    np.savetxt(drPath + "scale_custom.txt", scale)
    np.savetxt(drPath + "offset_custom.txt", off)

    print('Customization values have been saved. You can continue with practice.')

def start_reaching(drPath, check_mouse, lbl_tgt, num_joints, joints, dr_mode):
    """
    function to perform online cursor control - practice
    :param drPath: path where to load the BoMI forward map and customization values
    :param check_mouse: tkinter Boolean value that triggers mouse control instead of reaching task
    :param lbl_tgt: label in the main window that shows number of targets remaining
    :return:
    """
    pygame.init()

    # get value from checkbox - is mouse enabled?
    mouse_enabled = check_mouse.get()

    # set parameters for mediapipe detection and tracking
    min_detection = 0.6
    min_confidence = 0.6

    # Define some colors
    BLACK = (0, 0, 0)
    GREY = (0.50 * 255, 0.50 * 255, 0.50 * 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    YELLOW = (255, 255, 0)
    CURSOR = (0.19 * 255, 0.65 * 255, 0.4 * 255)


    # Create object of openCV, Reaching class and filter_butter3
    cap = cv2.VideoCapture(0)
    r = Reaching()
    filter_curs = FilterButter3("lowpass_4")

    # Defining 3 link surfaces
    link1_orig = pygame.Surface((r.link_length, 75))
    link2_orig = pygame.Surface((r.link_length, 75))
    link3_orig = pygame.Surface((r.link_length, 75))

    # for making transparent background while rotating the image
    link1_orig.set_colorkey(BLACK)
    link2_orig.set_colorkey(BLACK)
    link3_orig.set_colorkey(BLACK)

    # fill the rectangle / surface with the color GREY
    link1_orig.fill(GREY)
    link2_orig.fill(GREY)
    link3_orig.fill(GREY)

    # creating a copy of original image for smooth rotation
    link1 = link1_orig.copy()
    link2 = link2_orig.copy()
    link3 = link3_orig.copy()

    # Defining the initial angle of rotation
    link_rot1 = 0
    link_rot2 = 0
    link_rot3 = 0

    # Open a new window
    size = (r.width, r.height)
    screen = pygame.display.set_mode(size)
    # screen = pygame.display.toggle_fullscreen()

    # The clock will be used to control how fast the screen updates
    clock = pygame.time.Clock()

    # Initialize stopwatch for counting time elapsed in the different states of the reaching
    timer_enter_tgt = StopWatch()
    timer_start_trial = StopWatch()
    timer_practice = StopWatch()

    # initialize targets and the reaching log file header
    reaching_functions.initialize_targets(r)
    reaching_functions.write_header(r)

    # load BoMI forward map parameters for converting body landmarks into cursor coordinates
    map = load_bomi_map(dr_mode, drPath)

    # initialize MediaPipe Pose
    # mp_pose = mp.solutions.pose
    mp_hands = mp.solutions.hands
    # pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, upper_body_only=True, smooth_landmarks=False)
    hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5, max_num_hands=1)
    mp_holistic = mp.solutions.holistic
    holistic = mp_holistic.Holistic(min_detection_confidence=min_detection, min_tracking_confidence=min_confidence,
                                    upper_body_only=True, smooth_landmarks=False)

    # load scaling values for covering entire monitor workspace
    rot_dr = pd.read_csv(drPath + 'rotation_dr.txt', sep=' ', header=None).values
    scale_dr = pd.read_csv(drPath + 'scale_dr.txt', sep=' ', header=None).values
    scale_dr = np.reshape(scale_dr, (scale_dr.shape[0],))
    off_dr = pd.read_csv(drPath + 'offset_dr.txt', sep=' ', header=None).values
    off_dr = np.reshape(off_dr, (off_dr.shape[0],))
    rot_custom = pd.read_csv(drPath + 'rotation_custom.txt', sep=' ', header=None).values
    scale_custom = pd.read_csv(drPath + 'scale_custom.txt', sep=' ', header=None).values
    scale_custom = np.reshape(scale_custom, (scale_custom.shape[0],))
    off_custom = pd.read_csv(drPath + 'offset_custom.txt', sep=' ', header=None).values
    off_custom = np.reshape(off_custom, (off_custom.shape[0],))

    # initialize lock for avoiding race conditions in threads
    lock = Lock()

    # global variable accessed by main and mediapipe threads that contains the current vector of body landmarks
    global body
    body = np.zeros((num_joints,))  # initialize global variable

    # start thread for OpenCV. current frame will be appended in a queue in a separate thread
    q_frame = queue.Queue()
    opencv_thread = Thread(target=get_data_from_camera, args=(cap, q_frame, r))
    opencv_thread.start()
    print("openCV thread started in practice.")

    # initialize thread for mediapipe operations
    mediapipe_thread = Thread(target=mediapipe_forwardpass,
                              args=(hands, mp_hands, lock, q_frame, r, num_joints, joints))
    mediapipe_thread.start()
    print("mediapipe thread started in practice.")

    # initialize thread for writing reaching log file
    wfile_thread = Thread(target=write_practice_files, args=(r, timer_practice))
    timer_practice.start()  # start the timer for PracticeLog
    wfile_thread.start()
    print("writing reaching log file thread started in practice.")

    print("cursor control thread is about to start...")

    # -------- Main Program Loop -----------
    while not r.is_terminated:
        # --- Main event loop
        for event in pygame.event.get():  # User did something
            if event.type == pygame.QUIT:  # If user clicked close
                r.is_terminated = True  # Flag that we are done so we exit this loop
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_x:  # Pressing the x Key will quit the game
                    r.is_terminated = True
                if event.key == pygame.K_p:  # Pressing the p Key will pause/resume the game
                    reaching_functions.pause_acquisition(r, timer_practice)
                if event.key == pygame.K_SPACE:  # Pressing the space Key will click the mouse
                    pyautogui.click(r.crs_x, r.crs_y)

        if not r.is_paused:
            # Copy old cursor position
            r.old_crs_x = r.crs_anchor_x  # changed from r.crs_x
            r.old_crs_y = r.crs_anchor_y  # changed from r.crs_y

            # get current value of body
            r.body = np.copy(body)

            # apply BoMI forward map to body vector to obtain cursor position.
            # r.crs_x, r.crs_y, r.crs_z = reaching_functions.update_cursor_position\
            #     (r.body, map, rot_dr, scale_dr, off_dr, rot_custom, scale_custom, off_custom)

            # apply BoMI forward map to body vector to obtain 3 different degrees.
            r.crs_x, r.crs_y, r.crs_z = reaching_functions.update_degrees\
                (r.body, map, rot_dr, scale_dr, off_dr, rot_custom, scale_custom, off_custom)

            # Assigning Anchor Points
            pos1 = (size[0] / 2, size[1] * 0.85)

            link1rect = link1.get_rect()
            link2rect = link2.get_rect()
            link3rect = link3.get_rect()

            link1_anchor = (size[0] / 2, size[1] * 0.85)
            link2_anchor = ((link1_anchor[0] + (math.cos(math.radians(link_rot1)) * link1rect.w)),
                            link1_anchor[1] - (math.sin(math.radians(link_rot1)) * link1rect.w))
            link3_anchor = (link2_anchor[0] + math.cos(math.radians(link_rot2)) * link2rect.w,
                            link2_anchor[1] - (math.sin(math.radians(link_rot2)) * link2rect.w))
            crs_anchor = (link3_anchor[0] + math.cos(math.radians(link_rot3)) * link3rect.w,
                          link3_anchor[1] - (math.sin(math.radians(link_rot3)) * link3rect.w))

            # Defining anchor coordinates
            r.crs_anchor_x = crs_anchor[0]
            r.crs_anchor_y = crs_anchor[1]

            # # Moving the paddles when the user uses the arrow keys
            # keys = pygame.key.get_pressed()
            # if keys[pygame.K_w]:
            #     r.crs_y -= 75
            # if keys[pygame.K_a]:
            #     r.crs_x -= 75
            # if keys[pygame.K_s]:
            #     r.crs_y += 75
            # if keys[pygame.K_d]:
            #     r.crs_x += 75

            # Check if the crs is greater than set angle magnitude velocity:
            max_angle_velocity = 7
            min_angle_velocity = -7

            if r.crs_x >= max_angle_velocity:
                r.crs_x = max_angle_velocity
            if r.crs_x <= min_angle_velocity:
                r.crs_x = min_angle_velocity
            if r.crs_y >= max_angle_velocity:
                r.crs_y = max_angle_velocity
            if r.crs_y <= min_angle_velocity:
                r.crs_y = min_angle_velocity
            if r.crs_z >= max_angle_velocity:
                r.crs_z = max_angle_velocity
            if r.crs_z <= min_angle_velocity:
                r.crs_z = min_angle_velocity

            # Filter the cursor
            # r.crs_x, r.crs_y = reaching_functions.filter_cursor(r, filter_curs)

            # Filter the angles
            # r.crs_x, r.crs_y, r.crs_z = reaching_functions.filter_links(r, filter_curs)

            # if mouse checkbox was enabled do not draw the reaching GUI, only change coordinates of the computer cursor
            if mouse_enabled:
                pyautogui.moveTo(r.crs_x, r.crs_y)
            else:

                # Set target position to update the GUI
                reaching_functions.set_target_reaching(r)

                # First, clear the screen to black. In between screen.fill and pygame.display.flip() all the draw
                screen.fill(BLACK)

                # Defining how much each link rotates via PCA
                link_rot1 += r.crs_x
                link_rot2 += r.crs_y
                link_rot3 += r.crs_z

                if link_rot1 > 360: link_rot1 = link_rot1 - 360
                if link_rot2 > 360: link_rot2 = link_rot2 - 360
                if link_rot3 > 360: link_rot3 = link_rot3 - 360

                if link_rot1 < 0: link_rot1 = link_rot1 + 360
                if link_rot2 < 0: link_rot2 = link_rot2 + 360
                if link_rot3 < 0: link_rot3 = link_rot3 + 360

                r.theta1 = link_rot1
                r.theta2 = link_rot2
                r.theta3 = link_rot3

                # Do not show the cursor in the blind trials when the cursor is outside the home target
                if not r.is_blind:
                    # draw cursor
                    # pygame.draw.circle(screen, CURSOR, (int(r.crs_x), int(r.crs_y)), r.crs_radius)
                    # Drawing the links between the joints
                    pygame.draw.line(screen, GREY, link1_anchor, link2_anchor, 4)
                    pygame.draw.line(screen, GREY, link2_anchor, link3_anchor, 4)
                    pygame.draw.line(screen, GREY, link3_anchor, crs_anchor, 4)

                    # Drawing the joints
                    pygame.draw.circle(screen, RED, link1_anchor, r.crs_radius)
                    pygame.draw.circle(screen, RED, link2_anchor, r.crs_radius)
                    pygame.draw.circle(screen, RED, link3_anchor, r.crs_radius)
                    pygame.draw.circle(screen, CURSOR, crs_anchor, r.crs_radius * 1.25)

                # draw target. green if blind, state 0 or 1. yellow if notBlind and state 2
                if r.state == 0:  # green
                    pygame.draw.circle(screen, GREEN, (int(r.tgt_x), int(r.tgt_y)), r.tgt_radius, 2)
                elif r.state == 1:
                    pygame.draw.circle(screen, GREEN, (int(r.tgt_x), int(r.tgt_y)), r.tgt_radius, 2)
                elif r.state == 2:  # yellow
                    if r.is_blind:  # green again if blind trial
                        pygame.draw.circle(screen, GREEN, (int(r.tgt_x), int(r.tgt_y)), r.tgt_radius, 2)
                    else:  # yellow if not blind
                        pygame.draw.circle(screen, YELLOW, (int(r.tgt_x), int(r.tgt_y)), r.tgt_radius, 2)

                # Drawing a hologram of the cursor if outside the boundaries
                if crs_anchor[1] > r.height:
                    pygame.draw.circle(screen, GREY, (crs_anchor[0], r.height), r.crs_radius * 1.25, width=2)

                # Display scores:
                font = pygame.font.Font(None, 50)
                text = font.render(str(r.score), True, RED)
                screen.blit(text, (1250, 10))

                # Debugging purposes. Displaying information online
                deg1 = font.render("{:.3f}".format(r.crs_x), True, RED)
                deg2 = font.render("{:.3f}".format(r.crs_y), True, RED)
                deg3 = font.render("{:.3f}".format(r.crs_z), True, RED)
                x_coord = font.render(str(r.crs_anchor_x), True, GREEN)
                y_coord = font.render(str(r.crs_anchor_y), True, GREEN)
                screen.blit(deg1, (15, 10))
                screen.blit(deg2, (15, 60))
                screen.blit(deg3, (15, 110))
                screen.blit(x_coord, (15, 160))
                screen.blit(y_coord, (15, 210))

                # --- update the screen with what we've drawn.
                pygame.display.flip()

                # After showing the cursor, check whether cursor is in the target
                # reaching_functions.check_target_reaching(r, timer_enter_tgt) OLD CODE FROM X-Y
                reaching_functions.check_target_reaching_links(r, timer_enter_tgt)
                # Then check if cursor stayed in the target for enough time
                reaching_functions.check_time_reaching(r, timer_enter_tgt, timer_start_trial, timer_practice)

                # update label with number of targets remaining
                tgt_remaining = 248 - r.trial + 1
                lbl_tgt.configure(text='Number of targets remaining ' + str(tgt_remaining))
                lbl_tgt.update()

                # --- Limit to 50 frames per second
                clock.tick(50)

    # Once we have exited the main program loop, stop the game engine and release the capture
    pygame.quit()
    print("game engine object released in practice.")
    # pose.close()
    hands.close()
    print("pose estimation object released in practice.")
    cap.release()
    cv2.destroyAllWindows()
    print("openCV object released in practice.")


def get_data_from_camera(cap, q_frame, r):
    '''
    function that runs in the thread to capture current frame and put it into the queue
    :param cap: object of OpenCV class
    :param q_frame: queue to store current frame
    :param r: object of Reaching class
    :return:
    '''
    while not r.is_terminated:
        if not r.is_paused:
            ret, frame = cap.read()
            q_frame.put(frame)
    print('OpenCV thread terminated.')


def mediapipe_forwardpass(hands, mp_hands, lock, q_frame, r, num_joints, joints):
    """
    function that runs in the thread for estimating pose online
    :param pose: object of Mediapipe class used to predict poses
    :param mp_pose: object of Mediapipe class for extracting body landmarks
    :param lock: lock for avoiding race condition on body vector
    :param q_frame: queue where to append current webcam frame
    :param r: object of Reaching class
    :return:
    """
    global body
    while not r.is_terminated:
        if not r.is_paused:
            # not sure if we want to put try/catch here, just in case "ask forgiveness, not permission"
            # try:
            # get current frame from thread
            curr_frame = q_frame.get()
            body_list = []

            # Flip the image horizontally for a later selfie-view display, and convert the BGR image to RGB.
            image = cv2.cvtColor(cv2.flip(curr_frame, 1), cv2.COLOR_BGR2RGB)
            # To improve performance, optionally mark the image as not writeable to pass by reference.
            image.flags.writeable = False
            results = hands.process(image)
            # results = pose.process(image)
            # results_hands = hands.process(image)

            # if joints[0, 0] == 1 or joints[1, 0] == 1 or joints[2, 0] == 1:
            #     if not results.pose_landmarks:
            #         continue
            #     if joints[0, 0] == 1:
            #         body_list.append(results.pose_landmarks.landmark[mp_holistic.PoseLandmark.NOSE].x)
            #         body_list.append(results.pose_landmarks.landmark[mp_holistic.PoseLandmark.NOSE].y)
            #     if joints[1, 0] == 1:
            #         body_list.append(results.pose_landmarks.landmark[mp_holistic.PoseLandmark.RIGHT_EYE].x)
            #         body_list.append(results.pose_landmarks.landmark[mp_holistic.PoseLandmark.RIGHT_EYE].y)
            #         body_list.append(results.pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_EYE].x)
            #         body_list.append(results.pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_EYE].y)
            #     if joints[2, 0] == 1:
            #         body_list.append(results.pose_landmarks.landmark[mp_holistic.PoseLandmark.RIGHT_SHOULDER].x)
            #         body_list.append(results.pose_landmarks.landmark[mp_holistic.PoseLandmark.RIGHT_SHOULDER].y)
            #         body_list.append(results.pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_SHOULDER].x)
            #         body_list.append(results.pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_SHOULDER].y)

            if joints[3, 0] == 1 or joints[4, 0] == 1:
                if not results.multi_hand_landmarks:
                    continue
                # body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x)
                # body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y)
                if joints[4, 0] == 1:
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.WRIST].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.WRIST].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.THUMB_CMC].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.THUMB_CMC].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.THUMB_MCP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.THUMB_MCP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.THUMB_IP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.THUMB_IP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.THUMB_TIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.THUMB_TIP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.INDEX_FINGER_DIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.INDEX_FINGER_DIP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.MIDDLE_FINGER_DIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.MIDDLE_FINGER_DIP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.RING_FINGER_MCP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.RING_FINGER_MCP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.RING_FINGER_PIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.RING_FINGER_PIP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.RING_FINGER_DIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.RING_FINGER_DIP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.RING_FINGER_TIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.PINKY_MCP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.PINKY_MCP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.PINKY_PIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.PINKY_PIP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.PINKY_DIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.PINKY_DIP].y)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.PINKY_TIP].x)
                    body_list.append(results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.PINKY_TIP].y)

            body_mp = np.array(body_list)
            q_frame.queue.clear()

            # body_mp = np.reshape(body_mp_temp[np.argwhere(body_mp_temp)], ((num_joints*2,)))
            # body_mp = np.array((n_x, n_y, ls_x, ls_y, rs_x, rs_y))
            # body = np.divide(body_mp, norm)
            with lock:
                body = np.copy(body_mp)
            # except:
            #     print('Expection in mediapipe_forwardpass. Closing thread')
            #     r.is_terminated = True
    print('Mediapipe_forwardpass thread terminated.')


def write_practice_files(r, timer_practice):
    """
    function that runs in the thread for writing reaching log in a file
    :param r: object of Reaching class
    :param timer_practice: stopwatch that keeps track of elapsed time during reaching
    :return:
    """
    while not r.is_terminated:
        if not r.is_paused:
            starttime = time.time()

            log = str(timer_practice.elapsed_time) + "\t" + '\t'.join(map(str, r.body)) + "\t" + str(r.crs_x) + "\t" + \
                  str(r.crs_y) + "\t" + str(r.block) + "\t" + \
                  str(r.repetition) + "\t" + str(r.target) + "\t" + str(r.trial) + "\t" + str(r.state) + "\t" + \
                  str(r.comeback) + "\t" + str(r.is_blind) + "\t" + str(r.at_home) + "\t" + str(r.count_mouse) + "\t" + \
                  str(r.score) + "\n"

            with open(r.path_log + "PracticeLog.txt", "a") as file_log:
                file_log.write(log)

            # write @ 50 Hz
            time.sleep(0.033 - ((time.time() - starttime) % 0.033))

    print('Writing reaching log file thread terminated.')


# CODE STARTS HERE
if __name__ == "__main__":
    # initialize mainApplication tkinter window
    tk_window = tk.Tk()
    tk_window.geometry("1366x768")

    MainApplication(tk_window).pack(side="top", fill="both", expand=True)

    # initiate Tkinter mainloop
    tk_window.mainloop()
