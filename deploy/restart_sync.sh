#!/bin/bash

source /home/work/LOKI
cd /home/work/supervisor
supervisorctl restart 'assets_sync'
supervisorctl status
