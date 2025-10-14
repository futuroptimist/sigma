# Sigma docs viewer

A lightweight static server for previewing the contents of `../docs` during
hardware and firmware documentation work.

## Usage

```bash
cd viewer
npm install  # not required, but creates node_modules for parity with other repos
npm run dev  # serves docs on http://localhost:4173
```

Set `PORT=8000` (or similar) to pick a different port.  The server is dependency
free and relies solely on Node's `http` module.

The viewer is used in the migration guide to preview the STL safety callouts and
assembly diagrams added in this change.
