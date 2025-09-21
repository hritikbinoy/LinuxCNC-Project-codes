DEVELOPMENT OF 3D PRINTING SOFTWARE USING LINUXCNC 
This project is an ongoing prototype — the current stage focuses on LinuxCNC configuration and Python-based G-code generation. Future stages will expand into full 3D printer hardware integration.

What is this project?

This project is my first step towards building a 3D printer control system using open-source tools. It combines two main parts:
#LinuxCNC – a professional machine control system, which I set up to simulate a 3D printer by adding an extra axis for the extruder.
#Python GUI – a simple program I built where users can draw shapes and automatically generate G-code (the language machines understand).


FEATURES

LinuxCNC Configuration – I modified settings to add a 4th axis (extruder) for 3D printing.
Custom Python GUI – lets you draw shapes and create G-code files.
Integration – send the generated G-code to LinuxCNC to simulate 3D printer motion.
Future-ready – the setup is designed so real hardware (motors, extruder, sensors) can be added later.

HOW TO RUN

1. Install dependencies

sudo apt update
sudo apt install linuxcnc-uspace python3-pyqt5


2. Run the Python GUI

python3 printer_gui_test2(1).py


3. Start LinuxCNC with my config

linuxcnc configs/3dprinter/3dprinter.ini
