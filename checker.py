url_list = {"n6_32_blue":r'https://play.google.com/store/devices/details?id=nexus_6_blue_32gb', 
            #"n6_32_white":r'https://play.google.com/store/devices/details?id=nexus_6_white_32gb',
            #"n6_64_blue":r'https://play.google.com/store/devices/details?id=nexus_6_blue_64gb',
            #"n6_64_white":r'https://play.google.com/store/devices/details?id=nexus_6_white_64gb',
            #"n5_16_black":r'https://play.google.com/store/devices/details?id=nexus_5_black_16gb',
            #"n5_32_black":r'https://play.google.com/store/devices/details?id=nexus_5_black_32gb',
            #"n9_32_wifi_black":r'https://play.google.com/store/devices/details?id=nexus_9_black_32gb_wifi',
            #"n9_32_lte_black":r'https://play.google.com/store/devices/details?id=nexus_9_black_32gb_lte',
            #"n9_32_wifi_white":r'https://play.google.com/store/devices/details?id=nexus_9_white_32gb_wifi',
            }



haltfile = "NORUN"
log_suffix = "logfile"
state_suffix = "state"

import os
import sys
import requests
from bs4 import BeautifulSoup

def write_state(device, datadict, file):
    with open(device+'.'+file,"wt") as fp:
        fp.write("[date]:{date}\n".format(**datadict))
        fp.write("[device]:{device}\n".format(device=device))
        fp.write("[clickable-button]:{clickable-button}\n".format(**datadict))
        fp.write("[inventory-status]:{inventory-status}\n".format(**datadict))
        fp.write("[shipping-status]:{shipping-status}\n".format(**datadict))
        fp.write("[additional-info]:{additional-info}\n".format(**datadict))
        
def read_state(file):
    statedict = dict()
    with open(file,"rt") as fp:
        for line in fp.readlines():
            statedict[line.split(']')[0][1:]] = ':'.join(line.split(':')[1:])
    return statedict


def output(device, datadict,file):
    with open(device+'.'+file,"at") as fp:
        fp.write("{date}\n".format(**datadict))
        fp.write("[device]:{device}\n".format(device=device))
        fp.write("[clickable-button]:{clickable-button}\n".format(**datadict))
        fp.write("[inventory-status]:{inventory-status}\n".format(**datadict))
        fp.write("[shipping-status]:{shipping-status}\n".format(**datadict))
        fp.write("[additional-info]:{additional-info}\n".format(**datadict))
        fp.write("\n")
        
# check for norun flag
if os.path.exists(haltfile):
    print haltfile, "found, not running"
    sys.exit()
else:
    # main loop now

    scan_results = dict()
    
    # fetch URL and parse
    for device in url_list.keys():

        req = requests.get(url_list[device])
        bs = BeautifulSoup(req.text)
        
        play_button = bs.find('span','play-button') # only one span with this class against it
        button_pressable = False
        if 'disabled' not in play_button.attrs['class']:
            button_pressable = True
        
        inventory_status = bs.find('div', 'id-hardware-inventory-status')
        
        shipping_status = bs.find('div', 'shipping-status')
        try:
            shipping_status = "("+shipping_status.find('div').find('div').find('div').text+")"
        except:
            shipping_status = "(unknown)"
            
        additional_info = bs.find('div', 'hardware-promotion')
        try:
            additional_info = additional_info.find('div', 'content').text
        except:
            additional_info = ""
        scan_results[device] = {"date":req.headers['date'],
                                "clickable-button":button_pressable,
                                "inventory-status": inventory_status.attrs['data-availability'],
                                "shipping-status":shipping_status,
                                "additional-info":additional_info}

        output(device, scan_results[device],log_suffix)
        
        
    # data gathering done, lets see what's new..
    state_change = False
    message_string = ""
    for device in url_list.keys():
        
        try:
            state_dict = read_state(device+'.'+state_suffix)
            for key in scan_results[device].keys():
                if key != 'date':
                    if  str(scan_results[device][key]).strip() != str(state_dict[key]).strip():
                        message_string += "[{device}]:[{key}]\n(new){new}\n(old){old}\n\n".format(device = device, key=key, new=scan_results[device][key], old = state_dict[key])
        except IOError:
            state_dict = None
        
        write_state(device, scan_results[device],state_suffix)


    '''
    for device in url_list.keys():
        # if we have any clickable buttons 
        if scan_results[device]['clickable-button']:
            message_string += "{device}:AVAIL,{invstat}|".format(device=device, invstat = scan_results[device]['inventory-status'])
    '''
    
    if message_string != "":
        import smtplib
        from email.mime.text import MIMEText
        
        # we could also have an SMS pathway here if we wanted, but email may be better?
        # obviously, fill in your own credentials here and 

        msg = MIMEText(message_string)
        msg['Subject'] = "Autogen notification from stock checker, something's changed!!"
        msg['From'] = "me@fastmail.fm"   
        msg['To'] = "you@fastmail.fm"
        
        messaging = smtplib.SMTP_SSL('mail.messagingengine.com', 465)
        messaging.login("me@fastmail.fm", "your cleartext goes here")
        messaging.sendmail(msg['From'], [msg['To']], msg.as_string())
        messaging.quit()

