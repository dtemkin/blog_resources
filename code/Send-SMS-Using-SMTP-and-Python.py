
# coding: utf-8

# ## Sending SMS via SMTP
# 
# Recently, I was at a Python meetup and I saw a couple projects that involved send text messages to users. Both used twilio.com API which is perfectly fine but unfortunately has only a free trial version. I thought a more permanent solution would be to use the builtin "smtplib" library in Python to send messages to users by using the phone company's SMS or MMS Gateway.
# 
# There are only two catches to this method, 1) the person will not be text back and would have to send responses via email and 2) the users would need to provide their cell carriers unless you wanted to pay for another api like https://www.carrierlookup.com/ which offers $.01 per lookup when using their API. But, since this does defeat the notion of "free" we will assume the user provides their carrier info.
# 
# As always you can download the jupyter notebook here, or the python file here.

# In[2]:

import smtplib
import requests
import csv

subject = ""
msg = ""
gmail_account = {"user":None, "password": None}


def mail2textmsg(carrier, msgtype="sms", phone_num):
    
    gateway = gatewaylookup(carrier=carrier, typ=msgtype)
    ph = phone_num.replace("-","")
    ph = ph.replace("(","")
    ph = ph.replace(")","")
    ph = ph.replace("+","")
    
    if len(ph) == 10:
        to = '%s@%s' % (ph, gateway)
    
        gmail_user = gmail_account["username"]
        gmail_pwd = gmail_account["password"]

        smtpserver = smtplib.SMTP("smtp.gmail.com",587)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo
        smtpserver.login(gmail_user, gmail_pwd)
        header = 'To:' + ph + '\n' + 'From:  ' + gmail_user + '\n' + 'Subject:%s \n'
        print(header)
        mesg = "\n".join([header, "RE: %s" % subject, ' %s \n\n' % msg])
        smtpserver.sendmail(gmail_user, ph, mesg)
        print('mail sent!')
        smtpserver.close()
    else:
        print("Phone Number is Invalid Length. Should only include 10 digits.")
        
def gatewaylookup(carrier, typ):
    gatewaylist = "https://cdn.rawgit.com/just-dantastic/blog/d20dbeab/data/textmsg_carriers.ls"
    fields = ["provider","sms","mms","other"]
    req = requests.get(gatewaylist)
    readr = csv.DictReader(req.text, fieldnames=fields)
    if carrier.lower() in [p.lower() for p in row["provider"]]:
        for row in readr:
            if carrier.lower() == row["provider"].lower():
                return row[typ]
            else:
                pass
    else:
        print("Carrier Name is Invalid. Please be sure to remove all not alphanumeric characters.")
    

