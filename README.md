# ansible-poc
Ansible Proof of Concept – Automated User Management with Oracle Cloud.
## Description:
The purpose of this project to practice infrastructure automation using Ansible with a Chromebook as the control node and Oracle Cloud free-tier instances as targets. The project simulated a real-world HRMS-to-server user provisioning pipeline, integrating Python, Oracle Autonomous Database, and Ansible playbooks.

### Key Highlights:
* **Control Node Setup:** Configured Linux (Crostini) on Chromebook and installed Ansible as the automation control node.
* **Cloud Infrastructure:** Deployed and configured two Linux instances in Oracle Cloud, including SSH key setup and networking. Debugged a connectivity issue by updating security group rules for ingress traffic and modifying the route table to properly route outbound traffic through an Internet Gateway.
* **Data Pipeline Simulation:**
  * Built a mock HRMS system using an Oracle Autonomous Database.
  * Populated the database with fake users/roles using Python.
  * Extracted user data and exported it as JSON for use in Ansible playbooks.
* **Ansible Automation:** Developed playbooks to create, verify, and remove Linux users and groups on cloud servers. Leveraged Ansible’s idempotence to ensure safe re-runs without unintended changes.
* **Configuration & Version Control:** Used .gitignore for clean version control and TOML files for project configuration management.

### Outcome
Demonstrated end-to-end automation — from database-driven data extraction to automated provisioning of users on remote servers — highlighting practical skills in **Ansible, Python, SQL, and Oracle Cloud Infrastructure.**

## Step 1: Enable Linux Crostini on Chromebook and Install Ansible

```
sudo apt update
sudo apt install ansible -y
ansible --version
```
![Install](/imgs/InstallAnsible.png)

## Step 2: Create Virtual Machines using Oracle Cloud

Create two Linux instances, allow SSH (port 22) in the firewall/security group, and download the SSH private key. 

![instances](/imgs/CloudInstances.png)

## Step 3: Configure SSH from Chromebook

### Directions:
```
mv ~/Downloads/mykey.pem ~/.ssh/
chmod 600 ~/.ssh/mykey.pem
```

### My steps:
Had to right click on folder and share with Linux.  
```
mv /mnt/chromeos/MyFiles/Downloads/ssh-key-01.key ~/.ssh/ssh-key-01.key
mv /mnt/chromeos/MyFiles/Downloads/ssh-key-02.key ~/.ssh/ssh-key-02.key
```

List files in directory and change permissions on the key so only the owner has access.
```
ls -l ~/.ssh/
chmod 600 ~/.ssh/ssh-key-01.key
chmod 600 ~/.ssh/ssh-key-02.key
```
#### Note on chmod 600
* Unix-like file permissions are managed for three categories: the owner, the group, and others.
* Each permission type has a numerical value:
  * Read (r): 4
  * Write (w): 2
  * Execute (x): 1 
* chmod 600 is a command in Unix-like operating systems that sets file permissions so that only the file's owner has read and write access, with all group members and other users having no access. The first digit 6 means the owner gets read/write (2+4=6). The group gets 0. Others get 0.  
  * File permissions before:  
`-rw-r--r-- 1 myusername myusername 1675 Sep  9 19:27 ssh-key-01.key`  
  * After:  
`-rw------- 1 myusername myusername 1675 Sep  9 19:27 ssh-key-01.key`  

## Step 4: Test Connection to Servers

### Directions:
`ssh -i ~/.ssh/mykey.pem ubuntu@<cloud-public-ip>`

### My Steps:
Test connecting to server.  
`ssh -v -i ~/.ssh/ssh-key-01.key ubuntu@123.123.123.1`  

#### Note on Network Traffic Rules
While troubleshooting a timeout error, I learned that ingress traffic (incoming connections from the internet to the VM) is controlled by the Security List / Network Security Group rules (firewall). My subnet already had an ingress rule allowing SSH (port 22/TCP) from any public IP (0.0.0.0/0), so inbound access was not the issue. The problem was with egress traffic — the Internet Gateway (IGW), which handles outbound traffic from the VCN to the internet, was not attached to my subnet. To resolve this, I updated the subnet’s route table to include a rule pointing to the IGW. This ensured that all outbound traffic from the subnet could properly reach the internet.  
![igw](/imgs/IGW.png)

## Step 5: Create an Ansible Inventory
The Ansible inventory will list our servers in a group called 'cloud_servers'. This allows our playbooks to run plays on the group.

[Ansible documentation for building an inventory.](https://docs.ansible.com/ansible/latest/getting_started/get_started_inventory.html#get-started-inventory)

Create new directory for Proof of Concept (POC) project.
```
mkdir ansible-poc && cd ansible-poc
```

Create inventory.ini configuration file.  
Example:  
![inventory](/imgs/InventoryExample01.png)


Verify inventory.  
`ansible-inventory -i inventory.ini --list`

Ping the cloud_servers group in inventory.  
`ansible cloud_servers -m ping -i inventory.ini`

![TestConnection](/imgs/TestConnection.png)

## Step 6: Create an Autonomous Oracle Database

![database](/imgs/AutonomousDatabase01.png)

#### Note on TLS or Mutual TLS (mTLS) decision
The connection to the Autonomous Database had the option of using TLS or Mutual TLS (mTLS). The Oracle help seemed to encourage TLS and it works with the Python oracledb driver, so that is what I chose.

> Autonomous Database is preconfigured to support Oracle Net Services (a TNS listener is installed and configured to use secure TCPS). Connections to your Autonomous Database are secured, and can be authorized using TLS or mTLS authentication options. TLS authentication is easier to use, provides better connection latency, and does not require you to download client credentials (wallet).

In order to create my TLS connection I added my Chromebook IP address to the Access Control List for the Autonomous Database Network and turned off the requirement for mTLS.

![Database](/imgs/DatabaseNetwork.png)

## Step 7: Install Oracle Python Driver on Control Node
Update package lists, upgrade installed packages, and install [pip](https://realpython.com/what-is-pip/) and [venv](https://realpython.com/python-virtual-environments-a-primer/) system wide using sudo apt. 
```
cd ..
sudo apt update && sudo apt dist-upgrade -y
sudo apt install python3-pip
sudo apt install python3-venv -y
```

Create virtual environment, activate the environment, and install [python-oracledb driver](https://python-oracledb.readthedocs.io/en/latest/user_guide/introduction.html).
```
cd ansible-poc
python3 -m venv venv --prompt="(ansible-poc)"
source venv/bin/activate
pip install oracledb
```

After installing packages, I checked the storage for my Linux container. I am using 39% of my 10GB.
```df -h```
![storage](/imgs/Storage.png)


Create [toml files](https://realpython.com/python-toml/) for storing configuration data and .gitignore for ignoring files for git.
* [pyproject.toml](/pyproject.toml) - For storing project configuration data
* .gitignore - Excludes specific files or file patterns from being comitted to git

## Step 8: Prepare Data for Playbook

### Create user table in Oracle database using Python.
Use Python to populate mock HRMS system (Oracle database) with fake users and roles.  
[create_hrms_users.py](/create_hrms_users.py)

### Query users from Oracle database using Python and create JSON file.
Get user data from mock HRMS system and store in JSON file for playbook (this step could be added to the playbook).  
[get_hrms_users.py](/get_hrms_users.py)

## Step 9: Run Ansible Playbooks to Manage Users
### Create Ansible Playbooks
* [create_users.yml](/create_users.yml)
* [verify_users.yml](/verify_users.yml)
* [remove_users.yml](/remove_users.yml)

### Run playbook to create users on application server.
`ansible-playbook -i inventory.ini create_users.yml`

![RunPlay](/imgs/PlayCreateUsers.png)

### Verify users and groups exist on server

#### Using bash:  
```
ssh -i ~/.ssh/ssh-key-01.key ubuntu@123.123.123.1
getent group mygroup analyst
getent passwd carol
```

#### Or using ansible playbook:  
`ansible-playbook -i inventory.ini verify_users.yml`  

![Verify](/imgs/PlayVerifyUsers.png)

#### Note on idempotence
At this point I accidentally ran the create users playbook again instead of the verify users playbook. The output shows how **Ansible** operates on the principle of **idempotence**, meaning it only changes what is necessary to reach the desired state. This ensures that repeated execution of the same playbook will not cause unintended changes or errors, and only modifications required to align with the defined configuration are applied.
![Idempotence](/imgs/PlayCreateUsersAgain.png)

#### Note on Ansible’s default behavior for command
Even though we are only verifying users and not making changes, the play recap does list changes. That is because command always reports as “changed” because Ansible assumes running an arbitrary command might have changed system state (even though getent doesn’t). So, it is not changing anything on the server. It’s just Ansible’s default behavior for command.
![Verify](/imgs/PlayRecapVerifyUsers.png)

### Clean up users 
```
ansible-playbook -i inventory.ini create_users.yml
```
![Clean](/imgs/PlayRemoveUsers.png)
