# <p align=center> Policing Game in O-Tree </p>

<!--
<img src="https://github.com/Jadamso/TerritoryR/blob/master/Pictures/TerritoryScreenshot2.png"  align="center" width="1000" height="500">
-->



  



# Setup / Install
<details>
  <summary>click to expand</summary>
      
  ### Setup O-Tree Server on AWS

  To setup an AWS server, see
  https://github.com/Jadamso/ClusterInstall/blob/master/README_AWS.md#amazon-setup

  To setup Otree, see
  https://github.com/Jadamso/ClusterInstall/blob/master/README_AWS.md#o-tree-server-setup


  ### Install latest release of delegated_punishment
  Login to server `ssh -i LightsailDefaultKey.pem ubuntu@44.232.29.84`

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

  ### Session Types
  <!-- ------------------------------------------------ -->

  | **Inequality:** |**High->Low**|**Low->High**|
  |-----------------|-------------|-------------|
  | **B=0**         | Treatment_1 | Treatment_4 |
  | **B=10**        | Treatment_2 | Treatment_5 |
  | **B=30**        | Treatment_3 | Treatment_6 |

  <!-- ------------------------------------------------ -->

</details>

---
# Run Session


## Setup Server

Login to server `ssh -i LightsailDefaultKey.pem ubuntu@44.232.29.84`, 

Can create new database for the session by running `otree resetdb` on server.
*this will break all existing session urls in lab.*


Start Server
 * If accidentaly launch chrome before server started then restart server and relaunch windows



```bash
cd $HOME/delegated_punishment
sudo -E env "PATH=$PATH" otree runprodserver 80
```
<!--##
RUN SERVER IN BACKGROUND OR TMUX SESSION??
-->

Logout and exit the ssh connection to the server

## Start the Session

#### Manually Create Session on Admin PC

Go to http://44.232.29.84/room_without_session/delegated_punishment/
  * LOGIN username: `admin`
  * password: `password`

Create the Session
  * choose config: `delegated_punishment`
  * choose number of participants: `18`
  * open `Config Session` and specify game parameters
    * `SESSION_ID` (should be one integer greater than the inger used last time, defaults to 0)
    * `low_to_high` (check if incomes inequality are first low then high)
    * `tutorial_civilian_income` (in grain, also used for trial period)
    * `tutorial_officer_bonus` (in grain, also used for trial period)
    * `grain_conversion` (?? grain : 1 USD$)
    * `showup payment` (in USD$)


#### Launch Game on Client PCs

On admin PC, open `Lanschool`

* Close any desktop software
* Run software one computer at a time within each row (five participants are automatically grouped, and will exit their rows from the outside-in)
  * `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe --kiosk --force-device-scale-factor=1.00 http://44.232.29.84/room/delegated_punishment/`
  * Manually check all screens, e.g., all chrome browsers have kiosk mode, fullscreen, zoom 100%.
  * Make sure Chrome starts fresh if there any issues


Control Session on Local Admin PC
 * Be on `monitor` tab to `advance slowest used`
 * Read Instructions, *do not pace while reading*


## End the Session

From Local Admin PC
 * Call up subjects by their participant ID
   * Verify their participant ID matches payment
   * If required by admin, record their name and payment
  
From Local Admin PC or Manually
 * Close all client connections / kill software
 * Logout of Otree, Logout of PC
 * Collect instructions

Login to Server
 * Download/Export Data

```bash
mkdir /tmp/SessionData/
scp -r -i LightsailDefaultKey.pem ubuntu@44.232.29.84:~/delegated_punishment/data/* /tmp/SessionData/
```

---
# Server Statistics (Primarily for Debugging)
<details>
  <summary>click to expand</summary>

  To start recording statistics for 90 mins (every 10 seconds, for 540 times)
  ```bash
  SERVERLOG=$HOME/delegated_punishment/logs/SERVERLOG"_$(date "+%d%m%Y_%H%M%S".log)"
  sar -o $SERVERLOG 10 540 >/dev/null 2>&1 &
  ```

  Create analyze mem-usage statistics
  ```bash
  sar -r -f SERVERLOG_03032020_093004.log | sed \$d > mem_summary.log
  ## Note %memused includes cached memory
  ## to generate cpu stats, use `sar -u`
  ## to generate other stats, use `man sar`
  ```
  Open R in current directory 
  <!-- `R -e "#code here" `-->
  ```R
  DF <- read.table("mem_summary.log", skip=2, header=T)
  DF$Time <- as.POSIXct( paste0( format(Sys.time(), "%d-%m-%y"), DF[,1] ) )
  DF$MemTot <- DF$kbmemused / (DF$X.memused/100)
  DF$MemUsed <- ((DF$MemTot - DF$kbavail) / DF$MemTot)*100
  plot(MemUsed ~Time , DF, type="l", ylab="% Mem Used")
  q(save="no")'
  ```
  Manually Download `Rplots.pdf`

  <!-- ## Other Statistics
  ```    
      ## top -bd 1  | grep 'MiB Mem' 
      ## `cat /proc/meminfo | grep Active: | sed 's/Active: //g'` 
      ##  echo "$(date '+%Y-%m-%d %H:%M:%S') $(free -m | grep Mem: | sed 's/Mem://g')"
      ##  echo "$(date '+%Y-%m-%d %H:%M:%S') $(free -m | grep Mem | awk '{print (1-$7/$2) * 100.0}')"
  ```
  To stop recording statistics, `ctrl+C` 
  -->

  <!-- ## Other Statistics
      If CloudWatch (see https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/mon-scripts.html) is is setup, then edit the crontab file `crontab -e` with
      ```
      ## Post Server Metrics Every 5 Minutes
       */5 * * * * ~/aws-scripts-mon/mon-put-instance-data.pl --mem-util --disk-space-util --disk-path=/ --from-cron 
      ```
      and open the CloudWatch console at https://console.aws.amazon.com/cloudwatch/
  -->

</details>
