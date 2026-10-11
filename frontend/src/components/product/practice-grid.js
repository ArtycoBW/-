
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'


// Адаптация GetLayers Blocky Grid: scoped canvas, lifecycle, ограничение DPR/FPS.
export function mountPracticeGrid(canvas) {
const events = new AbortController();
/* ============================================================
   CONFIG  — every tweakable value lives here. Colors are '#rrggbb'
   strings; everything else is a number. The UI panel + localStorage
   persistence are generated from these keys.
   A white-background emergence grid (NOT the house black bloom rig):
   glass tiles grow out of an empty white field in a diagonal sweep,
   a blue glow band travelling across them, fog fading the far rows to
   white — authored from refs/photo_2026-08-05_14-34-21.jpg ("blocky").
============================================================ */
const CONFIG = {
  bgColor:      '#15191f',   // white field + tile TOPS — a flat seamless white at rest
  underColor:   '#8971bc',   // SKY-BLUE revealed on a tile's sides as it lifts
  edgeColor:    '#c3b2ef',   // bright rim that lights a raised tile's top edges
  shadeColor:   '#373043',   // cool ambient on the exposed blue sides

  gridCols:      24,         // tiles across X
  gridRows:      26,         // tiles across Z
  spacing:       0.48,       // world distance between tile centres
  tileScale:     0.9,        // tile footprint vs spacing — gaps let blue show between raised tiles
  tileHeight:    0.34,       // extruded height (the blue side wall you reveal)

  riseHeight:    0.85,       // how high a tile pops under the cursor

  diffuse:       0.5,        // key-light on the exposed sides
  fresnel:       0.4,        // glassy top-edge sheen (only while lifted)
  edgeWidth:     0.09,       // top-edge rim thickness
  edgeGlow:      0.8,        // top-edge rim brightness
  underGlow:     1.5,        // how strongly the sides read blue when lifted

  pointerRadius: 3.8,        // cursor lift falloff — the reach of the raised area (world units)
  pointerLift:   1.0,        // how high tiles rise directly under the cursor
  pulseSpeed:    3.0,        // double-click ripple expansion speed
  pulseWidth:    1.7,        // double-click ripple thickness

  fogNear:       8.0,        // distance the white haze starts
  fogFar:        28.0,       // distance the field fully fades to white

  autoRotate:    0,        // idle camera drift speed (0 = camera fully still)
  orbitDrag:     0,          // 1 = mouse-drag orbits the camera (0 = mouse ONLY raises tiles)
  camDist:       9.5         // camera distance from the field — the ZOOM slider (scroll stays off)
}

/* ---------- HELPERS ---------- */
function hexToVec3(hex) {
  const n = parseInt(hex.slice(1), 16)
  return new THREE.Vector3(((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255)
}

/* ---------- RENDERER / SCENE / CAMERA ---------- */

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'low-power' })
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
const scene = new THREE.Scene()
scene.background = new THREE.Color(CONFIG.bgColor)
const camera = new THREE.PerspectiveCamera(42, canvas.clientWidth / canvas.clientHeight, 0.1, 200)
camera.position.set(4.5, 11.5, 9)
scene.add(camera)

const controls = new OrbitControls(camera, renderer.domElement)
controls.enableDamping = true
controls.dampingFactor = 0.08
controls.minDistance = 4
controls.maxDistance = 40
controls.maxPolarAngle = Math.PI * 0.49          // keep the camera above the field
controls.target.set(0, 0.3, 0)
controls.enablePan = false
// drag-orbit + scroll-zoom are OFF by default (the mouse only raises tiles); the
// orbitDrag / scrollZoom CONFIG toggles below turn them back on from the panel.
controls.enableRotate = false
controls.enableZoom = false

/* ============================================================
   SCENE: BLOCKY GRID
   An InstancedBufferGeometry of unit boxes laid on the XZ plane.
   Every tile's emergence (grow + rise), idle shimmer, cursor lift,
   glowing wireframe frame, travelling blue band and fog fade are all
   computed on the GPU from per-instance attributes (aGrid, aDelay,
   aRand) + a single uTime clock, so nothing is stepped per-tile on CPU.
============================================================ */
class BlockyGrid {
  constructor(scene) {
    this.scene = scene
    this.uniforms = {
      iTime:       { value: 0 },
      uCam:        { value: new THREE.Vector3() },
      uPointer:    { value: new THREE.Vector2(999, 999) },
      uBg:         { value: hexToVec3(CONFIG.bgColor) },
      uUnder:      { value: hexToVec3(CONFIG.underColor) },
      uEdge:       { value: hexToVec3(CONFIG.edgeColor) },
      uShade:      { value: hexToVec3(CONFIG.shadeColor) },
      uFogColor:   { value: hexToVec3(CONFIG.bgColor) },
      uTileW:      { value: CONFIG.spacing * CONFIG.tileScale },
      uHeight:     { value: CONFIG.tileHeight },
      uRiseHeight: { value: CONFIG.riseHeight },
      uDiffuse:    { value: CONFIG.diffuse },
      uFresnel:    { value: CONFIG.fresnel },
      uEdgeWidth:  { value: CONFIG.edgeWidth },
      uEdgeGlow:   { value: CONFIG.edgeGlow },
      uUnderGlow:  { value: CONFIG.underGlow },
      uPtrRadius:  { value: CONFIG.pointerRadius },
      uPtrLift:    { value: CONFIG.pointerLift },
      uPulseTime:  { value: new Array(8).fill(-999) },      // ring buffer of concurrent click ripples
      uPulseCenter:{ value: Array.from({ length: 8 }, () => new THREE.Vector2(0, 0)) },
      uPulseSpeed: { value: CONFIG.pulseSpeed },
      uPulseWidth: { value: CONFIG.pulseWidth },
      uFogNear:    { value: CONFIG.fogNear },
      uFogFar:     { value: CONFIG.fogFar },
      uLightDir:   { value: new THREE.Vector3(0.5, 0.62, 0.4).normalize() }
    }
    this.material = new THREE.ShaderMaterial({
      uniforms: this.uniforms,
      vertexShader: `
        precision highp float;
        attribute vec3 aGrid;
        attribute float aRand;
        uniform float iTime, uTileW, uHeight, uRiseHeight;
        uniform float uPtrRadius, uPtrLift, uPulseSpeed, uPulseWidth;
        uniform vec2 uPointer;
        uniform vec2 uPulseCenter[8];
        uniform float uPulseTime[8];
        varying vec3 vNormal, vWorld, vLocal;
        varying float vLift;

        void main(){
          vLocal = position;                                   // unit box in [-0.5,0.5]
          // the field lies FLAT and seamless white at rest — tiles only rise where the CURSOR is.
          // a compact smooth falloff (exactly 0 past uPtrRadius) keeps the rest of the field flat
          float pd = distance(aGrid.xz, uPointer);
          float f = clamp(1.0 - pd / uPtrRadius, 0.0, 1.0);
          float lift = uPtrLift * f * f * (3.0 - 2.0 * f);
          // overlapping click ripples — fast clicks stack in the ring buffer and each ring
          // runs its full life independently, so a new click never cuts off the previous one
          for (int i = 0; i < 8; i++) {
            float age = iTime - uPulseTime[i];
            if (age < 0.0 || age > 3.5) continue;
            float front = age * uPulseSpeed;
            float r = distance(aGrid.xz, uPulseCenter[i]);
            lift += exp(-pow((r - front) / uPulseWidth, 2.0)) * smoothstep(3.5, 0.0, age);
          }
          lift = clamp(lift, 0.0, 1.0);
          vLift = lift;
          vec3 sp = vec3(position.x * uTileW, position.y * uHeight, position.z * uTileW);
          vec3 wp = aGrid + sp;
          // at rest each tile sits JUST BELOW the white base plane (hidden → the field is one
          // even white); the wave lifts it up through the plane so its top + blue sides emerge
          wp.y += lift * uRiseHeight - (uHeight * 0.5 + 0.04);
          vNormal = position.y >  0.49 ? vec3(0.0, 1.0, 0.0)
                  : position.y < -0.49 ? vec3(0.0,-1.0, 0.0)
                  : normalize(vec3(position.x, 0.0, position.z));
          vWorld = wp;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(wp, 1.0);
        }`,
      fragmentShader: `
        precision highp float;
        uniform vec3 uBg, uUnder, uEdge, uShade, uFogColor, uCam, uLightDir;
        uniform float uDiffuse, uFresnel, uEdgeWidth, uEdgeGlow, uUnderGlow, uFogNear, uFogFar;
        varying vec3 vNormal, vWorld, vLocal;
        varying float vLift;
        void main(){
          vec3 N = normalize(vNormal);
          vec3 V = normalize(uCam - vWorld);
          vec3 col;
          if (N.y > 0.5) {
            // TOP face — flat white at rest; a bright rim + glassy sheen only once lifted,
            // so the resting plane stays a perfectly even white with no visible squares
            col = uBg;
            vec3 a = 0.5 - abs(vLocal);
            float mx = max(a.x, max(a.y, a.z));
            float mn = min(a.x, min(a.y, a.z));
            float mid = a.x + a.y + a.z - mx - mn;
            float edge = 1.0 - smoothstep(0.0, uEdgeWidth, mid);
            float fres = pow(1.0 - max(dot(N, V), 0.0), 3.0);
            col += (edge * uEdge * uEdgeGlow + fres * uFresnel * uUnder) * vLift;
          } else {
            // SIDE (and underside) — the SKY-BLUE that shows from beneath as tiles rise.
            // The whole side (colour AND shading) fades in from flat white with lift, so an
            // un-lifted tile's sides are pure white and the resting plane reads perfectly even.
            float dif = max(dot(N, uLightDir), 0.0);
            vec3 base = mix(uBg, uUnder, clamp(vLift * uUnderGlow, 0.0, 1.0));
            vec3 lit = base * (uShade + dif * uDiffuse);
            col = mix(uBg, lit, clamp(vLift, 0.0, 1.0));
          }
          float fog = smoothstep(uFogNear, uFogFar, distance(uCam, vWorld));
          col = mix(col, uFogColor, fog);
          gl_FragColor = vec4(col, 1.0);
        }`,
      side: THREE.FrontSide
    })
    // Solid white base plane just under the tile tops — hides the hairline seams
    // between abutting tiles so the resting field reads as one perfectly even white,
    // and backs the gaps a lifted tile opens up (its blue sides sit above this plane).
    this.base = new THREE.Mesh(
      new THREE.PlaneGeometry(1, 1),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(CONFIG.bgColor) })
    )
    this.base.rotation.x = -Math.PI / 2
    scene.add(this.base)
    this.pulseIdx = 0
    this.shapeSig = ''
    this.build()
  }

  build() {
    const cols = CONFIG.gridCols, rows = CONFIG.gridRows, sp = CONFIG.spacing
    const sig = cols + 'x' + rows + 'x' + sp.toFixed(3)
    if (sig === this.shapeSig) return
    this.shapeSig = sig
    if (this.mesh) { this.scene.remove(this.mesh); this.geometry.dispose() }

    const box = new THREE.BoxGeometry(1, 1, 1)
    const geo = new THREE.InstancedBufferGeometry()
    geo.index = box.index
    geo.setAttribute('position', box.attributes.position)
    geo.setAttribute('normal', box.attributes.normal)

    const count = cols * rows
    const grid = new Float32Array(count * 3)
    const rand = new Float32Array(count)
    const ox = (cols - 1) * 0.5, oz = (rows - 1) * 0.5
    let i = 0
    for (let c = 0; c < cols; c++) {
      for (let r = 0; r < rows; r++) {
        grid[i * 3]     = (c - ox) * sp
        grid[i * 3 + 1] = 0
        grid[i * 3 + 2] = (r - oz) * sp
        const jit = (Math.sin(c * 12.9898 + r * 78.233) * 43758.5453) % 1
        rand[i] = jit < 0 ? jit + 1 : jit
        i++
      }
    }
    geo.setAttribute('aGrid', new THREE.InstancedBufferAttribute(grid, 3))
    geo.setAttribute('aRand', new THREE.InstancedBufferAttribute(rand, 1))
    geo.instanceCount = count

    this.geometry = geo
    this.mesh = new THREE.Mesh(geo, this.material)
    this.mesh.frustumCulled = false                                // custom vertex positions
    this.scene.add(this.mesh)

    const ext = Math.max(cols, rows) * sp * 1.4                    // cover the whole field + margin
    this.base.scale.set(ext, ext, 1)
    this.base.position.y = 0                                       // the flat white resting surface
  }

  // a click sends an expanding ripple ring out from the point that was clicked; each click
  // takes the next ring-buffer slot so rapid clicks stack instead of interrupting one another
  pulse(x, z) {
    const i = this.pulseIdx
    this.uniforms.uPulseCenter.value[i].set(x, z)
    this.uniforms.uPulseTime.value[i] = this.uniforms.iTime.value
    this.pulseIdx = (i + 1) % 8
  }

  resize() {}

  render() {
    this.uniforms.iTime.value = performance.now() / 1000
    this.uniforms.uCam.value.copy(camera.position)
  }
}

const sceneObj = new BlockyGrid(scene)

/* ---------- POINTER LIFT (raycast onto the y=0 plane) ---------- */
const raycaster = new THREE.Raycaster()
const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0)
const ndc = new THREE.Vector2()
const hit = new THREE.Vector3()
const pointerTarget = new THREE.Vector2(0, 0)
let pointerActive = false
canvas.addEventListener('pointermove', e => {
  pointerActive = true
  ndc.x = ((e.clientX - canvas.getBoundingClientRect().left) / canvas.clientWidth) * 2 - 1
  ndc.y = -((e.clientY - canvas.getBoundingClientRect().top) / canvas.clientHeight) * 2 + 1
  raycaster.setFromCamera(ndc, camera)
  if (raycaster.ray.intersectPlane(groundPlane, hit)) pointerTarget.set(hit.x, hit.z)
}, {signal: events.signal})
canvas.addEventListener('pointerleave', () => { pointerActive = false }, {signal: events.signal})
canvas.addEventListener('click', e => {
  ndc.x = ((e.clientX - canvas.getBoundingClientRect().left) / canvas.clientWidth) * 2 - 1
  ndc.y = -((e.clientY - canvas.getBoundingClientRect().top) / canvas.clientHeight) * 2 + 1
  raycaster.setFromCamera(ndc, camera)
  if (raycaster.ray.intersectPlane(groundPlane, hit)) sceneObj.pulse(hit.x, hit.z)
}, {signal: events.signal})

/* ---------- CONFIG → uniforms ---------- */
function applyConfig() {
  const u = sceneObj.uniforms
  scene.background.set(CONFIG.bgColor)
  u.uFogColor.value.copy(hexToVec3(CONFIG.bgColor))
  u.uBg.value.copy(hexToVec3(CONFIG.bgColor))
  u.uUnder.value.copy(hexToVec3(CONFIG.underColor))
  u.uEdge.value.copy(hexToVec3(CONFIG.edgeColor))
  u.uShade.value.copy(hexToVec3(CONFIG.shadeColor))
  u.uTileW.value = CONFIG.spacing * CONFIG.tileScale
  u.uHeight.value = CONFIG.tileHeight
  sceneObj.base.material.color.set(CONFIG.bgColor)
  u.uRiseHeight.value = CONFIG.riseHeight
  u.uDiffuse.value = CONFIG.diffuse
  u.uFresnel.value = CONFIG.fresnel
  u.uEdgeWidth.value = CONFIG.edgeWidth
  u.uEdgeGlow.value = CONFIG.edgeGlow
  u.uUnderGlow.value = CONFIG.underGlow
  u.uPtrRadius.value = CONFIG.pointerRadius
  u.uPtrLift.value = CONFIG.pointerLift
  u.uPulseSpeed.value = CONFIG.pulseSpeed
  u.uPulseWidth.value = CONFIG.pulseWidth
  u.uFogNear.value = CONFIG.fogNear
  u.uFogFar.value = CONFIG.fogFar
  controls.autoRotate = CONFIG.autoRotate > 0.001
  controls.autoRotateSpeed = CONFIG.autoRotate * 10
  controls.enableRotate = CONFIG.orbitDrag > 0.5
  // zoom is a SLIDER, not the wheel: re-place the camera along its current view direction
  // at the requested distance from the target (scroll-zoom stays disabled)
  const camDir = camera.position.clone().sub(controls.target).normalize()
  camera.position.copy(controls.target).addScaledVector(camDir, CONFIG.camDist)
  sceneObj.build()                                               // rebuilds only on grid/spacing change
}

/* ---------- RESIZE ---------- */
function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight, dpr = Math.min(window.devicePixelRatio, 1.5)
  renderer.setPixelRatio(dpr); renderer.setSize(w, h, false)
  camera.aspect = w / h; camera.updateProjectionMatrix()
  sceneObj.resize()
}
const observer = new ResizeObserver(resize); observer.observe(canvas); applyConfig(); resize()

let visible = true, last = 0, frame = 0;
const intersection = new IntersectionObserver(entries => {visible = entries[0].isIntersecting;});
intersection.observe(canvas);
function render(t) {
  frame = requestAnimationFrame(render);
  if (!visible || document.hidden || t-last < 33) return;
  if (!pointerActive) pointerTarget.set(Math.sin(t / 6000) * 2.3, Math.cos(t / 7000) * 1.8);
  if (sceneObj.uniforms.uPointer.value.x > 900) sceneObj.uniforms.uPointer.value.copy(pointerTarget);
  sceneObj.uniforms.uPointer.value.lerp(pointerTarget, 0.07);
  last=t; sceneObj.render(); controls.update(); renderer.render(scene,camera);
}
frame=requestAnimationFrame(render);
return () => {
  cancelAnimationFrame(frame); events.abort(); observer.disconnect(); intersection.disconnect(); controls.dispose();
  scene.traverse(object => { if (object.geometry) object.geometry.dispose(); if(object.material) (Array.isArray(object.material) ? object.material : [object.material]).forEach(m => m.dispose()); });
  renderer.dispose(); renderer.forceContextLoss();
};

}
