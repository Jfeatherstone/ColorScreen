cd /tmp

# Download the python code
wget https://github.com/Jfeatherstone/ColorScreen/releases/download/v1.0/ColorScreen.py

# Make a folder to put the source
mkdir /usr/lib/colorscreen

# Move the file over
mv ColorScreen.py /usr/lib/colorscreen/colorscreen.py

echo "python /usr/lib/colorscreen/colorscreen.py" >> /usr/bin/colorscreen

chmod +x /usr/bin/colorscreen

echo "Installed to /usr/lib/colorscreen/"

cd $OLD_PWD
