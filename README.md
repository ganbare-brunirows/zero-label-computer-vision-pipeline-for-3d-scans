# Autonomous Mesh-to-Model CV Pipeline

> An end-to-end, multi-agent pipeline that converts raw 3D meshes into highly accurate computer vision models using Houdini, Isaac Sim, and YOLOv8.

This project is a fully autonomous Computer Vision pipeline designed to convert raw 3D mesh scans into production-ready object detection models. Orchestrated by a team of specialized agents, the system automatically optimizes meshes in Houdini, generates procedural training data in NVIDIA Isaac Sim, and executes the GPU training loop for YOLOv8. 

The result is a highly accurate computer vision model capable of detecting scanned meshes in the real world—achieved without drawing a single manual bounding box.

## 🧠 Multi-Agent Architecture

The pipeline is operated entirely by a team of specialized agents working in tandem:

- **`@architect` (Lead):** Orchestrates the pipeline, triggers the subagents, and handles overall workflow validation.
- **`@sim_engineer`:** Handles all 3D pipeline tasks. Uses `hython` for Houdini asset prep, and NVIDIA Isaac Sim for procedural material assignment and synthetic data generation.
- **`@ml_engineer`:** Handles the machine learning pipeline. Ingests the synthetic dataset, formats it for YOLO, and executes the GPU training loop.
- **`@qa`:** Actively monitors training loss curves to prevent overfitting and evaluates final model mAP to determine if the model passes quality thresholds.

## ⚙️ Pipeline Steps

1. **Houdini Asset Preparation:** The `@sim_engineer` targets a directory of raw `.obj` files. Using a custom `hython` script, it actively optimizes the raw meshes (topology cleanup) before merging them into an optimized `Geos.usd` file.
2. **Isaac Sim Material Assignment:** Programmatically assigns textures and semantic classes to the USD primitives.
3. **Isaac Replicator (Data Generation):** Runs domain randomization (lighting, poses, backgrounds) and outputs thousands of synthetic images with perfectly calculated YOLO bounding box annotations. *Note: Includes a custom fix utilizing `UsdLux` dome lights to override destructive default lighting.*
4. **YOLO Training:** The `@ml_engineer` formats the raw annotations to YOLO normalized format, splits into `train/val`, and runs a 25-epoch training loop using the `yolov8n.pt` (Nano) architecture.
5. **QA Evaluation:** The `@qa` agent validates the final model against strict confidence thresholds.

## 📊 Results

- Successfully generated a fully synthetic dataset of **2,500 images** entirely procedurally.
- Trained a **YOLOv8 Nano (yolov8n)** model on the dataset.
- Achieved an outstanding final **mAP50 of 0.989** on the validation set.
- The loss curves showed zero signs of overfitting, proving the viability of the domain randomization parameters.

## 🚀 Usage

To kick off the pipeline on a new folder of 3D scans, simply use the following slash command in the agent chat:

```bash
/train-dataset from [Path_to_Folder]
```

The `@architect` will then automatically spin up the subagents to handle the rest. A production-ready weights file (`best.pt`) will be generated in the `models/` directory upon completion.
