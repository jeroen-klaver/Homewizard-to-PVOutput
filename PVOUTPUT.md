# PVOutput Integratie - Uitleg

## Wat is PVOutput?

PVOutput.org is een gratis service voor het delen en vergelijken van PV output data van zonnepaneel systemen. Het biedt statistieken, grafieken en kan data delen met andere systemen.

## Welke data stuurt deze container naar PVOutput?

De container verzamelt data van je HomeWizard apparaten en stuurt deze naar PVOutput volgens hun API specificatie.

### PVOutput Parameters

PVOutput accepteert de volgende parameters (v1-v6):

| Parameter | Naam | Eenheid | Beschrijving | Bron in deze container |
|-----------|------|---------|--------------|----------------------|
| **v1** | Energy Generation | Wh | Totaal opgewekt **vandaag** (cumulatief) | HomeWizard kWh meter(s) |
| **v2** | Power Generation | W | Actueel opgewekt vermogen | HomeWizard kWh meter(s) |
| **v3** | Energy Consumption | Wh | Totaal verbruikt **vandaag** (cumulatief) | Berekend: v1 + import - export |
| **v4** | Power Consumption | W | Actueel verbruik | Berekend: opwekking + grid power |
| **v5** | Temperature | °C | Temperatuur (optioneel) | Niet gebruikt |
| **v6** | Voltage | V | Voltage (optioneel) | Niet gebruikt |

## Hoe worden de waarden berekend?

### Actuele waarden (Power)

**v2 - Power Generation (Actuele opwekking)**
- Directe waarde van HomeWizard kWh meter(s): `active_power_w`
- Bij meerdere meters: som van alle meters

**v4 - Power Consumption (Actueel verbruik)**
- Formule: `Opwekking + Grid Power`
- Als grid power positief is (import): verbruik = opwekking + import
- Als grid power negatief is (export): verbruik = opwekking - export

**Voorbeeld:**
- Zonnepanelen opwekking: 3000W
- Grid power: -500W (export naar net)
- Verbruik: 3000 + (-500) = 2500W

### Dagelijkse totalen (Energy)

De container houdt automatisch bij wat de startwaarden waren bij het begin van de dag (of bij opstarten). Dagelijkse totalen zijn het **verschil** tussen nu en de startwaarde.

**v1 - Energy Generation (Totaal opgewekt vandaag)**
- Formule: `Huidige kWh - Start kWh van vandaag`
- Automatisch gereset om middernacht
- Bij meerdere meters: som van alle meters

**v3 - Energy Consumption (Totaal verbruikt vandaag)**
- Formule: `Opgewekt vandaag + Import vandaag - Export vandaag`
- Dit geeft het werkelijke verbruik in het huis

## Meerdere kWh meters (Omvormers)

Als je meerdere omvormers hebt (bijvoorbeeld verschillende strings op verschillende daken), kun je meerdere HomeWizard kWh meters toevoegen. De container combineert automatisch de data:

### Configuratie

```yaml
homewizard_kwh_meters:
  - name: "Omvormer Zuid"
    host: "192.168.1.101"
    enabled: true
  - name: "Omvormer West"
    host: "192.168.1.102"
    enabled: true
  - name: "Omvormer Oost"
    host: "192.168.1.103"
    enabled: true
```

### Datacombinatie

De container doet het volgende:

1. **Haalt data op** van alle ingeschakelde meters
2. **Sommeert de waarden**:
   - `total_power_export_kwh` = som van alle meters
   - `active_power_w` = som van alle meters
3. **Stuurt gecombineerde waarden** naar PVOutput
4. **Bewaart individuele data** voor weergave in het dashboard

### Voorbeeld

| Meter | Actueel vermogen | Totaal opgewekt |
|-------|-----------------|-----------------|
| Zuid | 1200W | 15.5 kWh |
| West | 800W | 12.3 kWh |
| Oost | 1000W | 14.1 kWh |
| **Totaal** | **3000W** | **41.9 kWh** |

Het totaal (3000W actueel, 41.9 kWh totaal) wordt gestuurd naar PVOutput.

## Update interval

Let op de volgende limieten van PVOutput:

### Gratis account
- **Minimum interval**: 300 seconden (5 minuten)
- **Maximum uploads**: 60 per dag
- De container standaard: 300 seconden

### Betaald account (PVOutput Donation)
- **Minimum interval**: 60 seconden (1 minuut)
- **Maximum uploads**: 288 per dag
- Je kunt het interval verlagen naar 60 seconden in de configuratie

## Data flow diagram

```
HomeWizard P1 Meter ────┐
                        │
                        ├──> Data Manager ──> PVOutput Converter ──> PVOutput API
                        │    (Dagelijkse      (v1, v2, v3, v4)
                        │     totalen)
HomeWizard kWh Meter 1 ─┤
HomeWizard kWh Meter 2 ─┤
HomeWizard kWh Meter 3 ─┘
```

## Troubleshooting

### Data wordt niet naar PVOutput gestuurd

1. **Check API key en System ID**
   - Log in op PVOutput.org
   - Ga naar Settings → API Settings
   - Controleer of de waarden correct zijn

2. **Check update interval**
   - Gratis accounts: minimaal 300 seconden
   - Te hoge frequentie resulteert in rejected requests

3. **Check logs**
   ```bash
   docker-compose logs -f
   ```
   Zoek naar "Data naar PVOutput gestuurd" of foutmeldingen

### Dagelijkse totalen kloppen niet

- De container reset dagelijkse waarden automatisch om middernacht
- Bij eerste opstart gebruikt het de huidige waarden als startpunt
- Herstart de container om 00:00 voor accurate dagelijkse totalen

### Individuele meters worden niet getoond

- Check of meters ingeschakeld zijn in config
- Check of IP adressen correct zijn
- Controleer of lokale API ingeschakeld is op HomeWizard apparaten

## API Endpoints voor debugging

Je kunt de volgende endpoints gebruiken om data te inspecteren:

```bash
# Laatste data
curl http://localhost:8080/api/data/latest

# Dagelijkse totalen
curl http://localhost:8080/api/data/daily

# Statistieken (inclusief individuele meters)
curl http://localhost:8080/api/data/statistics
```

## Meer informatie

- [PVOutput API Documentation](https://pvoutput.org/help/api_specification.html)
- [HomeWizard Energy API](https://homewizard-energy-api.readthedocs.io/)
