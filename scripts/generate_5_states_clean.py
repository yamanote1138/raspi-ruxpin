#!/usr/bin/env python3
"""
Generate 5 discrete mouth states with proper alpha compositing.

Only blend the visible pixels, preserve transparency in background.
"""

from pathlib import Path
from PIL import Image
import numpy as np


def blend_with_alpha_preservation(img1: Image.Image, img2: Image.Image, alpha: float) -> Image.Image:
    """Blend two images while preserving alpha channel properly"""

    # Convert to numpy arrays for pixel manipulation
    arr1 = np.array(img1, dtype=np.float32)
    arr2 = np.array(img2, dtype=np.float32)

    # Separate RGB and Alpha channels
    rgb1 = arr1[:, :, :3]
    alpha1 = arr1[:, :, 3:4]

    rgb2 = arr2[:, :, :3]
    alpha2 = arr2[:, :, 3:4]

    # Blend RGB channels
    blended_rgb = rgb1 * (1 - alpha) + rgb2 * alpha

    # Blend alpha channels (preserve transparency)
    blended_alpha = alpha1 * (1 - alpha) + alpha2 * alpha

    # Combine back together
    result = np.concatenate([blended_rgb, blended_alpha], axis=2)
    result = np.clip(result, 0, 255).astype(np.uint8)

    return Image.fromarray(result, 'RGBA')


def generate_5_state_images(source_dir: Path, output_dir: Path):
    """Generate only 5 discrete mouth positions, delete all others"""

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Eye states to process
    eye_states = ['eo', 'ec']

    # Only 5 positions
    states = [
        (0, 0.00, "fully closed"),
        (25, 0.25, "1/4 open"),
        (50, 0.50, "half open"),
        (75, 0.75, "3/4 open"),
        (100, 1.00, "fully open"),
    ]

    # First, delete all intermediate images (1-99 except 25, 50, 75)
    print("Cleaning up old intermediate images...")
    for eye_state in eye_states:
        for pos in range(1, 100):
            if pos in [25, 50, 75]:
                continue
            img_path = output_dir / f'teddy_{eye_state}m{pos}.png'
            if img_path.exists():
                img_path.unlink()
                print(f"  Deleted: {img_path.name}")

    print("\nGenerating clean images...")
    for eye_state in eye_states:
        # Load the closed and open mouth images
        closed_path = source_dir / f'teddy_{eye_state}mc.png'
        open_path = source_dir / f'teddy_{eye_state}mo.png'

        if not closed_path.exists() or not open_path.exists():
            print(f"Warning: Missing images for {eye_state}")
            continue

        img_closed = Image.open(closed_path).convert('RGBA')
        img_open = Image.open(open_path).convert('RGBA')

        print(f"\nProcessing {eye_state} (eyes {'open' if eye_state == 'eo' else 'closed'}):")

        # Generate images for each state
        for position, blend_alpha, description in states:
            if blend_alpha == 0.0:
                output_img = img_closed
            elif blend_alpha == 1.0:
                output_img = img_open
            else:
                # Use proper alpha-preserving blend
                output_img = blend_with_alpha_preservation(img_closed, img_open, blend_alpha)

            output_path = output_dir / f'teddy_{eye_state}m{position}.png'
            output_img.save(output_path, 'PNG', optimize=True)
            print(f"  Generated: {output_path.name} ({description})")

    print(f"\n✓ Complete! Only 5 states remain: 0, 25, 50, 75, 100")
    print(f"  All intermediate images removed")


if __name__ == '__main__':
    # Paths
    project_root = Path(__file__).parent.parent
    source_dir = project_root / 'frontend' / 'public' / 'img'
    output_dir = source_dir

    print("Raspi Ruxpin Clean 5-State Generator")
    print("=" * 50)
    print(f"Source directory: {source_dir}")
    print(f"Output directory: {output_dir}")

    generate_5_state_images(source_dir, output_dir)
