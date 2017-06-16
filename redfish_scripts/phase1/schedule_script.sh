#~/bin/bash
echo Starting the script to fetch the hardware details for $(date)

python /app/monitor/ilo_scripts/phase1/get_hvilo_data.py dalstg2
#if [ $? -ne 0 ]; then
#echo failed to execute the script for dalstg2
#exit 1 
#fi
python /app/monitor/ilo_scripts/phase1/get_hvilo_data.py dfwstg2
#if [ $? -ne 0 ]; then
#echo failed to execute the script for dfwstg2
#exit 1
#fi
sleep 20
echo executing the parsing script to trigger st2
python /app/monitor/ilo_scripts/phase1/parse.json
#if [ $? -ne 0 ]; then
#echo failed to trigger st2
#exit 1
#fi
