#!/usr/bin/env python

# exploreaDORa - A tool for exploring the DOR (Directory Object Record) structure on Cambridge Z88 EPROM cartridges.
# This tool was written as part of an effort to split apart multi-rom file images back to individual apps to enable
# obsolete software to be reomved from compilation roms.

import glob
import os
import struct
import sys

country_codes={
    0 : "USA",
    1 : "France",
    2 : "Germany",
    3 : "UK",
    4 : "Denmark",
    5 : "Sweden",
    6 : "Italy",
    7 : "Spain",
    8 : "Japan",
    9 : "Iceland",
    10 : "Norway",
    11 : "Switzerland",
    12 : "Turkey",
    13 : "reserved",
    14 : "reserved",
    15 : "reserved"}

dor_types={
    0x13 : "ROM Front DOR",
    0x83 : "Application Rom"
}

def print_extended_pointer(text, pointer):
    pointer_txt=hex(0x3fff&struct.unpack('<H', pointer[0:2])[0])
    print(f"{text}: {pointer_txt}, (bank {pointer[2]} {hex(pointer[2])})")

def EPTxt(pointer):
    pointer_txt=hex(0x3fff&struct.unpack('<H', pointer[0:2])[0])
    return(f"(bank {pointer[2]} {pointer_txt})")


def read_app_dor(bank, pointer):
    # The application DOR structrure is defined at https://cambridgez88.jira.com/wiki/spaces/DN/pages/8618237/The+Application+DOR
    # In multi-rom images the extended pointer to brother DOR points us to our next application.
    app_dor_parent=rom_image[bank][pointer:pointer+3]
    app_dor_brother=rom_image[bank][pointer+3:pointer+6] # For Help Front DOR
    app_dor_son=rom_image[bank][pointer+6:pointer+9]
    app_dor_type=rom_image[bank][pointer+9]
    app_dor_length=rom_image[bank][pointer+10]
    app_dor_key_to_info=rom_image[bank][pointer+11]
    app_dor_length_of_info=rom_image[bank][pointer+12]
    #  app_dor_reserved_for_future=rom_image[bank][pointer+13:pointer+15] # Still not in use 35 years after Z88 was made, but maybe it still will be in the future.
    app_dor_app_letter=rom_image[bank][pointer+15]
    app_dor_continuous_ram=rom_image[bank][pointer+16]
    # app_dor_env_overhead=rom_image[bank][pointer+17:pointer+19] # Never used as Oz calculates the overhead dynamically.
    app_dor_unsafe_workspace=rom_image[bank][pointer+19:pointer+21]
    app_dor_safe_workspace=rom_image[bank][pointer+21:pointer+23]
    app_dor_entry_point=rom_image[bank][pointer+23:pointer+25]
    app_dor_sgement0_binding=rom_image[bank][pointer+25]
    app_dor_sgement1_binding=rom_image[bank][pointer+26]
    app_dor_sgement2_binding=rom_image[bank][pointer+27]
    app_dor_sgement3_binding=rom_image[bank][pointer+28]
    app_dor_application_type=rom_image[bank][pointer+29:pointer+31]
    app_dor_key_to_help=rom_image[bank][pointer+31]
    app_dor_length_of_help=rom_image[bank][pointer+32]
    app_dor_pointer_to_topics=rom_image[bank][pointer+33:pointer+36]
    app_dor_pointer_to_commands=rom_image[bank][pointer+36:pointer+39]
    app_dor_pointer_to_app_help=rom_image[bank][pointer+39:pointer+42]
    app_dor_pointer_to_token_base=rom_image[bank][pointer+42:pointer+45]
    app_dor_key_to_name_section=rom_image[bank][pointer+45]
    app_dor_length_of_name=rom_image[bank][pointer+46]
    app_dor_name=rom_image[bank][pointer+47:pointer+47+app_dor_length_of_name]
    app_dor_terminator=rom_image[bank][pointer+48+app_dor_length_of_name]

    print(f"DORData: Parent: {EPTxt(app_dor_parent)}, Brother: {EPTxt(app_dor_brother)}, Son: {EPTxt(app_dor_son)}, ", end='')
    print(f"Type: {hex(app_dor_type)}:{dor_types[app_dor_type]}, Length: {app_dor_length}")
    print(f"APPInfo({chr(app_dor_key_to_info)}/{app_dor_length_of_info}): Key: []{chr(app_dor_app_letter)}, ", end='')
    print(f"Continuous RAM reqd: {app_dor_continuous_ram*256} bytes, UnsafeWS: {struct.unpack('<H', app_dor_unsafe_workspace)[0]} bytes, ", end='')
    print(f"SafeWS: {struct.unpack('<H', app_dor_safe_workspace)[0]} bytes")
    print(f"  Entry_point: {hex(0x3fff&struct.unpack('<H', app_dor_entry_point)[0])}|{hex(struct.unpack('<H', app_dor_entry_point)[0])}, ", end='')
    print(f"Segment Bindings : 0:{app_dor_sgement0_binding}, 1:{app_dor_sgement1_binding}, 2:{app_dor_sgement2_binding}, 3:{app_dor_sgement3_binding}, ")
    app_type=[]
    if app_dor_application_type[0] & 1:
        app_type.append("good")
    if app_dor_application_type[0] & 2:
        app_type.append("bad")
    if app_dor_application_type[0] & 4:
        app_type.append("ugly")
    if app_dor_application_type[0] & 8:
        app_type.append("popdown")
    if app_dor_application_type[0] & 16:
        app_type.append("onlyone")
    if app_dor_application_type[0] & 32:
        app_type.append("preserve_screen")
    if app_dor_application_type[0] & 64:
        app_type.append("filemanager")
    if app_dor_application_type[0] & 128:
        app_type.append("autoboot")
    if app_dor_application_type[1] & 1:
        app_type.append("capslock")
    if app_dor_application_type[1] & 2:
        app_type.append("invcaps")
    if app_dor_application_type[1] & 128:
        app_type.append("ignore_returns")
    print(f"  App Types: {app_dor_application_type[0]}, {app_dor_application_type[1]} : {app_type}")
    print(f"HelpData({chr(app_dor_key_to_help)}/{app_dor_length_of_help}), Topics: {EPTxt(app_dor_pointer_to_topics)}, Commands: {EPTxt(app_dor_pointer_to_commands)}, ", end='')
    print(f"Help: {EPTxt(app_dor_pointer_to_app_help)}, TokenBase: {EPTxt(app_dor_pointer_to_token_base)}")
    print(f"Name({chr(app_dor_key_to_name_section)}/{app_dor_length_of_name}): {app_dor_name[:len(app_dor_name)-1].decode('ascii')}")
    #print(f"app_dor_terminator: {app_dor_terminator}")
    print()
    return(app_dor_brother[2], 0x3fff&struct.unpack('<H', app_dor_brother[0:2])[0]) # Brother DOR is the next app in the chain.


# Read the card header.

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <rom_name>")

infile=sys.argv[1]
dirpath,filename=os.path.split(infile)
prefix=filename.split('.')[0]
romfiles=glob.glob(f"{dirpath}/{prefix}.[0123456][0123456789]")

# Read all of the pages into a dict for in-memory manipulation.
# Page number is the key, binary rom data is the value
rom_image={}
for file in sorted(romfiles):
    print(f"Reading {file}")
    suffix=file.split('.')[1]
    rom_image[int(suffix)]=open(file, mode='rb').read()
print(f"ROM Banks Loaded: {len(rom_image)}")

if len(rom_image) < 1:
    print("No ROMS loaded. Exiting.")
    sys.exit(1)

top_bank=max(rom_image.keys())

card_id=rom_image[top_bank][0x3ff8:0x3ffa]
country_code=rom_image[top_bank][0x3ffa]&15
external_application=rom_image[top_bank][0x3ffb]
size_in_banks=rom_image[top_bank][0x3ffc]
card_subtype=rom_image[top_bank][0x3ffd]
card_type=rom_image[top_bank][0x3ffe:0x4000]

print()
print(f"Card Type: {card_type.decode('utf-8')}, Subtype: {hex(card_subtype)}, Card Size (banks): {int(size_in_banks)}")
print(f"External Application: {external_application}, Country_Code: {hex(country_code)}, ({country_codes[country_code]}), Card ID: {card_id.hex()}")




# Read the application Front DOR which always starts at 0x3fc0
# This points us to the first Application DOR with the pointer_to_son
pointer_to_parent=rom_image[top_bank][0x3fc0:0x3fc3]
pointer_to_brother=rom_image[top_bank][0x3fc3:0x3fc6]
pointer_to_son=rom_image[top_bank][0x3fc6:0x3fc9]
dor_type=rom_image[top_bank][0x3fc9]
dor_length=rom_image[top_bank][0x3fca]
key_for_name_filed=rom_image[top_bank][0x3fcb]
length_of_name=rom_image[top_bank][0x3fcc]
name_bytes=rom_image[top_bank][0x3fcd:0x3fd2]
dor_terminator=rom_image[top_bank][0x3fd2]

print()
print(f"Front DOR Data")
print(f"DORData: Parent: {EPTxt(pointer_to_parent)}, Brother: {EPTxt(pointer_to_brother)}, Son: {EPTxt(pointer_to_son)} Type: {hex(dor_type)}:{dor_types[dor_type]}, Length: {dor_length}")
print(f"Name({chr(key_for_name_filed)}/{length_of_name}): {name_bytes[:len(name_bytes)-1]}")
print()


print(f"First App DOR at {pointer_to_son[2]}:{0x3fff&struct.unpack('<H', pointer_to_son[0:2])[0]}")
next_bank, next_pointer=read_app_dor(pointer_to_son[2], 0x3fff&struct.unpack('<H', pointer_to_son[0:2])[0])
while next_bank != 0:
    print(f"Following DOR at {next_bank}:{hex(next_pointer)}")
    next_bank, next_pointer=read_app_dor(next_bank, next_pointer)



