# HandBrake Config v1.0.0 — Initial Release

Plugin SimHub pour frein à main USB DIY.

## Fonctionnalités
- Entrée HID (joystick USB) ou Serial (Arduino/CH340)
- Calibration automatique et manuelle
- Zone morte haute et basse réglable
- Courbes de réponse : Linéaire, Expo, S-Curve
- Inversion d'axe
- Sortie vJoy intégrée (Device 2, Axe Y par défaut)
- UI temps réel avec barres de progression

## Installation
1. Fermer SimHub
2. Copier `HandBrakeConfig.dll` dans `C:\Program Files (x86)\SimHub\`
3. Relancer SimHub → Additional Plugins → activer HandBrake Config

## Prérequis
- SimHub 9.x+
- vJoy 2.1.9+ (optionnel, pour sortie virtuelle)
- Driver CH340 (si Arduino clone)

## Câblage Arduino (KY-023)
| KY-023 | Arduino Nano |
|--------|-------------|
| GND    | GND         |
| +5V    | 5V          |
| VRx    | A1          |
| VRy    | A2          |
| SW     | D2          |
