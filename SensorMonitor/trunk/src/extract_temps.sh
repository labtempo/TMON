#!/bin/bash

# 
# Script that extracts the temperatures from the file.
# It assumes that the temperature is located at the 
# last column. 
#

awk '{print $(NF)}' "$1"