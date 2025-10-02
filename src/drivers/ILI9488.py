"""
ILI9488 MicroPython Driver
Created by Denis Smolin in 2025

This driver provides an interface for controlling the ILI9488 TFT LCD display
using MicroPython on an ESP32 or similar microcontroller. It supports basic
graphics operations like drawing pixels, lines, rectangles, and text, as well
as displaying images.
"""

import time, machine

# ILI9488 Display Controller Commands
TFT_NOP = 0x00      # No Operation
TFT_SWRST = 0x01    # Software Reset
TFT_SLPIN = 0x10    # Enter Sleep Mode
TFT_SLPOUT = 0x11   # Exit Sleep Mode
TFT_INVOFF = 0x20   # Display Inversion Off
TFT_INVON = 0x21    # Display Inversion On
TFT_DISPOFF = 0x28  # Display Off
TFT_DISPON = 0x29   # Display On
TFT_CASET = 0x2A    # Column Address Set
TFT_PASET = 0x2B    # Page Address Set
TFT_RAMWR = 0x2C    # Memory Write
TFT_RAMRD = 0x2E    # Memory Read
TFT_MADCTL = 0x36   # Memory Access Control

def RGB(r, g, b):
    """Converts individual R, G, B color components into a tuple.

    Args:
        r (int): Red component (0-255).
        g (int): Green component (0-255).
        b (int): Blue component (0-255).

    Returns:
        tuple: A tuple (r, g, b) representing the RGB color.
    """
    return r, g, b

class ILI9488:
    """Driver for the ILI9488 TFT LCD display controller.

    Provides methods for display initialization, basic drawing primitives,
    text rendering, and image display.
    """
    # Predefined RGB color constants for convenience
    BLACK   = RGB(0, 0, 0)
    WHITE   = RGB(255, 255, 255)
    RED     = RGB(255, 0, 0)
    GREEN   = RGB(0, 255, 0)
    BLUE    = RGB(0, 0, 255)
    YELLOW  = RGB(255, 255, 0)
    CYAN    = RGB(0, 255, 255)
    MAGENTA = RGB(255, 0, 255)
    GRAY    = RGB(128, 128, 128)
    ORANGE  = RGB(255, 165, 0)
    PURPLE  = RGB(128, 0, 128)

    def __init__(self, spi, cs, dc, rst, rotation=0, font = None):
        """
        Initializes the ILI9488 display driver.

        Args:
            spi (machine.SPI): Configured SPI bus object.
            cs (machine.Pin): Chip Select pin object.
            dc (machine.Pin): Data/Command pin object.
            rst (machine.Pin): Reset pin object.
            rotation (int, optional): Initial screen rotation in degrees (0, 90, 180, 270). Defaults to 0.
            font (XglcdFont, optional): Default font object to use for text rendering. Defaults to None.
        """
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.width = 480  # Default width for 0/180 rotation
        self.height = 320 # Default height for 0/180 rotation
        self.rotation = rotation
        self.font = font

        # Configure control pins as outputs and set initial states
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=1)
        self.rst.init(self.rst.OUT, value=1)

        self.reset()
        self.init_display()
        self.rotate(rotation)

    def rotate(self, rotation):
        """Sets the display rotation.
        
        Args:
            rotation (int): Screen orientation in degrees (0, 90, 180, 270).
        """
        rotation = rotation % 360  # Normalize to 0-359 degrees
        self.rotation = rotation
        madctl = 0x28  # Default: MX=1 (row address order), MV=0 (column address order), MY=0 (page address order)
        
        # Adjust MADCTL register based on desired rotation
        # The BGR bit (bit 3, 0x08) is typically set for ILI9488 to ensure correct color order.
        if rotation == 0:
            madctl = 0x28  # Portrait (MX=1, MY=0, MV=0, BGR=1)
            self.width = 480
            self.height = 320
        elif rotation == 90:
            madctl = 0x48  # Landscape (MX=0, MY=1, MV=1, BGR=1)
            self.width = 320
            self.height = 480
        elif rotation == 180:
            madctl = 0xE8  # Portrait inverted (MX=1, MY=1, MV=0, BGR=1)
            self.width = 480
            self.height = 320
        elif rotation == 270:
            madctl = 0x88  # Landscape inverted (MX=0, MY=0, MV=1, BGR=1)
            self.width = 320
            self.height = 480
        else:
            print("Invalid rotation value, skipping...")

        # Send new configuration to display
        self.write_cmd(TFT_MADCTL)
        self.write_data(madctl)

    def reset(self):
        """Performs a hardware reset of the display controller."""
        self.rst.value(0) # Pull RST low
        time.sleep_ms(50)
        self.rst.value(1) # Pull RST high
        time.sleep_ms(50)

    def write_cmd(self, cmd):
        """Writes a command byte to the display controller.

        Args:
            cmd (int): The command byte to send.
        """
        self.cs.value(0) # Assert Chip Select
        self.dc.value(0) # Set Data/Command to Command mode
        self.spi.write(bytearray([cmd]))
        self.cs.value(1) # De-assert Chip Select

    def write_data(self, data):
        """Writes data bytes to the display controller.

        Args:
            data (int or bytes): The data to send. Can be a single byte (int) or a bytearray/bytes object.
        """
        self.cs.value(0) # Assert Chip Select
        self.dc.value(1) # Set Data/Command to Data mode
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs.value(1) # De-assert Chip Select

    def init_display(self):
        """Initializes the ILI9488 display with a sequence of commands and data.
        This sequence configures gamma, power, VCOM, pixel format, frame rate, and other display parameters.
        """
        # Positive Gamma Control
        self.write_cmd(0xE0)
        self.write_data(0x00)
        self.write_data(0x03)
        self.write_data(0x09)
        self.write_data(0x08)
        self.write_data(0x16)
        self.write_data(0x0A)
        self.write_data(0x3F)
        self.write_data(0x78)
        self.write_data(0x4C)
        self.write_data(0x09)
        self.write_data(0x0A)
        self.write_data(0x08)
        self.write_data(0x16)
        self.write_data(0x1A)
        self.write_data(0x0F)

        # Negative Gamma Control
        self.write_cmd(0XE1)
        self.write_data(0x00)
        self.write_data(0x16)
        self.write_data(0x19)
        self.write_data(0x03)
        self.write_data(0x0F)
        self.write_data(0x05)
        self.write_data(0x32)
        self.write_data(0x45)
        self.write_data(0x46)
        self.write_data(0x04)
        self.write_data(0x0E)
        self.write_data(0x0D)
        self.write_data(0x35)
        self.write_data(0x37)
        self.write_data(0x0F)

        # Power Control 1
        self.write_cmd(0XC0)
        self.write_data(0x17)
        self.write_data(0x15)

        # Power Control 2
        self.write_cmd(0xC1)
        self.write_data(0x41)

        # VCOM Control
        self.write_cmd(0xC5)
        self.write_data(0x00)
        self.write_data(0x12)
        self.write_data(0x80)

        # Pixel Interface Format
        self.write_cmd(0x3A)
        self.write_data(0x66) # 18-bit colour for SPI (RGB666)

        # Interface Mode Control
        self.write_cmd(0xB0)
        self.write_data(0x00)

        # Frame Rate Control
        self.write_cmd(0xB1)
        self.write_data(0xA0)

        # Display Inversion Control
        self.write_cmd(0xB4)
        self.write_data(0x02)

        # Display Function Control
        self.write_cmd(0xB6)
        self.write_data(0x02)
        self.write_data(0x02)
        self.write_data(0x3B)

        # Entry Mode Set
        self.write_cmd(0xB7)
        self.write_data(0xC6)

        # Adjust Control 3
        self.write_cmd(0xF7)
        self.write_data(0xA9)
        self.write_data(0x51)
        self.write_data(0x2C)
        self.write_data(0x82)

        # Exit Sleep Mode
        self.write_cmd(TFT_SLPOUT)
        time.sleep_ms(120)

        # Turn Display On
        self.write_cmd(TFT_DISPON)
        time.sleep_ms(25)

    def fill_screen(self, color):
        """Fills the entire display with a single color.

        Args:
            color (tuple): RGB color (r, g, b) to fill the screen with.
        """
        self.set_window(0, 0, self.width - 1, self.height - 1)
        r, g, b = color
        # Create a buffer for one row of pixels
        buf = bytearray(3 * self.width)
        for i in range(self.width):
            buf[3 * i] = r
            buf[3 * i + 1] = g
            buf[3 * i + 2] = b
        # Write the buffer for each row to fill the screen
        for i in range(self.height):
            self.write_data(buf)

    def fill_rect(self, x, y, width, height, color):
        """Draws a filled rectangle on the display.
        
        Args:
            x (int): X-coordinate of the top-left corner.
            y (int): Y-coordinate of the top-left corner.
            width (int): Width of the rectangle.
            height (int): Height of the rectangle.
            color (tuple): RGB color (r, g, b) to fill the rectangle with.
        """
        # Validate coordinates to ensure they are within display bounds
        if x >= self.width or y >= self.height:
            return
            
        # Clamp rectangle dimensions to display boundaries
        x_end = min(x + width - 1, self.width - 1)
        y_end = min(y + height - 1, self.height - 1)
        
        # Calculate actual dimensions after clamping
        actual_width = x_end - x + 1
        actual_height = y_end - y + 1
        
        # Set the drawing window to the rectangle area
        self.set_window(x, y, x_end, y_end)
        
        # Prepare color data for one row of the rectangle
        r, g, b = color
        buf = bytearray(3 * actual_width)
        
        # Fill buffer with the specified color
        for i in range(actual_width):
            buf[3 * i] = r
            buf[3 * i + 1] = g
            buf[3 * i + 2] = b
        
        # Write the color buffer for each row to draw the filled rectangle
        for _ in range(actual_height):
            self.write_data(buf)

    def set_window(self, x0, y0, x1, y1):
        """Sets the active window (drawing area) on the display.

        Args:
            x0 (int): Start column address.
            y0 (int): Start page (row) address.
            x1 (int): End column address.
            y1 (int): End page (row) address.
        """
        self.write_cmd(TFT_CASET) # Column address set
        self.write_data(x0 >> 8)
        self.write_data(x0 & 0xFF)
        self.write_data(x1 >> 8)
        self.write_data(x1 & 0xFF)

        self.write_cmd(TFT_PASET) # Page address set
        self.write_data(y0 >> 8)
        self.write_data(y0 & 0xFF)
        self.write_data(y1 >> 8)
        self.write_data(y1 & 0xFF)

        self.write_cmd(TFT_RAMWR) # Memory write command to prepare for pixel data

    def pixel(self, x, y, color):
        """Draws a single pixel at the specified coordinates.

        Args:
            x (int): X-coordinate of the pixel.
            y (int): Y-coordinate of the pixel.
            color (tuple): RGB color (r, g, b) of the pixel.
        """
        self.set_window(x, y, x, y)
        r, g, b = color
        self.write_data(r)
        self.write_data(g)
        self.write_data(b)

    def hline(self, x, y, w, color):
        """Draws a horizontal line.

        Args:
            x (int): Starting X-coordinate.
            y (int): Y-coordinate.
            w (int): Width (length) of the line.
            color (tuple): RGB color (r, g, b) of the line.
        """
        self.set_window(x, y, x + w - 1, y)
        r, g, b = color
        buf = bytearray(3 * w)
        for i in range(w):
            buf[3 * i] = r
            buf[3 * i + 1] = g
            buf[3 * i + 2] = b
        self.write_data(buf)

    def vline(self, x, y, h, color):
        """Draws a vertical line.

        Args:
            x (int): X-coordinate.
            y (int): Starting Y-coordinate.
            h (int): Height (length) of the line.
            color (tuple): RGB color (r, g, b) of the line.
        """
        self.set_window(x, y, x, y + h - 1)
        r, g, b = color
        buf = bytearray(3 * h)
        for i in range(h):
            buf[3 * i] = r
            buf[3 * i + 1] = g
            buf[3 * i + 2] = b
        self.write_data(buf)

    def rect(self, x, y, w, h, color):
        """Draws an unfilled rectangle.

        Args:
            x (int): X-coordinate of the top-left corner.
            y (int): Y-coordinate of the top-left corner.
            w (int): Width of the rectangle.
            h (int): Height of the rectangle.
            color (tuple): RGB color (r, g, b) of the rectangle borders.
        """
        self.hline(x, y, w, color)
        self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)

    def line(self, x0, y0, x1, y1, color):
        """Draws a line between two points using Bresenham's algorithm.

        Args:
            x0 (int): Starting X-coordinate.
            y0 (int): Starting Y-coordinate.
            x1 (int): Ending X-coordinate.
            y1 (int): Ending Y-coordinate.
            color (tuple): RGB color (r, g, b) of the line.
        """
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
    
    def text(self, x, y, text_str, color,  scale=1, background_color=None, spacing=1):
        """Draws text on the display using the currently set font.
        Supports scaling and optional background color.
        
        Args:
            x (int): Starting X-coordinate for the text.
            y (int): Starting Y-coordinate for the text.
            text_str (str): The string of text to display.
            color (tuple): RGB color (r, g, b) of the text.
            scale (int, optional): Scaling factor for the font (1 for no scaling). Defaults to 1.
            background_color (tuple, optional): RGB background color for the text. If None, background is transparent. Defaults to None.
            spacing (int, optional): Additional pixel spacing between characters. Defaults to 1.
        """
        if not self.font:
            print("Error: Font not loaded. Call set_font() first or pass font to constructor.")
            return
        if scale < 1:
            scale = 1  # Ensure scale is at least 1

        current_x = x
        for char_code in text_str:
            # Get character bitmap data from the font object
            char_data, char_width, char_height = self.font.get_letter(char_code, color, background_color)
            if char_data:
                scaled_width = char_width * scale
                scaled_height = char_height * scale
                
                if scale == 1:
                    # If no scaling, write original character data directly
                    self.set_window(current_x, y, current_x + char_width - 1, y + char_height - 1)
                    self.write_data(char_data)
                else:
                    # Create a buffer for the scaled character
                    scaled_data = bytearray(3 * scaled_width * scaled_height)
                    src_idx = 0
                    dest_idx = 0
                    
                    # Scale character pixels
                    for _ in range(char_height):
                        row_buffer = bytearray(3 * scaled_width)
                        row_idx = 0
                        
                        for _ in range(char_width):
                            pixel = char_data[src_idx:src_idx+3]
                            src_idx += 3
                            for _ in range(scale):
                                row_buffer[row_idx:row_idx+3] = pixel
                                row_idx += 3
                        
                        for _ in range(scale):
                            scaled_data[dest_idx:dest_idx+len(row_buffer)] = row_buffer
                            dest_idx += len(row_buffer)
                    
                    # Draw the scaled character
                    self.set_window(current_x, y, current_x + scaled_width - 1, y + scaled_height - 1)
                    self.write_data(scaled_data)
                
                # Advance cursor position for the next character
                current_x += scaled_width + spacing

    def set_font(self, font_obj):
        """Sets the font object to be used for subsequent text drawing operations.

        Args:
            font_obj (XglcdFont): The font object to set.
        """
        self.font = font_obj
    
    def image(self, x, y, w, h, data):
        """Displays an RGB666 image on the display at the specified coordinates.
        
        Args:
            x (int): X-coordinate of the top-left corner of the image.
            y (int): Y-coordinate of the top-left corner of the image.
            w (int): Width of the image in pixels.
            h (int): Height of the image in pixels.
            data (bytes): Raw RGB666 image data (3 bytes per pixel) as a bytearray or bytes object.
        """
        self.set_window(x, y, x + w - 1, y + h - 1)
        self.write_data(data)

