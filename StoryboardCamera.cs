using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// StoryboardCamera — TREE Scene 01, Gaussian Splat viewer.
///
/// SETUP
/// ─────
/// 1. In Edit mode, orbit until you see the courtyard + tree roughly centred
///    (shot 1B composition). Leave the camera there.
/// 2. Press Play. The script snapshots that Edit-mode pose as the calibration
///    baseline. Shot 1B loads with zero offsets (your Edit-mode view).
/// 3. Arrow keys / on-screen buttons to step through shots.
///
/// LIVE TUNING (per shot)
/// ──────────────────────
///   I / K   → pitch up / down  (0.5° per press)
///   J / L   → yaw  left / right
///   U / O   → FOV  decrease / increase
///   Hold Shift for 5× speed (2.5° per press)
///   Z       → print current shot offsets to Console (copy back to shotList)
///   R       → reset current shot offsets to zero
///
/// The top HUD shows absolute world rotation so you can see exactly where you
/// are in the PLY coordinate frame.
/// </summary>
[RequireComponent(typeof(Camera))]
public class StoryboardCamera : MonoBehaviour
{
    // ── Shot definition ──────────────────────────────────────────────────────

    [System.Serializable]
    public class ShotData
    {
        public string id;
        [TextArea(1,2)] public string label;
        [Tooltip("Degrees added to baseline Y rotation. + = look right.")]
        public float yawOffset;
        [Tooltip("Degrees added to baseline X rotation. + = look down, − = look up.")]
        public float pitchOffset;
        [Tooltip("Degrees added to baseline FOV.")]
        public float fovOffset;
    }

    [Header("Shots — tune pitchOffset / yawOffset / fovOffset per shot")]
    public List<ShotData> shotList = new List<ShotData>
    {
        // Start all at zero — use I/K/J/L/U/O keys to find the right view,
        // then press Z to log the values and copy them back here.
        new ShotData { id = "1A", label = "Full Campus — Entire World Revealed",
                       yawOffset = 0f, pitchOffset = 0f, fovOffset = +15f },
        new ShotData { id = "1B", label = "Courtyard Wide — Tree as Undeniable Center",
                       yawOffset = 0f, pitchOffset = 0f, fovOffset =   0f },
        new ShotData { id = "1C", label = "Worm's Eye — Monolith Reveal",
                       yawOffset = 0f, pitchOffset = 0f, fovOffset =  -5f },
        new ShotData { id = "1D", label = "Canopy Upshot — Natural Cathedral",
                       yawOffset = 0f, pitchOffset = 0f, fovOffset =  +5f },
        new ShotData { id = "1E", label = "Root Level — Nature Reclaiming Stone",
                       yawOffset = 0f, pitchOffset = 0f, fovOffset =  -5f },
        new ShotData { id = "1F", label = "Transition — Campus Full, Students Blind",
                       yawOffset = 0f, pitchOffset = 0f, fovOffset = +10f },
    };

    [Header("Transition")]
    [Range(1f, 20f)] public float lerpSpeed = 6f;

    [Header("Tuning step (° per keypress)")]
    public float tuneStep = 0.5f;  // held Shift = ×5

    // ── Internal state ───────────────────────────────────────────────────────

    Camera  _cam;
    int     _current = 1;  // start on 1B

    Vector3    _basePos;
    Quaternion _baseRot;
    float      _baseFov;

    float _curPitch, _curYaw, _curFov;

    // ── Unity lifecycle ───────────────────────────────────────────────────────

    void Awake()
    {
        _cam     = GetComponent<Camera>();
        _basePos = transform.position;
        _baseRot = transform.rotation;
        _baseFov = _cam.fieldOfView;

        Vector3 e = _baseRot.eulerAngles;
        _curPitch = e.x;
        _curYaw   = e.y;
        _curFov   = _baseFov;

        SnapToShot(_current);
    }

    void Update()
    {
        float step = tuneStep * (Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift) ? 5f : 1f);

        // ── Shot navigation ─────────────────────────────────────────────────
        if (Input.GetKeyDown(KeyCode.RightArrow) || Input.GetKeyDown(KeyCode.DownArrow))
            GoToShot((_current + 1) % shotList.Count);
        if (Input.GetKeyDown(KeyCode.LeftArrow)  || Input.GetKeyDown(KeyCode.UpArrow))
            GoToShot((_current - 1 + shotList.Count) % shotList.Count);

        // Direct shot select: 1–6 keys
        for (int i = 0; i < shotList.Count && i < 9; i++)
            if (Input.GetKeyDown(KeyCode.Alpha1 + i)) GoToShot(i);

        // ── Live tune ───────────────────────────────────────────────────────
        ShotData s = shotList[_current];

        if (Input.GetKey(KeyCode.I)) s.pitchOffset -= step;   // look up
        if (Input.GetKey(KeyCode.K)) s.pitchOffset += step;   // look down
        if (Input.GetKey(KeyCode.J)) s.yawOffset   -= step;   // yaw left
        if (Input.GetKey(KeyCode.L)) s.yawOffset   += step;   // yaw right
        if (Input.GetKey(KeyCode.U)) s.fovOffset   -= step;   // narrow
        if (Input.GetKey(KeyCode.O)) s.fovOffset   += step;   // widen

        // Print / Reset
        if (Input.GetKeyDown(KeyCode.Z)) LogCurrentShot();
        if (Input.GetKeyDown(KeyCode.R)) { s.pitchOffset = 0; s.yawOffset = 0; s.fovOffset = 0; }

        // ── Smooth lerp to target ────────────────────────────────────────────
        Vector3 be   = _baseRot.eulerAngles;
        float tPitch = be.x + s.pitchOffset;
        float tYaw   = be.y + s.yawOffset;
        float tFov   = _baseFov + s.fovOffset;

        _curPitch = Mathf.LerpAngle(_curPitch, tPitch, Time.deltaTime * lerpSpeed);
        _curYaw   = Mathf.LerpAngle(_curYaw,   tYaw,   Time.deltaTime * lerpSpeed);
        _curFov   = Mathf.Lerp(_curFov, tFov, Time.deltaTime * lerpSpeed);

        transform.SetPositionAndRotation(_basePos, Quaternion.Euler(_curPitch, _curYaw, 0f));
        _cam.fieldOfView = _curFov;
    }

    // ── API ───────────────────────────────────────────────────────────────────

    public void GoToShot(int i)
    {
        _current = Mathf.Clamp(i, 0, shotList.Count - 1);
        Debug.Log($"[StoryboardCamera] → Shot {shotList[_current].id}");
    }

    void SnapToShot(int i)
    {
        _current = i;
        ShotData s  = shotList[i];
        Vector3 be  = _baseRot.eulerAngles;
        _curPitch   = be.x + s.pitchOffset;
        _curYaw     = be.y + s.yawOffset;
        _curFov     = _baseFov + s.fovOffset;
        transform.SetPositionAndRotation(_basePos, Quaternion.Euler(_curPitch, _curYaw, 0f));
        _cam.fieldOfView = _curFov;
    }

    void LogCurrentShot()
    {
        ShotData s = shotList[_current];
        Debug.Log($"[StoryboardCamera] {s.id}  pitchOffset={s.pitchOffset:F1}  yawOffset={s.yawOffset:F1}  fovOffset={s.fovOffset:F1}" +
                  $"  |  abs rot ({_curPitch:F1}, {_curYaw:F1}, 0)  fov {_curFov:F1}");
    }

    // ── On-screen HUD ─────────────────────────────────────────────────────────

    void OnGUI()
    {
        GUIStyle row = new GUIStyle(GUI.skin.label) { fontSize = 12 };
        GUIStyle btn = new GUIStyle(GUI.skin.button) { fontSize = 11 };

        ShotData cur = shotList[_current];

        // Shot label
        GUI.Label(new Rect(8, 6, 700, 20), $"Shot {cur.id} — {cur.label}", row);

        // Absolute rotation debug (key for tuning)
        GUI.Label(new Rect(8, 24, 700, 20),
            $"abs rot ({_curPitch:F1}, {_curYaw:F1}, 0)  fov {_curFov:F1}°  |  " +
            $"offsets  pitch{cur.pitchOffset:+0.0;-0.0;+0.0}  yaw{cur.yawOffset:+0.0;-0.0;+0.0}  fov{cur.fovOffset:+0.0;-0.0;+0.0}", row);

        // Baseline reminder
        GUI.Label(new Rect(8, 42, 700, 20),
            $"eyeLevel: {_basePos}  |  baseRot: {_baseRot.eulerAngles}  baseFOV: {_baseFov}°", row);

        // Controls reminder
        GUI.Label(new Rect(8, 60, 700, 20),
            "← → shots  |  I/K: pitch  J/L: yaw  U/O: FOV  (Shift=fast)  |  Z: log  R: reset", row);

        // Prev / Next
        if (GUI.Button(new Rect(8, 80, 50, 22), "◀", btn))
            GoToShot((_current - 1 + shotList.Count) % shotList.Count);
        if (GUI.Button(new Rect(62, 80, 50, 22), "▶", btn))
            GoToShot((_current + 1) % shotList.Count);

        // Per-shot buttons
        float x = 120f;
        for (int i = 0; i < shotList.Count; i++)
        {
            Color prev = GUI.backgroundColor;
            GUI.backgroundColor = (i == _current) ? Color.yellow : Color.white;
            if (GUI.Button(new Rect(x, 80, 38, 22), shotList[i].id, btn)) GoToShot(i);
            GUI.backgroundColor = prev;
            x += 42f;
        }
    }
}
