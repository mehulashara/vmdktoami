#############################################################################
# Import required libraries
#############################################################################
import boto3,sys,json,os,time,requests,wget,getpass,psutil,socket
from boto.s3.key import Key
from clint.textui import colored

##############################################################################
# Start script
##############################################################################
def bytes2human(n):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n

def is_connected():
	REMOTE_SERVER = "www.mehul.com"
	try:
		host = socket.gethostbyname(REMOTE_SERVER)
		s = socket.create_connection((host, 80), 2)
		return "Connected"
	except:
		pass
		return "Not conneted"

### start main function
def main():
	print(colored.cyan('##########----------------------------------------------------------##########\n########## WELCOME TO AWS VM IMPORT TOOL FOR DELL EMC DPS SOLUTIONS ##########\n##########----------------------------------------------------------##########'))
	print(colored.yellow('\nThis tool can be used to import on-premise DPS VMware solutions to AWS cloud. \n\nRequiremnets: \n1. Internet connectivity \n2. OS File path for vmdks \n3. AWS Cerdentials with AdministratorAccess and AWS region\n'))
	print(colored.yellow('Checking internet connectivity ...'))
	print(colored.green(is_connected()))
	print(colored.yellow('\nAvailable OS Partitions:'))
	templ = "%-17s %8s %8s %8s %5s%% %9s  %s"
	print(colored.yellow(templ % ("Device", "Total", "Used", "Free", "Use ", "Type", "Mount")))
	for part in psutil.disk_partitions(all=False):
		if os.name == 'nt':
			if 'cdrom' in part.opts or part.fstype == '':
				continue
		usage = psutil.disk_usage(part.mountpoint)
		print(colored.yellow(templ % ( part.device, bytes2human(usage.total), bytes2human(usage.used), bytes2human(usage.free), int(usage.percent), part.fstype, part.mountpoint)))
	
	path = os.path
	var = str((os.path.splitext(str(path)[23]) + os.path.splitext(str(path)[24]) + os.path.splitext(str(path)[25])))

#	drive = input('\nDo you wish to use device ' + var[2] + ':\\ Y/N [Y]:')
#	drive = var[2]
#	drive = input('\nEnter the device where tarball or vmdk has been downloaded. Example C, D, etc: ')
#	mypath = (drive[0].upper() + ":\\NVE-AWS")
#	print(colored.yellow("\nCreating directory "+mypath))
#	if not os.path.isdir(mypath):
#		os.makedirs(mypath)
	paths = input('\nEnter full path to vmdk files: ')
	if not os.path.exists(paths):
		print(colored.yellow("Invalid path entered. Exiting..."))
		sys.exit()
		
	idea = 1
	k = int(0)
	dict = {}
	mylist =[]
	print(colored.yellow("\nLooking for vmdk files under "+paths))
	for file in os.listdir(paths):
		if file.endswith(".vmdk"):
			fullpath = paths+"\\"+file
			print(colored.yellow((fullpath) + "  " + str(os.path.getsize(fullpath) >> 20) + " M"))
			dict.update({fullpath:(str(os.path.getsize(fullpath) >> 20))})
			diskis = file
			k = k + 1
	
	if k == 0:
		print(colored.red("No vmdk files found under" + paths + ". Exiting..."))
		sys.exit()
	elif k >= 2 :
		print(colored.green("Found multiple vmdk files under " + paths))
	
	if  k == 1:
		mylist = [(diskis)]
	else:
		for i in range(k):
			data=str(input("Enter disk " + str(idea) + ":"))
			if data == "":
				print(colored.red("Invalid Input. Exiting..."))
				sys.exit()
			mylist.append(data)
			idea =  idea + 1
	
	print(mylist)
	print(colored.yellow('\nPlease enter choice of what you wish to import:\n1. Cloudboost		\n2. NetWorker Virtual Edition		\n3. Exit \n')) 
	
	idea=0
	count=int(0)
	length = len(dict)
	while count==0 or count==1 or count==2 or count==3: 
		x = ord(input('Enter your choice [ 1 | 2 | 3 ]: '))
		if x==49 or x==50:
			'''
			# check aws is installed correctly
			print('1. Verifying AWS-CLI installation')
			try:
				cmd = "aws --version"
				returned_value = os.system(cmd)
				print('Returned value: ', returned_value)
				if returned_value == 1:
					print('\nAWS-CLI is not installed on this machine. \nCreating directory ' + mypath + '\nDownloading AWS CLI msi to ' + mypath)
					if not os.path.isdir(mypath):
						os.makedirs(mypath)
					url = "https://s3.amazonaws.com/aws-cli/AWSCLI64.msi"  
					wget.download(url, mypath)
					print('\n\nInstalling AWS-CLI\n')
					os.system('msiexec /i C:\\NVE-AWS\\AWSCLI64.msi /quiet /qn /norestart /log C:\\NVE-AWS\\aws-cli-install.log')
					if os.system('aws --version') == 0:
						print("\nAWS-CLI is successfully installed on this OS \nConfiguring AWS CLI using command aws --configure")
				else:
					print(colored.yellow('\nAWS-CLI is already installed on this machine \nConfiguring AWS CLI using command aws --configure'))
			'''	
			try:
				print(colored.yellow("Characters are hidden"))
				ACCESS_KEY = getpass.getpass('Enter AWS Access Key ID: ')
				SECRET_KEY = getpass.getpass('Enter AWS Secret Access Key: ')
				region = input('Default region name ( us-east-2	| us-east-1 | us-west-1 | us-west-2 | ap-northeast-1 | ap-northeast-2 | ap-northeast-3 | ap-south-1	|ap-southeast-1	|ap-southeast-2 | ca-central-1 | cn-north-1	| cn-northwest-1 | eu-central-1	| eu-west-1	| eu-west-2	| eu-west-3 | sa-east-1 ) :')
				#format = input('Default output format:')
				bucket_name = 'dps-aws-{}'.format(int(time.time()))
				s3client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
				try:
					uploaded =[]
					s3client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={ 'LocationConstraint': region })
					print (colored.yellow('1. Creating a new S3 bucket with name: {}'.format(bucket_name)))
					print (colored.yellow('2. Uploading .vmdk file from ' + paths + ' to S3 bucket {}'.format(bucket_name)))
					for b in range(len(mylist)):
						filename = mypath + str(mylist[b])
						print(filename)
						print(colored.yellow("Uploading " + filename))
						uploadname = "dps-aws-00"+str(b)+".vmdk"
						s3client.upload_file(filename, bucket_name, uploadname)
						uploaded.append[(uploadname)]
					
#					print (colored.yellow('3. Files uploaded to S3 bucket {}' .format(bucket_name)))
					print(uploaded)
					sys.exit()
					
					bucket = boto3.resource('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY).Bucket(bucket_name)
					bucket.objects.all().delete()
					bucket.delete()
					print (colored.yellow('5. Deleted S3 bucket name: {}' .format(bucket_name)))
					print(colored.yellow('6. Please download, copy and extract vmdk from tar file to '+ mypath + ' and once the file is copied hit enter'))
					input
					print(colored.yellow('7. Checking .vmdk files available under ' + mypath))
					idea = 1
					k = int(0)
					for file in os.listdir(mypath):
						if file.endswith(".vmdk"):
							diskis = file
							k = k + 1
							print(k)
						elif k >= 2 :
							print(colored.red("Found multiple vmdk files under " + mypath + ". Expected one file. Exiting !!"))
							sys.exit()
					if k == 0:
							print(colored.red("No vmdk files found under" + mypath + ". Exiting..."))
							sys.exit()
					elif k == 1:
							print(colored.yellow("8. Using file " + diskis + " for AMI conversion"))

				finally:
						if idea == 0:
							print(colored.red("Invalid AWS Cerdentials or Region. Exiting..."))
						
			except:
				sys.exit()
		elif x==51:
			print (colored.yellow("Exiting..."))
			sys.exit()
		else:
			print(x)
			count=count+1
			if count>3:
				print(colored.red("Too many invalid attempts. Good Bye !!"))
				sys.exit()
			print("Attempt "+ str(count) + ": Kindly only enter options 1, 2 OR 3")

if __name__ == "__main__":  
	main()
	sys.exit(main())
