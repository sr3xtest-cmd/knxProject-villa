# Burooj Square — KNX Simulation Test Pack

Source project: Burooj_Square_Villa_ORIGINAL_BACKUP_20260917_172404.knxproj
ETS project title: (1) Burooj Square Villa
ETS ToolVersion in source: 6.2.7302.0

## Source coverage
- Group addresses: 618
- Device instances: 56
- Group addresses linked to at least one DeviceInstance: 0
- Device-to-Group Address links found: 0

## What this pack does
Turns the real ETS project database into a simulation-oriented test matrix. It does not rewrite the source project or invent missing device behavior. Use it with KNX Virtual and ETS Group Monitor to exercise Group Addresses and observe telegrams.

## Important limitation
The source project contains manufacturer-specific Zennio devices. KNX Virtual simulates its own virtual device set, not every Zennio application in this project. Therefore use this pack for telegram/DPT/Group Address validation and for end-to-end behavior on the subset that can be mapped to KNX Virtual virtual devices. A Zennio-specific application parameter cannot be declared fully simulated unless a matching virtual device exists.

## Files
- GROUP_TEST_MATRIX.csv — one row per Group Address with DPT, role, links and suggested test.
- DEVICE_GA_MATRIX.csv — device-to-Group Address relationships extracted from the actual project.
- SIMULATION_SETUP.md — step-by-step setup and testing workflow.
- OPERATOR_CHECKLIST.md — quick operator checklist.

## Role counts
- command/value: 318
- feedback: 286
- feedback/error: 14

## Test-kind counts
- 8-bit scaling: 161
- 1-bit control: 143
- switch: 116
- relative dimming: 70
- 2-byte float / temperature-style value: 33
- HVAC mode enum: 24
- unknown DPT: 21
- move/up-down: 18
- stop: 18
- text/string: 10
- 2-byte unsigned value: 4

## DPT counts
- DPST-5-1: 161
- DPST-1-6: 143
- DPST-1-1: 116
- DPST-3-7: 70
- DPST-9-1: 33
- DPST-20-105: 24
- (blank): 21
- DPST-1-8: 18
- DPST-1-17: 18
- DPST-16-0: 10
- DPST-7-7: 4