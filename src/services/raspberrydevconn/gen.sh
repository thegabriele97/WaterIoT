#!/bin/bash

while IFS= read -r line; do
    if [[ $line =~ ^Adafruit_DHT ]]; then
        echo $line > requirements_rpi.txt
        sed -i 's/Adafruit_DHT.*//g' requirements.txt
    fi
done < "requirements.txt"