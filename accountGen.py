#!/usr/bin/env python

from pprint import pprint
import csv
import collections
import datetime
import time
import subprocess
import sys
import os
import argparse
import pwd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import MySQLdb

# ARGUMENTS TO PASS WHEN INVOKING SCRIPT
parser = argparse.ArgumentParser(description='given a csv of name and email, creates an account and email credentials to student; dependencies include python, makepasswd, and email')
parser.add_argument('-f','--file', help='required-name of csv file', type=str)
args = vars(parser.parse_args())

csv_file = args['file']
msg = MIMEMultipart('alternative')

# Below Variables to set BEFORE FIRST TIME USE ******
me = ""
you = ""
cc = ""
msg['Subject'] = ''
office365_user = ''
office365_pwd = ''
# **************************************************

# Grab CSV data
with open(csv_file, 'rU') as f:
    reader = csv.reader(f)
    for row in reader:
        try:
            last_name = row[0]
            first_name = row[1]
            accessID = row[2]
            accessID = accessID.rstrip('\n')

            # Check and make sure account doesn't already exist
            try:
                pwd.getpwnam(accessID)
                print (accessID+" already exists on the system")
            except KeyError:
            # create password, output it, and save it as variable
                password = subprocess.Popen("makepasswd", stdout=subprocess.PIPE, shell=True)
                (password_out, password_error) = password.communicate()
                print password_out
                password_out = password_out.rstrip('\n')
            # Create account
                os.system('useradd -m -s /bin/bash '+accessID+' -K UMASK=026')
                os.system('echo '+accessID+':'+password_out+' | chpasswd')

            # Create MySQL db
                db = MySQLdb.connect(host='localhost', user='root', passwd='PASSWORD', port=3306)
                cursor = db.cursor()

                st1 = "CREATE USER %s@'localhost' IDENTIFIED BY %s"
                st2 = "GRANT USAGE ON *.* TO %s@'localhost' IDENTIFIED BY %s WITH MAX_QUERIES_PER_HOUR 0 MAX_CONNECTIONS_PER_HOUR 0 MAX_UPDATES_PER_HOUR 0 MAX_USER_CONNECTIONS 0;"
                st3 = "CREATE DATABASE IF NOT EXISTS %s;"
                st4 = "GRANT ALL PRIVILEGES ON {0}.* TO {1}@'localhost';".format(accessID, accessID)
                cursor.execute(st1, (accessID, password_out))
                cursor.execute(st2, (accessID, password_out))
                cursor.execute(st3 % accessID)
                cursor.execute(st4)
                db.commit()
                db.close()

            # Send email

                msg['From'] = me
                msg['To'] = you
                msg['BCC'] = cc

                # Create the body of the message (a plain-text and an HTML version).
                text = ""
                html = """
                <html>
                <head>
                <title>Login credentials</title>
                </head>
                <body>
                    {first_name},<br/><br/>

                      <p>Your username and password are listed below.</p><br/>
                      <p>username: {accessID}<br/>
                      password: {password_out}<br/>

                </body>
                </html>
                """.format(first_name=first_name,accessID=accessID,password_out=password_out)
                

                # Record the MIME types of both parts - text/plain and text/html.
                part1 = MIMEText(text, 'plain')
                part2 = MIMEText(html, 'html')

                # Attach parts into message container.
                msg.attach(part1)
                msg.attach(part2)



                # Send the message via our own SMTP server, but don't include the
                # envelope header.
                s = smtplib.SMTP('',PORT_NUMBER)
                s.ehlo()
                s.starttls()
                s.ehlo()
                s.login(office365_user,office365_pwd)
                s.sendmail(me, [you,cc], msg.as_string())
                s.quit()
                print "email sent to ",you

        except Exception, e:
            # Catch all the errors that might stop the script, append them to an error file, and then move onto the next url
            print e.__doc__
            print e.message
            now = datetime.datetime.now()
            error_file = now.strftime("%Y_%m_%d")
            myfile = open("user_gen_errors_"+error_file+".txt", "a")
            myfile.write("Couldn't complete user account creation process for "+first_name+" "+last_name+", "+accessID)
            myfile.write(e.message)
            myfile.close()
            continue
