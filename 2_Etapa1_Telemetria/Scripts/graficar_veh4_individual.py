import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FormatStrFormatter
import os

# ==========================================
# CONFIGURACIÓN
# ==========================================
vehiculo_objetivo = "veh4"       # Vehículo a analizar
limite_tiempo = 30.0             # Tiempo máximo a graficar (segundos)
archivo_csv = f"{vehiculo_objetivo}_filtrado.csv"

# Configurar estilo general (más compacto para doble columna)
sns.set_theme(style="whitegrid", context="paper", font_scale=1.0)
plt.rcParams['axes.titleweight'] = 'bold'

if not os.path.exists(archivo_csv):
    print(f"Error: No se encontró {archivo_csv}")
    exit()

print(f"Procesando {archivo_csv} hasta {limite_tiempo}s...")

# ==========================================
# PROCESAMIENTO DE DATOS
# ==========================================
try:
    df = pd.read_csv(archivo_csv, on_bad_lines='skip')
except Exception as e:
    print(f"Error leyendo {archivo_csv}: {e}")
    exit()

# Renombrar columnas
columnas_esperadas = [
    'time', 'source', 'dest', 'proto', 'len', 
    'speed_raw', 'heading_raw', 'lat_raw', 'lon_raw'
]
if len(df.columns) == len(columnas_esperadas):
    df.columns = columnas_esperadas
else:
    print(f"Formato incorrecto. Columnas encontradas: {len(df.columns)}")
    exit()

# Limpieza y conversión de unidades
for col in ['time', 'speed_raw', 'heading_raw', 'lat_raw', 'lon_raw']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna()

# FILTRO DE TIEMPO: Solo hasta 30 segundos
df = df[df['time'] <= limite_tiempo].copy()

if df.empty:
    print(f"No hay datos hasta {limite_tiempo}s.")
    exit()

# Transformación matemática ETSI a unidades físicas
df['speed_ms'] = df['speed_raw'] / 100.0
df['heading_deg'] = df['heading_raw'] / 10.0
df['lat'] = df['lat_raw'] / 10000000.0
df['lon'] = df['lon_raw'] / 10000000.0
df['dt_ms'] = df['time'].diff() * 1000.0

# Aceleración suavizada
df['accel'] = df['speed_ms'].diff() / df['time'].diff()
df['accel_smooth'] = df['accel'].rolling(window=3, center=True).mean()

# Hacer el tiempo relativo a cero para que empiece en 0
df['time'] = df['time'] - df['time'].iloc[0]

# ==========================================
# GENERACIÓN DE GRÁFICAS INDIVIDUALES
# ==========================================

# 1. Velocidad
plt.figure(figsize=(6, 4)) # Tamaño ideal para 1 columna
sns.lineplot(data=df, x='time', y='speed_ms', color="#2980b9", linewidth=2.5)
plt.fill_between(df['time'], df['speed_ms'], alpha=0.15, color="#2980b9")
plt.title(f"Velocidad - {vehiculo_objetivo.upper()}")
plt.ylabel("Velocidad [m/s]"); plt.xlabel("Tiempo [s]"); plt.ylim(bottom=0)
plt.tight_layout()
plt.savefig(f"{vehiculo_objetivo}_1_velocidad.png", dpi=300, bbox_inches='tight')
plt.close()

# 2. Aceleración
plt.figure(figsize=(6, 4))
sns.lineplot(data=df, x='time', y='accel_smooth', color="#c0392b", linewidth=2.5)
plt.axhline(0.5, color='gray', linestyle='--', alpha=0.7)
plt.axhline(-0.5, color='gray', linestyle='--', alpha=0.7)
plt.axhline(0, color='black', linewidth=1, alpha=0.4)
plt.title(f"Aceleración - {vehiculo_objetivo.upper()}")
plt.ylabel("Aceleración [m/s²]"); plt.xlabel("Tiempo [s]")
plt.tight_layout()
plt.savefig(f"{vehiculo_objetivo}_2_aceleracion.png", dpi=300, bbox_inches='tight')
plt.close()

# 3. Cadencia (Intervalo)
plt.figure(figsize=(6, 4))
sns.lineplot(data=df, x='time', y='dt_ms', color="#8e44ad", linewidth=2)
plt.axhline(100, color='#e74c3c', linestyle='--', alpha=0.6)
plt.axhline(1000, color='#27ae60', linestyle='--', alpha=0.6)
plt.title(f"Cadencia CAM - {vehiculo_objetivo.upper()}")
plt.ylabel("Intervalo [ms]"); plt.xlabel("Tiempo [s]"); plt.ylim(0, 1200)
plt.tight_layout()
plt.savefig(f"{vehiculo_objetivo}_3_cadencia.png", dpi=300, bbox_inches='tight')
plt.close()

# 4. Rumbo
plt.figure(figsize=(6, 4))
sns.lineplot(data=df, x='time', y='heading_deg', color="#f39c12", linewidth=2.5)
plt.title(f"Rumbo - {vehiculo_objetivo.upper()}")
plt.ylabel("Grados (°)"); plt.xlabel("Tiempo [s]")
plt.yticks([0, 90, 180, 270, 360]); plt.ylim(-10, 370)
plt.tight_layout()
plt.savefig(f"{vehiculo_objetivo}_4_rumbo.png", dpi=300, bbox_inches='tight')
plt.close()

# 5. Trayectoria Geográfica con Tiempo (Mapa de calor)
plt.figure(figsize=(6, 4))
plt.plot(df['lon'], df['lat'], color='lightgray', alpha=0.5, zorder=1)
sc = plt.scatter(df['lon'], df['lat'], c=df['time'], cmap='viridis', s=20, zorder=2)
cbar = plt.colorbar(sc); cbar.set_label('Tiempo [s]', rotation=270, labelpad=15)
plt.title(f"Trayectoria - {vehiculo_objetivo.upper()}")
plt.xlabel("Longitud"); plt.ylabel("Latitud")
plt.gca().xaxis.set_major_formatter(FormatStrFormatter('%.5f'))
plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%.5f'))
plt.tight_layout()
plt.savefig(f"{vehiculo_objetivo}_5_trayectoria.png", dpi=300, bbox_inches='tight')
plt.close()

# 6. Reconstrucción con Vectores (Flechas)
plt.figure(figsize=(6, 4))
plt.plot(df['lon'], df['lat'], color='lightgray', linestyle='--', linewidth=1.5, zorder=1)
theta_rad = np.radians(90 - df['heading_deg'])
U = np.cos(theta_rad); V = np.sin(theta_rad)
step = max(1, len(df) // 20) # Menos flechas para no saturar en columna
plt.quiver(df['lon'][::step], df['lat'][::step], U[::step], V[::step], 
           color='#2c3e50', scale=15, alpha=0.8, headwidth=4, pivot='mid', zorder=2)
plt.title(f"Vectores de Rumbo - {vehiculo_objetivo.upper()}")
plt.xlabel("Longitud"); plt.ylabel("Latitud")
plt.gca().xaxis.set_major_formatter(FormatStrFormatter('%.5f'))
plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%.5f'))
plt.tight_layout()
plt.savefig(f"{vehiculo_objetivo}_6_vectores.png", dpi=300, bbox_inches='tight')
plt.close()

print("¡Proceso finalizado! Se generaron 6 imágenes individuales.")