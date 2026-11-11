import os
import subprocess
import glob

# Busca todos los archivos .pcap que empiecen con "veh"
archivos_pcap = glob.glob("veh*.pcap")

if not archivos_pcap:
    print("No se encontraron archivos .pcap.")
    exit()

for pcap in archivos_pcap:
    csv_out = pcap.replace(".pcap", "_filtrado.csv")
    print(f"Procesando {pcap} -> {csv_out}...")

    cmd = [
        "tshark", "-r", pcap,
        "-Y", "its",                  # Filtro aplicado
        "-T", "fields",
        "-e", "frame.time_relative",  # Time
        "-e", "_ws.col.Source",       # Source
        "-e", "_ws.col.Destination",  # Destination
        "-e", "_ws.col.Protocol",     # Protocol
        "-e", "frame.len",            # Length
        "-e", "its.speedValue",       # speedValue corregido
        "-e", "its.headingValue",     # headingValue corregido
        "-e", "its.latitude",         # latitude corregido
        "-e", "its.longitude",        # longitude corregido
        "-E", "header=y",             
        "-E", "separator=,",          
        "-E", "quote=d"               
    ]

    with open(csv_out, "w") as f_out:
        subprocess.run(cmd, stdout=f_out, text=True)

print("¡Extracción completada con éxito!")