#############################################################################
# Import required libraries
#############################################################################
import boto3,os,time,getpass,psutil,socket,colored,sys
#from boto.s3.key import Key
from clint.textui import colored
##############################################################################
# Start script
##############################################################################
def available_partitions():
	templ = "%-17s %8s %8s %8s %5s%% %9s  %s"
	print(colored.yellow('\nAvailable OS Partitions:'))
	print(colored.yellow(templ % ("Device", "Total", "Used", "Free", "Use ", "Type", "Mount")))
	for part in psutil.disk_partitions(all=False):
		if os.name == 'nt':
			if 'cdrom' in part.opts or part.fstype == '':
				continue
		usage = psutil.disk_usage(part.mountpoint)
		print(colored.yellow(templ % ( part.device, bytes2human(usage.total), bytes2human(usage.used), bytes2human(usage.free), int(usage.percent), part.fstype, part.mountpoint)))

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
	REMOTE_SERVER = "www.amazon.com"
	print(colored.yellow('Checking internet connectivity ...'))
	try:
		host = socket.gethostbyname(REMOTE_SERVER)
		s = socket.create_connection((host, 80), 2)
		return "Connected"
	except:
		pass
		print(colored.red('Not conneted. Exiting...'))
		sys.exit()
		return "Not conneted"
		ef s3_controls(s3, bucket_name, region, paths, s3_upload_disks, vmdk_file_names, delete):
	if delete == 0:
		try:
			s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={ 'LocationConstraint': region })
			print(colored.yellow('1. Creating a new S3 bucket with name: {}'.format(bucket_name)))
			print(colored.yellow('2. Uploading .vmdk files from ' + paths + ' to S3 bucket {}'.format(bucket_name)))
			k=0
			for i in s3_upload_disks:
				s3.Object(bucket_name, vmdk_file_names[k]).put(Body=open(str(s3_upload_disks[k]), 'rb'))
				k = k + 1
			print(colored.yellow('3. Files uploaded to S3 bucket {}' .format(bucket_name)))
		except:
			return 0
	else:	
		bucket = s3.Bucket(bucket_name)
		for key in bucket.objects.all():
			key.delete()
		bucket.delete()
		print(colored.yellow('5. Deleted S3 bucket name: {}' .format(bucket_name)))
		return 1

def ami_convert(ec2, s3_upload_disks, bucket_name, vmdk_file_names):
	try:
		disk_description = ["First Disk", "Second Disk", "Third Disk", "Fourth Disk", "Fifth Disk", "Sixth Disk", "Seventh Disk", "Eighth Disk","Nineth Disk", "Tenth Disk"]
		disk_containers=""
		i = 1
		while i <= len(s3_upload_disks):
			disk_containers += "{'Description':'"+ disk_description[i-1] + "', 'Format':'vmdk', 'UserBucket':{'S3Bucket':'" + bucket_name + "', 'S3Key':'" + vmdk_file_names[i-1] + "'}},"
			i += 1
#		print(disk_containers)
		ami_import = "ec2.import_image(Description='Coverted using Python BOTO3', LicenseType='Auto', DiskContainers=[" + disk_containers[:-1] + "], DryRun=False, RoleName='vmimport')"
#		ami_import  = "ec2.import_image(Description='Coverted using Python BOTO3', LicenseType='Auto', DiskContainers=[{'Description': 'First Disk', 'Format': 'vmdk', 'UserBucket': {'S3Bucket': 'nve-aws','S3Key': 'disks/AWS-NVE-18.1.0.21-disk1.vmdk'}}], DryRun=False, RoleName='vmimport')"
		ami_response = eval(ami_import)
		print(colored.yellow('4. Importing AMI'))
		return ami_response
	except:
		sys.exit()

# start main function
def main():
	print(colored.cyan('##########----------------------------------------------------------##########\n########## 		WELCOME TO AWS VM IMPORT TOOL  		    ##########\n##########----------------------------------------------------------##########'))
	print(colored.yellow('\nPurpose:\nThis tool can be used to import on-premise vMware Virtual Machines to AWS cloud and migrate workloads to AWS.\nRequiremnets: \n1. Internet connectivity \n2. OS absolute path for vmdk \n3. AWS service account with AdministratorAccess and AWS region\n'))
	print(colored.green(is_connected()))
	available_partitions()
	paths = input('\nEnter absolute path to vmdk file: ')
	if not os.path.exists(paths):
		print(colored.yellow("Invalid vmdk file. Exiting..."))
		sys.exit()
	
	k = int(0)
	myfiles, files_vmdk, s3_upload_disks, vmdk_file_names = [], [], [], []
	fullpath=""
	print(colored.yellow("\nLooking for vmdk files under "+paths))

	for file in os.listdir(paths):
		if file.endswith(".vmdk"):
			fullpath = paths+"\\"+file
			myfiles.append(fullpath)
			print(colored.yellow((fullpath) + "  " + str(os.path.getsize(fullpath) >> 20) + " M"))
			diskis = file
			k = k + 1
	
	if k == 0:
		print(colored.red("No vmdk files found under " + paths + " Exiting..."))
		sys.exit()
	elif k >= 2 :
		print(colored.green("Found multiple vmdk files under " + paths))
	if  k == 1:
		s3_upload_disks.append(fullpath)
		vmdk_file_names.append(os.path.basename(fullpath))
	else:
		idea=1
		for i in range(k):
			data=str(input("Enter disk " + str(idea) + " absolute path:"))
			vmdk_file_names.append(os.path.basename(data))
			if data == "":
				print(colored.red("Invalid Input. Exiting..."))
				sys.exit()
			s3_upload_disks.append(data)
			idea =  idea + 1
	idea=0
	count=int(0)
	try:
		print(colored.yellow("Characters are hidden"))
		ACCESS_KEY = getpass.getpass('Enter AWS Access Key ID: ')
		SECRET_KEY = getpass.getpass('Enter AWS Secret Access Key: ')
		region = input('Default region name ( ap-south-1 ): ')
		bucket_name = 'aws-{}'.format(int(time.time()))
		ec2 = boto3.client('ec2', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=region)
		session = boto3.session.Session(aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=region)
		s3 = session.resource('s3')
		try:
			s3_controls(s3, bucket_name, region, paths, s3_upload_disks, vmdk_file_names, 0)		
			ami_responses = ami_convert(ec2, s3_upload_disks, bucket_name, vmdk_file_names)
#			print(ami_responses)
#			print("TaskID is")
#			TaskID = str(ami_response['ImportTaskId'])
#			time.sleep(10)
#			print(colored.yellow(TaskID))
#			StatusMessage = str(ami_response['StatusMessage'])
#			print("Status Message is ")
#			print(colored.yellow(StatusMessage))
			reply = str(input('Do you want to retain S3 bucket: ' + bucket_name + ' Y/N: ')).lower().strip()
			if reply[0] == 'y':
				print(colored.green("Ok"))
				idea = 1
			elif reply[0] == 'n':
				idea = s3_controls(s3, bucket_name, region, paths, fullpath, s3_upload_disks, 1)
			else:
				print(colored.red("Please only enter Y/N "))
				idea = 1
#			idea = 1
		finally:
			if idea == 0:
				print(colored.red("Invalid AWS Cerdentials or Region. Exiting..."))
	except:
		sys.exit()
if __name__ == "__main__":
	main()
#	sys.exit(main())
