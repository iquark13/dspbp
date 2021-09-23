
import json
import base64
import re
from typing import List
import zlib
import binascii
import struct
filename='bp.txt'
from reader import *
from dspid import *
import pprint

items=itemID()
recipies=recipeID()

with open(filename,'r') as file:
    data=file.readlines()
x
print(type(data))
print(type(data[0]))
data=data[0]

data = data.strip()
first_quote_loc = data.find('"')
second_quote_loc = data[first_quote_loc+1:].find('"') + first_quote_loc + 2

print(f'First Quote: {first_quote_loc}')
print(f'Second Quote: {second_quote_loc}')

header_segments = data[10:first_quote_loc].split(',')
hashed_string = data[:second_quote_loc-1]
hash_1 = data[second_quote_loc+0:]

print(f'Header Segments: {header_segments}')
print(f'Hash: {hash_1}')
print(f'End of Hashed Segment: {hashed_string[-20:]}')
print(f'Beginning of Hashed Segment: {hashed_string[:20]}')

comp = data[first_quote_loc+1:second_quote_loc-1]
print(f'Comp str: {comp}')
print(f'Length of compressed b64 encoded data: {len(comp)}')
comp = base64.b64decode(comp)
print(f'Length of decoded byte data: {len(comp)}')
decomp = zlib.decompress(comp,16+zlib.MAX_WBITS)
print(f'Length of uncompressed byte data: {len(decomp)}')

# outfile = 'decoded.txt'

# with open(outfile,mode='w') as file:
#     #out = binascii.b2a_uu(decomp)
#     for x in decomp:
#         file.write(str(x))
#         file.write('\n')
#     file.close()


reader = BinaryReader(decomp)

def parse_areas(indata)->list:
    areas = []
    count = reader.read_i8()
    for x in range(count):
        curarea = area()
        out = []
        out.append(reader.read_i8())
        out.append(reader.read_i8())
        out.append(reader.read_i16())
        out.append(reader.read_i16())
        out.append(reader.read_i16())
        out.append(reader.read_i16())
        out.append(reader.read_i16())
        out.append(reader.read_i16())

        curarea.add_list(out)

        areas.append(curarea)
    
    return areas

#Areas:

def parse_buildings(indata)->list:
    buildings = []
    
    count = reader.read_i32()
    startpos=reader.pos
    for x in range(count):
        curbldg = building()
        out = []
        out.append(reader.read_i32())
        out.append(reader.read_i8())
        out.append(reader.read_single())
        out.append(reader.read_single())
        out.append(reader.read_single())
        out.append(reader.read_single())
        out.append(reader.read_single())
        out.append(reader.read_single())
        out.append(reader.read_single())
        out.append(reader.read_single())
        out.append(reader.read_i16())
        out.append(reader.read_i16())
        out.append(reader.read_i32())
        out.append(reader.read_i32())
        out.append(reader.read_i8())
        out.append(reader.read_i8())
        out.append(reader.read_i8())
        out.append(reader.read_i8())
        out.append(reader.read_i8())
        out.append(reader.read_i8())
        out.append(reader.read_i16())
        out.append(reader.read_i16())

        for key,value in zip(curbldg.data.keys(),out):
            curbldg.data[key]=value


        parm_count = reader.read_i16()
        for y in range(parm_count):
            curbldg.parameters.append(reader.read_i32())
        
        buildings.append(curbldg)

    endpos=reader.pos

    print(f'Start: {startpos}\nEnd: {endpos}')
    pp = pprint.PrettyPrinter()
    pp.pprint(reader.data[startpos:endpos])

    return buildings

def parse_metadata(indata):
    reader.read_i32()
    reader.read_i32()
    reader.read_i32()
    reader.read_i32()
    reader.read_i32()
    reader.read_i32()
    reader.read_i32()
    return

def compare_buildings(input_list):
    key_copy = input_list[0].data.keys()
    compare = dict.fromkeys(key_copy)
    for key in compare:
        compare[key]=list()
        for building in input_list:
            if key=='item_id':
                compare[key].append(items.get(int(building.data[key])))
            elif key=='recipe_id':
                compare[key].append(recipies.get(int(building.data[key])))
            else:
                compare[key].append(building.data[key])
    return compare

parse_metadata('x')

print(reader.position)
areas=parse_areas(decomp)
print(areas)
print(reader.position)

bd = parse_buildings(decomp)
print('\n')

pp = pprint.PrettyPrinter(indent=2)
pp.pprint(compare_buildings(bd))

packer = binaryPack()

def pack_buildings(building_list:list[building]):

    bin_holder = bytearray()
    bin_out = []
    count_size = 32
    count = []
    count.append(len(building_list))

    fmt_order = [32,8,1,1,1,1,1,1,1,1,16,16,32,32,8,8,8,8,8,8,16,16]

    for bdg in building_list:
        to_encode = list(bdg.data.values())
    
        bin_out.append(packer.pack_list(to_encode,fmt_order))

    #add the count to the front
    count_bin = packer.pack_list(count,[count_size])
    bin_out.insert(0,count_bin)
    return bin_out

def pack_areas(area_list:list[area]):

    bin_holder = bytearray()
    bin_out = []
    count_size = 8
    count = []
    count.append(len(area_list))

    fmt_order = [8,8,16,16,16,16,16,16]

    for area in area_list:
        to_encode = list(area.data.values())
    
        bin_out.append(packer.pack_list(to_encode,fmt_order))

    #add the count to the front
    count_bin = packer.pack_list(count,[count_size])
    bin_out.insert(0,count_bin)
    return bin_out