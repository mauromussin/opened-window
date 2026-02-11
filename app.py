import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Wave Physics Lab: FDTD Beamsteering", layout="wide")

tab1, tab2 = st.tabs(["🎯 Modello Analitico", "🌊 Simulatore Onde 2D (FDTD)"])

# --- TAB 1: MODELLO ANALITICO (Fisica Pura) ---
with tab1:
    st.title("Analisi della Direttività e Diffrazione")
    
    # Input principali
    freqs = np.array([100, 125, 250, 500, 1000, 2000, 4000, 5000])
    wA = np.array([-19.1, -16.1, -8.6, -3.2, 0, 1.2, 1.0, 0.5]) 
    
    col_inp1, col_inp2 = st.columns([1, 1])
    with col_inp1:
        s = st.slider("Spessore Mazzetta (s) [m]", 0.0, 0.6, 0.2)
        w_width = st.slider("Larghezza Finestra [m]", 0.5, 2.0, 1.0)
    with col_inp2:
        d_mic = st.slider("Distanza Ricevitore P' [m]", 0.5, 5.0, 2.0)
        f_target = st.select_slider("Frequenza Analisi Polare [Hz]", options=freqs, value=1000)

    def calculate_physics(theta_deg):
        theta = np.radians(theta_deg)
        k = 2 * np.pi * freqs / 343
        lp_inc = 100 # Riferimento
        
        # Diffrazione Mazzetta
        delta = s * (1 - np.cos(theta))
        N = 2 * delta * freqs / 343
        att_diff = np.where(N > 0, 10 * np.log10(3 + 20*N), 0)
        
        # Direttività (Sinc)
        psi = (k * w_width / 2) * np.sin(theta)
        dir_factor = (np.sinc(psi / np.pi))**2
        
        lp_int = 10 * np.log10(dir_factor * np.cos(theta) / (2*np.pi*d_mic**2) + 1e-12) + lp_inc - att_diff
        return lp_inc - lp_int

    angles = np.linspace(0, 89, 90)
    att_vals = [calculate_physics(a).mean() for a in angles]
    
    fig_pol, ax_pol = plt.subplots(subplot_kw={'projection': 'polar'})
    ax_pol.plot(np.radians(angles), att_vals, lw=3, color='royalblue')
    ax_pol.set_theta_zero_location("N")
    ax_pol.set_theta_direction(-1)
    ax_pol.set_thetamin(0)
    ax_pol.set_thetamax(90)
    ax_pol.set_title("Attenuazione Totale [dB]", va='bottom')
    st.pyplot(fig_pol)

# --- TAB 2: SIMULATORE FDTD CON ANGOLO DI INCIDENZA ---
with tab2:
    st.title("Simulazione Numerica con Incidenza Angolare")
    st.write("Modellazione di un fronte d'onda piano inclinato che attraversa l'apertura.")

    col_sim_1, col_sim_2 = st.columns([1, 3])
    
    with col_sim_1:
        angle_inc = st.slider("Angolo di Incidenza Sorgente (°)", 0, 75, 30)
        freq_fdtd = st.slider("Frequenza (Adimensionale)", 0.1, 1.0, 0.4)
        wall_thick = st.slider("Spessore Muro (px)", 2, 12, 6)
        run_sim = st.button("▶️ Esegui Simulazione FDTD")

    if run_sim:
        # Griglia e setup
        nx, ny = 140, 100
        p = np.zeros((nx, ny))
        p_prev = np.zeros((nx, ny))
        mask = np.ones((nx, ny))
        
        # Geometria muro
        wx = 50 # Posizione muro
        gap = 16 # Apertura
        mask[wx : wx + wall_thick, : ny//2 - gap//2] = 0
        mask[wx : wx + wall_thick, ny//2 + gap//2 :] = 0
        
        plot_cont = st.empty()
        theta_rad = np.radians(angle_inc)
        
        for t in range(180):
            # SORGENTE PLANARE INCLINATA
            # Usiamo una linea di sorgenti lungo x=5 con ritardo di fase basato sull'angolo
            for y_idx in range(ny):
                # Il ritardo dipende dalla posizione y per creare l'inclinazione del fronte
                delay = y_idx * np.sin(theta_rad)
                p[5, y_idx] += np.sin(freq_fdtd * (t - delay)) * np.exp(-0.02 * (t - 40 - delay)**2)
            
            # Motore FDTD (Laplaciano)
            p_next = 2*p - p_prev + 0.25 * (
                np.roll(p, 1, 0) + np.roll(p, -1, 0) +
                np.roll(p, 1, 1) + np.roll(p, -1, 1) - 4*p
            )
            
            # Condizioni al contorno (Smorzamento)
            p_next *= mask
            p_next[0,:] = p_next[-1,:] = p_next[:,0] = p_next[:,-1] = 0
            
            p_prev, p = p, p_next
            
            if t % 8 == 0:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.imshow(p.T, cmap='coolwarm', origin='lower', vmin=-0.3, vmax=0.3)
                # Disegno muro in sovrapposizione
                ax.contour(mask.T, colors='black', levels=[0.5], linewidths=2)
                ax.set_title(f"Fronte d'onda con incidenza a {angle_inc}°")
                ax.axis('off')
                plot_cont.pyplot(fig)
                plt.close(fig)

        st.success("Simulazione conclusa. Si osservi come l'onda 'ruota' entrando nella mazzetta.")
