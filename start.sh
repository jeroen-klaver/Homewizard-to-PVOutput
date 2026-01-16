#!/bin/bash

# Start script voor HomeWizard naar PVOutput container

echo "HomeWizard naar PVOutput - Docker Container"
echo "==========================================="
echo ""

# Check of Docker geïnstalleerd is
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is niet geïnstalleerd"
    echo "Installeer Docker eerst: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check of Docker Compose geïnstalleerd is
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is niet geïnstalleerd"
    echo "Installeer Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check of config bestaat
if [ ! -f "config/config.yaml" ]; then
    echo "Waarschuwing: config/config.yaml bestaat niet"
    echo "Kopieer config/config.example.yaml naar config/config.yaml en pas aan"
    echo ""
    read -p "Wil je dit nu doen? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp config/config.example.yaml config/config.yaml
        echo "config.yaml aangemaakt. Bewerk dit bestand met je instellingen."
        echo "Je kunt ook de configuratie later aanpassen via de webinterface."
    fi
fi

echo ""
echo "Container wordt gestart..."
echo ""

# Start de container
docker-compose up -d

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Container succesvol gestart!"
    echo ""
    echo "Webinterface beschikbaar op: http://localhost:8080"
    echo ""
    echo "Handige commands:"
    echo "  - Logs bekijken:    docker-compose logs -f"
    echo "  - Status:           docker-compose ps"
    echo "  - Stoppen:          docker-compose down"
    echo "  - Herstarten:       docker-compose restart"
    echo ""
else
    echo ""
    echo "✗ Fout bij starten van container"
    echo "Bekijk de logs met: docker-compose logs"
    exit 1
fi
