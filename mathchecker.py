m = [x/8 if x != 1 else 4 for x in bp.fmt_metadata]
a = [x/8 if x != 1 else 4 for x in bp.fmt_area]
b = [x/8 if x != 1 else 4 for x in bp.fmt_building]

msum = 0
asum = 0
bsum = 0
for x in m:
    msum +=x
for x in a:
    asum +=x
for x in b:
    bsum +=x

print(f'Meta: {msum}')
print(f'Area: {asum}')
print(f'Building: {bsum}')

print(msum+1+asum+4+bsum)


################
for orig,new in zip(bp.decomp_bytes,bp._rawbytes_new):
    print(f'{(orig,new)} {1 if orig==new else 0}')