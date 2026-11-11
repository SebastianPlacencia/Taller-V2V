import os
import sys
import time
import pandas as pd

# Asegurar que las herramientas de SUMO (TraCI y sumolib) estén en el PATH
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
    sys.exit("Por favor, declara la variable de entorno 'SUMO_HOME'")

import traci
import sumolib

def crear_configuracion_visual():
    """Crea un archivo XML en tiempo real para forzar la configuración visual de SUMO"""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<viewsettings>
    <!-- Establece el fondo verde (Real World) por defecto -->
    <scheme name="real world"/>
    <!-- Etiquetas correctas para SUMO 1.12.0: exageración a 30 y muestra de nombres -->
    <vehicles vehicle_exaggeration="30.00" vehicleName_show="true" vehicleName_size="60.00" vehicleName_color="0,0,0,255" vehicleName_bgColor="255,255,255,180" vehicleName_constantSize="true"/>
</viewsettings>
"""
    with open("gui-settings.xml", "w") as f:
        f.write(xml_content)
    return "gui-settings.xml"

def preparar_datos():
    archivos = ['veh4_filtrado.csv', 'veh5_filtrado.csv']
    dfs = []
    for arch in archivos:
        if not os.path.exists(arch):
            print(f"Advertencia: No se encontró {arch}")
            continue
            
        df = pd.read_csv(arch, on_bad_lines='skip')
        
        df.columns = ['time', 'source', 'dest', 'proto', 'len', 'speed_raw', 'heading_raw', 'lat_raw', 'lon_raw']
        
        for col in ['time', 'speed_raw', 'heading_raw', 'lat_raw', 'lon_raw']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna()
        
        # Dejamos el ID tal cual viene del archivo ('veh4' o 'veh5')
        veh_id = arch.split('_')[0] 
        df['veh_id'] = veh_id
        
        df['speed'] = df['speed_raw'] / 100.0
        df['heading'] = df['heading_raw'] / 10.0
        df['lat'] = df['lat_raw'] / 10000000.0
        df['lon'] = df['lon_raw'] / 10000000.0
        dfs.append(df)
        
    if not dfs:
        sys.exit("No hay datos para procesar.")
        
    df_all = pd.concat(dfs).sort_values(by='time').reset_index(drop=True)
    return df_all

def main():
    print("Cargando datos, mapa y configuraciones visuales...")
    df_eventos = preparar_datos()
    
    # 1. Generar la configuración visual
    archivo_gui = crear_configuracion_visual()
    
    net_file = "zona_final.net.xml"
    net = sumolib.net.readNet(net_file)
    
    # 2. Iniciar SUMO inyectando el archivo '-g gui-settings.xml'
    sumoCmd = ["sumo-gui", "-n", net_file, "-g", archivo_gui, "--step-length", "0.05"]
    traci.start(sumoCmd)
    
    edges = [e.getID() for e in net.getEdges()]
    traci.route.add("ruta_sombra", [edges[0]])
    
    tiempo_simulacion = 0.0
    indice_evento = 0
    total_eventos = len(df_eventos)
    
    print("Iniciando inyección de telemetría (Sombra Digital)...")
    
    while indice_evento < total_eventos:
        
        while indice_evento < total_eventos and df_eventos.loc[indice_evento, 'time'] <= tiempo_simulacion:
            evento = df_eventos.loc[indice_evento]
            v_id = evento['veh_id']
            
            try:
                traci.vehicle.getSpeed(v_id)
            except traci.exceptions.TraCIException:
                # Si el vehículo no existe en el mapa, lo creamos/revivimos
                traci.vehicle.add(v_id, "ruta_sombra")
                traci.vehicle.setSpeedMode(v_id, 0)
                traci.vehicle.setLaneChangeMode(v_id, 0)
                traci.vehicle.setColor(v_id, (255, 0, 0) if v_id == 'veh4' else (0, 0, 255))
            
            x, y = net.convertLonLat2XY(evento['lon'], evento['lat'])
            
            traci.vehicle.moveToXY(v_id, "", -1, x, y, angle=evento['heading'], keepRoute=2)
            traci.vehicle.setSpeed(v_id, evento['speed'])
            
            indice_evento += 1
            
        traci.simulationStep()
        tiempo_simulacion += 0.05
        time.sleep(0.02) 

    traci.close()
    print("¡Reproducción de la Sombra Digital finalizada!")

if __name__ == "__main__":
    main()