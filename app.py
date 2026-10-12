import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Maintenance prédictive - moteurs", layout="wide")

SEUIL_ROUGE = 50    # alerte : intervention à programmer (seuil choisi dans le notebook)
SEUIL_ORANGE = 80   # pré-alerte : à surveiller (seuil indicatif)


@st.cache_data
def charger():
    return pd.read_csv("predictions_test.csv")


def etat(rul):
    if rul < SEUIL_ROUGE:
        return "Rouge"
    if rul < SEUIL_ORANGE:
        return "Orange"
    return "Vert"


df = charger().sort_values(["moteur", "cycle"])
dernier = df.groupby("moteur").tail(1).copy()
dernier["Etat"] = dernier["RUL_predite"].apply(etat)

# ---------- Titre ----------
st.title("Maintenance prédictive de moteurs d'avion")
st.caption("Données simulées NASA C-MAPSS (FD001) - prédiction de la durée de vie restante (RUL) "
           "par Gradient Boosting. Rejeu sur les 100 moteurs de test.")

# ---------- Indicateurs ----------
nb_total = len(dernier)
nb_rouge = int((dernier["Etat"] == "Rouge").sum())
nb_orange = int((dernier["Etat"] == "Orange").sum())
nb_vert = int((dernier["Etat"] == "Vert").sum())
rmse = float(np.sqrt(((dernier["RUL_predite"] - dernier["RUL_reelle"]) ** 2).mean()))

critiques = dernier["RUL_reelle"] < SEUIL_ROUGE
detectes = int(((dernier["Etat"] == "Rouge") & critiques).sum())
nb_critiques = int(critiques.sum())

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Moteurs suivis", nb_total)
c2.metric("Alerte (rouge)", nb_rouge)
c3.metric("Pré-alerte (orange)", nb_orange)
c4.metric("Sains (vert)", nb_vert)
c5.metric("Erreur moyenne (RMSE)", f"{rmse:.1f} cycles")
st.write(f"Moteurs réellement à moins de {SEUIL_ROUGE} cycles de la panne : "
         f"**{detectes} détectés sur {nb_critiques}**.")

st.divider()

# ---------- Détail d'un moteur ----------
gauche, droite = st.columns([1, 2])

with gauche:
    st.subheader("Détail d'un moteur")
    moteur = st.selectbox("Choisir un moteur", sorted(dernier["moteur"].tolist()))
    ligne = dernier[dernier["moteur"] == moteur].iloc[0]
    rul = float(ligne["RUL_predite"])
    message = f"RUL prédite : {rul:.0f} cycles"
    if ligne["Etat"] == "Rouge":
        st.error(f"ALERTE - {message}. Programmer une intervention.")
    elif ligne["Etat"] == "Orange":
        st.warning(f"PRÉ-ALERTE - {message}. À surveiller.")
    else:
        st.success(f"SAIN - {message}.")
    st.write(f"Dernier cycle observé : {int(ligne['cycle'])}")
    st.write(f"RUL réelle (donnée NASA, plafonnée à 125) : {ligne['RUL_reelle']:.0f} cycles")

with droite:
    d = df[df["moteur"] == moteur]
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(d["cycle"], d["RUL_reelle"], label="RUL réelle", linewidth=2)
    ax.plot(d["cycle"], d["RUL_predite"], label="RUL prédite", alpha=0.8)
    ax.axhline(SEUIL_ROUGE, color="red", linestyle="--", linewidth=1, label=f"seuil d'alerte ({SEUIL_ROUGE})")
    ax.axhline(SEUIL_ORANGE, color="orange", linestyle="--", linewidth=1, label=f"pré-alerte ({SEUIL_ORANGE})")
    ax.set_xlabel("Cycle")
    ax.set_ylabel("RUL (cycles)")
    ax.set_title(f"Moteur {moteur}")
    ax.legend(fontsize=8)
    st.pyplot(fig)

st.divider()

# ---------- Tableau des moteurs ----------
st.subheader("Tous les moteurs, du plus urgent au moins urgent")
tableau = dernier[["moteur", "cycle", "RUL_predite", "RUL_reelle", "Etat"]].copy()
tableau.columns = ["Moteur", "Dernier cycle", "RUL prédite", "RUL réelle", "État"]
tableau["RUL prédite"] = tableau["RUL prédite"].round(0)
tableau = tableau.sort_values("RUL prédite")

couleurs = {"Rouge": "#f8c9c9", "Orange": "#fde2b8", "Vert": "#cdeccd"}
st.dataframe(
    tableau.style.apply(lambda ligne: [f"background-color: {couleurs[ligne['État']]}"] * len(ligne), axis=1),
    hide_index=True,
)

st.caption("Limites : seuils choisis sur ces mêmes 100 moteurs de test (performance légèrement optimiste) ; "
           "données simulées ; RUL plafonnée à 125 cycles ; le seuil orange est indicatif.")