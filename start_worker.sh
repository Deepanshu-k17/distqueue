#!/bin/sh
python worker.py --queue default --worker-id render_worker --concurrency 2 --poll-interval 1
