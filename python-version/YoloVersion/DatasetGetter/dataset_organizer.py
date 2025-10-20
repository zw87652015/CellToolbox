"""
Dataset Organizer for YOLO Training

This tool automatically finds JPG images and their corresponding TXT label files,
then organizes them into a single folder ready for YOLO training.

Usage:
    python dataset_organizer.py

Features:
    - Recursively searches for image-label pairs
    - Validates matching filenames
    - Organizes into images/ and labels/ folders
    - Supports train/val split
    - Handles duplicates
    - Generates statistics
"""

import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json
from datetime import datetime


class DatasetOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Dataset Organizer - YOLO Training")
        self.root.geometry("900x700")
        
        # Paths
        self.source_dir = None
        self.output_dir = None
        
        # Found pairs
        self.image_label_pairs = []
        self.orphan_images = []
        self.orphan_labels = []
        
        self.create_ui()
    
    def create_ui(self):
        """Create the application UI"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Dataset Organizer", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Source directory
        source_frame = ttk.LabelFrame(main_frame, text="Source Directory", padding="10")
        source_frame.pack(fill=tk.X, pady=5)
        
        self.source_var = tk.StringVar(value="No directory selected")
        ttk.Label(source_frame, textvariable=self.source_var, 
                 wraplength=700).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(source_frame, text="Browse", 
                  command=self.select_source).pack(side=tk.RIGHT, padx=5)
        
        # Output directory
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        self.output_var = tk.StringVar(value="No directory selected")
        ttk.Label(output_frame, textvariable=self.output_var, 
                 wraplength=700).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Browse", 
                  command=self.select_output).pack(side=tk.RIGHT, padx=5)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        # Recursive search
        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Search subdirectories recursively", 
                       variable=self.recursive_var).pack(anchor=tk.W)
        
        # Copy or move
        self.copy_mode_var = tk.StringVar(value="copy")
        ttk.Radiobutton(options_frame, text="Copy files (keep originals)", 
                       variable=self.copy_mode_var, value="copy").pack(anchor=tk.W)
        ttk.Radiobutton(options_frame, text="Move files (remove originals)", 
                       variable=self.copy_mode_var, value="move").pack(anchor=tk.W)
        
        # Train/val split
        split_frame = ttk.Frame(options_frame)
        split_frame.pack(fill=tk.X, pady=5)
        
        self.split_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(split_frame, text="Split into train/val (random)", 
                       variable=self.split_var, 
                       command=self.toggle_split).pack(side=tk.LEFT)
        
        ttk.Label(split_frame, text="Val %:").pack(side=tk.LEFT, padx=(20, 5))
        self.val_percent_var = tk.StringVar(value="20")
        self.val_percent_entry = ttk.Entry(split_frame, textvariable=self.val_percent_var, 
                                           width=5, state='disabled')
        self.val_percent_entry.pack(side=tk.LEFT)
        
        # Random seed option
        seed_frame = ttk.Frame(options_frame)
        seed_frame.pack(fill=tk.X, pady=5)
        
        self.use_seed_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(seed_frame, text="Use random seed (reproducible split)", 
                       variable=self.use_seed_var,
                       command=self.toggle_seed).pack(side=tk.LEFT)
        
        ttk.Label(seed_frame, text="Seed:").pack(side=tk.LEFT, padx=(20, 5))
        self.seed_var = tk.StringVar(value="42")
        self.seed_entry = ttk.Entry(seed_frame, textvariable=self.seed_var, 
                                    width=10, state='disabled')
        self.seed_entry.pack(side=tk.LEFT)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="1. Scan for Pairs", 
                  command=self.scan_pairs).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="2. Organize Dataset", 
                  command=self.organize_dataset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", 
                  command=self.clear_results).pack(side=tk.LEFT, padx=5)
        
        # Results
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text = tk.Text(results_frame, height=20, 
                                    yscrollcommand=scrollbar.set, wrap=tk.WORD)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_text.yview)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.log("Welcome! Select source and output directories to start.")
    
    def select_source(self):
        """Select source directory"""
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_dir = directory
            self.source_var.set(directory)
            self.log(f"Source directory: {directory}")
    
    def select_output(self):
        """Select output directory"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir = directory
            self.output_var.set(directory)
            self.log(f"Output directory: {directory}")
    
    def toggle_split(self):
        """Toggle train/val split option"""
        if self.split_var.get():
            self.val_percent_entry.config(state='normal')
        else:
            self.val_percent_entry.config(state='disabled')
    
    def toggle_seed(self):
        """Toggle random seed option"""
        if self.use_seed_var.get():
            self.seed_entry.config(state='normal')
        else:
            self.seed_entry.config(state='disabled')
    
    def scan_pairs(self):
        """Scan for image-label pairs"""
        if not self.source_dir:
            messagebox.showwarning("Warning", "Please select source directory first")
            return
        
        self.log("\n=== Scanning for Image-Label Pairs ===")
        self.status_var.set("Scanning...")
        self.root.update()
        
        # Clear previous results
        self.image_label_pairs = []
        self.orphan_images = []
        self.orphan_labels = []
        
        # Find all images and labels
        if self.recursive_var.get():
            image_pattern = "**/*.jpg"
            label_pattern = "**/*.txt"
        else:
            image_pattern = "*.jpg"
            label_pattern = "*.txt"
        
        source_path = Path(self.source_dir)
        
        # Find all JPG files
        images = {}
        for img_path in source_path.glob(image_pattern):
            base_name = img_path.stem
            images[base_name] = img_path
        
        # Find all TXT files
        labels = {}
        for label_path in source_path.glob(label_pattern):
            base_name = label_path.stem
            # Skip metadata files
            if base_name.endswith('_metadata'):
                continue
            labels[base_name] = label_path
        
        # Match pairs
        for base_name, img_path in images.items():
            if base_name in labels:
                self.image_label_pairs.append({
                    'name': base_name,
                    'image': str(img_path),
                    'label': str(labels[base_name])
                })
            else:
                self.orphan_images.append(str(img_path))
        
        # Find orphan labels
        for base_name, label_path in labels.items():
            if base_name not in images:
                self.orphan_labels.append(str(label_path))
        
        # Display results
        self.log(f"\nFound {len(self.image_label_pairs)} matching pairs")
        self.log(f"Found {len(self.orphan_images)} images without labels")
        self.log(f"Found {len(self.orphan_labels)} labels without images")
        
        if self.image_label_pairs:
            self.log("\nSample pairs:")
            for i, pair in enumerate(self.image_label_pairs[:5]):
                self.log(f"  {i+1}. {pair['name']}")
            if len(self.image_label_pairs) > 5:
                self.log(f"  ... and {len(self.image_label_pairs) - 5} more")
        
        if self.orphan_images:
            self.log(f"\nWarning: {len(self.orphan_images)} images have no labels")
            self.log("These will be skipped during organization")
        
        if self.orphan_labels:
            self.log(f"\nWarning: {len(self.orphan_labels)} labels have no images")
            self.log("These will be skipped during organization")
        
        self.status_var.set(f"Found {len(self.image_label_pairs)} pairs")
    
    def organize_dataset(self):
        """Organize dataset into output directory"""
        if not self.output_dir:
            messagebox.showwarning("Warning", "Please select output directory first")
            return
        
        if not self.image_label_pairs:
            messagebox.showwarning("Warning", "Please scan for pairs first")
            return
        
        # Confirm
        msg = f"Organize {len(self.image_label_pairs)} pairs to:\n{self.output_dir}\n\n"
        msg += f"Mode: {self.copy_mode_var.get().upper()}\n"
        if self.split_var.get():
            msg += f"Split: train/val ({100-int(self.val_percent_var.get())}%/{self.val_percent_var.get()}%)"
        else:
            msg += "Split: No (all in one folder)"
        
        if not messagebox.askyesno("Confirm", msg):
            return
        
        self.log("\n=== Organizing Dataset ===")
        self.status_var.set("Organizing...")
        self.root.update()
        
        try:
            # Create output structure
            output_path = Path(self.output_dir)
            
            if self.split_var.get():
                # Train/val split
                val_percent = int(self.val_percent_var.get())
                if val_percent < 0 or val_percent > 50:
                    messagebox.showerror("Error", "Validation percentage must be between 0 and 50")
                    return
                
                # Create directories
                train_img_dir = output_path / 'images' / 'train'
                train_label_dir = output_path / 'labels' / 'train'
                val_img_dir = output_path / 'images' / 'val'
                val_label_dir = output_path / 'labels' / 'val'
                
                train_img_dir.mkdir(parents=True, exist_ok=True)
                train_label_dir.mkdir(parents=True, exist_ok=True)
                val_img_dir.mkdir(parents=True, exist_ok=True)
                val_label_dir.mkdir(parents=True, exist_ok=True)
                
                # Split data with random shuffling
                import random
                
                # Set random seed if specified (for reproducibility)
                if self.use_seed_var.get():
                    try:
                        seed = int(self.seed_var.get())
                        random.seed(seed)
                        self.log(f"Using random seed: {seed} (reproducible split)")
                    except ValueError:
                        self.log("Warning: Invalid seed, using random split")
                else:
                    # Use truly random split (different each time)
                    import time
                    random.seed(int(time.time() * 1000))
                    self.log("Using random split (different each time)")
                
                # Shuffle to ensure random distribution across conditions
                random.shuffle(self.image_label_pairs)
                self.log(f"Shuffled {len(self.image_label_pairs)} pairs randomly")
                
                # Split into train/val
                split_idx = int(len(self.image_label_pairs) * (1 - val_percent / 100))
                train_pairs = self.image_label_pairs[:split_idx]
                val_pairs = self.image_label_pairs[split_idx:]
                
                self.log(f"Split ratio: {100-val_percent}% train / {val_percent}% val")
                
                # Copy/move files
                self.process_pairs(train_pairs, train_img_dir, train_label_dir, "train")
                self.process_pairs(val_pairs, val_img_dir, val_label_dir, "val")
                
                self.log(f"\nTrain set: {len(train_pairs)} pairs")
                self.log(f"Val set: {len(val_pairs)} pairs")
                
            else:
                # No split - all in one folder
                img_dir = output_path / 'images'
                label_dir = output_path / 'labels'
                
                img_dir.mkdir(parents=True, exist_ok=True)
                label_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy/move files
                self.process_pairs(self.image_label_pairs, img_dir, label_dir, "all")
            
            # Save metadata
            self.save_metadata(output_path)
            
            self.log("\n=== Organization Complete ===")
            self.log(f"Output directory: {self.output_dir}")
            self.status_var.set("Complete!")
            
            messagebox.showinfo("Success", 
                               f"Successfully organized {len(self.image_label_pairs)} pairs!\n\n"
                               f"Location: {self.output_dir}")
            
        except Exception as e:
            self.log(f"\nError: {str(e)}")
            messagebox.showerror("Error", f"Failed to organize dataset:\n{str(e)}")
            self.status_var.set("Error")
    
    def process_pairs(self, pairs, img_dir, label_dir, subset_name):
        """Process and copy/move pairs"""
        mode = self.copy_mode_var.get()
        
        for i, pair in enumerate(pairs):
            try:
                # Get source paths
                src_img = Path(pair['image'])
                src_label = Path(pair['label'])
                
                # Get destination paths
                dst_img = img_dir / src_img.name
                dst_label = label_dir / src_label.name
                
                # Handle duplicates
                counter = 1
                while dst_img.exists():
                    dst_img = img_dir / f"{src_img.stem}_{counter}{src_img.suffix}"
                    dst_label = label_dir / f"{src_label.stem}_{counter}{src_label.suffix}"
                    counter += 1
                
                # Copy or move
                if mode == 'copy':
                    shutil.copy2(src_img, dst_img)
                    shutil.copy2(src_label, dst_label)
                else:  # move
                    shutil.move(str(src_img), str(dst_img))
                    shutil.move(str(src_label), str(dst_label))
                
                if (i + 1) % 100 == 0:
                    self.log(f"  Processed {i + 1}/{len(pairs)} pairs...")
                    self.root.update()
                    
            except Exception as e:
                self.log(f"  Error processing {pair['name']}: {str(e)}")
        
        self.log(f"  {subset_name}: {len(pairs)} pairs processed")
    
    def save_metadata(self, output_path):
        """Save organization metadata"""
        metadata = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'source_directory': self.source_dir,
            'output_directory': str(output_path),
            'total_pairs': len(self.image_label_pairs),
            'orphan_images': len(self.orphan_images),
            'orphan_labels': len(self.orphan_labels),
            'mode': self.copy_mode_var.get(),
            'split': self.split_var.get(),
            'split_method': 'random_shuffle',
            'val_percent': int(self.val_percent_var.get()) if self.split_var.get() else 0,
            'random_seed': int(self.seed_var.get()) if self.use_seed_var.get() else None,
            'reproducible': self.use_seed_var.get()
        }
        
        metadata_path = output_path / 'organization_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.log(f"Metadata saved: {metadata_path.name}")
    
    def clear_results(self):
        """Clear results"""
        self.results_text.delete(1.0, tk.END)
        self.image_label_pairs = []
        self.orphan_images = []
        self.orphan_labels = []
        self.status_var.set("Cleared")
        self.log("Results cleared. Ready for new scan.")
    
    def log(self, message):
        """Log message to results"""
        self.results_text.insert(tk.END, f"{message}\n")
        self.results_text.see(tk.END)


def main():
    root = tk.Tk()
    app = DatasetOrganizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
