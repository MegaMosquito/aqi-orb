FROM raspbian/stretch

# Install pip and jq
RUN apt update && apt install -y python3-pip jq

# Install Neopixel support software
RUN pip3 install rpi_ws281x
RUN pip3 install adafruit-circuitpython-neopixel
RUN python3 -m pip install --force-reinstall adafruit-blinka
RUN pip3 install requests

# Copy over the source
COPY aqi-orb.py /
WORKDIR /

# Run the daemon
CMD python3 aqi-orb.py

