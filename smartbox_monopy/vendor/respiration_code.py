# vendored code from 16-11-2022
# https://github.com/pmpf/Resp/blob/e7683d3aed0c96b93c87cc2f86444e33cc48727f/DataAnalysis/guardar.py

from time import sleep
from datetime import datetime
from scipy.signal   import butter, lfilter, welch
from numpy          import where
import numpy as np
import json

class Save:
    def __init__(self):
        self.sensor_1 = []
        self.sensor_2 = []
        self.count = 0
    def guardar(self,val, name):
        if name == '1':
            self.sensor_1.append(val)
            self.count = self.count +1
        elif name == '2':
            self.sensor_2.append(val)
    
def compute123(mongodb, save):
    while True:
        # print(len(save.sensor_2))
        if len(save.sensor_1) == 150 or len(save.sensor_2) == 150:
            print('################# COMPUTE #############################')
            rpm = computeResp(save.sensor_1,save.sensor_2)
            sesnor_json = {'sesnor_1': save.sensor_1,'sesnor_2': save.sensor_2}
            json_object = json.dumps(sesnor_json, indent=4)
            with open('row_data.json',"w") as json_file:
                json_file.write(json_object)
            save.sensor_1 = []
            save.sensor_2 = []
            mongodb.insert_sensors_collection('Respiratory Rate', rpm, datetime.now())
            save.count = 0

        

def powerSpectralDensit_fity( signal,  N_FFT = 10000000, 
                         BIAS_REMOVE = False, N_OVERLAP = 0.5, WINDOW_TYPE = 'hann',
                         AVERAGE = 'mean'):

    

    segmentLength = int(len(signal)/2)

    frequencies, power_spectral_density = welch(x        = signal,
                                                fs       = 10,
                                                # window   = WINDOW_TYPE,
                                                nperseg  = segmentLength,
                                                noverlap = int(N_OVERLAP* segmentLength),
                                                nfft     = N_FFT)
                                                # detrend  = BIAS_REMOVE,
                                                # average  = 'median')
    
    return frequencies, power_spectral_density

def computeMaxAmplitudeFrequency_1(frequencies, power_spectral_density):
    
    max_amplitude = max(power_spectral_density)
    max_index = where(power_spectral_density == max_amplitude)
    max_frequency     = frequencies[max_index]
    return max_amplitude, max_frequency*60

def filterSignal_1(signal, fs, FILTER_TYPE):
    
    nyq = 0.5 * fs 
    low = 0.17 / nyq #0.17
    high = 0.8 / nyq  # 2
    
    b,a = butter(5, high, btype='low', fs= fs)
    
    signal_filtered = lfilter(b, a, signal)

    return signal_filtered


def computeResp(s_1, s_2):
    print(s_1, s_2)
    fusion = []
    fusion_in_pro = []
    sensor_1 = filterSignal_1(s_1,10,'band')
    sensor_2 = filterSignal_1(s_2,10,'band')
    d_t = 15*10
    last = 0
    for i in range(0, d_t-3, 3):
        try:
            sensor_1_aux = np.array(sensor_1[i:i+3])
            sensor_2_aux = -1*np.array(sensor_2[i:i+3])
            d_s_1 = sensor_1_aux[-1]-sensor_1_aux[0]
            d_s_2 = sensor_2_aux[-1]-sensor_2_aux[0]
            
            if   d_s_1 > 0 and d_s_2>0:
                if last == 0:
                    # fusion.append(-1)
                    last =1
                if last == 1:
                    
                    fusion_in_pro = fusion_in_pro + list(sensor_1_aux + sensor_2_aux)
                    add_fusion = add_fusion + 1
                    # axs[1,0].plot(np.arange(0,len(fusion_in_pro)),fusion_in_pro)
                elif last == -1:
                    if len(fusion_in_pro) > 1:
                        fusion = fusion + list(normalization(fusion_in_pro))
                        # axs[1,1].plot(np.arange(0,len(fusion)),fusion)
                        fusion_in_pro = []
                        last = 0
                        add_fusion = 0
                    
                
            elif d_s_1 < 0 and d_s_2 < 0:
                if last == 0:
                    last =-1
                    # fusion.append(1)
                if last == -1:
                        
                    fusion_in_pro = fusion_in_pro + list(sensor_1_aux + sensor_2_aux)
                    add_fusion = add_fusion + 1
                    # axs[1,0].plot(np.arange(0,len(fusion_in_pro)),fusion_in_pro)
                    
                elif last == 1:
                    if len(fusion_in_pro) > 1:
                        fusion = fusion + list(normalization(fusion_in_pro))
                        # axs[1,1].plot(np.arange(0,len(fusion)),fusion)
                        fusion_in_pro = []
                        last = 0
                        add_fusion = 0
            # axs[0,0].plot(np.arange(0,len(sensor_1_aux)),sensor_1_aux)
            # axs[0,1].plot(np.arange(0,len(sensor_2_aux)),sensor_2_aux)
        except:
            pass
        
        
    
        #plt.pause(0.05)
    if len(fusion_in_pro)>0:
        fusion = fusion + list(normalization(fusion_in_pro))
        
    
    #sensor_3 = filterSignal_1(sensor_1[0:145]*sensor_1[0:145] + sensor_2[0:145]*sensor_1[0:145] + sensor_2[0:145]*sensor_2[0:145],10,'band')
    f_f, p_f = powerSpectralDensit_fity(fusion)
    
    amp_f,freq_f =computeMaxAmplitudeFrequency_1(f_f,p_f)
    print(freq_f)
    return freq_f[0]



def normalization(data):
    
    data_min = min(data)
    data_max = max(data)
    
    signal_normalize = [(x - data_min)/(data_max-data_min) for x in data]
    
    return signal_normalize