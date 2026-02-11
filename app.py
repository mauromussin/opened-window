import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Acoustic Wave Lab", layout="wide")

# --- NAVBAR LATERALE ---
st.sidebar.title("🎛️ Navigazione")
menu = st.sidebar.radio("Seleziona Approccio:", ["Home", "🎯 Modello Analitico", "🌊 Simulatore FDTD"])

# --- 0. PAGINA HOME ---
if menu == "Home":
    st.title("🔬 Studio dell'Isolamento di Facciata")
    st.markdown("""
    Benvenuto nel simulatore per lo studio della diffrazione e della direttività di un'apertura in facciata.
    
    ### Scegli un modulo per iniziare:
    * **🎯 Modello Analitico**: Calcolo rapido basato sulla fisica della diffrazione (Maekawa) e direttività (Sinc). Ideale per analisi parametriche e grafici polari.
    * **🌊 Simulatore FDTD**: Risoluzione numerica delle equazioni delle onde nel dominio del tempo. Ideale per visualizzare fisicamente come il fronte d'onda interagisce con la mazzetta.
    """)
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Diffraction_through_a_slit.svg/512px-Diffraction_through_a_slit.svg.png", caption="Esempio di diffrazione attraverso una fenditura.")

# --- 1. MODULO ANALITICO ---
elif menu == "🎯 Modello Analitico":
    st.title("🎯 Analisi Fisica dell'Attenuazione")
    
    st.sidebar.header("Parametri Fisici")
    s = st.sidebar.slider("Spessore Mazzetta (s) [m]", 0.0, 0.6, 0.2)
    w_width = st.sidebar.slider("Larghezza Finestra [m]", 0.5, 2.0, 1.0)
    d_mic = st.sidebar.slider("Distanza Ricevitore Interno [m]", 0.5, 5.0, 2.0)
    
    # Equalizzatore Sorgente
    st.subheader("Configura lo Spettro Sorgente (Lw)")
    freqs = np.array([100, 125, 250, 500, 1000, 2000, 4000, 5000])
    wA = np.array([-19.1, -16.1, -8.6, -3.2, 0, 1.2, 1.0, 0.5])
    
    cols = st.columns(len(freqs))
    lw_inputs = [cols[i].slider(f"{freqs[i]}Hz", 50, 110, 90, key=f"f{freqs[i]}") for i in range(len(freqs))]
    lw_octave = np.array(lw_inputs)

    def calculate_physics(theta_deg):
        theta = np.radians(theta_deg)
        k = 2 * np.pi * freqs / 343
        lp_inc = lw_octave - 11 # Semplificato
        
        # Diffrazione Mazzetta (Maekawa)
        delta = s * (1 - np.cos(theta))
        N = 2 * delta * freqs / 343
        att_diff = np.where(N > 0, 10 * np.log10(3 + 20*N), 0)
        
        # Direttività
        psi = (k * w_width / 2) * np.sin(theta)
        dir_factor = (np.sinc(psi / np.pi))**2
        
        lp_int = 10 * np.log10(dir_factor * np.cos(theta) / (2*np.pi*d_mic**2) + 1e-12) + lp_inc - att_diff
        
        ext_dba = 10 * np.log10(np.sum(10**((lp_inc + wA)/10)))
        int_dba = 10 * np.log10(np.sum(10**((lp_int + wA)/10)))
        return ext_dba - int_dba

    angles = np.linspace(0, 89, 90)
    att_vals = [calculate_physics(a) for a in angles]
    
    fig_pol, ax_pol = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(6,6))
    ax_pol.plot(np.radians(angles), att_vals, lw=3, color='royalblue')
    ax_pol.set_theta_zero_location("N")
    ax_pol.set_theta_direction(-1)
    ax_pol.set_thetamin(0)
    ax_pol.set_thetamax(90)
    st.pyplot(fig_pol)

# --- 2. MODULO FDTD ---
elif menu == "🌊 Simulatore FDTD":
    st.title("🌊 Simulazione Numerica Time-Domain")
    st.write("Modellazione del fronte d'onda piano inclinato.")

    col1, col2 = st.columns([1, 3])
    with col1:
        angle_inc = st.slider("Angolo Incidenza (°)", 0, 75, 30)
        thick_px = st.slider("Spessore Muro (px)", 2, 15, 6)
        run_sim = st.button("▶️ Avvia Simulazione")
    
    if run_sim:
        nx, ny = 120, 80
        p, p_prev = np.zeros((nx, ny)), np.zeros((nx, ny))
        mask = np.ones((nx, ny))
        wx, gap = 45, 16
        mask[wx : wx + thick_px, : ny//2 - gap//2] = 0
        mask[wx : wx + thick_px, ny//2 + gap//2 :] = 0
        
        theta_rad = np.radians(angle_inc)
        plot_placeholder = st.empty()
        
        for t in range(150):
            # Sorgente Planare
            for y in range(ny):
                delay = y * np.sin(theta_rad)
                p[5, y] += np.sin(0.4 * (t - delay)) * np.exp(-0.01 * (t - 30 - delay)**2)
            
            p_next = 2*p - p_prev + 0.25 * (np.roll(p,1,0)+np.roll(p,-1,0)+np.roll(p,1,1)+np.roll(p,-1,1)-4*p)
            p_next *= mask
            p_next[0,:] = p_next[-1,:] = p_next[:,0] = p_next[:,-1] = 0
            p_prev, p = p, p_next
            
            if t % 6 == 0:
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.imshow(p.T, cmap='RdBu', origin='lower', vmin=-0.4, vmax=0.4)
                ax.contour(mask.T, colors='black', levels=[0.5])
                ax.axis('off')
                plot_placeholder.pyplot(fig)
                plt.close(fig)
