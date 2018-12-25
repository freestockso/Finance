# encoding: UTF-8

import sys
import os
import struct
import datetime
import codecs
import shutil

def write2ext(fpath, dict2write, name_postfix='New'):
    # for line data "0|300253|32|chars|333.000"
    # in dict2write
    # key is "0|300253|32"
    # data is ("chars","333.000")
    
    dictOrig = {}
    
    infile = codecs.open(fpath, 'r', encoding = "gb2312")
    v1 = infile.readlines()
    for ln in v1:
        larr = ln.strip().split('|')
        if len(larr)<5:
            continue
        else:
            dictOrig[larr[0]+'|'+larr[1]+'|'+larr[2]] = (larr[3],larr[4])
        
    infile.close()
    
    dictNew = dictOrig.copy()
        
    for itKey in dict2write.keys():
        if len(itKey.split('|')) != 3:
            raise Exception(itKey)
        
        itVal = dict2write[itKey]
        
        if itVal == None:
            if itKey in dictNew:
                dictNew.pop(itKey)
            continue                
        
        if '|' in itVal[0]:
            raise Exception(itVal[0])
            
        dictNew[itKey] = (itVal[0], round(float(itVal[1]), 3))
    
    idx = fpath.rindex('.txt')
    fn_with_postfix = fpath[0:idx] + '_' + name_postfix + fpath[idx:]
    fn_orig_backup = fpath[0:idx] + '_' + 'orig' + fpath[idx:]
    
    output = codecs.open(fn_with_postfix, 'w', encoding = "gb2312")
    
    for itKey in dictNew.keys():
        itVal = dictNew[itKey]
        output.write(itKey)
        output.write('|' + itVal[0] + '|' + str(itVal[1]))
        output.write('\n')
        
    output.close()

    fn_orig_backup = fpath[0:idx] + '_' + datetime.datetime.now().strftime('orig@%Y%m%d%H%M%S') + fpath[idx:]
    
    shutil.copyfile(fpath,fn_orig_backup)
    shutil.copyfile(fn_with_postfix,fpath)    
        
    return

def main():
    
    print('init.')
    
    write2ext(r'D:\zd_pazq_loc\T0002\signals\extern_user.txt', {'0|300253|32':(u'中文chars',333.000)})
    
    print('ok.')
    return
    
class ClsA(object):

    #----------------------------------------------------------------------
    def __init__(self):
        
        self.a=0
        
if __name__ == '__main__':
    main()