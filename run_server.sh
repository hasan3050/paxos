#! /bin/sh

#killing any previously running process
kill -9 $(lsof -t -i:9100) 
kill -9 $(lsof -t -i:9102) 
kill -9 $(lsof -t -i:9104)  

# running the servers
python3 ./server.py --id 0 &
python3 ./server.py --id 1 &
python3 ./server.py --id 2 &