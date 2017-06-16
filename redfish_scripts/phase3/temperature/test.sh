#!/bin/bash
echo "scripted started"
time python /app/monitor/ilo_scripts/phase2/testing/temperature/get_hvilo_data.py dal1 >> time.txt &
time python /app/monitor/ilo_scripts/phase2/testing/temperature/get_hvilo_data.py dal2 >> time.txt &
time python /app/monitor/ilo_scripts/phase2/testing/temperature/get_hvilo_data.py dal3 >> time.txt &
time python /app/monitor/ilo_scripts/phase2/testing/temperature/get_hvilo_data.py dal4 >> time.txt &
time python /app/monitor/ilo_scripts/phase2/testing/temperature/get_hvilo_data.py dalstg2 >> time.txt &
time python /app/monitor/ilo_scripts/phase2/testing/temperature/get_hvilo_data.py dfw1 >> time.txt &
time python /app/monitor/ilo_scripts/phase2/testing/temperature/get_hvilo_data.py dfw2 >> time.txt &
time python /app/monitor/ilo_scripts/phase2/testing/temperature/get_hvilo_data.py dfw3 >> time.txt &
time python /app/monitor/ilo_scripts/phase2/testing/temperature/get_hvilo_data.py dfw4 >> time.txt &
time python /app/monitor/ilo_scripts/phase2/testing/temperature/get_hvilo_data.py dfwstg2 >> time.txt &
#python /app/monitor/ilo_scripts/phase2/testing/temperature/get_hvilo_data.py d &
