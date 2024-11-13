#!/bin/bash
echo "Running scheduled posts check..."
python -c 'from main import get_all_post; get_all_post()'
