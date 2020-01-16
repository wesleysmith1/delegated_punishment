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
pip install -r requirements.txt

```

To update to the latest version
```bash

    cd $HOME
    git pull https://github.com/yelsew414/delegated_punishment.git

```


---
# Pre-Session Setup


## Create Players and Passwords (including admin) ? 

## Setup Game Parameters (Treatments)?

---
# Run Session

Session Types

<!-- ------------------------------------------------ -->

| **Inequality:** |**High->Low**|**Low->High**|
|-----------------|-------------|-------------|
| **B=0**         | Treatment_1 | Treatment_2 |
| **B=5**         | Treatment_3 | Treatment_4 |
| **B=10**        | Treatment_5 | Treatment_6 |
| **B=15**        | Treatment_7 | Treatment_8 |


<!-- ------------------------------------------------ -->


Launch New Session *Still need to specify game parameters*

```bash

cd $HOME/delegated_punishment
echo 'y' | otree resetdb
sudo -E env "PATH=$PATH" otree runprodserver 80

```


Logout and exit the ssh connection to the server

## Connect Subjects (using launcher)
Launch google chrome and sign in students (JA1 ... JAN) 
 * **Be Careful** to Start Server Before Launcher
 * If accidentaly launch chrome before server started then restart server and relaunch windows
</br>


Launcher:
 * http://34.221.168.234/DelegatedPunishment?username=[+]&password=PoDjangos
AutoInc[x] tag 1

<!--
Admins: username=admin & password=PoDjangos
 * http://34.221.168.234
-->



## Stop Server Export Data



