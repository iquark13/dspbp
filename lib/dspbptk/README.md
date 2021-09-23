# External MD5 Checksum from johndoe31415/dspbptk

I realized that I didn't want to reverse engineer the modified MD5 checksum that youthcat studios used, and pulled this very useful module from the existing dspbptk library.

See the repo here: [dspbptk](https://github.com/johndoe31415/dspbptk)

## Usage

DysonSphereMD5(DysonSphereMD5.Variant.MD5F) expects the hashed string *EXCLUDING* the final quote.

A sample function to provide the MD5 hash given a blueprint string is below:

```python
    def gen_md5f(bp_string:str)->str:
        '''
        Note: bp_string should be either FULL blueprint with hash, 
        or a 'hashed' portion of the string - 
            aka: from [BLUEPRINT..."] MINUS the last ".
        '''
        rindex=0
        if bp_string.count('"') != 2:
            if bp_string.count('"') != 1:
                raise InvalidBPString('Blueprint String is not valid for hashing')
            rindex = None
        
        if not bp_string.startswith('BLUEPRINT'):
            raise InvalidBPString('Blueprint String is not valid for hashing')
        
        if rindex == 0:
            index = bp_string.rindex('\"')
        elif rindex == None:
            index = None
        
        hashed_data = bp_string[:index]
        
        hash_value = DysonSphereMD5(DysonSphereMD5.Variant.MD5F). \
            update(hashed_data.encode('utf-8')).hexdigest().upper()

        return hash_value    
```
