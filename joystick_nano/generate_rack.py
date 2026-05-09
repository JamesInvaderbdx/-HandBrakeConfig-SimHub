"""
Génère le profil 2D du rack en DXF — importable dans Fusion 360
Rack & Pinion frein à main KY-040 — module 1.0
"""

import math
import struct

# ── Paramètres ───────────────────────────────────────────────
MODULE   = 1.0    # module engrenage
TRAVEL   = 15.0   # course frein à main (mm)
BASE_H   = 4.0    # hauteur de la base sous les dents (mm)
WIDTH    = 8.0    # épaisseur (info seulement — extrusion dans Fusion)
CLEARANCE = 0.1   # jeu flancs de dent

# ── Calculs ──────────────────────────────────────────────────
pitch    = math.pi * MODULE          # pas = 3.1416 mm
tooth_h  = 2.25 * MODULE            # hauteur dent = 2.25 mm
tw_base  = pitch / 2 - CLEARANCE    # largeur base dent
tw_tip   = pitch / 4                # largeur sommet dent
n_teeth  = math.ceil((TRAVEL + 2 * pitch) / pitch)
rack_len = n_teeth * pitch

print(f"=== RACK — module {MODULE} ===")
print(f"  Pas (pitch)      : {pitch:.3f} mm")
print(f"  Hauteur dent     : {tooth_h:.3f} mm")
print(f"  Largeur base     : {tw_base:.3f} mm")
print(f"  Largeur sommet   : {tw_tip:.3f} mm")
print(f"  Nb dents         : {n_teeth}")
print(f"  Longueur totale  : {rack_len:.2f} mm")
print(f"  Hauteur totale   : {BASE_H + tooth_h:.3f} mm")
print(f"  Épaisseur (extr) : {WIDTH} mm")
print()

# ── Construction du profil (liste de points) ─────────────────
def rack_profile(n, pitch, tooth_h, tw_base, tw_tip, base_h):
    """Retourne la polyligne fermée du profil rack."""
    pts = []

    # Départ coin bas-gauche
    pts.append((0.0, 0.0))

    for i in range(n):
        x0 = i * pitch
        gap = pitch - tw_base          # espace entre deux dents
        x1 = x0 + gap / 2             # début flanc montant gauche
        x2 = x1 + (tw_base - tw_tip) / 2  # début sommet
        x3 = x2 + tw_tip              # fin sommet
        x4 = x3 + (tw_base - tw_tip) / 2  # fin flanc descendant

        pts.append((x1, base_h))
        pts.append((x2, base_h + tooth_h))
        pts.append((x3, base_h + tooth_h))
        pts.append((x4, base_h))

    pts.append((rack_len, base_h))
    pts.append((rack_len, 0.0))
    pts.append((0.0, 0.0))  # fermeture
    return pts

profile = rack_profile(n_teeth, pitch, tooth_h, tw_base, tw_tip, BASE_H)

# ── Export DXF R12 (compatible toutes versions Fusion 360) ────
def write_dxf(filename, pts):
    with open(filename, 'w') as f:
        f.write("0\nSECTION\n2\nHEADER\n")
        f.write("9\n$ACADVER\n1\nAC1009\n")   # R12 — compatible partout
        f.write("0\nENDSEC\n")
        f.write("0\nSECTION\n2\nENTITIES\n")
        # Segments LINE entre chaque paire de points
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            f.write("0\nLINE\n8\n0\n")
            f.write("10\n{:.6f}\n20\n{:.6f}\n30\n0.0\n".format(x1, y1))
            f.write("11\n{:.6f}\n21\n{:.6f}\n31\n0.0\n".format(x2, y2))
        f.write("0\nENDSEC\n0\nEOF\n")
    print(f"  -> {filename}")

out = "rack_handbrake.dxf"
write_dxf(out, profile)
print(f"DXF genere : {out}")
print()
print("Dans Fusion 360 :")
print("  Insert > Insert DXF > selectionner rack_handbrake.dxf")
print("  Extrude le profil sur 8 mm")
print("  Ajouter trous de fixation selon besoin")
