import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURAZIONE DASHBOARD ---
st.set_page_config(page_title="Simulatore Acustico Finestra Aperta", layout="wide")
st.title("🎛️ Analisi Parametrica: Attenuazione Finestra Aperta")

# --- SIDEBAR PER PARAMETRI DINAMICI ---
st.sidebar.header("Parametri Sorgente e Facciata")
lw_val = st.sidebar.slider("Potenza Sonora Lw [dB]", 80, 120, 100)
dist_s = st.sidebar.slider("Distanza Sorgente-Finestra [m]", 1, 100, 20)
alpha_f = st.sidebar.slider("Assorbimento Facciata [α]", 0.0, 1.0, 0.05)

st.sidebar.header("Geometria Finestra e Stanza")
thick_s = st.sidebar.slider("Spessore Mazzetta [m]", 0.0, 0.5, 0.2)
dist_int = st.sidebar.slider("Distanza Interna P' [m]", 0.5, 5.0, 2.0)
rt60 = st.sidebar.slider("Tempo di Riverbero [s]", 0.2, 2.0, 0.5)

# --- MOTORE DI CALCOLO (Versione Parametrica) ---
freqs = np.array([125, 250, 500, 1000, 2000, 4000])
wA = np.array([-16.1, -8.6, -3.2, 0, 1.2, 1.0]) # Pesi A

def calculate_attenuation(theta_deg):
    theta = np.radians(theta_deg)
    k = 2 * np.pi * freqs / 343
    R = np.sqrt(1 - alpha_f)
    
    # Esterno (Riflessione variabile)
    delta_p = 2 * 1.0 * np.cos(theta) 
    gain_refl = 10 * np.log10(1 + R**2 + 2*R*np.cos(k * delta_p) + 1e-10)
    lp_ext = (lw_val - 20*np.log10(dist_s) - 11) + gain_refl
    
    # Interno (Faro + Riverbero + Spessore)
    psi = (k * 1.0 / 2) * (np.sin(0) - np.sin(theta))
    dir_factor = (np.sinc(psi / np.pi))**2
    
    # Schermatura spessore (Maekawa)
    delta_s = thick_s * (1 - np.sin(np.pi/2 - theta))
    N = 2 * delta_s * freqs / 343
    att_thick = np.where(N > 0, 20*np.log10(np.sqrt(2*np.pi*N)/np.tanh(np.sqrt(2*np.pi*N))), 0)
    
    i_dir = (1.0 * np.cos(theta) * dir_factor) / (2 * np.pi * dist_int**2)
    i_riv = (4 * 1.0 * np.cos(theta)) / (0.161 * 50 / rt60)
    
    lp_int = 10 * np.log10(i_dir + i_riv) + (lw_val - 20*np.log10(dist_s) - 11) - att_thick
    
    # Somma dBA
    ext_dba = 10 * np.log10(np.sum(10**((lp_ext + wA)/10)))
    int_dba = 10 * np.log10(np.sum(10**((lp_int + wA)/10)))
    return ext_dba - int_dba

# --- GENERAZIONE GRAFICO ---
angles = np.linspace(0, 85, 90)
results = [calculate_attenuation(a) for a in angles]

fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
ax.plot(np.radians(angles), results, color='teal', lw=2)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_thetamin(0)
ax.set_thetamax(90)
ax.grid(True, ls=':')

# Visualizzazione nella App
st.pyplot(fig)

st.write(f"**Interpretazione:** L'attenuazione a 0° è di circa {calculate_attenuation(0):.1f} dBA.")