import asyncio
import httpx
import re

async def main():
    url = "http://data.ncpor.res.in/bharati/live"
    async with httpx.AsyncClient(timeout=5.0) as client:
        res = await client.get(url)
        html = res.text
        
        temp_match = re.search(r'id\s*=\s*"divtemp">\s*&nbsp;([\-\d\.]+)', html)
        rh_match = re.search(r'id\s*=\s*"divrh">\s*&nbsp;([\-\d\.]+)', html)
        ap_match = re.search(r'id\s*=\s*"divap">\s*&nbsp;([\-\d\.]+)', html)
        ws_match = re.search(r'id\s*=\s*"divw">\s*&nbsp;([\-\d\.]+)', html)
        
        print("Temp:", temp_match.group(1) if temp_match else None)
        print("RH:", rh_match.group(1) if rh_match else None)
        print("AP:", ap_match.group(1) if ap_match else None)
        print("WS:", ws_match.group(1) if ws_match else None)

asyncio.run(main())
