#!/bin/bash

echo "================================================"
echo "   Setting up SSH Key Authentication"
echo "================================================"
echo ""

PUBLIC_KEY="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCnr5EeXhkbGJqiuCceA8aI5SaWq8rDYvF9VNY2yNSZ4XW+TKIihvJgEG+s9E3iacQvCDC7hkpz6BReIYM7QmZRDdNgEuLRkh5pHGK8OcMvRiqeXTboCVWuJMYg911Tvl4YC8s0gRVWmsSZP3maapaOiK9fhqP7vifo9ctdlsf3Z3xd55edY9yLBsk4QZV9yiFn2Cgc7ZEfGsrvwpnOD3yLb81aFItRV2My5EV3Crg4uurcnTXk+xYDaOoUix2F5N5K8kJzTDJUre8q229Zz5tNL9lId8eHMxX/C86k33ta34S2a8w1BzmQ0ybFeGmOV8dBif4hEdsqkKEzohwFwU2xB+gbD7rSj5G3WrtfCGrszs+CWPBCv3j8t4GrT+nQaipsQ0l917r7OucmjD2HrEDoXwhdvC4JPzijYIVoJ99PPzB8xPvVJj/enAFhu2TFVqspexmpiyruT2rF6YDouEdXsPl7ZPDCKcuRd2kpAYkhETQ4n1cuv9qB49UrzUBO7Sg7cFIIV+4DzgEizKaQm3ZHlJANxR6Vb029uLyJiGRE5mA7rmaagx5vsi9ceeYVEq5mESaetJ6B9CFky4D78MgINiPdWC1yKJ8EpkMshVdiJfer3Z4RavWNyauFf82MjFXzIkcsCUS/8jF3vOP+afhWnvEr8Kyjz/vDxmbpV9Z33Q== topher.sikorra@gmail.com"

echo "📝 You'll need to enter the password 'fortress' one last time..."
echo ""

# Create .ssh directory and add the key
ssh root@homeassistant.local "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$PUBLIC_KEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo '✅ SSH key added successfully!'"

echo ""
echo "🔐 Testing passwordless SSH connection..."
ssh -o PasswordAuthentication=no root@homeassistant.local "echo '✅ Passwordless SSH is working!'" || echo "❌ Passwordless SSH failed"

echo ""
echo "================================================"