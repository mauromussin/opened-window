import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Wave Physics Lab: Aperture Diffraction", layout="wide")

tab1, tab2 = st.tabs(["🎯 Modello Analitico (Diffrazione)", "🌊 Simulatore Numerico (FDTD)"])

# --- TAB 1: MODELLO ANALITICO FISICO ---
with tab1:
    st.title("Fisica della Diffrazione e Direttività")
    
    # Equalizzatore Potenza Sonora
    st.subheader("1. Spettro Sorgente (Lw)")
    freqs = np.array([100, 125, 250, 500, 1000, 2000, 4000, 5000])
    wA = np.array([-19.1, -16.1, -8.6, -3.2, 0, 1.2, 1.0, 0.5]) 
    default_lw = [106, 105, 102, 100, 98, 95, 90, 88]
    
    cols_lw = st.columns(len(freqs))
    lw_inputs = [cols_lw[i].slider(f"{freqs[i]}Hz", 50, 110, default_lw[i]) for i in range(len(freqs))]
    lw_octave = np.array(lw_inputs)

    # Parametri Geometrici
    st.sidebar.header("Parametri Fisici")
    s = st.sidebar.slider("Spessore Mazzetta (s) [m]", 0.0, 0.6, 0.2)
    w_width = st.sidebar.slider("Larghezza Apertura [m]", 0.5, 2.0, 1.0)
    d_src = st.sidebar.slider("Distanza Sorgente [m]", 2, 50, 15)
    d_mic = st.sidebar.slider("Distanza Ricevitore Interno [m]", 0.5, 5.0, 2.0)

    # Motore di Calcolo Fisico
    def calculate_physics(theta_deg):
        theta = np.radians(theta_deg)
        k = 2 * np.pi * freqs / 343
        
        # 1. Propagazione Esterna (Campo Libero)
        lp_incidente = lw_octave - 20*np.log10(d_src) - 11
        
        # 2. Diffrazione della Mazzetta (Maekawa)
        delta = s * (1 - np.cos(theta))
        N = 2 * delta * freqs / 343
        att_diff = np.where(N > 0, 10 * np.log10(3 + 20*N), 0)
        
        # 3. Direttività dell'Apertura (Modello Sinc)
        psi = (k * w_width / 2) * np.sin(theta)
        dir_factor = (np.sinc(psi / np.pi))**2
        
        # 4. Livello Interno (Pressione puntuale)
        # i_int proporzionale alla potenza incidente, direttività e divergenza interna
        i_int = (np.cos(theta) * dir_factor) / (2 * np.pi * d_mic**2)
        lp_int = 10 * np.log10(i_int + 1e-12) + lp_incidente - att_diff
        
        # Totali dBA
        ext_dba = 10 * np.log10(np.sum(10**((lp_incidente + wA)/10)))
        int_dba = 10 * np.log10(np.sum(10**((lp_int + wA)/10)))
        return ext_dba - int_dba, att_diff.mean()

    # Plot Polare
    angles = np.linspace(0, 89, 90)
    results = np.array([calculate_physics(a) for a in angles])
    
    fig_pol, ax_pol = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(7,7))
    ax_pol.plot(np.radians(angles), results[:, 0], lw=3, label="Attenuazione Totale [dB]")
    ax_pol.fill_between(np.radians(angles), 0, results[:, 1], color='g', alpha=0.2, label="Contributo Mazzetta")
    ax_pol.set_theta_zero_location("N")
    ax_pol.set_theta_direction(-1)
    ax_pol.set_thetamin(0)
    ax_pol.set_thetamax(90)
    ax_pol.legend()
    st.pyplot(fig_pol)

# --- TAB 2: SIMULATORE NUMERICO FDTD ---
with tab2:
    st.title("Simulatore Time-Domain (FDTD)")
    st.write("Risoluzione numerica dell'equazione delle onde $\\nabla^2 p - \\frac{1}{c^2}\\frac{\\partial^2 p}{\\partial t^2} = 0$.")
    
    c_sim = st.button("🚀 Avvia Calcolo Numerico")
    
    if c_sim:
        # Griglia e parametri
        nx, ny = 100, 70
        p, p_prev = np.zeros((nx, ny)), np.zeros((nx, ny))
        mask = np.ones((nx, ny))
        # Disegno muro
        wall_x, thick_px, gap_px = 35, 6, 12
        mask[wall_x : wall_x+thick_px, : ny//2 - gap_px//2] = 0
        mask[wall_x : wall_x+thick_px, ny//2 + gap_px//2 :] = 0
        
        disp = st.empty()
        for t in range(150):
            # Sorgente pulsata
            p[5, ny//2] += np.sin(0.5 * t) * np.exp(-0.01 * (t-40)**2)
            
            # Update FDTD
            p_next = 2*p - p_prev + 0.25 * (np.roll(p,1,0)+np.roll(p,-1,0)+np.roll(p,1,1)+np.roll(p,-1,1)-4*p)
            p_next *= mask # Parete rigida
            p_prev, p = p, p_next
            
            if t % 5 == 0:
                fig, ax = plt.subplots()
                ax.imshow(p.T, cmap='RdGy', vmin=-0.2, vmax=0.2, origin='lower')
                ax.contour(mask.T, colors='cyan', levels=[0.5])
                ax.axis('off')
                disp.pyplot(fig)
                plt.close(fig)
