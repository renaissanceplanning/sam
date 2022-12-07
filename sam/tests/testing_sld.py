from sam.download.sld import dl_sld
from sam.config import counties

broward = counties.loc[counties.GEOID == "12011"]

sld = dl_sld(mask=broward)

print()