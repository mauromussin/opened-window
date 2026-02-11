import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURAZIONE DASHBOARD ---
st.set_page_config(page_title="Simulatore Acustico Finestra", layout="wide")
st.title("🎛️ Simulatore Parametrico: Attenuazione dBA")
st.markdown("Analisi dell'attenuazione sonora con inclusione della banda a 100 Hz.")

# --- SIDEBAR: INPUT PARAMETRICI ---
st.sidebar.header("1. Potenza Sonora Sorgente (Lw)")
# Inserimento manuale per banda (inclusi i 100 Hz)
lw_100 = st.sidebar.number_input("100 Hz [dB]", value=106)
lw_125 = st.sidebar.number_input("125 Hz [dB]", value=105)
lw_250 = st.sidebar.number_input("250 Hz [dB]", value=102)
lw_500 = st.sidebar.number_input("500 Hz [dB]", value=100)
lw_1000 = st.sidebar.number_input("1000 Hz [dB]", value=98)
lw_2000 = st.sidebar.number_input("2000 Hz [dB]", value=95)
lw_4000 = st.sidebar.number_input("4000 Hz [dB]", value=90)

# Aggiornamento vettori
lw_octave = np.array([lw_100, lw_125, lw_250, lw_500, lw_1000, lw_2000, lw_4000])
freqs = np.array([100, 125, 250, 500, 1000, 2000, 4000])
# Pesatura A aggiornata (100 Hz = -19.1 dB)
wA = np.array([-19.1, -16.1, -8.6, -3.2, 0, 1.2, 1.0]) 

st.sidebar.header("2. Ambiente Esterno")
dist_s = st.sidebar.slider("Distanza Sorgente-Finestra [m]", 1, 100, 20)
alpha_f = st.sidebar.slider("Assorbimento Facciata [α]", 0.0, 1.0, 0.05)

st.sidebar.header("3. Geometria e Interno")
thick_s = st.sidebar.slider("Spessore Mazzetta [m]", 0.0, 0.5, 0.2)
dist_int = st.sidebar.slider("Distanza Interna P' [m]", 0.5, 5.0, 2.0)
rt60 = st.sidebar.slider("Tempo di Riverbero [s]", 0.2, 2.0, 0.5)

# --- MOTORE DI CALCOLO ---
def calculate_attenuation_dba(theta_deg):
    theta = np.radians(theta_deg)
    k = 2 * np.pi * freqs / 343
    R = np.sqrt(1 - alpha_f)
    area_W = 1.0
    V_room = 50.0
    A_room = 0.161 * V_room / rt60
    
    # --- ESTERNO (Punto P a 1m) ---
    lp_incidente = lw_octave - 20*np.log10(dist_s) - 11
    delta_p = 2 * 1.0 * np.cos(theta)
    gain_refl = 10 * np.log10(1 + R**2 + 2*R*np.cos(k * delta_p) + 1e-10)
    lp_ext = lp_incidente + gain_refl
    
    # --- INTERNO (Punto P' a dist_int) ---
    psi = (k * np.sqrt(area_W) / 2) * (np.sin(0) - np.sin(theta))
    dir_factor = (np.sinc(psi / np.pi))**2
    
    delta_s = thick_s * (1 - np.sin(np.pi/2 - theta))
    N = 2 * delta_s * freqs / 343
    att_thick = np.where(N > 0, 20*np.log10(np.sqrt(2*np.pi*N)/np.tanh(np.sqrt(2*np.pi*N))), 0)
    
    i_dir = (area_W * np.cos(theta) * dir_factor) / (2 * np.pi * dist_int**2)
    i_riv = (4 * area_W * np.cos(theta)) / A_room
    
    lp_int = 10 * np.log10(i_dir + i_riv + 1e-10) + lp_incidente - att_thick
    
    # --- SOMMA dBA ---
    lp_ext_weighted = lp_ext + wA
    lp_int_weighted = lp_int + wA
    
    ext_dba = 10 * np.log10(np.sum(10**(lp_ext_weighted/10)))
    int_dba = 10 * np.log10(np.sum(10**(lp_int_weighted/10)))
    
    return ext_dba - int_dba, ext_dba, int_dba, lp_ext_weighted, lp_int_weighted

# --- VISUALIZZAZIONE ---
angles = np.linspace(0, 85, 90)
res_all = [calculate_attenuation_dba(a) for a in angles]
att_vals = [r[0] for r in res_all]

col1, col2 = st.columns([2, 1])

with col1:
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8,8))
    ax.plot(np.radians(angles), att_vals, color='#D62728', lw=2.5, label='Attenuazione dBA')
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_thetamin(0)
    ax.set_thetamax(90)
    ax.legend(loc='lower right')
    st.pyplot(fig)

with col2:
    st.subheader("Analisi Spettrale (0°)")
    att_0, ext_0, int_0, spec_ext, spec_int = calculate_attenuation_dba(0)
    
    # Grafico a barre dello spettro dBA
    fig_spec, ax_spec = plt.subplots()
    x = np.arange(len(freqs))
    ax_spec.bar(x - 0.2, spec_ext, 0.4, label='Esterno (P)', color='#1f77b4')
    ax_spec.bar(x + 0.2, spec_int, 0.4, label='Interno (P\')', color='#ff7f0e')
    ax_spec.set_xticks(x)
    ax_spec.set_xticklabels([str(f) for f in freqs])
    ax_spec.set_ylabel("Livello [dBA]")
    ax_spec.legend()
    st.pyplot(fig_spec)
    
    st.metric("Attenuazione Globale", f"{att_0:.1f} dB")

