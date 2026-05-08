<div align="center">

# HandBrake Config — SimHub Plugin

**Calibration complète pour frein à main DIY ou générique**  
HID joystick · Arduino Nano · vJoy · Courbe de réponse · Lissage

[![Download](https://img.shields.io/github/v/release/JamesInvaderbdx/-HandBrakeConfig-SimHub?label=download&color=e91e8c)](https://github.com/JamesInvaderbdx/-HandBrakeConfig-SimHub/releases)
[![SimHub](https://img.shields.io/badge/SimHub-9.x-4fc3f7)](https://www.simhubdash.com/)
[![License](https://img.shields.io/github/license/JamesInvaderbdx/-HandBrakeConfig-SimHub)](LICENSE)
[![Ko-Fi](https://img.shields.io/badge/buy%20me%20a%20coffee-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/eklid)

</div>

---

## Pourquoi ce plugin ?

La plupart des freins à main DIY arrivent en joystick HID basique ou en Arduino brut — sans calibration, sans zone morte, et avec une réponse linéaire peu réaliste. Ce plugin SimHub règle tout ça en quelques clics.

---

## Fonctionnalités

| Feature | Détail |
|---|---|
| **Dual input** | Joystick HID **ou** Arduino Nano via port série |
| **Calibration auto** | Tire/relâche → min/max détectés automatiquement |
| **Lissage** | Filtre moyenne glissante réglable (1–32 samples) |
| **Zone morte** | Deadzone bas (relâché) et haut (enfoncé) indépendantes |
| **Courbe de réponse** | Linéaire / Exponentielle / S-Curve + exposant réglable |
| **Inversion d'axe** | En un clic |
| **Sortie vJoy** | Device 2 / Axe Y — plug & play avec les jeux |
| **Propriétés SimHub** | `HandBrake.Output` [0–1] · `HandBrake.OutputPercent` [0–100] |

---

## Installation

### Plugin SimHub
1. Télécharger la dernière version → [Releases](https://github.com/JamesInvaderbdx/-HandBrakeConfig-SimHub/releases)
2. Copier `HandBrakeConfig.dll` dans `C:\Program Files (x86)\SimHub\`
3. Relancer SimHub → le plugin apparaît dans le menu latéral

### Prérequis optionnels
- **[vJoy](https://github.com/jshafer817/vJoy)** — pour l'émulation joystick vers les jeux
- **Arduino Nano + module KY-023** — pour le mode série

---

## Câblage Arduino (mode série)

```
KY-023  →  Arduino Nano
  GND   →  GND
  +5V   →  5V
  VRx   →  A1
  VRy   →  A2
  SW    →  D2
```

Flasher le sketch fourni : [`joystick_nano/joystick_nano.ino`](joystick_nano/joystick_nano.ino)

---

## Outil de calibration Python (standalone)

Un outil de calibration autonome (sans SimHub) est disponible dans [`calibration_tool/`](calibration_tool/).  
Idéal pour tester et ajuster le frein avant de lancer SimHub.

```bash
pip install pyserial customtkinter pyvjoy
python calibration_tool/handbrake_config.py
```

---

## Utilisation dans SimHub

Les propriétés sont exposées en temps réel :

```
HandBrake.Output          → valeur 0.0 à 1.0
HandBrake.OutputPercent   → valeur 0 à 100
```

Exemple dans un dashboard SimHub :
```
[HandBrake.OutputPercent] %
```

---

## Réglages recommandés pour commencer

| Paramètre | Valeur suggérée |
|---|---|
| Smooth (samples) | 8 (monter à 16 si encore instable) |
| Zone morte bas | 3–5% |
| Zone morte haut | 2–3% |
| Courbe | S-Curve (feeling plus naturel) |

---

## Contribuer / signaler un bug

Issues et PRs bienvenus → [Issues](https://github.com/JamesInvaderbdx/-HandBrakeConfig-SimHub/issues)

---

<div align="center">
Développé par <strong>eKLID</strong> — eKLID PiXL Production · Bordeaux<br>
<a href="https://ko-fi.com/eklid">☕ Offrir un café</a>
</div>
