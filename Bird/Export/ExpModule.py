import xlwt
import datetime

from operator import itemgetter, attrgetter


'''
设置单元格样式
'''
def set_style(name,height,bold=False):
    style = xlwt.XFStyle()  # 初始化样式

    font = xlwt.Font()  # 为样式创建字体
    font.name = name # 'Times New Roman'
    #font.bold = bold
    font.color_index = 4
    font.height = height


    # borders= xlwt.Borders()
    # borders.left= 6
    # borders.right= 6
    # borders.top= 6
    # borders.bottom= 6

    style.font = font
    # style.borders = borders

    return style

# 输出板块信息
def exportXls_CategorysTrend(CateData, TimeRange, fileName = None):

    rowNum = 0
    colNum = 0
    
    f = xlwt.Workbook() #创建工作簿

    sheet1 = f.add_sheet(u'CategoryTrend', cell_overwrite_ok = True) #创建sheet

    # 生成第一行，以时段排列
    for i in range(len(TimeRange)-1):
        sheet1.write(rowNum,(i*2),TimeRange[i])
        sheet1.write(rowNum,(i*2+1),TimeRange[i+1])
    rowNum += 1

    # 以行生成数据
    for dictData in CateData:
        for key,value in dictData.items():
            for i in range(len(value)):
                sheet1.write(rowNum,(i*2),key)
                sheet1.write(rowNum,(i*2+1),value[i])
            rowNum += 1
    
    f.save('.\\Export\\demo1.xls') #保存文件

    # '''
    # 创建第一个sheet:
    # sheet1
    # '''
    # sheet1 = f.add_sheet(u'sheet1',cell_overwrite_ok=True) #创建sheet
    # row0 = [u'业务',u'状态',u'北京',u'上海',u'广州',u'深圳',u'状态小计',u'合计']
    # column0 = [u'机票',u'船票',u'火车票',u'汽车票',u'其它']
    # status = [u'预订',u'出票',u'退票',u'业务小计']

    # #生成第一行
    # for i in range(0,len(row0)):
    #     sheet1.write(0,i,row0[i],set_style('Times New Roman',220,True))

    # #生成第一列和最后一列(合并4行)
    # i, j = 1, 0
    # while i < 4*len(column0) and j < len(column0):
    #     sheet1.write_merge(i,i+3,0,0,column0[j],set_style('Arial',220,True)) #第一列
    #     sheet1.write_merge(i,i+3,7,7) #最后一列"合计"
    #     i += 4
    #     j += 1

    # sheet1.write_merge(21,21,0,1,u'合计',set_style('Times New Roman',220,True))

    # #生成第二列
    # i = 0
    # while i < 4*len(column0):
    #     for j in range(0,len(status)):
    #         sheet1.write(j+i+1,1,status[j])
    #     i += 4

    # f.save('demo1.xls') #保存文件

# 0|399300|20180926|1.000
def ExpTypingToTdx(TimeTypeList,CODE,ID,Expfile):
    f = open(Expfile, 'w')
    for i in range(len(TimeTypeList)):
        tTime = datetime.datetime.strptime(TimeTypeList[i][0], '%Y/%m/%d-%H:%M')
        tDate = tTime.strftime('%Y%m%d')
        tType = TimeTypeList[i][1]
        tStr = ID +'|' + CODE + '|' + tDate  + '|' + ('%.3f' % tType) + '\n'
        f.writelines(tStr)
    f.close

# xRangeNum 整合数据后 从后向前保留波段数。
def ExpPowerWave(PowerList, SortedRangeData, ExpFile, TotalRangeNum, RangeNum, SumFlag = ()):

    startRange = 0
    if (RangeNum < TotalRangeNum):
        startRange = TotalRangeNum - RangeNum

    SumNum = 0
    for i in range(len(SumFlag)):
        if SumFlag[i] == 1:
            SumNum += 1 

    ExpDict = {}
    for i in range(startRange, len(SortedRangeData)-SumNum):
        for j in range(len(SortedRangeData[i])):
            if SortedRangeData[i][j][0] in ExpDict:
                ExpDict[SortedRangeData[i][j][0]].append(PowerList[i][j])
            else:
                ExpDict[SortedRangeData[i][j][0]] = [PowerList[i][j]]

    f = open(ExpFile, 'w')
    for key, value in ExpDict.items():
        strData = ''
        for item in value:
            strData += str(item) + '->'
        f.writelines(key + ':' + strData[:-2] + '\n')
    f.close


# xRangeNum 整合数据后 从后向前保留波段数。
def ExpData2TXT(PowerList, ExpFile, SortedRangeData, RangeTime,RangeType,TotalRangeNum, xRangeNum = 1000):

    startRange = 0
    if (xRangeNum < TotalRangeNum):
        startRange = TotalRangeNum - xRangeNum
    
    f = open(ExpFile, 'w')

    # 写入时间戳
    strTime = ''
    for i in range(startRange, TotalRangeNum):
        strTime += RangeTime[i] + '\t' + RangeType[i] + '\t\t'
    strTime += '\n'
    f.writelines(strTime)

    # 写入数据
    for i in range(len(SortedRangeData[0])):
        strData = ''
        for j in range(startRange, TotalRangeNum):
            dList = SortedRangeData[j]
            strData += dList[i][0] + '\t'
            strData += str(dList[i][1]) + '\t'
            if PowerList != []:
                strData += str(PowerList[j][i]) + '\t'
            else:
                strData += '\t'
        strData += '\n'
        f.writelines(strData)
    f.close


# 0|399300|20180926|1.000
def FormatData2TXTForTDX(TimeTypeList,CODE,ID):
    f = open('.\\Export\\dataTdx.txt', 'w')
    for i in range(len(TimeTypeList)):
        tTime = datetime.datetime.strptime(TimeTypeList[i][0], '%Y/%m/%d-%H:%M')
        tDate = tTime.strftime('%Y%m%d')
        tType = TimeTypeList[i][1]
        tStr = CODE +'|' + ID + '|' + tDate  + '|' + ('%.3f' % tType) + '\n'
        f.writelines(tStr)
    f.close

# xRangeNum 整合数据后 从后向前保留波段数。
def FormatData2TXT(TimeTypeList,CateData,xRangeNum = 1000):
    timeFlagList = []   #存储波段时间戳，转换规则如下。最后一个时间戳 为无效值。 20180131-20180228, 转换后0131-0228。
    typeFlagList = []   #存储分型
    tIndex = 0
    for i in range(len(TimeTypeList)-1): 
        if (TimeTypeList[i+1][1] == 1):     # 顶分型
            cType = '+'
        elif (TimeTypeList[i+1][1] == -1):  # 底分型
            cType = '-'
        elif(TimeTypeList[i+1][1] == 0):    # 无分型 一般为数据开始或结束波段
            cType = '*'
        elif(TimeTypeList[i+1][1] == 2):    # 无分型 数据起始日至第一个波段涨跌幅度
            cType = '#1'
        elif(TimeTypeList[i+1][1] == 3):    # 无分型 当前所有波段涨跌幅度
            cType = '#2'
        else:
            cType = 'Error'
        typeFlagList.append(cType)

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

        timeFlagList.append(str((T_std1.year % 100)* 10000 + T_std1.month * 100 + T_std1.day) + '-' 
        + str((T_std2.year % 100) * 10000 +T_std2.month * 100 + T_std2.day))

    rangeNum = len(TimeTypeList) - 1
    startRange = 0
    if (xRangeNum < rangeNum):
        startRange = rangeNum - xRangeNum
    
    # 以波段为基础，整合板块数据，降序排列
    AllData = []
    for i in range(len(timeFlagList)):
        rDataList = []
        for dictData in CateData:
            for key,value in dictData.items(): 
                rDataList.append((key,value[i]))
        rDataList = sorted(rDataList, key = itemgetter(1), reverse = True)
        AllData.append(rDataList)

    fileFolder = '.\\Export\\'
    cTime = datetime.datetime.now().strftime('%Y%m%d%H%M')
    fileName = 'data' + cTime +'.txt'
    filePath = fileFolder + fileName
    
    f = open(filePath, 'w')

    # 写入时间戳
    strTime = ''
    for i in range(startRange, rangeNum):
        strTime += timeFlagList[i] + '\t' + typeFlagList[i] + '\t\t'
    strTime += '\n'
    f.writelines(strTime)

    # 写入数据
    for i in range(len(CateData)):
        strData = ''
        for j in range(startRange, rangeNum):
            dList = AllData[j]
            strData += dList[i][0] + '\t'
            strData += str(dList[i][1]) + '\t\t'
        strData += '\n'    
        f.writelines(strData)
    f.close


if __name__ == '__main__':

    time = [['2018/06/07-00:00',0],['2018/07/06-00:00',1],['2018/07/24-00:00',-1],['2018/08/20-00:00',1],['2018/09/04-00:00',-1],['2018/09/13-00:00',1],['2018/09/26-00:00',-1],['2018/10/19-00:00',1],['2018/11/02-00:00',-1],['2018/11/12-00:00',1],['2018/11/19-00:00',-1],['2018/11/27-00:00',1],['2018/12/03-00:00',-1],['2018/12/10-00:00',0]]  
    data = [{'煤炭': [-9.82, 4.96, -0.86, 3.08, -0.06, 7.16, -3.95, 6.71, 0.01, 0.69, -6.46, 2.03, 1.15]},
            {'电力': [-7.95, 6.1, -3.83, 1.76, 0.25, 2.74, -8.65, 5.59, 1.51, 4.51, -3.87, 2.93, 1.12]},
            {'石油': [-6.04, 2.73, 6.08,4.85, 4.67, 8.82, -6.19, 0.22, -0.66, -1.1, -4.25, 2.67, 0.35]},
            {'钢铁': [-9.16, 12.64, 1.62, -2.27, -5.21, 5.05, -7.76, 7.62, -0.09, 2.33, -9.05, 0.32, 1.5]},
            {'有色': [-15.18, 7.22, -10.28, 0.43, -2.51, 4.75, -14.6, 11.99, 1.66, 4.63, -6.15, 4.97, 0.86]},
            {'化纤': [-13.31, 13.59, 1.88, 1.7, -4.48, 4.45, -16.18, 10.27, 3.2, 3.99, -6.15, 4.79, 1.92]},
            {'化工': [-12.83, 8.43, -8.02, 0.3, -3.26, 3.52, -13.05, 6.34, 3.24, 5.08, -6.24, 4.43, 1.55]},
            {'建材': [-15.61, 18.82, -2.78, 2.18, -7.25, 6.76, -10.87, 8.74, 2.76, 7.28, -3.12, 2.53, 0.85]},
            {'造纸': [-15.31, 3.79, -6.12, 2.6, -3.48, 1.3, -15.91, 9.23, 10.61, 8.11, -6.61, 3.23, 0.89]},
            {'矿物制品': [-19.08, 12.56, -11.79, 0.47, -0.98, 4.03, -16.6, 13.68, 8.81, 11.69, -6.6, 3.83, -1.24]},
            {'日用化工': [-19.02, 4.67, -13.47, -5.83, -7.31, 2.14, -12.92, 9.87, 5.36, 7.44, -4.29, 4.18, 1.88]},
            {'农林牧渔': [-14.41, 8.23, -8.45, 1.7, -1.04, 2.76, -9.97, 8.91, 5.38, 5.92, -4.03, 5.7, 2.74]},
            {'纺织服饰': [-15.95, 4.63, -9.25, 0.24, -1.87, 1.26, -12.66, 6.18, 3.96, 7.48, -5.12, 3.19, 0.91]},
            {'食品饮料': [-12.64, 5.16, -8.83, 1.72, -1.02, 10.12, -5.36, 0.78, 3.93, 3.15, -3.71, 5.54, 0.7]},
            {'酿酒': [-10.55, 6.58, -13.76, 4.73, -5.24, 14.28, -6.69, -6.1, -0.48, 2.5, -2.6, 8.99, 1.51]},
            {'家用电器': [-12.52, 4.48, -12.1, 1.47, -2.83, 4.84, -5.92, 5.24, 3.36, 5.14, -4.36, 2.9, -2.42]},
            {'汽车类': [-10.97, 3.76, -9.31, 1.4, -1.89, 6.82, -12.91, 5.84, 3.62, 3.23, -3.97, 3.37, -0.49]},
            {'医疗保健': [-12.76, 4.55, -14.91, 3.98, -4.25, 2.22, -12.32, 13.84, 6.89, 4.84, -2.36, 4.93, -1.93]},
            {'家居用品': [-20.16, 4.03, -12.56, -0.25, -6.0, 2.34, -17.32, 9.52, 5.68, 9.1, -8.41, 4.03, -0.65]},
            {'医药': [-13.21, 2.04, -11.17, 1.97, -4.73, 1.74, -11.22, 9.12, 4.51, 3.47, -2.48, 3.83,-4.5]},
            {'商业连锁': [-18.29, 7.41, -10.12, 2.12, -3.35, 3.27, -11.0, 8.89, 3.72, 5.46, -4.6, 2.25, -0.96]},
            {'商贸代理': [-16.76, 8.54, -5.39, 0.92, -0.79, 4.82, -17.19, 12.64, 6.18, 10.2, -5.19, 2.23, -0.68]},
            {'传媒娱乐': [-12.16, 1.08, -11.65, 0.29, -1.68, 2.22, -11.62, 8.74, -0.2, 10.1, -5.06, 3.28, 1.72]},
            {'广告包装': [-13.55, 5.02, -5.08, 2.72, -0.38, 2.31, -12.71, 8.69, 7.57, 7.24, -4.88, 1.66, 1.04]},
            {'文教休闲': [-15.76, 5.97, -4.38, 0.31, -2.59, 2.1, -15.76, 9.33, 6.81, 6.05, -3.67, 2.97, 0.61]},
            {'酒店餐饮': [-14.14, 6.2, -17.36, 0.44, -0.94, 6.91, -15.82, 15.51, 4.33, 6.45, -7.07, 5.76, 0.85]},
            {'旅游': [-10.73, 9.15, -12.19, 3.33, -3.11, 8.42, -16.77, 11.14, 4.57, 3.05, -4.1, 4.45, 1.4]},
            {'航空': [-5.86, 7.43, -11.52, 11.06, 5.69, -0.76, -13.8, 10.35, 1.21, 6.16, -3.17, 2.9, -2.45]},
            {'船舶': [-16.25, 9.24, -2.8, 3.6, 2.01, 2.32, -9.08, 6.31,2.63, 4.42, -0.16, 4.78, -1.16]},
            {'运输设备': [-16.7, 11.04, -0.55, 2.33, 0.36, 5.77, -7.74, 8.32, 0.33, 2.72, -1.82, 3.18, 4.12]},
            {'通用机械': [-15.89, 6.62, -11.1, -0.65, -1.15, 4.52, -14.83, 10.03, 6.82, 8.19, -3.62, 4.44, 1.3]},
            {'工业机械': [-15.26, 7.47, -7.19, 1.43, 0.08, 2.34, -15.3, 10.24, 6.05, 6.43, -4.43, 3.97, 0.91]},
            {'电气设备': [-12.87, 7.26, -9.11, 1.03, 1.3, 3.35, -11.81, 9.81, 5.42, 7.11, -4.96, 4.51, 0.04]},
            {'工程机械': [-9.77, 7.93, 0.79, 1.84, -3.22, 3.38, -12.07, 6.54, 3.94, 4.85, -4.81, 3.71, 1.16]},
            {'电器仪表': [-16.64, 8.22, -12.5, 2.99, -6.67, 6.74, -15.92, 11.32, 8.34, 9.93, -8.5, 7.95, -0.51]},
            {'电信运营': [-12.33, 10.54, 4.35, 1.11, -0.35, 1.97, -12.49, 10.83, 3.35, 5.81, -6.44, 4.81, -1.17]},
            {'公共交通': [-15.08, 6.57, -5.72, 0.22, -0.07, 3.59, -13.94, 10.86, 4.41, 12.03, -3.21, 0.42, -0.92]},
            {'水务': [-12.52, 7.06, -5.66, 1.63, -0.7, 2.99, -10.91, 9.15, 5.2, 7.27, -4.44, 1.24, 0.63]},
            {'供气供热': [-17.68, 9.87, -5.5, -1.47, 6.08, 8.15, -10.13, 4.37, 7.98, 8.58, -5.27, -0.93, 3.47]},
            {'环境保护': [-15.22, 4.11, -11.02, -2.55, -1.76, 1.39, -18.73, 13.05, 7.9, 10.08, -6.1, 2.78, 0.87]},
            {'运输服务': [-15.71, 0.11, -7.57, 0.95, -3.45, 6.26, -11.8, 13.72, 2.73, 4.53, -4.27, 4.04, 0.27]},
            {'仓储物流': [-18.37, 5.91, -10.36, -1.48, 0.51, 7.52, -12.71, 6.77, 1.66, 6.77, -4.68, 0.22, -2.61]},
            {'交通设施': [-12.56, 5.29, -4.92, 0.17, -1.95, 4.78, -6.64, 8.18, 1.68, 6.71, -4.84, 2.21, -0.87]},
            {'银行': [-7.42, 8.94, -2.79, 5.01, -0.82, 7.11, -1.79, 6.64, -2.76, 1.31, -1.15, 1.85, -0.59]},
            {'证券': [-11.7, 6.11, -5.14, 2.61, -1.46, 4.35, -11.62, 25.6, 0.47, 11.82, -5.66, 4.07, -1.13]},
            {'保险': [-8.27, 10.19, -5.81, 8.38, -1.7, 10.39, -1.63, 8.68, -0.01, 2.37, -4.17, 3.0, -2.39]},
            {'多元金融': [-10.33, 0.97, -7.39, -1.35, -0.37, 2.55, -11.22, 14.88, 2.43, 10.85, -7.78, 1.7, -2.81]},
            {'建筑': [-10.47, 12.56, -0.38, -0.98, -1.92, 4.64, -8.57, 7.76, 0.77, 5.88, -3.13, 2.57, 1.55]},
            {'房地产': [-14.96, 6.75, -4.46, 4.89, -1.76, 3.44, -14.03, 14.65, 2.56, 11.62, -3.16, 0.51, -1.66]},
            {'IT设备': [-10.76, 13.33, -6.47, 5.53, -2.2, 0.15, -14.22, 10.39, 5.83, 7.27, -7.13, 3.2, -1.92]},
            {'通信设备': [-19.23, 10.39, -4.84, 3.27, 0.38, 1.95, -14.66, 10.57, 8.26, 6.19, -3.79, 5.12, 1.07]},
            {'半导体': [-9.04, 9.18, -12.37, 1.07, -5.96, 1.9, -14.68, 12.22, 8.38, 7.89, -6.06, 5.65, 1.82]},
            {'元器件': [-13.21, 11.58, -10.29, 2.71, -3.26, 1.34, -13.18, 11.82, 3.71, 6.49, -7.25, 5.13, -0.47]},
            {'软件服务': [-11.18, 6.89, -5.95, 6.34, -2.0, 1.06, -13.63, 11.38, 5.5, 8.22, -6.56, 3.17, 0.46]},
            {'互联网': [-12.27, 3.51, -10.13, 4.89, -3.54, 1.15, -11.94, 15.4, 5.98, 10.76, -7.65, 3.48, 0.14]},
            {'综合类': [-14.16, 3.63, -6.09, -3.42, -2.93, 1.93, -17.86, 11.09, 10.21, 10.84, -7.45, 3.72, -1.36]}]

    #exportXls_CategorysTrend(data,time)
    #FormatData2TXT(time,data)
    FormatData2TXT(time,data,12)

