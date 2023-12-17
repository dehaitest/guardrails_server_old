#!/bin/bash

sudo docker build -t guardrails_demo .
sudo docker tag guardrails_demo:latest localhost:3000/guardrails_demo:latest
sudo docker push localhost:3000/guardrails_demo:latest
sudo docker image prune
