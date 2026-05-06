# Setting Up SSH Key Authentication for Home Assistant

To avoid entering the password every time, follow these steps to set up SSH key authentication:

## Step 1: Copy your SSH public key

Your public key is:
```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCnr5EeXhkbGJqiuCceA8aI5SaWq8rDYvF9VNY2yNSZ4XW+TKIihvJgEG+s9E3iacQvCDC7hkpz6BReIYM7QmZRDdNgEuLRkh5pHGK8OcMvRiqeXTboCVWuJMYg911Tvl4YC8s0gRVWmsSZP3maapaOiK9fhqP7vifo9ctdlsf3Z3xd55edY9yLBsk4QZV9yiFn2Cgc7ZEfGsrvwpnOD3yLb81aFItRV2My5EV3Crg4uurcnTXk+xYDaOoUix2F5N5K8kJzTDJUre8q229Zz5tNL9lId8eHMxX/C86k33ta34S2a8w1BzmQ0ybFeGmOV8dBif4hEdsqkKEzohwFwU2xB+gbD7rSj5G3WrtfCGrszs+CWPBCv3j8t4GrT+nQaipsQ0l917r7OucmjD2HrEDoXwhdvC4JPzijYIVoJ99PPzB8xPvVJj/enAFhu2TFVqspexmpiyruT2rF6YDouEdXsPl7ZPDCKcuRd2kpAYkhETQ4n1cuv9qB49UrzUBO7Sg7cFIIV+4DzgEizKaQm3ZHlJANxR6Vb029uLyJiGRE5mA7rmaagx5vsi9ceeYVEq5mESaetJ6B9CFky4D78MgINiPdWC1yKJ8EpkMshVdiJfer3Z4RavWNyauFf82MjFXzIkcsCUS/8jF3vOP+afhWnvEr8Kyjz/vDxmbpV9Z33Q== topher.sikorra@gmail.com
```

## Step 2: SSH into Home Assistant manually

```bash
ssh root@homeassistant.local
# Enter password: fortress
```

## Step 3: Add the key to authorized_keys

Once logged in, run these commands:

```bash
# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add your public key
cat >> ~/.ssh/authorized_keys << 'EOF'
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCnr5EeXhkbGJqiuCceA8aI5SaWq8rDYvF9VNY2yNSZ4XW+TKIihvJgEG+s9E3iacQvCDC7hkpz6BReIYM7QmZRDdNgEuLRkh5pHGK8OcMvRiqeXTboCVWuJMYg911Tvl4YC8s0gRVWmsSZP3maapaOiK9fhqP7vifo9ctdlsf3Z3xd55edY9yLBsk4QZV9yiFn2Cgc7ZEfGsrvwpnOD3yLb81aFItRV2My5EV3Crg4uurcnTXk+xYDaOoUix2F5N5K8kJzTDJUre8q229Zz5tNL9lId8eHMxX/C86k33ta34S2a8w1BzmQ0ybFeGmOV8dBif4hEdsqkKEzohwFwU2xB+gbD7rSj5G3WrtfCGrszs+CWPBCv3j8t4GrT+nQaipsQ0l917r7OucmjD2HrEDoXwhdvC4JPzijYIVoJ99PPzB8xPvVJj/enAFhu2TFVqspexmpiyruT2rF6YDouEdXsPl7ZPDCKcuRd2kpAYkhETQ4n1cuv9qB49UrzUBO7Sg7cFIIV+4DzgEizKaQm3ZHlJANxR6Vb029uLyJiGRE5mA7rmaagx5vsi9ceeYVEq5mESaetJ6B9CFky4D78MgINiPdWC1yKJ8EpkMshVdiJfer3Z4RavWNyauFf82MjFXzIkcsCUS/8jF3vOP+afhWnvEr8Kyjz/vDxmbpV9Z33Q== topher.sikorra@gmail.com
EOF

# Set proper permissions
chmod 600 ~/.ssh/authorized_keys

# Exit SSH
exit
```

## Step 4: Test passwordless SSH

From your local machine:

```bash
ssh root@homeassistant.local
# Should connect without asking for password!
```

## Step 5: Update deployment scripts

Once SSH key authentication is working, all the deployment scripts will work without passwords:

```bash
# Deploy latest from GitHub
./deploy.sh

# Or update both directories
./update_simple.sh
```

## Alternative: Using the Home Assistant UI

You can also add your SSH key through the Advanced SSH & Web Terminal addon configuration:

1. Go to Settings → Add-ons → Advanced SSH & Web Terminal
2. Click on Configuration tab
3. Add your public key to the `authorized_keys` section
4. Save and restart the addon