import pandas as pd
from pathlib import Path
from audio import AudioFeature
from model import Model
from sklearn.ensemble import RandomForestClassifier
import os
import pickle
import numpy as np


def parse_metadata(path):
    meta_df = pd.read_csv(path)
    meta_df = meta_df[["slice_file_name", "fold", "class"]]
    meta = zip(meta_df["slice_file_name"], meta_df["fold"], meta_df["class"])

    return meta


def slice_holdout_idx(fold_arr):
    random_idx = []
    for i in range(1, 11):
        random_idx.extend(
            np.random.choice(np.where(fold_arr == i)[0], 45, replace=False).tolist()  
        )
    return np.array(random_idx)

if __name__ == "__main__":

    metadata = parse_metadata("metadata/UrbanSound8K.csv")

    audio_features = []
    for row in metadata:

        path, fold, label = row

        fn = path.replace(".wav", "")
        transformed_path = f"{Path.home()}/projects/urban_sound_classification/data/fold{fold}/{fn}.pkl"

        if os.path.isfile(transformed_path):
            # if the file exists as a .pkl already, then load it
            with open(transformed_path, "rb") as f:
                audio = pickle.load(f)
                audio_features.append(audio)
        else:
            # if the file doesn't exist, then extract its features from the source data and save the result
            src_path = f"{Path.home()}/datasets/UrbanSound8K/audio/fold{fold}/{path}"
            audio = AudioFeature(src_path, fold, label)
            audio.extract_features("mfcc", "spectral", "chroma")
            audio_features.append(audio)

    feature_matrix = np.vstack([audio.features for audio in audio_features])
    labels = np.array([audio.label for audio in audio_features])
    folds = np.array([audio.fold for audio in audio_features])

    holdout_idx = slice_holdout_idx(folds)
    
    features_test = feature_matrix[holdout_idx, :]
    labels_test = labels[holdout_idx]

    features_train = np.delete(feature_matrix, holdout_idx, axis=0)
    labels_train = np.delete(labels, holdout_idx, axis=0)
    folds_train = np.delete(folds, holdout_idx, axis=0)

    model_cfg = dict(
        model=RandomForestClassifier(
            random_state=42,
            n_jobs=10,
            class_weight="balanced",
            n_estimators=500,
            bootstrap=True,
        ),
    )
    model = Model(features_train, labels_train, folds_train, model_cfg)
    fold_acc = model.train_kfold()

    # TODO - show box plot or std and mean like they were saying