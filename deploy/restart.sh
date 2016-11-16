#!/bin/bash

source /home/work/LOKI
cd /home/work/supervisor
supervisorctl restart 'loki:*'
supervisorctl status
