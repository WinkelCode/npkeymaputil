import hid
from typing import Tuple
import argparse

# Constants
vendor = int(0x05ac)
product = int(0x024f)
max_request_size = int(0x7ff)

get_keymap_header = [0x05, 0x84, 0xd8, 0x00, 0x00, 0x00]
set_keymap_header = [0x06, 0x04, 0xd8, 0x00, 0x40, 0x00, 0x00, 0x00]

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Utility to read from or write a keymap to a keyboard.')
    parser.add_argument('-r', '--read', metavar='OUTPUT_FILE',
                        help='Read keymap from the keyboard and save to OUTPUT_FILE. Without -f, this will only display the command.')
    parser.add_argument('-w', '--write', metavar='INPUT_FILE',
                        help='Write keymap from INPUT_FILE to the keyboard. Without -f, this will only display the command.')
    parser.add_argument('-f', '--force', action='store_true',
                        help='Execute the read or write operation. Without this flag, the script will only print the operation to stdout.')
    args = parser.parse_args()
    if args.read and args.write:
        parser.error(
            'You can\'t specify both read and write operations at the same time.')
    elif not args.read and not args.write:
        parser.error('You must specify either a read or write operation.')

    # Functions
    def get_device(vendor: int, product: int) -> Tuple[bytes, bytes]:
        request_path = b''
        data_path = b''
        devices = hid.enumerate(vendor, product)
        if not devices:
            raise Exception(f'No devices matching VID: {vendor:04x} PID: {product:04x} found')
        for device in devices:
            if device['interface_number'] != -1 and device['usage'] == 1 and device['usage_page'] == int(0xff00):
                if b'&Col05' in device['path']:
                    if request_path != b'':
                        raise Exception(
                            f"Multiple request devices found: {request_path.decode()} and {device['path'].decode()}")
                    request_path = device['path']
                elif b'&Col06' in device['path']:
                    if data_path != b'':
                        raise Exception(
                            f"Multiple data devices found: {data_path.decode()} and {device['path'].decode()}")
                    data_path = device['path']
        if not request_path:
            raise Exception('No request device found')
        if not data_path:
            raise Exception('No data device found')
        return (request_path, data_path)

    def format_to_hex_template(int_list):
        chunk_size = 4
        chunks = [int_list[i:i + chunk_size] for i in range(0, len(int_list), chunk_size)]
        formatted_str = ''
        for idx, chunk in enumerate(chunks):
            hex_values = ' '.join(f'{i:02x}' for i in chunk)
            formatted_str += f'{idx * chunk_size:04x}  {hex_values}\n'
        return formatted_str
    
    def list_to_hex(int_list):
        return ' '.join(f'{i:02x}' for i in int_list)

    # Main
    (request_path, data_path) = get_device(vendor, product)
    r = hid.device()
    d = hid.device()
    r.open_path(request_path)
    d.open_path(data_path)

    if args.read:
        output_file = args.read
        if args.force:
            print(f'Reading keymap from keyboard and saving to {output_file}.')
            send_result = r.send_feature_report(get_keymap_header)
            print(f'Sent {send_result} bytes to keyboard.')
            receive_result = d.get_feature_report(0x06, max_request_size)
            print(f'Received {len(receive_result)} bytes from keyboard.')
            receive_result_pruned = receive_result[8:]
            with open(output_file, 'wb') as f:
                f.write(bytes(receive_result_pruned))
        else:
            print(
                f'Command to read keymap and save to {output_file} (no action taken, use -f to execute).')
            print(list_to_hex(get_keymap_header))
            print(f'Length: {len(get_keymap_header)} bytes')

    if args.write:
        input_file = args.write
        with open(input_file, 'rb') as f:
            input_file_bytes = f.read()
        write_keymap_buffer = set_keymap_header + list(input_file_bytes)
        if args.force:
            print(f'Writing keymap from {input_file} to keyboard.')
            send_result = d.send_feature_report(write_keymap_buffer)
            print(f'Sent {send_result} bytes to keyboard.')
        else:
            print(
                f'Command to write keymap from {input_file} to keyboard (no action taken, use -f to execute).')
            print(list_to_hex(write_keymap_buffer))
            print(f'Length: {len(write_keymap_buffer)} bytes')
    r.close()
    d.close()

if __name__ == '__main__':
    main()
