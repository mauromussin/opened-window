import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Modello Analitico", layout="wide")
st.title("🎯 Analisi Fisica dell'Attenuazione")

if st.button("⬅️ Torna alla Home"):
    st.switch_page("app.py")

# Equalizzatore Sorgente
st.subheader("Sorgente Sonora (Lw)")
freqs = np.array([100, 125, 250, 500, 1000, 2000, 4000, 5000])
wA = np.array([-19.1, -16.1, -8.6, -3.2, 0, 1.2, 1.0, 0.5])
cols = st.columns(len(freqs))
lw_inputs = [cols[i].slider(f"{freqs[i]}Hz", 60, 110, 90) for i in range(len(freqs))]

# Parametri Sidebar
s = st.sidebar.slider("Spessore Mazzetta [m]", 0.0, 0.6, 0.2)
w = st.sidebar.slider("Larghezza Finestra [m]", 0.5, 2.0, 1.0)
d_mic = st.sidebar.slider("Distanza Interna [m]", 0.5, 5.0, 2.0)

def calculate(theta_deg):
    theta = np.radians(theta_deg)
    k = 2 * np.pi * freqs / 343
    # Diffrazione
    delta = s * (1 - np.cos(theta))
    N = 2 * delta * freqs / 343
    att_diff = np.where(N > 0, 10 * np.log10(3 + 20*N), 0)
    # Direttività
    psi = (k * w / 2) * np.sin(theta)
    dir_f = (np.sinc(psi / np.pi))**2
    # Risultato dBA
    lp_int = 10 * np.log10(dir_f * np.cos(theta) / (2*np.pi*d_mic**2) + 1e-12) - att_diff
    return -lp_int.mean()

angles = np.linspace(0, 89, 90)
res = [calculate(a) for a in angles]

fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
ax.plot(np.radians(angles), res, lw=3)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_thetamin(0)
ax.set_thetamax(90)
st.pyplot(fig)
