import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Analisi Coerente UNI/TR 11175", layout="wide")
st.title("🎛️ Scomposizione Fisica dell'Attenuazione (100Hz - 5000Hz)")

# --- AREA POTENZA SONORA (EQUALIZZATORE) ---
st.subheader("1. Spettro di Potenza Sonora della Sorgente (Lw)")
st.write("Regola i cursori per definire lo spettro della sorgente stradale.")

freqs = np.array([100, 125, 250, 500, 1000, 2000, 4000, 5000])
wA = np.array([-19.1, -16.1, -8.6, -3.2, 0, 1.2, 1.0, 0.5]) # Pesatura A incl. 5k
default_lw = [106, 105, 102, 100, 98, 95, 90, 88]

cols_lw = st.columns(len(freqs))
lw_inputs = []

for i, col in enumerate(cols_lw):
    with col:
        val = st.slider(f"{freqs[i]} Hz", 70, 110, default_lw[i], key=f"lw_{freqs[i]}")
        lw_inputs.append(val)

lw_octave = np.array(lw_inputs)

# --- SIDEBAR: PARAMETRI FISICI ---
st.sidebar.header("2. Parametri Geometrici")
thick_s = st.sidebar.slider("Spessore Mazzetta (s) [m]", 0.0, 0.5, 0.2)
dist_s = st.sidebar.slider("Distanza Sorgente [m]", 1, 100, 20)
dist_int = st.sidebar.slider("Distanza Interna P' [m]", 0.5, 5.0, 2.0)
rt60 = st.sidebar.slider("Tempo di Riverbero [s]", 0.2, 2.0, 0.5)

st.sidebar.header("3. Fattore di Forma")
tipo_facciata = st.sidebar.selectbox(
    "Geometria Facciata", 
    ["Piana (Standard)", "Nicchia Profonda", "Presenza di Balcone", "Strada Canyon"]
)

# --- MOTORE DI CALCOLO COERENTE ---
def calculate_components(theta_deg):
    theta = np.radians(theta_deg)
    c = 343
    k = 2 * np.pi * freqs / c
    area_W = 1.0
    V_room = 50.0
    A_room = 0.161 * V_room / rt60
    
    # 1. LIVELLO ESTERNO (P)
    lp_incidente = lw_octave - 20*np.log10(dist_s) - 11
    # Guadagno facciata base + correzione UNI/TR 11175
    shape_map = {"Piana (Standard)": 0, "Nicchia Profonda": -2, "Presenza di Balcone": 2.5, "Strada Canyon": -3}
    lp_ext = lp_incidente + 3 - shape_map[tipo_facciata]
    
    # 2. CURVA ISO 12354 (Solo proiezione e riverbero)
    i_iso = (4 * area_W * np.cos(theta)) / A_room
    lp_int_iso = 10 * np.log10(i_iso + 1e-10) + lp_incidente
    
    # 3. CURVA DIFFRAZIONE (Mazzetta)
    # Coerenza fisica: delta = s * (1 - cos(theta))
    delta = thick_s * (1 - np.cos(theta))
    N = 2 * delta * freqs / c
    att_diff_freq = np.where(N > 0, 10 * np.log10(3 + 20*N), 0)
    
    # 4. MODELLO COMPLETO (Inclusa Direttività Sinc)
    psi = (k * np.sqrt(area_W) / 2) * (np.sin(0) - np.sin(theta))
    dir_factor = (np.sinc(psi / np.pi))**2
    i_dir = (area_W * np.cos(theta) * dir_factor) / (2 * np.pi * dist_int**2)
    
    lp_int_tot = 10 * np.log10(i_dir + i_iso + 1e-10) + lp_incidente - att_diff_freq
    
    # Pesatura A e Totali
    def to_dba(lp): return 10 * np.log10(np.sum(10**((lp + wA)/10)))
    
    val_ext = to_dba(lp_ext)
    val_iso = val_ext - to_dba(lp_int_iso)
    val_tot = val_ext - to_dba(lp_int_tot)
    val_diff = val_tot - val_iso # Contributo puro della fisica mazzetta/diffrazione
    
    return val_iso, val_diff, val_tot

# --- GRAFICA ---
angles = np.linspace(0, 89, 90)
res = np.array([calculate_components(a) for a in angles])

col_plot, col_table = st.columns([2, 1])

with col_plot:
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8,8))
    ax.plot(np.radians(angles), res[:, 0], 'r--', label='ISO 12354 (Teorica)')
    ax.plot(np.radians(angles), res[:, 1], 'g:', label='Delta Diffrazione (Mazzetta)')
    ax.plot(np.radians(angles), res[:, 2], 'b-', lw=3, label='Attenuazione Totale')
    
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_thetamin(0)
    ax.set_thetamax(90)
    ax.legend(loc='lower right')
    st.pyplot(fig)

with col_table:
    st.subheader("Analisi Comparativa")
    # Tabella rapida per tre angoli chiave
    test_angles = [0, 45, 80]
    for a in test_angles:
        v_iso, v_diff, v_tot = calculate_components(a)
        st.write(f"**Angolo {a}°**")
        st.write(f"- ISO 12354: {v_iso:.1f} dB")
        st.write(f"- Bonus Fisico: +{v_diff:.1f} dB")
        st.write(f"- Totale Reale: {v_tot:.1f} dB")
        st.write("---")

st.info("💡 **Osservazione:** Nota come a 0° il 'Bonus Fisico' sia nullo, confermando la coerenza del modello con la teoria della diffrazione.")
