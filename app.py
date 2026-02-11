import streamlit as st

st.set_page_config(page_title="Acoustic Research Lab", layout="centered")

st.title("🔬 Laboratorio di Acustica: Studio della Facciata")
st.markdown("""
Benvenuto nel simulatore acustico. Scegli l'approccio di calcolo che desideri utilizzare per studiare 
l'attenuazione sonora attraverso l'apertura in facciata.
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🎯 Approccio Analitico")
    st.write("Calcolo rapido basato su potenziale fisico, direttività (Sinc) e teoria di Maekawa.")
    if st.button("Vai alla parte Analitica"):
        st.switch_page("pages/1_Analitica.py")

with col2:
    st.subheader("🌊 Approccio Numerico")
    st.write("Simulazione FDTD (Differenze Finite) nel dominio del tempo per visualizzare la propagazione.")
    if st.button("Vai alla parte FDTD"):
        st.switch_page("pages/2_FDTD.py")
