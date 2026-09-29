import argparse
import cv2
import numpy as np


MM_PER_INCH = 25.4
DEFAULT_EXPECTED_WIDTH_MM = 69.0
DEFAULT_EXPECTED_HEIGHT_MM = 94.0


def mm_to_pixels(mm_value, dpi):
    """Convert a physical dimension in millimeters to pixels.

    Negative values are valid for offsets (e.g. left/up shifts), while bleed is
    validated separately as a non-negative quantity.
    """
    if dpi <= 0:
        raise ValueError("DPI must be positive.")

    return int(round(mm_value * dpi / MM_PER_INCH))


def read_dpi_from_image(
    path,
    expected_width_mm=DEFAULT_EXPECTED_WIDTH_MM,
    expected_height_mm=DEFAULT_EXPECTED_HEIGHT_MM,
):
    """Estimate DPI from the image pixel size and known physical size."""
    try:
        from PIL import Image

        with Image.open(path) as image:
            width_px, height_px = image.size

            if width_px <= 0 or height_px <= 0:
                return None

            width_dpi = (width_px / expected_width_mm) * MM_PER_INCH
            height_dpi = (height_px / expected_height_mm) * MM_PER_INCH

            dpi = 0.5 * (width_dpi + height_dpi)

            if dpi <= 0:
                return None

            return dpi
    except Exception:
        return None


def load_image(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)

    if image is None:
        raise RuntimeError(f"Could not read image: {path}")

    return image


def make_similarity_transform(offset_x, offset_y, rotation_deg, center_x=0.0, center_y=0.0):
    """Build a similarity transform that rotates about a center point.

    The transform is defined in image coordinates where +y points downward.
    In this coordinate system, positive rotation values appear counterclockwise
    in the displayed image. Negative values appear clockwise.
    """
    theta = np.deg2rad(rotation_deg)
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)

    tx = center_x + offset_x - (cos_theta * center_x + sin_theta * center_y)
    ty = center_y + offset_y + (sin_theta * center_x - cos_theta * center_y)

    return np.array(
        [
            [cos_theta, sin_theta, float(tx)],
            [-sin_theta, cos_theta, float(ty)],
        ],
        dtype=np.float64,
    )


def make_compensated_image(source, transform, x, y, width, height):
    """Apply the inverse transform to sample the original image into the print crop."""
    inverse = cv2.invertAffineTransform(transform)

    u, v = np.meshgrid(
        np.arange(int(round(width)), dtype=np.float32),
        np.arange(int(round(height)), dtype=np.float32),
        indexing="xy",
    )

    printed = np.stack([x + u, y + v], axis=-1).reshape(-1, 2)
    source_points = cv2.transform(
        printed.reshape(-1, 1, 2),
        inverse,
    ).reshape(int(round(height)), int(round(width)), 2)

    map_x = source_points[:, :, 0].astype(np.float32)
    map_y = source_points[:, :, 1].astype(np.float32)

    return cv2.remap(
        source,
        map_x,
        map_y,
        interpolation=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )


def compute_fixed_crop_size(source_shape, bleed_pixels):
    """Return the fixed output region for the image after removing bleed.

    We crop the inner bleed rectangle, not the source origin, so the output is
    centered on the actual content. Rotation and translation are applied inside
    this fixed canvas and must not change its dimensions.
    """
    inner_width = source_shape[1] - 2 * bleed_pixels
    inner_height = source_shape[0] - 2 * bleed_pixels

    if inner_width <= 0 or inner_height <= 0:
        raise ValueError("Bleed is too large for the source image dimensions.")

    x = float(bleed_pixels)
    y = float(bleed_pixels)
    return x, y, float(inner_width), float(inner_height)


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Generate a compensated image for print output using a fixed inner-bleed crop, "
            "a center-based rotation, and millimeter-based offsets."
        )
    )

    parser.add_argument("--source", required=True, help="Path to the source image.")
    parser.add_argument("--output", required=True, help="Output path for the compensated image.")

    parser.add_argument(
        "--offset_x_mm",
        "--offset_x",
        "--offset-x-mm",
        "--offset-x",
        dest="offset_x_mm",
        type=float,
        required=True,
        help="Horizontal translation in millimeters; converted to pixels using the selected or detected DPI.",
    )
    parser.add_argument(
        "--offset_y_mm",
        "--offset_y",
        "--offset-y-mm",
        "--offset-y",
        dest="offset_y_mm",
        type=float,
        required=True,
        help="Vertical translation in millimeters; converted to pixels using the selected or detected DPI.",
    )
    parser.add_argument(
        "--bleed_mm",
        "--bleed-mm",
        dest="bleed_mm",
        type=float,
        required=True,
        help="Bleed on each side in millimeters.",
    )
    parser.add_argument(
        "--rotation_deg",
        "--rotation",
        "--rotation-deg",
        dest="rotation_deg",
        type=float,
        default=0.0,
        help="Rotation in degrees, clockwise in image coordinates. Positive values rotate clockwise.",
    )
    parser.add_argument(
        "--dpi",
        type=float,
        help="Optional DPI used for mm-to-pixel conversion. If omitted, the script infers DPI from the image size.",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.bleed_mm < 0:
        parser.error("--bleed-mm cannot be negative.")

    source = load_image(args.source)

    dpi = args.dpi
    if dpi is None:
        dpi = read_dpi_from_image(
            args.source,
            expected_width_mm=DEFAULT_EXPECTED_WIDTH_MM,
            expected_height_mm=DEFAULT_EXPECTED_HEIGHT_MM,
        )
        if dpi is not None:
            print(f"Detected DPI from source image: {dpi:.2f}")

    if dpi is None:
        parser.error(
            "Could not determine DPI from the source image. Provide --dpi or embed DPI metadata in the image."
        )

    if dpi <= 0:
        parser.error("--dpi must be greater than zero.")

    bleed_pixels = mm_to_pixels(args.bleed_mm, dpi)

    if bleed_pixels <= 0:
        raise ValueError("Computed bleed in pixels must be positive.")

    if bleed_pixels * 2 >= source.shape[1] or bleed_pixels * 2 >= source.shape[0]:
        raise ValueError("Bleed is too large for the source image dimensions.")

    offset_x_pixels = mm_to_pixels(args.offset_x_mm, dpi)
    offset_y_pixels = mm_to_pixels(args.offset_y_mm, dpi)

    x, y, width, height = compute_fixed_crop_size(source.shape, bleed_pixels)
    center_x = x + (width - 1.0) / 2.0
    center_y = y + (height - 1.0) / 2.0

    transform = make_similarity_transform(
        offset_x_pixels,
        offset_y_pixels,
        args.rotation_deg,
        center_x=center_x,
        center_y=center_y,
    )

    result = make_compensated_image(source, transform, x, y, width, height)

    if not cv2.imwrite(args.output, result):
        raise RuntimeError(f"Could not write {args.output}")

    print()
    print("COMPENSATED IMAGE")
    print("-----------------")
    print(f"Source region: ({x:.3f}, {y:.3f}) -> ({x + width:.3f}, {y + height:.3f})")
    print(f"Output size: {result.shape[1]} x {result.shape[0]}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
