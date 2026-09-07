import httpx
import re
import urllib3

urllib3.disable_warnings()

html = httpx.get('https://data.ncpor.res.in/bharati/live', verify=False).text
temp_match = re.search(r'id\s*=\s*["\']divtemp["\'][^>]*>\s*(?:&nbsp;)?\s*([-\d\.]+)', html)
rh_match = re.search(r'id\s*=\s*["\']divrh["\'][^>]*>\s*(?:&nbsp;)?\s*([\d\.]+)', html)
ap_match = re.search(r'id\s*=\s*["\']divap["\'][^>]*>\s*(?:&nbsp;)?\s*([\d\.]+)', html)
w_match = re.search(r'id\s*=\s*["\']divw["\'][^>]*>\s*(?:&nbsp;)?\s*([\d\.]+)', html)

x_matches = re.findall(r'x:\s*(\d+)', html)
latest_ms = max(int(x) for x in x_matches) if x_matches else None

print("Temp:", temp_match.group(1) if temp_match else "None")
print("RH:", rh_match.group(1) if rh_match else "None")
print("AP:", ap_match.group(1) if ap_match else "None")
print("W:", w_match.group(1) if w_match else "None")
print("Latest MS:", latest_ms)
