# encoding: UTF-8

import sys
import os
import struct
import datetime
import shutil

import tdxdataext

def findPosInFile_day(hBinFile, nSize, sYYYYMMDD):
    size_unit = 32
    num = int(sYYYYMMDD)
    left = 0
    right = nSize//size_unit - 1
    while left <= right:   #循环条件
        mid = (left + right) // 2   #获取中间位置，数字的索引（序列前提是有序的）
        
        hBinFile.seek(mid*size_unit)
        rbs = hBinFile.read(4)
        getVal = struct.unpack('I',rbs)[0]  # I unsigned int integer 4        
        
        if num < getVal:  #如果查询数字比中间数字小，那就去二分后的左边找，
            right = mid - 1   #来到左边后，需要将右变的边界换为mid-1
        elif num > getVal:   #如果查询数字比中间数字大，那么去二分后的右边找
            left = mid + 1    #来到右边后，需要将左边的边界换为mid+1
        else:
            return mid*size_unit  #如果查询数字刚好为中间值，返回该值得索引
        
    return -1  #如果循环结束，左边大于了右边，代表没有找到

def binary_search_list(lis, nun):
    left = 0
    right = len(lis) - 1
    while left <= right:   #循环条件
        mid = (left + right) // 2   #获取中间位置，数字的索引（序列前提是有序的）
        if num < lis[mid]:  #如果查询数字比中间数字小，那就去二分后的左边找，
            right = mid - 1   #来到左边后，需要将右变的边界换为mid-1
        elif num > lis[mid]:   #如果查询数字比中间数字大，那么去二分后的右边找
            left = mid + 1    #来到右边后，需要将左边的边界换为mid+1
        else:
            return mid  #如果查询数字刚好为中间值，返回该值得索引
    return -1  #如果循环结束，左边大于了右边，代表没有找到

def day_b2v(ab32):
    rv=vUnit()
    
    idt = struct.unpack('I',ab32[0:4])[0]  # I unsigned int integer 4
    
    o1,h1,l1,c1 = struct.unpack('4I',ab32[4:20])  # I unsigned int integer 4
    rv.open = o1/100.0
    rv.high = h1/100.0
    rv.low = l1/100.0
    rv.close = c1/100.0
    
    rv.amount = struct.unpack('f',ab32[20:24])[0]  # f float float 4 
    
    rv.volume = struct.unpack('I',ab32[24:28])[0]  # I unsigned int integer 4 
    
    return rv

def calc_sigdef_day(hBinFile, nPos):
    rVal = ClsA()
    
    hBinFile.seek(nPos)
    rbs = hBinFile.read(32)
    ut1 = day_b2v(rbs)

    rVal.amount = round(ut1.amount/10000.0,3)
    rVal.close = ut1.close
    rVal.ratio = None
    
    if nPos>=32:
        hBinFile.seek(nPos-32)
        rbs = hBinFile.read(32)
        ut2 = day_b2v(rbs)
        rVal.ratio = (ut1.close-ut2.close)/ut2.close
        rVal.ratio = round(rVal.ratio*100.0,2)
        
    return rVal

def test_find():
    
    fpath_day=r'D:\zd_pazq_test\vipdoc\sh\lday\sh000001.day'
    
    hfile1 = open(fpath_day, 'rb')
    
    print(var1.__dict__)
    
    hfile1.close()
    
    print(nPos)
    
    return

def test_find_list():
    
    n = 0
    
    infile = open(r'HYList.txt', 'r')
    v1 = infile.readlines()
    for ln in v1:
        lstr = ln.strip()
        if lstr.startswith('.'):
            continue
    
        fpath_day = r'D:\zd_pazq_test\vipdoc\{CODE2}\lday\{CODE8}.day'
        #fpath_day = r'D:\zd_pazq\vipdoc\{CODE2}\lday\{CODE8}.day'        
        fpath_day = fpath_day.replace('{CODE2}',lstr[0:2])
        fpath_day = fpath_day.replace('{CODE8}',lstr)
        
        if not os.access(fpath_day, os.R_OK):
            continue
        
        hfile1 = open(fpath_day, 'rb')
    
        nPos = findPosInFile_day(hfile1, os.path.getsize(fpath_day), '20120105')
        if nPos < 0:
            pass
        else:
            var1 = calc_sigdef_day(hfile1, nPos)
            n += 1
        
        hfile1.close()
        
    print(n)
        
    return

def get_hist_for_list(lstCode, sYYYYMMDD, path_tdx_dir):
    
    rvDict = {}
    
    n = 0
    for itor in lstCode:
        lstr = itor.lower()
    
        fpath_day = path_tdx_dir+r'\vipdoc\{CODE2}\lday\{CODE8}.day'
        fpath_day = fpath_day.replace('{CODE2}',lstr[0:2])
        fpath_day = fpath_day.replace('{CODE8}',lstr)
        
        if not os.access(fpath_day, os.R_OK):
            continue
        
        hfile1 = open(fpath_day, 'rb')
    
        nPos = findPosInFile_day(hfile1, os.path.getsize(fpath_day), sYYYYMMDD)
        if nPos < 0:
            pass
        else:
            var1 = calc_sigdef_day(hfile1, nPos)
            if lstr[0:2] == 'sh':
                nmarket = 1
            elif lstr[0:2] == 'sz':
                nmarket = 0
            #'快照金额'=51
            rvDict[str(nmarket)+'|'+lstr[2:]+'|'+'51'] = ('', var1.amount)
            #'快照涨一'=52
            rvDict[str(nmarket)+'|'+lstr[2:]+'|'+'52'] = ('', var1.ratio)
            #'快照价收'=53
            rvDict[str(nmarket)+'|'+lstr[2:]+'|'+'53'] = ('', var1.close)
            n += 1
        
        hfile1.close()
        
    print(n)
        
    return rvDict

def gen_hist_extdata_for_hylist(fn_hylist, sYYYYMMDD, path_tdx_dir):
    
    lst = []
    
    infile = open(fn_hylist, 'r')
    v1 = infile.readlines()
    for ln in v1:
        lstr = ln.strip()
        if lstr.startswith('.'):
            continue
        
        lst.append(lstr)
        
    infile.close()
        
    dict2write = get_hist_for_list(lst, sYYYYMMDD, path_tdx_dir)
    
    tdxdataext.write2ext(path_tdx_dir+r'\T0002\signals\extern_user.txt', dict2write)
        
    return

def write2BLK(fnInput, fnOutput):
    
    lst = []
    
    infile = open(fnInput, 'r')
    v1 = infile.readlines()
    for ln in v1:
        lstr = ln.strip()
        if lstr == '':
            continue
        
        if lstr.startswith('88'):
            lstr = '1' + lstr
        else:
            raise Exception('not support type of ' + lstr)
        
        lst.append(lstr)
        
    infile.close()
    
    output = open(fnOutput, 'w')
    
    for s in lst:
        output.write(s)        
        output.write('\n')
        
    output.write('\n')
    
    output.close()

def main():
    
    print('init.')

    #test_find()

    print(datetime.datetime.now())    
    
    #test_find_list()
    
    s_tdx_path = r'D:\zd_pazq_loc'

    #gen_hist_extdata_for_hylist(r'HYList.txt', '20150624', s_tdx_path)
    
    write2BLK('BLKH', s_tdx_path + r'\T0002\blocknew\HS1.blk')
    
    print(datetime.datetime.now())
    
    print('ok.')
    return
    
class ClsA(object):

    #----------------------------------------------------------------------
    def __init__(self):
        
        self.a=0
        

class vUnit(object):

    #----------------------------------------------------------------------
    def __init__(self):
        
        self.date=0
        self.time=0
        self.sdatetime=''
        self.open=0.0
        self.high=0.0
        self.low=0.0
        self.close=0.0
        self.amount=0.0
        self.volume=0.0
        
if __name__ == '__main__':
    main()