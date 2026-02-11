import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Analisi Coerente UNI/TR 11175", layout="wide")
st.title("🎛️ Scomposizione Fisica dell'Attenuazione")

# --- SIDEBAR PARAMETRI ---
st.sidebar.header("Parametri Modello")
thick_s = st.sidebar.slider("Spessore Mazzetta (s) [m]", 0.0, 0.5, 0.2)
dist_s = st.sidebar.slider("Distanza Sorgente [m]", 1, 100, 20)
rt60 = st.sidebar.slider("Tempo di Riverbero [s]", 0.2, 2.0, 0.5)

# Equalizzatore (semplificato per brevità, ma coerente)
freqs = np.array([100, 125, 250, 500, 1000, 2000, 4000])
wA = np.array([-19.1, -16.1, -8.6, -3.2, 0, 1.2, 1.0]) 
lw_vals = np.array([106, 105, 102, 100, 98, 95, 90]) # Potenza standard

# --- MOTORE DI CALCOLO COERENTE ---
def calculate_components(theta_deg):
    theta = np.radians(theta_deg)
    c = 343
    k = 2 * np.pi * freqs / c
    
    # 1. LIVELLO ESTERNO (P) - Riferimento
    # Includiamo il guadagno di facciata standard (+3dB medio)
    lp_incidente = lw_vals - 20*np.log10(dist_s) - 11
    lp_ext = lp_incidente + 3 
    
    # --- CURVA 1: ISO 12354 (Solo proiezione geometrica) ---
    # Attenuazione dovuta alla riduzione dell'area apparente
    # Aggiungiamo un termine di base dovuto al riverbero interno
    A_room = 0.161 * 50 / rt60
    i_iso = (4 * 1.0 * np.cos(theta)) / A_room
    lp_int_iso = 10 * np.log10(i_iso + 1e-10) + lp_incidente
    
    # --- CURVA 2: EFFETTO DIFFRAZIONE/MAZZETTA ---
    # delta = s * (1 - cos(theta)) -> a 0 gradi delta = 0
    delta = thick_s * (1 - np.cos(theta))
    N = 2 * delta * freqs / c
    # Maekawa continua per il contributo della diffrazione
    att_diff_freq = np.where(N > 0, 10 * np.log10(3 + 20*N), 0)
    
    # --- CURVA 3: TOTALE (Modello Fisico Completo) ---
    # Aggiungiamo la direttività (Sinc)
    psi = (k * 1.0 / 2) * (np.sin(0) - np.sin(theta))
    dir_factor = (np.sinc(psi / np.pi))**2
    i_dir = (1.0 * np.cos(theta) * dir_factor) / (2 * np.pi * 2.0**2) # d_int = 2m
    
    lp_int_tot = 10 * np.log10(i_dir + i_iso + 1e-10) + lp_incidente - att_diff_freq
    
    # Funzione per pesatura A
    def to_dba(lp): return 10 * np.log10(np.sum(10**((lp + wA)/10)))
    
    val_ext = to_dba(lp_ext)
    val_iso = val_ext - to_dba(lp_int_iso)
    val_tot = val_ext - to_dba(lp_int_tot)
    val_diff = val_tot - val_iso
    
    return val_iso, val_diff, val_tot

# --- GRAFICA ---
angles = np.linspace(0, 89, 90)
results = np.array([calculate_components(a) for a in angles])

fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8,8))
ax.plot(np.radians(angles), results[:, 0], 'r--', label='ISO 12354 (Area proiettata)')
ax.plot(np.radians(angles), results[:, 1], 'g:', label='Contributo Diffrazione (Mazzetta)')
ax.plot(np.radians(angles), results[:, 2], 'b-', lw=3, label='Attenuazione Totale')

ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_thetamin(0)
ax.set_thetamax(90)
ax.set_ylim(0, max(results[:, 2]) + 5)
ax.legend(loc='lower right')
st.pyplot(fig)
