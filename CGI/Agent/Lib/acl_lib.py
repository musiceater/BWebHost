# -*- coding: utf-8 -*-

import string
"""
	do or operation to strings
	
"""	
def doOR(d1, d2):
	l1=len(d1)
	l2=len(d2)
	length=l1
	if l2> l1:
		length=l2
	retStr=''
	for i in range(0,length):
		d1_e='0'
		d2_e='0'
		if i>=length-l1:	
			d1_e=d1[i-(length-l1)]
		if i>=length-l2:	
			d2_e=d2[i-(length-l2)]
		if d1_e=='1' or d2_e=='1':
			retStr=retStr+'1'
		else:
			retStr=retStr+'0'
		
	return retStr
	
if __name__ == '__main__':
	#passin=sys.argv[1:]
	#print passin, len(passin)
	print doOR('10011','0100')