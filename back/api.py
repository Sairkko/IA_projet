from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
import uvicorn
import numpy as np
import pandas as pd

# Initialisation de FastAPI
app = FastAPI()

# Définition des modèles de données d'entrée
class PredictionNoteData(BaseModel):
    ville: str
    surface: float
    price: float

class PredictionYearData(BaseModel):
    ville: str

class PredictionGarageData(BaseModel):
    ville: str
    price: float

# Initialisation des modèles de machine learning
model_note = LinearRegression()
model_year = LinearRegression()
model_garage = LogisticRegression(max_iter=200)

# Utilisation cohérente de l'encodeur
label_encoder = LabelEncoder()

# Variable pour vérifier si les modèles sont entraînés
is_model_trained = False

# Endpoint pour entraîner les modèles
@app.post("/train")
async def train():
    global is_model_trained
    global model_note, model_year, model_garage
    global label_encoder

    # Lire le fichier CSV
    df = pd.read_csv('suites.csv')

    # Encoder la colonne 'ville'
    df['ville_encoded'] = label_encoder.fit_transform(df['ville'])

    # 1. Régression linéaire pour prédire la note
    X_note = df[['ville_encoded', 'surface', 'price']]
    y_note = df['note']
    model_note.fit(X_note, y_note)

    # 2. Régression linéaire pour prédire l'année de construction
    X_year = df[['ville_encoded']]
    y_year = df['annee']
    model_year.fit(X_year, y_year)

    # 3. Classification logistique pour prédire la présence d'un garage
    X_garage = df[['ville_encoded', 'price']]
    y_garage = df['garage']
    model_garage.fit(X_garage, y_garage)

    # Marquer les modèles comme entraînés
    is_model_trained = True

    return {"message": "Modèles entraînés avec succès."}

# Endpoint pour prédire la note en fonction de la ville, surface et prix
@app.post("/predict-note")
async def predict_note(data: PredictionNoteData):
    if not is_model_trained:
        raise HTTPException(status_code=400, detail="Le modèle n'est pas encore entraîné.")

    # Encoder la ville
    ville_encoded = label_encoder.transform([data.ville])[0]
    X_new = np.array([[ville_encoded, data.surface, data.price]])

    predicted_note = model_note.predict(X_new)[0]
    return {"predicted_note": predicted_note}

# Endpoint pour prédire l'année en fonction de la ville et calculer R² et RMSE
@app.post("/predict-year")
async def predict_year(data: PredictionYearData):
    if not is_model_trained:
        raise HTTPException(status_code=400, detail="Le modèle n'est pas encore entraîné.")

    # Encoder la ville pour la nouvelle donnée
    ville_encoded = label_encoder.transform([data.ville])[0]
    X_new = np.array([[ville_encoded]])

    predicted_year = model_year.predict(X_new)[0]

    # Lire le fichier CSV
    df = pd.read_csv('suites.csv')

    # Encoder la colonne 'ville' pour toutes les données
    df['ville_encoded'] = label_encoder.transform(df['ville'])

    # Calcul de R² et RMSE
    X_year_all = df[['ville_encoded']]  # Assurez-vous que c'est un DataFrame à deux dimensions
    y_year_all = df['annee']
    y_pred_all = model_year.predict(X_year_all)
    r2 = model_year.score(X_year_all, y_year_all)
    rmse = np.sqrt(mean_squared_error(y_year_all, y_pred_all))

    return {"predicted_year": predicted_year, "R²": r2, "RMSE": rmse}

# Endpoint pour prédire la présence d'un garage en fonction du prix et de la ville
@app.post("/predict-garage")
async def predict_garage(data: PredictionGarageData):
    if not is_model_trained:
        raise HTTPException(status_code=400, detail="Le modèle n'est pas encore entraîné.")

    # Encoder la ville
    ville_encoded = label_encoder.transform([data.ville])[0]
    X_new = np.array([[ville_encoded, data.price]])

    predicted_garage = model_garage.predict(X_new)[0]
    return {"predicted_garage": bool(predicted_garage)}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=5000)
