# import re
# pattern = re.compile(r'#999999')
# str = 'F:\\StockData\\SH#999999.txt'
# asd = pattern.search(str)
# #asd = re.match(pattern, str)
# print(asd.group(0))

import datetime

asd = datetime.datetime.strptime('2018/06/07-00:00', '%Y/%m/%d-%H:%M')

print ((asd+datetime.timedelta(days=-1)).strftime('%Y/%m/%d-%H:%M'))


asd = datetime.datetime.strptime('2018/06/07-00:00', '%Y/%m/%d-%H:%M')
print(asd.strftime('%Y%m%d'))

asd = datetime.datetime.now()
print(asd)
# print(asd.strftime('%Y/%m/%d-%H:%M'))
print(asd.strftime('%H%M'))



#asd = datetime.datetime.strptime('2019-01-09 08:30:01.367000', '%Y-%m-%d %H:%M:%S.')
#print(asd.strftime('%Y%m%d'))

# for i in range(10):
#      pass
# print(i)

# asd = [1,2,3,4,5,6,7,8,9,0]
# print (asd[8:9])


# asd1 = [[0],[1]]
# asd2 = [[2]]

# print (asd1+asd2)
# import pickle
 
# data1 = {'a': [1, 2.0, 3, 4+6j],
#      'b': ('string', u'Unicode string'),
#      'c': None}
 
# selfref_list = [1, 2, 3]
# selfref_list.append(selfref_list)
 
# output = open('data.pkl', 'wb')
 
# # Pickle dictionary using protocol 0.
# pickle.dump(data1, output)
 
# # Pickle the list using the highest protocol available.
# pickle.dump(selfref_list, output, -1)
 
# output.close()

# list1 = [[2],[3]]
# list2 = [[6],[1],[2]]

# print(list1+list2)


# dica={'a':1,'b':2,'c':3,'d':4,'f':"hello"}
# dicb={'b':3,'d':5,'e':7,'m':9,'k':'world'}
# dic={}
# for key in dica:
#     print(key)
#     if dicb.get(key):
#         dic[key]=dica[key]+dicb[key]
#     else:
#         dic[key]=dica[key]
# for key in dicb:
#     if dica.get(key):
#         pass
#     else:
#         dic[key]=dicb[key]
            
# print(dic)



# asd = [1,2,3]
# qwe = 1
# def asdModifier(listT, qwe):
#     listT[0] = 6
#     qwe = 2
# asdModifier(asd,qwe)
# print(asd)
# print(qwe)

# ilist = [[1],[2],[3]]
# for i in ilist:
#     i.append(6)

# print(ilist)

# import os
# i = 1
# for (root, dirs, files) in os.walk('.//StockData'):

#      print(i)
#      print(root)
#      # print(dirs)
#      # print(files)
#      print(os.path.basename(root))
#      i+=1

# #最大数
# def Get_Max(list):
#    return max(list)
# #最小数
# def Get_Min(list):
#    return min(list)
# #极差
# def Get_Range(list):
#    return max(list) - min(list)
    
# #中位数
# def get_median(data):
#    data = sorted(data)size = len(data)
#    if size % 2 == 0: 
#       # 判断列表长度为偶数
#       median = (data[size//2]+data[size//2-1])/2
#    if size % 2 == 1: 
#       # 判断列表长度为奇数
#       median = data[(size-1)//2]
#    return median
 
# #众数(返回多个众数的平均值)
# def Get_Most(list):
#    most=[]
#    item_num = dict((item, list.count(item)) 
#    for item in list)for k,v in item_num.items():
#       if v == max(item_num.values()):
#          most.append(k)
#    return sum(most)/len(most)
          
# #获取平均数
# def Get_Average(list):
#    sum = 0
#    for item in list:     
#       sum += item  
#    return sum/len(list)

print(round(3.55))