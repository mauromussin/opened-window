import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURAZIONE DASHBOARD ---
st.set_page_config(page_title="Simulatore Acustico UNI/TR 11175", layout="wide")
st.title("🎛️ Simulatore Parametrico: Attenuazione dBA")

# --- AREA POTENZA SONORA (EQUALIZZATORE) ---
st.subheader("1. Spettro di Potenza Sonora della Sorgente (Lw)")
st.write("Regola i cursori per definire i dB per ciascuna banda d'ottava (70 - 110 dB).")

# Creazione di 7 colonne per gli slider (uno per ogni banda)
cols_lw = st.columns(7)
freq_labels = ["100 Hz", "125 Hz", "250 Hz", "500 Hz", "1000 Hz", "2000 Hz", "4000 Hz"]
default_vals = [106, 105, 102, 100, 98, 95, 90]
lw_inputs = []

for i, col in enumerate(cols_lw):
    with col:
        # Nota: Streamlit non ha un parametro 'vertical' nativo per gli slider standard, 
        # ma disporli in colonne strette crea l'effetto "mixer/equalizzatore".
        val = st.slider(freq_labels[i], 70, 110, default_vals[i], key=f"lw_{i}")
        lw_inputs.append(val)

lw_octave = np.array(lw_inputs)
freqs = np.array([100, 125, 250, 500, 1000, 2000, 4000])
wA = np.array([-19.1, -16.1, -8.6, -3.2, 0, 1.2, 1.0]) 

# --- SIDEBAR: ALTRI PARAMETRI ---
st.sidebar.header("2. Fattore di Forma (UNI/TR 11175)")
tipo_facciata = st.sidebar.selectbox(
    "Geometria della Facciata",
    ["Piana (Standard)", "Nicchia Profonda", "Presenza di Balcone", "Strada Canyon"]
)
alpha_f = st.sidebar.slider("Assorbimento Facciata [α]", 0.0, 1.0, 0.05)

st.sidebar.header("3. Geometria e Interno")
thick_s = st.sidebar.slider("Spessore Mazzetta [m]", 0.0, 0.5, 0.2)
dist_s = st.sidebar.slider("Distanza Sorgente-Finestra [m]", 1, 100, 20)
dist_int = st.sidebar.slider("Distanza Interna P' [m]", 0.5, 5.0, 2.0)
rt60 = st.sidebar.slider("Tempo di Riverbero [s]", 0.2, 2.0, 0.5)

# --- MOTORE DI CALCOLO ---
def get_shape_factor_db(tipo):
    factors = {"Piana (Standard)": 0.0, "Nicchia Profonda": -2.0, "Presenza di Balcone": 2.5, "Strada Canyon": -3.0}
    return factors[tipo]

def calculate_physics(theta_deg):
    theta = np.radians(theta_deg)
    k = 2 * np.pi * freqs / 343
    R_coef = np.sqrt(1 - alpha_f)
    area_W = 1.0 
    V_room = 50.0 
    A_room = 0.161 * V_room / rt60
    
    lp_incidente = lw_octave - 20*np.log10(dist_s) - 11
    delta_p = 2 * 1.0 * np.cos(theta)
    gain_refl = 10 * np.log10(1 + R_coef**2 + 2*R_coef*np.cos(k * delta_p) + 1e-10)
    
    dl_fs = get_shape_factor_db(tipo_facciata)
    lp_ext = lp_incidente + gain_refl - dl_fs 
    
    psi = (k * np.sqrt(area_W) / 2) * (np.sin(0) - np.sin(theta))
    dir_factor = (np.sinc(psi / np.pi))**2
    
    delta_s = thick_s * (1 - np.sin(np.pi/2 - theta))
    N = 2 * delta_s * freqs / 343
    att_thick = np.where(N > 0, 20*np.log10(np.sqrt(2*np.pi*N)/np.tanh(np.sqrt(2*np.pi*N))), 0)
    
    i_dir = (area_W * np.cos(theta) * dir_factor) / (2 * np.pi * dist_int**2)
    i_riv = (4 * area_W * np.cos(theta)) / A_room
    
    lp_int = 10 * np.log10(i_dir + i_riv + 1e-10) + lp_incidente - att_thick
    
    spec_ext_dba = lp_ext + wA
    spec_int_dba = lp_int + wA
    total_ext_dba = 10 * np.log10(np.sum(10**(spec_ext_dba/10)))
    total_int_dba = 10 * np.log10(np.sum(10**(spec_int_dba/10)))
    
    return total_ext_dba - total_int_dba, total_ext_dba, total_int_dba, spec_ext_dba, spec_int_dba

# --- VISUALIZZAZIONE ---
angles = np.linspace(0, 85, 90)
data = [calculate_physics(a) for a in angles]
att_plot = [d[0] for d in data]

col_main, col_stats = st.columns([2, 1])

with col_main:
    st.subheader("Risposta Polare dell'Attenuazione")
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(7,7))
    ax.plot(np.radians(angles), att_plot, color='#1c91ff', lw=3)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_thetamin(0)
    ax.set_thetamax(90)
    st.pyplot(fig)

with col_stats:
    st.subheader("Valori a 0°")
    att_0, ext_0, int_0, s_ext, s_int = calculate_physics(0)
    st.metric("Esterno", f"{ext_0:.1f} dBA")
    st.metric("Interno", f"{int_0:.1f} dBA")
    st.metric("Delta dBA", f"{att_0:.1f} dB")
    
    # Grafico spettro dBA
    fig_bar, ax_bar = plt.subplots(figsize=(5,4))
    ax_bar.bar(freq_labels, s_ext, alpha=0.5, label='P (Est)', color='gray')
    ax_bar.bar(freq_labels, s_int, alpha=0.8, label="P' (Int)", color='#1c91ff')
    ax_bar.set_ylabel("dB(A)")
    ax_bar.legend()
    st.pyplot(fig_bar)

st.divider()
st.info(f"Geometria: {tipo_facciata} | Spessore: {thick_s}m | Distanza Interna: {dist_int}m")


