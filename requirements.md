# LDP Odin Integration Requirements Specification

Replace existing python data receiver and processor with C++ ODIN system.


## Frame Receiver
priority: Must

Create shared object plugin for ODIN's frame receiver to accept data from LDP's FEM.



## Frame Processor
Priority: Must

Create shared object plugin for Odin's frame processor to accept and process data from the frame receiver.



## Control Integration
Priority: Should

Integrate existing LDP python GUI with frame receiver and processor.



#### Metadata Integration
Priority: Should

Adapt frame processor to integrate and store metadata from control GUI into HDF files.



#### Live View
Priority: Could

Adapt ODIN to allow live view within GUI to still work.



## Testing
Priority: Could

Use Travis CI to create testing for the above.
