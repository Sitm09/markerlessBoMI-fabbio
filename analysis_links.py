import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import cm
import os
import csv
import math
from reaching import Reaching

import reaching as r

sub_ID = 84
path_log = os.path.dirname(os.path.abspath(__file__)) + "/Results"
results_file = path_log + "/CompleteVision/" + str(sub_ID) + "/ResultsLogDay2.txt"
# i = 0
# p = 0
# with open(results_file, newline='') as csvfile:
#     data = csv.reader(csvfile, delimiter='\t', quotechar='|')
#     for row in data:
#         if '' in row:
#             print(i)
#             p += 1
#             if p > 20:
#                 exit()
#         i += 1


# Creates file from Log
results = np.genfromtxt(results_file, delimiter='\t', skip_header=1, autostrip=True)
# Removes preceding zeroes
no_zeroes = np.delete(results, np.where(results[:, 1] == 0), axis=0)
# Entire Day Success rate
day_success = no_zeroes[-1, -3] / no_zeroes[-1, -1] * 100

# Getting time it takes to get to the center target

