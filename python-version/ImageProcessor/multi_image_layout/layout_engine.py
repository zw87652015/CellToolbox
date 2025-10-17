"""
Layout Engine Module
Handles grid layout calculations and empty cell strategies
"""
from typing import Tuple, List
from enum import Enum
import math


class EmptyCellStrategy(Enum):
    """Strategy for handling empty cells in last row"""
    LEFT = "居左"
    CENTER = "居中"
    DISTRIBUTED = "分散"


class LayoutPreset:
    """Predefined layout presets"""
    PRESETS = [
        (5, 5, "5×5 (25格)"),
        (6, 6, "6×6 (36格)"),
        (3, 8, "3×8 (24格)"),
        (4, 10, "4×10 (40格)"),
        (2, 20, "2×20 (40格)"),
        (7, 7, "7×7 (49格)"),
        (8, 8, "8×8 (64格)"),
        (10, 10, "10×10 (100格)"),
    ]
    
    @classmethod
    def get_preset_names(cls) -> List[str]:
        """Get list of preset names"""
        return ["自定义"] + [name for _, _, name in cls.PRESETS]
    
    @classmethod
    def get_preset_layout(cls, index: int) -> Tuple[int, int]:
        """Get layout for preset index (0 = custom)"""
        if index <= 0 or index > len(cls.PRESETS):
            return 5, 5
        return cls.PRESETS[index - 1][0], cls.PRESETS[index - 1][1]


class LayoutEngine:
    """Handles layout calculations"""
    
    def __init__(self):
        self.cols = 5
        self.rows = 5
        self.image_count = 0
        self.empty_cell_strategy = EmptyCellStrategy.CENTER
    
    def set_layout(self, cols: int, rows: int):
        """Set layout dimensions"""
        self.cols = max(1, cols)
        self.rows = max(1, rows)
    
    def set_image_count(self, count: int):
        """Set number of images"""
        self.image_count = max(0, count)
    
    def set_empty_cell_strategy(self, strategy: EmptyCellStrategy):
        """Set strategy for empty cells"""
        self.empty_cell_strategy = strategy
    
    def get_total_cells(self) -> int:
        """Get total number of cells in grid"""
        return self.cols * self.rows
    
    def get_empty_cell_count(self) -> int:
        """Get number of empty cells"""
        total = self.get_total_cells()
        return max(0, total - self.image_count)
    
    def is_layout_sufficient(self) -> bool:
        """Check if layout can fit all images"""
        return self.image_count <= self.get_total_cells()
    
    def get_last_row_info(self) -> Tuple[int, int, int]:
        """
        Get information about last row
        Returns: (last_row_index, images_in_last_row, empty_in_last_row)
        """
        if self.image_count == 0:
            return 0, 0, self.cols
        
        last_row_idx = (self.image_count - 1) // self.cols
        images_in_last_row = self.image_count - (last_row_idx * self.cols)
        empty_in_last_row = self.cols - images_in_last_row
        
        return last_row_idx, images_in_last_row, empty_in_last_row
    
    def get_cell_position(self, image_index: int) -> Tuple[int, int]:
        """
        Get (col, row) position for an image index
        Accounts for empty cell strategy
        """
        if image_index >= self.image_count:
            return -1, -1
        
        # Calculate row
        row = image_index // self.cols
        col_in_row = image_index % self.cols
        
        # Check if this is the last row with empty cells
        last_row_idx, images_in_last, empty_in_last = self.get_last_row_info()
        
        if row == last_row_idx and empty_in_last > 0:
            # Apply empty cell strategy
            if self.empty_cell_strategy == EmptyCellStrategy.CENTER:
                offset = empty_in_last // 2
                col = col_in_row + offset
            elif self.empty_cell_strategy == EmptyCellStrategy.LEFT:
                col = col_in_row
            elif self.empty_cell_strategy == EmptyCellStrategy.DISTRIBUTED:
                # Distribute empty cells evenly
                if images_in_last == 1:
                    col = self.cols // 2
                else:
                    spacing = (self.cols - 1) / (images_in_last - 1)
                    col = int(col_in_row * spacing)
            else:
                col = col_in_row
        else:
            col = col_in_row
        
        return col, row
    
    def get_canvas_size(self, cell_width: int, cell_height: int, 
                       gap: int = 0, border: int = 0) -> Tuple[int, int]:
        """
        Calculate total canvas size
        Args:
            cell_width: Width of each cell
            cell_height: Height of each cell
            gap: Gap between cells
            border: Border around entire canvas
        Returns: (total_width, total_height)
        """
        width = self.cols * cell_width + (self.cols - 1) * gap + 2 * border
        height = self.rows * cell_height + (self.rows - 1) * gap + 2 * border
        return width, height
    
    def get_cell_rect(self, col: int, row: int, cell_width: int, cell_height: int,
                     gap: int = 0, border: int = 0) -> Tuple[int, int, int, int]:
        """
        Get bounding box for a cell
        Returns: (x, y, width, height)
        """
        x = border + col * (cell_width + gap)
        y = border + row * (cell_height + gap)
        return x, y, cell_width, cell_height
    
    def suggest_optimal_layout(self, image_count: int) -> List[Tuple[int, int, str]]:
        """
        Suggest optimal layouts for given image count
        Returns: List of (cols, rows, reason)
        """
        suggestions = []
        
        # Perfect square
        sqrt = int(math.sqrt(image_count))
        if sqrt * sqrt == image_count:
            suggestions.append((sqrt, sqrt, f"完美正方形 {sqrt}×{sqrt}"))
        
        # Near square
        if sqrt * (sqrt + 1) >= image_count:
            suggestions.append((sqrt, sqrt + 1, f"接近正方形 {sqrt}×{sqrt + 1}"))
        
        # Check if prime
        if self._is_prime(image_count) and image_count > 3:
            suggestions.append((1, image_count, f"质数 - 单列布局 1×{image_count}"))
            suggestions.append((image_count, 1, f"质数 - 单行布局 {image_count}×1"))
        
        # Find factors
        factors = self._find_factors(image_count)
        for factor in factors[:3]:  # Top 3 most balanced
            col, row = factor
            if col <= row:
                suggestions.append((col, row, f"因数分解 {col}×{row}"))
        
        return suggestions
    
    def _is_prime(self, n: int) -> bool:
        """Check if number is prime"""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            if n % i == 0:
                return False
        return True
    
    def _find_factors(self, n: int) -> List[Tuple[int, int]]:
        """
        Find factor pairs sorted by how close they are to square
        Returns: List of (smaller, larger) tuples
        """
        factors = []
        for i in range(1, int(math.sqrt(n)) + 1):
            if n % i == 0:
                factors.append((i, n // i))
        
        # Sort by how close to square (minimize difference)
        factors.sort(key=lambda x: x[1] - x[0])
        return factors
    
    def get_empty_cell_positions(self) -> List[Tuple[int, int]]:
        """
        Get positions of all empty cells
        Returns: List of (col, row) tuples
        """
        if self.image_count >= self.get_total_cells():
            return []
        
        empty_positions = []
        last_row_idx, images_in_last, empty_in_last = self.get_last_row_info()
        
        if empty_in_last == 0:
            return []
        
        # Calculate which columns are empty based on strategy
        if self.empty_cell_strategy == EmptyCellStrategy.CENTER:
            offset = empty_in_last // 2
            for i in range(offset):
                empty_positions.append((i, last_row_idx))
            for i in range(images_in_last + offset, self.cols):
                empty_positions.append((i, last_row_idx))
        
        elif self.empty_cell_strategy == EmptyCellStrategy.LEFT:
            for i in range(images_in_last, self.cols):
                empty_positions.append((i, last_row_idx))
        
        elif self.empty_cell_strategy == EmptyCellStrategy.DISTRIBUTED:
            # Mark all positions as potentially empty, then remove occupied ones
            all_last_row = [(c, last_row_idx) for c in range(self.cols)]
            occupied = set()
            for img_idx in range((last_row_idx * self.cols), self.image_count):
                col, row = self.get_cell_position(img_idx)
                occupied.add((col, row))
            empty_positions = [pos for pos in all_last_row if pos not in occupied]
        
        return empty_positions
    
    def validate_layout(self) -> Tuple[bool, str]:
        """
        Validate current layout
        Returns: (is_valid, message)
        """
        if self.cols <= 0 or self.rows <= 0:
            return False, "行列数必须大于0"
        
        if self.image_count == 0:
            return False, "未加载图片"
        
        total = self.get_total_cells()
        if self.image_count > total:
            needed = math.ceil(self.image_count / self.cols)
            return False, f"布局不足，需要至少 {needed} 行"
        
        return True, "布局有效"
    
    def get_layout_info(self) -> str:
        """Get human-readable layout information"""
        total = self.get_total_cells()
        empty = self.get_empty_cell_count()
        
        if empty == 0:
            return f"{self.cols}×{self.rows} 布局，恰好容纳 {self.image_count} 张图"
        else:
            return f"{self.cols}×{self.rows} 布局，{self.image_count} 张图，末行空出 {empty} 格"
