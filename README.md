# Print Compensation

This script compensates for a print transform by applying a fixed inner-bleed crop, optional offset translation, and a rotation around the crop center.

## Usage

```powershell
python .\print_compensation.py \
  --source "C:\path\to\input.jpg" \
  --output "C:\path\to\output.png" \
  --offset_x_mm -0.225 \
  --offset_y_mm 0 \
  --bleed_mm 1.6 \
  --rotation_deg 0.35 \
  --dpi 300
```

## Parameters

- `--source`: input image path
- `--output`: output image path
- `--offset_x_mm`: horizontal offset in millimeters, converted to pixels using DPI
- `--offset_y_mm`: vertical offset in millimeters, converted to pixels using DPI
- `--bleed_mm`: bleed on each side in millimeters
- `--rotation_deg`: rotation in degrees in image coordinates. Positive values appear counterclockwise in the displayed image because Y points downward.
- `--dpi`: optional DPI override. If omitted, the script tries to infer DPI from the image size

## DPI detection

If `--dpi` is not provided, the script estimates DPI from the image size using the assumed physical print size of 69 mm x 94 mm.

Example:

```powershell
python .\print_compensation.py --source "C:\path\to\input.jpg" --output "C:\path\to\output.png" --offset_x_mm 0 --offset_y_mm 0 --bleed_mm 2.275 --rotation_deg 0
```

## Tuning the transform

- If the image looks too heavy on the left, reduce `--offset_x_mm`.
- If it looks too heavy on the right, increase `--offset_x_mm`.
- If it looks too heavy on the top, reduce `--offset_y_mm`.
- If it looks too heavy on the bottom, increase `--offset_y_mm`.
- If it needs to rotate counterclockwise, increase `--rotation_deg`.
- If it needs to rotate clockwise, decrease `--rotation_deg`.

## Notes
- Offsets are in millimeters, not pixels.
- Bleed is a per-side value in millimeters.
