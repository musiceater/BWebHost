import sys
import pyLogger
log = pyLogger.pylogger('acl','/var/log/nas_acl.log')

fullACL=[
	 'list_directory',
	 'read_data',
	 'add_file',
	 'write_data',
	 'add_subdirectory',
     'append_data',
	 'read_xattr',
	 'write_xattr',
	 'execute',
	 'delete_child',
     'read_attributes',
	 'write_attributes',
	 'delete',
	 'read_acl',
	 'write_acl',
     'write_owner'
	 ]	 

modACL=[		 
	'list_directory',
	'read_data',
	'add_file',
	'write_data',
	'add_subdirectory',
    'append_data',
	'read_xattr',
	'write_xattr',
	'execute',
	'read_attributes',
    'write_attributes',
	'delete',
	'read_acl'
	]


rnrACL=[
    'list_directory',
	'read_data',
	'read_xattr',
	'execute',
	'read_attributes',
	'read_acl']


listACL=[
	'list_directory',
	'read_xattr',
	'read_data',
	'execute',
	'read_attributes',
	'read_acl']
	

readACL=[
    'list_directory',
	'read_data',
	'read_xattr',
	'read_attributes',
	'read_acl']
	

writeACL=[
    'add_file',
	'write_data',
	'add_subdirectory',
	'append_data',
	'write_xattr',
    'write_attributes']


def combineACL(srclist,tarlist):
	#srclist might be empty
	result=srclist
	found=0
	for item1 in tarlist:
		found=0
		for item2 in srclist:
			if item1==item2:
				found=1
		if found==0:
			result.append(item1)
	
	return result

def addAppend(op, str, islist):
	retStr='/'.join(str)
	if op=='allow':
		if len(retStr)!=0:
			retStr = retStr + '/synchronize'
	if islist==0:
		retStr=retStr+':file_inherit/dir_inherit:'+op
	else:
		retStr=retStr+':dir_inherit:'+op

		
	return retStr
	
def getACLList(op, controls):
	aclStr=[]
	isList=0
	isrnr=0
	for control in controls:
		
		if control == 'full':
			aclStr.append(addAppend(op, fullACL, 0))
			break
		elif control == 'mod':
			aclStr.append(addAppend(op, modACL, 0))
			break
		else:
			if control == 'rnr':
				aclStr.append(addAppend(op, rnrACL, 0))
				isrnr=1
			elif isrnr==0:
				if control == 'list':
					aclStr.append(addAppend(op, listACL, 1))
				elif control == 'read':
					aclStr.append(addAppend(op, readACL, 0))

			if control == 'write':
				aclStr.append(addAppend(op, writeACL, 0))
	if len(aclStr)==0:
		#aclStr.append(':file_inherit/dir_inherit:%s'%op)
		aclStr.append(':file_inherit:%s'%op)
	return aclStr
		
#print full,mod,rnr,list,read,write



if __name__ == '__main__':
	passin=sys.argv[1:]
	log.error('passin %s %d'%(passin,len(passin)))
	if len(passin)==0: sys.exit()
	#print passin, len(passin)
	
	acl=''
	try:
		for item in passin:
			entity=item.split(':')
			op=entity[0]
			log.error('op=%s %s'%(op,entity))
			retACL=getACLList(op,entity[1:])
			for item2 in retACL:
				print item2
		
	except:
		pass
	
	
	
	
	
	