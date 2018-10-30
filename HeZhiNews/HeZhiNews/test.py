import re
text='xyxw/173.htm'
regx = re.search('(\d+)',text)
print(regx.group(0))



