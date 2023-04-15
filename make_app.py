#!/usr/bin/env python

# A tool for helping to build Z88 Compressed app files.
# This code reads in a bunch of lz49 compressed app files, creates an app header and writes them all together into a single app.

import glob
import os
import struct
import sys
from colorama import just_fix_windows_console
from termcolor import colored

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <rom_name>")

infile=sys.argv[1]
dirpath,filename=os.path.split(infile)
prefix=filename.split('.')[0]
romfiles=glob.glob(f"{dirpath}/{prefix}.lz[0123456789]")

app_header=b'\xa5\x5a'

# Read all of the pages into a dict for in-memory manipulation.
# Page number is the key, binary rom data is the value
rom_image={}
for file in sorted(romfiles):
    print(f"Reading {file}")
    suffix=file.split('.')
    rom_image[suffix]=open(file, mode='rb').read()

if len(rom_image) < 1:
    print("No ROMS loaded. Exiting.")
    sys.exit(1)

print(f"ROM Banks Loaded: {len(rom_image)}")
for bank in rom_image.keys():
    print(f"Bank: {bank} Length: {len(rom_image[bank])} {hex(len(rom_image[bank]))}")

app_header=b'\xa5\x5a' # File Identifier ($5AA5)
app_header+=len(rom_image).to_bytes(1, byteorder='little') # Number of banks
app_header+=b'\xff' # (0 for legacy RAM app, 255 for compressed)
app_header+=b'\x00\x00\x00' # Pointer for first DOR (if 0,0,0 then ROM Front DOR is used)
app_header+=b'\x00' # flags for required even banks
for bank in rom_image.keys():
    app_header+=b'\x00\x00' # Offset of block
    app_header+=(len(rom_image[bank]) & 255).to_bytes(1, byteorder='little') # Length of block, little end first.
    app_header+=(len(rom_image[bank])>>8 & 255).to_bytes(1, byteorder='little') # Length of block, big end last.
while len(app_header) < 40: # Pad the rest of the app record with nulls until it is 40 bytes long.
    app_header+=b'\x00'
 
print(f"Saving app: {dirpath}/{prefix}.app")
outfile=open(f"{dirpath}/{prefix}.app", "wb")
outfile.write(app_header)
for bank in rom_image:
    outfile.write(rom_image[bank])
outfile.close()
