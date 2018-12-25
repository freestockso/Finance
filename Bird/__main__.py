import sys
import datetime
import json
import pickle

from Export import ExpModule
from Stock import TrendAnalyzer
from DataBase import TdxData
from Logger import Log

def BatchProcessing(f_JSON, NeedToTyping = True):
    CMD_TYPING = 'cmd_typing'     # 批量处理数据分型
    CMD_DATA = 'cmd_data'       # 批量处理数据分析，需以分型为基础。
    ExpPath = ".//Export//"             # 输出文件路径
    # 创建分析对象
    T = TrendAnalyzer.Trend()

    with open(f_JSON, "r", encoding='utf-8') as f:
        BatCMD = json.load(f)
    
    if NeedToTyping == True:
        CmdList = BatCMD[CMD_TYPING]
        for cmd in CmdList:
            StoreData = []                      # 把当前数据存储到硬盘上
            StartTime = cmd["StartTime"]        # 数据时间范围，起始时间
            EndTime = cmd["EndTime"]            # 数据时间范围，终止时间，None 表示当前时间
            DataPath = cmd["DataPath"]          # 标的数据路径
            TRADE_CODE = cmd['TRADE_CODE']      # 标的数据交易所代码，沪 = 1； 深 = 0
            ID_CODE = cmd['ID_CODE']            # 标的数据代码
            ID_NAME = cmd['ID_NAME']            # 标的数据名称

            FidData = ExpPath + "Typing" + ID_CODE + '.txt'     # 给通达信分型显示使用的数据
            FidPKL = ExpPath + "Typing" + ID_CODE + '.pkl'      # 存储分型结果和数据列表
            
            if EndTime == "None":
                EndTime = datetime.datetime.now().strftime('%Y/%m/%d-%H:%M')
            # 数据源初始化
            DataBase = TdxData.TdxDataEngine(DataPath)
            # 获取当前路径下所有文件路径列表
            FilePathList = DataBase.GetTdxFileList()
            # 获取标的数据文件路径
            FilePath = DataBase.SearchInFileList(FilePathList,'',ID_CODE)
            # 在标的数据文件中获取数据,[{key1:[[data1],[data2],[datan]]},{key2:[[data1],[data2],[datan]]}]
            DataList = DataBase.HandlerTdxDataToList(FilePath,StartTime, EndTime)
            # 分析标的数据，将2维数组转化成dataframe
            DataFrame = T.StockDataList2DataFrame(DataList[0][ID_NAME])
            # 基于缠论，标的数据去掉包含关系。
            RE_DataFrame = T.Candlestick_RemoveEmbodySeqMode(DataFrame)
            # 基于缠论分析标的数据顶底分型， 返回分型 顶底时间列表, 返回结果为2维数组
            TimeTypeList = T.Candlestick_TypeAnalysis(RE_DataFrame,True)
            # 分型处理后，把结果输出到txt，导入tdx 显示分型标识
            ExpModule.ExpTypingToTdx(TimeTypeList,ID_CODE,TRADE_CODE,FidData)
            # 将时间波段分型结果 和 数据列表 输出到文件中。
            StoreData.append(TimeTypeList)
            StoreData.append(DataList)
            f = open(FidPKL,'wb')
            pickle.dump(StoreData,f)
            f.close()

    # 数据波段输出
    CmdList = BatCMD[CMD_DATA]
    for cmd in CmdList:
        StartTime = cmd["StartTime"]        # 数据时间范围，起始时间
        EndTime = cmd["EndTime"]            # 数据时间范围，终止时间，None 表示当前时间
        DataPath = cmd["DataPath"]          # 标的数据路径
        ID_CODE = cmd['ID_CODE']            # 标的数据代码
        RangeNum = cmd['RangeNum']          # 波段数
    
        # 获取指定标的，分型数据及数据列表
        FidPKL = ExpPath + "Typing" + ID_CODE + '.pkl'      # 存储分型结果和数据列表
        f = open(FidPKL,'rb')
        TypingData = pickle.load(f)
        f.close()

        cTimeTypeList = T.cutTimeRange(typeTimeList,startTime,endTime)
        # 数据源初始化
        Tdx = TdxData.TdxDataEngine(DataPath)
        filePath = Tdx.GetTdxFileList()
        # 获取指标数据，当前获取板块指标数据
        File_BK = Tdx.SearchInFileList(filePath,ID_BK, '')
        Data_BK = Tdx.HandlerTdxDataToList(File_BK,cTimeTypeList[0][0],cTimeTypeList[-1][0])


    
    

def main():
    startTime = '2018/06/07-00:00'  # 数据开始波段
    endTime = '2018/12/25-00:00'    # 数据结束波段
    DataPath = r'.\StockData'       # 数据路径
    ID_ZS_CODE = '0'                # 标的指数，沪 = 1； 深 = 0
    ID_ZS_SH = '399300'             # 标的指数，以此划分波段
    NAME_ZS_SH = '沪深300'          # 标的指数名称
    ID_BK = 'Categorys'             # 分析目标数据文件夹名
    RangeNum = 8                    # 输出波段数
    NeedToTyping = False            # 需不需要做分型统计

    if endTime == None:
        endTime = datetime.datetime.now().strftime('%Y/%m/%d-%H:%M')

    # 数据源初始化
    Tdx = TdxData.TdxDataEngine(DataPath)
    filePath = Tdx.GetTdxFileList()
    # 获取标的数据，以此为基础分型。
    File_SH = Tdx.SearchInFileList(filePath,'',ID_ZS_SH)
    # 数据起始时间为2000年，结束时间为当前最新时间。
    Data_SH = Tdx.HandlerTdxDataToList(File_SH,'2000/01/01-00:00', datetime.datetime.now().strftime('%Y/%m/%d-%H:%M'))
    # 创建分析对象
    T = TrendAnalyzer.Trend()

    if NeedToTyping == True:
        # 分析标的数据，将2维数组转化成dataframe
        tData = T.StockDataList2DataFrame(Data_SH[0][NAME_ZS_SH])
        # 基于缠论，标的数据去掉包含关系。
        tData_RE = T.Candlestick_RemoveEmbodySeqMode(tData)
        # k线，去掉包含关系后K线显示。
        # T.Candlestick_Drawing(tData_RE)
        # 基于缠论分析标的数据顶底分型， 返回分型 顶底时间列表, 返回结果为2维数组
        typeTimeList = T.Candlestick_TypeAnalysis(tData_RE,True)
        # 分型处理后，把结果输出到txt，导入tdx 显示分型标识
        ExpModule.FormatData2TXTForTDX(typeTimeList,ID_ZS_CODE,ID_ZS_SH)

        # 将分型和时间结果输出到文件中。
        f = open(r'./Export/type&time.pkl','wb')
        pickle.dump(typeTimeList,f)
        f.close()
    else:
        # 从pkl文件中，获取分型和时间结果
        try:
            f = open(r'./Export/type&time.pkl','rb')
            typeTimeList = pickle.load(f)
            f.close()
        except Exception as e:
            print("Error: 未读取到分型数据，程序停止")
            sys.exit()

    cTimeTypeList = T.cutTimeRange(typeTimeList,startTime,endTime)

    # 获取指标数据，当前获取板块指标数据
    File_BK = Tdx.SearchInFileList(filePath,ID_BK, '')
    Data_BK = Tdx.HandlerTdxDataToList(File_BK,cTimeTypeList[0][0],cTimeTypeList[-1][0])

    # 在板块数据中加入标的数据。
    Data_BK += Data_SH

    # 基于标的数据分型后的时间段，计算数据波段涨幅
    listRange = T.calcPriceRange(Data_BK, cTimeTypeList)
    # 按时间轴，增加数据波段统计涨幅,  结果会存储在 listRange 和 typeTimeList，添加1-2组数据。
    RangeNum = T.calcPriceXRange(listRange, cTimeTypeList, RangeNum, Data_BK)
    # 波段涨幅，降序，输出到Data.txt 导入 excel 模板，分析使用
    ExpModule.FormatData2TXT(cTimeTypeList,listRange,RangeNum)

    print('Done')

def exportPriceRangeByNaturalTime(sTime, eTime):

    DataPath = r'.\StockData'       # 数据路径
    ID_BK = 'Categorys'             # 分析目标数据文件夹名

    # 数据源初始化
    Tdx = TdxData.TdxDataEngine(DataPath)
    filePath = Tdx.GetTdxFileList()
    # 创建时间&分型列表
    cTimeTypeList = []
    cTimeTypeList.append([sTime,0])
    cTimeTypeList.append([eTime,0])
    # 创建分析对象
    T = TrendAnalyzer.Trend()
    # 获取指标数据，当前获取板块指标数据
    File_BK = Tdx.SearchInFileList(filePath,ID_BK, '')
    # 获取数据的时间前推5天
    tTime = datetime.datetime.strptime(cTimeTypeList[0][0], '%Y/%m/%d-%H:%M')
    tTime = (tTime + datetime.timedelta(days=-5)).strftime('%Y/%m/%d-%H:%M')
    Data_BK = Tdx.HandlerTdxDataToList(File_BK,tTime,cTimeTypeList[-1][0])
    # 基于标的数据分型后的时间段，计算数据波段涨幅
    listRange = T.calcPriceRange(Data_BK, cTimeTypeList)
    # 波段涨幅，降序，输出到Data.txt 导入 excel 模板，分析使用
    ExpModule.FormatData2TXT(cTimeTypeList,listRange)

    
if __name__ == '__main__':
    # main()
    # exportPriceRangeByNaturalTime('2018/12/24-00:00','2018/12/24-00:00')
    BatchProcessing(".//BAT.json")