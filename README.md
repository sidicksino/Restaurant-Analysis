# Restaurant Analysis

Computer vision and analytics pipeline for restaurant CCTV footage using YOLO object detection, table occupancy tracking, and spatial analytics.

---

## COCO Dataset Classes Reference (YOLO)

Pre-trained YOLO models (such as YOLOv8 and YOLO11 trained on the standard **COCO** dataset) support **80 classes** indexed from `0` to `79`.

### Full Class List (0 – 79)

| Class ID | Class Name | Class ID | Class Name |
| :---: | :--- | :---: | :--- |
| **0** | person | **40** | wine glass |
| **1** | bicycle | **41** | cup |
| **2** | car | **42** | fork |
| **3** | motorcycle | **43** | knife |
| **4** | airplane | **44** | spoon |
| **5** | bus | **45** | bowl |
| **6** | train | **46** | banana |
| **7** | truck | **47** | apple |
| **8** | boat | **48** | sandwich |
| **9** | traffic light | **49** | orange |
| **10** | fire hydrant | **50** | broccoli |
| **11** | stop sign | **51** | carrot |
| **12** | parking meter | **52** | hot dog |
| **13** | bench | **53** | pizza |
| **14** | bird | **54** | donut |
| **15** | cat | **55** | cake |
| **16** | dog | **56** | chair |
| **17** | horse | **57** | couch |
| **18** | sheep | **58** | potted plant |
| **19** | cow | **59** | bed |
| **20** | elephant | **60** | dining table |
| **21** | bear | **61** | toilet |
| **22** | zebra | **62** | tv |
| **23** | giraffe | **63** | laptop |
| **24** | backpack | **64** | mouse |
| **25** | umbrella | **65** | remote |
| **26** | handbag | **66** | keyboard |
| **27** | tie | **67** | cell phone |
| **28** | suitcase | **68** | microwave |
| **29** | frisbee | **69** | oven |
| **30** | skis | **70** | toaster |
| **31** | snowboard | **71** | sink |
| **32** | sports ball | **72** | refrigerator |
| **33** | kite | **73** | book |
| **34** | baseball bat | **74** | clock |
| **35** | baseball glove | **75** | vase |
| **36** | skateboard | **76** | scissors |
| **37** | surfboard | **77** | teddy bear |
| **38** | tennis racket | **78** | hair drier |
| **39** | bottle | **79** | toothbrush |

---

### Key Classes for Restaurant Analytics

| Class ID | Name | Usage in Project |
| :---: | :--- | :--- |
| `0` | **person** | Customer and staff detection, occupancy counting |
| `39` | **bottle** | Table item / beverage tracking |
| `40` | **wine glass** | Dining tracking |
| `41` | **cup** | Beverage service tracking |
| `42 – 45` | **fork, knife, spoon, bowl** | Cutlery & dish tracking |
| `52 – 55` | **hot dog, pizza, donut, cake** | Food delivery / dining state |
| `56` | **chair** | Seating arrangement & availability |
| `60` | **dining table** | Table detection & zone calibration |

---

## Usage in Code

To filter detection by specific class IDs in Ultralytics YOLO, pass the `classes` parameter to the model:

```python
from ultralytics import YOLO

model = YOLO("models/yolo11l.pt")

# Detect only persons (class 0)
results = model(frame, classes=[0], conf=0.3)

# Detect only cars (class 2)
results = model(frame, classes=[2], conf=0.3)

# Detect people, chairs, and dining tables
results = model(frame, classes=[0, 56, 60], conf=0.3)
```

---

## Project Structure

- `phase_1/` - YOLO baseline scripts (full object detection, person detection, car detection).
- `phase_2/` - Table occupancy tracking and zone analytics.
- `utils/` - Calibration utilities for selecting table areas and points.
- `models/` - Local model weights directory (e.g. `yolo11l.pt`).
- `videos/` - Input CCTV videos for testing and demo inference.

---

## Environment Setup & How to Run

This project uses the virtual environment with `ultralytics`, `torch`, and `opencv-python` installed located at `/Users/sidick/Desktop/Computer-Vision-Open-cv/venv`.

### 1. Open Terminal and Navigate to Project

```bash
cd "/Users/sidick/Desktop/Restaurant Analysis"
```

### 2. Activate the Virtual Environment

```bash
source "/Users/sidick/Desktop/Computer-Vision-Open-cv/venv/bin/activate"
```
*(Your terminal prompt should now show `(venv)` at the beginning).*

### 3. Run the Scripts

- **Phase 1: Basic YOLO Detection (All COCO Objects)**
  ```bash
  python3 phase_1/01_yolo_basics.py
  ```

- **Phase 1: Person Detection Only**
  ```bash
  python3 phase_1/02_person_detection.py
  ```

- **Phase 1: Car Detection**
  ```bash
  python3 phase_1/02_car_detection.py
  ```

- **Phase 2: Restaurant Table Occupancy & Seating Analysis**
  ```bash
  python3 phase_2/02_table_occupancy.py
  ```

> Press <kbd>Q</kbd> in the display window at any time to exit the video preview.

### 4. Apple Silicon (Mac MPS) Acceleration

On Mac with Apple Silicon (M1/M2/M3/M4), YOLO runs with GPU hardware acceleration by specifying `device="mps"`:
```python
results = model(frame, device="mps", verbose=False)
```

### 5. Deactivating the Environment

When you are done working:
```bash
deactivate
```

### 6. VS Code / IDE Interpreter Configuration

To ensure your editor recognizes `ultralytics` and `cv2` without warnings:
1. Open Command Palette in VS Code (`Cmd + Shift + P`).
2. Search for **Python: Select Interpreter**.
3. Select **Enter interpreter path...** and enter:
   ```
   /Users/sidick/Desktop/Computer-Vision-Open-cv/venv/bin/python3
   ```

