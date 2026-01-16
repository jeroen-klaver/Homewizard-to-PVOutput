# Installatie Instructies

## Methode 1: Snelle Start met Script (Aanbevolen)

### Stap 1: Clone de repository

```bash
git clone <repository-url>
cd homewizard-pvoutput
```

### Stap 2: Voer het start script uit

```bash
./start.sh
```

Het script zal:
- Controleren of Docker en Docker Compose geïnstalleerd zijn
- Een config bestand aanmaken als deze niet bestaat
- De container starten
- De webinterface URL tonen

### Stap 3: Configureer via de webinterface

1. Open http://localhost:8080 in je browser
2. Klik op "Configuratie" → "Toon"
3. Vul je gegevens in:
   - HomeWizard P1 meter IP adres
   - HomeWizard kWh meter IP adres (optioneel)
   - PVOutput API key en System ID
4. Klik op "Opslaan"

## Methode 2: Handmatige Installatie

### Stap 1: Clone de repository

```bash
git clone <repository-url>
cd homewizard-pvoutput
```

### Stap 2: Maak configuratie bestand aan

```bash
cp config/config.example.yaml config/config.yaml
```

### Stap 3: Bewerk configuratie

Open `config/config.yaml` in een teksteditor en pas aan:

```yaml
homewizard_p1:
  host: "192.168.1.100"  # Jouw P1 meter IP
  enabled: true

homewizard_kwh:
  host: "192.168.1.101"  # Jouw kWh meter IP (optioneel)
  enabled: false

pvoutput:
  api_key: "jouw-api-key"
  system_id: "jouw-system-id"

update_interval: 300
```

### Stap 4: Start de container

```bash
docker-compose up -d
```

### Stap 5: Controleer de logs

```bash
docker-compose logs -f
```

### Stap 6: Open de webinterface

Open je browser en ga naar: http://localhost:8080

## Vereisten

### Software

- Docker (versie 20.10 of hoger)
- Docker Compose (versie 1.29 of hoger)

#### Docker installeren

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**Windows/Mac:**
Download en installeer [Docker Desktop](https://www.docker.com/products/docker-desktop)

### Hardware/Netwerk

- HomeWizard P1 meter (Wi-Fi P1 meter)
- HomeWizard kWh meter (optioneel, voor zonnepanelen)
- Beide apparaten op hetzelfde netwerk als de Docker host

### PVOutput Account

1. Maak een account aan op [PVOutput.org](https://pvoutput.org)
2. Registreer je systeem (solar installatie)
3. Verkrijg je API key en System ID via Settings → API Settings

## IP Adressen van HomeWizard Apparaten Vinden

### Methode 1: Via de HomeWizard App

1. Open de HomeWizard Energy app
2. Selecteer het apparaat
3. Ga naar instellingen (tandwiel icoon)
4. Zoek "Lokale API" of "API configuratie"
5. Noteer het IP adres

### Methode 2: Via je router

1. Log in op je router admin interface
2. Zoek naar aangesloten apparaten
3. Zoek naar apparaten met "HomeWizard" in de naam

### Methode 3: Netwerk scan

**Linux/Mac:**
```bash
sudo nmap -sn 192.168.1.0/24
```

**Windows:**
Gebruik een tool zoals [Advanced IP Scanner](https://www.advanced-ip-scanner.com/)

## Lokale API Inschakelen

De HomeWizard apparaten hebben een lokale API die standaard **uitgeschakeld** kan zijn:

1. Open de HomeWizard Energy app
2. Selecteer het apparaat
3. Ga naar instellingen
4. Zoek "Lokale API" of "API toegang"
5. Schakel de API in

## Test de API

Test of je de HomeWizard apparaten kunt bereiken:

```bash
# P1 meter
curl http://<p1-meter-ip>/api/v1/data

# kWh meter
curl http://<kwh-meter-ip>/api/v1/data
```

Je zou JSON data terug moeten krijgen met meetwaarden.

## Poort Aanpassen

Standaard draait de webinterface op poort 8080. Om dit aan te passen:

Bewerk `docker-compose.yml`:

```yaml
ports:
  - "8081:8080"  # Wijzig 8081 naar gewenste poort
```

## Timezone Instellen

Bewerk `docker-compose.yml`:

```yaml
environment:
  - TZ=Europe/Amsterdam  # Wijzig naar jouw timezone
```

Beschikbare timezones: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

## Auto-start bij Systeem Boot

De container is geconfigureerd met `restart: unless-stopped`, wat betekent dat deze automatisch start bij systeem boot.

Om dit uit te schakelen, wijzig in `docker-compose.yml`:

```yaml
restart: "no"
```

## Updates

Om de container te updaten naar een nieuwe versie:

```bash
cd homewizard-pvoutput
git pull
docker-compose up -d --build
```

## Deinstallatie

Om de container te verwijderen:

```bash
docker-compose down
docker rmi homewizard-pvoutput
```

Om ook de configuratie te verwijderen:

```bash
rm -rf config/
```

## Problemen?

Zie de [Troubleshooting sectie in de README](README.md#troubleshooting) voor veelvoorkomende problemen en oplossingen.
