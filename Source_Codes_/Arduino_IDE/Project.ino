#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include "MAX30100_PulseOximeter.h"

PulseOximeter pox;

/* ----------- PINS ----------- */
#define ECG_PIN   34
#define LO_PLUS   32
#define LO_MINUS  33

/* ----------- WIFI ----------- */
const char* ssid = "Galaxy M35 5G 72FE";
const char* password = "7337285435";

/* ----------- GOOGLE SCRIPT ----------- */
String GOOGLE_SCRIPT_URL =
"https://script.google.com/macros/s/AKfycbxMvwKSLsMWm46gUkmWWQUU-zl0O8zt8P1bKyhnv_wRMIMYg3_Kbj0EHCkP4wchp8gGZw/exec";

/* ----------- ECG FILTER ----------- */
const int MA_WINDOW = 6;
int buffer[MA_WINDOW] = {0};
int idx = 0;
long sum = 0;

float baseline = 0;
float alpha = 0.995;

/* ----------- RR LOGIC ----------- */
unsigned long lastPeakTime = 0;
bool peakDetected = false;
float threshold = 120;

unsigned long rrSum = 0;
int rrCount = 0;

/* ----------- TIMING ----------- */
unsigned long ecgStartTime;
const unsigned long RR_MEASURE_TIME = 90000; // 1.5 minutes
bool rrDone = false;

/* ----------- MAX30100 ----------- */
#define MEASURE_TIME 20000 // 20 seconds
unsigned long poxStartTime = 0;
bool poxMeasuring = false;
bool poxDone = false;

float hrSum = 0;
float spo2Sum = 0;
int poxCount = 0;

/* ----------- UPLOAD ----------- */
bool uploaded = false;

void setup() {
  Serial.begin(9600);   // ✅ SAME AS WORKING ECG CODE
  delay(1000);

  pinMode(LO_PLUS, INPUT);
  pinMode(LO_MINUS, INPUT);

  Wire.begin(21, 22);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  if (!pox.begin()) {
    while (1);
  }

  pox.setIRLedCurrent(MAX30100_LED_CURR_7_6MA);

  ecgStartTime = millis();
}

void loop() {

  /* ================= ECG SECTION (IDENTICAL BEHAVIOR) ================= */

  if (digitalRead(LO_PLUS) || digitalRead(LO_MINUS)) {
    Serial.println(0);
  } else {

    int raw = analogRead(ECG_PIN);

    sum -= buffer[idx];
    buffer[idx] = raw;
    sum += raw;
    idx = (idx + 1) % MA_WINDOW;
    float smooth = sum / (float)MA_WINDOW;

    baseline = alpha * baseline + (1 - alpha) * smooth;
    float ecg = smooth - baseline;

    // ✅ CLEAN ECG OUTPUT (NO TEXT)
    Serial.println(ecg);

    if (!rrDone) {
      if (ecg > threshold && !peakDetected) {
        peakDetected = true;
        unsigned long now = millis();

        if (lastPeakTime > 0) {
          unsigned long rr = now - lastPeakTime;
          if (rr >= 550 && rr <= 1200) {
            rrSum += rr;
            rrCount++;
          }
        }
        lastPeakTime = now;
      }

      if (ecg < threshold) peakDetected = false;

      if (millis() - ecgStartTime > RR_MEASURE_TIME) {
        rrDone = true;
      }
    }
  }

  /* ================= MAX30100 SECTION ================= */

  if (!poxDone) {
    pox.update();

    float hr = pox.getHeartRate();
    float spo2 = pox.getSpO2();

    bool valid = (hr >= 55 && hr <= 140 && spo2 >= 90 && spo2 <= 100);

    if (!poxMeasuring && valid) {
      poxMeasuring = true;
      poxStartTime = millis();
      hrSum = 0;
      spo2Sum = 0;
      poxCount = 0;
    }

    if (poxMeasuring && valid) {
      hrSum += hr;
      spo2Sum += spo2;
      poxCount++;
    }

    if (poxMeasuring && millis() - poxStartTime >= MEASURE_TIME) {
      poxDone = true;
    }
  }

  /* ================= FINAL UPLOAD ================= */

  if (rrDone && poxDone && !uploaded) {
    if (rrCount > 0 && poxCount > 0) {

      unsigned long avgRR = rrSum / rrCount;
      float avgHR = hrSum / poxCount;
      float avgSpO2 = spo2Sum / poxCount;

      sendToGoogle(avgRR, avgHR, avgSpO2);
      uploaded = true;
    }
  }

  delay(10); // ✅ SAME SAMPLING RATE (~125 Hz)
}

/* ================= SEND TO GOOGLE ================= */

void sendToGoogle(unsigned long rr, float hr, float spo2) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = GOOGLE_SCRIPT_URL +
                 "?rr=" + String(rr) +
                 "&hr=" + String(hr, 1) +
                 "&spo2=" + String(spo2, 1);
    http.begin(url);
    http.GET();
    http.end();
  }
}
