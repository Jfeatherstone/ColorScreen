#!/bin/sh

cd /tmp

# Download the python code
wget https://github.com/Jfeatherstone/ColorScreen/releases/download/v1.0/ColorScreen.py

# Make a folder to put the source (if it doesn't exist)
if [ ! -e /usr/lib/colorscreen ]; then
    mkdir /usr/lib/colorscreen
    echo "Created folder /usr/lib/colorscreen"
fi

# Move the file over
mv ColorScreen.py /usr/lib/colorscreen/colorscreen.py

echo "Installed to /usr/lib/colorscreen/"

# Created the run script
echo "python /usr/lib/colorscreen/colorscreen.py" > /usr/bin/colorscreen
chmod +x /usr/bin/colorscreen

echo "Created executable in /usr/bin/"
echo "Exiting..."

cd $OLD_PWD

exit 0
