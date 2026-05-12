import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';

document.getElementById('load-status').textContent = 'v10 — panorama viewer';

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
// Panorama URLs
// DEFAULT_PANO_URL: equirectangular JPG used by shots without a panoUrl.
// Per-shot panorama: add `panoUrl: '...'` to any SHOTS entry to load a
// different panorama for that shot (e.g. closer to the tree, or aerial).
// ---------------------------------------------------------------------------
const DEFAULT_PANO_URL = 'https://cdn.marble.worldlabs.ai/fcf05383-91d7-4880-8186-98899075f4a1/84a8ada1-29fe-482e-8f97-bbde6cda991c_panos/rgb_0.png';

// ---------------------------------------------------------------------------
// Scene 01 shots
//
// yaw:   horizontal look direction in degrees (0 = panorama centre, +ve = right)
// pitch: vertical tilt in degrees (+ve = look up, -ve = look down)
// fov:   vertical field of view in degrees
// ---------------------------------------------------------------------------
const SHOTS = [
  {
    id: '1A', label: 'Full Campus — The Entire World Revealed',
    who: 'None', where: 'Full campus view', when: 'Early morning',
    yaw: 35, pitch: -5, fov: 90,
    characters: [],
  },
  {
    id: '1B', label: 'Courtyard Wide — Tree as Undeniable Center',
    who: 'Zara', where: 'Central courtyard', when: 'Early morning',
    yaw: 35, pitch: 0, fov: 75,
    characters: [
      { role: 'zara', x: 0, z: -20, y: -10, rotY: 0.0 },
    ],
  },
  {
    id: '1C', label: "Worm's Eye — The Monolith Reveal",
    who: 'The Tree', where: 'Under the tree', when: 'Early morning',
    yaw: 35, pitch: 60, fov: 70,
    characters: [],
  },
  {
    id: '1D', label: 'Canopy Upshot — Natural Cathedral',
    who: 'The Tree', where: 'Under the tree', when: 'Mid-morning',
    yaw: 35, pitch: 82, fov: 85,
    characters: [],
  },
  {
    id: '1E', label: 'Root Level — Nature Reclaiming Stone',
    who: 'The Tree', where: 'Courtyard, ground level', when: 'Early morning',
    yaw: 35, pitch: -40, fov: 70,
    characters: [],
  },
  {
    id: '1F', label: 'Transition — Campus Full, Students Blind',
    who: 'Zara + Students', where: 'Central courtyard', when: 'Mid-morning',
    yaw: 35, pitch: -5, fov: 100,
    characters: [
      { role: 'zara',    x:  0,   z: -20, y: -10, rotY:  0.0 },
      { role: 'student', x: -3,   z: -25, y: -11, rotY:  0.3 },
      { role: 'student', x:  2,   z: -20, y: -10, rotY: -0.2 },
      { role: 'student', x:  4,   z: -30, y: -12, rotY:  0.5 },
    ],
  },
];

// ---------------------------------------------------------------------------
// Character placeholder colours
// ---------------------------------------------------------------------------
const CHAR_COLORS = {
  zara:      0xe8956d,  // warm terracotta — Zara stands out
  student:   0x4a6fa5,  // muted blue — anonymous crowd
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

// Camera sits at origin and rotates — panorama wraps around it as background.
const camera = new THREE.PerspectiveCamera(85, window.innerWidth / window.innerHeight, 0.01, 1000);
camera.position.set(0, 0, 0);

scene.add(new THREE.AmbientLight(0xfff8e8, 1.4));
const sun = new THREE.DirectionalLight(0xfff5d0, 2.0);
sun.position.set(2, 8, 3);
scene.add(sun);

// ---------------------------------------------------------------------------
// Look direction state
// lon: horizontal angle in degrees (+ve = look right)
// lat: vertical angle in degrees   (+ve = look up)
// ---------------------------------------------------------------------------
let lon = 0, lat = 0;
let targetLon = 0, targetLat = 0, targetFov = 85;

function applyLook() {
  const latRad = THREE.MathUtils.degToRad(Math.max(-85, Math.min(85, lat)));
  const lonRad = THREE.MathUtils.degToRad(lon);
  camera.rotation.set(-latRad, -lonRad, 0, 'YXZ');
}

// ---------------------------------------------------------------------------
// Pointer drag — rotate view
// ---------------------------------------------------------------------------
let isDragging = false, prevX = 0, prevY = 0;

renderer.domElement.style.touchAction = 'none';

renderer.domElement.addEventListener('pointerdown', (e) => {
  isDragging = true;
  prevX = e.clientX;
  prevY = e.clientY;
  renderer.domElement.setPointerCapture(e.pointerId);
  renderer.domElement.style.cursor = 'grabbing';
});

renderer.domElement.addEventListener('pointermove', (e) => {
  if (!isDragging) return;
  lon  -= (e.clientX - prevX) * 0.15;
  lat  += (e.clientY - prevY) * 0.15;
  lat   = Math.max(-85, Math.min(85, lat));
  targetLon = lon;
  targetLat = lat;
  prevX = e.clientX;
  prevY = e.clientY;
});

renderer.domElement.addEventListener('pointerup', () => {
  isDragging = false;
  renderer.domElement.style.cursor = 'grab';
});

renderer.domElement.style.cursor = 'grab';

// Scroll wheel / pinch → FOV zoom
renderer.domElement.addEventListener('wheel', (e) => {
  e.preventDefault();
  camera.fov = Math.max(20, Math.min(120, camera.fov + e.deltaY * 0.05));
  camera.updateProjectionMatrix();
  targetFov = camera.fov;
}, { passive: false });

// ---------------------------------------------------------------------------
// Panorama loading
// ---------------------------------------------------------------------------
const loadBar  = document.getElementById('load-bar');
const loading  = document.getElementById('loading');
const loadSub  = document.getElementById('load-status');

let currentPanoUrl  = null;
let currentBgTex    = null;

async function loadPanorama(url) {
  loading.style.display    = 'flex';
  loading.style.opacity    = '1';
  loading.style.transition = '';
  loadBar.style.width      = '0%';
  loadSub.textContent      = 'Connecting…';

  const timeout = setTimeout(() => {
    showError('Timed out after 30 s.<br>Try a hard-refresh (Ctrl+Shift+R / Cmd+Shift+R).');
  }, 30000);

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const total  = parseInt(response.headers.get('content-length') || '0');
    const reader = response.body.getReader();
    const chunks = [];
    let received = 0;

    loadSub.textContent = 'Downloading panorama…';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      received += value.length;
      const pct = total
        ? Math.round(received / total * 85)
        : Math.min(85, Math.round(received / 500000 * 30));
      loadBar.style.width = pct + '%';
      loadSub.textContent = `Downloading… ${(received / 1e6).toFixed(1)} MB`;
    }

    loadSub.textContent = 'Decoding image…';
    loadBar.style.width = '90%';

    const blob    = new Blob(chunks);
    const blobUrl = URL.createObjectURL(blob);

    await new Promise((resolve, reject) => {
      new THREE.TextureLoader().load(blobUrl, (tex) => {
        tex.mapping     = THREE.EquirectangularReflectionMapping;
        tex.colorSpace  = THREE.SRGBColorSpace;
        if (currentBgTex) currentBgTex.dispose();
        currentBgTex    = tex;
        scene.background = tex;
        URL.revokeObjectURL(blobUrl);
        currentPanoUrl  = url;
        resolve();
      }, undefined, reject);
    });

    loadBar.style.width = '100%';
    clearTimeout(timeout);

    setTimeout(() => {
      loading.style.opacity    = '0';
      loading.style.transition = 'opacity 0.5s';
      setTimeout(() => { loading.style.display = 'none'; }, 500);
    }, 300);

  } catch (err) {
    clearTimeout(timeout);
    showError(`Failed to load panorama:<br>${err.message}`);
  }
}

// ---------------------------------------------------------------------------
// Characters
// ---------------------------------------------------------------------------
const gltfLoader = new GLTFLoader();
const fbxLoader  = new FBXLoader();
const characterMeshes = {};
const mixers = [];

// Pre-loaded character pool: { role → [Object3D, ...] }
// Each entry is a fully-loaded, independently-animated Object3D ready to
// be added to the scene. We preload as many copies as the busiest shot needs.
const charPool = {};

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

// Characters loaded at runtime from GitHub CDN — keeps build under Cloudflare's 25 MB limit.
const GITHUB_RAW = 'https://raw.githubusercontent.com/12turtleships/3dgs-storyboard-automation/master/characters';
const charPaths = {
  zara:      { path: `${GITHUB_RAW}/student_texting_walk.fbx`, type: 'fbx' },
  student:   { path: `${GITHUB_RAW}/student_texting_walk.fbx`, type: 'fbx' },
  professor: { path: `${GITHUB_RAW}/professor_idle.glb`,       type: 'glb' },
};

// Count the most instances of each role needed in any single shot.
const maxNeeded = {};
SHOTS.forEach(shot => {
  const counts = {};
  shot.characters.forEach(c => { counts[c.role] = (counts[c.role] || 0) + 1; });
  Object.entries(counts).forEach(([role, n]) => {
    maxNeeded[role] = Math.max(maxNeeded[role] || 0, n);
  });
});

function loadOneInstance(role, path, type, phaseOffset) {
  const loader = type === 'fbx' ? fbxLoader : gltfLoader;
  loader.load(path, (result) => {
    const obj   = type === 'fbx' ? result : result.scene;
    const clips = result.animations || [];
    // Mixamo FBX is in centimetres; FBXLoader does not auto-scale → 0.01 cm→m.
    if (type === 'fbx') obj.scale.setScalar(0.01);

    obj.userData.dbg = `clips:${clips.length}`;

    if (clips.length > 0) {
      obj.userData.dbg += ` tracks:${clips[0].tracks.length} dur:${clips[0].duration.toFixed(1)}s`;
      const mixer = new THREE.AnimationMixer(obj);
      const action = mixer.clipAction(clips[0]);
      action.play();
      mixer.update(0.001); // force first pose so bind-pose isn't shown
      if (phaseOffset > 0) mixer.setTime(phaseOffset);
      mixers.push(mixer);
      obj.userData.mixer = mixer;
    }

    charPool[role].push(obj);
    placeCharacters(SHOTS[currentShot]);
  }, undefined, () => {
    charPool[role].push(null);
    placeCharacters(SHOTS[currentShot]);
  });
}

// Kick off pre-loads for every role that appears in any shot.
Object.entries(maxNeeded).forEach(([role, n]) => {
  charPool[role] = [];
  const { path, type } = charPaths[role] || charPaths.student;
  for (let i = 0; i < n; i++) {
    loadOneInstance(role, path, type, i * 0.4);
  }
});

function placeCharacters(shot) {
  // Remove all current character meshes.
  Object.values(characterMeshes).forEach(m => scene.remove(m));
  Object.keys(characterMeshes).forEach(k => delete characterMeshes[k]);

  // Track how many of each role we've already assigned this shot.
  const usedCount = {};

  shot.characters.forEach((c, i) => {
    const idx  = usedCount[c.role] = (usedCount[c.role] || 0);
    usedCount[c.role]++;
    const pool = charPool[c.role] || [];
    const mesh = (pool[idx] != null) ? pool[idx] : makeCharacterPlaceholder(c.role);

    mesh.position.set(c.x || 0, c.y != null ? c.y : -1.7, c.z || -5);
    mesh.rotation.y = c.rotY || 0;
    scene.add(mesh);
    characterMeshes[`char_${i}`] = mesh;
  });
}

// ---------------------------------------------------------------------------
// Shot navigation
// ---------------------------------------------------------------------------
let currentShot = 0;

function buildNav() {
  const nav    = document.getElementById('nav');
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

function animateToShot(shot) {
  // Shortest-path yaw wrap: avoid spinning the long way around 360°.
  const delta = ((shot.yaw - targetLon) % 360 + 540) % 360 - 180;
  targetLon = targetLon + delta;
  targetLat = shot.pitch;
  targetFov = shot.fov;
}

function goToShot(index) {
  currentShot = index;
  const shot  = SHOTS[index];
  const url   = shot.panoUrl || DEFAULT_PANO_URL;

  document.getElementById('shot-label').textContent = `Shot ${shot.id} — ${shot.label}`;
  updateCharInfo(shot);
  buildNav();
  placeCharacters(shot);

  if (url !== currentPanoUrl) {
    loadPanorama(url).then(() => animateToShot(shot));
    return;
  }
  animateToShot(shot);
}

function updateCharInfo(shot) {
  const info = document.getElementById('char-info');
  if (!shot.who || shot.who === 'None') { info.style.display = 'none'; return; }
  info.style.display = 'block';
  document.getElementById('ci-who').textContent   = `WHO: ${shot.who}`;
  document.getElementById('ci-where').textContent = `WHERE: ${shot.where}`;
  document.getElementById('ci-when').textContent  = `WHEN: ${shot.when}`;
}

// ---------------------------------------------------------------------------
// Character nudge controls
// Select a character with Tab, then nudge with:
//   W/S  → move forward/back (z)
//   A/D  → move left/right (x)
//   Q/E  → move up/down (y)
// Debug HUD shows the current position so you can copy values back to SHOTS.
// ---------------------------------------------------------------------------
let selectedChar = -1;  // index into shot.characters (-1 = none)

function selectChar(idx) {
  const shot = SHOTS[currentShot];
  // Clear highlight on previous
  if (selectedChar >= 0) {
    const prev = characterMeshes[`char_${selectedChar}`];
    if (prev) prev.traverse(o => { if (o.isMesh) o.material.emissive?.set(0x000000); });
  }
  selectedChar = (shot.characters.length === 0) ? -1 : idx % shot.characters.length;
  // Highlight selected
  if (selectedChar >= 0) {
    const cur = characterMeshes[`char_${selectedChar}`];
    if (cur) cur.traverse(o => { if (o.isMesh && o.material.emissive) o.material.emissive.set(0x442200); });
  }
}

function nudgeChar(dx, dy, dz) {
  if (selectedChar < 0) return;
  const shot = SHOTS[currentShot];
  const c    = shot.characters[selectedChar];
  c.x = (c.x || 0) + dx;
  c.y = (c.y != null ? c.y : -1.7) + dy;
  c.z = (c.z || 0) + dz;
  const mesh = characterMeshes[`char_${selectedChar}`];
  if (mesh) mesh.position.set(c.x, c.y, c.z);
}

// ---------------------------------------------------------------------------
// Keyboard shortcuts
// ---------------------------------------------------------------------------
window.addEventListener('keydown', (e) => {
  // Shot navigation — only when no character selected or modifier held
  if (!e.shiftKey && selectedChar < 0) {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown')
      goToShot((currentShot + 1) % SHOTS.length);
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp')
      goToShot((currentShot - 1 + SHOTS.length) % SHOTS.length);
  }
  // Fine-tune pitch of current shot with [ / ]
  if (e.key === '[') { targetLat -= 2; lat = targetLat; }
  if (e.key === ']') { targetLat += 2; lat = targetLat; }

  // Character selection
  if (e.key === 'Tab') { e.preventDefault(); selectChar(selectedChar + 1); }
  if (e.key === 'Escape') selectChar(-1);

  // Character nudge (1 m steps; hold Shift for 0.25 m)
  const step = e.shiftKey ? 0.25 : 1;
  if (e.key === 'w' || e.key === 'W') nudgeChar(0, 0, -step);
  if (e.key === 's' || e.key === 'S') nudgeChar(0, 0,  step);
  if (e.key === 'a' || e.key === 'A') nudgeChar(-step, 0, 0);
  if (e.key === 'd' || e.key === 'D') nudgeChar( step, 0, 0);
  if (e.key === 'q' || e.key === 'Q') nudgeChar(0,  step, 0);
  if (e.key === 'e' || e.key === 'E') nudgeChar(0, -step, 0);
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

  if (!isDragging) {
    const ease = 0.07;
    lon += (targetLon - lon) * ease;
    lat += (targetLat - lat) * ease;
    camera.fov += (targetFov - camera.fov) * ease;
    camera.updateProjectionMatrix();
  }

  applyLook();

  const shot = SHOTS[currentShot];
  // Pool debug: show how many instances loaded and their animation state.
  const poolInfo = Object.entries(charPool)
    .filter(([, pool]) => pool.length > 0)
    .map(([role, pool]) => {
      const info = pool.map(o => o ? (o.userData.dbg || 'ok') : 'err').join('|');
      return `${role}[${info}]`;
    }).join('  ');
  let dbg = `lon(${lon.toFixed(1)}°) lat(${lat.toFixed(1)}°) fov(${camera.fov.toFixed(0)}°)  ${poolInfo}`;
  if (selectedChar >= 0 && shot.characters[selectedChar]) {
    const c = shot.characters[selectedChar];
    dbg += `   [char ${selectedChar}] x(${(c.x||0).toFixed(2)}) y(${(c.y!=null?c.y:-1.7).toFixed(2)}) z(${(c.z||0).toFixed(2)})`;
    dbg += '  WASD=x/z  QE=y  Shift=fine';
  } else if (shot.characters.length > 0) {
    dbg += '   Tab=select character';
  }
  document.getElementById('cam-debug').textContent = dbg;

  renderer.render(scene, camera);
}

// ---------------------------------------------------------------------------
// Init — load panorama then start
// ---------------------------------------------------------------------------
const shot0 = SHOTS[currentShot];
lon = targetLon = shot0.yaw;
lat = targetLat = shot0.pitch;
camera.fov = targetFov = shot0.fov;
camera.updateProjectionMatrix();

loadPanorama(DEFAULT_PANO_URL).then(() => {
  buildNav();
  animate();
  updateCharInfo(shot0);
  placeCharacters(shot0);
  document.getElementById('shot-label').textContent = `Shot ${shot0.id} — ${shot0.label}`;
});
