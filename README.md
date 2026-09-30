# Print Compensation

This script prepares a source image for printing by cropping to the fixed inner bleed area, shifting the artwork in millimeters, and rotating it around the center of the crop.

The result is intended to be placed into PrintFab Composer as the final artwork for a single-card print job.

## Quick start

Use the script like this:

```powershell
python .\print_compensation.py \
  --source "C:\path\to\input.jpg" \
  --output "C:\path\to\output.png" \
  --offset_x -0.225 \
  --offset_y 0 \
  --bleed_mm 1.6 \
  --rotation 0.35 \
  --dpi 1200
```

This is the common starting point for the current workflow.

## Parameter reference

- `--source`: input image path
- `--output`: output image path
- `--offset_x`: horizontal shift in millimeters. Negative moves the image left; positive moves it right.
- `--offset_y`: vertical shift in millimeters. Negative moves the image up; positive moves it down.
- `--bleed_mm`: bleed on each side in millimeters
- `--rotation`: rotation in degrees in image coordinates. Positive values appear counterclockwise in the displayed image because Y points downward.
- `--dpi`: optional DPI override. If omitted, the script tries to infer DPI from the image size.

## DPI detection

If `--dpi` is not provided, the script estimates DPI from the image size using the assumed physical print size of 69 mm x 94 mm.

## Tuning the transform

Start with the defaults above, then adjust from there:

- If the image looks too heavy on the left, reduce `--offset_x`.
- If it looks too heavy on the right, increase `--offset_x`.
- If it looks too heavy on the top, reduce `--offset_y`.
- If it looks too heavy on the bottom, increase `--offset_y`.
- If it needs to rotate counterclockwise, increase `--rotation`.
- If it needs to rotate clockwise, decrease `--rotation`.

## PrintFab workflow

Use the compensated output in the following way:

1. Create a custom media page

   In PrintFab, open the page-size editor and add a custom media size for the card format. The example setup uses a 63x88 borderless page.

   ![PrintFab media size setup](media-size.png)

2. Configure the print profile

   Select the 63x88 borderless profile and set the printer profile to the correct card settings for the job.

   ![PrintFab print profile setup](print-profile.png)

3. Add the image and prepare it for printing

   In PrintFab Composer, click Add Image / PDF, drag the compensated image into the card frame, and press Fill Page. This automatically centers the artwork and fills the page without additional manual scaling.

   ![PrintFab composer image placement](image-prep.png)

   In other words, the script creates the final artwork layer, and PrintFab is then used only to place it on the correct card-sized borderless page and print it.

## Notes
- Offsets are in millimeters, not pixels.
- Bleed is a per-side value in millimeters.
