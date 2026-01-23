import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Gestion du Planning Hospitalier de la Faculté d'Odontologie",
    page_icon="https://media.licdn.com/dms/image/v2/D4D0BAQFQznNSBtSWWg/company-logo_200_200/company-logo_200_200/0/1738144388664/facult_d_odontologie_de_montpellier_logo?e=2147483647&v=beta&t=Uge2R8Hv_hCc8gv79aMsBIYe6lShFbPoMLJKzDF0bXk",
    layout="wide"
)

st.title("Gestion du Planning Hospitalier")
st.subheader("Faculté d'Odontologie de Montpellier")

st.markdown("---")

# Introduction
st.markdown("""
### À propos de l'application

La planification des stages cliniques est un exercice complexe qui nécessite de coordonner 
de nombreux paramètres
            \n1. Disponibilité des étudiants
            \n2. Capacités d'accueil des services
            \n3. Présence des encadrants
            \n4. Respect des quotas de formation par discipline.

Cet outil a été conçu pour simplifier ce processus et garantir une répartition équitable 
des ressources tout en respectant les contraintes pédagogiques et organisationnelles 
de la faculté.
""")

st.markdown("<br>", unsafe_allow_html=True)

# Workflow de l'application
st.markdown("### Comment utiliser l'application ?")

st.markdown("""
Le processus de création du planning se déroule en trois étapes principales, 
accessibles depuis le menu latéral.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    ### Import Données
    Importez vos fichiers Excel :
    - Calendrier universitaire
    """)

with col2:
    st.info("""
    ### Configuration
    Configurez :
    - Les disciplines
    - Les stages
    """)

with col3:
    st.success("""
    ### Résultats
    Consultez et exportez :
    - Planning calendrier
    - Planning par étudiant
    """)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

st.caption("© 2026 - Faculté d'Odontologie de Montpellier")
