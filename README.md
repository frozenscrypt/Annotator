Image and Video Annotation Tool

Tool is under maintenance and feature additions with video annotation script coming soon!

Uses python 3

Installations:

sudo apt-get install python-tk
sudo apt-get isntall opencv-python
pip install Pillow


Instructions:

1. GUI utilizes images numbered starting from 0

2. The bash script renames all images in a directory as needed.
   run ./rename_images.sh
   If permission denied, first run "chmod +x rename_images.sh" (without quotes)  before the above command.

3. To run the GUI
   run python image_annotation_gui.py path-to-configFile

Config-file is a json file with keys to specify the filename(input folder directory) , image folder name, output folder name, multiplier to scale the images as needed(<1), frame number or the initial image number( tells the gui from where to start the annotation process)

Features:

1. Allows to draw multiple boxes to a image
2. Each time a box is drawn and a comment is added if needed, click submit to save the annotation
3. Clear button allows to clear a faulty annotation but once submitted, it can't be cleared
4. Next button calls the next image
5. Previous button calls the previous image and deletes the previous annotation from the data file
4. Log box displays the current operation on the current image


