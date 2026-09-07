import re
html = open('ncpor_utf8.html', 'r', encoding='utf-8').read()
t = re.search(r'id\s*=\s*[\"\'']divtemp[\"\''][^>]*>\s*(?:&nbsp;)?\s*([-\d\.]+)', html)
rh = re.search(r'id\s*=\s*[\"\'']divrh[\"\''][^>]*>\s*(?:&nbsp;)?\s*([\d\.]+)', html)
print('Temp:', t)
print('RH:', rh)
