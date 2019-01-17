import numpy
import pandas
import copy
 
# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # context内引入全局变量s1
    
    context.bird = GenObj()
    
    bird = context.bird
    
    bird.S = get_dominant_future('J')   # 合约名
    bird.Cout = 200        # 数据条数
    bird.Freq = '5m'        # 数据的频率
    bird.TotalAmount = 0 # 仓位
    bird.Time = 0
    bird.Time1 = 0
    bird.BuyStop = 0
    bird.SellStop = 0
    bird.Time = 0
    bird.T = Trend()
 
    # 初始化时订阅合约行情。订阅之后的合约行情会在handle_tick中进行更新。
    subscribe(bird.S)
    # 实时打印日志
    logger.info("RunInfo: {}".format(context.run_info))
 
# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    bird = context.bird
    bird.Time = 0
    bird.Time1 = 0
    bird.S = get_dominant_future('J')
    subscribe(bird.S)
 
# 你选择的期货数据更新将会触发此段逻辑
def handle_bar(context, bar_dict):
    bird = context.bird
    
    CurTime = int(context.now.strftime('%H%M'))
    if CurTime % 10 == 0 and CurTime != bird.Time:
        bird.Time = CurTime 
        price = history_bars(bird.S, bird.Cout, bird.Freq, ['datetime','open','high','low','close'])
        re_price = bird.T.RemoveEmbodySeqMode_2DArray(price)
        DOHLCT = bird.T.TypeAnalysis_2DArray(re_price)
        Signal_2B_Buy1 = bird.T.Strategy_2B_Buy1(DOHLCT)
        Signal_2B_Sell1 = bird.T.Strategy_2B_Sell1(DOHLCT)
        
        if Signal_2B_Buy1[0] == bird.T.Buy:
            if context.portfolio.positions[bird.S].buy_quantity == 0:
                buy_open(bird.S,1,style=MarketOrder())
            bird.BuyStop = Signal_2B_Buy1[1]
        elif Signal_2B_Buy1[0] == bird.T.BuyClose:
            if context.portfolio.positions[bird.S].closable_buy_quantity > 0:
                sell_close(context.portfolio.positions[bird.S].order_book_id, 1, style=MarketOrder())
        
        if Signal_2B_Sell1[0] == bird.T.Sell:
            if context.portfolio.positions[bird.S].sell_quantity == 0:
                sell_open(bird.S,1,style=MarketOrder())
            bird.SellStop = Signal_2B_Sell1[1]
        elif Signal_2B_Sell1[0] == bird.T.SellClose:
            if context.portfolio.positions[bird.S].closable_sell_quantity > 0:
                buy_close(context.portfolio.positions[bird.S].order_book_id, 1, style=MarketOrder())
            
    
    # 强止损
    if context.portfolio.positions[bird.S].closable_buy_quantity > 0 and bar_dict[context.portfolio.positions[bird.S].order_book_id].close < bird.BuyStop:
        sell_close(context.portfolio.positions[bird.S].order_book_id, 1, style=MarketOrder())

    if context.portfolio.positions[bird.S].closable_sell_quantity > 0 and bar_dict[context.portfolio.positions[bird.S].order_book_id].close > bird.SellStop:
        buy_close(context.portfolio.positions[bird.S].order_book_id, 1, style=MarketOrder())
            

# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    pass

class Trend(object):
    def __init__(self):
        self.TYPING_NULL = 0      
        self.TYPING_TOP = 1        
        self.TYPING_BTM = -1
        
        self.Buy = 1
        self.BuyClose = 2
        self.Sell = -1
        self.SellClose = -2
    
    # 返回数据【买卖信号，止损点】
    def Strategy_2B(self, TypeList, open = 1, high = 2, low = 3, close = 4):
        
        if len(TypeList) > 6:
            # 向下趋势，反转
            if (TypeList[-6][low] > TypeList[-4][low] and TypeList[-4][low] > TypeList[-2][low] and
                TypeList[-5][high] > TypeList[-3][high] and TypeList[-1][close] > TypeList[-4][close]):
                return [self.Buy, TypeList[-2][close]]
            # 向上趋势，反转
            if (TypeList[-6][high] < TypeList[-4][high] and TypeList[-4][high] < TypeList[-2][high] and
                TypeList[-5][low] < TypeList[-3][low] and TypeList[-1][close] < TypeList[-3][close]):
                return [self.Sell, TypeList[-2][close]]
        
        return [0,0]
    
    # 返回数据【买信号，止损点】
    def Strategy_2B_Buy1(self, TypeList, open = 1, high = 2, low = 3, close = 4):
        
        if len(TypeList) > 6:
            # 向下趋势，反转
            if (TypeList[-6][low] > TypeList[-4][low] and TypeList[-4][low] > TypeList[-2][low] and
                TypeList[-5][high] > TypeList[-3][high] and TypeList[-1][close] > TypeList[-4][close]):
                return [self.Buy, TypeList[-2][close]]
            # 向上趋势，反转
            if (TypeList[-6][high] < TypeList[-4][high] and TypeList[-4][high] < TypeList[-2][high] and
                TypeList[-5][low] < TypeList[-3][low] and TypeList[-1][close] < TypeList[-3][close]):
                return [self.BuyClose, 0]
        
        return [0,0]

    def Strategy_2B_Sell1(self, TypeList, open = 1, high = 2, low = 3, close = 4):
        
        if len(TypeList) > 6:
            # 向上趋势，反转
            if (TypeList[-6][high] < TypeList[-4][high] and TypeList[-4][high] < TypeList[-2][high] and
                TypeList[-5][low] < TypeList[-3][low] and TypeList[-1][close] < TypeList[-4][close]):
                return [self.Sell, TypeList[-2][close]]
            # 向下趋势，反转
            if (TypeList[-6][low] > TypeList[-4][low] and TypeList[-4][low] > TypeList[-2][low] and
                TypeList[-5][high] > TypeList[-3][high] and TypeList[-1][close] > TypeList[-3][close]):
                return [self.SellClose, 0]
        
        return [0,0]
        

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