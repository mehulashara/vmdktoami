#############################################################################
# Import required libraries
#############################################################################
import boto3,sys,json,os,time,requests,wget,getpass,psutil,socket,colored
#from boto.s3.key import Key
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
	REMOTE_SERVER = "www.amazon.com"
	try:
		host = socket.gethostbyname(REMOTE_SERVER)
		s = socket.create_connection((host, 80), 2)
		return "Connected"
	except:
		pass
		print(colored.red('Not conneted. Exiting...'))
		sys.exit()
		return "Not conneted"
		
def s3_controls(s3, bucket_name, region, paths, s3_upload_disks, vmdk_file_names, delete):
	if delete == 0:
		try:
			s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={ 'LocationConstraint': region })
			print(colored.yellow('1. Creating a new S3 bucket with name: {}'.format(bucket_name)))
			print(colored.yellow('2. Uploading .vmdk files from ' + paths + ' to S3 bucket {}'.format(bucket_name)))
			k=0
			for i in s3_upload_disks:
#				fullpath = str(s3_upload_disks[k])
#				s3.Object(bucket_name, vmdk_file_names[k]).put(Body=open(fullpath, 'rb'))
				s3.Object(bucket_name, vmdk_file_names[k]).put(Body=open(str(s3_upload_disks[k]), 'rb'))
				k = k + 1
			print(colored.yellow('3. Files uploaded to S3 bucket {}' .format(bucket_name)))
		except:
			return "Not conneted"
	else:	
		bucket = s3.Bucket(bucket_name)
		for key in bucket.objects.all():
			key.delete()
		bucket.delete()
		print(colored.yellow('4. Deleted S3 bucket name: {}' .format(bucket_name)))
		sys.exit()

# start main function
def main():
	print(colored.cyan('##########----------------------------------------------------------##########\n########## WELCOME TO AWS VM IMPORT TOOL FOR DELL EMC DPS SOLUTIONS ##########\n##########----------------------------------------------------------##########'))
	print(colored.yellow('\nPurpose:\nThis tool can be used to import on-premise vMware Virtual Machines to AWS cloud.\nRequiremnets: \n1. Internet connectivity \n2. OS absolute path for vmdk \n3. AWS service account with AdministratorAccess and AWS region\n'))
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
#		ACCESS_KEY = getpass.getpass('Enter AWS Access Key ID: ')
		ACCESS_KEY = "AKIAIYM5Y5MQ2ZTZD7AA"
#		SECRET_KEY = getpass.getpass('Enter AWS Secret Access Key: ')
		SECRET_KEY = "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"
		region = input('Default region name ( ap-south-1 ): ')
		bucket_name = 'aws-{}'.format(int(time.time()))
		ec2 = boto3.client('ec2', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=region)
		print(ec2)
		session = boto3.session.Session(aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=region)
		s3 = session.resource('s3')
		print(s3)
		try:
			s3_controls(s3, bucket_name, region, paths, s3_upload_disks, vmdk_file_names, 0)	
#			bucket = s3.Bucket(bucket_name)
#			for key in bucket.objects.all():
#				key.delete()
#			bucket.delete()
#			print(colored.yellow('4. Deleted S3 bucket name: {}' .format(bucket_name)))
			print(colored.yellow('4. Importing AMI'))
			disk_description = ["First Disk", "Second Disk", "Third Disk", "Fourth Disk", "Fifth Disk", "Sixth Disk", "Seventh Disk", "Eighth Disk","Nineth Disk", "Tenth Disk"]
			disk_containers=""
			i = 1
			while i <= len(s3_upload_disks):
				disk_containers = disk_containers + "{'Description':'"+ disk_description[i-1] + "', 'Format':'vmdk', 'UserBucket':{'S3Bucket':'" + bucket_name + "', S3Key:'" + vmdk_file_names[i-1] + "'}},"
				i += 1
#			print(disk_containers)
#			ami_import = "ec2.import_image(Description='Coverted using Python BOTO3', LicenseType='BYOL', DiskContainers=[" + disk_containers + " DryRun=False, RoleName='vmimport')"
#			ami_import = "ec2.import_image(Description='Coverted using Python BOTO3', LicenseType='BYOL', DiskContainers=[{'Description': 'First Disk', 'Format': 'vmdk', 'UserBucket': {'S3Bucket': 'nve-aws','S3Key': 'disks/AWS-NVE-18.1.0.21-disk1.vmdk'}}], DryRun=False, RoleName='vmimport')"
#			ami_response = eval(ami_import)
#			print(ami_response)
#			response = ec2.import_image(Description='Coverted using Python BOTO3', LicenseType='BYOL', DiskContainers=[{'Description': 'First Disk', 'Format': 'vmdk', 'UserBucket': {'S3Bucket': 'nve-aws','S3Key': 'disks/AWS-NVE-18.1.0.21-disk1.vmdk'}}], DryRun=False, RoleName='vmimport')
#			print(response)
			time.sleep(10) # Wait for 5 seconds
#			TaskID = str(ami_response['ImportTaskId'])
#			print(colored.yellow(TaskID))
			status = ec2.describe_conversion_tasks(ConversionTaskIds=['import-ami-0afcd40f8498c9582'])
#			time.sleep(10) # Wait for 5 seconds
#			status = ec2.describe_conversion_tasks(ConversionTaskIds=[TaskID])
			print(colored.yellow(status))
#			print (colored.yellow('5. Deleted S3 bucket name: {}' .format(bucket_name)))
#			s3_controls(s3, bucket_name, region, paths, fullpath, s3_upload_disks, 1)
			idea = 1
		finally:
			if idea == 0:
				print(colored.red("Invalid AWS Cerdentials or Region. Exiting..."))
	except:
		sys.exit()
if __name__ == "__main__":
	main()
	sys.exit(main())