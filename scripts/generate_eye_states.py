#!/usr/bin/env python3
"""
Generate intermediate eye states with proper alpha compositing.

Creates images with 5 eye positions (0, 25, 50, 75, 100) combined with
5 mouth positions (0, 25, 50, 75, 100) = 25 total images.
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


def generate_eye_state_images(source_dir: Path, output_dir: Path):
    """Generate images with 5 eye positions and 5 mouth positions"""

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # 5 discrete positions
    positions = [
        (0, 0.00, "fully closed"),
        (25, 0.25, "1/4 open"),
        (50, 0.50, "half open"),
        (75, 0.75, "3/4 open"),
        (100, 1.00, "fully open"),
    ]

    # Load base images (eyes closed and open, each with mouth closed and open)
    base_images = {}
    for eye_state in ['ec', 'eo']:
        for mouth_state in ['mc', 'mo']:
            path = source_dir / f'teddy_{eye_state}{mouth_state}.png'
            if not path.exists():
                print(f"Error: Missing base image {path}")
                return
            base_images[f'{eye_state}{mouth_state}'] = Image.open(path).convert('RGBA')
            print(f"Loaded: {path.name}")

    print("\nGenerating eye state images...")

    # Generate for each eye position
    for eye_pos, eye_alpha, eye_desc in positions:
        print(f"\nEye position {eye_pos}% ({eye_desc}):")

        # For each mouth position
        for mouth_pos, mouth_alpha, mouth_desc in positions:
            # Blend eyes first (closed to open)
            if eye_alpha == 0.0:
                # Eyes fully closed
                img_closed_mouth = base_images['ecmc']
                img_open_mouth = base_images['ecmo']
            elif eye_alpha == 1.0:
                # Eyes fully open
                img_closed_mouth = base_images['eomc']
                img_open_mouth = base_images['eomo']
            else:
                # Eyes intermediate - blend between closed and open
                img_closed_mouth = blend_with_alpha_preservation(
                    base_images['ecmc'], base_images['eomc'], eye_alpha
                )
                img_open_mouth = blend_with_alpha_preservation(
                    base_images['ecmo'], base_images['eomo'], eye_alpha
                )

            # Then blend mouth (closed to open)
            if mouth_alpha == 0.0:
                output_img = img_closed_mouth
            elif mouth_alpha == 1.0:
                output_img = img_open_mouth
            else:
                output_img = blend_with_alpha_preservation(
                    img_closed_mouth, img_open_mouth, mouth_alpha
                )

            # Save with new naming convention: teddy_e{eye_pos}m{mouth_pos}.png
            output_path = output_dir / f'teddy_e{eye_pos}m{mouth_pos}.png'
            output_img.save(output_path, 'PNG', optimize=True)
            print(f"  Generated: {output_path.name} (mouth: {mouth_desc})")

    # Clean up old naming convention files (eo/ec)
    print("\nCleaning up old naming convention...")
    for old_file in output_dir.glob('teddy_e[oc]m*.png'):
        if old_file.name not in ['teddy_ecmc.png', 'teddy_ecmo.png', 'teddy_eomc.png', 'teddy_eomo.png']:
            old_file.unlink()
            print(f"  Deleted: {old_file.name}")

    print(f"\n✓ Complete! Generated 25 images (5 eye positions × 5 mouth positions)")
    print(f"  Eye positions: 0, 25, 50, 75, 100")
    print(f"  Mouth positions: 0, 25, 50, 75, 100")


if __name__ == '__main__':
    # Paths
    project_root = Path(__file__).parent.parent
    source_dir = project_root / 'frontend' / 'public' / 'img'
    output_dir = source_dir

    print("Raspi Ruxpin Eye State Generator")
    print("=" * 50)
    print(f"Source directory: {source_dir}")
    print(f"Output directory: {output_dir}")
    print()

    generate_eye_state_images(source_dir, output_dir)
