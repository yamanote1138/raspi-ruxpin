# TODO

## Untested

- [ ] **Hardware testing** — Arduino firmware (`arduino/ruxpin/ruxpin.ino`) has not been uploaded or tested on actual hardware. Serial handshake, config, mode switching, ADC amplitude processing, and servo control all need verification with real Arduino + servos.
- [ ] **CLI testing** — `uv run raspi-ruxpin-cli` has not been manually exercised. Menu navigation, TTS generation, sound playback, settings changes, and title management need a walkthrough.
- [ ] **Raspberry Pi deployment** — Full end-to-end test on Pi: serial connection to Arduino, ALSA audio, volume control, phoneme analysis (if deps installed).
- [ ] **Realtime mode end-to-end** — Arduino ADC reading audio signal, driving servos, reporting `MOUTH:<code>` back over serial, frontend visualization updating.

## Docs Needing Rewrite

- [ ] `README.md` — Still describes old GPIO architecture in project structure and hardware sections
- [ ] `docs/DEPLOYMENT.md` — Entire wiring diagram and env vars are for old GPIO system
- [ ] `docs/TROUBLESHOOTING.md` — GPIO Issues and Servo Issues sections are obsolete
- [ ] `docs/QUICKSTART.md` — References old "Puppet Mode"/"Speak Mode" UI, wrong port, wrong formatter
