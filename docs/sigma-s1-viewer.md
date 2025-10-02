# Sigma S1 3D Viewer

Inspect the Sigma S1 enclosure directly in your browser using the interactive
viewer below. The embedded component renders the STL exported from the
OpenSCAD source in `hardware/cad/`.

<script type="module"
        src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js">
</script>

<model-viewer src="../hardware/stl/sigma-s1-enclosure.stl"
              alt="Sigma S1 enclosure"
              camera-controls
              auto-rotate
              ar
              style="width: 100%; height: 500px; background-color: #f4f4f4;">
  Loading 3D model...
</model-viewer>

The viewer supports touch and mouse gestures for orbiting, zooming, and
panning. Use the toolbar buttons that appear on hover to reset the camera or
switch between interaction modes.
