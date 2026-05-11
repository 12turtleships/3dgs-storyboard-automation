import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';
import { SkeletonUtils } from 'three/examples/jsm/utils/SkeletonUtils.js';

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
      { role: 'zara', x: 0.5, z: -8, rotY: 0.0 },
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
      { role: 'zara',    x:  0,   z: -7,  rotY:  0.0 },
      { role: 'student', x: -2.5, z: -9,  rotY:  0.3 },
      { role: 'student', x:  1.5, z: -7,  rotY: -0.2 },
      { role: 'student', x:  3,   z: -11, rotY:  0.5 },
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
// charLibrary stores { source: Object3D, clips: AnimationClip[] } per role.
// source is never added to the scene — only SkeletonUtils.clone()d copies are.
const charLibrary = {};

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
  if (role === 'zara') {
    // Head tilted back — looking up at the tree.
    head.rotation.x = -0.5;
  }
  return group;
}

function loadCharacter(role, path, type) {
  const loader = type === 'fbx' ? fbxLoader : gltfLoader;
  loader.load(path, (result) => {
    const source = type === 'fbx' ? result : result.scene;
    const clips  = result.animations || [];
    // Mixamo FBX is in centimetres; FBXLoader does not auto-scale → 0.01 cm→m.
    if (type === 'fbx') source.scale.setScalar(0.01);
    charLibrary[role] = { source, clips };
    // Re-place characters for the active shot now that the model is ready.
    placeCharacters(SHOTS[currentShot]);
  }, undefined, () => {
    // Fall back to placeholder — mark role as failed so placeCharacters uses it.
    charLibrary[role] = null;
    placeCharacters(SHOTS[currentShot]);
  });
}

// Characters loaded at runtime from GitHub CDN — keeps build under Cloudflare's 25 MB limit.
const GITHUB_RAW = 'https://raw.githubusercontent.com/12turtleships/3dgs-storyboard-automation/master/characters';
const charPaths = {
  zara:      { path: `${GITHUB_RAW}/student_texting_walk.fbx`, type: 'fbx' },
  student:   { path: `${GITHUB_RAW}/student_texting_walk.fbx`, type: 'fbx' },
  professor: { path: `${GITHUB_RAW}/professor_idle.glb`,       type: 'glb' },
};
// Deduplicate: only load each unique path once; share the same library entry.
const loaded = new Set();
Object.entries(charPaths).forEach(([role, { path, type }]) => {
  // Find if another role already uses the same path.
  const sharedRole = Object.keys(charPaths).find(
    r => r !== role && charPaths[r].path === path
  );
  if (sharedRole && loaded.has(path)) {
    // Mirror the library reference once the shared role finishes loading.
    const mirror = () => {
      if (charLibrary[sharedRole] !== undefined) {
        charLibrary[role] = charLibrary[sharedRole];
      } else {
        setTimeout(mirror, 100);
      }
    };
    mirror();
  } else {
    loaded.add(path);
    loadCharacter(role, path, type);
  }
});

function placeCharacters(shot) {
  // Remove existing character meshes from scene.
  Object.values(characterMeshes).forEach(m => {
    scene.remove(m);
    // Dispose mixer for this mesh if one was created.
    m.userData.mixer && m.userData.mixer.stopAllAction();
  });
  Object.keys(characterMeshes).forEach(k => delete characterMeshes[k]);

  shot.characters.forEach((c, i) => {
    const lib = charLibrary[c.role];
    let mesh;
    if (lib && lib.source) {
      // SkeletonUtils.clone properly rebinds skinned mesh bones to the new skeleton.
      mesh = SkeletonUtils.clone(lib.source);
      if (lib.clips.length > 0) {
        const mixer = new THREE.AnimationMixer(mesh);
        mixer.clipAction(lib.clips[0]).play();
        mixers.push(mixer);
        mesh.userData.mixer = mixer;
      }
    } else {
      mesh = makeCharacterPlaceholder(c.role);
    }
    // Camera is at eye level (~1.7 m above ground); place feet at y = -1.7.
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
// Keyboard shortcuts
// ---------------------------------------------------------------------------
window.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown')
    goToShot((currentShot + 1) % SHOTS.length);
  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp')
    goToShot((currentShot - 1 + SHOTS.length) % SHOTS.length);
  // Fine-tune pitch of current shot with [ / ]
  if (e.key === '[') { targetLat -= 2; lat = targetLat; }
  if (e.key === ']') { targetLat += 2; lat = targetLat; }
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

  document.getElementById('cam-debug').textContent =
    `lon(${lon.toFixed(1)}°)  lat(${lat.toFixed(1)}°)  fov(${camera.fov.toFixed(0)}°)`;

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
