# aqi-orb

This repo contains the code for a US government EPA (Environmental Protection Agency) AQI (Air Quality Index) color "orb", similar in appearance to the Purple Air "PA-I" indoor air quality sensor, but smaller. This orb can be placed on any surface in your house and it will monitor to an outdoor sensor and reflect its PM2.5 sensor value with with the corresponding AQI color. If you have your own PurpleAir outdoor sensor, you can use that. If you don't then you can use any sensor shown on the PurpleAir map. It looks like this:

...photo coming soon...

To be honest, I would have just bought this as a product from PurpleAir if they sold it (they are a great company) for say $100-$150. But they don't sell any indoor visualization device for their outdoor sensors, so I built this one. The total parts cost was about $20-$30(USD) and I spent a full Saturday designing, building, and coding it:

 - I used a Raspberry Pi zero WH ($15USD) but a ZeroW ($10) would work just as well
 - I used an 8-neopixel ring like this one: https://smile.amazon.com/ACROBOTIC-8-Pixel-Addressable-24-Bit-WS2812B/dp/B07HLS587W/ref=sr_1_7?dchild=1&keywords=neopixel+ring&qid=1599420043&sr=8-7 but in retrospect I think a single neopixel would be better (the ring is very bright!)
 - I installed a microUSB socket ($0.50USD) identical to thsi one: https://smile.amazon.com/HiLetgo-Adapter-Connector-Converter-pinboard/dp/B07W844N43/ref=sr_1_4?dchild=1&keywords=micro+usb+socket&qid=1599420174&sr=8-4 but you could just plug in a cable into the Raspberry Pi sock. I just wanted to be a little more elegant about it.
 
In addition to the above, I used wires, solder, and some plastic for the 3D prints (but the costs for all of that were under $1USD I would guess). Of course, you need a soldering tool, and either your own 3D printer or access to a friend's or a printing service.

PurpleAir map is here: https://www.purpleair.com/map?opt=1/mAQI/a10/cC0#1/9.6/-30

Purchase (optional) PurpleAir sensor here: https://www2.purpleair.com/collections/air-quality-sensors

AQI level breakpoints are here: https://aqs.epa.gov/aqsweb/documents/codetables/aqi_breakpoints.html

More AQI info is available here and I scraped the RGB colors from here too: https://cfpub.epa.gov/airnow/index.cfm?action=aqibasics.aqi

The 3D Model for the orb shell, and the interior supports for the Raspberry Pi ZeroWH, the microUSB socket, and the NeoPixel ring, is here: https://www.tinkercad.com/things/0YcAZ7Y7R6v

