import base64
import zlib
from reader import *
import pprint as pp
from dspid import *
from hashlib import md5


class blueprint(object):
    '''
    class to complete blueprint parsing and packing
    '''
    pprint = pp.PrettyPrinter(2)
    items = itemID()
    recipes = recipeID()


    def __init__(self,bpdata:str):
        '''
        Usage: This class decodes a DSP blueprint, and can 
            optionally also reencode the bp after changes are made.

        Methods:
            init: provide the blueprint string as a str

        Attributes:
            state: returns information regarding the parsing status
            
        '''
        #Start with handling for original and modified bp data.
        self._blueprint_string = bpdata
        self._blueprint_string_new = ''
        self._bpdata = self._blueprint_string
        self._bpdata_new = None

        #Initialization methods working with the string, and creating 
        #   various classes and whatnot for use.
        self._prep_data()
        self._find_quotes()
        self._define_segements()
        self._decompress()
        self._gen_metadata()
        self._gen_buildings()
        self._gen_areas()
        
        #setup the reader and the packer
        self.reader = BinaryReader(self.decomp_bytes)
        self.packer = binaryPack()

        #initialize state:
        self._state_init()

        #now it is time to parse the BP!
        self._fmt_prep()
        self._parseBP()
        
        return

    def parse_metadata(self)->None:
        if self.meta_parsed==True:
            print('Metadata has already been parsed. Reset to \
                    complete new parsing.')
            return
        
        if self.reader.pos != 0:
            print('Required reader reset, check data!')
            self.reader._reset()
        
        fmt = self.fmt_metadata
        parse_holder = self.reader.read_list(fmt)

        for key,value in zip(self._metadata_reader_keys,parse_holder):
            self.metadata[key]=value

        self.meta_parsed=True
        print('Metadata successfully parsed')
        return
        
        

    def parse_areas(self)->None:
        if self._meta_parsed == False:
            print('Metadata not parsed! Exiting...')
            return
        elif self._areas_parsed == True:
            print('Areas already parsed! exiting.')
            return
        elif self.reader.pos == 0 or self.reader.pos == self.reader.length:
            print('Reader reports that parsing order has been messed up. Reset!')
            return
        area_holder = []
        area_count = self.reader.read_i8()
        fmt = self.fmt_area
        for ara in range(area_count):
            curarea = area()
            read_list = self.reader.read_list(fmt)
            curarea.add_list(read_list)
            area_holder.append(curarea)
        
        self._areas=area_holder
        
        self._areas_parsed = True
        print(f'{area_count} areas parsed successfully!')
        
        return

    def parse_buildings(self):
        if self._meta_parsed != True or self._areas_parsed != True:
            print('Metadata or Areas not parsed. Exiting.')
            return
        elif self._buildings_parsed == True:
            print('Buildings already parsed! Exiting.')
            return

        building_holder = []
        building_count = self.reader.read_i32()
        fmt = self.fmt_building
        fmt_param = []
        for bdg in range(building_count):
            curbdg = building()
            read_list = self.reader.read_list(fmt)
            curbdg.add_list(read_list)
            

            #Now parameters
            param_count = self.reader.read_i16()
            for param in range(param_count):
                curbdg.parameters.append(self.reader.read_i32())
            
            building_holder.append(curbdg)

        self._buildings = building_holder

        self._buildings_parsed = True
        print(f'{building_count} buildings parsed successfully!')

        return

    def building_compare(self,buildings:list[building]):
        holder = dict.fromkeys(list(buildings[0].data.keys()))
        for key in holder:
            holder[key]=[]

        for bd in buildings:
            for key in holder:
                holder[key].append(bd.data[key]) # type: ignore
        
        return holder

    def repack(self):
        '''
        This function call all necessary items to repack the blueprint
            in a DSP compatible form.
        
            ARGS: None
            Returns: New BP String
            Sets: self.blueprint_string_new
        '''

        #Parse the BP changes
        self._pack_bp()

        newstr = self.header_str
        newstr +='"' + self._encoded_recompress.decode('utf-8') + '"'

        newhash = md5(newstr.encode('utf-8'))
        newhash = newhash.digest().hex()

        finalstr = newstr + newhash

        return finalstr
        





    def _prep_data(self):
        '''
        Does strip and data checking prior to quoting
        '''

        self._bpdata = self._bpdata.strip()
        return

    def _find_quotes(self):
        '''
        Finds the locations of the quotes for compressed string/header/hash splitting
        '''
        self.first_quote_loc = self._bpdata.find('"')
        self.second_quote_loc = self._bpdata[self.first_quote_loc+1:].find('"') \
                            + self.first_quote_loc + 2
        return

    def _define_segements(self):
        '''
        defines:
        self.header_str
        self.header_segments
        self.hashed_string
        self.hash_1
        self.compressed_str

        '''
        self.header_str = self._bpdata[:self.first_quote_loc]
        self.header_segments = self._bpdata[10:self.first_quote_loc].split(',')
        self.hashed_string = self._bpdata[:self.second_quote_loc]
        self.hash_1 = self._bpdata[self.second_quote_loc+0:]
        self.compressed_str = self._bpdata[self.first_quote_loc+1:self.second_quote_loc-1]

        return

    def _decompress(self):

        #decode from base64
        decoded = base64.b64decode(self.compressed_str)
        self.decompressed_bytes = zlib.decompress(decoded,16+zlib.MAX_WBITS)
        self.decoded_bytes = decoded
        return

    def _fmt_prep(self):
        self.fmt_metadata = [32,32,32,32,32,32,32]
        self.fmt_area = [8,8,16,16,16,16,16,16]
        self.fmt_building = [32,8,1,1,1,1,1,1,1,1,16,16,32,32,8,8,8,8,8,8,16,16]
        self.fmt_area_count = 8
        self.fmt_building_count = 32
        self.fmt_building_param_count = 16
        self.fmt_building_param = 32
        
        return

    def _gen_metadata(self):
        self.metadata= {
                        'icon_layout':int(self.header[1]),
                        'icon0':int(self.header[2]),
                        'icon1':int(self.header[3]),
                        'icon2':int(self.header[4]),
                        'icon5':int(self.header[5]),
                        'icon4':int(self.header[6]),
                        'time':int(self.header[8])/10000000,
                        'game_version':self.header[9],
                        'short_description': self.header[10] if self.header[10] else '',
                        'description':self.header[11] if self.header[11] else '',
                        'version':'',
                        'cursor_offset_x':'',
                        'cursor_offset_y':'',
                        'cursor_target_area':'',
                        'drag_box_size_x':'',
                        'drag_box_size_y':'',
                        'primary_area_idx':''

                        }
        self._metadata_reader_keys = ['version','cursor_offset_x',
                    'cursor_offset_y','cursor_target_area','drag_box_size_x',
                    'drag_box_size_y','primary_area_idx']

        return

    def _gen_buildings(self):
        '''
        This function generates a building holder list for holding building data.

        Uses the building() class.
        '''
        self._buildings:list[building]=[]
        return

    def _gen_areas(self):
        '''
        This function generates a building holder list for holding building data.

        Uses the building() class.
        '''
        self._areas:list[area]=[]
        return

    def _state_init(self):
        '''
        Initialize parsing status for the blue print.
        '''
        self._meta_parsed = False
        self._areas_parsed = False
        self._buildings_parsed = False
        return

    def _parseBP(self):
        '''
        Parse the blueprint provided during class initialization through the 3 
            steps of parsing.

        Order is critical due to the binaryReader being stateful.
        '''
        self.parse_metadata()
        self.parse_areas()
        self.parse_buildings()
        return

    def _pack_bp(self):
        '''
        This function packs up a blueprint binary
            compresses it, encodes it in b64, and returns the final BP string.

        Fundamentally we have the following order of operations:

            Step 1: Gather counts
                - number of buildings (substep to get parameters)
                - number of areas
            
            Step 2: Pack sections individually to binary per fmt_...
                - Buildings
                - Areas
                - Metadata
            
            Step 3: Compress and encode
                - Combine the binary strings
                - GZIP the strings to compress
                - b64encode compressed bytes
            
            Step 4: MD5 hash
                - TODO: Figure out MD5 hash

            Step 5: Combine resulting string with header and update _bpdata_new

        '''
        
        num_buildings = len(self.buildings)
        num_areas = len(self._areas)
        
        #Pack up the buildings
        self.packer.pack_list([num_buildings],[self.fmt_building_count])
        for bd in self.buildings:
            self.packer.pack_list(list(bd.data.values()),self.fmt_building)
            self.packer.pack_list([bd.param_count],[self.fmt_building_param_count])
            if bd.param_count >= 1:
                self.packer.pack_list([*bd.parameters],
                    [*bd.param_count*[self.fmt_building_param]])
        
        bdg_rawbytes = self.packer.flush()

        #Pack up the areas
        self.packer.pack_list([num_areas],[self.fmt_area_count])
        for ara in self._areas:
            self.packer.pack_list(list(ara.data.values()),self.fmt_area)

        ara_rawbytes = self.packer.flush()

        #Pack up the metadata
        md_holder = []
        for key in self._metadata_reader_keys:
            md_holder.append(self.metadata[key])
        self.packer.pack_list(md_holder,self.fmt_metadata)

        metadata_rawbytes = self.packer.flush()

        #Combine all bytes to one single string in proper order.
        rawbytes = bytes()
        rawbytes += metadata_rawbytes+ara_rawbytes+bdg_rawbytes
        
        #Run gzip compression sequence:
        print(f'Size of data before compression: {len(rawbytes)}')
        compressed_bytes = self._compress(rawbytes)

        #Encode using base64:
        print(f'Size of data after compression: {len(compressed_bytes)}')
        encoded_comp_bytes = base64.b64encode(compressed_bytes)
        
        print(f'Size of data after encoding: {len(encoded_comp_bytes)}')
        self._rawbytes_new = rawbytes #debug
        self._recompressed = compressed_bytes #debug
        
        #Final reencoded byte string
        self._encoded_recompress = encoded_comp_bytes


        return

    def _compress(self,byte_data):
        '''
        This function runs GZIP compression using the zlib library.
        '''
        compactor = zlib.compressobj(wbits=16+zlib.MAX_WBITS)
        first=bytes()
        first = compactor.compress(byte_data)
        first += compactor.flush()

        return first


    @property
    def header(self):
        return self.header_segments

    @property
    def hash(self):
        return self.hash_1

    @property
    def decomp_bytes(self):
        return self.decompressed_bytes

    @property
    def meta_parsed(self):
        return self._meta_parsed

    @meta_parsed.setter
    def meta_parsed(self,value:bool):
        self._meta_parsed=value
        return

    @property
    def areas_parsed(self):
        return self._areas_parsed

    @areas_parsed.setter
    def areas_parsed(self,value:bool):
        self._areas_parsed=value
        return

    @property
    def buildings_parsed(self):
        return self._buildings_parsed

    @buildings_parsed.setter
    def buildings_parsed(self,value:bool):
        self._buildings_parsed=value
        return

    @property
    def buildings(self):
        return self._buildings

    @property
    def state(self):
        '''
        attribute returns dict of current state of BP
        {
            Parsing: 
            {
                metaData: bool,
                Areas: bool,
                Buildings: bool
            },
            Position: reader.pos,
            Areas : int # of areas,
            Buildings : int # of buildings
        }
        '''

        state = {
                    'Parsing': {
                        'metaData':self.meta_parsed,
                        'Areas':self.areas_parsed,
                        'Buildings':self.buildings_parsed
                    },
                    'Position':self.reader.pos,
                    'Areas':len(self._areas),
                    'Buildings':len(self._buildings)
                }    
        type(self).pprint.pprint(state)
        return state

    @property
    def building_stats(self):
        item_holder = []
        for bd in self.buildings:
            item_holder.append(type(self).items[bd.data['item_id']])
        unique_bd = list(set(item_holder))

        counts = [item_holder.count(x) for x in unique_bd]

        return {x:y for x,y in zip(unique_bd,counts)}

    @property
    def recipe_stats(self):
        item_holder = []
        for bd in self.buildings:
            item_holder.append(type(self).recipes[bd.data['recipe_id']])
        unique_bd = list(set(item_holder))

        counts = [item_holder.count(x) for x in unique_bd]

        return {x:y for x,y in zip(unique_bd,counts)}
    
    @property
    def param_stats(self):
        item_holder = []
        for bd in self.buildings:
            try:
                item_holder.append(bd.parameters[0])
            except:
                pass
        unique_bd = list(set(item_holder))

        counts = [item_holder.count(x) for x in unique_bd]

        return {x:y for x,y in zip(unique_bd,counts)}




if __name__=='__main__':

    filename='bp.txt'
    with open(filename,'r') as file:
        data=file.readlines()

    print(type(data))
    print(type(data[0]))
    data=data[0]

    bp = blueprint(data)

    # for bd in bp.buildings:
    #     bp.pprint.pprint(bd.info)

    blueprint.pprint.pprint(bp.building_stats)
    blueprint.pprint.pprint(bp.recipe_stats)
    blueprint.pprint.pprint(bp.param_stats)

    print()
    #blueprint.pprint.pprint(bp.building_compare(bp.buildings))
  