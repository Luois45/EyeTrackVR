import pandas as pd
import numpy as np
import cv2
from pythonosc import udp_client
 
     
     
OSCip="127.0.0.1" 
OSCport=9000 #VR Chat OSC port
client = udp_client.SimpleUDPClient(OSCip, OSCport)
#higher intensity means more closed/ more white/less pupil

# HOW THIS WORKS:
# Here is my idea: 
# we get the intensity of pupil area from HSF crop, When the eyelid starts to close, the pupil starts being obstructed by skin which is generally lighter than the pupil. 
# This causes the intensity to increase. We save all of the darkest intensities of each pupil position to calculate for pupil movement. 
# ex. when you look up there is less pupil visible, which results in an uncalculated change in intensity even though the eyelid has not moved in a meaningful way. 
# We compare the darkest intensity of that area, to the lightest (global) intensity to find the appropriate openness state via a float.
fname = "test_list.txt"
data = pd.read_csv(fname, sep=",")

#TODO we need more pixel points for smooth operation, lets get this setup in hsrac and add a .25 or .33 range?

def intense(x, y, frame):
    upper_x = x + 25
    lower_x = x - 25
    upper_y = y + 25
    lower_y = y - 25
    frame = frame[lower_y:upper_y, lower_x:upper_x]

    xy = int(str(x) + str(y) + str(x+y))
    intensity = np.sum(frame)
    #print(intensity)
    changed = False
    try: #max pupil per cord
        dfb = data[data['xy']==xy].index.values.astype(int)[0] # find pandas index of line with matching xy value

        if intensity < data.at[dfb, 'intensity']: #if current intensity value is less (more pupil), save that
            data.at[dfb, 'intensity'] = intensity # set value
            changed = True
            print("var adjusted")
        
        else: 
            intensitya = data.at[dfb, 'intensity'] - 3 #if current intensity value is less (more pupil), save that
            data.at[dfb, 'intensity'] = intensitya # set value
            changed = True
          #  print("var inc", intensity, intensitya)


    except: # that value is not yet saved
        data.loc[len(data.index)] = [xy, intensity] #create new data on last line of csv with current intesity
        changed = True


    try: # min pupil global
        if intensity > data.at[0, 'intensity']: #if current intensity value is more (less pupil), save that NOTE: we have the 
            data.at[0, 'intensity'] = intensity # set value at 0 index
            changed = True
            print("new max", intensity)

        else:
            intensityd = data.at[0, 'intensity'] - 10 #continuously adjust closed intensity, will be set when user blink, used to allow eyes to close when lighting changes
            data.at[0, 'intensity'] = intensityd # set value at 0 index
            changed = True
            
    except: # there is no max intensity yet, create
        data.at[0, 'intensity'] = intensity # set value at 0 index
        changed = True
        print("create max", intensity)

    try:
        maxp = data.at[dfb, 'intensity']
        minp = data.at[0, 'intensity']
        #eyeopen = (intensity - minp) / (maxp - minp)
        eyeopen = (intensity - maxp) / (minp - maxp)
        eyeopen = 1 - eyeopen
        print(intensity, maxp, minp, x, y)
       # eyeopen = max(0.0, min(1.0, eyeopen))
      #  print(f"EYEOPEN: {eyeopen}")
        client.send_message("/avatar/parameters/RightEyeLidExpandedSqueeze", float(eyeopen)) # open r
        client.send_message("/avatar/parameters/LeftEyeLidExpandedSqueeze", float(eyeopen))
    except:
        print('[INFO] Something went wrong, assuming blink.')
        eyeopen = 0.0

    if changed == True:
        data.to_csv(fname, encoding='utf-8', index=False) #save file since we made a change



    return eyeopen

#vid = cv2.VideoCapture("http://192.168.1.43:4747/video")
#x = int(input("x"))
#y = int(input("y"))

#while(True):
      
 #   ret, frame = vid.read()
  
  #  cv2.imshow('frame', frame)
   # upper_x = x + 20
    #lower_x = x - 20
  #  upper_y = y + 20
   # lower_y = y - 20
    
  #  cropped_image = frame[lower_y:upper_y, lower_x:upper_x]
   # intense(x,y, cropped_image)

   # if cv2.waitKey(1) & 0xFF == ord('q'):
    #    break
  
#vid.release()
#cv2.destroyAllWindows()