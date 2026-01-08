import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Résultats",
    page_icon="",
    layout="wide"
)

st.title("Résultats du Planning")
st.markdown("---")

# Onglets pour différentes vues
tab1, tab2, tab3 = st.tabs(["Vue Calendrier", "Vue Étudiants", "Vue Fauteuils"])

with tab1:
    st.subheader("Planning Calendrier")
    # Ici : affichage du calendrier (peut utiliser st.dataframe avec style)
    st.info("Calendrier interactif à implémenter")

with tab2:
    st.subheader("Planning par Étudiant")
    etudiant = st.selectbox("Sélectionner un étudiant", ["DUPONT Jean", "MARTIN Marie", "..."])
    st.info(f"Planning de {etudiant}")

st.markdown("---")

# Section Export
st.header("Export")

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="⬇ Télécharger Planning Excel",
        data="",  # Votre DataFrame converti en Excel
        file_name="planning_hospitalier.xlsx",
        mime="application/vnd.ms-excel",
        help="Exporter le planning au format Excel"
    )

with col2:
    st.download_button(
        label="⬇ Télécharger Planning PDF",
        data="",
        file_name="planning_hospitalier.pdf",
        mime="application/pdf",
        help="Exporter le planning au format PDF"
    )
