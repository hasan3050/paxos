#! /bin/sh

#killing any previously running process
kill $(lsof -t -i:9100) 
kill $(lsof -t -i:9102) 
kill $(lsof -t -i:9104)  

# running the servers
python3 ./server.py --id 0 &
python3 ./server.py --id 1 &
python3 ./server.py --id 2 &