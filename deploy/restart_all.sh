#!/bin/bash

cd ../deploy/supervisor
supervisorctl restart all
supervisorctl status
