from Export import ExpModule
from Stock import TrendAnalyzer
from DataBase import TdxData

def main():
    startTime = '2018/01/01-00:00'  # 数据开始波段
    endTime = '2018/12/18-00:00'    # 数据结束波段
    DataPath = r'.\StockData'       # 数据路径
    ID_ZS_CODE = '0'                # 标的指数，沪 = 1； 深 = 0
    ID_ZS_SH = '399300'             # 标的指数，以此划分波段
    NAME_ZS_SH = '沪深300'          # 标的指数名称
    ID_BK = 'Categorys'             # 分析目标数据文件夹名
    RangeNum = 8                    # 输出波段数                 

    # 获取数据
    Tdx = TdxData.TdxDataEngine(DataPath)
    filePath = Tdx.GetTdxFileList()
    File_SH = Tdx.SearchInFileList(filePath,'',ID_ZS_SH)
    File_BK = Tdx.SearchInFileList(filePath,ID_BK, '')
    Data_SH = Tdx.HandlerTdxDataToList(File_SH,startTime,endTime)
    Data_BK = Tdx.HandlerTdxDataToList(File_BK,startTime,endTime)

    # 分析数据
    T = TrendAnalyzer.Trend()
    tData = T.StockDataList2DataFrame(Data_SH[0][NAME_ZS_SH])
    tData_RE = T.Candlestick_RemoveEmbodySeqMode(tData)

    # # k线
    # T.Candlestick_Drawing(tData_RE)

    # 分析分型， 返回分型 顶底时间列表, 返回结果为2维数组
    typeTimeList = T.Candlestick_TypeAnalysis(tData_RE,True)
    ExpModule.FormatData2TXTForTDX(typeTimeList,ID_ZS_CODE,ID_ZS_SH)   # 分型处理后，把结果输出到txt，导入tdx 显示分型标识

    listRange = T.calcPriceRange(Data_BK, typeTimeList)     # 按时间轴，计算数据波段涨幅
    RangeNum = T.calcPriceXRange(listRange, typeTimeList,RangeNum)     # 按时间轴，计算数据波段涨幅,  结果会存储在 listRange 和 typeTimeList，添加1-2组数据。

    #ExpModule.FormatData2TXT(typeTimeList,listRange)        # 波段涨幅，降序，输出到Data.txt 导入 excel 模板，分析使用
    ExpModule.FormatData2TXT(typeTimeList,listRange,RangeNum)        # 波段涨幅，降序，输出到Data.txt 导入 excel 模板，分析使用
    
if __name__ == '__main__':
    main()