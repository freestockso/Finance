# encoding: UTF-8

import sys
import os
import struct

import codecs
import tdxdataext

if sys.version_info.major >= 3:
    g_py_ver_ge3 = True
else:
    g_py_ver_ge3 = False

# Maybe this function is not necessary
# To keep no encoding error for both py2 & py3:
# Just to use codecs.open and codecs.close in pairs with encoding=XX
# And remember to add 'u' prefix for all "中文" strings in py2 source file
def str_fromfilegb2312_for_py2(str1):
    if g_py_ver_ge3:
        return str1
    else:
        return str1.decode('gb2312')
        
def gendict_88XXXX_gnName():

    rvDict = {}
    rvDict_rev = {}
    
    infile = open(path_tdx_dir + r'\T0002\hq_cache\tdxzs.cfg', 'r')
    v1 = infile.readlines()
    print(len(v1))
    for ln in v1:
        larr = ln.strip().split('|')
        if len(larr) >= 6:
            #check 88 code
            s1 = larr[1]
            s2 = str_fromfilegb2312_for_py2(larr[5])
            sType = larr[2]
            if (s1.startswith('88') and
                sType=='4'):
                rvDict[s1] = s2
                rvDict_rev[s2] = s1
        
    infile.close()
    return (rvDict, rvDict_rev)

def gendict_STCODE_gnName():

    rvDict = {}
    rvDict_rev = {}
    
    infile = open(path_tdx_dir + r'\T0002\hq_cache\block_gn.dat', 'rb')
    rbs = infile.read()        
    infile.close()
    
    #//data format - T0002/hq_cache/block.dat block_fg.dat block_gn.dat block_zs.dat
    #struct TTDXBlockHeader
    #{
        #char         szVersion[64];        // 0, Registry ver:1.0 (1999-9-28)
        #int            nIndexOffset;            // 64, 0x00000054
        #int            nDataOffset;            // 68, 0x00000180
        #int            nData1;                // 72, 0x00000003
        #int            nData2;                // 76, 0x00000000
        #int            nData3;                // 80, 0x00000003
    #};    
    nDataOffset = 68
    
    #struct TTDXBlockIndex
    #{
        #char        szName[64];            // 0, Root, Block, Val
        #int            nData1;                // 64
        #int            nData2;                // 68
        #int            nLength;                // 72, length of the block
        #int            nOffset;                // 76, offset of the data part
        #int            nData3;                // 80
        #int            nData4;                // 84
        #int            nData5;                // 88, root=-1,block=0,val=1
        #int            nData6;                // 92, root=1,block=2,val=-1
        #int            nStatus;                // 96, 1
    #};
    
    #struct TTDXBlockRecord
    #{
        #char         szName[9];
        #short        nCount;
        #short        nLevel;
        #char         szCode[400][7];
    #};
    
    #content at nDataOffset:
    #(2 bytes of record counts)(record1)(record2)..((recordN))
    
    offsetData = struct.unpack('I',rbs[nDataOffset:nDataOffset+4])[0]  # I unsigned int integer 4 
    nRec = struct.unpack('H',rbs[offsetData:offsetData+2])[0]  # H unsigned short integer 2
    
    size_rec = (9+2+2+7*400)
    for i in range(0,nRec):
        offsetStart = offsetData+2+i*size_rec
        bsRecData = rbs[offsetStart:offsetStart+size_rec]
        bsName = bsRecData[0:9]
        bsName = bsName[0:bsName.index(b'\x00')]
        gnName = bsName.decode('gb2312')
        
        if not gnName in rvDict_rev:
            rvDict_rev[gnName] = []
        locLst_rev = rvDict_rev[gnName]
        
        STCount = struct.unpack('H',bsRecData[9:11])[0]  # H unsigned short integer 2
        for j in range(0,STCount):
            offset_j = 13+7*j
            bsOneST = bsRecData[offset_j:offset_j+7-1]
            STName = bsOneST.decode()
            if STName[0] == '6':
                sMarket = 'sh'
            elif STName[0] == '0' or STName[0] == '3':
                sMarket = 'sz'
            
            STName = sMarket + STName
            if not STName in rvDict:
                rvDict[STName] = []
            locLst = rvDict[STName]
            
            locLst.append(gnName)
            locLst_rev.append(STName)
        
    for itKey in rvDict.keys():
        rvDict[itKey].sort()
        
    for itKey in rvDict_rev.keys():
        rvDict_rev[itKey].sort()            
    
    return (rvDict, rvDict_rev)

def writeGNinDataExt(dictSTGN):
    
    #{'0|300253|32':(u'中文chars',333.000)}
    dict2write = {}
    
    for itor in dictSTGN.keys():
        codeST = itor
        lstr = codeST
        
        s_txt = ''
        for lstItor in dictSTGN[codeST]:
            if len(s_txt)>0:
                s_txt += ','
                
            s_txt += lstItor
    
        if lstr[0:2] == 'sh':
            nmarket = 1
        elif lstr[0:2] == 'sz':
            nmarket = 0
        #'概念成分'=35
        dict2write[str(nmarket)+'|'+lstr[2:]+'|'+'35'] = (s_txt, 0.000)
        
    tdxdataext.write2ext(r'D:\zd_pazq_loc\T0002\signals\extern_user.txt', dict2write)
    
    return

def main():
    
    print('init.')
    
    global path_tdx_dir
    path_tdx_dir = r'D:\zd_pazq_loc'
    
    (dict88GN,dictGN88) = gendict_88XXXX_gnName()
    (dictSTGN,dictGNST) = gendict_STCODE_gnName()
    
    outfn = 'GNList.txt'
    output = codecs.open(outfn, 'w', encoding = "utf-8")
    #output = codecs.open(outfn, 'w')
    
    for itor in dict88GN.keys():
        code88 = itor
        gnName = dict88GN[code88]
        
        output.write('.'+code88+','+gnName)
        output.write('\n')
        
        for lstItor in dictGNST[gnName]:
            output.write(lstItor)
            output.write('\n')
    
    output.close()
    
    outfn = 'STinGN.txt'
    output = codecs.open(outfn, 'w', encoding = "utf-8")
    #output = codecs.open(outfn, 'w')
    
    for itor in dictSTGN.keys():
        codeST = itor
        output.write(codeST+':')
        for lstItor in dictSTGN[codeST]:
            output.write(lstItor)
            output.write(',')
        output.write('\n')
    
    output.close()
    
    writeGNinDataExt(dictSTGN)
    
    print('ok.')
    return
    
class ClsA(object):

    #----------------------------------------------------------------------
    def __init__(self):
        
        self.a=0
        
        
if __name__ == '__main__':
    main()