import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Analisi Diffrazione UNI/TR 11175", layout="wide")
st.title("🎛️ Scomposizione dell'Attenuazione: Norma vs Fisica")

# --- EQUALIZZATORE SORGENTE ---
st.subheader("1. Spettro di Potenza Sonora (Lw)")
cols_lw = st.columns(7)
freq_labels = ["100 Hz", "125 Hz", "250 Hz", "500 Hz", "1000 Hz", "2000 Hz", "4000 Hz"]
default_vals = [106, 105, 102, 100, 98, 95, 90]
lw_inputs = []
for i, col in enumerate(cols_lw):
    with col:
        val = st.slider(freq_labels[i], 70, 110, default_vals[i], key=f"lw_{i}")
        lw_inputs.append(val)

lw_octave = np.array(lw_inputs)
freqs = np.array([100, 125, 250, 500, 1000, 2000, 4000])
wA = np.array([-19.1, -16.1, -8.6, -3.2, 0, 1.2, 1.0]) 

# --- SIDEBAR ---
st.sidebar.header("Parametri Geometrici")
tipo_facciata = st.sidebar.selectbox("Fattore Forma", ["Piana (Standard)", "Nicchia Profonda", "Presenza di Balcone", "Strada Canyon"])
thick_s = st.sidebar.slider("Spessore Mazzetta (s) [m]", 0.0, 0.5, 0.2)
dist_int = st.sidebar.slider("Distanza Interna P' [m]", 0.5, 5.0, 2.0)
dist_s = st.sidebar.slider("Distanza Sorgente [m]", 1, 100, 20)
rt60 = st.sidebar.slider("Tempo di Riverbero [s]", 0.2, 2.0, 0.5)

# --- MOTORE DI CALCOLO SCOMPOSTO ---
def calculate_all_components(theta_deg):
    theta = np.radians(theta_deg)
    k = 2 * np.pi * freqs / 343
    A_room = 0.161 * 50 / rt60
    area_W = 1.0
    
    # 1. LIVELLO ESTERNO (P)
    lp_incidente = lw_octave - 20*np.log10(dist_s) - 11
    # Guadagno facciata + forma
    gain_facade = 10 * np.log10(1 + 0.95 + 2*0.97*np.cos(k * 2 * np.cos(theta)) + 1e-10)
    shape_map = {"Piana (Standard)": 0, "Nicchia Profonda": -2, "Presenza di Balcone": 2.5, "Strada Canyon": -3}
    lp_ext = lp_incidente + gain_facade - shape_map[tipo_facciata]
    
    # 2. COMPONENTE ISO 12354 (Solo campo riverberato medio)
    i_riv = (4 * area_W * np.cos(theta)) / A_room
    lp_int_iso = 10 * np.log10(i_riv + 1e-10) + lp_incidente
    
    # 3. COMPONENTE DIFFRAZIONE E DIRETIVITÀ (Faro + Spessore)
    psi = (k * np.sqrt(area_W) / 2) * (np.sin(0) - np.sin(theta))
    dir_factor = (np.sinc(psi / np.pi))**2
    delta_s = thick_s * (1 - np.sin(np.pi/2 - theta))
    N = 2 * delta_s * freqs / 343
    att_thick = np.where(N > 0, 20*np.log10(np.sqrt(2*np.pi*N)/np.tanh(np.sqrt(2*np.pi*N))), 0)
    
    # Livello interno totale (Fisico)
    i_dir = (area_W * np.cos(theta) * dir_factor) / (2 * np.pi * dist_int**2)
    lp_int_total = 10 * np.log10(i_dir + i_riv + 1e-10) + lp_incidente - att_thick
    
    # --- PESATURA A E SOMME ---
    def to_dba(lp_array): return 10 * np.log10(np.sum(10**((lp_array + wA)/10)))
    
    ext_dba = to_dba(lp_ext)
    iso_dba = to_dba(lp_int_iso)
    total_int_dba = to_dba(lp_int_total)
    
    # Calcolo differenze
    att_iso = ext_dba - iso_dba
    att_total = ext_dba - total_int_dba
    diffraction_loss = att_total - att_iso # Il contributo della fisica aggiuntiva
    
    return att_iso, diffraction_loss, att_total

# --- GRAFICA ---
angles = np.linspace(0, 85, 90)
res = np.array([calculate_all_components(a) for a in angles])

fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8,8))
ax.plot(np.radians(angles), res[:,0], 'r--', label='ISO 12354 (Base)', alpha=0.7)
ax.plot(np.radians(angles), res[:,1], 'g:', label='Contributo Diffrazione/Mazzetta')
ax.plot(np.radians(angles), res[:,2], 'b-', lw=3, label='Attenuazione Totale (Modello)')

ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_thetamin(0)
ax.set_thetamax(90)
ax.set_ylim(bottom=0)
ax.legend(loc='lower right')
st.pyplot(fig)

st.info("**Legenda:** La linea tratteggiata rossa è l'isolamento teorico normativo. La linea blu mostra come la direttività e la mazzetta aumentino l'isolamento reale agli angoli radenti.")



