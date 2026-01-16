# HomeWizard naar PVOutput - Docker Container

Een complete Docker container oplossing die data van HomeWizard apparaten (P1 meter en kWh meter) uitleest en automatisch doorstuurt naar PVOutput.org. Inclusief een mooie webinterface met live data visualisatie en grafieken.

## Features

- **Automatische data collectie** van HomeWizard P1 meter (stroomverbruik/teruglevering)
- **Automatische data collectie** van HomeWizard kWh meter (zonnepanelen opwekking)
- **Automatisch doorsturen** naar PVOutput.org
- **Live webinterface** met:
  - Real-time overzicht van opwekking, verbruik en grid import/export
  - Grafieken met historische data (laatste uur)
  - Configuratie management via web interface
  - Responsive design voor mobiel en desktop
- **Configureerbaar update interval** (minimum 300 seconden voor gratis PVOutput accounts)
- **Docker gebaseerd** voor eenvoudige installatie en gebruik

## Vereisten

- Docker en Docker Compose geïnstalleerd
- HomeWizard P1 meter en/of kWh meter op je lokale netwerk
- PVOutput.org account met API key en System ID

## Snelle Start

### 1. Clone deze repository

```bash
git clone <repository-url>
cd homewizard-pvoutput
```

### 2. Configuratie aanmaken

Kopieer het voorbeeld configuratie bestand:

```bash
cp config/config.example.yaml config/config.yaml
```

Bewerk `config/config.yaml` met je eigen instellingen:

```yaml
# HomeWizard P1 Meter configuratie
homewizard_p1:
  host: "192.168.1.100"  # IP adres van je HomeWizard P1 meter
  enabled: true

# HomeWizard kWh Meter configuratie (voor zonnepanelen)
homewizard_kwh:
  host: "192.168.1.101"  # IP adres van je HomeWizard kWh meter
  enabled: true

# PVOutput configuratie
pvoutput:
  api_key: "jouw-api-key-hier"
  system_id: "jouw-system-id-hier"

# Update interval in seconden (minimum 300 voor gratis account)
update_interval: 300

# Webserver configuratie
webserver:
  port: 8080
  host: "0.0.0.0"
```

### 3. HomeWizard API Keys verkrijgen

Je hebt geen API keys nodig voor HomeWizard - de apparaten hebben een lokale API die je direct kunt gebruiken.

#### IP adres van je HomeWizard apparaten vinden:

1. Open de HomeWizard Energy app
2. Ga naar het apparaat (P1 meter of kWh meter)
3. Tik op instellingen (tandwiel icoon)
4. Zoek naar "Lokale API" of "API configuratie"
5. Noteer het IP adres

Of gebruik een netwerk scanner om de apparaten te vinden op je netwerk.

### 4. PVOutput API gegevens verkrijgen

1. Log in op [PVOutput.org](https://pvoutput.org)
2. Ga naar "Settings"
3. Klik op "API Settings"
4. Noteer je **API Key** en **System ID**

### 5. Container starten

```bash
docker-compose up -d
```

### 6. Webinterface openen

Open je browser en ga naar:

```
http://localhost:8080
```

Of gebruik het IP adres van je Docker host als je op een andere machine zit.

## Webinterface

De webinterface toont:

- **Zonnepanelen**: Actuele opwekking en totaal opgewekt
- **Verbruik**: Actueel verbruik en zelfverbruik
- **Netwerk**: Import/export van en naar het elektriciteitsnet
- **PVOutput Status**: Of de data succesvol wordt verzonden
- **Grafiek**: Real-time visualisatie van opwekking, verbruik en grid power
- **Configuratie**: Pas instellingen aan via de web interface

## Configuratie via Webinterface

Je kunt de configuratie ook aanpassen via de webinterface:

1. Klik op "Configuratie" in de webinterface
2. Pas de instellingen aan
3. Klik op "Opslaan"
4. De container zal automatisch herstarten met de nieuwe instellingen

## Docker Commands

### Container starten
```bash
docker-compose up -d
```

### Logs bekijken
```bash
docker-compose logs -f
```

### Container stoppen
```bash
docker-compose down
```

### Container herstarten
```bash
docker-compose restart
```

### Container herbouwen na wijzigingen
```bash
docker-compose up -d --build
```

## Troubleshooting

### HomeWizard data wordt niet opgehaald

1. Controleer of de IP adressen correct zijn in `config/config.yaml`
2. Controleer of de HomeWizard apparaten bereikbaar zijn vanaf de Docker host:
   ```bash
   curl http://<homewizard-ip>/api/v1/data
   ```
3. Zorg ervoor dat de lokale API ingeschakeld is in de HomeWizard app

### Data wordt niet naar PVOutput gestuurd

1. Controleer of de API key en System ID correct zijn
2. Let op: gratis PVOutput accounts hebben een limiet van 1 update per 5 minuten
3. Bekijk de logs voor foutmeldingen:
   ```bash
   docker-compose logs -f
   ```

### Webinterface niet bereikbaar

1. Controleer of de container draait:
   ```bash
   docker-compose ps
   ```
2. Controleer of poort 8080 niet al in gebruik is
3. Probeer de health check:
   ```bash
   docker-compose exec homewizard-pvoutput python -c "import httpx; print(httpx.get('http://localhost:8080/api/status').json())"
   ```

## Project Structuur

```
.
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css          # Styling voor webinterface
│   │   └── js/
│   │       └── app.js             # JavaScript voor webinterface
│   ├── templates/
│   │   └── index.html             # HTML template voor dashboard
│   ├── config.py                  # Configuratie management
│   ├── homewizard.py             # HomeWizard API client
│   ├── pvoutput.py               # PVOutput API client
│   ├── data_manager.py           # Data opslag en statistieken
│   └── main.py                   # Hoofdapplicatie
├── config/
│   ├── config.example.yaml       # Voorbeeld configuratie
│   └── config.yaml               # Jouw configuratie (niet in git)
├── Dockerfile                    # Docker image definitie
├── docker-compose.yml            # Docker Compose configuratie
├── requirements.txt              # Python dependencies
└── README.md                     # Deze file
```

## API Endpoints

De container biedt een REST API:

- `GET /api/status` - Algemene status
- `GET /api/data/latest` - Nieuwste data
- `GET /api/data/history?hours=1` - Historische data
- `GET /api/data/statistics` - Statistieken
- `GET /api/config` - Huidige configuratie
- `POST /api/config` - Update configuratie
- `POST /api/update-now` - Forceer directe update

## Advanced Configuratie

### Custom poort

Pas de poort aan in `docker-compose.yml`:

```yaml
ports:
  - "8081:8080"  # Host poort 8081, container poort 8080
```

### Timezone

Pas de timezone aan in `docker-compose.yml`:

```yaml
environment:
  - TZ=Europe/Amsterdam  # Wijzig naar jouw timezone
```

### Update interval

Het update interval kan worden aangepast in de configuratie. Let op:

- Gratis PVOutput accounts: minimum 300 seconden (5 minuten)
- Betaalde PVOutput accounts: minimum 60 seconden (1 minuut)

## Licentie

Dit project is open source en beschikbaar voor iedereen.

## Support

Voor vragen, problemen of feature requests, open een issue op GitHub.