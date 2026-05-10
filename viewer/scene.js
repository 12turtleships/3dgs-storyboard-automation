import * as THREE from 'three';
import { SparkRenderer, SplatMesh } from '@sparkjsdev/spark';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// Immediate sync update — proves JS bundle executed
document.getElementById('load-status').textContent = 'v9 — JS running';

// Show any unhandled error visibly on the loading screen
function showError(msg) {
  const el = document.getElementById('loading');
  if (el) {
    el.style.display = 'flex';
    el.style.opacity = '1';
    el.innerHTML = `<div style="color:#e55;font-size:13px;max-width:80%;text-align:center;line-height:1.6">${msg}</div>`;
  }
  console.error(msg);
}
window.addEventListener('error', e => showError(`JS Error: ${e.message}<br>${e.filename}:${e.lineno}`));
window.addEventListener('unhandledrejection', e => showError(`Promise rejected: ${e.reason}`));

// ---------------------------------------------------------------------------
// World assets
// DEFAULT_SPZ_URL: shared campus world used by shots without a spzUrl.
// Per-shot SPZ: add `spzUrl: '...'` to any SHOTS entry to load a different
// world for that shot (e.g. a higher-quality regeneration of a specific scene).
// ---------------------------------------------------------------------------
const DEFAULT_SPZ_URL = 'https://cdn.marble.worldlabs.ai/fcf05383-91d7-4880-8186-98899075f4a1/2da89a0f-f85d-4077-8a7a-0540631cb250_ceramic_500k.spz';
let currentSpzUrl = null; // tracks which SPZ is currently loaded

// ---------------------------------------------------------------------------
// Camera calibration
// Observed: Y=-30 → ground visible, Y=-1 → sky visible.
// ground  = bbox.max.y - size.y * 0.40  (≈ -30 for this world)
// eyeLevel = ground + 1.7               (human eye height, ≈ -28.3)
// Exposed as module-level var so animateCamera can use it per shot.
// ---------------------------------------------------------------------------
let eyeLevel = -28;   // overwritten in onLoad after bbox calibration
let worldCentre = new THREE.Vector3(); // set in onLoad; used by animateCamera for zSnap

// ---------------------------------------------------------------------------
// Scene 01 shots — WHO / WHERE / WHEN from story_plot.py
//
// yaw:     horizontal look direction in degrees (0 = forward / toward -Z)
// pitch:   vertical tilt in degrees (+90 = straight up, -90 = straight down)
// fov:     horizontal field of view in degrees
// yOffset: camera Y = eyeLevel + yOffset  (THREE.js Y-up)
//          For normal shots  (+ve = higher, -ve = lower/ground)
//          For flipUp shots  visual altitude is INVERTED: +ve = visually lower,
//                            -ve (smaller yOffset) = visually higher aerial view
// zSnap:   camera Z = worldCentre.z + zSnap  (omit → worldCentre.z = tree centre)
//          +ve → in front of scene centre (toward viewer), -ve → behind
// ---------------------------------------------------------------------------
const SHOTS = [
  {
    id: '1A', label: 'Full Campus — The Entire World Revealed',
    who: 'None', where: 'Full campus, aerial approach', when: 'Early morning',
    yaw: 0, pitch: -42, fov: 85,
    yOffset: 24,  // Y≈-4.3 — visually higher (with flipUp, more -Y = higher visual altitude)
    zSnap: 34,    // Z = centre.z + 34 ≈ 0, near scene centre
    flipUp: true, // camera.up=(0,-1,0): scene visual-up is -Y in THREE.js world
    characters: [],
  },
  {
    id: '1B', label: 'Courtyard Wide — Tree as Undeniable Center',
    who: 'The Tree', where: 'Central courtyard, ground level', when: 'Early morning',
    yaw: 0, pitch: 0, fov: 85,
    yOffset: 0,    // eye level, looking straight ahead — calibrate after testing new world
    characters: [],
  },
  {
    id: '1C', label: "Worm's Eye — The Monolith Reveal",
    who: 'The Tree', where: 'Under the tree', when: 'Early morning',
    yaw: 0, pitch: 75, fov: 70,
    yOffset: -1.5, // at/near ground, looking near-vertically upward
    characters: [],
  },
  {
    id: '1D', label: 'Canopy Upshot — Natural Cathedral',
    who: 'The Tree', where: 'Under the tree', when: 'Mid-morning',
    yaw: 0, pitch: 65, fov: 80,
    yOffset: 0,    // eye level, steep upward look through canopy
    characters: [],
  },
  {
    id: '1E', label: 'Root Level — Nature Reclaiming Stone',
    who: 'The Tree', where: 'Courtyard, ground level', when: 'Early morning',
    yaw: 0, pitch: -20, fov: 75,
    yOffset: -1.5, // at ground, slight downward look at roots
    characters: [],
  },
  {
    id: '1F', label: 'Transition — Campus Full, Students Blind',
    who: 'Students (background)', where: 'Central courtyard', when: 'Mid-morning',
    yaw: 0, pitch: 5, fov: 100,
    yOffset: 0,    // eye level, very slight upward tilt — calibrate after testing new world
    characters: [
      { role: 'student', x: -2, z: -8,  rotY: 0.3  },
      { role: 'student', x:  1, z: -6,  rotY: -0.2 },
      { role: 'student', x:  3, z: -10, rotY: 0.5  },
    ],
  },
];

// ---------------------------------------------------------------------------
// Character placeholder colours (used until .fbx/glb files are provided)
// ---------------------------------------------------------------------------
const CHAR_COLORS = {
  zara:      0x8b7355,
  student:   0x4a6fa5,
  professor: 0x6b5b45,
};

// ---------------------------------------------------------------------------
// Three.js setup
// ---------------------------------------------------------------------------
const container = document.getElementById('canvas-container');
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true });
} catch (e) {
  showError(`WebGL failed to initialise: ${e.message}<br>Try a different browser or enable hardware acceleration.`);
  throw e;
}
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
container.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(85, window.innerWidth / window.innerHeight, 0.01, 1000);
camera.position.set(0, eyeLevel, 0);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.rotateSpeed = 0.6;
controls.zoomSpeed = 0.8;
controls.panSpeed = 1.0;
controls.screenSpacePanning = true;   // pan tracks screen, not world-up
controls.minPolarAngle = 0;           // allow full vertical rotation
controls.maxPolarAngle = Math.PI;
controls.minDistance = 0.1;           // no minimum zoom distance
controls.maxDistance = Infinity;      // no maximum zoom distance
controls.target.set(0, eyeLevel, -5);
controls.update();

// ---------------------------------------------------------------------------
// Spark renderer — must be added to the scene so onBeforeRender fires
// ---------------------------------------------------------------------------
const spark = new SparkRenderer({ renderer });
scene.add(spark);

// ---------------------------------------------------------------------------
// Load the .spz world — manual fetch for visible progress + error handling
// onReady(groundY) is called after bbox calibration, before the loading
// overlay is hidden, so the caller can snap the camera first.
// ---------------------------------------------------------------------------
const loadBar = document.getElementById('load-bar');
const loading = document.getElementById('loading');
const loadSub = document.getElementById('load-status');

let splat;

async function loadSplatFromUrl(url, onReady) {
  // Remove existing splat from scene so the old world disappears cleanly.
  if (splat) { scene.remove(splat); splat = null; }

  loading.style.display = 'flex';
  loading.style.opacity = '1';
  loading.style.transition = '';
  loadBar.style.width = '0%';

  const timeout = setTimeout(() => {
    showError('Timed out after 45 s.<br>The world file may be unreachable from your network.<br>Try a hard-refresh (Ctrl+Shift+R / Cmd+Shift+R) or check your connection.');
  }, 45000);

  try {
    loadSub.textContent = 'Connecting to CDN…';
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status} from CDN`);

    const total = parseInt(response.headers.get('content-length') || '0');
    const reader = response.body.getReader();
    const chunks = [];
    let received = 0;

    loadSub.textContent = 'Downloading world…';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      received += value.length;
      const pct = total ? Math.round(received / total * 85) : Math.min(85, Math.round(received / 300000));
      loadBar.style.width = pct + '%';
      loadSub.textContent = `Downloading… ${(received / 1e6).toFixed(1)} MB`;
    }

    loadSub.textContent = 'Initialising 3D scene…';
    loadBar.style.width = '90%';

    const buffer = new Uint8Array(received);
    let pos = 0;
    for (const chunk of chunks) { buffer.set(chunk, pos); pos += chunk.length; }

    splat = new SplatMesh({
      fileBytes: buffer.buffer,
      onLoad: (mesh) => {
        try {
          loadBar.style.width = '100%';

          const bbox = mesh.getBoundingBox();
          const centre = new THREE.Vector3();
          bbox.getCenter(centre);
          const size = new THREE.Vector3();
          bbox.getSize(size);

          console.log('SPZ bbox — centre:', centre, 'size:', size);

          // ground ≈ bbox.max.y - size.y * 0.40  (calibrated empirically)
          const groundY = bbox.max.y - size.y * 0.40;
          eyeLevel = groundY + 1.7;
          worldCentre.copy(centre);
          currentSpzUrl = url;

          console.log(`groundY=${groundY.toFixed(2)}  eyeLevel=${eyeLevel.toFixed(2)}`);

          onReady(groundY, centre);

          setTimeout(() => {
            loading.style.opacity = '0';
            loading.style.transition = 'opacity 0.5s';
            setTimeout(() => loading.style.display = 'none', 500);
          }, 300);
        } catch (err) {
          showError(`Scene init error: ${err.message}`);
        }
      },
    });
    splat.position.set(0, 0, 0);
    scene.add(splat);

    clearTimeout(timeout);
  } catch (err) {
    clearTimeout(timeout);
    showError(`Failed to load world:<br>${err.message}`);
  }
}

function snapCameraToShot(shot, groundY, centre) {
  const destY = eyeLevel + (shot.yOffset || 0);
  camera.fov = shot.fov;
  camera.updateProjectionMatrix();
  camera.up.set(0, shot.flipUp ? -1 : 1, 0);
  camera.position.set(centre.x, destY, centre.z + (shot.zSnap || 0));

  const yawRad   = THREE.MathUtils.degToRad(shot.yaw);
  const pitchRad = THREE.MathUtils.degToRad(shot.pitch);
  const dx =  Math.sin(yawRad) * Math.cos(pitchRad);
  const dy =  Math.sin(pitchRad);
  const dz = -Math.cos(yawRad) * Math.cos(pitchRad);
  const visualCentre = new THREE.Vector3(centre.x, groundY, centre.z);
  const tDist = Math.max(30, camera.position.distanceTo(visualCentre));
  controls.target.set(
    camera.position.x + dx * tDist,
    camera.position.y + dy * tDist,
    camera.position.z + dz * tDist
  );
  controls.update();
}

// Initial load — snap to first shot after calibration.
loadSplatFromUrl(DEFAULT_SPZ_URL, (groundY, centre) => {
  const shot = SHOTS[currentShot];
  snapCameraToShot(shot, groundY, centre);
  document.getElementById('shot-label').textContent = `Shot ${shot.id} — ${shot.label}`;
  updateCharInfo(shot);
  buildNav();
});

// ---------------------------------------------------------------------------
// Ambient + directional light (summer midday)
// ---------------------------------------------------------------------------
scene.add(new THREE.AmbientLight(0xfff8e8, 1.2));
const sun = new THREE.DirectionalLight(0xfff5d0, 2.5);
sun.position.set(2, 8, 3);
scene.add(sun);

// ---------------------------------------------------------------------------
// Character placeholders (capsule geometry, colored by role)
// Replaced by real .glb files when Mixamo assets are provided
// ---------------------------------------------------------------------------
const gltfLoader = new GLTFLoader();
const fbxLoader = new FBXLoader();
const characterMeshes = {};
const mixers = [];

function makeCharacterPlaceholder(role) {
  const group = new THREE.Group();
  const color = CHAR_COLORS[role] || 0x888888;

  const body = new THREE.Mesh(
    new THREE.CapsuleGeometry(0.22, 0.9, 4, 8),
    new THREE.MeshLambertMaterial({ color })
  );
  body.position.y = 0.85;
  group.add(body);

  const head = new THREE.Mesh(
    new THREE.SphereGeometry(0.18, 8, 8),
    new THREE.MeshLambertMaterial({ color })
  );
  head.position.y = 1.65;
  group.add(head);

  if (role === 'student') {
    const phone = new THREE.Mesh(
      new THREE.BoxGeometry(0.07, 0.13, 0.01),
      new THREE.MeshLambertMaterial({ color: 0x111111, emissive: 0x223344, emissiveIntensity: 0.8 })
    );
    phone.position.set(0.12, 1.55, -0.22);
    group.add(phone);
  }

  return group;
}

function tryLoadFBX(role, path, onSuccess) {
  fbxLoader.load(
    path,
    (fbx) => {
      fbx.scale.setScalar(0.01); // Mixamo FBX is in cm, THREE.js in m
      if (fbx.animations && fbx.animations.length > 0) {
        const mixer = new THREE.AnimationMixer(fbx);
        mixer.clipAction(fbx.animations[0]).play();
        fbx.userData.mixer = mixer;
        mixers.push(mixer);
      }
      onSuccess(fbx);
    },
    undefined,
    () => { onSuccess(makeCharacterPlaceholder(role)); }
  );
}

function tryLoadGLB(role, path, onSuccess) {
  gltfLoader.load(
    path,
    (gltf) => {
      const obj = gltf.scene;
      if (gltf.animations && gltf.animations.length > 0) {
        const mixer = new THREE.AnimationMixer(obj);
        mixer.clipAction(gltf.animations[0]).play();
        obj.userData.mixer = mixer;
        mixers.push(mixer);
      }
      onSuccess(obj);
    },
    undefined,
    () => { onSuccess(makeCharacterPlaceholder(role)); }
  );
}

// Attempt to load real character files; fall back to placeholders
const charPaths = {
  zara:      { path: '../characters/zara_idle.glb',            type: 'glb' },
  student:   { path: '../characters/student_texting_walk.fbx', type: 'fbx' },
  professor: { path: '../characters/professor_idle.glb',       type: 'glb' },
};

const charModels = {};
Object.entries(charPaths).forEach(([role, { path, type }]) => {
  const loader = type === 'fbx' ? tryLoadFBX : tryLoadGLB;
  loader(role, path, (obj) => { charModels[role] = obj; });
});

// ---------------------------------------------------------------------------
// Shot navigation
// ---------------------------------------------------------------------------
let currentShot = 0;

function buildNav() {
  const nav = document.getElementById('nav');
  const arrows = document.getElementById('arrows');
  nav.innerHTML = '';
  nav.appendChild(arrows);

  SHOTS.forEach((shot, i) => {
    const btn = document.createElement('button');
    btn.className = 'shot-btn' + (i === currentShot ? ' active' : '');
    btn.innerHTML = `<span class="shot-id">${shot.id}</span><span class="shot-name">${shot.label.split('—')[0].trim()}</span>`;
    btn.onclick = () => goToShot(i);
    nav.appendChild(btn);
  });

  arrows.querySelector('#btn-prev').onclick = () => goToShot((currentShot - 1 + SHOTS.length) % SHOTS.length);
  arrows.querySelector('#btn-next').onclick = () => goToShot((currentShot + 1) % SHOTS.length);
}

function placeCharacters(shot) {
  Object.values(characterMeshes).forEach(m => scene.remove(m));
  Object.keys(characterMeshes).forEach(k => delete characterMeshes[k]);
  shot.characters.forEach((c, i) => {
    const model = charModels[c.role];
    if (!model) return;
    const clone = model.clone(true);
    clone.position.set(c.x, 0, c.z);
    clone.rotation.y = c.rotY || 0;
    if (!clone.scale.x || clone.scale.x === 1.0) clone.scale.setScalar(1.0);
    scene.add(clone);
    if (model.userData.mixer) {
      const srcAction = model.userData.mixer._actions[0];
      if (srcAction) {
        const mixer = new THREE.AnimationMixer(clone);
        mixer.clipAction(srcAction._clip).play();
        mixers.push(mixer);
        clone.userData.mixer = mixer;
      }
    }
    characterMeshes[`char_${i}`] = clone;
  });
}

function goToShot(index) {
  currentShot = index;
  const shot = SHOTS[index];
  const targetUrl = shot.spzUrl || DEFAULT_SPZ_URL;

  document.getElementById('shot-label').textContent = `Shot ${shot.id} — ${shot.label}`;
  updateCharInfo(shot);
  buildNav();

  if (targetUrl !== currentSpzUrl) {
    // Different world — reload SPZ, then snap camera (no lerp: new world, new coords).
    loadSplatFromUrl(targetUrl, (groundY, centre) => {
      placeCharacters(shot);
      snapCameraToShot(shot, groundY, centre);
    });
    return;
  }

  placeCharacters(shot);
  animateCamera(shot);
}

function updateCharInfo(shot) {
  const info = document.getElementById('char-info');
  if (shot.who === 'None') { info.style.display = 'none'; return; }
  info.style.display = 'block';
  document.getElementById('ci-who').textContent = `WHO: ${shot.who}`;
  document.getElementById('ci-where').textContent = `WHERE: ${shot.where}`;
  document.getElementById('ci-when').textContent = `WHEN: ${shot.when}`;
}

// ---------------------------------------------------------------------------
// Camera animation
//
// Each shot defines yaw/pitch/fov (look direction) and yOffset (Y position
// relative to eyeLevel). animateCamera moves camera.position.y to
// eyeLevel + shot.yOffset and computes lookTarget from the destination
// position — not the current position — so the view is correct mid-lerp.
// ---------------------------------------------------------------------------
function animateCamera(shot) {
  camera.fov = shot.fov;
  camera.updateProjectionMatrix();
  camera.up.set(0, shot.flipUp ? -1 : 1, 0);

  // Destination camera position — Y from eyeLevel+yOffset; Z snapped to worldCentre+zSnap if set
  const destY = eyeLevel + (shot.yOffset || 0);
  const destZ = shot.zSnap != null ? worldCentre.z + shot.zSnap : worldCentre.z;
  const destPos = new THREE.Vector3(worldCentre.x, destY, destZ);

  // Compute look direction from shot yaw/pitch
  const yawRad   = THREE.MathUtils.degToRad(shot.yaw);
  const pitchRad = THREE.MathUtils.degToRad(shot.pitch);
  const dx =  Math.sin(yawRad) * Math.cos(pitchRad);
  const dy =  Math.sin(pitchRad);
  const dz = -Math.cos(yawRad) * Math.cos(pitchRad);

  // Use distance to visual ground-level centre so target lands on the campus
  const groundY = eyeLevel - 1.7;
  const visualCentre = new THREE.Vector3(worldCentre.x, groundY, worldCentre.z);
  const dist = Math.max(30, destPos.distanceTo(visualCentre));
  const lookTarget = new THREE.Vector3(
    destPos.x + dx * dist,
    destPos.y + dy * dist,
    destPos.z + dz * dist
  );

  const startPos    = camera.position.clone();
  const startTarget = controls.target.clone();
  let t = 0;
  const duration = 60; // frames

  function step() {
    t++;
    const alpha = 1 - Math.pow(1 - t / duration, 3); // ease-out cubic
    camera.position.lerpVectors(startPos, destPos, alpha);
    controls.target.lerpVectors(startTarget, lookTarget, alpha);
    controls.update();
    if (t < duration) requestAnimationFrame(step);
  }
  step();
}

// ---------------------------------------------------------------------------
// Keyboard navigation
// Arrow keys: previous / next shot
// [ / ]     : nudge camera Y by 1 unit to fine-tune eye level
// ---------------------------------------------------------------------------
window.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown')
    goToShot((currentShot + 1) % SHOTS.length);
  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp')
    goToShot((currentShot - 1 + SHOTS.length) % SHOTS.length);
  if (e.key === '[') {
    eyeLevel -= 1;
    camera.position.y -= 1;
    controls.target.y -= 1;
    controls.update();
    document.getElementById('shot-label').textContent = `eyeLevel nudged → ${eyeLevel.toFixed(1)} (use ] to go up)`;
  }
  if (e.key === ']') {
    eyeLevel += 1;
    camera.position.y += 1;
    controls.target.y += 1;
    controls.update();
    document.getElementById('shot-label').textContent = `eyeLevel nudged → ${eyeLevel.toFixed(1)} (use [ to go down)`;
  }
});

// ---------------------------------------------------------------------------
// Resize
// ---------------------------------------------------------------------------
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ---------------------------------------------------------------------------
// Animation loop
// ---------------------------------------------------------------------------
const clock = new THREE.Clock();

function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  mixers.forEach(m => m.update(delta));
  controls.update();

  // Live camera readout — press P to print coords to console and HUD
  const p = camera.position;
  const t = controls.target;
  document.getElementById('cam-debug').textContent =
    `cam(${p.x.toFixed(1)}, ${p.y.toFixed(1)}, ${p.z.toFixed(1)})  ` +
    `target(${t.x.toFixed(1)}, ${t.y.toFixed(1)}, ${t.z.toFixed(1)})`;

  spark.render(scene, camera);
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
buildNav();
animate();
