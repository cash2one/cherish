#!/bin/bash

openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ./auth-center.key -out ./auth-center.crt
chmod 400 *.key 
chmod 444 *.crt
