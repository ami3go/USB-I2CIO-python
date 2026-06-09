import time
from devasys_usbi2cio import DevasysUsbI2cIo


class LCD2004_PCF8574:
    """
    LCD 2004 / 20x4 HD44780 display over PCF8574 I2C backpack.

    Common PCF8574 backpack pin mapping:
        P0 = RS
        P1 = RW
        P2 = EN
        P3 = Backlight
        P4 = D4
        P5 = D5
        P6 = D6
        P7 = D7
    """

    # PCF8574 bit mapping
    RS = 0x01
    RW = 0x02
    EN = 0x04
    BL = 0x08

    # LCD commands
    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCONTROL = 0x08
    LCD_FUNCTIONSET = 0x20
    LCD_SETDDRAMADDR = 0x80

    def __init__(self, i2c, address=0x27, cols=20, rows=4, backlight=True):
        self.i2c = i2c
        self.address = address
        self.cols = cols
        self.rows = rows
        self.backlight = backlight

        self._init_lcd()

    def _write_byte(self, value):
        self.i2c.write(self.address, [value & 0xFF])

    def _pulse_enable(self, value):
        self._write_byte(value | self.EN)
        time.sleep(0.000001)
        self._write_byte(value & ~self.EN)
        time.sleep(0.00005)

    def _write4bits(self, nibble, mode=0):
        """
        Send 4-bit nibble to LCD.
        nibble must be 0x0 to 0xF.
        """
        value = (nibble << 4) & 0xF0

        if self.backlight:
            value |= self.BL

        value |= mode
        self._write_byte(value)
        self._pulse_enable(value)

    def _send(self, value, mode=0):
        high = (value >> 4) & 0x0F
        low = value & 0x0F

        self._write4bits(high, mode)
        self._write4bits(low, mode)

    def command(self, value):
        self._send(value, mode=0)

        if value in (self.LCD_CLEARDISPLAY, self.LCD_RETURNHOME):
            time.sleep(0.002)

    def write_char(self, char):
        self._send(ord(char), mode=self.RS)

    def write_text(self, text):
        for char in text:
            self.write_char(char)

    def clear(self):
        self.command(self.LCD_CLEARDISPLAY)
        time.sleep(0.002)

    def home(self):
        self.command(self.LCD_RETURNHOME)
        time.sleep(0.002)

    def set_cursor(self, col, row):
        """
        Set cursor position.
        For 20x4 LCD, DDRAM row offsets are:
            row 0: 0x00
            row 1: 0x40
            row 2: 0x14
            row 3: 0x54
        """
        row_offsets = [0x00, 0x40, 0x14, 0x54]

        if row >= self.rows:
            row = self.rows - 1

        if col >= self.cols:
            col = self.cols - 1

        address = col + row_offsets[row]
        self.command(self.LCD_SETDDRAMADDR | address)

    def write_line(self, row, text):
        self.set_cursor(0, row)
        text = text[:self.cols]
        text = text.ljust(self.cols)
        self.write_text(text)

    def display_on(self):
        self.command(self.LCD_DISPLAYCONTROL | 0x04)

    def display_off(self):
        self.command(self.LCD_DISPLAYCONTROL)

    def backlight_on(self):
        self.backlight = True
        self._write_byte(self.BL)

    def backlight_off(self):
        self.backlight = False
        self._write_byte(0x00)

    def _init_lcd(self):
        time.sleep(0.05)

        # Reset sequence for HD44780 4-bit mode
        self._write4bits(0x03)
        time.sleep(0.005)

        self._write4bits(0x03)
        time.sleep(0.005)

        self._write4bits(0x03)
        time.sleep(0.001)

        # Set 4-bit mode
        self._write4bits(0x02)
        time.sleep(0.001)

        # Function set:
        # 4-bit mode, 2-line mode, 5x8 font
        # 20x4 displays still use this "2-line" controller setting
        self.command(self.LCD_FUNCTIONSET | 0x08)

        # Display off
        self.command(self.LCD_DISPLAYCONTROL)

        # Clear display
        self.clear()

        # Entry mode:
        # increment cursor, no display shift
        self.command(self.LCD_ENTRYMODESET | 0x02)

        # Display on, cursor off, blink off
        self.command(self.LCD_DISPLAYCONTROL | 0x04)


def main():
    with DevasysUsbI2cIo(dll_path="UsbI2cIo.dll") as i2c:
        print("Scanning I2C bus...")
        devices = i2c.scan()
        print("Found:", [f"0x{x:02X}" for x in devices])

        # Most common LCD addresses are 0x27 or 0x3F
        lcd_addr = 0x27
        #
        if lcd_addr not in devices:
            print(f"LCD not found at 0x{lcd_addr:02X}. Try 0x3F.")
            return

        lcd = LCD2004_PCF8574(i2c, address=lcd_addr)
        print("init done")
        lcd.clear()
        lcd.write_line(0, "DeVaSys USB-I2C")
        lcd.write_line(1, "LCD 2004 test")
        lcd.write_line(2, "Address: 0x27")
        lcd.write_line(3, "Hello Alexandr!")

        time.sleep(3)

        counter = 0
        while True:
            lcd.write_line(3, f"Counter: {counter}")
            print(f"Counter: {counter})
            counter += 1
            time.sleep(1)


if __name__ == "__main__":
    main()