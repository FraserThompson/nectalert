# KINECT DOORBELL SURVEILLANCE SYSTEM

## What?

Utilizes a kinect sensor positioned somewhere around your front door and a Raspberry Pi positioned somewhere inside probably.

* Detects faces and lets you know if someone unknown is at the door via push notifications and a customisable noise
* Welcomes you and your comrades home with a friendly customisable greeding
* Streams video to your phone
* Saves images when motion is detected
* Switches to infrared mode at night
* Automatically terminates visitors with an inadequate social credit score [todo]

## Why?

I found a Kinect at a second hand store for $20 and thought I'd do something with it, also I needed a doorbell.

## How?

**WARNING: DOCUMENTATION NEEDS WORK SO IT MIGHT NOT WORK WITHOUT SOME ADDITIONAL TWEAKING**

1. Install dependencies: libfreenect, opencv, NGINX, uWSGI, hass, an MQTT broker (I used Mosquitto) [todo expand on this]
1. Get this repo and put it in `/home/pi/nectalert`
1. Put a `beep.wav` and a `doorbell.wav` in `./sounds`. Also optionally a file called `hello_[resident]` for each resident you want to recognize (determined by the array in `notifier.py`)
1. Configure homeassistant to look at the video feed and receive notifications by copying `./conf/configuration.yaml` to `/home/homeassistant/.homeassistant/configuration.yaml` and `./conf/automation.yaml` to `/home/homeassistant/.homeassistant/automation.yaml` but not before replacing my home's URL (smell.today) with your homes URL
1. Restart homeassistant with `sudo systemctl restart home-assistant@homeassistant.service`. If you want to see if it worked `journalctl -f -u home-assistant@homeassistant.service`
1. Copy the nginx configs from `./conf` to `/etc/nginx/sites-available` and `ln -s` them to `/etc/nginx/sites-enabled` but not before replacing my home's URL (smell.today) with your homes URL
1. Stick your kinect sensor up where you plan on having it
1. Copy `nectalert@pi.service` from `./conf` to `/etc/systemd/system` and do `sudo systemctl --system daemon-reload` and then `sudo systemctl enable nectalert@pi.service` 
1. Run `sudo systemctl start nectalert@pi.service` and go to https://[your pi]:8069 in a browser to verify it works and walk away!

You will need to buy a domain for your house and configure LetsEncrypt and have a router which does its own DNS if you want to do push notifications to your phone btw [todo expand on this]

### Registering faces

You'll also need to register some faces or it won't work. To do this:

Put input images in `embeddings/input_images/[name]` and run `python3 register_face.py [sam jim bob]`. This will take a while if you have a lot of images.

Then you should restart the service with `sudo sytemd restart nectalert@pi.service`.

### Testing accuracy

`python3 face_recognition_test.py filename.jpg` will run the face recognizer on that file and return the name of the face it found.

## Renewing certificate (these instructions are for you, Fraser)

1. `sudo nano certbot-renew`
1. Follow prompts
1. `sudo service restart nginx`