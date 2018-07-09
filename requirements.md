# LPD Odin Integration Requirements Specification

Create ODIN plugin to recieve, process and store data from the LPD detector, replacing the existing python system. Duplicate, adapt and optimise existing [Excalibur](https://github.com/dls-controls/excalibur-detector) code to work for LPD.

![](https://raw.githubusercontent.com/stfc-aeg/odin-workshop/master/images/odin_data.png)

## LPD Frame Producer
Priority: Should Have

Port Excalibur frame producer script to simulate LPD packet flow.

| Requirement | Conditions | Status |
|:-----------:|:----------:|:-------:|
| All detector specific names use `lpd`, `Lpd` or `LPD`. | No detector specific names for files, class, functions, variables, object or keys referring to Excalibur or other non-LPD detectors. Script still functions with no resulting errors. | 19/06/18: Complete |
| Retrieve frame number, packet number and SOF/EOF from last 8 bytes (trailer) of UDP packet rather than first 8 bytes (header) without error. | All retrieved data matches that of pcap file | 18/06/18: Complete |
| Remove Excalibur subframe handling from script. | Script stills handles and packages data correctly, sent frames match pcap file. | 21/06/18: Complete |


## LPD Frame Receiver
Priority: Must Have

Port frame receiver for LPD.

| Requirement | Conditions | Status |
|:-----------:|:----------:|:------:|
| All detector specific names use `lpd`, `Lpd` or `LPD`. | No detector specific names for files, class, functions, variables, object or keys referring to `Excalibur` or other non-LPD detectors. Script still functions with no resulting errors. | |
| Upon startup, read config and create shared memory buffer. |
| Listen for buffer config request from FP. Reply upon request. |
| Listen for incoming UDP packets. Upon detection, trigger decoder. |
| Add packet payload to shared memory buffer. |
| Handle packet loss. | Timeout frame after specified time. Send frame-ready with empty buffers in frame. |
| Handle out-of-order packets. | 
| Upon filled/timed out frame. FR-Control sends frame-ready message to FP. |
| When FR-Control receives frame-release message from FP, FR-Receive thread empties and opens buffer for re-use |


## LPD Frame Processor
Priority: Must Have

Port framer processor for LPD.

| Requirement | Conditions | Status |
|:-----------:|:----------:|:-------:|
| All detector specific names use `lpd`, `Lpd` or `LPD`. | No detector specific names for files, class, functions, variables, object or keys referring to `Excalibur` or other non-LPD detectors. Script still functions with no resulting errors. | |
| Upon startup, request shared memory configuration from FR. |
| Listen for frame-ready notification from FR. Upon receiving, trigger file writer. |
| Add metadata from control to frame before writing to file. |
| Write frame to HDF5 file. Send frame-release to FR upon completion. |


## Travis CI Testing
Priority: Should Have

Use Travis CI to create testing for the above.


## Control Integration
Priority: Should Have

Integrate existing LPD python GUI with frame receiver and processor.


## Live View
Priority: Could Have

Adapt ODIN to allow live view within GUI to still work.


## Port Excalibur scripts to LPD
Priority: Could Have

Rename all files, functions, classes and variables to use `LPD` where `Excalibur` is used.
