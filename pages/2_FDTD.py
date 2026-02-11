import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulatore FDTD", layout="wide")
st.title("🌊 Simulazione Numerica FDTD")

if st.button("⬅️ Torna alla Home"):
    st.switch_page("app.py")

angle_inc = st.slider("Angolo di Incidenza Sorgente (°)", 0, 75, 30)
thick = st.slider("Spessore Muro (pixel)", 2, 15, 6)
run = st.button("▶️ Avvia Simulazione")

if run:
    nx, ny = 120, 80
    p, p_prev = np.zeros((nx, ny)), np.zeros((nx, ny))
    mask = np.ones((nx, ny))
    wx, gap = 45, 16
    mask[wx : wx + thick, : ny//2 - gap//2] = 0
    mask[wx : wx + thick, ny//2 + gap//2 :] = 0
    
    theta = np.radians(angle_inc)
    placeholder = st.empty()
    
    for t in range(150):
        # Sorgente Planare Inclinata
        for y in range(ny):
            delay = y * np.sin(theta)
            p[5, y] += np.sin(0.4 * (t - delay)) * np.exp(-0.01 * (t - 30 - delay)**2)
        
        # Motore FDTD
        p_next = 2*p - p_prev + 0.25 * (np.roll(p,1,0)+np.roll(p,-1,0)+np.roll(p,1,1)+np.roll(p,-1,1)-4*p)
        p_next *= mask
        p_next[0,:] = p_next[-1,:] = p_next[:,0] = p_next[:,-1] = 0
        p_prev, p = p, p_next
        
        if t % 6 == 0:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.imshow(p.T, cmap='RdBu', origin='lower', vmin=-0.4, vmax=0.4)
            ax.contour(mask.T, colors='black', levels=[0.5])
            ax.axis('off')
            placeholder.pyplot(fig)
            plt.close(fig)
