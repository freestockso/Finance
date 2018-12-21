import sys
import datetime
import pickle

from Export import ExpModule
from Stock import TrendAnalyzer
from DataBase import TdxData
from Logger import Log

def main():
    startTime = '2018/01/01-00:00'  # 数据开始波段
    # endTime = '2018/12/19-00:00'    # 数据结束波段
    endTime = None               # 数据结束波段
    DataPath = r'.\StockData'       # 数据路径
    ID_ZS_CODE = '0'                # 标的指数，沪 = 1； 深 = 0
    ID_ZS_SH = '399300'             # 标的指数，以此划分波段
    NAME_ZS_SH = '沪深300'          # 标的指数名称
    ID_BK = 'Categorys'             # 分析目标数据文件夹名
    RangeNum = 50                    # 输出波段数
    NeedToTyping = False            # 需不需要做分型统计

    if endTime == None:
        endTime = datetime.datetime.now().strftime('%Y/%m/%d-%H:%M')

    # 数据源初始化
    Tdx = TdxData.TdxDataEngine(DataPath)
    filePath = Tdx.GetTdxFileList()
    # 创建分析对象
    T = TrendAnalyzer.Trend()

    if NeedToTyping == True:
        # 获取标的数据，以此为基础分型。
        File_SH = Tdx.SearchInFileList(filePath,'',ID_ZS_SH)
        # 数据起始时间为2000年，结束时间为当前最新时间。
        Data_SH = Tdx.HandlerTdxDataToList(File_SH,'2000/01/01-00:00', datetime.datetime.now().strftime('%Y/%m/%d-%H:%M'))
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

    print(typeTimeList)
    sys.exit()

    # 获取指标数据，当前获取板块指标数据
    File_BK = Tdx.SearchInFileList(filePath,ID_BK, '')
    Data_BK = Tdx.HandlerTdxDataToList(File_BK,startTime,endTime)

    # 基于标的数据分型后的时间段，计算数据波段涨幅
    listRange = T.calcPriceRange(Data_BK, typeTimeList)
    # 按时间轴，增加数据波段统计涨幅,  结果会存储在 listRange 和 typeTimeList，添加1-2组数据。
    RangeNum = T.calcPriceXRange(listRange, typeTimeList, RangeNum, Data_BK)
    # 波段涨幅，降序，输出到Data.txt 导入 excel 模板，分析使用
    ExpModule.FormatData2TXT(typeTimeList,listRange,RangeNum)

    print('Done')
    
if __name__ == '__main__':
    main()