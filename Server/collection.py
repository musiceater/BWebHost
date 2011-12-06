# Copyright (c) 2005.-2006. Ivan Voras <ivoras@gmail.com>
# Released under the Artistic License

from member import Member

class Collection(Member):

    def __init__(self, name):
        self.name = name

    def getMembers(self):
        return []

    


