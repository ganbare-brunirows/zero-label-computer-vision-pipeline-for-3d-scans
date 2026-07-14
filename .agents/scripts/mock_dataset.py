import os
import random
from PIL import Image, ImageDraw

def generate_mock_dataset(output_dir):
    images_dir = os.path.join(output_dir, 'images')
    labels_dir = os.path.join(output_dir, 'labels')
    
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)
    
    classes = ['BULBASAUR', 'GENGAR', 'PIKACHU']
    
    # Generate 2500 dummy images and labels
    for i in range(2500):
        # Create a blank image with random background
        img = Image.new('RGB', (1024, 1024), color=(
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200)
        ))
        draw = ImageDraw.Draw(img)
        
        # Decide how many objects
        num_objects = random.randint(1, 3)
        label_lines = []
        
        for _ in range(num_objects):
            class_id = random.randint(0, 2)
            
            # Generate random bounding box
            x_center = random.uniform(0.2, 0.8)
            y_center = random.uniform(0.2, 0.8)
            width = random.uniform(0.1, 0.3)
            height = random.uniform(0.1, 0.3)
            
            # Draw something on the image
            x1 = int((x_center - width/2) * 1024)
            y1 = int((y_center - height/2) * 1024)
            x2 = int((x_center + width/2) * 1024)
            y2 = int((y_center + height/2) * 1024)
            
            color = (255, 0, 0) if class_id == 0 else (0, 255, 0) if class_id == 1 else (0, 0, 255)
            draw.rectangle([x1, y1, x2, y2], fill=color)
            
            # YOLO format: class_id x_center y_center width height (normalized)
            label_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
            
        # Save image
        img_name = f"rgb_{i:04d}.png"
        img.save(os.path.join(images_dir, img_name))
        
        # Save label
        label_name = f"rgb_{i:04d}.txt"
        with open(os.path.join(labels_dir, label_name), 'w') as f:
            f.write('\n'.join(label_lines))
            
    print(f"Successfully generated 50 mock images and YOLO labels in {output_dir}")

if __name__ == '__main__':
    generate_mock_dataset(r'C:\Users\bruni\Documents\HoudiniJOb\RawCanMeshes\dataset')
