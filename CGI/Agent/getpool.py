import json

def execute():
	return encodeJSON()
	
def encodeJSON():
	pool1 = []
	elements = []
	element1 = {'LDName':'Pool1LD1','Partition':'0','Size':'1T','Type':'RAID0','Used':'yes','Status':'online'}
	elements.append(element1)
	poolcontent = {'PoolName':'Pool1', 'Size':'1T','Used':'20M','Available':'1T','Capacity':'0%','State':'1.00X','element':elements}
	pool1.append(poolcontent)

	
	
	pool2 = []
	
	elements = []
	element1 = {'LDName':'Pool2LD1','Partition':'0','Size':'1T','Type':'RAID0','Used':'yes','Status':'online'}
	element2 = {'LDName':'Pool2LD2','Partition':'0','Size':'1T','Type':'RAID1','Used':'no','Status':'offline'}
	elements.append(element1)
	elements.append(element2)
	poolcontent = {'PoolName':'Pool2', 'Size':'2T','Used':'40M','Available':'2T','Capacity':'0%','State':'2.00X','element':elements}
	pool2.append(poolcontent)
	

	pools = pool1+pool2
	
	return json.dumps(pools)

