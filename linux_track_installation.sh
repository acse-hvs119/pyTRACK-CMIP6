#!/bin/sh
#
# Shell script for installing TRACK-1.5.2 on a standard Linux system.
# Assumes that the user has the basic unconfigured TRACK package in home
# directory. 

apt-get update
apt-get install -y csh libnetcdf-dev libnetcdff-dev gcc gfortran

export CC=gcc FC=gfortran ARFLAGS=
export PATH=${PATH}:.

cd ~/TRACK-1.5.2

master -build -i=linux -f=linux

make utils

