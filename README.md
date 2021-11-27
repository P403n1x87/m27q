# Gigabyte M27Q Settings Controller

This Python library allows you to control the Gigabyte M27Q settings via USB.
Feel free to contribute further settings.

The initial implementation was based on [this gist](https://gist.github.com/wadimw/4ac972d07ed1f3b6f22a101375ecac41).

> On Linux you might be required to create a `udev` rule in, e.g.
> `/etc/udev/rules.d/10-local.rules` to allow USB traffic to the monitor with:
> 
> `SUBSYSTEM=="usb", ATTRS{idVendor}=="2109", ATTR{idProduct}=="8883", MODE="0666"`.
## Example

This is a simple script to simulate the KVM switch button

~~~ python
from m27q import MonitorControl


with MonitorControl() as m:
    m.toggle_kvm()
~~~