# -*- coding: utf-8 -*-

import json
import os
import re
from Logger import Log
from DataBase import MongoDB
import datetime

class TdxDataEngine(object):

    def __init__(self,FilePath):

        self.writeLog = Log.Logger('TdxDataEngine.txt')

        self.DataPath = FilePath    # file path for stock data

        self.STR_CATEGORY = "CategoryName"
        self.STR_CONTENT = "Content"

        self.MongoHandler = MongoDB.Mongo()

        # An example for all of data  Header + Body
        self.HeaderEx = {
            "_id":"880301", # it's for mongodb, avoid duplication
            "Name":"煤炭",
            "Type":"Day", 
            "Rehab":"Front",
            "Data":[]       # it's list for BodyEx
        }

        self.BodyEx = {
            "2005/06/07":
            {
                "Opening":159.89,
                "Maximum":164.31,
                "Minimum":157.22,
                "Close":158.69,
                "Volume":489895,
                "Turnover":339753952.00
            }
        }

    # get file list from the special folder.
    # output will store into the dict "DataItem"
    # DataItem ={"CategoryNames":[file paths list], ..., "CategoryNames":[file paths list]}
    def GetTdxFileList(self):

        DataItem = {}

        if (os.path.exists(self.DataPath) != True):
            self.writeLog.log(u'Path is Invalid!')
            return DataItem

        for (root, dirs, files) in os.walk(self.DataPath):

            CategoryName = os.path.basename(root)
            CategoryPath = root

            FileList = []

            for ef in files:
                FileList.append(os.path.join(CategoryPath, ef))

            if len(FileList) != 0 :          
                DataItem[CategoryName] = FileList
            else :
                self.writeLog.log(u'File list is None')
        return DataItem

    # Search in DataItem.
    # output will store into the dict
    # result ={"CategoryNames":[file paths list]}
    # id is number of shares，股票期货代码
    # FL_Data is file list that is dict
    # search by category or id
    # 搜索一个文件夹下所有的文件列表 把文件夹名给 category即可 id 为空
    # 搜索指定文件时 category为空，文件ID付给id即可。 文件ID 不是文件名，是股票代码值
    def SearchInFileList(self, FL_Data, category = '', id = ''):

        if not FL_Data and isinstance(FL_Data, dict):
            self.writeLog.log(u'File list is Invalid')
            return

        patternID = re.compile(r'.{4,6}')    # 删除无效ID名
        if re.match(patternID, id) == None:
            id = '#'    #invalid id， search by category
        
        reID = '#'+ id
        patternID = re.compile(reID) # (r'#\d{6}') search "file name"

        for key, value in FL_Data.items():

            if not isinstance(value,list):
                self.writeLog.log(u'Path list is Invalid')
                return
            
            if id == '#': # search by category
                if key == category:
                    return {key : value}
                else:
                    continue
            
            for path in value:
                if re.search(patternID, path):
                    return {key : [path]}

        return {}

    # Get tdx data from the Tdx data file, file list is in DataItem. This is generator 
    # 1st return the category name, and then return the each line in turn.
    # 1st format : {"CategoryName" : Name}
    # others format :  {"Content" : lineData}
    def GetTdxData(self, FL_Data):
        if not FL_Data and isinstance(FL_Data, dict):
            self.writeLog.log(u'File list is Invalid')
            return
        
        for key, value in FL_Data.items():

            if not isinstance(value,list):
                self.writeLog.log(u'Path list is Invalid')
                return
            
            yield {self.STR_CATEGORY : key}
            
            for path in value:
                try:
                    with open(path, 'r') as f:
                        for line in f.readlines():
                            line = line.strip('\n')
                            yield {self.STR_CONTENT : line}

                except Exception:
                    self.writeLog.log('Failed'+path)
                    break

    # handle tdx data from the generator from the function(GetTdxData)
    # date format: '2018/09/17-21:37'
    # return [{key1:[[data1],[data2],[datan]]},{key2:[[data1],[data2],[datan]]}]
    def HandlerTdxDataToList(self, filePath, start = '1990/01/01-00:00', end = '2100/01/01-00:00'):
        CurData = None
        DataType = "day"
        curItem = ''
        DataList = []
        AllData = []

        pattHeader = re.compile(r"[A-Za-z0-9]{4,6} ") # matching file header
        pattClass = re.compile(r"^\s{2,}") # matching data class
        pattData = re.compile(r"\d{4}/\d{2}/\d{2}") # matching data item
        pattFooter = re.compile(r"\D{4}:\D{3}") # matching file footer

        for data in self.GetTdxData(filePath):
            if self.STR_CATEGORY in data:
                CurCategory = data[self.STR_CATEGORY]
            elif self.STR_CONTENT in data:
                CurData =  data[self.STR_CONTENT]
                if re.match(pattHeader, CurData):
                    HeaderList = re.split(r'\s{1}',CurData) #split by space
                    curItem = HeaderList[1]
                elif re.match(pattClass, CurData):
                    BodyList = re.split(r'\t{1}',CurData) #split by tab
                    if len(BodyList) == 8 and BodyList[1].strip() == '时间':
                        DataType = "mins"
                elif re.match(pattData, CurData):
                    BodyList = re.split(r'\s{1}',CurData) #split by space

                    if (len(BodyList) != 7) and (len(BodyList) != 8):
                        self.writeLog.log('DataFile Body Error : ' + CurData)
                    
                    if DataType == "mins":
                        # convert to the ex : "2018/09/17-21:37"
                        time = BodyList[1][:2] + ':' + BodyList[1][2:]
                        BodyList.pop(1) # remove time item from the list
                    elif DataType == "day":
                        time = "00:00"
                        
                    date = BodyList[0] + '-' + time

                    cDate = datetime.datetime.strptime(date, '%Y/%m/%d-%H:%M')
                    sDate = datetime.datetime.strptime(start, '%Y/%m/%d-%H:%M')
                    eDate = datetime.datetime.strptime(end, '%Y/%m/%d-%H:%M')

                    if cDate < sDate or cDate > eDate:
                        continue

                    BodyList[0] = date

                    for i in range(1,len(BodyList)):
                        BodyList[i] = float(BodyList[i])

                    DataList.append(BodyList)

                elif re.match(pattFooter, CurData):
                    AllData.append({curItem : DataList})
                    DataList = []
                    curItem = ''
                    continue
                else:
                    self.writeLog.log('Matching failed : ' + CurData)
        
        return AllData

    # handle tdx data from the generator from the function(GetTdxData)
    def HandlerTdxDataToMongodb(self, filePath):
        
        CurCategory = None
        CurData = None
        CurDoc = {"_id" : ""}
        StorageMode = None

        pattHeader = re.compile(r"\d{6}") # matching file header
        pattClass = re.compile(r"^\s{2,}") # matching data class
        pattData = re.compile(r"\d{4}/\d{2}/\d{2}") # matching data item
        pattFooter = re.compile(r"\D{4}:\D{3}") # matching file footer

        for data in self.GetTdxData(filePath):
            if self.STR_CATEGORY in data:
                CurCategory = data[self.STR_CATEGORY]
            elif self.STR_CONTENT in data:
                CurData =  data[self.STR_CONTENT]
            
                if re.match(pattHeader, CurData):
                    # log start execution time, for one txt to mongodb
                    self.writeLog.logTimeStart()

                    HeaderList = re.split(r'\s{1}',CurData) #split by space
                    
                    if (len(HeaderList) != 4):
                        self.writeLog.log('DataFile Header Error : ' + CurData)

                    Header = {
                        "_id" : HeaderList[0], 
                        "Name": HeaderList[1],
                        "Type": HeaderList[2], 
                        "Rehab":  HeaderList[3],
                        "Data":[]
                    }

                    CurDoc = {"_id" : HeaderList[0]}
                    StorageMode = 'Insert'

                elif re.match(pattClass, CurData):
                    # No need for database, it converts to Json Format, refer to self.HeaderEx and self.BodyEx
                    continue
                elif re.match(pattData, CurData):
                    BodyList = re.split(r'\s{1}',CurData) #split by tab

                    if (len(BodyList) != 7) and (len(BodyList) != 8):
                        self.writeLog.log('DataFile Body Error : ' + CurData)

                    Body = {
                        BodyList[0]:
                        {
                            "Opening":BodyList[1],
                            "Maximum":BodyList[2],
                            "Minimum":BodyList[3],
                            "Close":BodyList[4],
                            "Volume":BodyList[5],
                            "Turnover":BodyList[6]
                        }
                    }

                    StorageMode = 'Update'

                elif re.match(pattFooter, CurData):
                    # log end execution time, for one txt to mongodb
                    self.writeLog.logTimeEnd(CurDoc["_id"])

                    # ending of each data files
                    Header = {}
                    Body = {}
                    CurDoc = {"_id" : ""}
                    continue
                else:
                    self.writeLog.log('Matching failed : ' + CurData)

                if StorageMode == 'Insert':
                    self.MongoHandler.dbInsert('stock',CurCategory,Header)
                elif StorageMode == 'Update':
                    self.MongoHandler.dbUpdateBody('stock',CurCategory, Body, CurDoc)

if __name__ == '__main__':
    TDX_DH = TdxDataEngine(r'C:\Users\wenbwang\Desktop\StockData\New folder')
    filePath = TDX_DH.GetTdxFileList()
    #TDX_DH.HandlerTdxDataToMongodb(filePath)
    filePath = TDX_DH.SearchInFileList("SH", "600000", filePath)
    Data = TDX_DH.HandlerTdxDataToDataFrame(filePath)
    print(Data)
    print("Done")