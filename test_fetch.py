import urllib.request
import re

html = urllib.request.urlopen('http://data.ncpor.res.in/bharati/live').read().decode('utf-8')

# The original regex from ncpor_service.py:
print("Trying original regex:")
temp_match = re.search(r'id\s*=\s*"divtemp">\s*&nbsp;([\-\d\.]+)', html)
rh_match = re.search(r'id\s*=\s*"divrh">\s*&nbsp;([\d\.]+)', html)
ap_match = re.search(r'id\s*=\s*"divap">\s*&nbsp;([\d\.]+)', html)
ws_match = re.search(r'id\s*=\s*"divw">\s*&nbsp;([\d\.]+)', html)

print("Temp:", temp_match.group(1) if temp_match else "None")
print("RH:", rh_match.group(1) if rh_match else "None")
print("AP:", ap_match.group(1) if ap_match else "None")
print("WS:", ws_match.group(1) if ws_match else "None")

# More robust regex
print("\nTrying robust regex:")
t = re.search(r'id=["\']divtemp["\'][^>]*>(.*?)</div>', html, re.I|re.DOTALL)
if t:
    print("Temp raw:", repr(t.group(1)))
