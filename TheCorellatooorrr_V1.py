import numpy as np
from numpy import NaN, ceil, floor
import pandas as pd
import requests
import io
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.gridspec import GridSpec

 #You can change to manual coin and time length selection instead of auto selection based on what you've already saved in the input .csv file
# by commenting out the relevant 6 lines below here and uncommenting lines 23 - 25. 
#Auto input of coin selection and parameters:
dfIn = pd.read_csv(r"C:\Users\jimmi\Documents\PairCorrelation\PairCorrInput.csv")  #We need to make sure the little r is there next to the path string to make it a raw string.
Coin1 = str(dfIn.loc[0].at["Coin1"])                                   #Windows requires directory designators of "\\" instead of just "\" which works for mac and linux.
Coin2 = str(dfIn.loc[0].at["Coin2"])
CCAvs = pd.Series.dropna(dfIn["CC Averages"])
numCCAvs = len(CCAvs)
print("Correlation averages to calculate: \n",CCAvs,numCCAvs)
print('Coin 1 is: '+Coin1)
print('Coin 2 is: '+Coin2)
TimeLength = str(dfIn.loc[0].at["NumDays"])
#print(Coin1,Coin2,TimeLength)
#Call API for selected coins with manual input:
#Coin1 = input("Give a coin gecko API for coin 1: ")
#Coin2 = input("Give a coin gecko API for coin 2: ")
#TimeLength = input('Provide number of days into the past that you wish to get the historical data for: ')

#Call CoinGecko API:
url = r'https://api.coingecko.com/api/v3/coins/'+Coin1+r'/market_chart?vs_currency=usd&days='+TimeLength+r'&interval=daily' 
url2 = r'https://api.coingecko.com/api/v3/coins/'+Coin2+r'/market_chart?vs_currency=usd&days='+TimeLength+r'&interval=daily' 
r = requests.get(url)           #Requests calls the coin gecko API. I'll have to figure out how to add trading view too. 
r2 = requests.get(url2)
df = pd.read_csv(io.StringIO(r.text))
df2 = pd.read_csv(io.StringIO(r2.text))
df = pd.DataFrame.from_dict(r.json())
df2 = pd.DataFrame.from_dict(r2.json())
#print(df)

length = len(df)
length2 = len(df2)
if(length < length2):
    comLength = length
else:
    comLength = length2
print('Coin1 length: '+str(length)+ ', Coin2 length: '+str(length2)+  '.')
if(length != length2):     #Check that the two data matrices pulled from the API are of equal length:
    print("Warning: Length of the two price matrices are not equal, pull out. Set numDays parameter to: "+str(comLength-1)+'.')
    quit()
else:
    elementA1 = df.loc[0].at["prices"]     #Figure out the time string in the json response. 
    elementA2 = df.loc[comLength-1].at["prices"]     #Turns out to be time elapsed in ms since start of price tracking!!
    startTime = elementA1[0]      
    endTime = elementA2[0]       
    numDays = int(floor((endTime-startTime)/(1000*60*60*24)+1))
    print("Number of days into the past before today tracked here: "+str(numDays)+'\r')

    list = []
    for i in range((numDays-1), -1, -1):         #This converts the json response array from API into Pandas dataframe..
        element = df.loc[i].at["prices"]
        mc = df.loc[i].at["market_caps"]
        tv = df.loc[i].at["total_volumes"]
        TimeInPast = numDays - floor((element[0]-startTime)/(1000*60*60*24)+1)
        list.append([TimeInPast,element[1], mc[1], tv[1]])
    PriceMatrix1 = pd.DataFrame(list,columns=['Days ago','Price (USD)','Market Cap (USD)','Volume (USD)'])
    #print(PriceMatrix1)
    Price1 = pd.Series.to_numpy(PriceMatrix1['Price (USD)'])

    list = []
    for i in range((numDays-1),-1,-1):
        element = df2.loc[i].at["prices"]
        mc = df2.loc[i].at["market_caps"]
        tv = df2.loc[i].at["total_volumes"]
        TimeInPast = numDays - floor((element[0]-startTime)/(1000*60*60*24)+2)
        list.append([TimeInPast,element[1], mc[1], tv[1]])
    PriceMatrix2 = pd.DataFrame(list,columns=['Days ago','Price (USD)','Market Cap (USD)','Volume (USD)'])
    #print(PriceMatrix2)
    Price2 = pd.Series.to_numpy(PriceMatrix2['Price (USD)'])

    def CovCorrCalc(AssetPrice1: np.ndarray, AssetPrice2: np.ndarray) -> np.ndarray:           #Function for the cov and Corr. 
        num = len(AssetPrice1)
        Numerator = 0; Coin1_std = 0; Coin2_std = 0
        mean_Coin1 = np.mean(AssetPrice1)
        mean_Coin2 = np.mean(AssetPrice2)
        CovCorr = []

        for i in range(int(num)):   
            Numerator += (AssetPrice1[i] - mean_Coin1)*(AssetPrice2[i] - mean_Coin2)
            Coin1_std += (AssetPrice1[i] - mean_Coin1)**2
            Coin2_std += (AssetPrice2[i] - mean_Coin2)**2
        Denominator = np.real((Coin1_std**0.5)*(Coin2_std**0.5))
        CovCorr.append(Numerator/(num-1))     #Co-variance of asset pair over the datasets.
        CovCorr.append(np.real(Numerator/Denominator))  #Correlation co-efficient of asset pair over the datasets.
        
        return CovCorr       #Returns a two number list that has the covariance in the first slot and correlation in the second. 

    #Use my covariance, correlation function: 
    CovCorr = CovCorrCalc(Price1, Price2)
    CovString = 'Asset pair co-variance over the whole \ntime period (manual): '+str(round(CovCorr[0], 4))
    CorrString = 'Asset pair correlation over the whole \ntime period (manual): '+str(round(CovCorr[1], 4))
    print(CovString); print(CorrString)

    #Check it with numpy correlation calculation:
    print('Standard deviation (numpy) coin1, coin2: ',np.std(Price1),np.std(Price2))
    NumpyCorr = np.corrcoef(Price1,Price2)
    NumpyCov = np.cov(Price1,Price2)
    NPCorrString = 'Asset pair correlation over the whole \ntime period (from numpy): '+str(round(NumpyCorr[1,0], 4))
    NPCovString = 'Asset pair covariance over the whole \ntime period (from numpy): '+str(round(NumpyCov[1,0], 4))
    print(NPCorrString); print(NPCovString)

    ########################## Correlation for certain periods calculated like a moving average function:
    def CovCorrMA(period: int, AssetPrice1: np.ndarray, AssetPrice2: np.ndarray) -> pd.DataFrame:
        count = 0;  Numerator = 0; Coin1_std = 0; Coin2_std = 0
        num = len(AssetPrice1)
        mean_Coin1 = np.mean(AssetPrice1)
        mean_Coin2 = np.mean(AssetPrice2)
        
        CovCorrList = []
        for i in range(num):            
            if(i > (num-int(period))):
                break 
            for j in range(int(period)):
                count = i + j
                Numerator += (AssetPrice1[count] - mean_Coin1)*(AssetPrice2[count] - mean_Coin2)
                Coin1_std += (AssetPrice1[count] - mean_Coin1)**2
                Coin2_std += (AssetPrice2[count] - mean_Coin2)**2
            Denominator = np.real((Coin1_std**0.5)*(Coin2_std**0.5))
            PeriodCorr = (np.real(Numerator/Denominator))
            PeriodCov = (np.real(Numerator/(num-1)))
            CovCorrList.append([PeriodCov, PeriodCorr])
            Numerator = 0        ## Reset the counter variables.
            Coin1_std = 0
            Coin2_std = 0
        CovColName = 'CV_'+str(period)+'day'
        CorrColName = 'CC_'+str(period)+'day'
        CovCorrDF = pd.DataFrame(CovCorrList, columns=[CovColName, CorrColName])
        return CovCorrDF       #Dataframe containing the MA for the given period, 1st column co-variance, second column correlation co-efficient. 

    MasterDF = pd.concat([PriceMatrix1,PriceMatrix2],axis=1) # Create the master dataframe to output to csv.  
    for i in range(numCCAvs):
        CorrAv = CovCorrMA(int(CCAvs[i]),Price1, Price2)
        MasterDF = pd.concat([MasterDF, CorrAv],axis=1)
    CovCorr_Full = CovCorrMA(numDays, Price1, Price2)
    MasterDF = pd.concat([MasterDF, CovCorr_Full],axis=1)
    MasterDF.to_csv(r'C:\Users\jimmi\Documents\PairCorrelation\PairCorrOutput.csv', index = False)  #We need to make sure the little r is there next to the path string to make it a raw string.
    print('Data output to: '+r'C:\Users\jimmi\Documents\PairCorrelation\PairCorrOutput.csv') #We need to make sure the little r is there next to the path string to make it a raw string. 

    #Calculate normalised price ratio wave and normalized percentage changed from median wave.
    PriceRatio = PriceMatrix1['Price (USD)']/PriceMatrix2['Price (USD)']
    Ratio_norm = (PriceRatio - PriceRatio.min())/ (PriceRatio.max() - PriceRatio.min())
    Percentage = PriceRatio
    midpoint = np.median(PriceRatio)
    points = len(PriceRatio)
    print('Median of the '+str(Coin1)+'/'+str(Coin2)+' data is: '+ str(midpoint))

    for i in range(int(points)):
        Percentage.loc[i] = ((Percentage.loc[i] - midpoint)/midpoint)*100

    # # ################################### #Plot figures #############################################################

    #Price ratio plot.
    fig = plt.figure(figsize=(8.3,9.5))
    gs1 = GridSpec(3, 1, top = 0.95, bottom=0.07, left=0.11, right=0.86, wspace=0.01, height_ratios=[2,2,1], hspace=0.22)
    ratString = Coin1+'/'+Coin2
    ax1 = fig.add_subplot(gs1[0])
    TitleString = 'Price ratio '+Coin1+'/'+Coin2+r', $\Delta$% from median'
    ax1.set_title(TitleString, fontsize=12)
    trace3 = ax1.plot(PriceMatrix1['Days ago'], Percentage, c = 'black', label=ratString)
    ax1.invert_xaxis()
    ax1.set_ylabel(r'$\Delta$ price from median (%)', fontsize=14)
    ax1b = ax1.twinx()
    ax1b.plot(PriceMatrix1['Days ago'], Percentage, c = 'black')
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax1b.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax1.legend(loc=2)

    #Price of both assets on the one graph.

    ax2 = fig.add_subplot(gs1[1],sharex=ax1)
    TitleString = Coin1+' vs left axis, '+Coin2+' vs right axis'
    ax2.set_ylabel('Price (USD)', fontsize=14)
    ax2.set_title(TitleString, fontsize=12)
    trace1 = ax2.plot(PriceMatrix1['Days ago'], PriceMatrix1['Price (USD)'], c='black',label =Coin1)
    ax2b = ax2.twinx()
    trace2 = ax2b.plot(PriceMatrix2['Days ago'], PriceMatrix2['Price (USD)'], c='red',label =Coin2)
    ax2b.set_ylabel('Price (USD)', fontsize=14)
    ax2.legend(loc=2); ax2b.legend(loc=1)

    # Correlation fig.:
    CorrString = 'Pair correlation over the whole period: '+str(round(float(NumpyCorr[1,0]), 4))
    ax3 = fig.add_subplot(gs1[2],sharex=ax1)
    ax3.set_title(CorrString, fontsize=12)
    ax3.set_xlabel('Days in past before today', fontsize=14)
    ax3.set_ylabel('Correlation', fontsize=14)
    for i in range(numCCAvs):
        traceName = 'CC_'+str(int(CCAvs[i]))+'day'
        tracelabel = '$CC_{'+str(int(CCAvs[i]))+'d}$'
        r = (i/(numCCAvs-1)); g = 0; b = 1 - (i/(numCCAvs-1))
        LW = 1+(i*0.25)
        traceName = ax3.plot(MasterDF[traceName], c =(r, g, b), label = tracelabel, linewidth = LW)
    ax3.legend(loc='best', bbox_to_anchor=(1, 1))
    ax3.set_ylim(-1.1, 1.1)

    plt.show() # Show figure. Function will remain running until you close the figure. 
