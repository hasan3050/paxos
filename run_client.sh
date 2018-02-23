#! /bin/sh

#killing any previously running process
kill $(lsof -t -i:9200)
kill $(lsof -t -i:9202)

#running the clients
python3 ./client.py --id 0 &
#python3 ./client.py --id 1 --host "127.0.0.1" --port 9202 

kill $(lsof -t -i:9200)
kill $(lsof -t -i:9202)  