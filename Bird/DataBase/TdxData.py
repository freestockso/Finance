# -*- coding: utf-8 -*-

import json
import os
import re
from Logger import Log
from DataBase import MongoDB

import numpy
import pandas

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

            CategoryName = root.split('\\')[-1]
            CategoryPath = root

            FileList = []

            for ef in files:
                FileList.append(CategoryPath + '\\' + ef)

            if len(FileList) != 0 :          
                DataItem[CategoryName] = FileList
            else :
                self.writeLog.log(u'File list is None')
        return DataItem

    # Search in DataItem.
    # output will store into the dict
    # result ={"CategoryNames":[file paths list]}
    # sz is SH or SZ, 上海 深圳
    # id is number of shares，股票期货代码
    # FL_Data is file list that is dict
    def SearchInFileList(self, sz, id, FL_Data):

        if not FL_Data and isinstance(FL_Data, dict):
            self.writeLog.log(u'File list is Invalid')
            return

        for key, value in FL_Data.items():

            if not isinstance(value,list):
                self.writeLog.log(u'Path list is Invalid')
                return
            
            for path in value:
                DataFileName = sz +'#'+ id + '.txt'

                if DataFileName == path.split('\\')[-1]:
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
    # return DataFrame 
    def HandlerTdxDataToDataFrame(self, filePath):
        CurData = None
        DataType = "day"
        AllData = []

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
                    continue # no need for this function
                elif re.match(pattClass, CurData):
                    BodyList = re.split(r'\t{1}',CurData) #split by tab
                    if len(BodyList) == 8 and BodyList[1].strip() == '时间':
                        DataType = "mins"
                elif re.match(pattData, CurData):
                    BodyList = re.split(r'\s{1}',CurData) #split by tab

                    if (len(BodyList) != 7) and (len(BodyList) != 8):
                        self.writeLog.log('DataFile Body Error : ' + CurData)
                    
                    if DataType == "mins":
                        # convert to the ex : "2018/09/17-21:37"
                        time = BodyList[1][:2] + ':' + BodyList[1][2:]
                        BodyList.pop(1) # remove time item from the list
                    elif DataType == "day":
                        time = "00:00"
                        
                    date = BodyList[0] + '-' + time
                    BodyList[0] = date

                    for i in range(1,len(BodyList)):
                        BodyList[i] = float(BodyList[i])

                    AllData.append(BodyList)

                elif re.match(pattFooter, CurData):
                    #no need for this function
                    continue
                else:
                    self.writeLog.log('Matching failed : ' + CurData)

        TdxDataFrame = pandas.DataFrame(AllData)
        TdxDataFrame.columns = ['date','open','high','low','close','volume','Turnover']
        
        return TdxDataFrame


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