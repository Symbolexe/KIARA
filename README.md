# KIARA - PLC Scanner Tool

KIARA is a Python tool for scanning and enumerating Programmable Logic Controllers (PLCs) using the Modbus protocol. It helps identify PLCs on a network, retrieve basic device information, and list available registers.

## Features

- Scan specified IP addresses, IP ranges, or a list from a file.
- Check common Modbus TCP ports (502, 102) for device availability.
- Retrieve PLC information including manufacturer, model, firmware version, and register values.
- Multi-threaded scanning for improved performance.

## Requirements

- Python 3.6 or higher
- `pymodbus3` library (`pip install pymodbus3`)

## Usage

1. Clone the repository:

   ```bash
   git clone https://github.com/symbolexe/KIARA
   cd KIARA
## Install dependencies (if not installed):
```bash
pip install pymodbus3
```
### Run the tool with Python:
```bash
python kiara.py <target>
```

Replace <target> with:

```Single IP address: python3 kiara.py 192.168.1.1```
or
```IP range: python KIARA.PY 192.168.1.1-10```

File containing IP addresses (one per line): python KIARA.PY targets.txt

View results in the console. PLC information will be displayed for each discovered device.

### Example
```bash
python kiara.py 192.168.1.1-10
```
### Output Example
```bash
PLC(s) found:
At 192.168.1.1:
  Unit ID: 1
  Manufacturer: Example Inc.
  Model: PLC-123
  Firmware Version: 1.0.0
  Input Registers:
    Register 0: 123
    Register 1: 456
  Holding Registers:
    Register 1000: 789
```
## Acknowledgments
- Inspired by the need for a simple yet effective PLC scanning tool.
- Thanks to the developers of pymodbus3 for the Modbus library.
