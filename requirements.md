# LPD Odin Integration Requirements Specification

Replace existing python data receiver and processor with C++ ODIN system.

## LPD Frame Producer
Priority: Should Have

Port Excalibur frame producer script to simulate LPD packet flow.


## ODIN Frame Receiver
Priority: Must Have

Create shared object plugin for ODIN's frame receiver to accept data from LPD's FEM.


## ODIN Frame Processor
Priority: Must Have

Create shared object plugin for ODIN's frame processor to accept and process data from the frame receiver.

## Travis CI Testing
Priority: Should Have

Use Travis CI to create testing for the above.


## Control Integration
Priority: Should Have

Integrate existing LPD python GUI with frame receiver and processor.


## Metadata Integration
Priority: Should Have

Adapt frame processor to integrate and store metadata from control GUI into HDF files.


## Live View
Priority: Could Have

Adapt ODIN to allow live view within GUI to still work.


## Port Excalibur scripts to LPD
Priority: Could Have

Rename all files, functions, classes and variables to use `LPD` where `Excalibur` is used.
