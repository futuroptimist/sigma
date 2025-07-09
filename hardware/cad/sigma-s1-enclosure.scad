// Simple enclosure for Sigma S1
// Designed for ESP32-WROOM module with mic, speaker, and AA battery compartment
// Parameters allow tweaking wall thickness and overall dimensions

thickness = 2;            // wall thickness in mm
width = 60;               // enclosure width in mm
height = 80;              // enclosure height in mm
depth = 30;               // enclosure depth in mm
battery_length = 52;      // length of AA battery compartment

module shell() {
    difference() {
        // outer shell
        cube([width, depth, height], center=false);
        // hollow interior
        translate([thickness, thickness, thickness])
            cube([width-2*thickness, depth-2*thickness, height-2*thickness], center=false);
        // battery cutout at bottom
        translate([(width-battery_length)/2, depth-1, thickness])
            cube([battery_length, 1, 14], center=false);
    }
}

shell();
