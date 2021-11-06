#!/bin/sh

docker run -d -p 8502:8501 \
  --mount type=bind,\
source=/home/drose/github/birb-watch/classifier/models/effecientNet_B3,\
target=/models/effecientNet_B3 \
  -e MODEL_NAME=effecientNet_B3 -t tensorflow/serving