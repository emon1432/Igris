---
name: screen-perception
description: Methodology and toolchain for multi-modal screen perception, coordinate mapping, and Linux AT-SPI accessibility inspection.
---

# Screen Perception & Coordinate Mapping Skill

This skill documents methodologies for observing desktop state, identifying UI components, and mapping coordinates for accurate input delivery.

## 1. High-Speed Frame Capture
* Utilize Python `mss` to grab full-resolution desktop frames within 10-15ms across either display (`:0` or `:99`).
* Compress or downscale frames as needed for VLM spatial analysis.

## 2. Linux AT-SPI Tree Traversal
* Query the Linux `python-atspi` D-Bus interface to retrieve structural UI element hierarchies:
  - Application Window Title
  - Component Role (`PushButton`, `Entry`, `Text`, `Window`, `MenuBar`)
  - Exact Bounding Box Coordinates `(x, y, width, height)`
* Provides deterministic, pixel-perfect click centers to complement VLM spatial predictions.

## 3. Normalized Coordinate Translation
When the VLM outputs normalized coordinates in the range $[0, 1000]$, convert them to absolute screen pixels $(W \times H)$:
$$X_{target} = \frac{x_{model}}{1000} \times W, \quad Y_{target} = \frac{y_{model}}{1000} \times H$$
