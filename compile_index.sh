#!/bin/bash

BASEURL="https://pokgak.github.io/ba-plotscripts/"
INDEX="index.html"

links=""
PLOTLIST=$(ls docs/*.html)
for plot in $PLOTLIST
do
    links+="<li><a href=\"https://pokgak.github.io/ba-plotscripts/${plot}\">${plot}</a></li>\n"
done

sed -e "s|<li>REPLACE</li>|$links|p" index.template
