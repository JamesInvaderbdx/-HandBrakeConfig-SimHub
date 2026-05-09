// ============================================================
// Rack & Pinion — Frein à main KY-040
// Module 1.0 | 8 dents | PLA | Buse 0.4
// ============================================================

m         = 1.0;   // module
N         = 8;     // dents pignon
travel    = 15;    // course linéaire mm
thickness = 8;     // épaisseur engrenages mm

shaft_d   = 6.0;   // axe KY-040 mm
flat_d    = 5.5;   // cote du plat D (mesurer sur votre pièce)

clearance = 0.2;   // jeu impression

// --- Calculs ---
r_pitch = m * N / 2;          // rayon primitif = 4 mm
r_tip   = r_pitch + m;        // rayon de tête  = 5 mm
r_root  = r_pitch - 1.25 * m; // rayon de pied  = 2.75 mm
pitch   = PI * m;             // pas = 3.14 mm
rack_l  = travel + 4 * pitch; // longueur rack avec marges

// ============================================================
// PIGNON
// ============================================================
module tooth_2d() {
    tw_base = pitch / 2 - 0.1;
    tw_tip  = pitch / 4;
    h       = r_tip - r_root;
    polygon([
        [-tw_base/2, 0],
        [ tw_base/2, 0],
        [ tw_tip/2,  h],
        [-tw_tip/2,  h]
    ]);
}

module pinion() {
    difference() {
        // Corps principal
        linear_extrude(thickness)
        difference() {
            circle(r = r_tip, $fn = 64);
            circle(r = r_root, $fn = 64);
            for (i = [0 : N-1])
                rotate([0, 0, i * 360/N])
                    translate([0, r_root])
                        tooth_2d();
        }
        // Alésage axe D
        translate([0, 0, -0.5]) {
            cylinder(d = shaft_d + clearance, h = thickness + 1, $fn = 32);
            translate([flat_d/2, -(shaft_d+1)/2, 0])
                cube([shaft_d, shaft_d + 1, thickness + 1]);
        }
    }
}

// ============================================================
// RACK
// ============================================================
module rack_tooth_2d() {
    tw_base = pitch / 2 - 0.1;
    tw_tip  = pitch / 4;
    h       = 2.25 * m;
    polygon([
        [-tw_base/2, 0],
        [ tw_base/2, 0],
        [ tw_tip/2,  h],
        [-tw_tip/2,  h]
    ]);
}

module rack() {
    n_teeth = floor(rack_l / pitch);
    base_h  = 4;

    union() {
        // Base
        cube([rack_l, base_h, thickness]);
        // Dents
        for (i = [0 : n_teeth - 1])
            translate([i * pitch + pitch/2, base_h, 0])
                linear_extrude(thickness)
                    rack_tooth_2d();
    }
}

// ============================================================
// RENDU — modifier pour exporter séparément
// ============================================================

// Pignon
translate([0, 0, 0])
    pinion();

// Rack (décalé pour visualisation)
translate([20, -10, 0])
    rack();
