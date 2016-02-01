#!/bin/bash
sudo cp lircd.conf /etc/lirc
sudo cp hardware.conf /etc/lirc
sudo cp resq-pi /etc/init.d
sudo cp unicorn /etc/init.d
sudo cp nginx.conf /etc/nginx
sudo update-rc.d resq-pi defaults
sudo update-rc.d unicorn defaults
line="53 17   * * *   root    /home/pi/resq_pi.py --credits"
(crontab -u pi -l; echo "$line" ) | crontab -u pi -
