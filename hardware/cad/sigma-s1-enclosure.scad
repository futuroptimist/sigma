/* Sigma S1 Enclosure
   Basic shell for an ESP32 device with
   push-to-talk button, microphone and speaker.
   Inspired by wove/flywheel/sugarkube CAD conventions.
*/

wall = 2;             // shell thickness in mm
width = 60;           // outer width
height = 80;          // outer height
depth = 30;           // outer depth
battery_length = 52;  // AA holder length

button_d = 8;         // diameter of push button hole
mic_d = 3;            // microphone opening
speaker_d = 10;       // overall speaker area
speaker_holes = 5;    // number of speaker vents

module battery_cutout() {
    translate([(width-battery_length)/2, depth-1, wall])
        cube([battery_length, 1, 14], center=false);
}

module button_hole() {
    translate([width/2, 0, height-20])
        rotate([90,0,0])
            cylinder(d=button_d, h=depth+1);
}

module mic_hole() {
    translate([width/3, 0, height/2])
        rotate([90,0,0])
            cylinder(d=mic_d, h=depth+1);
}

module speaker_grill() {
    for(i=[0:speaker_holes-1])
        translate([2*width/3, 0, height/2 + i*4])
            rotate([90,0,0])
                cylinder(d=speaker_d/speaker_holes, h=depth+1);
}

module enclosure() {
    difference() {
        cube([width, depth, height], center=false);
        translate([wall, wall, wall])
            cube([width-2*wall, depth-2*wall, height-2*wall], center=false);
        battery_cutout();
        button_hole();
        mic_hole();
        speaker_grill();
    }
}

enclosure();
