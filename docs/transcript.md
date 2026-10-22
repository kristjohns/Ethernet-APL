# Transcript — Ethernet-APL, explained — and how it differs from CAN bus

_Generated from the narration that is rendered into the video._

## Intro  `00:00`

Somewhere in a chemical plant, a radar level transmitter watches the surface of a liquid, twenty meters below. It knows the full echo profile, its own electronics temperature, the condition of its antenna, and weeks of trends. And it reports — one number. A current between four and twenty milliamps, on two wires. If you're lucky, a trickle of digital data rides along at 1,200 bits per second — the speed of an early telephone modem. Meanwhile, a few hundred meters away, the office network moves a billion bits per second — almost a million times more.

This video is about the technology that finally brings Ethernet all the way out to the instrument: Ethernet-APL.

We'll take it apart down to the volts, the symbols, and the joules. And as a reference point, we'll use a network that many engineers already know from vehicles and machines: CAN bus.

## 01 · The last kilometer  `00:57`

Process instruments have spoken the same basic language for decades. The 4–20 mA loop is brilliantly simple: two wires, one analog value, and the same two wires power the instrument. Four milliamps, not zero, means zero percent — so a broken wire is instantly obvious.

In the 1980s, HART added digital communication by superimposing a small tone on that current: 1,200 hertz for a one, 2,200 hertz for a zero. Because the tone averages to zero, the analog value is untouched — but the data rate is only 1,200 bits per second.

In the 1990s, fieldbuses such as FOUNDATION Fieldbus H1 and PROFIBUS PA went fully digital, at 31.25 kilobits per second — shared by every device on the segment.

Meanwhile, the rest of industry moved to Ethernet, at a hundred megabits per second and more. On a logarithmic scale, the gap is enormous.

So why didn't plain Ethernet simply run out into the plant? Four walls stood in the way. Distance. Standard 100BASE-TX Ethernet is limited to one hundred meters per link, while field cables run for hundreds of meters — sometimes a kilometer or more. Wires. Office Ethernet needs two or four pairs; plants are full of installed two-wire cable. Power. A field instrument has no local supply. It must be powered over the same two wires that carry its signal. And explosion protection. In hazardous areas, the energy in a circuit must be limited, so that not even a fault can ignite the atmosphere. Ordinary Ethernet was never designed for that. Ethernet-APL — the Advanced Physical Layer — was designed to break all four walls. The key word is “physical”.

## 02 · One new layer  `02:56`

APL replaces only the bottom layer of the network stack: the copper, the voltages, the power, and the safety rules. Everything above it is unchanged Ethernet: the same frames and MAC addresses, IP, TCP and UDP, and the industrial protocols on top — PROFINET, EtherNet/IP, HART-IP, OPC UA, Modbus TCP — even a web server inside the instrument.

Its foundation is 10BASE-T1L, part of the IEEE 802.3cg standard from 2019: ten megabits per second, full duplex, over a single twisted pair, for up to a kilometer. On top of that, the APL project — a joint effort of FieldComm Group, ODVA, the OPC Foundation, and PROFIBUS and PROFINET International — added what process plants need: port profiles that define how power is delivered over the same pair, standardized as IEC TS 63444, and an intrinsic-safety concept called 2-WISE, published as IEC TS 60079-47.

The result: two wires, ten megabits per second in both directions, power and data together, trunks up to one kilometer, and intrinsically safe spurs that reach all the way into Zone 0.

## 03 · Our reference: CAN bus  `04:20`

Before we open up APL, let's set up our reference. CAN, the Controller Area Network, was presented by Bosch in 1986 to tame the growing tangle of wiring in cars. Today it's everywhere: vehicles, tractors, robots, medical devices.

Physically, CAN is one twisted pair, called CAN high and CAN low, running past every node. A 120-ohm resistor at each end matches the cable's characteristic impedance, so signals don't reflect.

CAN has two bus states. In the recessive state, nobody drives the bus: the termination resistors pull both wires to about two and a half volts, and the difference is zero. To send a dominant bit, a transceiver pushes CAN high up to about three and a half volts and pulls CAN low down to one and a half — a difference of about two volts. The receiver looks only at the difference. It's exactly like a differential-pressure transmitter, which ignores the static line pressure: interference that couples equally into both wires simply cancels out. APL, as we'll see, uses the very same trick.

Now the crucial property. Dominant always wins. If even one node drives a dominant zero, the bus is dominant, no matter how many others send a recessive one. Engineers call this a wired-AND, and CAN builds its entire access method on it.

Suppose three nodes start a frame at the same instant. Each one sends its eleven-bit identifier, bit by bit, while listening to the bus. At the fifth bit, the cabin-temperature node sends a recessive one, but reads back a dominant zero. Someone with a more important message is talking, so it stops immediately, and just listens. Three bits later, the engine-speed node loses the same way. The brake-pressure message, with the lowest identifier, wins — and its frame continues undamaged. No collision, no retransmission, no time lost. This is bitwise arbitration, and it's why CAN is so deterministic: the most important message always gets through first.

A classic CAN frame carries at most eight bytes of data, wrapped in nearly fifty bits of overhead: the identifier, control bits, a fifteen-bit CRC, an acknowledge slot, and an end-of-frame marker. After five identical bits, the transmitter inserts one opposite stuff bit, so the receivers never lose their clock.

Notice what's missing: there's no destination address. The identifier names the content, like “engine speed”, and every node decides for itself whether it cares.

But arbitration has a price, and it is paid in meters. For the wired-AND to work, a dominant bit from the far end of the bus must reach every node — and the transmitter must read back the result — before the bit is sampled. Signals travel about five nanoseconds per meter. So the round trip to the far end and back, plus the transceiver delays, has to fit inside a fraction of one bit. At one megabit per second, a bit lasts just one microsecond, which limits the bus to about forty meters. Want two hundred meters? Then slow down, so that every bit lasts long enough.

Plot the usual limits on logarithmic axes. Five hundred meters? 125 kilobits per second. A kilometer? About fifty. Bit rate times length is roughly constant: CAN trades speed for distance. That's also why CAN FD only accelerates the data phase. Once arbitration is over and a single node is talking, the round-trip constraint disappears.

## 04 · Inside Ethernet-APL  `08:07`

Now let's look at Ethernet-APL with the same eyes. First, topology. There is no shared bus. Every link connects exactly two ports, point to point, and switches tie the links together.

A typical plant uses a trunk-and-spur layout. In the safe area, an APL power switch connects to the plant network and feeds a trunk cable up to one kilometer long, carrying both data and power, with a 2.4-volt peak-to-peak signal. Out in the hazardous area, a field switch takes that power and distributes it over spurs up to two hundred meters long. Each spur serves exactly one instrument, with a lower one-volt signal and intrinsically safe power. And because every spur is its own link, every instrument gets its own ten megabits per second, in each direction, all the time. Nothing is shared, so there's nothing to arbitrate.

Wait — both directions at the same time, on one pair? In CAN, two transmitters driving the bus at once is exactly the conflict that arbitration resolves. In APL, it's the normal state. Both ends transmit continuously, and on the wire the two signals simply add up. So each receiver sees the far-end signal — weakened by up to about 25 dB after a kilometer of cable — buried under its own, much stronger transmission. The trick is that every transceiver knows exactly what it just sent. An adaptive digital filter — the echo canceller — learns how its own signal appears at its input, including reflections, and subtracts that copy. What remains is the far end. It's the same principle as noise-cancelling headphones.

So here is the deepest difference between the two physical layers. CAN uses a nonlinear medium, where dominant beats recessive, so that nodes can take turns. APL uses a linear medium plus signal processing, so that both ends can talk at once.

Next: how do you push ten megabits per second through a kilometer of cable originally designed for slow fieldbus signals? You keep the frequencies low. CAN uses two voltage levels: one bit per symbol. 10BASE-T1L uses three: plus, zero, and minus. This is called PAM-3.

The coder takes four data bits at a time and maps them onto three ternary symbols. Four bits have sixteen combinations; three ternary symbols have twenty-seven. The spare codes let the encoder choose, at every step, the pattern that keeps the average voltage at zero, so there's no DC drift — which matters, as we'll see in a moment.

Symbols are sent at 7.5 megabaud. Seven and a half million symbols per second, times four-thirds of a bit per symbol, is exactly ten megabits per second.

Because the data is scrambled first, the spectrum stays smooth, whatever you send. Most of the energy sits below the Nyquist frequency of 3.75 megahertz, where a kilometer of cable costs about 25 dB — a loss the receiver's equalizer can handle.

Power travels on the same two wires, and the trick is frequency, again. Power is direct current, at zero hertz. The data lives between roughly a hundred kilohertz and a few megahertz — and, thanks to the DC-free code, it contains no DC of its own.

So at each end of the cable, inductors pass the direct current to and from the power supply, but block the fast data, while capacitors pass the data to the transceiver, but block the DC. A mechanical engineer would recognize it immediately: a static load with a vibration riding on top, separated by a low-pass and a high-pass filter.

How much power? An APL power switch can feed a trunk with up to about ninety-two watts at the source. An instrument on an intrinsically safe spur gets roughly half a watt to one watt, depending on its power class. That sounds modest — but it's more than ten times the forty milliwatts or so that a four-to-twenty milliamp instrument has to live on.

## 05 · Intrinsic safety  `12:26`

Now the fourth wall: explosive atmospheres. An explosion needs three things: fuel, oxygen, and an ignition source. In a process plant, you can't always remove the first two.

Areas are classified into zones. Zone 0: an explosive atmosphere is present continuously or for long periods — inside a tank, for instance. Zone 1: likely in normal operation. Zone 2: not expected, and only briefly if it happens.

Intrinsic safety removes the ignition source. Voltage, current and power are limited — and so is the energy stored in the circuit's capacitance and inductance, one half C V squared and one half L I squared — so that even the spark from a broken wire or a short circuit stays below the minimum ignition energy of the gas. For hydrogen, that's only about twenty microjoules.

Protection level “i-a” means the circuit stays safe even with two simultaneous faults. That's what's required to enter Zone 0.

Traditionally, every intrinsically safe loop needed a calculation: does the source's voltage, current and power fit the device, and does the cable's capacitance and inductance fit what's left? 2-WISE replaces that with predefined port profiles. A 2-WISE field-switch port and a 2-WISE instrument with matching profiles are designed to be safe together, on up to two hundred meters of spur cable. You compare the labels, and you're done — much like FISCO did for fieldbus. CAN has no standardized plug-and-play equivalent: intrinsically safe CAN systems exist, but they're engineered case by case. For APL, intrinsic safety was a design goal from day one.

## 06 · Head to head  `14:16`

Let's put the two side by side. Bandwidth. On classic CAN, one megabit per second at most — and that's at forty meters — shared by every node on the bus. With ten nodes, each gets, on average, a tenth. On APL, every device has a private ten megabits per second, in each direction.

Distance. Back to our chart of bit rate versus cable length. CAN falls along that diagonal: double the length, halve the speed. 10BASE-T1L stays flat at ten megabits per second, all the way to a kilometer. Its speed-distance product is about two hundred times higher.

Frames. A CAN frame carries up to eight bytes, and names its content. An Ethernet frame carries up to fifteen hundred bytes, and names its destination and its source with MAC addresses — while IP addresses let it be routed across the whole plant network, or beyond.

What does that mean in practice? Take one megabyte — say, a firmware update, or a diagnostic log. Over HART: almost two hours. Over a fieldbus: about four minutes. Over CAN at one megabit per second: around fifteen seconds. Over Ethernet-APL: less than a second.

Power, and hazardous areas: CAN leaves both to the system designer. APL delivers power over the data pair, and it is intrinsically safe by design.

So is APL simply better? No. CAN is cheap: a CAN controller is built into countless microcontrollers, and its frames are tiny and efficient. Its arbitration gives hard, priority-based timing on short buses — exactly what vehicles and machines need. Ethernet-APL solves a different problem: long cables, hazardous areas, power over two wires, and rich data from every instrument — using the same IP-based networking as the rest of the enterprise.

## Summary  `16:19`

So, to sum up. CAN is a party line. Everyone shares one pair of wires, the most important voice always wins, and speed and distance trade off against each other. Ethernet-APL is a private line from every instrument: point to point, full duplex, ten megabits per second up to a kilometer, power and data on the same two wires, and intrinsically safe all the way into Zone 0.

The four walls are down. After decades of four to twenty milliamps, the process plant can finally speak the same language as the rest of the network — from the sensor, all the way to the cloud.

Thanks for watching.
