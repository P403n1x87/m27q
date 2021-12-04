# For Gigabyte M27Q KVM connected over USB
#
# Based on: https://gist.github.com/wadimw/4ac972d07ed1f3b6f22a101375ecac41


import sys
import typing as t
from dataclasses import dataclass
from time import sleep
import usb.core
import usb.util


@dataclass
class BasicProperty:
    minimum: int
    maximum: int
    message_a: int
    message_b: int = 0

    def clamp(self, v: int):
        return max(self.minimum, min(self.maximum, v))


@dataclass
class EnumProperty:
    allowed: t.List[int]
    message_a: int
    message_b: int = 0

    def clamp(self, v: int):
        if v not in self.allowed:
            raise Exception(f"Only allowed values: {self.allowed}")
        return v


Property = t.Union[BasicProperty, EnumProperty]


class MonitorControl:
    BRIGHTNESS = BasicProperty(0, 100, 0x10, 0x00)
    CONTRAST = BasicProperty(0, 100, 0x12, 0x00)
    SHARPNESS = BasicProperty(0, 100, 0x87, 0x00)
    BLUE_LIGHT_REDUCTION = BasicProperty(0, 10, 0xe0, 0x0b)
    KVM_STATUS = BasicProperty(0, 1, 0xe0, 0x69)
    BLACK_EQUALIZER = BasicProperty(0, 10, 0xe0, 0x02)
    OSD_TIMEOUT = EnumProperty([5, 10, 15, 20, 25, 30], 0xe0, 0x30)

    def __init__(self):
        self._VID = 0x2109  # (VIA Labs, Inc.)
        self._PID = 0x8883  # USB Billboard Device
        self._dev = None
        self._usb_delay = 50 / 1000  # 50 ms sleep after every usb op
        self._min_brightness = 0
        self._max_brightness = 100
        self._min_volume = 0
        self._max_volume = 100

    # Find USB device, set config
    def __enter__(self):
        self._dev = usb.core.find(idVendor=self._VID, idProduct=self._PID)
        if self._dev is None:
            raise IOError(f"Device VID_{self._VID}&PID_{self._PID} not found")

        self._had_driver = False
        if sys.platform != "win32":
            if self._dev.is_kernel_driver_active(0):
                self._dev.detach_kernel_driver(0)
                self._had_driver = True

        self._dev.set_configuration(1)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._had_driver:
            self._dev.attach_kernel_driver(0)

    def usb_write(self, b_request: int, w_value: int, w_index: int, message: bytes):
        bm_request_type = 0x40
        if not self._dev.ctrl_transfer(
            bm_request_type, b_request, w_value, w_index, message
        ) == len(message):
            raise IOError("Transferred message length mismatch")
        sleep(self._usb_delay)

    def usb_read(self, b_request: int, w_value: int, w_index: int, msg_length: int):
        bm_request_type = 0xC0
        data = self._dev.ctrl_transfer(
            bm_request_type, b_request, w_value, w_index, msg_length
        )
        sleep(self._usb_delay)
        return data

    def get_osd(self, data: t.List[int]):
        self.usb_write(
            b_request=178,
            w_value=0,
            w_index=0,
            message=bytearray([0x6E, 0x51, 0x81 + len(data), 0x01]) + bytearray(data),
        )
        data = self.usb_read(b_request=162, w_value=0, w_index=111, msg_length=12)
        return data[10]

    def set_osd(self, data: bytearray):
        self.usb_write(
            b_request=178,
            w_value=0,
            w_index=0,
            message=bytearray([0x6E, 0x51, 0x81 + len(data), 0x03] + data),
        )

    def set_property(self, property: Property, value: int):
        self.set_osd([property.message_a, property.message_b, property.clamp(value)])

    def get_property(self, property: Property):
        return self.get_osd([property.message_a, property.message_b])

    def transition_property(self, property: BasicProperty, target: int, step: int = 3):
        current = self.get_property(property)
        diff = abs(target - current)
        if current <= target:
            step = 1 * step  # increase
        else:
            step = -1 * step  # decrease
        while diff >= abs(step):
            current += step
            self.set_property(property, current)
            diff -= abs(step)
        # Set one last time
        if current != target:
            self.set_property(property, target)

    def set_brightness(self, brightness: int):
        self.set_property(MonitorControl.BRIGHTNESS, brightness)

    def get_brightness(self):
        return self.get_property(MonitorControl.BRIGHTNESS)

    def transition_brightness(self, to_brightness: int, step: int = 3):
        self.transition_property(MonitorControl.BRIGHTNESS, to_brightness, step)

    def set_volume(self, volume: int):
        self.set_property(MonitorControl.VOLUME, volume)

    def get_volume(self):
        return self.get_property(MonitorControl.VOLUME)

    def set_contrast(self, contrast: int):
        self.set_property(MonitorControl.CONTRAST, contrast)

    def get_contrast(self):
        return self.get_property(MonitorControl.CONTRAST)

    def get_kvm_status(self):
        return self.get_property(MonitorControl.KVM_STATUS)

    def set_kvm_status(self, status):
        self.set_property(MonitorControl.KVM_STATUS, status)

    def toggle_kvm(self):
        self.set_kvm_status(1 - self.get_kvm_status())


# Test
if __name__ == "__main__":
    with MonitorControl() as m:
        m.set_volume(20)
        print(m.get_volume())
        # m.toggle_kvm()
