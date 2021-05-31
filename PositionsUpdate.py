"""
Created: 5/25/2021 08:43AM

Script used to update positions based on Fidelity .csv downloads.

Created By: Michael Stebbins
"""

import os
import shutil

positions_path = "C:/Users/Kiaru/OneDrive/Financial Tracking/Fidelity Positions"
output_path = "C:/Users/Kiaru/OneDrive/Financial Tracking/Fidelity Positions/Current Positions.csv"

# Get available files
file_list = [f for f in os.listdir(positions_path)
            if os.path.isfile(os.path.join(positions_path,f))
            if f != "Current Positions.csv"]

last_mod = 0
last_path = ""

for f in file_list:
    file_path = os.path.join(positions_path,f)
    if os.path.getmtime(file_path) > last_mod:
        last_mod = os.path.getmtime(file_path)
        last_path = file_path

shutil.copyfile(last_path,output_path)

print("Update Complete!")
