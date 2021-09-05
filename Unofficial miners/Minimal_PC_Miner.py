#!/usr/bin/env python3
# Minimal version of Duino-Coin PC Miner, useful for developing own apps.
# Created by revox 2020-2021
# Modifications made by Robert Furr (robtech21) and YeahNotSewerSide
# Mining Pools added by mkursadulusoy - 2021-09-06

import hashlib
import os
from socket import socket
import sys  # Only python3 included libraries
import time
import ssl
import select
from json import load as jsonload
import requests


soc = socket()

username = input('Username?\n> ')
diff_choice = input(
    'Use lower difficulty? (Y/N) [Leave empty for default of True]\n> ')
if diff_choice.lower == "n":
    UseLowerDiff = False
else:
    UseLowerDiff = True

def fetch_pools():
    while True:
        try:
            response = requests.get(
                "https://server.duinocoin.com/getPool"
            ).json()
            NODE_ADDRESS = response["ip"]
            NODE_PORT = response["port"]

            return NODE_ADDRESS, NODE_PORT
        except Exception as e:
            print(" Error retrieving mining node: "+ str(e)+ ", retrying in 15s","error")
            time.sleep(15)

while True:
    try:
        print('Searching for fastest connection to the server')
        try:
            NODE_ADDRESS, NODE_PORT = fetch_pools()
        except Exception as e:
            NODE_ADDRESS = "server.duinocoin.com"
            NODE_PORT = 2813
            print("Using default server port and address")
        soc.connect((str(NODE_ADDRESS), int(NODE_PORT)))
        print('Fastest connection found')
        server_version = soc.recv(100).decode()
        print ("Server Version: "+server_version)
        # Mining section
        while True:
            if UseLowerDiff:
                # Send job request for lower diff
                soc.send(bytes(
                    "JOB,"
                    + str(username)
                    + ",MEDIUM",
                    encoding="utf8"))
            else:
                # Send job request
                soc.send(bytes(
                    "JOB,"
                    + str(username),
                    encoding="utf8"))

            # Receive work
            job = soc.recv(1024).decode().rstrip("\n")
            # Split received data to job and difficulty 
            job = job.split(",")
            difficulty = job[2]

            hashingStartTime = time.time()
            base_hash = hashlib.sha1(str(job[0]).encode('ascii'))
            temp_hash = None

            for result in range(100 * int(difficulty) + 1):
                # Calculate hash with difficulty
                temp_hash = base_hash.copy()
                temp_hash.update(str(result).encode('ascii'))
                ducos1 = temp_hash.hexdigest()

                # If hash is even with expected hash result
                if job[1] == ducos1:
                    hashingStopTime = time.time()
                    timeDifference = hashingStopTime - hashingStartTime
                    hashrate = result / timeDifference

                    # Send numeric result to the server
                    soc.send(bytes(
                        str(result)
                        + ","
                        + str(hashrate)
                        + ",Minimal_PC_Miner",
                        encoding="utf8"))

                    # Get feedback about the result
                    feedback = soc.recv(1024).decode().rstrip("\n")
                    # If result was good
                    if feedback == "GOOD":
                        print("Accepted share",
                              result,
                              "Hashrate",
                              int(hashrate/1000),
                              "kH/s",
                              "Difficulty",
                              difficulty)
                        break
                    # If result was incorrect
                    elif feedback == "BAD":
                        print("Rejected share",
                              result,
                              "Hashrate",
                              int(hashrate/1000),
                              "kH/s",
                              "Difficulty",
                              difficulty)
                        break

    except Exception as e:
        print("Error occured: " + str(e) + ", restarting in 5s.")
        time.sleep(5)
        os.execl(sys.executable, sys.executable, *sys.argv)
