# A short walk

A little tool to allow small groups to create walks with voicenotes for each other.

This is designed for use with a specific place as the usual starting point - you can set the 
default GPS coordinates and scale of the map in config.json 

It requires ffmpeg for transcoding the audio, as I can't figure out how to get browsers to create 
audio in a consistent format.

Needs a tidy up probably.

# Install

install ffmpeg: https://ffmpeg.org/download.html

python3 install -r requirements.txt

cp static/splash/splash.example.jpg static/splash/splash.jpg

cp config.json.example config.json

edit for your use - fields are:

DOMAIN: domain where it's hosted
USER / PASS: basic auth username and password
GEO: starting point
SCALE: how zoomed in it is

asw.service.example might be useful to adapt for systemd

apache-ssl.conf is an example apache2 config for letsencrypt (you need https for recording via 
the browser except on localhost)

to run it with waitress (for production)

    pip3 install waitress

uncomment
    #serve(app, host='0.0.0.0', port=5001)

and comment
    app.run(host="0.0.0.0",port=5001)



# Run

python3 server_sqlite.py


# various links / sources

 * https://stackoverflow.com/questions/41622980/how-to-customize-touch-interaction-on-leaflet-maps#41631385
 * https://github.com/mdn/dom-examples/tree/main/media/web-dictaphone
 * https://stackoverflow.com/a/74087012
 * https://github.com/Leaflet/Leaflet.draw/issues/695#issuecomment-577151966
 * https://gis.stackexchange.com/questions/422864/getting-total-length-of-polyline-from-leaflet-draw
 
