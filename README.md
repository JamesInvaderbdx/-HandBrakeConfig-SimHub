# HandBrake Config — SimHub Plugin

Plugin SimHub pour frein à main DIY. Supporte joystick HID et Arduino Nano (serial).

## Fonctionnalités
- Mode HID joystick ou Arduino Nano (port série)
- Calibration automatique
- Inversion d'axe
- Zone morte réglable
- Courbe de réponse (linéaire / expo / S-curve)
- Sortie vJoy intégrée (Device 2 / Axe Y)
- Propriétés SimHub : `HandBrake.Output` [0–1] et `HandBrake.OutputPercent` [0–100]

## Installation
1. Copier `HandBrakeConfig.dll` dans `C:\Program Files (x86)\SimHub\`
2. Relancer SimHub

## Câblage Arduino (KY-023)
| Joystick | Nano |
|----------|------|
| GND | GND |
| +5V | 5V |
| VRx | A1 |
| VRy | A2 |
| SW | D2 |

## Prérequis
- [SimHub](https://www.simhubdash.com/)
- [vJoy](https://github.com/jshafer817/vJoy) (optionnel)
- Arduino Nano + KY-023 (mode serial uniquement)

## Crédits
Développé par [eKLID](https://eklid.fr) — pixel art production
