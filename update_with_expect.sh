#!/usr/bin/expect -f

# Update both AppDaemon directories from GitHub using expect for password handling

set timeout 30
set password "fortress"

spawn ssh root@homeassistant.local

expect {
    "password:" {
        send "$password\r"
        expect "# "
    }
    "Permission denied" {
        puts "Authentication failed"
        exit 1
    }
}

# Update /config/apps/
send "cd /config/apps/\r"
expect "# "
send "wget -O apps.yaml https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/appdaemon/apps/apps.yaml\r"
expect "# "
send "wget -O celestial.py https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/appdaemon/apps/celestial.py\r"
expect "# "
send "echo 'Updated /config/apps/'\r"
expect "# "

# Check if addon_configs directory exists and update it
send "if \[ -d /addon_configs/a0d7b954_appdaemon/apps/ \]; then cd /addon_configs/a0d7b954_appdaemon/apps/; wget -O apps.yaml https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/appdaemon/apps/apps.yaml; wget -O celestial.py https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/appdaemon/apps/celestial.py; echo 'Updated addon_configs'; fi\r"
expect "# "

# Restart AppDaemon
send "ha addon restart a0d7b954_appdaemon\r"
expect "# "

# Check the logs
send "grep 'Mapped' /addon_configs/a0d7b954_appdaemon/logs/appdaemon.log | tail -5\r"
expect "# "

send "exit\r"
expect eof

puts "\n✅ Both directories updated successfully!"