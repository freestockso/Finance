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
    def Candlestick_MergeData(self, kData, Index, Count):

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
    def Candlestick_RemoveEmbody(self, kData):
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
                    tData = self.Candlestick_MergeData(kData, (i + 1 - CurCount), CurCount)
                    CurCount = 1
                # 在当前数据不存在包含关系时，CurCount = 1，直接存储    
                else:    
                    tData = CurData    
                CurData = NextData
                rkData = pandas.concat([rkData,tData],axis = 0)
        
        return rkData
    
    # 在去掉包含关系后，进行分型处理：顶分型或底分型
    # 在去掉包含关系后，k线转向必有一个顶分型和一个底分型
    def Candlestick_TypeAnalysis(self, kData):
        
        typeDict = {}
        i = 0
        index = 0
        # 基于结合律,查询所有分型，存在dict里, key is index, start by 0
        while i < (len(kData)-2):
            Data1 = kData[i:(i+1)]
            Data2 = kData[(i+1):(i+2)]
            if i == len(kData) - 2: 
                Data3 = kData[(i+2):-1]
            else:
                Data3 = kData[(i+2):(i+3)]

            if (Data2.iloc[-1].high > Data1.iloc[-1].high and Data2.iloc[-1].high > Data3.iloc[-1].high and
                Data2.iloc[-1].low > Data1.iloc[-1].low and Data2.iloc[-1].low > Data3.iloc[-1].low
                ):
                typeDict[index] = [i+1,'G']
                i = i + 4   # 3个K线 + 1个associative结合律
                index = index + 1
            elif (Data2.iloc[-1].high < Data1.iloc[-1].high and Data2.iloc[-1].high < Data3.iloc[-1].high and
                Data2.iloc[-1].low < Data1.iloc[-1].low and Data2.iloc[-1].low < Data3.iloc[-1].low
                ):
                typeDict[index] = [i+1,'D']
                i = i + 4   # 3个K线 + 1个associative结合律
                index = index + 1

            i = i + 1
        
        print(typeDict)

        #合并分型
        i = 1 #start by 2nd
        l = len(typeDict)
        preKey = 0 # 记录数据的key值
        preType = typeDict[i-1][1]
        preData = kData[typeDict[i-1][0]:(typeDict[i-1][0]+1)]

        while i < l:
            curKey = i #当前数据的key值
            curType = typeDict[i][1]
            curData = kData[typeDict[i][0]:(typeDict[i][0]+1)]
            if preType == curType: #同分型，比较高低
                if curType == 'G': #顶分型，比高，删除低点
                    if preData.iloc[-1].high < curData.iloc[-1].high:
                        typeDict.pop(preKey)
                        preKey = curKey
                        preType = curType
                        preData = curData
                    else:
                        typeDict.pop(curKey)
                elif curType == 'D':#低分型，比低，删除高点
                    if preData.iloc[-1].low > curData.iloc[-1].low:
                        typeDict.pop(preKey)
                        preKey = curKey
                        preType = curType
                        preData = curData
                    else:
                        typeDict.pop(curKey)
            elif preType != curType: #不同分型
                preKey = curKey
                preType = curType
                preData = curData

            i = i + 1

        print(typeDict)

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

    Tdx = TdxData.TdxDataEngine(r'F:\StockData')
    filePath = Tdx.GetTdxFileList()
    filePath = Tdx.SearchInFileList("SZ", "399300", filePath)
    tData = Tdx.HandlerTdxDataToDataFrame(filePath)

    #print(tData)

    #asd = pandas.DataFrame([["2018/08/27-09:35",10.33 , 10.35 , 10.27 , 10.31 , 2151100.0  ,22191502.0]])
    #asd.columns =  ['date','open','high','low','close','volume','Turnover']

    T = Trend()
    result = T.Candlestick_RemoveEmbody(tData)

    # f1 = open(r'C:\Users\wenbwang\Desktop\1.txt','w')
    # f2 = open(r'C:\Users\wenbwang\Desktop\2.txt','w')
    # for i in range(len(tData)-1):
    #     temp1 = tData[i:i+1]
    #     print(temp1,file = f1)
    # print(tData[i:-1],file = f1)
    # print(len(tData))
    # for i in range(len(result)-1):
    #     temp1 = result[i:i+1]
    #     print(temp1,file = f2)
    # print(result[i:-1],file = f2)
    # print(len(result))
    # f1.close()
    # f2.close()

    #T.Candlestick_Drawing(result)  # k线
    typeDict = T.Candlestick_TypeAnalysis(result)

    # for index, row in result.iterrows():
    #     print(row['date'])

    for key, value in typeDict.items():
        i = 0
        for index, row in result.iterrows():
            if i == value[0]:
                print(row['date'])
                break
            i = i + 1

    print("Done")