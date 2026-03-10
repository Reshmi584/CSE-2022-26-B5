import time
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

# ==============================
# 1. CONNECT TO GOOGLE SHEETS
# ==============================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "caramel-aria-486414-d3-3ef5b64aabaf.json", scope
)

client = gspread.authorize(creds)
SPREADSHEET_ID = "1L_v7n8TSMOwjCN-UTkwDJy7pglPcAIfeLlzbZ6twBlE"

# ==============================
# 2. READ TRAINING DATA
# ==============================
train_sheet = client.open_by_key(SPREADSHEET_ID).worksheet("TrainingData")
train_df = pd.DataFrame(train_sheet.get_all_records())

train_df = train_df.dropna(subset=[
    "Avg_RR(ms)", "Avg_HR(bpm)", "Avg_SpO2(%)",
    "RR_Status", "HR_Status", "SpO2_Status", "Final"
])

# ==============================
# 3. ENCODE LABELS
# ==============================
rr_encoder = LabelEncoder()
hr_encoder = LabelEncoder()
spo2_encoder = LabelEncoder()
final_encoder = LabelEncoder()

X_train = train_df[["Avg_RR(ms)", "Avg_HR(bpm)", "Avg_SpO2(%)"]]

y_rr = rr_encoder.fit_transform(train_df["RR_Status"])
y_hr = hr_encoder.fit_transform(train_df["HR_Status"])
y_spo2 = spo2_encoder.fit_transform(train_df["SpO2_Status"])
y_final = final_encoder.fit_transform(train_df["Final"])

# ==============================
# 4. TRAIN RANDOM FOREST MODELS
# ==============================
rr_model = RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42)
hr_model = RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42)
spo2_model = RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42)
final_model = RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42)

rr_model.fit(X_train, y_rr)
hr_model.fit(X_train, y_hr)
spo2_model.fit(X_train, y_spo2)
final_model.fit(X_train, y_final)

# ==============================
# 4.1 TRAINING ACCURACY
# ==============================
rr_acc = accuracy_score(y_rr, rr_model.predict(X_train))
hr_acc = accuracy_score(y_hr, hr_model.predict(X_train))
spo2_acc = accuracy_score(y_spo2, spo2_model.predict(X_train))
final_acc = accuracy_score(y_final, final_model.predict(X_train))

#print("📊 Training Accuracy:")
#print(f"   RR Status   : {rr_acc * 100:.2f}%")
#print(f"   HR Status   : {hr_acc * 100:.2f}%")
#print(f"   SpO2 Status : {spo2_acc * 100:.2f}%")
#print(f"   Final Class : {final_acc * 100:.2f}%")

#print(f"\n🏁 Overall Model Accuracy: {final_acc * 100:.2f}%")
print("🚀 ML Service Started. Waiting for sensor data...\n")

# ==============================
# 5. REAL-TIME LOOP
# ==============================
while True:
    try:
        output_sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Output")
        output_df = pd.DataFrame(output_sheet.get_all_records())

        output_df["Final"] = (
            output_df["Final"]
            .fillna("")
            .astype(str)
            .str.strip()
            .replace("nan", "")
        )

        pending_rows = output_df[output_df["Final"] == ""]

        if pending_rows.empty:
            print("⏳ No new data. Checking again in 60s...")
            time.sleep(60)
            continue

        row_idx = pending_rows.index[0]
        latest = pending_rows.loc[[row_idx],
                          ["Avg_RR(ms)", "Avg_HR(bpm)", "Avg_SpO2(%)"]]

        # Convert empty strings to NaN
        latest = latest.replace('', pd.NA)

        # Convert to numeric safely
        latest = latest.apply(pd.to_numeric, errors='coerce')

        # Check if any value missing
        if latest.isna().any().any():
            print("⚠️ Sensor row incomplete or invalid. Waiting...")
            time.sleep(30)
            continue

        # 🔥 Predict all statuses
        rr_pred = rr_encoder.inverse_transform(rr_model.predict(latest))[0]
        hr_pred = hr_encoder.inverse_transform(hr_model.predict(latest))[0]
        spo2_pred = spo2_encoder.inverse_transform(spo2_model.predict(latest))[0]
        final_pred = final_encoder.inverse_transform(final_model.predict(latest))[0]

        headers = output_sheet.row_values(1)
        sheet_row_number = row_idx + 2

        output_sheet.update_cell(sheet_row_number, headers.index("RR_Status") + 1, rr_pred)
        output_sheet.update_cell(sheet_row_number, headers.index("HR_Status") + 1, hr_pred)
        output_sheet.update_cell(sheet_row_number, headers.index("SpO2_Status") + 1, spo2_pred)
        output_sheet.update_cell(sheet_row_number, headers.index("Final") + 1, final_pred)

        print(f"✅ Row {sheet_row_number} classified → {final_pred}")

        time.sleep(60)

    except KeyboardInterrupt:
        print("\n🛑 ML Service stopped by user.")
        break

    except Exception as e:
        print("❌ Error:", e)
        time.sleep(60)
