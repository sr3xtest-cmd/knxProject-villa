# Simulation setup — Burooj Square

## 1. Install the simulator

Install the current ETS and KNX Virtual on the same Windows PC. KNX Association states that KNX Virtual is a PC-based simulator that behaves like a real KNX installation and can be used with ETS without physical KNX hardware.

Use only the official KNX download from MyKNX. Do not use third-party copies.

## 2. Keep the original project safe

Work from Burooj_Square_Villa_V01.knxproj or another copy. Do not overwrite the verified original backup.

## 3. Connect ETS to KNX Virtual

Start KNX Virtual, then start ETS and select the KNX Virtual connection/interface in the connection settings.

## 4. Test the real project's Group Addresses

Open GROUP_TEST_MATRIX.csv.

For every row whose Role is command/value:
1. Open ETS Group Monitor.
2. Send the RecommendedAction/TestValues from the row.
3. Watch the returned telegrams and any matching feedback/status Group Address.
4. Record a result outside this pack.

For feedback/status rows, use READ/OBSERVE and do not force-write unless the application explicitly defines that object as writable.

## 5. Start with these functional groups

Test these first because they are represented clearly by their DPT/name:
- DPST-1-1 switching
- DPST-5-1 scaling
- DPST-3-7 relative dimming
- DPST-1-8 move/up-down
- DPST-1-17 stop
- DPST-9-1 temperature/setpoint-style values
- DPST-20-105 HVAC mode

Then continue through the remaining rows using the exact DPT from the CSV.

## 6. What counts as verified

Mark a function verified only when:
- ETS accepts the telegram without a DPT mismatch;
- the compatible KNX Virtual device/load reacts when one is configured;
- feedback/status returns on the expected Group Address;
- no unexpected linked object changes are seen.

## 7. Important boundary

A KNX Virtual pass verifies the KNX telegram path and the virtual function under test. It does not prove every Zennio-specific parameter in the final hardware. Those require final-device commissioning and functional testing.
