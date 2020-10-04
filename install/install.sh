cd /tmp

# Download the binary (packaged with dependencies)
wget https://github.com/Jfeatherstone/ColorScreen/releases/download/v1.0/ColorScreen

# Move the file over
mv ColorScreen /usr/bin/colorscreen

chmod +x /usr/bin/colorscreen

cd $OLD_PWD
