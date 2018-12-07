# -*- coding: utf-8 -*-

import numpy
import pandas
import matplotlib
import mpl_finance as mpf
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.ticker import Formatter
#import datetime

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
    def Candlestick_TypeAnalysis(self, kData):
        
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
                        continue
                    elif i + 1 < preIndex + 4: #不满足结合律
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
                        i += 1
                        continue
                    elif i + 1 < preIndex + 4: #不满足结合律
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

        return typeDict

    
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


if __name__ == '__main__':

    Tdx = TdxData.TdxDataEngine(r'.\StockData')
    filePath = Tdx.GetTdxFileList()
    filePath = Tdx.SearchInFileList("SZ", "399300", filePath)
    tData = Tdx.HandlerTdxDataToDataFrame(filePath)

    #print(tData)

    #asd = pandas.DataFrame([["2018/08/27-09:35",10.33 , 10.35 , 10.27 , 10.31 , 2151100.0  ,22191502.0]])
    #asd.columns =  ['date','open','high','low','close','volume','Turnover']

    T = Trend()
    #result = T.Candlestick_RemoveEmbodySetMode(tData)
    result = T.Candlestick_RemoveEmbodySeqMode(tData)
    #print(result)

    # f1 = open(r'C:\Users\LL\Desktop\1.txt','w')
    # f2 = open(r'C:\Users\LL\Desktop\2.txt','w')
    # for i in range(len(tData)):
    #     temp1 = tData[i:i+1]
    #     print(temp1,file = f1)
    # print(len(tData))
    # for i in range(len(result)):
    #     temp1 = result[i:i+1]
    #     print(temp1,file = f2)
    # print(len(result))
    # f1.close()
    # f2.close()

    # # k线
    # T.Candlestick_Drawing(result)

    # 分析分型
    typeDict = T.Candlestick_TypeAnalysis(result)
    #print(typeDict)

    # 输出分型
    for key, value in typeDict.items():
        i = 0
        for index, row in result.iterrows():
            if i == value[0]:
                print(row['date'])
                break
            i = i + 1

    print("Done")