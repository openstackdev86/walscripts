#~/bin/bash
echo Starting the script to fetch the hardware details for $(date)

echo "started dfw1"
python /app/monitor/ilo_scripts/phase1/get_hvilo_data.py dfw1
echo "started dfw2"
python /app/monitor/ilo_scripts/phase1/get_hvilo_data.py dfw2
echo "started dfw3"
python /app/monitor/ilo_scripts/phase1/get_hvilo_data.py dfw3
echo "started dfw4"
python /app/monitor/ilo_scripts/phase1/get_hvilo_data.py dfw4
echo "started dal1"
python /app/monitor/ilo_scripts/phase1/get_hvilo_data.py dal1
echo "started dal2" 
python /app/monitor/ilo_scripts/phase1/get_hvilo_data.py dal2
echo "started dal3"
python /app/monitor/ilo_scripts/phase1/get_hvilo_data.py dal3
echo "started dal4"
python /app/monitor/ilo_scripts/phase1/get_hvilo_data.py dal4
echo "started dalstg2"
python /app/monitor/ilo_scripts/phase1/get_hvilo_data.py dalstg2
echo "started dfwstg2"
python /app/monitor/ilo_scripts/phase1/get_hvilo_data.py dfwstg2

sleep 20
echo executing the parsing script to trigger st2
python /app/monitor/ilo_scripts/phase1/parse-json.py
#if [ $? -ne 0 ]; then
#echo failed to trigger st2
#exit 1
#fi
