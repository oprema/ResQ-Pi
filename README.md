# ResQ-Pi
A SMS and E-Mail notification system for elderly and handicaped people

I am pretty handicaped and I can get myself in situations where I need someone to come over to my flat and help me. This Raspberry Pi project should avoid that those situations get dangeours for me and others.

## How does it work?

ResQ-Pi waits for me to trigger an alarm with a small infrared control, a infrared control I always have with me when I am at home (within reach of the ResQ-Pis infrared reception).
Using the admin panel provided with this software and accessable with a browser, it is possible to configure the ResQ-Pi. Whenever the IR receiver detects an alarm, it sends one or more SMSs or E-Mails to a unlimited number of designated recipients. The web-front-end is available in German and English. A simple custom electronics (Raspberry Pi [HAT](https://www.raspberrypi.org/blog/introducing-raspberry-pi-hats/)) manages IR reception.

## What is needed to build a ResQ-Pi?

I use a Raspberry-Pi B+ or 2 (8GB sdcard) with a wireless LAN usb-stick and a 3G-GSM-Stick. The GSM-Stick should include a prepaid card with sufficient credits to be able to send SMS messages. The infrared receiver and three LEDs are available through a PCB connected to the GPIO-Port.

For the folks who thinks that the setup below is too difficult to manage I will provide an Raspbian-Image soon.

### Technology Stack:

- A Python daemon to handle IR (Lirc) commands
- SQLite to store configuration parameters
- Gammu to handle SMS sending
- Ruby and Sinatra for the web front end
- Unicorn as application server
- Nginx as reverse proxy

### Installation on a vanilla Raspbian (Jessie/Jessie-Lite)

Most packages used by ResQ-Pi come already installed on a vanilla Raspbian Jessie. The others that are needed are mentioned below.

First you want to setup your Raspi to be connected via ssh (there are lots of instructions how to do that on the internet). Once you have logged-in via ssh (ssh pi@<ip-address> password: **raspberry**) you want to update your Raspbian.

```
sudo apt-get update
sudo apt-get-upgrade 
```

And use all available Sdcard-Memory for our root partition
```
sudo raspi-config
-> Expand Filesystem
```

I also recommend to upgrade your firmware to the newest incarnation.
You want to do this with:

```
sudo apt-get install rpi-update
sudo rpi-update
sudo reboot
```

Change your hostname name
```
sudo raspi-config
-> Advanced Options -> Hostname -> resq-pi ... or choose a name you like.
```

From the Raspbian repos you need:
```
sudo apt-get install sqlite3 libsqlite3-dev ruby-dev python-dev python-pycurl nginx liblircclient-dev gammu python-gammu gammu-smsd lirc rubygems python-pip git ruby
```

Ruby and rubygems are usually already installed, but next you need install:
```
sudo gem install sinatra bundle unicorn --no-ri --no-rdoc
```
The python daemon needs some pip libraries as well:
```
sudo pip install docopt setproctitle pycrypto pylirc2
```

Now get the ResQ-Pi sources with:
```
git clone https://github.com/oprema/resq-pi
```
Setup Lirc:
Enabling the IR-Control feature in Raspbian is easy. Just open
```
sudo nano /boot/config.txt
```
and uncomment
```
#dtoverlay=lirc-rpi
```
Setup of Lirc depends on which IR remote control you want to use. The configuration is for a Apple IR Remote Control Model A1156. Other remote controls need to be teached in.

Configuration:
I have prepared a shell script to setup all configurations
```
cd ~/config && sudo ./install.sh
sudo reboot
```

Installing an empty sqlite database with:
```
sudo ~/resq_pi.py --resetdb --verbose
sudo chmod a+rwx ~/.resq-pi && sudo chmod a+w ~/.resq-pi/resq-pi.db
```
For the web-front-end do:
```
cd ~/app && bundle install    ... this takes a while
```
For a first front-end test execute:
```
bundle exec rackup -p4567 --host 0.0.0.0
```
And open a Web-Browser:
with http://resq-pi:4567 you should see a yellow start page.
Login with it's default password: **admin** is now possible.

If the web server is not found use the Raspi IP which you get with:
```
ifconfig
```

Schematic:

![Image of the ResQ-Pi Schematic](/images/resq-pi_Schaltplan.jpg)

The available LEDs indicate that an alarm is executed and in process. In it's default configuration you need to press the forward button on the Apple IR control three times to call for help.

SSL/TLS for nginx:
```
sudo mkdir -p /etc/nginx/conf.d/ssl && cd /etc/nginx/conf.d/ssl
sudo openssl genrsa -out server.key 2048
sudo openssl req -new -key server.key -out server.csr
sudo openssl x509 -req -days 1095 -in server.csr -signkey server.key -out server.crt
sudo reboot
```
Timezone:
Last but not least you should set the correct timezone.
```
sudo dpkg-reconfigure tzdata
```
