# CadQuery Models


## 1. Overview

A bucket repository for all my CadQuery 3D models and experiments, except larger projects that deserver their own repo. [CadQuery](http://cadquery.readthedocs.io/) is an open source 3D CAD system where you use Python code to describe the design, rather than drawing it in some kind of GUI application.


## 2. Contents

Each subfolder is its own independent Python package and contains a single design, or a set of closely related designs. It also contains STL exports of the design with its default parameters. You can view STL files in 3D here on Github, which allows you to easily explore what the designs are about.

Content by folder:

* **`arcblock`.** A parametric, arc-shaped block with bolt holes. For example as furniture foot, guide or similar.

* **`case`.** A parametric, cuboid case made from six overlapping wall panels.

* **`chuteloft`.** A paremetric chute created from a loft between two U-shaped profiles.

* **`demos`.** Various demos of CadQuery features.

* **`experiments`.** Various own experiments with CadQuery features and prototypes of added features. Also experiments with how to organize CadQuery Python code well.

* **`footblock`.** A parametric cuboid foot block or spacer block with bolt holes. Optionally ramp shaped.

* **`latchmount`.** A parametric mount for a deadbolt latch, consisting of baseplate and counterplate.

* **`lenscover`.** A parametric cover that can be hooked to the top edge of an eyeglasses lens.

* **`lidfixer`.** A device for Auer Eurobox plastic boxes to help fix the lid in a closed position.

* **`mollemount`.** A parametric backplate for cases of smartphones and phablets with a Mollemount interface. Mollemount is a device mount system of my own design, using the PALS loops known from military backpacks and carry equipment.

* **`motormount`.** A parametric stepper motor mount in the shape of an L bracket.

* **`rodclip`.** A parametric clip for a rod that can be bolted into a recess using a single bolt.

* **`slidingknob`.** A parametric sliding knob with a window to see the current setting.

* **`wristmount`.** A parametric holder to mount a mobile device to the wrist or lower arm. UNFINISHED.

* **`xmount`.** Armor-X X-Mount Type M parts. This is a discontinued commercial mount system for smartphones and other small electronic devices. Inluded are a plug, socket (unfinished) and a wall mount, all fully parametric.


## 3. Code conventions

Follows the Python [file naming conventions](https://softwareengineering.stackexchange.com/a/308976).
