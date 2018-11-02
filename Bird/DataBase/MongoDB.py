# -*- coding: utf-8 -*-

import pymongo
from pymongo import MongoClient

from DataBase import Setting
from Logger import Log

# handler on Mongo.
# Support import/export data to database. 

class Mongo(object):

    def __init__(self):
        
        self.writeLog = Log.Logger('mongodb.txt')

        # connect DB
        self.ConnectDB()

    def ConnectDB(self):
        try:
            # connect mongodb
            self.dbClient = MongoClient(Setting.DATABASE_ADDR,Setting.DATABASE_PORT)
                
            # Call server_info to verify the server state
            self.dbClient.server_info()

            self.writeLog.log(u'MongoDB连接成功')

        except Exception:
            self.writeLog.log(u'MongoDB连接失败')
    
    def dbInsert(self, dbName, collectionName, d):
        try:
            """向MongoDB中插入数据，d是具体数据"""
            if self.dbClient:
                db = self.dbClient[dbName]
                collection = db[collectionName]
                collection.insert_one(d)
            else:
                self.writeLog.log(u'数据插入失败，MongoDB没有连接')
        except Exception:
            self.writeLog.log(Exception)

    def dbQuery(self, dbName, collectionName, d):
        try:
            """从MongoDB中读取数据，d是查询要求，返回的是数据库查询的指针"""
            if self.dbClient:
                db = self.dbClient[dbName]
                collection = db[collectionName]
                cursor = collection.find(d)
                if cursor:
                    return list(cursor)
                else:
                    return []
            else:
                self.writeLog.log(u'数据查询失败，MongoDB没有连接')   
                return []
        except Exception:
            self.writeLog.log(Exception)

    def dbQueryAll(self, dbName, collectionName):
        try:
            """从MongoDB中读取数据，d是查询要求，返回的是数据库查询的指针"""
            if self.dbClient:
                db = self.dbClient[dbName]
                collection = db[collectionName]
                cursor = collection.find()
                if cursor:
                    return list(cursor)
                else:
                    return []
            else:
                self.writeLog.log(u'数据查询失败，MongoDB没有连接')   
                return []
        except Exception:
            self.writeLog.log(Exception)        
    
    #def dbUpdate(self, dbName, collectionName, d, flt, upsert=False):
    def dbUpdateBody(self, dbName, collectionName, d, flt):
        """向MongoDB中更新数据，d是具体数据，flt是过滤条件，upsert代表若无是否要插入"""
        if self.dbClient:
            db = self.dbClient[dbName]
            collection = db[collectionName]
            collection.update(flt,{'$addToSet':{'Data':d}})
        else:
            self.writeLog.log(u'数据更新失败，MongoDB没有连接')   

    def dbDelCollection(self, dbName, collectionName):
        if self.dbClient:
            db = self.dbClient[dbName]
            collection = db[collectionName]
            collection.drop()
        else:
            self.writeLog.log(u'数据更新失败，MongoDB没有连接')           

testData = {
 "_id":"880301",
 "Item":"880301",
 "Name":"煤炭", 
 "Type":"Day", 
 "Rehab":"Front",
 "Data" : []
 }

if __name__ == '__main__':
    mongo = Mongo()
    #mongo.dbInsert("test","category",testData)
    #mongo.dbInsert("test","category",testData)
    #mongo.dbUpdateBody("test","category",{"Item":"880301"})
    #datalist = mongo.dbQuery("test","category",{"Item":"880301"})
    #datalist = mongo.dbQuery("stock","IndusCategorys",{"_id":"880301"})
    mongo.dbDelCollection("stock","IndusCategorys")
    #print(datalist)
