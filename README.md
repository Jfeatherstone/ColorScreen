<p align="center">
    <img src="./images/icon_512x512.png" align="center" width="256px"
</p>


<p align="center">
    <center><h2> Color Screen </h2></center>
</p>

Color Screen (title is WIP) is an application for simulating arbitrary regions of your screen as someone with various types of colorblindness would see it. This can be used to check presentations, scientific figures, etc. to make sure they are legible to everyone!

### Color Blindness Simulation

The application is currently able to simulate the three different types of dichromacy:

- Protanopia
- Deuteranopia
- Tritanopia

The simulation method was taken from [here](https://ixora.io/projects/colorblindness/color-blindness-simulation-research/), which outlines all of the variations in terms of their respective transformation matrices. I am by no means an expert on this very complicated subject, and don't claim to have any understanding that isn't presented in the above site. Comparing the results of my implementation with other sites/methods has gives good results, but the simulations should be taken as approximate regardless.
