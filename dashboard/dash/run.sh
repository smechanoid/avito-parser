#!/bin/sh

unset LD_PRELOAD
export CUDA_HOME=/opt/cuda
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${CUDA_HOME}/lib64
export PATH=${CUDA_HOME}/bin:$PATH

source /opt/venv/python3.10/bin/activate

python app.py 
