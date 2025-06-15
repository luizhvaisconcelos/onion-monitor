#!/bin/bash
cd /opt/apps/omonitor
git add -A
git commit -m "$1"
git push origin main
