import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import io

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Wave Physics GIF Creator", layout="wide")

tab1, tab2 = st.tabs(["🎯 Analisi Analitica", "🎥 Simulatore & GIF FDTD"])

with tab2:
    st.title("Generatore di Propagazione Dinamica")
    st.write("Configura l'angolo e avvia la simulazione per generare l'animazione del fronte d'onda.")

    col_sim_1, col_sim_2 = st.columns([1, 3])
    
    with col_sim_1:
        angle_inc = st.slider("Angolo di Incidenza (°)", 0, 75, 30)
        thick_px = st.slider("Spessore Muro (px)", 2, 15, 8)
        gap_px = st.slider("Luce Finestra (px)", 10, 30, 18)
        f_val = st.slider("Frequenza Sorgente", 0.2, 0.8, 0.4)
        run_sim = st.button("🚀 Genera Animazione")

    if run_sim:
        # Griglia e Parametri (Ottimizzati per velocità)
        nx, ny = 120, 80
        p = np.zeros((nx, ny))
        p_prev = np.zeros((nx, ny))
        mask = np.ones((nx, ny))
        
        # Geometria del muro (Mazzetta)
        wx = 45 # posizione x del muro
        mask[wx : wx + thick_px, : ny//2 - gap_px//2] = 0
        mask[wx : wx + thick_px, ny//2 + gap_px//2 :] = 0
        
        theta_rad = np.radians(angle_inc)
        frames = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        plot_placeholder = st.empty()

        # Simulazione
        steps = 160
        for t in range(steps):
            # Sorgente Planare Inclinata (Phased)
            for y_idx in range(ny):
                delay = y_idx * np.sin(theta_rad)
                # Impulso sinusoidale modulato da gaussiana per pulizia visiva
                p[5, y_idx] += np.sin(f_val * (t - delay)) * np.exp(-0.01 * (t - 30 - delay)**2)
            
            # Motore FDTD (Kernel Differenze Finite)
            p_next = 2*p - p_prev + 0.25 * (
                np.roll(p, 1, 0) + np.roll(p, -1, 0) +
                np.roll(p, 1, 1) + np.roll(p, -1, 1) - 4*p
            )
            
            p_next *= mask # Parete Rigida
            # Assorbimento bordi semplice
            p_next[0,:] = p_next[-1,:] = p_next[:,0] = p_next[:,-1] = 0
            
            p_prev, p = p, p_next
            
            # Rendering dei frame per la "GIF"
            if t % 4 == 0:
                fig, ax = plt.subplots(figsize=(8, 5))
                # Colormap 'RdBu' evidenzia bene le zone di pressione e rarefazione
                im = ax.imshow(p.T, cmap='RdBu', origin='lower', vmin=-0.4, vmax=0.4, interpolation='bilinear')
                ax.contour(mask.T, colors='black', levels=[0.5], linewidths=3)
                ax.set_title(f"T = {t} | Incidenza: {angle_inc}°")
                ax.axis('off')
                
                # Visualizzazione live
                plot_placeholder.pyplot(fig)
                plt.close(fig)
            
            progress_bar.progress(t / steps)
            status_text.text(f"Calcolo frame {t}/{steps}...")

        st.success("Simulazione completata! L'onda è passata attraverso la mazzetta.")
        st.info("💡 **Analisi Fisica:** Nota come lo spigolo della mazzetta 'spezzi' il fronte d'onda, creando una sorgente cilindrica secondaria all'interno della stanza (Principio di Huygens).")
