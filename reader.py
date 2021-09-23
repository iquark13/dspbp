import struct

data = [37,100,13,3]
bdata=b'%\x00\x00\x00d\x00\x00\x00\r\x00\x00\x00\x03\x00\x00\x00'

class BinaryReader(object):
    '''
    Creates reader objects for reading specific sizes of items
    '''

    def __init__(self,data):
        self.position = 0
        self.data = data
        self.length = len(self.data)
        self.fmt_dict = {32:self.read_i32,16:self.read_i16,
                            8:self.read_i8,1:self.read_single}


    def read_i32(self):
        return self.get_integer(4,'<i')

    def read_i16(self):
        return self.get_integer(2, '<h')

    def read_i8(self):
        return self.get_integer(1, 'b')

    def read_single(self):
        return self.get_integer(4,'<f')


    def get_string(self,byte_count):
        '''
        args: byte_count = number of bytes to read
        returns: string
        '''
        fmt_str = str(byte_count)+'B'
        value = struct.pack(fmt_str,*self.data[self.position:self.position+byte_count])
        self.position += byte_count
        return value

    def get_integer(self,byte_count, fmt):
        '''
        Args:
            byte_count:int
            format:str (python formatting string)
        Return:int
        '''

        value = self.data[self.position:self.position+byte_count]
        out = struct.unpack(fmt,value)
        self.position += byte_count
        return out[0]

    def read_list(self,fmt_list:'list[int]')->list:
        '''
        Returns: list of read values per fmt_list
        Args: fmt_list = list[8,16,32,1] defining read sizes
        '''
        out_holder = []
        for read in fmt_list:
            out_holder.append(self.fmt_dict[read]())
        return out_holder

    def _reset(self):
        self.position = 0

    @property
    def pos(self):
        return self.position

class binaryPack(object):
    '''
    This class is used to pack binary bytes in the proper formatting for creating blue prints
    '''

    def __init__(self):
        self.data=[]
        self.buffer:bytes = bytes()
        self.fmt_dict={8:self.pack_i8,16:self.pack_i16,32:self.pack_i32,1:self.pack_single}

    def _pack(self,data,fmt):
        out = struct.pack(fmt,data)
        return out

    def pack_i8(self,data):
        return self._pack(data,'b')

    def pack_i16(self,data):
        return self._pack(data,'<h')
    
    def pack_i32(self,data):
        return self._pack(data,'<i')

    def pack_single(self,data):
        return self._pack(data,'<f')

    def pack_list(self,data:list,fmt_list:"list[int]"):
        data_holder = bytes()
        for val,fmt in zip(data,fmt_list):
            data_holder += self.fmt_dict[fmt](val)
        self.data=data_holder
        self.buffer+=data_holder
        return self.data

    def flush(self):
        tmp = self.buffer
        self.buffer:bytes = bytes()
        return tmp

    @property
    def binData(self):
        return self.data

class building(object):

    def __init__(self):
        self._listadded = False
        self.parameters=[]
        names = ['index','area_index','local_offset_x','local_offset_y',
            'local_offset_z','local_offset_x2','local_offset_y2','local_offset_z2',
            'yaw','yaw2','item_id','model_index','temp_output_obj_idx',
            'temp_input_obj_idx','output_to_slot','input_from_slot','output_from_slot',
            'input_to_slot','output_offset','input_offset','recipe_id','filter_fd']
        self.data = dict.fromkeys(names)

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return self.__str__()
    
    def add_list(self,input_list:list):
        '''
        After reading a list of encoded bytes, this method provides and easy way
            to get data into the building object.

        Args: input_list = list[encoded values in order of names]
        Returns: None
        '''
        for key, value in zip(self.data.keys(),input_list):
            self.data[key]=value

        self._listadded = True

        return

    @property
    def param_count(self):
        return len(self.parameters)

    @property
    def info(self):
        return self.data
        
class area(object):

    def __init__(self):
        self.parameters=[]
        names = ['Area Count','Index','parent index','Tropic Anchor','Area Segments', 'Anchor Local offset x',
            'anchor local offset y','width','height']
        self.data = dict.fromkeys(names)

    def add_list(self,input_list:list):
        for key, value in zip(self.data.keys(),input_list):
            self.data[key]=value

        return



if __name__=='__main__':

    reader = BinaryReader(bdata)
