using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Storyboard camera for TREE — Scene 01.
///
/// HOW IT WORKS
/// ────────────
/// In Edit mode, frame shot 1B exactly as you want it (position, rotation, FOV).
/// Press Play. The script snapshots that transform as the calibration baseline.
/// Every other shot is expressed as a delta from that baseline:
///   • pitchOffset  – degrees added to X rotation (+ = look down, − = look up)
///   • yawOffset    – degrees added to Y rotation (+ = look right, − = look left)
///   • fovOffset    – degrees added to FOV
///
/// Press Left/Right arrow (or the on-screen buttons) to step through shots.
/// The transition animates smoothly via Lerp.
///
/// TUNING WORKFLOW
/// ───────────────
/// 1. In Edit mode, aim the camera at the tree courtyard for shot 1B.
/// 2. Press Play → shot 1B loads with zero offsets (your Edit-mode pose).
/// 3. Navigate to the shot you want to tune.
/// 4. Adjust pitchOffset / yawOffset / fovOffset in the Inspector (live).
/// 5. Copy the values back into the shotList entries below.
/// </summary>
[RequireComponent(typeof(Camera))]
public class StoryboardCamera : MonoBehaviour
{
    // ── Shot definition ──────────────────────────────────────────────────────

    [System.Serializable]
    public class ShotData
    {
        public string id;
        public string label;
        [Tooltip("Degrees added to baseline Y rotation. + = look right.")]
        public float yawOffset;
        [Tooltip("Degrees added to baseline X rotation. + = look down.")]
        public float pitchOffset;
        [Tooltip("Degrees added to baseline FOV.")]
        public float fovOffset;
    }

    [Header("Shots")]
    public List<ShotData> shotList = new List<ShotData>
    {
        new ShotData { id = "1A", label = "Full Campus",           yawOffset =   0f, pitchOffset =   0f, fovOffset = +15f },
        new ShotData { id = "1B", label = "Courtyard Wide",        yawOffset =   0f, pitchOffset =   0f, fovOffset =   0f },
        new ShotData { id = "1C", label = "Worm's Eye — Monolith", yawOffset =   0f, pitchOffset = -70f, fovOffset =  -5f },
        new ShotData { id = "1D", label = "Canopy Upshot",         yawOffset =   0f, pitchOffset = -82f, fovOffset =  +5f },
        new ShotData { id = "1E", label = "Root Level",            yawOffset =   0f, pitchOffset = +35f, fovOffset =  -5f },
        new ShotData { id = "1F", label = "Transition — Oblivious",yawOffset =   0f, pitchOffset =   0f, fovOffset = +10f },
    };

    [Header("Transition")]
    [Tooltip("How fast shots blend. Higher = snappier.")]
    [Range(0.5f, 20f)] public float lerpSpeed = 5f;

    [Header("Debug — live-tune the current shot")]
    [Tooltip("Adjust these at runtime to tune the selected shot, then copy values back.")]
    public float pitchOffset;
    public float yawOffset;
    public float fovOffset;

    // ── Internal state ───────────────────────────────────────────────────────

    Camera  _cam;
    int     _currentShot = 1;  // start on shot 1B (index 1)

    // Baseline captured from Edit-mode camera pose when Play is pressed.
    Vector3    _basePosition;
    Quaternion _baseRotation;
    float      _baseFov;

    // Current animated values (Euler angles for smooth wrap).
    float _curPitch;
    float _curYaw;
    float _curFov;

    // ── Unity lifecycle ───────────────────────────────────────────────────────

    void Awake()
    {
        _cam = GetComponent<Camera>();

        // Snapshot the Edit-mode pose as the calibration baseline.
        _basePosition = transform.position;
        _baseRotation = transform.rotation;
        _baseFov      = _cam.fieldOfView;

        // Extract Euler angles so we can add offsets sensibly.
        Vector3 baseEuler = _baseRotation.eulerAngles;
        _curPitch = baseEuler.x;
        _curYaw   = baseEuler.y;
        _curFov   = _baseFov;

        ApplyShot(_currentShot, snap: true);
    }

    void Update()
    {
        // Keyboard navigation.
        if (Input.GetKeyDown(KeyCode.RightArrow) || Input.GetKeyDown(KeyCode.DownArrow))
            GoToShot((_currentShot + 1) % shotList.Count);
        if (Input.GetKeyDown(KeyCode.LeftArrow) || Input.GetKeyDown(KeyCode.UpArrow))
            GoToShot((_currentShot - 1 + shotList.Count) % shotList.Count);

        // Propagate any Inspector live-tweaks to the current shot entry.
        shotList[_currentShot].pitchOffset = pitchOffset;
        shotList[_currentShot].yawOffset   = yawOffset;
        shotList[_currentShot].fovOffset   = fovOffset;

        // Smooth lerp toward target.
        ShotData s      = shotList[_currentShot];
        Vector3 baseEuler = _baseRotation.eulerAngles;

        float targetPitch = baseEuler.x + s.pitchOffset;
        float targetYaw   = baseEuler.y + s.yawOffset;
        float targetFov   = _baseFov    + s.fovOffset;

        _curPitch = Mathf.LerpAngle(_curPitch, targetPitch, Time.deltaTime * lerpSpeed);
        _curYaw   = Mathf.LerpAngle(_curYaw,   targetYaw,   Time.deltaTime * lerpSpeed);
        _curFov   = Mathf.Lerp(_curFov, targetFov, Time.deltaTime * lerpSpeed);

        transform.rotation     = Quaternion.Euler(_curPitch, _curYaw, 0f);
        transform.position     = _basePosition;
        _cam.fieldOfView       = _curFov;
    }

    // ── Public API ────────────────────────────────────────────────────────────

    public void GoToShot(int index)
    {
        _currentShot = Mathf.Clamp(index, 0, shotList.Count - 1);
        // Sync Inspector live-tune fields.
        pitchOffset = shotList[_currentShot].pitchOffset;
        yawOffset   = shotList[_currentShot].yawOffset;
        fovOffset   = shotList[_currentShot].fovOffset;
        Debug.Log($"[StoryboardCamera] Shot {shotList[_currentShot].id} — {shotList[_currentShot].label}");
    }

    void ApplyShot(int index, bool snap = false)
    {
        _currentShot = index;
        pitchOffset  = shotList[index].pitchOffset;
        yawOffset    = shotList[index].yawOffset;
        fovOffset    = shotList[index].fovOffset;

        if (snap)
        {
            ShotData s      = shotList[index];
            Vector3 baseEuler = _baseRotation.eulerAngles;
            _curPitch = baseEuler.x + s.pitchOffset;
            _curYaw   = baseEuler.y + s.yawOffset;
            _curFov   = _baseFov    + s.fovOffset;
            transform.rotation = Quaternion.Euler(_curPitch, _curYaw, 0f);
            _cam.fieldOfView   = _curFov;
        }
    }

    // ── On-screen UI ──────────────────────────────────────────────────────────

    void OnGUI()
    {
        GUIStyle label = new GUIStyle(GUI.skin.label)
        {
            fontSize  = 13,
            alignment = TextAnchor.UpperLeft,
        };
        GUIStyle btn = new GUIStyle(GUI.skin.button) { fontSize = 12 };

        // Shot label bar.
        ShotData cur = shotList[_currentShot];
        GUI.Label(new Rect(10, 10, 600, 24),
            $"Shot {cur.id} — {cur.label}   |   pitch{cur.pitchOffset:+0.0;-0.0;0}°  yaw{cur.yawOffset:+0.0;-0.0;0}°  fov{cur.fovOffset:+0.0;-0.0;0}°",
            label);

        // Prev / Next buttons.
        if (GUI.Button(new Rect(10, 38, 60, 24), "◀ Prev", btn))
            GoToShot((_currentShot - 1 + shotList.Count) % shotList.Count);
        if (GUI.Button(new Rect(76, 38, 60, 24), "Next ▶", btn))
            GoToShot((_currentShot + 1) % shotList.Count);

        // Shot selector buttons.
        float x = 150f;
        for (int i = 0; i < shotList.Count; i++)
        {
            bool active = (i == _currentShot);
            Color prev = GUI.backgroundColor;
            GUI.backgroundColor = active ? Color.yellow : Color.white;
            if (GUI.Button(new Rect(x, 38, 44, 24), shotList[i].id, btn))
                GoToShot(i);
            GUI.backgroundColor = prev;
            x += 48f;
        }

        // Live-tune reminder.
        GUI.Label(new Rect(10, 66, 700, 20),
            "Tune: adjust pitchOffset / yawOffset / fovOffset in Inspector → copy values back to shotList",
            label);
    }
}
