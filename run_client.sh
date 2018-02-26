#! /bin/sh

#killing any previously running process
kill $(lsof -t -i:9200)
kill $(lsof -t -i:9202)

#running the clients
python3 ./client.py --id 0 &
python3 ./client.py --id 1 

kill $(lsof -t -i:9200)
kill $(lsof -t -i:9202)  