#!/usr/bin/env python

import csv
import datetime
import subprocess
import os
import argparse
import pwd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ARGUMENTS TO PASS WHEN INVOKING SCRIPT
parser = argparse.ArgumentParser(description='given a csv of last name, first name, and WSU accessID, creates an account and email credentials to student; Note: since these credentials are emailed out, they should be ones that either be changed upon login (i.e. mandatory password reset), accounts that are not privy to sensitive information, and/or accounts that are only to systems that contain or have to access to little to no sensitive data.')
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

			# Check and make sure account doesn't already exist
			try:
				pwd.getpwnam(accessID)
				print (accessID+" already exists on the system")
			except KeyError:
			# create password, output it, and save it as variable
				password = subprocess.Popen("makepasswd", stdout=subprocess.PIPE, shell=True)
				(password_out, password_error) = password.communicate()
				print password_out
			# Create account
				os.system('useradd -m -s /bin/bash '+accessID)
				os.system('echo '+accessID+':'+password_out+' | chpasswd')

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
