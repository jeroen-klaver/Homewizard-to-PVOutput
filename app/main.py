import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
from typing import Dict
import uvicorn

from app.config import Config
from app.homewizard import HomeWizardClient, HomeWizardDataProcessor
from app.pvoutput import PVOutputClient, PVOutputDataConverter
from app.data_manager import DataManager

# Globale instances
config = Config()
data_manager = DataManager()
p1_client = None
kwh_clients = {}  # Dictionary om meerdere kWh meter clients op te slaan (key: host)
pvoutput_client = None
update_task = None

async def collect_and_send_data():
    """Verzamel data van HomeWizard en stuur naar PVOutput"""
    global p1_client, kwh_clients, pvoutput_client

    # Haal P1 data op
    p1_data = {}
    if config.homewizard_p1_enabled and config.homewizard_p1_host:
        if not p1_client:
            p1_client = HomeWizardClient(config.homewizard_p1_host)

        raw_p1_data = await p1_client.get_data()
        p1_data = HomeWizardDataProcessor.process_p1_data(raw_p1_data)
        data_manager.add_p1_data(p1_data)
        print(f"P1 data verzameld: {p1_data.get('active_power_w', 0)}W")

    # Haal data op van alle kWh meters
    kwh_data_list = []
    kwh_meters = config.homewizard_kwh_meters_enabled

    if kwh_meters:
        for meter in kwh_meters:
            meter_host = meter.get('host')
            meter_name = meter.get('name', meter_host)

            # Maak client aan als deze nog niet bestaat
            if meter_host not in kwh_clients:
                kwh_clients[meter_host] = HomeWizardClient(meter_host)

            try:
                # Haal data op van deze meter
                raw_kwh_data = await kwh_clients[meter_host].get_data()
                processed_data = HomeWizardDataProcessor.process_kwh_data(raw_kwh_data)

                # Voeg meter naam toe aan data
                processed_data['meter_name'] = meter_name
                processed_data['meter_host'] = meter_host

                kwh_data_list.append(processed_data)
                print(f"kWh data verzameld van '{meter_name}': {processed_data.get('active_power_w', 0)}W")

            except Exception as e:
                print(f"Fout bij ophalen data van '{meter_name}' ({meter_host}): {e}")

    # Combineer data van alle kWh meters
    kwh_data = {}
    if kwh_data_list:
        kwh_data = HomeWizardDataProcessor.combine_kwh_data(kwh_data_list)
        data_manager.add_kwh_data(kwh_data)
        print(f"Totaal kWh data (alle meters): {kwh_data.get('active_power_w', 0)}W van {kwh_data.get('meter_count', 0)} meter(s)")

    # Stuur naar PVOutput
    if config.pvoutput_api_key and config.pvoutput_system_id:
        if not pvoutput_client:
            pvoutput_client = PVOutputClient(config.pvoutput_api_key, config.pvoutput_system_id)

        # Haal dagelijkse totalen op
        daily_totals = data_manager.get_daily_totals()

        # Converteer naar PVOutput formaat (met dagelijkse totalen)
        pvoutput_data = PVOutputDataConverter.convert_to_pvoutput(p1_data, kwh_data, daily_totals)

        if pvoutput_data:
            await pvoutput_client.add_status(
                energy_generation=pvoutput_data.get('energy_generation'),
                power_generation=pvoutput_data.get('power_generation'),
                energy_consumption=pvoutput_data.get('energy_consumption'),
                power_consumption=pvoutput_data.get('power_consumption')
            )
            print(f"Data naar PVOutput gestuurd: {pvoutput_data}")

async def scheduled_update_loop():
    """Achtergrond taak die periodiek data verzamelt en verstuurt"""
    while True:
        try:
            await collect_and_send_data()
        except Exception as e:
            print(f"Fout in scheduled update: {e}")

        # Wacht tot de volgende update
        await asyncio.sleep(config.update_interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Beheer de levenscyclus van de applicatie"""
    global update_task

    # Start achtergrond taak
    update_task = asyncio.create_task(scheduled_update_loop())
    print(f"Scheduled updates gestart (interval: {config.update_interval}s)")

    yield

    # Stop achtergrond taak
    if update_task:
        update_task.cancel()
        try:
            await update_task
        except asyncio.CancelledError:
            pass

# FastAPI app
app = FastAPI(
    title="HomeWizard naar PVOutput",
    description="Verzamel data van HomeWizard apparaten en stuur naar PVOutput",
    lifespan=lifespan
)

# Mount static files en templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Web routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Hoofd dashboard pagina"""
    return templates.TemplateResponse("index.html", {"request": request})

# API routes
@app.get("/api/status")
async def get_status():
    """Haal actuele status op"""
    kwh_meters = config.homewizard_kwh_meters_enabled
    return {
        "status": "running",
        "config": {
            "p1_enabled": config.homewizard_p1_enabled,
            "kwh_enabled": len(kwh_meters) > 0,
            "kwh_meter_count": len(kwh_meters),
            "pvoutput_configured": bool(config.pvoutput_api_key and config.pvoutput_system_id),
            "update_interval": config.update_interval
        }
    }

@app.get("/api/data/latest")
async def get_latest_data():
    """Haal nieuwste data op"""
    return data_manager.get_latest_data()

@app.get("/api/data/daily")
async def get_daily_totals():
    """Haal dagelijkse totalen op (voor PVOutput)"""
    return data_manager.get_daily_totals()

@app.get("/api/data/history")
async def get_history_data(hours: int = 1):
    """Haal historische data op"""
    if hours < 1 or hours > 24:
        raise HTTPException(status_code=400, detail="Hours moet tussen 1 en 24 zijn")
    return data_manager.get_history(hours)

@app.get("/api/data/statistics")
async def get_statistics():
    """Haal statistieken op"""
    stats = data_manager.get_statistics()

    # Voeg individuele kWh meter data toe als beschikbaar
    if data_manager.latest_kwh_data and 'meters' in data_manager.latest_kwh_data:
        stats['individual_kwh_meters'] = data_manager.latest_kwh_data['meters']

    return stats

@app.get("/api/config")
async def get_config():
    """Haal configuratie op (zonder gevoelige data)"""
    return {
        "homewizard_p1": {
            "host": config.homewizard_p1_host,
            "enabled": config.homewizard_p1_enabled
        },
        "homewizard_kwh_meters": config.homewizard_kwh_meters,
        "pvoutput": {
            "system_id": config.pvoutput_system_id,
            "api_key_configured": bool(config.pvoutput_api_key)
        },
        "update_interval": config.update_interval
    }

@app.post("/api/config")
async def update_config(new_config: Dict):
    """Update configuratie"""
    global p1_client, kwh_clients, pvoutput_client

    # Update config data
    if "homewizard_p1" in new_config:
        config.data["homewizard_p1"] = new_config["homewizard_p1"]
        p1_client = None  # Reset client

    if "homewizard_kwh_meters" in new_config:
        config.data["homewizard_kwh_meters"] = new_config["homewizard_kwh_meters"]
        kwh_clients = {}  # Reset alle kWh clients

    if "pvoutput" in new_config:
        config.data["pvoutput"] = new_config["pvoutput"]
        pvoutput_client = None  # Reset client

    if "update_interval" in new_config:
        config.data["update_interval"] = new_config["update_interval"]

    # Sla config op
    config.save()

    return {"status": "success", "message": "Configuratie opgeslagen"}

@app.post("/api/update-now")
async def trigger_update():
    """Forceer een onmiddellijke data update"""
    try:
        await collect_and_send_data()
        return {"status": "success", "message": "Data update uitgevoerd"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.webserver_host,
        port=config.webserver_port,
        reload=False
    )
