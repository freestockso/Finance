# -*- coding: utf-8 -*-

import numpy
import pandas
import matplotlib
import mpl_finance as mpf
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.ticker import Formatter
from operator import itemgetter, attrgetter
import datetime
import copy

import sys
sys.path.append('.\\')

from Logger import Log
from DataBase import MongoDB
from DataBase import TdxData

class Trend(object):
    
    def __init__(self):
        self.TYPING_NULL = 0        # 无顶底分型
        self.TYPING_TOP = 1         # 顶分型
        self.TYPING_BTM = -1        # 底分型
        self.SummaryData1 = 0       # 统计数据1存在标识， 0为不存在，1为存在。
        self.SummaryData2 = 0       # 统计数据2存在标识， 0为不存在，1为存在。
        self.SeqNum = 0
        self.SeqDate = pandas.date_range('2000/1/1','2020/1/1', freq = '1D')
        self.writeLog = Log.Logger('TrendAnalyzer.txt')
    
    def cPrint(self, Content):
        #print(Content)
        pass
    
    def GetAverage(self,NumList):
        Sum = 0
        for i in range(len(NumList)):
            Sum += NumList[i]
        return Sum / len(NumList)
    
    def PowerWave(self, PowerList):
        pass

    # 对排序数据进行强弱分类 ++强，+偏强，-偏弱，--弱
    def PowerClassification(self, SortedDataList,ID_NAME):
        plusplus = 10
        plus = 18
        minus = 18
        minusminus = 10
        plusplusType = 'pp'
        plusType = 'p'
        minusType = 'm'
        minusminusType = 'mm'
        RangeNum = len(SortedDataList)

        # 将数据转化为2维列表,存储在 AllData
        AllData = []
        # TargetIndex 为1维列表 用于记录标的数据索引
        TargetIndex = []
        for i in range(RangeNum):
            DataList = []
            for j in range(len(SortedDataList[i])):
                if SortedDataList[i][j][0] == ID_NAME:
                    TargetIndex.append(j)
                DataList.append(SortedDataList[i][j][1])
            AllData.append(DataList)
        
        # Quota 为2维列表 用于每组波段标的数据值和当前波段数据平均值
        Quota = []
        for i in range(RangeNum):
            Quota.append([AllData[i][TargetIndex[i]],self.GetAverage(AllData[i])])
        
        # 波段数据强弱显示存在Power列表中,二维列表
        Power = []
        for i in range(RangeNum):
            cPower = [0] * len(AllData[i])
            # 当前波段数据平均涨幅大于0 为上行
            if Quota[i][1] >= 0:    # 上行
                # 先选++组
                k = 0
                for j in range(len(AllData[i])):
                    # 如果等于标的数据索引，退出
                    if j == TargetIndex[i]:
                        continue
                    # 必须大于A且大于B且最多10个（10个最大值）
                    if AllData[i][j] > Quota[i][0] and  AllData[i][j] > Quota[i][1] and k < plusplus:
                        cPower[j] = plusplusType
                        k += 1
                # 再选--组
                k = 0
                for j in range((len(AllData[i])-1),-1,-1):
                    # 如果等于标的数据索引，退出
                    if j == TargetIndex[i]:
                        continue
                    # 必须小于A且小于B且最多10个（10个最大值）
                    if AllData[i][j] < Quota[i][0] and  AllData[i][j] < Quota[i][1] and k < minusminus:
                        cPower[j] = minusminusType
                        k += 1
                # 再选+组
                k = 0
                for j in range(len(AllData[i])):
                    # 如果等于标的数据索引，退出
                    if j == TargetIndex[i]:
                        continue
                    # 必须大于B且最多18个（++组后18个最大值）
                    if cPower[j] == 0 and AllData[i][j] > Quota[i][1] and k < plus:
                        cPower[j] = plusType
                        k += 1
                # 最后选-组
                for j in range(len(AllData[i])):
                    # 如果等于标的数据索引，退出
                    if j == TargetIndex[i]:
                        continue
                    # 剩余项都算-组
                    if cPower[j] == 0:
                        cPower[j] = minusType
                Power.append(cPower)
            else:   # 下行
                # 先选--组
                k = 0
                for j in range((len(AllData[i])-1),-1,-1):
                    # 如果等于标的数据索引，退出
                    if j == TargetIndex[i]:
                        continue
                    # 必须小于A且小于B且最多10个（10个最大值）
                    if AllData[i][j] < Quota[i][0] and  AllData[i][j] < Quota[i][1] and k < minusminus:
                        cPower[j] = minusminusType
                        k += 1
                # 再选++组
                k = 0
                for j in range(len(AllData[i])):
                    # 如果等于标的数据索引，退出
                    if j == TargetIndex[i]:
                        continue
                    # 必须大于A且大于B且最多10个（10个最大值）
                    if AllData[i][j] > Quota[i][0] and  AllData[i][j] > Quota[i][1] and k < plusplus:
                        cPower[j] = plusplusType
                        k += 1
                # 再选-组
                k = 0
                for j in range((len(AllData[i])-1),-1,-1):
                    # 如果等于标的数据索引，退出
                    if j == TargetIndex[i]:
                        continue
                    # 再选-组，必须小于B且最多18个（--后18个最小值）
                    if cPower[j] == 0 and AllData[i][j] < Quota[i][1] and k < minus:
                        cPower[j] = minusType
                        k += 1
                # 最后选+组
                for j in range(len(AllData[i])):
                    # 如果等于标的数据索引，退出
                    if j == TargetIndex[i]:
                        continue
                    # 剩余项都算+组
                    if cPower[j] == 0:
                        cPower[j] = plusType
                Power.append(cPower)

        return Power




    # 波段涨幅列表排序，返回结果为2维列表 例如 [[('航空', -4.42), ('石油', -5.57), ('电力', -6.88)]]
    # Mode = True 为降序，Mode = False 为升序
    def RangeListSort(self, RangeList, TimeTypeList, Mode = True):
        AllData = []
        for i in range(len(TimeTypeList) - 1):
            rDataList = []
            for dictData in RangeList:
                for key,value in dictData.items(): 
                    rDataList.append((key,value[i]))
            rDataList = sorted(rDataList, key = itemgetter(1), reverse = Mode)
            AllData.append(rDataList)
        return AllData

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
    
    # 根据时间波段分型列表，分别输出波段时间和波段类型
    # ExpTimeList = []   #存储波段时间戳，转换规则如下。最后一个时间戳 为无效值。 20180131-20180228, 转换后0131-0228。
    # ExpTypeList = []   #存储分型
    # 返回时间分型，总的波段数
    def GetRangeInfo(self, TimeTypeList, ExpRangeTime, ExpRangeType,SumFlag = ()):
        TotalRangeNum = len(TimeTypeList) - 1
        SumNum = 0
        SumIndex = []
        j = 0
        for i in range(len(SumFlag)):
            if SumFlag[i] == 1:
                SumNum += 1 
                SumIndex.append(i+1)
        tIndex = 0
        for i in range(TotalRangeNum): # 波段类型为当前时间周期内后一个分型类型，统计数据类型 单独处理
            if (i == (TotalRangeNum - SumNum)): # 判断当前索引是不是统计数据。
                cType = '#' + str(SumIndex[j])
                j += 1
                SumNum -= 1
            elif (TimeTypeList[i+1][1] == 1):     # 顶分型
                cType = '+'
            elif (TimeTypeList[i+1][1] == -1):  # 底分型
                cType = '-'
            elif(TimeTypeList[i+1][1] == 0):    # 无分型 一般为数据开始或结束波段
                cType = '*'
            else:
                cType = 'Error'
            ExpRangeType.append(cType)

            if cType == '#1':
                time1 = TimeTypeList[0][0]
                time2 = TimeTypeList[i+1][0]
                tIndex = i + 1
            elif cType == '#2':
                time1 = TimeTypeList[tIndex][0]
                time2 = TimeTypeList[i + 1][0]
            else:
                time1 = TimeTypeList[i][0]
                time2 = TimeTypeList[i+1][0]

            T_std1 = datetime.datetime.strptime(time1, '%Y/%m/%d-%H:%M')
            T_std2 = datetime.datetime.strptime(time2, '%Y/%m/%d-%H:%M')

            ExpRangeTime.append(str((T_std1.year % 100)* 10000 + T_std1.month * 100 + T_std1.day) + '-' 
            + str((T_std2.year % 100) * 10000 +T_std2.month * 100 + T_std2.day))
        
        return TotalRangeNum
    
    # its parameters is based on the result of calcPriceRange.
    # 根据rangenum数（波段数） ，以此为节点统计 波段涨幅。 涨幅相加。
    # 此函数会改变 rDataList 和 TimeTypeList， 增加2组 波段涨幅 （第1组为数据开始到后数第RangeNum-1个波段 第2组为后数第RangeNum个波段到数据最后波段，）
    # 返回波段数据标识列表
    def calcPriceXRange(self, rDataList, TimeTypeList, RangeNum, DataList):
        self.SummaryData1 = 0
        self.SummaryData2 = 0
        totalRangeNum = len(TimeTypeList) - 1
        preRangeNum = 0
        if totalRangeNum > RangeNum and RangeNum != 0:
            preRangeNum = totalRangeNum - RangeNum
        else:
            RangeNum = totalRangeNum
        
        Temp_TimeTypeList = []
        Temp_TimeTypeList.append(TimeTypeList[0])
        # 新增统计数据时间段的分型为TYPING_NULL
        if preRangeNum > 0:
            Temp_TimeTypeList.append([TimeTypeList[preRangeNum][0],self.TYPING_NULL])
            self.SummaryData1 = 1
        Temp_TimeTypeList.append([TimeTypeList[-1][0],self.TYPING_NULL])
        self.SummaryData2 = 1

        Temp_listRange = self.calcPriceRange(DataList, Temp_TimeTypeList)

        Temp_TimeTypeList.pop(0) # 删除第一个时间节点，然后添加到 主 timetypelist里面去
        TimeTypeList += Temp_TimeTypeList

        for i in range(len(rDataList)):
            for key in rDataList[i]:
                if Temp_listRange[i].get(key):
                    rDataList[i][key] += Temp_listRange[i][key]
                else:
                    print("Error:数据类型不匹配。")

        return (RangeNum + self.SummaryData1 + self.SummaryData2)
    
    
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
    def RemoveEmbodySeqMode_2DArray(self, kData, open = 1, high = 2, low = 3, close = 4):
        
        contain = 0
        tempH1 = 0
        tempH2 = 0
        tempL1 = 0
        tempL2 = 0

        rkData = []     # 结果存储
        MergeData = []  #合并后数据
        PreData = []    #前一个数据
        CurData = []    #当前数据
        NextData = []   #下一个数据

        for i in range(len(kData)-1):
            if contain == 0:
                CurData = kData[i]     #当前数据
            else:
                contain = 0
                CurData = MergeData     #当前数据

            NextData = kData[i+1]   #后一个数据

            #whether there is a containment relationship.
            # 前2组if语句，记录包含关系的个数
            if (CurData[high] >= NextData[high] and CurData[low] <= NextData[low]):
                contain = 1 #第一根包含第二根
            elif (CurData[high] <= NextData[high] and CurData[low] >= NextData[low]):
                contain = 2 #第二根包含第一根
            
            if contain == 0:
                rkData.append(CurData)
                PreData = CurData
            else:
                if contain == 1:
                    MergeData = copy.deepcopy(CurData)
                elif contain == 2:
                    MergeData = copy.deepcopy(NextData)

                if PreData == []:
                    tempH1 = CurData[high]
                    tempH2 = NextData[high]
                    tempL1 = CurData[low] 
                    tempL2 = NextData[low]
                else:
                    tempH1 = PreData[high]
                    tempH2 = CurData[high]
                    tempL1 = PreData[low] 
                    tempL2 = CurData[low]

                if tempH1 < tempH2:
                    MergeData[open] = CurData[open] if CurData[open] > NextData[open] else NextData[open]
                    MergeData[close] = CurData[close] if CurData[close] > NextData[close] else NextData[close]
                    MergeData[high] = CurData[high] if CurData[high] > NextData[high] else NextData[high]
                    MergeData[low] = CurData[low] if CurData[low] > NextData[low] else NextData[low]
                elif tempL1 > tempL2:
                    MergeData[open] = CurData[open] if CurData[open] < NextData[open] else NextData[open]
                    MergeData[close] = CurData[close] if CurData[close] < NextData[close] else NextData[close]
                    MergeData[high] = CurData[high] if CurData[high] < NextData[high] else NextData[high]
                    MergeData[low] = CurData[low] if CurData[low] < NextData[low] else NextData[low]
                else:
                    print ("ERROR : Direction is no, in Candlestick_MergeData")

        # 加载最后一条数据,无包含关系连接最后一条数据，有包含关系连接合并数据
        if contain == 0:
            rkData.append(NextData)
        else:
            rkData.append(MergeData)          
        
        return rkData
    
    # 在去掉包含关系后，进行分型处理：顶分型或底分型
    # 在去掉包含关系后，k线转向必有一个顶分型和一个底分型
    # the result is time list, that is point to G and D
    # mode is true, append start & end time to the result, false is no need.
    def TypeAnalysis_2DArray(self, kData, Mode = False, open = 1, high = 2, low = 3, close = 4):
        
        i = 0
        preType = self.TYPING_NULL
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
            Data1 = kData[i]
            Data2 = kData[(i+1)]
            Data3 = kData[(i+2)]

            if (Data2[high] > Data1[high] and Data2[high] > Data3[high] and
                Data2[low] > Data1[low] and Data2[low] > Data3[low]
                ):
                # 当前数据为顶分型
                if preType == self.TYPING_NULL or preType == self.TYPING_TOP: #同顶分型 比较高点
                    if Data2[high] < preHigh: # 当前高点低于之前高点 忽略当前分型
                        i += 1
                        self.cPrint("同顶分型 比较高点, 当前高点低于之前高点 忽略当前分型")
                        self.cPrint(Data2)
                        continue
                    else: # 当前高点高于之前高点，“不需要”满足结合律，在之前项基础上保存当前项
                        preType = self.TYPING_TOP
                        preHigh = Data2[high]
                        preLow = Data2[low]
                        preIndex = i + 1
                        typeDict[preKey] = [i + 1, self.TYPING_TOP] # 更新当前顶分型
                        i += 1
                elif preType == self.TYPING_BTM: # 不同分型
                    if Data2[high] < preHigh or Data2[low] < preLow: # 顶分型的顶最低价高于上一个底分型的最低价，顶最高价高于上一个底最高价
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
                        preType = self.TYPING_TOP
                        preHigh = Data2[high]
                        preLow = Data2[low]
                        preIndex = i + 1
                        preKey += 1
                        typeDict[preKey] = [preIndex, preType] 
                        i += 1

            elif (Data2[high] < Data1[high] and Data2[high] < Data3[high] and
                Data2[low] < Data1[low] and Data2[low] < Data3[low]
                ):
                # 当前数据为底分型
                if preType == self.TYPING_NULL or preType == self.TYPING_BTM: #同底分型 比较低点
                    if Data2[low] > preLow: # 当前低点高于之前低点 忽略当前分型
                        self.cPrint("同底分型 比较低点 当前低点高于之前低点 忽略当前分型")
                        self.cPrint(Data2)
                        i += 1
                        continue
                    else: # 当前低点低于之前低点，“不需要”满足结合律，在之前项基础上保存当前项
                        preType = self.TYPING_BTM
                        preHigh = Data2[high]
                        preLow = Data2[low]
                        preIndex = i + 1
                        typeDict[preKey] = [i + 1, self.TYPING_BTM] #更新当前底分型
                        i += 1
                elif preType == self.TYPING_TOP: # 不同分型
                    if Data2[high] > preHigh or Data2[low] > preLow: # 底分型的底最高价低于上一个顶分型的最高价，底最低价低于上一个顶最低价
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
                        preType = self.TYPING_BTM
                        preHigh = Data2[high]
                        preLow = Data2[low]
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
                typeTimeList.insert(0,[0,self.TYPING_NULL]) # kData 第一个数据索引为0，分型为空
            if (typeTimeList[len(typeTimeList)-1][0] != (len(kData)-1)): #最一个数据kData索引不是kData最后一个数据项时，添加kData最后一个数据
                typeTimeList.append([(len(kData)-1),self.TYPING_NULL]) # kData 最后一个数据索引为0，分型为空

        for item in typeTimeList:
            row = item[0]
            item[0] = kData[row][0]

            # i = 0
            # for index, row in kData.iterrows():
            #     if i == value[0]:
            #         typeTimeList.append(row['date'])
            #         break
            #     i = i + 1

        return typeTimeList

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
        preType = self.TYPING_NULL
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
                if preType == self.TYPING_NULL or preType == self.TYPING_TOP: #同顶分型 比较高点
                    if Data2.iloc[-1].high < preHigh: # 当前高点低于之前高点 忽略当前分型
                        i += 1
                        self.cPrint("同顶分型 比较高点, 当前高点低于之前高点 忽略当前分型")
                        self.cPrint(Data2)
                        continue
                    else: # 当前高点高于之前高点，“不需要”满足结合律，在之前项基础上保存当前项
                        preType = self.TYPING_TOP
                        preHigh = Data2.iloc[-1].high
                        preLow = Data2.iloc[-1].low
                        preIndex = i + 1
                        typeDict[preKey] = [i + 1, self.TYPING_TOP] # 更新当前顶分型
                        i += 1
                elif preType == self.TYPING_BTM: # 不同分型
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
                        preType = self.TYPING_TOP
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
                if preType == self.TYPING_NULL or preType == self.TYPING_BTM: #同底分型 比较低点
                    if Data2.iloc[-1].low > preLow: # 当前低点高于之前低点 忽略当前分型
                        self.cPrint("同底分型 比较低点 当前低点高于之前低点 忽略当前分型")
                        self.cPrint(Data2)
                        i += 1
                        continue
                    else: # 当前低点低于之前低点，“不需要”满足结合律，在之前项基础上保存当前项
                        preType = self.TYPING_BTM
                        preHigh = Data2.iloc[-1].high
                        preLow = Data2.iloc[-1].low
                        preIndex = i + 1
                        typeDict[preKey] = [i + 1, self.TYPING_BTM] #更新当前底分型
                        i += 1
                elif preType == self.TYPING_TOP: # 不同分型
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
                        preType = self.TYPING_BTM
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
                typeTimeList.insert(0,[0,self.TYPING_NULL]) # kData 第一个数据索引为0，分型为空
            if (typeTimeList[len(typeTimeList)-1][0] != (len(kData)-1)): #最一个数据kData索引不是kData最后一个数据项时，添加kData最后一个数据
                typeTimeList.append([(len(kData)-1),self.TYPING_NULL]) # kData 最后一个数据索引为0，分型为空

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


if __name__ == '__test__':

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


test_data = [[20190108110000, 5890., 5904., 5888., 5904.],
[20190108110500, 5902., 5902., 5892., 5892.],
[20190108111000, 5892., 5894., 5886., 5888.],
[20190108111500, 5888., 5892., 5884., 5884.],
[20190108112000, 5884., 5888., 5878., 5886.],
[20190108112500, 5886., 5896., 5886., 5896.],
[20190108113000, 5896., 5902., 5892., 5896.],
[20190108133500, 5894., 5894., 5884., 5890.],
[20190108134000, 5890., 5890., 5882., 5884.],
[20190108134500, 5884., 5886., 5872., 5876.],
[20190108135000, 5876., 5880., 5872., 5874.],
[20190108135500, 5874., 5884., 5874., 5880.],
[20190108140000, 5880., 5886., 5876., 5884.],
[20190108140500, 5884., 5890., 5878., 5886.],
[20190108141000, 5886., 5890., 5882., 5890.],
[20190108141500, 5892., 5902., 5890., 5900.],
[20190108142000, 5900., 5916., 5898., 5910.],
[20190108142500, 5912., 5914., 5902., 5904.],
[20190108143000, 5904., 5906., 5894., 5896.],
[20190108143500, 5896., 5906., 5896., 5904.],
[20190108144000, 5904., 5904., 5892., 5898.],
[20190108144500, 5898., 5902., 5894., 5898.],
[20190108145000, 5898., 5900., 5890., 5894.],
[20190108145500, 5892., 5894., 5878., 5882.],
[20190108150000, 5882., 5886., 5880., 5884.],
[20190108210500, 5910., 5930., 5906., 5916.],
[20190108211000, 5916., 5920., 5902., 5918.],
[20190108211500, 5916., 5920., 5910., 5910.],
[20190108212000, 5910., 5918., 5906., 5914.],
[20190108212500, 5914., 5924., 5914., 5914.],
[20190108213000, 5914., 5922., 5910., 5922.],
[20190108213500, 5922., 5928., 5914., 5926.],
[20190108214000, 5926., 5928., 5918., 5920.],
[20190108214500, 5922., 5928., 5920., 5922.],
[20190108215000, 5922., 5924., 5906., 5908.],
[20190108215500, 5908., 5910., 5890., 5894.],
[20190108220000, 5896., 5902., 5894., 5900.],
[20190108220500, 5898., 5924., 5892., 5922.],
[20190108221000, 5920., 5922., 5908., 5910.],
[20190108221500, 5912., 5914., 5906., 5910.],
[20190108222000, 5912., 5916., 5902., 5904.],
[20190108222500, 5904., 5912., 5904., 5908.],
[20190108223000, 5908., 5914., 5902., 5910.],
[20190108223500, 5910., 5920., 5908., 5916.],
[20190108224000, 5916., 5916., 5906., 5906.],
[20190108224500, 5908., 5916., 5906., 5916.],
[20190108225000, 5916., 5918., 5910., 5916.],
[20190108225500, 5914., 5918., 5912., 5912.],
[20190108230000, 5914., 5918., 5912., 5916.],
[20190108230500, 5914., 5920., 5914., 5916.],
[20190108231000, 5916., 5920., 5908., 5910.],
[20190108231500, 5910., 5912., 5898., 5900.],
[20190108232000, 5902., 5902., 5892., 5900.],
[20190108232500, 5900., 5902., 5898., 5898.],
[20190108233000, 5898., 5908., 5898., 5898.],
[20190109090500, 5910., 5964., 5910., 5936.],
[20190109091000, 5938., 5958., 5936., 5950.],
[20190109091500, 5952., 5964., 5946., 5952.],
[20190109092000, 5954., 5960., 5950., 5960.],
[20190109092500, 5960., 5970., 5952., 5966.],
[20190109093000, 5964., 5986., 5960., 5984.],
[20190109093500, 5986., 5990., 5974., 5982.],
[20190109094000, 5980., 5992., 5980., 5980.],
[20190109094500, 5982., 5984., 5974., 5974.],
[20190109095000, 5974., 5984., 5972., 5982.],
[20190109095500, 5984., 5986., 5978., 5980.],
[20190109100000, 5982., 5990., 5978., 5990.],
[20190109100500, 5990., 5998., 5986., 5994.],
[20190109101000, 5994., 5998., 5986., 5988.],
[20190109101500, 5988., 5996., 5988., 5992.],
[20190109103500, 5990., 5990., 5976., 5980.],
[20190109104000, 5980., 5990., 5980., 5988.],
[20190109104500, 5990., 5994., 5986., 5994.],
[20190109105000, 5994., 6000., 5988., 5992.],
[20190109105500, 5992., 6014., 5990., 6012.],
[20190109110000, 6012., 6022., 6010., 6016.],
[20190109110500, 6014., 6026., 6010., 6016.],
[20190109111000, 6018., 6020., 6004., 6008.],
[20190109111500, 6008., 6012., 6004., 6010.],
[20190109112000, 6010., 6010., 6000., 6004.],
[20190109112500, 6004., 6008., 5998., 6006.],
[20190109113000, 6006., 6010., 6002., 6008.],
[20190109133500, 6012., 6018., 6006., 6014.],
[20190109134000, 6014., 6014., 6008., 6014.],
[20190109134500, 6018., 6018., 6008., 6010.],
[20190109135000, 6010., 6016., 6004., 6010.],
[20190109135500, 6010., 6014., 6008., 6008.],
[20190109140000, 6008., 6014., 6004., 6012.],
[20190109140500, 6014., 6016., 5982., 5992.],
[20190109141000, 5994., 5996., 5986., 5986.],
[20190109141500, 5988., 5998., 5986., 5992.],
[20190109142000, 5992., 6000., 5992., 5994.],
[20190109142500, 5992., 5998., 5988., 5994.],
[20190109143000, 5994., 6000., 5988., 5988.],
[20190109143500, 5990., 5992., 5976., 5982.],
[20190109144000, 5982., 5984., 5974., 5980.],
[20190109144500, 5980., 5986., 5976., 5984.],
[20190109145000, 5984., 5990., 5980., 5988.],
[20190109145500, 5990., 5992., 5984., 5988.],
[20190109150000, 5990., 5994., 5988., 5990.]]
import time
if __name__ == '__main__':


    T = Trend()
    # print(time.time())
    # RE_DataFrame = T.RemoveEmbodySeqMode_2DArray(test_data)
    # TimeTypeList = T.TypeAnalysis_2DArray(RE_DataFrame,True)
    # print(time.time())

    print(time.time())
    DataFrame = pandas.DataFrame(test_data)
    DataFrame.columns = ['date','open','high','low','close']
    # 基于缠论，标的数据去掉包含关系。
    RE_DataFrame = T.Candlestick_RemoveEmbodySeqMode(DataFrame)
    T.Candlestick_Drawing(RE_DataFrame)
    TimeTypeList = T.Candlestick_TypeAnalysis(RE_DataFrame,True)
    print(time.time())


    print (TimeTypeList)
