# -*- coding: utf-8 -*-

import numpy
import pandas
import matplotlib
import mpl_finance as mpf
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.ticker import Formatter
import datetime

import sys
sys.path.append('.\\')

from Logger import Log
from DataBase import MongoDB
from DataBase import TdxData

class Trend(object):
    
    def __init__(self):
        self.SeqNum = 0
        self.SeqDate = pandas.date_range('2000/1/1','2020/1/1', freq = '1D')
        self.writeLog = Log.Logger('TrendAnalyzer.txt')
    
    def cPrint(self, Content):
        #print(Content)
        pass


    def cutTimeRange(self, TimeTypeList, sTime, eTime):
        sIndex = 0
        sFlag = 0
        eIndex = 0
        
        sDate = datetime.datetime.strptime(sTime, '%Y/%m/%d-%H:%M')
        eDate = datetime.datetime.strptime(eTime, '%Y/%m/%d-%H:%M')

        for i in range(1,len(TimeTypeList)):
            cDate = datetime.datetime.strptime(TimeTypeList[i][0], '%Y/%m/%d-%H:%M')
            if sIndex == 0 and sFlag == 0 and cDate == sDate:
                sIndex = i
                sFlag = 0xFF # 设定为无效值 避免2次进入
            elif sIndex == 0 and sFlag == 0 and cDate > sDate:
                sIndex = i - 1
                sFlag = 0xFF # 设定为无效值 避免2次进入
            if eIndex == 0 and cDate >= eDate:
                eIndex = i
        if (eIndex == 0):
            eIndex = i

        return TimeTypeList[sIndex:(eIndex+1)]

    
    # its parameters is based on the result of calcPriceRange.
    # 根据rangenum数（波段数） ，以此为节点统计 波段涨幅。 涨幅相加。
    # 此函数会改变 rDataList 和 TimeTypeList， 增加2组 波段涨幅 （第1组为数据开始到后数第RangeNum-1个波段 第2组为后数第RangeNum个波段到数据最后波段，）
    # 返回波段数+2，因为增加2波数据
    def calcPriceXRange(self, rDataList, TimeTypeList, RangeNum, DataList):
        totalRangeNum = len(TimeTypeList) - 1
        preRangeNum = 0
        if totalRangeNum > RangeNum and RangeNum != 0:
            preRangeNum = totalRangeNum - RangeNum
        else:
            RangeNum = totalRangeNum
        
        Temp_TimeTypeList = []
        Temp_TimeTypeList.append(TimeTypeList[0])
        if preRangeNum > 0:
            Temp_TimeTypeList.append([TimeTypeList[preRangeNum][0],2])
        Temp_TimeTypeList.append([TimeTypeList[-1][0],3])

        Temp_listRange = self.calcPriceRange(DataList, Temp_TimeTypeList)

        Temp_TimeTypeList.pop(0) # 删除第一个时间节点，然后添加到 主 timetypelist里面去
        TimeTypeList += Temp_TimeTypeList

        for i in range(len(rDataList)):
            for key in rDataList[i]:
                if Temp_listRange[i].get(key):
                    rDataList[i][key] += Temp_listRange[i][key]
                else:
                    print("Error:数据类型不匹配。")

        return (RangeNum + 2)
    
    
    # # its parameters is based on the result of calcPriceRange.
    # # 根据rangenum数（波段数） ，以此为节点统计 波段涨幅。 涨幅相加。
    # # 此函数会改变 rDataList 和 TimeTypeList， 增加2组 波段涨幅 （第一组为后数第RangeNum个波段到数据最后波段，第二组为数据开始到后数第RangeNum-1个波段）
    # # 返回波段数+2，因为增加2波数据
    # def calcPriceXRange(self, rDataList, TimeTypeList, RangeNum):
    #     totalRangeNum = len(TimeTypeList) - 1
    #     preRangeNum = 0
    #     if totalRangeNum > RangeNum:
    #         preRangeNum = totalRangeNum - RangeNum
    #     else:
    #         RangeNum = totalRangeNum

    #     time1 = TimeTypeList[preRangeNum][0] #第一组数据的开始时间。
    #     type1 = 2                            #第一组数据的类型 不是顶分 不是底分 不是空，2为特殊类型。
    #     TimeTypeList.append([time1,type1])

    #     if (preRangeNum > 0):
    #         time2 = TimeTypeList[0][0]           #第二组数据的开始时间。
    #         type2 = 3                            #第二组数据的类型 不是顶分 不是底分 不是空，2为特殊类型。
    #         TimeTypeList.append([time2,type2])

    #     for rData in rDataList:
    #         for key, value in rData.items():
    #             # 为每个数据列表 添加第一组数据 （后数第RangeNum个波段到数据最后波段） 涨幅和
    #             rangeVal = 0
    #             for i in range(preRangeNum,len(value)):
    #                 rangeVal += value[i]
    #             value.append(float('%.2f' % rangeVal))

    #             # 为每个数据列表 添加第二组数据 （数据开始到后数第RangeNum-1个波段） 涨幅和
    #             rangeVal = 0
    #             if (preRangeNum > 0):
    #                 for i in range(preRangeNum):
    #                     rangeVal += value[i]
    #                 value.append(float('%.2f' % rangeVal))

    #     return (RangeNum + 2)

    # 涨跌幅=(现价-上一个交易日收盘价)/上一个交易日收盘价*100%
    # DataList is the dict list, [{item:[data]], data's format is list: "日期 开盘 最高 最低 收盘 成交量 成交额"
    # TimeList is list, ['2008/09/01-00:00','2008/09/01-00:00','2008/09/01-00:00']
    # return result : [{'煤炭': ['-9.82%', '4.96%', '-0.86%', '3.08%', '-0.06%', '7.16%', '-3.95%', '6.71%', '0.01%', '0.69%', '-6.46%', '2.03%', '1.15%']}]
    def calcPriceRange(self, DataList, TimeTypeList):

        OFFSET_DATE = 0
        OFFSET_CLOSE = 4
        pData = pandas.DataFrame()

        # 从list里面获取时间节点，组装成新的时间list使用
        TimeList = []
        for item in TimeTypeList:
            TimeList.append(item[0])
        
        if len(TimeList) < 2:
            return pData

        rDataList = []
        key = ''
        value =''
        for dictData in DataList:
            for key,value in dictData.items(): # 获取 key & value
                pass

            tDataList = []
            for time in TimeList:
                Found = False
                IndexFlag = 0 # 当数据不全时 使用接近时间的前一个数据。
                for i in range(len(value)):
                    if time == value[i][OFFSET_DATE]: # 以时间索引查找数据，记录当前日和上一日的收盘价，无上一日时 以当前日存储。每个日期存储2个数据。
                        if i > 0 :
                            tDataList.append(value[i-1][OFFSET_CLOSE])
                        else:
                            tDataList.append(value[i][OFFSET_CLOSE])
                        tDataList.append(value[i][OFFSET_CLOSE])
                        Found = True
                        break
                    if (time > value[i-1][OFFSET_DATE] and time < value[i][OFFSET_DATE]):
                        IndexFlag = i - 1
                if Found == False:
                    print("未找到对应数据：%s %s " % (key,time))
                    if IndexFlag > 0 :
                        tDataList.append(value[IndexFlag-1][OFFSET_CLOSE])
                    else:
                        tDataList.append(value[IndexFlag][OFFSET_CLOSE])
                    tDataList.append(value[IndexFlag][OFFSET_CLOSE])

            tRangeList = []
            for i in range(len(TimeList)-1): 
                # # 涨跌幅=(现价-上一个交易日收盘价)/上一个交易日收盘价*100%
                # rVal = '%.2f' % (((tDataList[i*2+3] - tDataList[i*2])/tDataList[i*2]) * 100)    #小数点保留2位,    "转百分数'%.2f%%'"
                # 涨跌幅=(现价-波段起始日收盘价)/上一个交易日收盘价*100%
                rVal = '%.2f' % (((tDataList[i*2+3] - tDataList[i*2+1])/tDataList[i*2+1]) * 100)    #小数点保留2位,    "转百分数'%.2f%%'"
                tRangeList.append(float(rVal))
            
            rDataList.append({key:tRangeList})
        
        return rDataList
    
    # the data format is DataFrame
    def Candlestick_MergeDataSetMode(self, kData, Index, Count):

        # 设定方向，向上 or 向下
        Direction = 'no'
        #kData[(Index-1):Index].high[-1]
        #kData[Index:(Index+1)].high[-1]
        if Index > 0:   # 此组包含数据前有其他数据，并与本组包含数据不存在包含关系。
            if kData[Index:(Index+1)].high.iloc[-1] > kData[(Index-1):Index].high.iloc[-1]:
                Direction = 'up'
            elif kData[Index:(Index+1)].low.iloc[-1] < kData[(Index-1):Index].low.iloc[-1]:
                Direction = 'down'
        elif Index == 0: # 此组包含数据前无其他数据，判断方向 使用本组的前两条数据
            if kData[(Index+1):(Index+2)].high.iloc[-1] > kData[Index:(Index+1)].high.iloc[-1]:
                Direction = 'up'
            elif kData[(Index+1):(Index+2)].low.iloc[-1] < kData[Index:(Index+1)].low.iloc[-1]:
                Direction = 'down'
            elif kData[(Index+1):(Index+2)].high.iloc[-1] < kData[Index:(Index+1)].high.iloc[-1]:
                Direction = 'down'
            elif kData[(Index+1):(Index+2)].low.iloc[-1] > kData[Index:(Index+1)].low.iloc[-1]:
                Direction = 'up'
            else:
                Direction = 'up'    # it's for the same's case.
        
        tData = kData[Index:(Index+1)]
        open = tData.open.iloc[-1]
        close = tData.close.iloc[-1]
        high = tData.high.iloc[-1]
        low = tData.low.iloc[-1]
        
        if Direction == 'up':
            for i in range(Index + 1,(Index+Count)):
                open = open if open > kData[i:(i+1)].open.iloc[-1] else kData[i:(i+1)].open.iloc[-1]
                close = close if close > kData[i:(i+1)].close.iloc[-1] else kData[i:(i+1)].close.iloc[-1]
                high = high if high > kData[i:(i+1)].high.iloc[-1] else kData[i:(i+1)].high.iloc[-1]
                low = low if low > kData[i:(i+1)].low.iloc[-1] else kData[i:(i+1)].low.iloc[-1]
        elif Direction == 'down':
            for i in range(Index + 1,(Index+Count)):
                open = open if open < kData[i:(i+1)].open.iloc[-1] else kData[i:(i+1)].open.iloc[-1]
                close = close if close < kData[i:(i+1)].close.iloc[-1] else kData[i:(i+1)].close.iloc[-1]
                high = high if high < kData[i:(i+1)].high.iloc[-1] else kData[i:(i+1)].high.iloc[-1]
                low = low if low < kData[i:(i+1)].low.iloc[-1] else kData[i:(i+1)].low.iloc[-1]
        elif Direction == 'no':
            print ("ERROR : Direction is no, in Candlestick_MergeData")

        tData.open.iloc[-1] = open
        tData.close.iloc[-1] = close
        tData.high.iloc[-1] = high
        tData.low.iloc[-1] = low
        tData.date.iloc[-1] = kData[(Index+Count-1):(Index+Count)].date.iloc[-1] #使用最后的时间节点

        return tData

    # kData store K data, format is DataFrame
    # rkData store the result after the RemoveEmbody
    # 包含关系 统计处理（合并后的时间节点 可能有问题, 当前dataframe数据为引用设置，会改变原始值）
    def Candlestick_RemoveEmbodySetMode(self, kData):
        rkData = pandas.DataFrame()

        CurData = kData[:1]
        CurCount = 1
        LastFlag = False
        for i in range(len(kData)):
            if i != (len(kData) - 1):
                NextData = kData[(i+1):(i+2)]
            else:
                #最后一条数据的next data设定为无效值，不存在包含关系。
                #当最后一条数据与之前数据不存在包含关系时，进行最后一条数据的存储
                #当最后一条数据与之前数据存在包含关系时，进行数据的合并并存储 
                LastFlag = True

            #whether there is a containment relationship.
            # 前2组if语句，记录包含关系的个数
            if LastFlag == False and CurData.high.iloc[-1] >= NextData.high.iloc[-1] and CurData.low.iloc[-1] <= NextData.low.iloc[-1]:
                CurCount = CurCount + 1

            elif LastFlag == False and CurData.high.iloc[-1] <= NextData.high.iloc[-1] and CurData.low.iloc[-1] >= NextData.low.iloc[-1]:
                CurData = NextData
                CurCount = CurCount + 1
            else:
                # 当组数据存在包含关系时，CurCount > 1， 合并数据 并存储。
                if CurCount > 1:
                    tData = self.Candlestick_MergeDataSetMode(kData, (i + 1 - CurCount), CurCount)
                    CurCount = 1
                # 在当前数据不存在包含关系时，CurCount = 1，直接存储    
                else:    
                    tData = CurData    
                CurData = NextData
                rkData = pandas.concat([rkData,tData],axis = 0)
        
        return rkData

    # kData store K data, format is DataFrame
    # rkData store the result after the RemoveEmbody
    # 按时间顺序比较包含关系，两两比较，包含关系没有传递性。
    def Candlestick_RemoveEmbodySeqMode(self, kData):
        rkData = pandas.DataFrame()

        contain = 0
        tempH1 = 0
        tempH2 = 0
        tempL1 = 0
        tempL2 = 0

        MergeData = pandas.DataFrame()  #合并后数据
        PreData = pandas.DataFrame()    #前一个数据
        CurData = pandas.DataFrame()    #当前数据
        NextData = pandas.DataFrame()   #下一个数据

        for i in range(len(kData)-1):
            if contain == 0:
                CurData = kData[i:i+1]     #当前数据
            else:
                contain = 0
                CurData = MergeData     #当前数据

            NextData = kData[i+1:i+2]   #后一个数据

            #whether there is a containment relationship.
            # 前2组if语句，记录包含关系的个数
            if (CurData.high.iloc[-1] >= NextData.high.iloc[-1] and CurData.low.iloc[-1] <= NextData.low.iloc[-1]):
                contain = 1 #第一根包含第二根
            elif (CurData.high.iloc[-1] <= NextData.high.iloc[-1] and CurData.low.iloc[-1] >= NextData.low.iloc[-1]):
                contain = 2 #第二根包含第一根
            
            if contain == 0:
                rkData = pandas.concat([rkData,CurData],axis = 0)
                PreData = CurData
            else:
                if contain == 1:
                    MergeData = CurData.copy(deep = True)
                elif contain == 2:
                    MergeData = NextData.copy(deep = True)

                if PreData.empty == True:
                    tempH1 = CurData.high.iloc[-1]
                    tempH2 = NextData.high.iloc[-1]
                    tempL1 = CurData.low.iloc[-1] 
                    tempL2 = NextData.low.iloc[-1]
                else:
                    tempH1 = PreData.high.iloc[-1]
                    tempH2 = CurData.high.iloc[-1]
                    tempL1 = PreData.low.iloc[-1] 
                    tempL2 = CurData.low.iloc[-1]

                if tempH1 < tempH2:
                    MergeData.open.iloc[-1] = CurData.open.iloc[-1] if CurData.open.iloc[-1] > NextData.open.iloc[-1] else NextData.open.iloc[-1]
                    MergeData.close.iloc[-1] = CurData.close.iloc[-1] if CurData.close.iloc[-1] > NextData.close.iloc[-1] else NextData.close.iloc[-1]
                    MergeData.high.iloc[-1] = CurData.high.iloc[-1] if CurData.high.iloc[-1] > NextData.high.iloc[-1] else NextData.high.iloc[-1]
                    MergeData.low.iloc[-1] = CurData.low.iloc[-1] if CurData.low.iloc[-1] > NextData.low.iloc[-1] else NextData.low.iloc[-1]
                elif tempL1 > tempL2:
                    MergeData.open.iloc[-1] = CurData.open.iloc[-1] if CurData.open.iloc[-1] < NextData.open.iloc[-1] else NextData.open.iloc[-1]
                    MergeData.close.iloc[-1] = CurData.close.iloc[-1] if CurData.close.iloc[-1] < NextData.close.iloc[-1] else NextData.close.iloc[-1]
                    MergeData.high.iloc[-1] = CurData.high.iloc[-1] if CurData.high.iloc[-1] < NextData.high.iloc[-1] else NextData.high.iloc[-1]
                    MergeData.low.iloc[-1] = CurData.low.iloc[-1] if CurData.low.iloc[-1] < NextData.low.iloc[-1] else NextData.low.iloc[-1]
                else:
                    print ("ERROR : Direction is no, in Candlestick_MergeData")

        # 加载最后一条数据,无包含关系连接最后一条数据，有包含关系连接合并数据
        if contain == 0:
            rkData = pandas.concat([rkData,NextData],axis = 0)
        else:
            rkData = pandas.concat([rkData,MergeData],axis = 0)            
        
        return rkData

    # 在去掉包含关系后，进行分型处理：顶分型或底分型
    # 在去掉包含关系后，k线转向必有一个顶分型和一个底分型
    # the result is time list, that is point to G and D
    # mode is true, append start & end time to the result, false is no need.
    def Candlestick_TypeAnalysis(self, kData, Mode = False):
        
        i = 0
        preType = 0
        preHigh = 0
        preLow = 0
        preIndex = -5    #记录当前K线索引
        preKey = 0
        typeDict = {preKey:[preIndex,preType]}
        # 查询所有分型, -1 : 底分型; 0 : 空; 1 : 顶分型。
        # A 相同分型 取最高价或最低价
        # B 不同分型 
        #   1. 底分型的底最高价低于上一个顶分型的最高价，底最低价低于上一个顶最低价
        #   2. 顶分型的顶最低价高于上一个底分型的最低价，顶最高价高于上一个底最高价
        # C 基于结合律,顶底之间必须5根k线 （包括顶底）

        while i < (len(kData)-2):
            Data1 = kData[i:(i+1)]
            Data2 = kData[(i+1):(i+2)]
            Data3 = kData[(i+2):(i+3)]

            if (Data2.iloc[-1].high > Data1.iloc[-1].high and Data2.iloc[-1].high > Data3.iloc[-1].high and
                Data2.iloc[-1].low > Data1.iloc[-1].low and Data2.iloc[-1].low > Data3.iloc[-1].low
                ):
                # 当前数据为顶分型
                if preType == 0 or preType == 1: #同顶分型 比较高点
                    if Data2.iloc[-1].high < preHigh: # 当前高点低于之前高点 忽略当前分型
                        i += 1
                        self.cPrint("同顶分型 比较高点, 当前高点低于之前高点 忽略当前分型")
                        self.cPrint(Data2)
                        continue
                    else: # 当前高点高于之前高点，“不需要”满足结合律，在之前项基础上保存当前项
                        preType = 1
                        preHigh = Data2.iloc[-1].high
                        preLow = Data2.iloc[-1].low
                        preIndex = i + 1
                        typeDict[preKey] = [i + 1, 1] # 更新当前顶分型
                        i += 1
                elif preType == -1: # 不同分型
                    if Data2.iloc[-1].high < preHigh or Data2.iloc[-1].low < preLow: # 顶分型的顶最低价高于上一个底分型的最低价，顶最高价高于上一个底最高价
                        i += 1
                        self.cPrint("顶分型 分型的顶最低价高于上一个底分型的最低价，顶最高价高于上一个底最高价")
                        self.cPrint(Data2)
                        continue
                    elif i + 1 < preIndex + 4: #不满足结合律
                        self.cPrint("顶分型 不满足结合律")
                        self.cPrint(Data2)
                        i += 1
                        continue
                    else: #把当前数据赋值给之前数据，添加当前数据为新的顶分型
                        preType = 1
                        preHigh = Data2.iloc[-1].high
                        preLow = Data2.iloc[-1].low
                        preIndex = i + 1
                        preKey += 1
                        typeDict[preKey] = [preIndex, preType] 
                        i += 1

            elif (Data2.iloc[-1].high < Data1.iloc[-1].high and Data2.iloc[-1].high < Data3.iloc[-1].high and
                Data2.iloc[-1].low < Data1.iloc[-1].low and Data2.iloc[-1].low < Data3.iloc[-1].low
                ):
                # 当前数据为底分型
                if preType == 0 or preType == -1: #同底分型 比较低点
                    if Data2.iloc[-1].low > preLow: # 当前低点高于之前低点 忽略当前分型
                        self.cPrint("同底分型 比较低点 当前低点高于之前低点 忽略当前分型")
                        self.cPrint(Data2)
                        i += 1
                        continue
                    else: # 当前低点低于之前低点，“不需要”满足结合律，在之前项基础上保存当前项
                        preType = -1
                        preHigh = Data2.iloc[-1].high
                        preLow = Data2.iloc[-1].low
                        preIndex = i + 1
                        typeDict[preKey] = [i + 1, -1] #更新当前底分型
                        i += 1
                elif preType == 1: # 不同分型
                    if Data2.iloc[-1].high > preHigh or Data2.iloc[-1].low > preLow: # 底分型的底最高价低于上一个顶分型的最高价，底最低价低于上一个顶最低价
                        self.cPrint("#底分型的底最高价低于上一个顶分型的最高价，底最低价低于上一个顶最低价")
                        self.cPrint(Data2)
                        i += 1
                        continue
                    elif i + 1 < preIndex + 4: #不满足结合律
                        self.cPrint("底分型 不满足结合律")
                        self.cPrint(Data2)
                        i += 1
                        continue
                    else: # 把当前数据赋值给之前数据，添加当前数据为新的底分型
                        preType = -1
                        preHigh = Data2.iloc[-1].high
                        preLow = Data2.iloc[-1].low
                        preIndex = i + 1
                        preKey += 1
                        typeDict[preKey] = [preIndex, preType]
                        i += 1
            i += 1

        # 在分型基础上，输出时间
        # typeDict 格式： {key:{index, type}}  key为搜索时的索引值从0开始，+1；index为kData第几个数据项（行）从0开始，type表示 顶底
        typeTimeList = []
        for key, value in typeDict.items():
            typeTimeList.append(value)
        if Mode == True and len(typeTimeList) > 0:
            if (typeTimeList[0][0] != 0): #第一个数据kData索引不是0时，添加kData第一个数据
                typeTimeList.insert(0,[0,0]) # kData 第一个数据索引为0，分型为空
            if (typeTimeList[len(typeTimeList)-1][0] != (len(kData)-1)): #最一个数据kData索引不是kData最后一个数据项时，添加kData最后一个数据
                typeTimeList.append([(len(kData)-1),0]) # kData 最后一个数据索引为0，分型为空

        for item in typeTimeList:
            row = item[0]
            item[0] = kData.iloc[[row]].iloc[-1].date

            # i = 0
            # for index, row in kData.iterrows():
            #     if i == value[0]:
            #         typeTimeList.append(row['date'])
            #         break
            #     i = i + 1

        return typeTimeList

    
    #将x轴的浮点数格式化成日期小时分钟
    #默认的x轴格式化是日期被dates.date2num之后的浮点数，因为在上面乘以了1440，所以默认是错误的
    #只能自己将浮点数格式化为日期时间分钟
    #参考https://matplotlib.org/examples/pylab_examples/date_index_formatter.html
    class MyFormatter(Formatter):
        def __init__(self, dates, fmt = '%Y%m%d %H:%M'):
            self.dates = dates
            self.fmt = fmt

        def __call__(self, x, pos = 0):
            'Return the label for time x at position pos'
            ind = int(numpy.round(x))
            #ind就是x轴的刻度数值，不是日期的下标
            return dates.num2date(ind/1440).strftime(self.fmt)

    # return seqnum, seqnum + 1
    def fSeqNum(self, DateInput):

        DtIndex = self.SeqDate[self.SeqNum]
        self.SeqNum = self.SeqNum + 1

        return DtIndex

    # 绘制K线
    def Candlestick_Drawing(self, kData):

        # kData need to convert time to Pandas' format.
        tData = kData

        # convert data to pandas format, ignore it, for the continuesly K-line
        #tData['date'] = pandas.to_datetime(tData['date'],format = "%Y/%m/%d-%H:%M")
        #tData['date'] = tData['date'].apply(lambda x:dates.date2num(x)*1440)

        # seq for data
        self.SeqNum = 0
        tData['date'] = tData['date'].apply(lambda x:self.fSeqNum(x))
        tData['date'] = pandas.to_datetime(tData['date'],format = "%Y-%m-%d")
        tData['date'] = tData['date'].apply(lambda x:dates.date2num(x))
        
        #convert to matrix
        tData_mat = tData.values

        # 创建一个子图 
        fig,ax = plt.subplots(figsize = (20, 10))
 
        fig.subplots_adjust(bottom = 0.2)
        #开盘,最高,最低,收盘
        mpf.candlestick_ohlc(ax,tData_mat,width=0.9,colorup='red',colordown='green')
        #开盘,收盘,最高,最低
        #mpf.candlestick_ochl(ax,tData_mattData_mat,width=1.2,colorup='r',colordown='green')
        #mpf.candlestick_ohlc(ax, tData_mat, colordown = 'green', colorup = 'red', width = 0.2, alpha = 1)
        
        formatter = self.MyFormatter(tData_mat[:,0])
        ax.xaxis.set_major_formatter(formatter)

        plt.title("100000")
        plt.xlabel("Date")
        plt.ylabel("Price")

        '''
        for label in ax.get_xticklabels():
            label.set_rotation(90)
            label.set_horizontalalignment('right')
        '''    

        # 设置X轴刻度为日期时间
        ax.xaxis_date()
        # X轴刻度文字倾斜45度
        plt.xticks(rotation=45)

        ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(6)) 
            
        plt.show()

    # 股票数据格式转换，2维列表到dataframe， 列默认为：['date','open','high','low','close','volume','Turnover']
    def StockDataList2DataFrame(self,dList):
        pData = pandas.DataFrame(dList)
        pData.columns = ['date','open','high','low','close','volume','Turnover']
        return pData


if __name__ == '__main__':

    startTime = '2018/06/01-00:00'
    endTime = '2018/12/12-00:00'
    DataPath = r'.\StockData'
    ID_ZS_SH = '399300'
    NAME_ZS_SH = '沪深300'
    ID_BK = 'Categorys'

    Tdx = TdxData.TdxDataEngine(DataPath)
    filePath = Tdx.GetTdxFileList()
    File_SH = Tdx.SearchInFileList(filePath,'',ID_ZS_SH)
    File_BK = Tdx.SearchInFileList(filePath,ID_BK, '')
    Data_SH = Tdx.HandlerTdxDataToList(File_SH,startTime,endTime)
    Data_BK = Tdx.HandlerTdxDataToList(File_BK,startTime,endTime)

    #asd = pandas.DataFrame([["2018/08/27-09:35",10.33 , 10.35 , 10.27 , 10.31 , 2151100.0  ,22191502.0]])
    #asd.columns =  ['date','open','high','low','close','volume','Turnover']

    T = Trend()
    tData = T.StockDataList2DataFrame(Data_SH[0][NAME_ZS_SH])

    #tData_RE = T.Candlestick_RemoveEmbodySetMode(tData)
    tData_RE = T.Candlestick_RemoveEmbodySeqMode(tData)

    # f1 = open(r'C:\Users\LL\Desktop\1.txt','w')
    # f2 = open(r'C:\Users\LL\Desktop\2.txt','w')
    # for i in range(len(tData)):
    #     temp1 = tData[i:i+1]
    #     print(temp1,file = f1)
    # print(len(tData))
    # for i in range(len(tData_RE)):
    #     temp1 = tData_RE[i:i+1]
    #     print(temp1,file = f2)
    # print(len(tData_RE))
    # f1.close()
    # f2.close()

    # # k线
    # T.Candlestick_Drawing(tData_RE)

    # 分析分型， 返回分型 顶底时间列表
    typeTimeList = T.Candlestick_TypeAnalysis(tData_RE)

    TimeList = []
    for item in typeTimeList:
        TimeList.append(item[0])

    T.calcPriceRange(Data_BK, TimeList)

    print(TimeList)

    print("Done")