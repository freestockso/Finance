import numpy
import pandas
import copy
 
# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # context内引入全局变量s1
    
    context.bird = GenObj()
    
    bird = context.bird

    bird.Timer = 0              # 每天计时器

    # 品种列表
    bird.TypesList = [   
        {
            'Type' : 'J',           # 品种名
            'TypeIndex' : 'J99',    # 品种指数
            'BuyStop' : 0,          # 买入止损点
            'SellStop' : 0,         # 卖出止损点
            'Amount' : 2,           # 总仓位
            'Highest' : 0,          # 历史最高价
            'Lowest' : 0,           # 历史最低价
        }
    ]

    # 品种列表，对应的合约号
    bird.ContractList = []
    
    # 策略参数
    bird.StgyParam = {
        'Stgy_2B_Buy1' : {
            'BarNum' : 200,         # 200根k线分型处理
            'BarFreq' : '5m',       # K线频率，ex： '5m' 5分钟
            'AnaFreq' : 10         # 分析频率，ex： 10， 每10分钟分析策略
        },

        'Stgy_2B_Sell1' : {
            'BarNum' : 200,         # 200根k线分型处理
            'BarFreq' : '5m',       # K线频率，ex： '5m' 5分钟
            'AnaFreq' : 10         # 分析频率，ex： 10， 每10分钟分析策略
        }
    }

    bird.T = Trend()
    bird.S = Strategy()
    
    # 注册合约行情
    GetContractName(context, bird)
    for s in bird.ContractList:
        # 初始化时订阅合约行情。订阅之后的合约行情会在handle_tick中进行更新。
        subscribe(s)

    # 注册品种指数行情
    for item in bird.TypesList:
        subscribe(item['TypeIndex'])
 
    # 实时打印日志
    logger.info("RunInfo: {}".format(context.run_info))

# 获取合约列表
def GetContractName(context, bird):
    
    bird.ContractList = []

    for item in bird.TypesList:
        # checking the existing contracts
        Type = item['Type']
        Contracts = get_dominant_future(Type)
        for OrderID, Val in context.portfolio.positions.items():
            IDstr = OrderID
            for i in range(10):
                IDstr = IDstr.replace(str(i),'')
            # 仓内有 当前合约
            if Type == IDstr:
                Contracts = OrderID
            else:
                Contracts = get_dominant_future(Type)
            
        bird.ContractList.append(Contracts)
    
# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    bird = context.bird
    
    GetContractName(context, bird)

    # 注册合约行情
    for s in bird.ContractList:
        # 初始化时订阅合约行情。订阅之后的合约行情会在handle_tick中进行更新。
        subscribe(s)

    # 注册品种指数行情
    for item in bird.TypesList:
        subscribe(item['TypeIndex'])

        BarData = history_bars(item['TypeIndex'], 200, '1d', ['high','low'])

        HighList = [x[0] for x in BarData]
        LowList = [x[1] for x in BarData]
        item['Highest'] = max(HighList)
        item['Lowest'] = min(LowList)

# 你选择的期货数据更新将会触发此段逻辑
def handle_bar(context, bar_dict):
    bird = context.bird

    bird.S.Stgy_2B_Buy1(bird, context, bar_dict)
    bird.S.Stgy_2B_Sell1(bird, context, bar_dict)
    
# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    pass

class Strategy(object):
    def __init__(self):
        self.DataType = ['datetime','open','high','low','close']
        self.open = 1
        self.high = 2
        self.low = 3
        self.close = 4

        self.BUY = 1
        self.SELL = -1

    def Stgy_2B_Buy1(self, bird, context, bar_dict):

        # 当前策略参数
        SP = bird.StgyParam['Stgy_2B_Buy1']
        CurTime = int(context.now.strftime('%H%M'))

        if CurTime % SP['AnaFreq'] == 0 :

            for i in range(len(bird.ContractList)):
                CurCont = bird.ContractList[i]
                BarData = history_bars(CurCont, SP['BarNum'], SP['BarFreq'], self.DataType)
                BarData = bird.T.RemoveEmbodySeqMode_2DArray(BarData)
                # 返回数据列表，时间，开，高，低，收，型
                DOHLCT = bird.T.TypeAnalysis_2DArray(BarData)

                if len(DOHLCT) > 6:
                    # 向下趋势，反转, 买入开仓信号，买入开仓&设置强止损点位
                    if (DOHLCT[-6][self.low] > DOHLCT[-4][self.low] and DOHLCT[-4][self.low] > DOHLCT[-2][self.low] and
                        DOHLCT[-5][self.high] > DOHLCT[-3][self.high] and DOHLCT[-1][self.close] > DOHLCT[-4][self.close]):
                        if context.portfolio.positions[CurCont].buy_quantity == 0:
                            Amount = self.PositionProportion(self.BUY, bar_dict[CurCont].close, bird.TypesList[i])
                            if Amount > 0:
                                buy_open(CurCont,Amount,style=MarketOrder())
                        bird.TypesList[i]['BuyStop'] = DOHLCT[-2][self.close]
                    # 向上趋势，反转，买入开仓趋势止损信号。
                    if (DOHLCT[-6][self.high] < DOHLCT[-4][self.high] and DOHLCT[-4][self.high] < DOHLCT[-2][self.high] and
                        DOHLCT[-5][self.low] < DOHLCT[-3][self.low] and DOHLCT[-1][self.close] < DOHLCT[-3][self.close]):
                        Amount = context.portfolio.positions[CurCont].closable_buy_quantity
                        if Amount > 0:
                            sell_close(CurCont, Amount, style=MarketOrder())
        
        # 强止损
        for i in range(len(bird.ContractList)):
            CurCont = bird.ContractList[i]
            Amount = context.portfolio.positions[CurCont].closable_buy_quantity
            if Amount > 0 and bar_dict[CurCont].close < bird.TypesList[i]['BuyStop']:
                sell_close(CurCont, Amount, style=MarketOrder())

    def Stgy_2B_Sell1(self, bird, context, bar_dict):
    
        # 当前策略参数
        SP = bird.StgyParam['Stgy_2B_Sell1']
        CurTime = int(context.now.strftime('%H%M'))

        if CurTime % SP['AnaFreq'] == 0 :

            for i in range(len(bird.ContractList)):
                CurCont = bird.ContractList[i]
                BarData = history_bars(CurCont, SP['BarNum'], SP['BarFreq'], self.DataType)
                BarData = bird.T.RemoveEmbodySeqMode_2DArray(BarData)
                # 返回数据列表，时间，开，高，低，收，型
                DOHLCT = bird.T.TypeAnalysis_2DArray(BarData)

                if len(DOHLCT) > 6:
                    # 向上趋势，反转
                    if (DOHLCT[-6][self.high] < DOHLCT[-4][self.high] and DOHLCT[-4][self.high] < DOHLCT[-2][self.high] and
                        DOHLCT[-5][self.low] < DOHLCT[-3][self.low] and DOHLCT[-1][self.close] < DOHLCT[-4][self.close]):
                        if context.portfolio.positions[CurCont].sell_quantity == 0:
                            Amount = self.PositionProportion(self.SELL, bar_dict[CurCont].close, bird.TypesList[i])
                            if Amount > 0:
                                sell_open(CurCont,Amount,style=MarketOrder())
                        bird.TypesList[i]['SellStop'] = DOHLCT[-2][self.close]
                    # 向下趋势，反转
                    if (DOHLCT[-6][self.low] > DOHLCT[-4][self.low] and DOHLCT[-4][self.low] > DOHLCT[-2][self.low] and
                        DOHLCT[-5][self.high] > DOHLCT[-3][self.high] and DOHLCT[-1][self.close] > DOHLCT[-3][self.close]):
                        Amount = context.portfolio.positions[CurCont].closable_sell_quantity
                        if Amount > 0:
                            buy_close(CurCont, Amount, style=MarketOrder())

        # 强止损
        for i in range(len(bird.ContractList)):
            CurCont = bird.ContractList[i]
            Amount = context.portfolio.positions[CurCont].closable_sell_quantity
            if Amount > 0 and bar_dict[CurCont].close > bird.TypesList[i]['SellStop']:
                buy_close(CurCont, Amount, style=MarketOrder())

    def PositionProportion(self, Flag, Price, TypeData):

        # 计算最高点和最低点之间的均值。
        Avg = (TypeData['Highest'] + TypeData['Lowest']) / 2
        # 计算差值，差值等于 最高点或最低点减去10% 再减去均值的 绝对值。目的降噪
        Diff = abs((TypeData['Highest'] * (1 - 0)) - Avg)
        
        if Flag == self.BUY:
            if Price <= Avg:
                return TypeData['Amount']
            else:
                T_Diff = abs(Price - Avg)
                if (T_Diff / Diff) > 0.8:
                    return 0
                elif (T_Diff / Diff) > 0.6:
                    return round(TypeData['Amount'] * 0.5)
                else:
                    return TypeData['Amount']
        elif Flag == self.SELL:
            if Price >= Avg:
                return TypeData['Amount']
            else:
                T_Diff = abs(Avg - Price)
                if (T_Diff / Diff) > 0.8:
                    return 0
                elif (T_Diff / Diff) > 0.6:
                    return round(TypeData['Amount'] * 0.5)
                else:
                    return TypeData['Amount']

class Trend(object):
    def __init__(self):
        self.TYPING_NULL = 0      
        self.TYPING_TOP = 1        
        self.TYPING_BTM = -1
        
    def RemoveEmbodySeqMode_2DArray(self, kData, open = 1, high = 2, low = 3, close = 4):
        
        contain = 0
        tempH1 = 0
        tempH2 = 0
        tempL1 = 0
        tempL2 = 0

        rkData = []     
        MergeData = []  
        PreData = []    
        CurData = []    
        NextData = []  

        for i in range(len(kData)-1):
            if contain == 0:
                CurData = kData[i]   
            else:
                contain = 0
                CurData = MergeData    

            NextData = kData[i+1]  


            if (CurData[high] >= NextData[high] and CurData[low] <= NextData[low]):
                contain = 1 
            elif (CurData[high] <= NextData[high] and CurData[low] >= NextData[low]):
                contain = 2 
            
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
                    pass

        if contain == 0:
            rkData.append(NextData)
        else:
            rkData.append(MergeData)          
        
        return rkData
    
    def TypeAnalysis_2DArray(self, kData, Mode = True, open = 1, high = 2, low = 3, close = 4):
        
        i = 0
        preType = self.TYPING_NULL
        preHigh = 0
        preLow = 0
        preIndex = -5   
        preKey = 0
        typeDict = {preKey:[preIndex,preType]}


        while i < (len(kData)-2):
            Data1 = kData[i]
            Data2 = kData[(i+1)]
            Data3 = kData[(i+2)]

            if (Data2[high] > Data1[high] and Data2[high] > Data3[high] and
                Data2[low] > Data1[low] and Data2[low] > Data3[low]
                ):

                if preType == self.TYPING_NULL or preType == self.TYPING_TOP: 
                    if Data2[high] < preHigh: 
                        i += 1

                        continue
                    else:
                        preType = self.TYPING_TOP
                        preHigh = Data2[high]
                        preLow = Data2[low]
                        preIndex = i + 1
                        typeDict[preKey] = [i + 1, self.TYPING_TOP] 
                        i += 1
                elif preType == self.TYPING_BTM: 
                    if Data2[high] < preHigh or Data2[low] < preLow:
                        i += 1
                        continue
                    elif i + 1 < preIndex + 4: 
                        i += 1
                        continue
                    else: 
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

                if preType == self.TYPING_NULL or preType == self.TYPING_BTM: 
                    if Data2[low] > preLow:
                        i += 1
                        continue
                    else:
                        preType = self.TYPING_BTM
                        preHigh = Data2[high]
                        preLow = Data2[low]
                        preIndex = i + 1
                        typeDict[preKey] = [i + 1, self.TYPING_BTM]
                        i += 1
                elif preType == self.TYPING_TOP:
                    if Data2[high] > preHigh or Data2[low] > preLow: 
                        i += 1
                        continue
                    elif i + 1 < preIndex + 4: 
                        i += 1
                        continue
                    else:
                        preType = self.TYPING_BTM
                        preHigh = Data2[high]
                        preLow = Data2[low]
                        preIndex = i + 1
                        preKey += 1
                        typeDict[preKey] = [preIndex, preType]
                        i += 1
            i += 1

        typeTimeList = []
        for key, value in typeDict.items():
            typeTimeList.append(value)
        if Mode == True and len(typeTimeList) > 0:
            if (typeTimeList[0][0] != 0):
                typeTimeList.insert(0,[0,self.TYPING_NULL]) 
            if (typeTimeList[len(typeTimeList)-1][0] != (len(kData)-1)): 
                if typeTimeList[len(typeTimeList)-1][1] == self.TYPING_TOP:
                    typeTimeList.append([(len(kData)-1),self.TYPING_BTM])
                elif typeTimeList[len(typeTimeList)-1][1] == self.TYPING_BTM:
                    typeTimeList.append([(len(kData)-1),self.TYPING_TOP])
                else:
                    typeTimeList.append([(len(kData)-1),self.TYPING_NULL])

        for item in typeTimeList:
            try:
                row = item[0]
                item[0] = kData[row][0]
                item.insert(1, kData[row][close])
                item.insert(1, kData[row][low])
                item.insert(1, kData[row][high])
                item.insert(1, kData[row][open])
            except Exception:
                print(row)
                print(kData)
            
        # 返回值为2维数据，其中一项为 datetime open high low close type
        return typeTimeList

class GenObj:
    pass