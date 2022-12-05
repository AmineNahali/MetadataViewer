# -*- coding: utf-8 -*-
"""
Created on 2021-08-04

@author: PatrickPoitras
"""


import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize
import os
import struct
import time
import datetime


class Constants:
    DEFAULT_NPOINTS = 250
    
#code start
def ArrayToNumbers(filename):
    lines = []            
    with open (filename, 'rt') as thefile: 
        for line in thefile:                
            lines.append(line)                                       
    lines = lines[1:len(lines)] # Disregarding MetaData 

    txtdata = []

    # Going through Entire Data
    for i in range(len(lines)):
        txtdata.append(ConvertToNumbers(lines[i]))
    return txtdata        

def ConvertToNumbers(inputlist):
    finallist = [] # a list of numbers that will be returned at the end.
    finallistfloat = [] # a list of numbers simular to finallist, but converted as a float
    tempstr = "" # a string that will combine a number, to be added to list, then reset. 
    
    for letterindex in range(len(inputlist)): # iterating through each character.
        if inputlist[letterindex] == "\t": # if its a new word.
            finallist.append(tempstr) 
            tempstr = ""
        else: 
            tempstr += inputlist[letterindex]
    
    if len(tempstr) > 0:
       finallist.append(tempstr)
    # Iterates, and typecasts to floats.
    
    for number in range(len(finallist)): # iterating through all numbers in list.
        finallistfloat.append(float(finallist[number]))

    return finallistfloat

def BinaryArrayToNumbers(datfilename):
    templist =[]
    binarylist = [] # master list used for data values
    finalbinarylist = []
    with open(datfilename, "rb") as binary_file: # scope of binary
        # Read the whole file at once
        data = binary_file.read(4) # returns iterator
    
        while(data):
            binarylist.append(struct.unpack("f", data)[0])
            data = binary_file.read(4)
    
    # Looping through, building double array appropriately
    for i in range(len(binarylist)):
        if binarylist[i] != 4286578688.0:
            templist.append(binarylist[i]) # add to the temporary list 
        # When a new iteration is reached
        else: 
            finalbinarylist.append(templist) # adding to the master branch
            templist = [] # resetting the list
    return finalbinarylist


def verifyBlanking(dataSeries,noiseFloor):
    #filter out points that are not valid
    
    length = len(dataSeries)
    avg1 = np.mean(dataSeries[:Constants.DEFAULT_NPOINTS])
    avg2 = np.mean(dataSeries[length//2:length//2+Constants.DEFAULT_NPOINTS])
    avg3 = np.mean(dataSeries[-Constants.DEFAULT_NPOINTS:])
    
    cond1 = avg1 < avg2
    cond2 = avg1 < avg3
    distanceCondition = (avg3-avg1) < (2*(noiseFloor-avg1))
    distanceCondition2 = max(dataSeries[-Constants.DEFAULT_NPOINTS:]) > min(dataSeries[:Constants.DEFAULT_NPOINTS])
    
    condition = True
    if (cond1 or cond2 or distanceCondition or distanceCondition2):
        condition = False
    return condition


#remove the covariance warning. Covariance is not going to be able to be estimated
#for a non-continuous fit function

import warnings
warnings.filterwarnings("ignore")

def fitFunction(x,b,c,m,tau,cut):
    a = (m*cut+b-c)/np.exp(-cut/tau)
    cut = np.abs(cut)
    linearpart = m*x+b
    exppart = a*np.exp(-x/tau) + c
    transition = np.heaviside((x-cut),1)
    return (1-transition)*linearpart + exppart*transition

def STOT(x):
    return np.std(x)/np.mean(x)

##Parameter start
randomnumber = 0

def writeGarbage(filepath):
    g = open("garbageLines.txt","a")
    g.write(filepath+"\n")
    g.close()

currentCount = 0

def parseTime(sss):
    try:
        #old filename format
        h,m,s,p = (" ".join(sss.split("_")[:-1])[3:]).split(" ")
        h = int(h)
        if p == "PM" and h != 12:
            h += 12
        if p == "AM" and h == 12:
            h = 0
        m = int(m)
        s = int(s)
        return datetime.time(h,m,s)
    except ValueError: #new filename format
        sss = "_".join(sss.split("_")[:-1]) #remove line name and trailing information
        sss = sss.replace("_"," ").replace("h",":").replace("m",":").replace("s","")
        return datetime.datetime.fromisoformat(sss)


def process(RAW_DATA_FILEPATH, counter=None):    
    OUTPUT_FILEPATH = RAW_DATA_FILEPATH +"/"+"output.dat"
    OUTPUT_ENABLE = True

    f = open("{0}/{1}".format(RAW_DATA_FILEPATH,"TimeTable"))
    u = list(f.readlines())[1:]
    u = [i.split("\t") for i in u]
    u = [(float(i[0]),i[1]) for i in u]
    mapdict = {}
    for i in u:
        wl,linename = i
        mapdict[linename] = wl
        
    if OUTPUT_ENABLE:
        outputfile = open(OUTPUT_FILEPATH,'w')
    global currentCount
    if not os.path.exists(os.path.join(RAW_DATA_FILEPATH,"RawData")):
        return None
    for file in os.listdir(os.path.join(RAW_DATA_FILEPATH,"RawData")):
        currentCount += 1
        starttime = time.time()
        fp = os.path.join(RAW_DATA_FILEPATH,"RawData/"+file)
        lines = []
        if file.split(".")[-1] =="txt":
            lines = ArrayToNumbers(fp)
        else:
            lines = BinaryArrayToNumbers(fp)
        if counter is not None:
            print("({0}/{1}) ".format(currentCount,counter),end="")
        print(fp)
        timestamp = parseTime(file)
        linename = file.split("_")[-1].split(".")[0]
        sample = 5.00000E-9
        tau_crop = []
        transitionpoints = []
        residuals = []
        graph = False
        noiseFloors = []
        filterReject = 0
        for u in lines:
            noiseFloors.append(np.mean(u[-Constants.DEFAULT_NPOINTS:]))
        
        noiseFloor = np.mean(noiseFloors)
        for u in range(len(lines)):
            y = lines[u]
            if False and not verifyBlanking(y,noiseFloor):
                filterReject += 1
                continue
            
            p0 =  (y[0],
                   np.mean(y[4500:]),
                   25000, #slope
                   2.5E-6, #average time
                   250*sample) #default transition point
            
            p0_crop = p0
            h_crop = None
            x = np.arange(0,sample*len(y),sample)
            try:
                h_crop = scipy.optimize.curve_fit(fitFunction,x,y,p0=p0_crop)
            except RuntimeError:
                print(fp, "is garbage!")
                writeGarbage(fp)
                continue
            tau_crop.append(h_crop[0][3])
            transitionpoints.append(h_crop[0][2])

            h = h_crop
            res = sum(np.abs((y-fitFunction(x,*h_crop[0]))))
            residuals.append(res)
            if graph and res > 20:
                plt.plot(x/1E-6,fitFunction(x,*h_crop[0]))
                plt.plot(x/1E-6,y)
                labels = ['b','c','m','tau','cut','k']
                for i in range(len(h[0])):
                    print(labels[i]+":",h[0][i], p0_crop[i])
                plt.show()
            else:
                pass
                #print(u,tau_sigmoid[-1], tau_linear[-1],tau_crop[-1])
        
        halfval = np.mean(transitionpoints)
        tc_blue = []
        tc_orange = []
        
        for ii in range(len(tau_crop)):
            if transitionpoints[ii] > halfval:
                tc_orange.append(tau_crop[ii])
            else:
                tc_blue.append(tau_crop[ii])
        
        #plt.title(fp)
        #plt.plot(tc_blue,'.')
        #plt.plot(tc_orange,'.')
        global randomnumber
        #plt.savefig("COfoire{:05d}.png".format(randomnumber))
        randomnumber+= 1
        #plt.clf()
        print(linename, np.mean(tau_crop),    np.std(tau_crop),   STOT(tau_crop), np.mean(residuals),    sep="\t")
        if OUTPUT_ENABLE:
            mean = np.mean(tau_crop)
            stot = STOT(tau_crop)
            mean_res = np.mean(residuals)
            if len(residuals) > 0:
                max_res = np.max(residuals)
            else:
                max_res = "nan"
            if mean is None or mean == float('nan'):
                mean = "NaN"
            else:
                mean = "{:.6f}E-6".format(mean*1E6)
            if stot is None or stot == float('nan'):
                stot = "NaN"
            else:
                stot = "{:.6f}E-6".format(stot*1E6)
            outputfile.write("{0},{1},{2},{3},{4},{5}\n".format(linename,mean,stot,mean_res,max_res,timestamp))
        print("Rejected:", filterReject,"\tTime:", time.time()-starttime)

def countFolders(folder):
    try:
        return len(os.listdir(os.path.join(folder,"RawData")))
    except FileNotFoundError:
        return 0
    
def buildAndProcess(specificfolderpath):
    folders = sorted(os.listdir(specificfolderpath))
    folders = [i for i in folders if ".py" not in i and ".done" not in i and ".bat" not in i and ".exe" not in i and ".txt" not in i]
    folders = [os.path.join(specificfolderpath,i) for i in folders]
    
    ss = sum([countFolders(i) for i in folders])
    
    for folder in folders:
        process(folder,ss)

if __name__ == "__main__":
    buildAndProcess("./")