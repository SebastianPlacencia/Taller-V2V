# Taller V2V: Telemetría ETSI y Sombra Digital en SUMO

Este repositorio contiene el desarrollo completo del taller de Redes Vehiculares y Heterogéneas, dividido en dos etapas: la captura de telemetría real mediante mensajes CAM (ETSI ITS-G5) y la creación de una Sombra Digital (Digital Twin) en SUMO.

## Estructura del Repositorio

### 1_Recursos_Base
Contiene los archivos de configuración del mapa de Cuenca (`zona_final.net.xml`), las rutas generadas para los vehículos (`zona_final.rou.xml`) y el archivo de configuración de SUMO (`zona_final.sumocfg`). Estos archivos son la base para ambas etapas.

### 2_Etapa1_Telemetria
Aquí se encuentra todo el proceso de captura y análisis de los mensajes V2V.
- **Datos_Crudos_PCAP:** Archivos de captura de red (`.pcap`) generados por ns-3 para cada vehículo.
- **Datos_Filtrados_CSV:** Archivos CSV con los campos del CAM extraídos (tiempo, velocidad, rumbo, latitud, longitud).
- **Scripts:** 
  - `extraer_datos.py`: Automatiza la conversión de `.pcap` a CSV usando `tshark`.
  - `generar_graficas.py`: Procesa los CSV y genera paneles de análisis (velocidad, aceleración, cadencia, rumbo, trayectoria).
  - `graficar_veh4_individual.py`: Script específico para generar las gráficas individuales del vehículo 4.
- **Graficas:** Imágenes en PNG con los resultados del análisis cinemático de los vehículos.

### 3_Etapa2_Sombra_Digital
Implementación de la Sombra Digital. Contiene el script `sombra_digital.py`, que utiliza TraCI para inyectar la telemetría real en SUMO, junto con los archivos de configuración visual (`gui-settings.xml`) y los datos de los vehículos 4 y 5 necesarios para la reproducción.

## Ejecución

Para ejecutar la Etapa 1, asegúrate de tener `tshark` instalado y ejecuta:
```bash
python3 extraer_datos.py
python3 generar_graficas.py
