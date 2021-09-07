import sys
from PyQt5 import QtWidgets, QtCore, QtGui, Qt
import numpy as np
import time
import matplotlib.pyplot as plt
import pyautogui
from PIL import Image, ImageQt

# Delay on taking the screenshot (or pause afterwards, not quite sure)
pyautogui.PAUSE = .1

# Here are all of the transformation matrices that we use
# They are taken (mostly) from the link above

# Transform to the "linear-light" (XYZ) space
RGBtoXYZTransform = np.array([[.4124564, .3575761, .1804375],
                    [.2126729, .7151522, .0721750],
                    [.0193339, .1191920, .9503041]])

# Transform to the Long, Medium, Short (LMS) color space
# This uses the Hunt-Pointer-Estevez model
XYZtoLMSTransform = np.array([[.4002, .7076, -.0808],
                             [-.2263, 1.1653, .0457],
                             [0, 0, .9182]])

# Create a single operator to define both transformations
RGBtoLMSTransform = np.dot(XYZtoLMSTransform, RGBtoXYZTransform)
# And calculate the inverse transform to transform back after we modify the image
LMStoRGBTransform = np.linalg.inv(RGBtoLMSTransform)
#print(LMStoRGBTransform)

# These are our specific color blindness matrices
# Each on leaves two cones unmodified while transforming one

# Protanopia - Missing L cones -
protanopiaTransform = np.array([[0, 1.05118294, -.05116099],
                               [0, 1., 0],
                               [0, 0, 1.]])

# Deuteranopia - Missing M cones
deuteranopiaTransform = np.array([[1., 0, 0],
                                 [.9513092, 0, .04866992],
                                 [0, 0, 1.]])

# Tritanopia - Missing S cones
tritanopiaTransform = np.array([[1., 0, 0],
                               [0, 1., 0],
                               [-.86744736, 1.86727089, 0]])
# This method is outlined in the following repo (adapted from UE4)
# https://github.com/botman99/ColorBlindSimulation
# which itself references:
# https://ixora.io/projects/colorblindness/color-blindness-simulation-research/
def colorblindTransform(sRGBImageMatrix, transformType):
    # Make sure we have the right dimensions for the image
    # Should be: shape(imageMatrix) = (:,:,3)

    # For a detailed explanation of the entire process, see:
    # https://ixora.io/projects/colorblindness/color-blindness-simulation-research/
    
    
    # Transform from standard RGB to linear RGB
    # 2.4 is the "gamma" value; if you want more information look that up (or check it out on one of the previous pages)
    # These lines are a bit of dozy, so I would definitely check over the part of the ixora.io page
    # about this
    linearRGBImageMatrix = np.zeros_like(sRGBImageMatrix, dtype='double')
    linearRGBImageMatrix[sRGBImageMatrix <= .04045*255] = sRGBImageMatrix[sRGBImageMatrix <= .04045*255]/(255.*12.92)
    linearRGBImageMatrix[sRGBImageMatrix > .04045*255] = pow((sRGBImageMatrix[sRGBImageMatrix > .04045*255]/255 + .055)/1.055, 2.4)
    #print(len(np.unique(linearRGBImageMatrix))) # Print the number of unique items
    
    #linearRGBImageMatrix = pow(abs(sRGBImageMatrix), 2.2)

    # Apply our transformations to the cone space
    # The notation to apply any of our transformations is a little more complicated than a dot product
    # since the operators have to be applied from the left
    # Normally this would be trivial and we could just switch the order of arguments np.dot() but since
    # our pixel arrays are a (N,M,3) tensor, it's not quite that easy. The solution is to use the
    # np.tensordot() function, which allows us to specify exactly how many axes to work along
    
    # Note that we work with the transposed image matrix while in LMS space
    # We could convert back and forth, but that would just use 3 extra transpose operations and slow down evaluation
    LMSImageMatrix = np.tensordot(RGBtoLMSTransform, np.transpose(linearRGBImageMatrix), axes=1)
    
    # Apply the request colorblindness transformation
    if transformType.lower() == "protanopia":
        LMSImageMatrix = np.tensordot(protanopiaTransform, LMSImageMatrix, axes=1)
    elif transformType.lower() == "deuteranopia":
        LMSImageMatrix = np.tensordot(deuteranopiaTransform, LMSImageMatrix, axes=1)
    elif transformType.lower() == "tritanopia":
        LMSImageMatrix = np.tensordot(tritanopiaTransform, LMSImageMatrix, axes=1)
    elif transformType.lower() == 'original':
        pass # This is here just so I can loop over the transformation for testing
    else:
        raise Exception(f'Unsupported transform provided: {transformType}')
        
    # Now transform back to linear RGB space
    linearRGBImageMatrix = np.transpose(np.tensordot(LMStoRGBTransform, LMSImageMatrix, axes=1))

    # And back to standard RGB
    # Again, check out the webpage listed above for more information on this operation
    editedImageMatrix = np.zeros_like(sRGBImageMatrix, dtype='int')
    editedImageMatrix[linearRGBImageMatrix <= .0031308] = 255 * 12.92 * linearRGBImageMatrix[linearRGBImageMatrix <= .0031308]
    editedImageMatrix[linearRGBImageMatrix > .0031308] = 255 * (1.055 * pow(linearRGBImageMatrix[linearRGBImageMatrix > .0031308], .41666) - .055)
    
    # Make sure there aren't any non-physical values
    editedImageMatrix[editedImageMatrix > 255] = 255
    editedImageMatrix[editedImageMatrix < 0] = 0

    return editedImageMatrix


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, app):
        super(MainWindow, self).__init__()

        screen = app.primaryScreen()
        defaultWindowSize = screen.size()*.5
        self.resize(defaultWindowSize)

        self.centralWidget = QtWidgets.QWidget()

        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setAlignment(Qt.Qt.AlignCenter)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setAlignment(Qt.Qt.AlignCenter)
        # To create size grips
        self.statusBar()
        self.setStyleSheet("""
                           background: lightgray;
                           """)

        # Refresh button
        self.refreshBtn = QtWidgets.QPushButton('Refresh')
        self.refreshBtn.setMaximumWidth(100)
        self.refreshBtn.clicked.connect(self.refreshRegion)
        self.horizontalLayout.addWidget(self.refreshBtn)
        self.layout.setAlignment(Qt.Qt.AlignTop)
        self.layout.setSpacing(10)

        # Radio buttons
        self.buttonGroup = QtWidgets.QButtonGroup()

        self.originalBtn = QtWidgets.QRadioButton('Original')
        self.protanopiaBtn = QtWidgets.QRadioButton('Protanopia')
        self.deuteranopiaBtn = QtWidgets.QRadioButton('Deuteranopia')
        self.tritanopiaBtn = QtWidgets.QRadioButton('Tritanopia')

        self.buttonGroup.buttonClicked.connect(self.changeTransform)

        self.buttonGroup.addButton(self.originalBtn)
        self.buttonGroup.addButton(self.protanopiaBtn)
        self.buttonGroup.addButton(self.deuteranopiaBtn)
        self.buttonGroup.addButton(self.tritanopiaBtn)

        self.horizontalLayout.addWidget(self.originalBtn)
        self.horizontalLayout.addWidget(self.protanopiaBtn)
        self.horizontalLayout.addWidget(self.deuteranopiaBtn)
        self.horizontalLayout.addWidget(self.tritanopiaBtn)

        self.originalBtn.setChecked(True)

        self.layout.addLayout(self.horizontalLayout)

        # Where the image will be displayed
        self.imagePane = QtWidgets.QLabel()
        self.imagePane.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.imagePane.setAlignment(Qt.Qt.AlignCenter)
        #self.imagePane.setStyleSheet("""
        #                             outline-style: solid;
        #                             outline-color: black;
        #                             outline-width: 5px
        #                             """)

        self.layout.addWidget(self.imagePane)

        self.currentSC = None

        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)
        self.setWindowTitle('float')


    def refreshRegion(self):
        # Whichever radio button is selected
        currentTransform = self.buttonGroup.checkedButton().text()

        # Grab the region of the screen
        widgetLocation = self.imagePane.pos()
        windowLocation = self.pos()
        widgetDimensions = self.imagePane.size()

        absoluteWidgetRegion = (int(widgetLocation.x() + windowLocation.x()),
                                int(widgetLocation.y() + windowLocation.y()),
                                int(widgetDimensions.width()),
                                int(widgetDimensions.height()))

        # Hide the window
        self.setVisible(False)

        # Wait
        time.sleep(.1)

        # Now take a screenshot
        sc = pyautogui.screenshot(region=absoluteWidgetRegion)
        self.currentSC = sc 

        # Tranform it
        edited = colorblindTransform(np.array(sc), currentTransform)
        img = Image.fromarray(np.uint8(edited)).convert('RGBA')
        pixmap = QtGui.QPixmap.fromImage(ImageQt.ImageQt(img))

        self.imagePane.setPixmap(pixmap)
        # So that we can make the window smaller if we want
        self.imagePane.setMinimumSize(Qt.QSize(10, 10))

        self.setVisible(True)
        
        return

    def changeTransform(self):

        if self.currentSC != None:
            # Whichever radio button is selected
            currentTransform = self.buttonGroup.checkedButton().text()

            # Tranform it
            edited = colorblindTransform(np.array(self.currentSC), currentTransform)
            img = Image.fromarray(np.uint8(edited)).convert('RGBA')
            pixmap = QtGui.QPixmap.fromImage(ImageQt.ImageQt(img))

            self.imagePane.setPixmap(pixmap)
            # So that we can make the window smaller if we want
            self.imagePane.setMinimumSize(Qt.QSize(10, 10))

            return


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec())
