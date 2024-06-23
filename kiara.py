import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymodbus3.client.sync import ModbusTcpClient
from pymodbus3.constants import Endian
from pymodbus3.payload import BinaryPayloadDecoder
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def read_registers(client, unit_id, start_address, num_registers):
    try:
        result = client.read_holding_registers(start_address, num_registers, unit=unit_id)
        if result.isError():
            return None
        return result.registers
    except Exception as e:
        logging.error(f"Error reading registers from Unit ID {unit_id}: {str(e)}")
        return None

def get_plc_info(client, unit_id):
    plc_info = {
        'Unit ID': unit_id,
        'Manufacturer': '',
        'Model': '',
        'Firmware Version': '',
        'Input Registers': {},
        'Holding Registers': {}
    }

    try:
        # Read manufacturer information
        manufacturer_registers = read_registers(client, unit_id, 0x0800, 8)
        if manufacturer_registers:
            decoder = BinaryPayloadDecoder.fromRegisters(manufacturer_registers, Endian.Big, wordorder=Endian.Big)
            plc_info['Manufacturer'] = decoder.decode_string(8).decode('utf-8').strip()
        
        # Read model information
        model_registers = read_registers(client, unit_id, 0x0808, 8)
        if model_registers:
            decoder = BinaryPayloadDecoder.fromRegisters(model_registers, Endian.Big, wordorder=Endian.Big)
            plc_info['Model'] = decoder.decode_string(8).decode('utf-8').strip()
        
        # Read firmware version
        firmware_registers = read_registers(client, unit_id, 0x0810, 4)
        if firmware_registers:
            plc_info['Firmware Version'] = '.'.join(map(str, firmware_registers))
        
        # Read input registers (example: first 10 registers)
        for reg_address in range(0, 10):
            reg_value = read_registers(client, unit_id, reg_address, 1)
            if reg_value:
                plc_info['Input Registers'][f'Register {reg_address}'] = reg_value[0]
        
        # Read holding registers (example: first 10 registers)
        for reg_address in range(0, 10):
            reg_value = read_registers(client, unit_id, reg_address + 1000, 1)
            if reg_value:
                plc_info['Holding Registers'][f'Register {reg_address}'] = reg_value[0]

    except Exception as e:
        logging.error(f"Error reading PLC info from Unit ID {unit_id}: {str(e)}")
    
    return plc_info if any(plc_info.values()) else None

def scan_ip_range(ip_range):
    found_plcs = []
    for ip in ip_range:
        target_ip = str(ip)
        try:
            for port in [502, 102]:  # Check common ICS ports
                client = ModbusTcpClient(target_ip, port=port)
                if client.connect():
                    logging.info(f"Found Modbus device at {target_ip}:{port}")
                    for unit_id in range(1, 601):  # Scan unit IDs from 1 to 600
                        plc_info = get_plc_info(client, unit_id)
                        if plc_info:
                            found_plcs.append((target_ip, plc_info))
                    client.close()
                    break  # Stop checking other ports if connection succeeded

        except socket.error:
            logging.error(f"Connection to {target_ip} failed. Check IP address or PLC availability.")

    return found_plcs

def scan_plc(target_ips):
    found_plcs = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for ip_range in target_ips:
            if '-' in ip_range:  # Range notation (e.g., 192.168.1.1-10)
                start_ip, end_ip = ip_range.split('-')
                ip_network = ipaddress.ip_network(f"{start_ip}/{end_ip}", strict=False)
                futures.append(executor.submit(scan_ip_range, ip_network.hosts()))
            else:
                try:
                    ip_network = ipaddress.ip_network(ip_range, strict=False)
                    futures.append(executor.submit(scan_ip_range, ip_network.hosts()))
                except ValueError:  # Invalid IP range format, treat as single IP
                    futures.append(executor.submit(scan_ip_range, [ipaddress.ip_address(ip_range)]))
        
        for future in as_completed(futures):
            found_plcs.extend(future.result())

    return found_plcs

def load_target_ips_from_file(filename):
    target_ips = []
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):  # Ignore empty lines and comments
                target_ips.append(line)
    return target_ips

def parse_arguments():
    parser = argparse.ArgumentParser(description="PLC Scanner Tool - KIARA")
    parser.add_argument('target', metavar='target', type=str, help='Target IP address, range (e.g., 192.168.1.1-10), or file name')
    return parser.parse_args()

def main():
    args = parse_arguments()
    target_input = args.target

    if '-' in target_input or '/' in target_input:
        target_ips = [target_input]
    elif target_input.endswith('.txt'):
        target_ips = load_target_ips_from_file(target_input)
    else:
        target_ips = [target_input]

    found_plcs = scan_plc(target_ips)

    if found_plcs:
        logging.info("PLC(s) found:")
        # Sort PLCs by IP address for consistent output
        found_plcs.sort(key=lambda x: x[0])

        for ip, plc_info in found_plcs:
            print(f"At {ip}:")
            for key, value in plc_info.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"    {sub_key}: {sub_value}")
                else:
                    print(f"  {key}: {value}")
            print()
    else:
        logging.info("No PLCs found.")

if __name__ == "__main__":
    main()
