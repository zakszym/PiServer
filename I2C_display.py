from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import time as t


# Define the I2C address of your display (default: 0x3C)
I2C_ADDR = 0x3C

# Initialize I2C communication
serial = i2c(port=1, address=I2C_ADDR)

# Create a SH1106 OLED display instance
device = sh1106(serial, rotate=0)  # Set 'rotate' based on your display orientation


# Create a blank image
width = device.width
height = device.height
image = Image.new('1', (width, height))

# Get a drawing object to draw on the image
draw = ImageDraw.Draw(image)

# Load a font
font = ImageFont.load_default()

# Display text
draw.text((0, 0), 'Hello,', font=font, fill=255)
draw.text((0, 10), 'Raspberry Pi!', font=font, fill=255)
draw.text((0, 20), 'Raspberry Pi!', font=font, fill=255)
draw.text((0, 30), 'Raspberry Pi!', font=font, fill=255)
draw.text((0, 40), 'Raspberry Pi!', font=font, fill=255)
draw.text((0, 50), 'Raspberry Pi!', font=font, fill=255)

# Display the image
device.display(image)

t.sleep(20)