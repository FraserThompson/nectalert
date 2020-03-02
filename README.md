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
1. Configure homeassistant to look at the video feed and receive notifications by adding this to your `/home/homeassistant/.homeassistant/configuration.yaml`:

```
mqtt:
    broker: localhost

binary_sensor:
    - platform: mqtt
      name: "Another Visitor"
      state_topic: "home/another_visitor"
      payload_on: "Yes"
      payload_off: "No"

notify:
  - name: everyone
    platform: group
    services:
      - service: mobile_app_[a_phone]
      - service: mobile_app_[another_phone]

camera:
  - platform: mjpeg
    mjpeg_url: https://[your hass url]:8069/video_feed

```

and this to automations.yaml:

```
- alias: 'Another Visitor'
  trigger:
    platform: state
    entity_id: binary_sensor.another_visitor
    to: 'on'
  action:
    service: notify.everyone
    data:
      title: "ANOTHER VISITOR!!!"
      message: "STAY A WHILE..."
      - alias: 'Another Visitor'
- alias: 'Motion detected'
  trigger:
    platform: mqtt
    topic: "home/frontdoor_movement"
    payload: "Yes"
  condition:
    - condition: time
      after: '21:00'
      before: '05:30'
    - condition: state
      entity_id: light.hue_color_lamp_7
      state: 'off'
  action:
    - service: light.turn_on
      entity_id: light.hue_color_lamp_7
    - delay:
        minutes: 10
    - service: light.turn_off
      entity_id: light.hue_color_lamp_7

```

1. Restart homeassistant with `sudo systemctl restart home-assistant@homeassistant.service`
1. Copy the nginx configs from `./conf` to `/etc/nginx/sites-available` and `ln -s` them to `/etc/nginx/sites-enabled` but not before replacing [your_URL] with your homes URL
1. Stick your kinect sensor up where you plan on having it
1. Copy `nectalert@pi.service` from `./conf` to `/etc/systemd/system` and do `sudo systemctl --system daemon-reload` and then `sudo systemctl enable nectalert@pi.service` 
1. Run `sudo sytemd start nectalert@pi.service` and go to https://[your pi]:8069 in a browser to verify it works and walk away!

You will need to buy a domain for your house and configure LetsEncrypt and have a router which does its own DNS if you want to do push notifications to your phone btw [todo expand on this]

### Registering faces

You'll also need to register some faces or it won't work. To do this:

1. Go to https://[your pi]:8069/register_face?name=[name of person]
1. If you've got a speaker connected you'll hear a sound. Stand in front of your Kinect while it takes photos of you. Might take a while. Move your face around and stuff during this time.
1. When you hear another sound you can leave physically but stay on the browser page until it says something.

Then you should restart the service with `sudo sytemd restart nectalert@pi.service`.