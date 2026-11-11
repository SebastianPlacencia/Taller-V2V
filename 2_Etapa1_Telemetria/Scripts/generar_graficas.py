import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FormatStrFormatter

# Configurar estilo general
sns.set_theme(style="whitegrid", context="paper", font_scale=1.1)
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.titlesize'] = 13

archivos_csv = glob.glob("*_filtrado.csv")

if not archivos_csv:
    print("No se encontraron archivos CSV. Verifica la ruta.")
    exit()

for archivo in archivos_csv:
    veh_name = archivo.replace('_filtrado.csv', '').upper()
    print(f"Generando panel completo para {veh_name}...")

    try:
        df = pd.read_csv(archivo, on_bad_lines='skip')
    except Exception as e:
        print(f"Error leyendo {archivo}: {e}")
        continue

    # 1. Renombrar columnas
    columnas_esperadas = [
        'time', 'source', 'dest', 'proto', 'len', 
        'speed_raw', 'heading_raw', 'lat_raw', 'lon_raw'
    ]
    if len(df.columns) == len(columnas_esperadas):
        df.columns = columnas_esperadas
    else:
        print(f"Formato incorrecto en {archivo}. Saltando...")
        continue

    # 2. Limpieza de datos
    for col in ['time', 'speed_raw', 'heading_raw', 'lat_raw', 'lon_raw']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna()

    # 3. Transformación matemática ETSI a unidades físicas
    df['speed_ms'] = df['speed_raw'] / 100.0            # 0.01 m/s a m/s
    df['heading_deg'] = df['heading_raw'] / 10.0        # 0.1 grados a grados
    df['lat'] = df['lat_raw'] / 10000000.0              # 0.1 microgrados a grados decimales
    df['lon'] = df['lon_raw'] / 10000000.0
    df['dt_ms'] = df['time'].diff() * 1000.0            # ms entre paquetes
    
    # Aceleración suavizada
    df['accel'] = df['speed_ms'].diff() / df['time'].diff()
    df['accel_smooth'] = df['accel'].rolling(window=3, center=True).mean()

    # 4. Crear el lienzo de 3x2 (Más alto para acomodar los mapas)
    fig, axs = plt.subplots(3, 2, figsize=(16, 15), constrained_layout=True)
    fig.suptitle(f"Análisis Cinemático y de Red - {veh_name}", fontsize=18, fontweight='bold', color='#1a252f')

    # --- Gráfica 1: Velocidad ---
    ax = axs[0, 0]
    sns.lineplot(data=df, x='time', y='speed_ms', ax=ax, color="#2980b9", linewidth=2.5)
    ax.fill_between(df['time'], df['speed_ms'], alpha=0.15, color="#2980b9")
    ax.set_title("Velocidad vs Tiempo")
    ax.set_ylabel("Velocidad [m/s]")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylim(bottom=0)

    # --- Gráfica 2: Aceleración ---
    ax = axs[0, 1]
    sns.lineplot(data=df, x='time', y='accel_smooth', ax=ax, color="#c0392b", linewidth=2.5)
    ax.axhline(0.5, color='gray', linestyle='--', alpha=0.7, label="Umbral ETSI (+0.5)")
    ax.axhline(-0.5, color='gray', linestyle='--', alpha=0.7, label="Umbral ETSI (-0.5)")
    ax.axhline(0, color='black', linewidth=1, alpha=0.4)
    ax.set_title("Aceleración vs Tiempo")
    ax.set_ylabel("Aceleración [m/s²]")
    ax.set_xlabel("Tiempo [s]")
    ax.legend(loc='upper right')

    # --- Gráfica 3: Cadencia (Intervalo) ---
    ax = axs[1, 0]
    sns.lineplot(data=df, x='time', y='dt_ms', ax=ax, color="#8e44ad", linewidth=2)
    ax.axhline(100, color='#e74c3c', linestyle='--', alpha=0.6, label="Min 100ms")
    ax.axhline(1000, color='#27ae60', linestyle='--', alpha=0.6, label="Max 1000ms")
    ax.set_title("Cadencia de CAM (Intervalo)")
    ax.set_ylabel("Intervalo [ms]")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylim(0, 1200)
    ax.legend(loc='center right')

    # --- Gráfica 4: Rumbo ---
    ax = axs[1, 1]
    sns.lineplot(data=df, x='time', y='heading_deg', ax=ax, color="#f39c12", linewidth=2.5)
    ax.set_title("Rumbo (Heading) vs Tiempo")
    ax.set_ylabel("Grados (0-360)")
    ax.set_xlabel("Tiempo [s]")
    ax.set_yticks([0, 90, 180, 270, 360])
    ax.set_ylim(-10, 370)

    # ================= NUEVAS GRÁFICAS DE TRAYECTORIA ================= #

    # --- Gráfica 5: Trayectoria Geográfica con Degradado de Tiempo ---
    ax = axs[2, 0]
    ax.plot(df['lon'], df['lat'], color='lightgray', alpha=0.5, zorder=1) # Línea guía
    sc = ax.scatter(df['lon'], df['lat'], c=df['time'], cmap='viridis', s=40, edgecolor='white', linewidth=0.5, zorder=2)
    cbar = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Tiempo [s]', rotation=270, labelpad=15)
    ax.set_title("Trayectoria Geográfica (Color = Tiempo)")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.5f'))
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.5f'))

    # --- Gráfica 6: Reconstrucción de Ruta con Vectores (Flechas) ---
    ax = axs[2, 1]
    ax.plot(df['lon'], df['lat'], color='lightgray', linestyle='--', linewidth=2, zorder=1)
    
    # Conversión de Rumbo ETSI (N=0, E=90) a radianes matemáticos (E=0, N=90)
    theta_rad = np.radians(90 - df['heading_deg'])
    U = np.cos(theta_rad)
    V = np.sin(theta_rad)
    
    # Submuestreo para que las flechas no se amontonen (1 flecha aprox cada 30-40 paquetes)
    step = max(1, len(df) // 35)
    ax.quiver(df['lon'][::step], df['lat'][::step], U[::step], V[::step], 
              color='#2c3e50', scale=20, alpha=0.8, headwidth=4, pivot='mid', zorder=2)
              
    ax.set_title("Reconstrucción de Ruta (Flechas = Rumbo)")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.5f'))
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.5f'))

    # Guardado
    img_name = f"{veh_name}_analisis_completo.png"
    plt.savefig(img_name, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  -> Guardado exitosamente como {img_name}")

print("¡Proceso de graficado finalizado!")