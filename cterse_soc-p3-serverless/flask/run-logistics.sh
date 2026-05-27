#!/bin/bash

cd examples/logistics

mkdir -p logs
mkdir -p db

echo "Starting merchant..."
python merchant_agent.py &>logs/merchant.log &
MERCHANT_PID=$!

echo "Starting labeler..."
python labeler_agent.py &>logs/labeler.log &
LABELER_PID=$!

echo "Starting wrapper..."
python wrapper_agent.py &>logs/wrapper.log &
WRAPPER_PID=$!

echo "Starting packer..."
python packer_agent.py &>logs/packer.log &
PACKER_PID=$!

echo "Press Ctrl-D to terminate servers..."
cat >/dev/null
kill $MERCHANT_PID $LABELER_PID $WRAPPER_PID $PACKER_PID
