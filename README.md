# Policing Game in O-Tree

<!--
<img src="https://github.com/Jadamso/TerritoryR/blob/master/Pictures/TerritoryScreenshot2.png"  align="center" width="1000" height="500">
-->


---
# Setup O-Tree Server on AWS

To setup an AWS server, see
https://github.com/Jadamso/ClusterInstall/blob/master/README_AWS.md#amazon-setup

To setup Otree, see
https://github.com/Jadamso/ClusterInstall/blob/master/README_AWS.md#o-tree-server-setup


---
# Install latest release

Login to server `ssh ubuntu@34.215.160.83`

To initially install
```bash

    cd $HOME
    git clone https://github.com/yelsew414/delegated_punishment.git
    cd $HOME/delegated_punishment
    pip3 install -r requirements.txt

```

To update to the latest version
```bash

    cd $HOME
    git pull https://github.com/yelsew414/delegated_punishment.git

```

<!-- --- -->

<!-- 
## Pre-Session Setup
## Create Players and Passwords (including admin) ? 
## Setup Game Parameters (Treatments)?
-->

---
# Run Session


#### Session Types

<!-- ------------------------------------------------ -->



| **Inequality:** |**High->Low**|**Low->High**|
|-----------------|-------------|-------------|
| **B=0**         | Treatment_1 | Treatment_2 |
| **B=5**         | Treatment_3 | Treatment_4 |
| **B=10**        | Treatment_5 | Treatment_6 |
| **B=15**        | Treatment_7 | Treatment_8 |


<!-- ------------------------------------------------ -->


#### Setup Session

Create new database for the session by running `otree resetdb` on server.

*this will break all existing session urls in lab.*


Launch New Session *need to specify game parameters?*

```bash

    cd $HOME/delegated_punishment
    echo 'y' | otree resetdb
    sudo -E env "PATH=$PATH" otree runprodserver 80

```


Logout and exit the ssh connection to the server

## Connect Clients (Subjects)

 * **Be Careful** to Start Server Before Clients
 * If accidentaly launch chrome before server started then restart server and relaunch windows
</br>


Manually Create Session on Local Admin PC
 * go to http://34.221.168.234/
 * create session with a `SESSION_ID`

Launch Homepage on Client PC:
 * C:/ ... /chrome.exe --kiosk
 * http://34.215.160.83/join/ `SESSION_ID`

<!--
Launch google chrome and sign in students (JA1 ... JAN) 
Launch Individual Pages:
 * http://34.221.168.234/DelegatedPunishment?username=[+]&password=PoDjangos
AutoInc[x] tag 1


Admins: username=admin & password=PoDjangos
 * http://34.221.168.234
-->



## End of Session

From Local Admin PC
 * Enter Payoffs from Admin PC
 * Close Client Connections

From Server
 * Download/Export Data

```bash

    mkdir /tmp/SessionData/
    scp ubuntu@34.215.160.83:~/delegated_punishment/data/* /tmp/SessionData/

```

 * Stop/Shutdown Server


## Server Statistics (Primarily for Debugging)


To start recording statistics, run
```bash

    SERVERLOG=$HOME/delegated_punishment/logs/SERVERLOG"_$(date "+%d%m%Y_%H%M%S")".log
    top -b -d 1  > SERVERLOG

```
   
To stop recording statistics, `ctrl+C` 
   
To analyze statistics
```bash

    cat $(echo SERVERLOG) | grep '%Cpu(s):' --line-buffered
    cat $(echo SERVERLOG) | sed -n '8,$p' | sort -r -n -k 10,10

```

