#!/bin/bash

python main.py
git config --global user.email "edosetiabudi2@protonmail.com"
git config --global user.name "ApiX"
git add .
git commit -am "Make it better"
git push origin master --force
