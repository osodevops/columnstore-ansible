 #!/bin/bash -eux
#!/bin/bash -eux
# Using this to overcome the issue caputred here: https://saveriomiroddi.github.io/Handling-the-apt-lock-on-ubuntu-server-installations/
# TODO: Find a more elegant solution
set -e

function killService() {
    service=$1
    sudo systemctl stop $service
    sudo systemctl kill --kill-who=all $service

#    # Wait until the status of the service is either exited or killed.
#    while ! (sudo systemctl status "$service" | grep -q "Main.*code=\(exited\|killed\)")
#    do
#        sleep 10
#    done
}

function disableTimers() {
    sudo systemctl disable apt-daily.timer
    sudo systemctl disable apt-daily-upgrade.timer
}

function killServices() {
    killService unattended-upgrades.service
    killService apt-daily.service
    killService apt-daily-upgrade.service
}

function main() {
    disableTimers
    killServices
}

main

sudo apt-get update -y
sudo apt install python-boto3 -y
ansible-galaxy collection install community.general


