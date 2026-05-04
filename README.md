# 3dgs-storyboard-automation

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![World Labs](https://img.shields.io/badge/World_Labs-API-orange)
![Veo 3.1](https://img.shields.io/badge/Veo_3.1-Supported-green)
![3DGS](https://img.shields.io/badge/3DGS-SparkJS-lightgrey)

> An automated machine learning pipeline that converts 2D cinematic storyboards into navigable 3D Gaussian Splat environments using Large World Models.

## Overview
This repository provides a "3D-as-Code" orchestration framework designed for Virtual Production and VFX Pre-visualization (Pre-vis). By leveraging zero-shot spatial intelligence via Large World Models (LWMs), this pipeline automates the generation of persistent, physically plausible 3D environments (`.spz` Gaussian Splats and `.glb` collision meshes) directly from cinematic text prompts and character reference imagery.

## The Business Case (Why this exists)
Traditional 3D environment generation for LED Volumes (e.g., StageCraft) requires weeks of manual asset creation in Unreal Engine. This pipeline shifts "Dark Work" to GPU inference, allowing directors to fly through spatial representations of their storyboards within minutes.

| Metric | Traditional VFX Pre-vis | 3DGS Automation Pipeline |
| :--- | :--- | :--- |
| **Labor Cost** | $75–$150/hr (Mid-level artist) | ~$0.18–$1.26 per scene (API Compute) |
| **Turnaround** | 10–20 hours per shot | 2–5 minutes per shot |
| **Spatial Output** | Static renders or heavy meshes | Real-time streamable `.spz` & `.glb` |

## System Architecture
The pipeline is divided into three core micro-services:
1. **Conditioning Engine:** Utilizes Google Veo 3.1 (C-S-A-C-S prompting formula) to lock character consistency (e.g., generating reference states for protagonist continuity).
2. **Spatial Generation Engine:** Interfaces with the World Labs API (`marble-1.0-draft` and `marble-1.1`) to extrude 2D intent into 360-degree panoramas, and subsequently into 3D Gaussian Splats.
3. **Web Renderer:** A lightweight frontend implementation utilizing `SparkJS` to render the outputs in real-time WebGL.

## Case Study: *The Tree of Knowledge*
This pipeline was validated using a 19-scene sci-fi cinematic storyboard detailing the intersection of brutalist architecture and solarpunk themes.

* **Input:** Text prompts detailing cinematography, subject, and lighting (e.g., *"Low angle wide shot, worm's-eye view looking straight up the trunk of a massive ancient Sequoia tree..."*)
* **Output Assets Generated:**
  * Navigable 3DGS environments (`.spz`) for 19 unique scenes.
  * Extracted collision meshes (`.glb`) ready for rigid-body physics simulation.

## Installation & Setup

**1. Clone the repository**
```bash
git clone https://github.com/12turtleships/3dgs-storyboard-automation.git
cd 3dgs-storyboard-automation
```

**2. Install dependencies**
```bash
pip install requests python-dotenv
```

**3. Configure your API key**
```bash
cp .env.example .env
# Edit .env and set your World Labs API key:
# WLT_API_KEY=your_worldlabs_api_key_here
```

**4. Run a scene generation**
```bash
python generate_tree_scene_01.py
```

The script will poll for completion and print asset download links (`.spz` splats, `.glb` mesh, web viewer URL) once generation is done (~2–5 minutes).
