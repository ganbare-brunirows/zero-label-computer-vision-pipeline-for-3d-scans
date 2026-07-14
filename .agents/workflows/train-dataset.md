---
description: End-to-end pipeline covering Houdini USD preparation, Isaac Sim synthetic data generation, YOLO training, and QA evaluation.
---

# Autonomous SDG & CV Pipeline

This workflow defines the process to go from raw 3D assets to a trained YOLO object detection model using Synthetic Data Generation.
When the user types `/train-scans <folder>`, orchestrate the R&D preproduction process strictly using `agents.md` and the corresponding skill files.

## Steps

### Step 1: Asset Preparation (Houdini)
**Actor:** @sim_engineer
1. Receive raw 3D assets.
2. Execute the Houdini preparation script via the `run-houdini-scan-prep` skill using <folder> as the argument <folder_with_objs>
3. Validate that a consolidated, optimized `.usd` file is produced.

### Step 2: Material Creation (Isaac Sim)
**Actor:** @sim_engineer
1. Take the `.usd` file and the folder from Step 1.
2. Execute the Isaac Sim script via the `isaac-sim-image-creation` skill to apply materials to the primitives.
3. Validate the materials asignation and notify the user

### Step 3: Synthetic Data Generation (Isaac Sim)
**Actor:** @sim_engineer
1. Take the `.usd` file from Step 2.
2. Execute the Isaac Sim script via the `run-isaac-sim-replicator` skill to run Isaac Replicator.
3. Validate that a diverse dataset (images + YOLO annotations) is generated in the `dataset/` directory.

### Step 4: Model Training (YOLO)
**Actor:** @ml_engineer
1. Process the raw Replicator output: Write a Python script to convert the Replicator bounding boxes into YOLO normalized format, split the images/labels into `train` and `val` directories, and generate the required `data.yaml` file.
2. Autonomously execute a local YOLOv8 training script utilizing the available NVIDIA GPU.
3. Use the `yolov8n.pt` (nano) architecture and train for exactly `25` epochs.
4. **Agentic Polling:** Use the `schedule` tool to create a recurring background task (e.g., `*/3 * * * *`) that fetches the live training status every 3 minutes and provides a real-time update to the user.
5. **Cross-Agent Communication:** Continuously send live epoch loss metrics to the `@qa` agent via the `send_message` tool during training.
6. Once training completes, save the `best.pt` model weights and metrics back to the local `models/` directory.

### Step 5: Quality Assurance & Feedback Loop
**Actor:** @qa
1. Actively monitor the live metrics received from the `@ml_engineer` during the training run. If early signs of overfitting or diverging loss are detected, immediately instruct the `@ml_engineer` to abort the training.
2. Review the final training metrics and inference results.
3. If the metrics are below acceptable thresholds (e.g., mAP < 0.8), reject the model and instruct the **@sim_engineer** to adjust Replicator parameters (e.g., more lighting variation, different camera angles) and restart from Step 3.
4. If the metrics are good, approve the model and execute final pipeline validation tests.