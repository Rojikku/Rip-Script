#!/usr/bin/env bash
rsync -av -P Rip.py rancher@192.168.0.253:/mnt/config/sonarr/Scripts/Rip.py
rsync -av -P Variables.py rancher@192.168.0.253:/mnt/config/sonarr/Scripts/Variables.py