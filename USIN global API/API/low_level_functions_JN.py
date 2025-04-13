import time
import json
import numpy as np
import pickle
from ubertone.apf04_driver import Apf04Driver
from ubertone.apf04_measures import extract_measures


def plot_echoTimeseries(data,ngate,ax):
    ax.plot(data['time'],data['echo'][:,ngate])
    ax.set_xlabel('t in s')
    ax.set_ylabel('echo amplitude')
    
def plot_velocityTimeseries(data,ngate,ax):
    ax.plot(data['time'],data['velocity'][:,ngate])
    ax.set_xlabel('t in s')
    ax.set_ylabel('U in m/s')
    
def plot_echoProfile(data,n_profile,ax):
    ax.plot(data['x'],data['echo'][n_profile])
    ax.set_title('ECHO')
    ax.set_xlabel('x in m')
    ax.set_ylabel('echo amplitude')

def plot_velocityProfile(data,n_profile,ax):    
    ax.plot(data['x'],data['velocity'][n_profile])
    ax.set_title('VELOCITY')
    ax.set_xlabel('x in m')
    ax.set_ylabel('U in m/s')
    
def save_data(fileName,myData,boardSettings):
    with open(fileName, "wb") as datafile:
        pickle.dump([myData,boardSettings] , datafile)
        
        
def load_data(fileName):
    Data,dataSettings=pickle.load( open( fileName , "rb" ) )
    #print all settings final values
    for j in dataSettings.keys():
        print(j,'=',dataSettings[j])
    return Data,dataSettings

def get_profile(apf_instance,use_config,Nprofile):
    # select the configuration on the board you want to use:
    apf_instance.select_config(use_config)
    # check the parameters of the active configuration
    apf_instance.act_check_config()
    #Read the checked config you have written on the board, store it for the extraction of the profiles.
    _config_=apf_instance.read_config(use_config)
    
    
    # Get measurement duration in order to define the timeout 
    timeout = _config_.get_bloc_duration()
    print ("timeout = %f"%timeout)
    
    startTs = time.time()
    tmp_=startTs
    dt=[]
    raw_data=[]
    
    myData={}
    myData['velocity']=[]
    myData['echo']=[]
    myData['snr']=[]
    myData['std']=[]
    myData['time']=[]
    myData['f_sampling']=[]
    time_=[]
    
    for _ in range (Nprofile):
        # Trigger the measurement of one profile, the function is released
        # when the data are ready
        apf_instance.act_meas_profile(0.2 + 1.1*timeout)
        # Read the profile data (velocities, echo amplitudes ...)
        _raw_data=apf_instance.read_profile(_config_.n_vol)
        #Store the raw data into a list
        raw_data.append(_raw_data)  
        myData['f_sampling'].append(time.time()-tmp_)
        tmp_=time.time()
        
    stopTs = time.time()
    timeDiff = stopTs  - startTs
    print ("for %d profiles : %f sec"%(Nprofile, timeDiff))
    

    
    #format the data
    for raw_profile in raw_data:
        _tmp=extract_measures(raw_profile, _config_)
        myData['velocity'].append(_tmp['velocity']) 
        myData['echo'].append(_tmp['amplitude']) 
        myData['snr'].append(_tmp['snr']) 
        myData['std'].append(_tmp['std']) 
        time_.append(_tmp['timestamp']) 
        

    for t_ in time_:
        tmp=t_-time_[0]
        myData['time'].append(tmp.total_seconds()) 
    
    
    for key in myData.keys():
        myData[key]=np.array(myData[key])
        
        
    sound_speed=apf_instance.read_sound_speed() #read_sound_speed from the board
    mySettings=_config_.to_dict(sound_speed)
    x=np.linspace(0,mySettings['nb_gates'],mySettings['nb_gates'])
    x=mySettings['position_first_gate']+x*mySettings['gate_distance']
    myData['x']=x
    
    return myData

def load_settings_fromFile(fileName):
    # Read settings file
    with open(fileName) as json_file:
        settings = json.loads(json_file.read())
    print('###########################################')
    print('\n')
    print('Loaded settings')
    print('\n')
    for k in settings.keys():
        print(k,': ',settings[k])
    print('###########################################')

    return settings 



def load_settings_fromBoard(apf_instance,numConfig):
    #read config 0,1 or 2 from the board.
    config=apf_instance.read_config(numConfig)      #read the config from the board: you can select '0','1' opr '2'
    sound_speed=apf_instance.read_sound_speed() #read_sound_speed from the board
    if sound_speed==0:
        print('ERROR: Sound speed on the board is set to zero')
        print('load a config from file and write it on the board')
        return
    else:
        settings=config.to_dict(sound_speed)   #translate the config into settings. 
        settings['soundspeed']=sound_speed
        settings['gate_size']=settings['soundspeed']/(2.*settings['f_emission'])*settings['nb_cycles_per_emission']
        settings['gate_distance']=settings['gate_size']*settings['overlap']
        settings['dynamicRange']=settings['soundspeed']*settings['prf']/2/settings['f_emission'] #dynamic range of velocity
        settings['v_max']=settings['v_min']+settings['dynamicRange']
    
        print('###########################################')
        print('\n')
        print('Loaded settings')
        print('\n')
        for k in settings.keys():
            print(k,': ',settings[k])
        print('###########################################')
        return settings

def update_settings(settings):
    settings['gate_size']=settings['soundspeed']/(2.*settings['f_emission'])*settings['nb_cycles_per_emission']
    settings['gate_distance']=settings['gate_size']*settings['overlap']
    settings['dynamicRange']=settings['soundspeed']*settings['prf']/2/settings['f_emission'] #dynamic range of velocity
    # settings['v_min']=settings['velocity_offset']-settings['dynamicRange']/2 #I center the dynamic range on 0m/s
    settings['v_max']=settings['v_min']+settings['dynamicRange']
        
    return settings


def save_settings_toFile(fileName,settings):
    # write settings file
    with open(fileName, 'w') as json_file:
        json.dump(settings,json_file)
    return  

def write_settings_toBoard(apf_instance,settings,numConfig):     
    # Create ConfigHw instance 
    myConfig= apf_instance.new_config() # create the instance
    #create config from settings
    myConfig.set(settings) #fill the config with the settings

    #write soundSpeed on the board as set in your settings
    if settings['soundspeed']==0:
        print('ERROR: sound speed is zero')
        return
    else:
        apf_instance.write_sound_speed(settings['soundspeed'], False)
        # Stop any current action (in case of)
        apf_instance.act_stop()

        #upload config on the board:
        #you can write 3 configs on the board, set n_config=0,1,2
        apf_instance.write_config (myConfig, numConfig)

        #check the config and adjust target values to board compatible values
        apf_instance.act_check_config()
        #your target settings may not be valid values for the registers. We now compare your target settings with 
        #read the configuration from the board
        config_board=apf_instance.read_config(numConfig)
        soundspeed=apf_instance.read_sound_speed()
        print('\n')
        print('Uploaded and checked configuration')
        print('\n')
        effective_settings=config_board.to_dict(soundspeed)

        effective_settings['dynamicRange']=effective_settings['soundspeed']*effective_settings['prf']/2/effective_settings['f_emission'] #dynamic range of velocity
        effective_settings['v_max']=settings['v_min']+effective_settings['dynamicRange']
        
        #print all settings final values
        for j in settings.keys():
            if j in effective_settings.keys():
                if effective_settings[j]!=settings[j]:                   
                    print(j,'=',settings[j],"- ADJUSTED TO:",effective_settings[j])
                else:
                    print(j,'=',settings[j])
            else: print(j,'=',settings[j])
        
        return effective_settings