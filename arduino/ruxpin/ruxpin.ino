/**
 * Raspi Ruxpin — Arduino Motor Controller
 *
 * Receives serial commands from the Pi to drive eyes and mouth servos.
 * Supports two servo types (H-bridge and standard) and three sync modes
 * (realtime from ADC, amplitude from serial, phoneme from serial).
 *
 * Serial protocol: 115200 baud, newline-terminated ASCII.
 * See CLAUDE.md for full protocol specification.
 */

#include <Servo.h>

// ─── Pin defaults ────────────────────────────────────────────────
#define PIN_UPPER_JAW   9
#define PIN_LOWER_JAW   10
#define PIN_EYES        11
#define PIN_AUDIO       A0

// H-bridge direction pins (only used in HBRIDGE mode)
#define PIN_UPPER_DIR   4
#define PIN_UPPER_CDIR  5
#define PIN_LOWER_DIR   6
#define PIN_LOWER_CDIR  7
#define PIN_EYES_DIR    12
#define PIN_EYES_CDIR   13

// ─── Constants ───────────────────────────────────────────────────
#define SERIAL_BAUD     115200
#define CMD_BUFFER_SIZE 64
#define ADC_SAMPLE_HZ   50
#define ADC_WINDOW_MS    20
#define NUM_POSITIONS    7
#define BLINK_CLOSE_MS   150
#define BLINK_DURATION   400   // total ms for close + pause + open

// ─── Enums ───────────────────────────────────────────────────────
enum SystemState {
  STATE_BOOT,
  STATE_HANDSHAKE,
  STATE_CONFIG,
  STATE_RUNNING
};

enum ServoMode {
  MODE_HBRIDGE,
  MODE_STANDARD
};

enum SyncMode {
  SYNC_AMPLITUDE,  // Pi sends timed mouth commands (pre-analyzed amplitude)
  SYNC_PHONEME,    // Pi sends timed mouth commands (pre-analyzed phonemes)
  SYNC_REALTIME    // Arduino reads ADC, drives servos, reports positions to Pi
};

// Mouth position codes (index matches enum)
// C=0, T=1, S=2, N=3, M=4, L=5, W=6
enum MouthPos {
  POS_C = 0, POS_T, POS_S, POS_N, POS_M, POS_L, POS_W
};

const char* POS_NAMES[] = {"C", "T", "S", "N", "M", "L", "W"};

// ─── Calibration ─────────────────────────────────────────────────
struct CalEntry {
  int upper;
  int lower;
};

// Default calibration (degrees for standard servos, duty% for H-bridge)
CalEntry calibration[NUM_POSITIONS] = {
  {101, 99},  // C - closed
  {97,  95},  // T
  {92,  90},  // S
  {86,  84},  // N
  {78,  76},  // M
  {68,  66},  // L
  {55,  53},  // W - wide open
};

// Amplitude thresholds mapped to 0-1023 ADC range (from normalized 0.0-1.0)
// Original thresholds with 0.7 power compression applied to normalized RMS
// ADC maps 0-5V linearly to 0-1023; audio signal is AC-coupled around 2.5V
// These thresholds are on the RMS of the AC component, scaled to 0.0-1.0
const float AMP_THRESHOLDS[] = {0.17, 0.12, 0.085, 0.055, 0.03, 0.01, 0.0};
const MouthPos AMP_POSITIONS[] = {POS_W, POS_L, POS_M, POS_N, POS_S, POS_T, POS_C};
#define NUM_THRESHOLDS 7

// ─── State ───────────────────────────────────────────────────────
SystemState sysState = STATE_BOOT;
ServoMode servoMode = MODE_HBRIDGE;
SyncMode syncMode = SYNC_AMPLITUDE;
MouthPos currentMouth = POS_C;
bool eyesOpen = true;

// Servo objects (only used in STANDARD mode)
Servo upperServo;
Servo lowerServo;
Servo eyesServo;

// Standard servo positions for eyes
#define EYES_OPEN_ANGLE   90
#define EYES_CLOSED_ANGLE 10

// Blink state
bool blinking = false;
unsigned long blinkStart = 0;

// Command buffer
char cmdBuffer[CMD_BUFFER_SIZE];
int cmdIndex = 0;

// ADC sampling
unsigned long lastSampleTime = 0;
long adcSum = 0;
int adcCount = 0;
int adcBaseline = 512; // Midpoint of 10-bit ADC (2.5V reference)

// ─── Forward declarations ────────────────────────────────────────
void processCommand(const char* cmd);
void setMouthPosition(MouthPos pos);
void setMouthAngles(int upper, int lower);
void openEyes();
void closeEyes();
void startBlink();
void updateBlink();
void processADC();
MouthPos amplitudeToPosition(float normalizedRms);
void driveHBridge(int pwmPin, int dirPin, int cdirPin, int value, bool forward);
void sendStatus();

// ─── Setup ───────────────────────────────────────────────────────
void setup() {
  Serial.begin(SERIAL_BAUD);
  while (!Serial) { ; } // Wait for serial

  // Default pin modes (H-bridge)
  pinMode(PIN_UPPER_JAW, OUTPUT);
  pinMode(PIN_LOWER_JAW, OUTPUT);
  pinMode(PIN_EYES, OUTPUT);
  pinMode(PIN_UPPER_DIR, OUTPUT);
  pinMode(PIN_UPPER_CDIR, OUTPUT);
  pinMode(PIN_LOWER_DIR, OUTPUT);
  pinMode(PIN_LOWER_CDIR, OUTPUT);
  pinMode(PIN_EYES_DIR, OUTPUT);
  pinMode(PIN_EYES_CDIR, OUTPUT);

  // Audio input
  pinMode(PIN_AUDIO, INPUT);

  // Calibrate ADC baseline (average of first 100 readings)
  long sum = 0;
  for (int i = 0; i < 100; i++) {
    sum += analogRead(PIN_AUDIO);
    delay(1);
  }
  adcBaseline = sum / 100;

  // Send READY
  Serial.println("READY");
  sysState = STATE_HANDSHAKE;
}

// ─── Main loop ───────────────────────────────────────────────────
void loop() {
  // Read serial (non-blocking)
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (cmdIndex > 0) {
        cmdBuffer[cmdIndex] = '\0';
        processCommand(cmdBuffer);
        cmdIndex = 0;
      }
    } else if (cmdIndex < CMD_BUFFER_SIZE - 1) {
      cmdBuffer[cmdIndex++] = c;
    }
  }

  // Only process ADC and blink in RUNNING state
  if (sysState == STATE_RUNNING) {
    // ADC amplitude processing (only in REALTIME — Arduino drives servos from audio)
    if (syncMode == SYNC_REALTIME) {
      processADC();
    }

    // Blink animation
    updateBlink();
  }
}

// ─── Command processing ──────────────────────────────────────────
void processCommand(const char* cmd) {
  // Config commands (during handshake/config phase)
  if (strncmp(cmd, "CFG:", 4) == 0) {
    handleConfig(cmd + 4);
    return;
  }

  // Runtime commands (only in RUNNING state, but allow PING always)
  if (strcmp(cmd, "PING") == 0) {
    Serial.println("PONG");
    return;
  }

  if (strcmp(cmd, "STATUS") == 0) {
    sendStatus();
    return;
  }

  if (sysState != STATE_RUNNING) {
    Serial.println("ERR:Not in running state");
    return;
  }

  // Mouth position by code: M<code> (MC, MT, MS, MN, MM, ML, MW)
  if (cmd[0] == 'M' && strlen(cmd) == 2) {
    MouthPos pos = codeToPosition(cmd[1]);
    if (pos != (MouthPos)-1) {
      setMouthPosition(pos);
    } else {
      Serial.println("ERR:Invalid mouth code");
    }
    return;
  }

  // Mouth position by angles: J<upper>,<lower>
  if (cmd[0] == 'J') {
    int upper, lower;
    if (sscanf(cmd + 1, "%d,%d", &upper, &lower) == 2) {
      setMouthAngles(upper, lower);
    } else {
      Serial.println("ERR:Invalid jaw format");
    }
    return;
  }

  // Eyes commands
  if (strcmp(cmd, "EO") == 0) { openEyes(); return; }
  if (strcmp(cmd, "EC") == 0) { closeEyes(); return; }
  if (strcmp(cmd, "EB") == 0) { startBlink(); return; }

  // Audio state hints (informational only — Arduino reads ADC regardless)
  if (strncmp(cmd, "AUDIO:", 6) == 0) {
    return;  // Acknowledged silently
  }

  // Mode switch
  if (strncmp(cmd, "MODE:", 5) == 0) {
    if (strcmp(cmd + 5, "AMPLITUDE") == 0) {
      syncMode = SYNC_AMPLITUDE;
    } else if (strcmp(cmd + 5, "PHONEME") == 0) {
      syncMode = SYNC_PHONEME;
    } else if (strcmp(cmd + 5, "REALTIME") == 0) {
      syncMode = SYNC_REALTIME;
    } else {
      Serial.println("ERR:Invalid mode");
      return;
    }
    Serial.println("OK");
    return;
  }

  Serial.println("ERR:Unknown command");
}

void handleConfig(const char* cfg) {
  if (sysState == STATE_HANDSHAKE) {
    sysState = STATE_CONFIG;
  }

  // SERVO type
  if (strncmp(cfg, "SERVO:", 6) == 0) {
    if (strcmp(cfg + 6, "HBRIDGE") == 0) {
      servoMode = MODE_HBRIDGE;
    } else if (strcmp(cfg + 6, "STANDARD") == 0) {
      servoMode = MODE_STANDARD;
      // Attach standard servos
      upperServo.attach(PIN_UPPER_JAW);
      lowerServo.attach(PIN_LOWER_JAW);
      eyesServo.attach(PIN_EYES);
    }
    return;
  }

  // Calibration: CAL:<code>:<upper>:<lower>
  if (strncmp(cfg, "CAL:", 4) == 0) {
    char code;
    int upper, lower;
    if (sscanf(cfg + 4, "%c:%d:%d", &code, &upper, &lower) == 3) {
      MouthPos pos = codeToPosition(code);
      if (pos != (MouthPos)-1) {
        calibration[pos].upper = upper;
        calibration[pos].lower = lower;
      }
    }
    return;
  }

  // Mode
  if (strncmp(cfg, "MODE:", 5) == 0) {
    if (strcmp(cfg + 5, "AMPLITUDE") == 0) {
      syncMode = SYNC_AMPLITUDE;
    } else if (strcmp(cfg + 5, "PHONEME") == 0) {
      syncMode = SYNC_PHONEME;
    } else if (strcmp(cfg + 5, "REALTIME") == 0) {
      syncMode = SYNC_REALTIME;
    }
    return;
  }

  // Done
  if (strcmp(cfg, "DONE") == 0) {
    sysState = STATE_RUNNING;
    Serial.println("OK");

    // Initialize positions
    setMouthPosition(POS_C);
    openEyes();
    return;
  }
}

MouthPos codeToPosition(char code) {
  switch (code) {
    case 'C': return POS_C;
    case 'T': return POS_T;
    case 'S': return POS_S;
    case 'N': return POS_N;
    case 'M': return POS_M;
    case 'L': return POS_L;
    case 'W': return POS_W;
    default:  return (MouthPos)-1;
  }
}

// ─── Servo control ───────────────────────────────────────────────
void setMouthPosition(MouthPos pos) {
  if (pos == currentMouth) return;
  currentMouth = pos;

  int upper = calibration[pos].upper;
  int lower = calibration[pos].lower;
  setMouthAngles(upper, lower);
}

void setMouthAngles(int upper, int lower) {
  if (servoMode == MODE_STANDARD) {
    upperServo.write(constrain(upper, 0, 180));
    lowerServo.write(constrain(lower, 0, 180));
  } else {
    // H-bridge: use calibration values as PWM duty cycle
    // Direction based on opening vs closing relative to current position
    bool opening = (upper < calibration[currentMouth].upper);
    driveHBridge(PIN_UPPER_JAW, PIN_UPPER_DIR, PIN_UPPER_CDIR, abs(upper), opening);
    driveHBridge(PIN_LOWER_JAW, PIN_LOWER_DIR, PIN_LOWER_CDIR, abs(lower), !opening);
  }
}

void openEyes() {
  eyesOpen = true;
  if (servoMode == MODE_STANDARD) {
    eyesServo.write(EYES_OPEN_ANGLE);
  } else {
    driveHBridge(PIN_EYES, PIN_EYES_DIR, PIN_EYES_CDIR, 100, true);
    delay(BLINK_DURATION / 2);
    analogWrite(PIN_EYES, 0); // Stop
  }
}

void closeEyes() {
  eyesOpen = false;
  if (servoMode == MODE_STANDARD) {
    eyesServo.write(EYES_CLOSED_ANGLE);
  } else {
    driveHBridge(PIN_EYES, PIN_EYES_DIR, PIN_EYES_CDIR, 100, false);
    delay(BLINK_DURATION / 2);
    analogWrite(PIN_EYES, 0); // Stop
  }
}

void startBlink() {
  if (blinking) return;
  blinking = true;
  blinkStart = millis();
  closeEyes();
}

void updateBlink() {
  if (!blinking) return;

  unsigned long elapsed = millis() - blinkStart;
  if (elapsed >= BLINK_CLOSE_MS + 50) {
    // Reopen
    openEyes();
    blinking = false;
  }
}

void driveHBridge(int pwmPin, int dirPin, int cdirPin, int value, bool forward) {
  if (forward) {
    digitalWrite(dirPin, HIGH);
    digitalWrite(cdirPin, LOW);
  } else {
    digitalWrite(dirPin, LOW);
    digitalWrite(cdirPin, HIGH);
  }
  analogWrite(pwmPin, constrain(value, 0, 255));
}

// ─── ADC amplitude processing ────────────────────────────────────
void processADC() {
  unsigned long now = millis();

  // Accumulate samples
  int raw = analogRead(PIN_AUDIO);
  int centered = raw - adcBaseline; // Remove DC offset
  adcSum += (long)centered * centered;
  adcCount++;

  // Process window every ADC_WINDOW_MS
  if (now - lastSampleTime >= ADC_WINDOW_MS) {
    lastSampleTime = now;

    if (adcCount > 0) {
      // Compute RMS, normalize to 0.0-1.0
      float rms = sqrt((float)adcSum / adcCount);
      float normalized = rms / 512.0; // 512 = half of 10-bit range
      if (normalized > 1.0) normalized = 1.0;

      // Apply power compression
      float compressed = (normalized > 0) ? pow(normalized, 0.7) : 0.0;

      // Map to mouth position
      MouthPos newPos = amplitudeToPosition(compressed);
      if (newPos != currentMouth) {
        setMouthPosition(newPos);
        // Report position change to Pi for frontend visualization
        Serial.print("MOUTH:");
        Serial.println(POS_NAMES[currentMouth]);
      }
    }

    adcSum = 0;
    adcCount = 0;
  }
}

MouthPos amplitudeToPosition(float normalizedRms) {
  for (int i = 0; i < NUM_THRESHOLDS; i++) {
    if (normalizedRms >= AMP_THRESHOLDS[i]) {
      return AMP_POSITIONS[i];
    }
  }
  return POS_C;
}

// ─── Status reporting ────────────────────────────────────────────
void sendStatus() {
  Serial.print("STATUS:MODE:");
  const char* modeName = "AMPLITUDE";
  if (syncMode == SYNC_PHONEME) modeName = "PHONEME";
  else if (syncMode == SYNC_REALTIME) modeName = "REALTIME";
  Serial.print(modeName);
  Serial.print(",MOUTH:");
  Serial.print(POS_NAMES[currentMouth]);
  Serial.print(",EYES:");
  Serial.println(eyesOpen ? "open" : "closed");
}
