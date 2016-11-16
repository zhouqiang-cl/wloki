#!/bin/bash

source /home/work/LOKI
if [[ $? -ne 0 ]]; then
    exit 1
fi
pip install -U pip
pip install -r requirements.txt
