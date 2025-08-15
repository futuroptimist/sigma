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
speaker_holes = 7;    // number of speaker vents
lanyard_d = 5;        // diameter of lanyard holes
lanyard_offset = 6;   // distance from each edge
usb_w = 14;           // width of USB-C cutout (extra cable clearance)
usb_h = 4;            // height of USB-C cutout
usb_z = 10;           // distance from bottom to cutout

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

module lanyard_holes() {
    for (x=[lanyard_offset, width - lanyard_offset])
        translate([x, depth/2, height - wall/2])
            cylinder(d=lanyard_d, h=wall+1, center=true);
}

module usb_cutout() {
    translate([width/2 - usb_w/2, -1, wall + usb_z])
        cube([usb_w, wall + 2, usb_h], center=false);
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
        lanyard_holes();
        usb_cutout();
    }
}

enclosure();
