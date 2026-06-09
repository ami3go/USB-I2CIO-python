"""
LCD 2004 / 20x4 HD44780 over PCF8574 I2C backpack example.

Common I2C addresses:
    0x27
    0x3F

Common PCF8574 backpack mapping:
    P0 = RS
    P1 = RW
    P2 = EN
    P3 = Backlight
    P4 = D4
    P5 = D5
    P6 = D6
    P7 = D7
"""

import time

from devasys_usbi2cio import DevasysI2CError, DevasysUsbI2cIo


class LCD2004_PCF8574:
    """Simple LCD 2004 driver for HD44780-compatible display over PCF8574."""

    RS = 0x01
    RW = 0x02
    EN = 0x04
    BL = 0x08

    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCONTROL = 0x08
    LCD_FUNCTIONSET = 0x20
    LCD_SETDDRAMADDR = 0x80

    ROW_OFFSETS = [0x00, 0x40, 0x14, 0x54]

    def __init__(self, i2c, address: int = 0x27, cols: int = 20, rows: int = 4, backlight: bool = True) -> None:
        self.i2c = i2c
        self.address = address
        self.cols = cols
        self.rows = rows
        self.backlight = backlight
        self._init_lcd()

    def _write_byte(self, value: int) -> None:
        self.i2c.write(self.address, [value & 0xFF])

    def _pulse_enable(self, value: int) -> None:
        self._write_byte(value | self.EN)
        time.sleep(0.000001)
        self._write_byte(value & ~self.EN)
        time.sleep(0.00005)

    def _write4bits(self, nibble: int, mode: int = 0) -> None:
        value = (nibble << 4) & 0xF0

        if self.backlight:
            value |= self.BL

        value |= mode
        self._write_byte(value)
        self._pulse_enable(value)

    def _send(self, value: int, mode: int = 0) -> None:
        self._write4bits((value >> 4) & 0x0F, mode)
        self._write4bits(value & 0x0F, mode)

    def command(self, value: int) -> None:
        self._send(value, mode=0)

        if value in (self.LCD_CLEARDISPLAY, self.LCD_RETURNHOME):
            time.sleep(0.002)

    def write_char(self, char: str) -> None:
        self._send(ord(char), mode=self.RS)

    def write_text(self, text: str) -> None:
        for char in text:
            self.write_char(char)

    def clear(self) -> None:
        self.command(self.LCD_CLEARDISPLAY)
        time.sleep(0.002)

    def home(self) -> None:
        self.command(self.LCD_RETURNHOME)
        time.sleep(0.002)

    def set_cursor(self, col: int, row: int) -> None:
        if row >= self.rows:
            row = self.rows - 1
        if col >= self.cols:
            col = self.cols - 1

        address = col + self.ROW_OFFSETS[row]
        self.command(self.LCD_SETDDRAMADDR | address)

    def write_line(self, row: int, text: str) -> None:
        self.set_cursor(0, row)
        self.write_text(text[: self.cols].ljust(self.cols))

    def display_on(self) -> None:
        self.command(self.LCD_DISPLAYCONTROL | 0x04)

    def display_off(self) -> None:
        self.command(self.LCD_DISPLAYCONTROL)

    def backlight_on(self) -> None:
        self.backlight = True
        self._write_byte(self.BL)

    def backlight_off(self) -> None:
        self.backlight = False
        self._write_byte(0x00)

    def _init_lcd(self) -> None:
        time.sleep(0.05)

        # HD44780 4-bit initialization sequence.
        self._write4bits(0x03)
        time.sleep(0.005)

        self._write4bits(0x03)
        time.sleep(0.005)

        self._write4bits(0x03)
        time.sleep(0.001)

        self._write4bits(0x02)
        time.sleep(0.001)

        # 4-bit mode, 2-line controller setting, 5x8 font.
        # 20x4 LCDs still use the 2-line function-set bit.
        self.command(self.LCD_FUNCTIONSET | 0x08)

        self.command(self.LCD_DISPLAYCONTROL)
        self.clear()
        self.command(self.LCD_ENTRYMODESET | 0x02)
        self.command(self.LCD_DISPLAYCONTROL | 0x04)


def main() -> None:
    try:
        with DevasysUsbI2cIo(dll_path="UsbI2cIo.dll", instance=0) as i2c:
            print("Scanning I2C bus...")
            devices = i2c.scan()
            print("Found:", [f"0x{x:02X}" for x in devices])

            lcd_addr = 0x27

            if lcd_addr not in devices:
                print(f"LCD not found at 0x{lcd_addr:02X}. Try changing lcd_addr to 0x3F.")
                return

            lcd = LCD2004_PCF8574(i2c, address=lcd_addr)

            lcd.clear()
            lcd.write_line(0, "DeVaSys USB-I2C")
            lcd.write_line(1, "LCD 2004 test")
            lcd.write_line(2, f"Address: 0x{lcd_addr:02X}")

            counter = 0
            while True:
                lcd.write_line(3, f"Counter: {counter}")
                counter += 1
                time.sleep(1)

    except DevasysI2CError as exc:
        print("DeVaSys error:")
        print(exc)


if __name__ == "__main__":
    main()
