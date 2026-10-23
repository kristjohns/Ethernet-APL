# Transcript — Ethernet-APL, a deep dive — from the volts on the wire to the plant network (and how it differs from CAN bus)

_Generated from the narration that is rendered into the video._

## Intro  `00:00`

Somewhere in a chemical plant, a radar level transmitter watches the surface of a liquid, twenty meters below. It knows the full echo profile, its own electronics temperature, the condition of its antenna, and weeks of trends. And it reports — one number. A current between four and twenty milliamps, on two wires. If you're lucky, a trickle of digital data rides along at 1,200 bits per second — the speed of an early telephone modem. Meanwhile, a few hundred meters away, the office network moves a billion bits per second — almost a million times more.

This video is about the technology that finally brings Ethernet all the way out to the instrument: Ethernet-APL.

We'll take it apart all the way down: how a bit becomes a voltage, how that voltage travels through a kilometer of copper, and how the far end pulls it back out of the noise — with a good dose of history along the way. And as a reference point, we'll use a network that many engineers already know from vehicles and machines: CAN bus.

## 01 · The last kilometer  `01:07`

Process instruments have spoken the same basic language for decades. The 4–20 mA loop is brilliantly simple: two wires, one analog value, and the same two wires power the instrument. Four milliamps, not zero, means zero percent — so a broken wire is instantly obvious.

In the 1980s, HART added digital communication by superimposing a small tone on that current: 1,200 hertz for a one, 2,200 hertz for a zero. Because the tone averages to zero, the analog value is untouched — but the data rate is only 1,200 bits per second.

In the 1990s, fieldbuses such as FOUNDATION Fieldbus H1 and PROFIBUS PA went fully digital, at 31.25 kilobits per second — shared by every device on the segment.

Meanwhile, the rest of industry moved to Ethernet, at a hundred megabits per second and more. On a logarithmic scale, the gap is enormous.

So why didn't plain Ethernet simply run out into the plant? Four walls stood in the way. Distance. Standard 100BASE-TX Ethernet is limited to one hundred meters per link, while field cables run for hundreds of meters — sometimes a kilometer or more. Wires. Office Ethernet needs two or four pairs; plants are full of installed two-wire cable. Power. A field instrument has no local supply. It must be powered over the same two wires that carry its signal. And explosion protection. In hazardous areas, the energy in a circuit must be limited, so that not even a fault can ignite the atmosphere. Ordinary Ethernet was never designed for that. Ethernet-APL — the Advanced Physical Layer — was designed to break all four walls. The key word is “physical”.

## 02 · One new layer  `03:05`

APL replaces only the bottom layer of the network stack: the copper, the voltages, the power, and the safety rules. Everything above it is unchanged Ethernet: the same frames and MAC addresses, IP, TCP and UDP, and the industrial protocols on top — PROFINET, EtherNet/IP, HART-IP, OPC UA, Modbus TCP — even a web server inside the instrument.

Its foundation is 10BASE-T1L, part of the IEEE 802.3cg standard from 2019: ten megabits per second, full duplex, over a single twisted pair, for up to a kilometer. On top of that, the APL project — a joint effort of FieldComm Group, ODVA, the OPC Foundation, and PROFIBUS and PROFINET International — added what process plants need: port profiles that define how power is delivered over the same pair, standardized as IEC TS 63444, and an intrinsic-safety concept called 2-WISE, published as IEC TS 60079-47.

The result: two wires, ten megabits per second in both directions, power and data together, trunks up to one kilometer, and intrinsically safe spurs that reach all the way into Zone 0.

## 03 · Our reference: CAN bus  `04:29`

Before we open up APL, let's set up our reference. CAN, the Controller Area Network, was presented by Bosch in 1986 to tame the growing tangle of wiring in cars. Today it's everywhere: vehicles, tractors, robots, medical devices.

Physically, CAN is one twisted pair, called CAN high and CAN low, running past every node. A 120-ohm resistor at each end matches the cable's characteristic impedance, so signals don't reflect.

CAN has two bus states. In the recessive state, nobody drives the bus: the termination resistors pull both wires to about two and a half volts, and the difference is zero. To send a dominant bit, a transceiver pushes CAN high up to about three and a half volts and pulls CAN low down to one and a half — a difference of about two volts. The receiver looks only at the difference. It's exactly like a differential-pressure transmitter, which ignores the static line pressure: interference that couples equally into both wires simply cancels out. APL, as we'll see, uses the very same trick.

Now the crucial property. Dominant always wins. If even one node drives a dominant zero, the bus is dominant, no matter how many others send a recessive one. Engineers call this a wired-AND, and CAN builds its entire access method on it.

Suppose three nodes start a frame at the same instant. Each one sends its eleven-bit identifier, bit by bit, while listening to the bus. At the fifth bit, the cabin-temperature node sends a recessive one, but reads back a dominant zero. Someone with a more important message is talking, so it stops immediately, and just listens. Three bits later, the engine-speed node loses the same way. The brake-pressure message, with the lowest identifier, wins — and its frame continues undamaged. No collision, no retransmission, no time lost. This is bitwise arbitration, and it's why CAN is so deterministic: the most important message always gets through first.

A classic CAN frame carries at most eight bytes of data, wrapped in nearly fifty bits of overhead: the identifier, control bits, a fifteen-bit CRC, an acknowledge slot, and an end-of-frame marker. After five identical bits, the transmitter inserts one opposite stuff bit, so the receivers never lose their clock.

Notice what's missing: there's no destination address. The identifier names the content, like “engine speed”, and every node decides for itself whether it cares.

But arbitration has a price, and it is paid in meters. For the wired-AND to work, a dominant bit from the far end of the bus must reach every node — and the transmitter must read back the result — before the bit is sampled. Signals travel about five nanoseconds per meter. So the round trip to the far end and back, plus the transceiver delays, has to fit inside a fraction of one bit. At one megabit per second, a bit lasts just one microsecond, which limits the bus to about forty meters. Want two hundred meters? Then slow down, so that every bit lasts long enough.

Plot the usual limits on logarithmic axes. Five hundred meters? 125 kilobits per second. A kilometer? About fifty. Bit rate times length is roughly constant: CAN trades speed for distance. That's also why CAN FD only accelerates the data phase. Once arbitration is over and a single node is talking, the round-trip constraint disappears.

One more detail of CAN's physical layer will matter later. There is no clock wire. So how does a receiver know where one bit ends and the next begins? Each node divides the bit time into small time quanta, counted from its own crystal oscillator. A bit consists of four segments: a synchronization segment, where an edge is expected; a propagation segment, which absorbs the round-trip delay we just met; and two phase segments. The bus is sampled between the two phase segments — typically somewhere between seventy-five and eighty-seven and a half percent of the bit.

Every frame begins with a hard synchronization on the very first recessive-to-dominant edge: the start of frame. After that, whenever a recessive-to-dominant edge arrives a little early or late, the receiver stretches phase segment one, or shortens phase segment two, by a few quanta, and realigns. And that's the real reason for bit stuffing: after five identical bits there must be an edge, so the oscillators can never drift apart for long. Keep this picture in mind. CAN recovers its timing from occasional edges. APL will need something far finer.

## 04 · From coax to one pair  `09:29`

Ethernet itself started out as a party line, not so different from CAN. In 1973, at Xerox PARC, Bob Metcalfe sketched a network in which every computer tapped into one shared coaxial cable: the 'ether'. Before sending, a station listened. If two started at the same moment, their signals collided, and both backed off and tried again later: carrier sense, multiple access, with collision detection.

And it carried the very same physical constraint as CAN. A sender must still be transmitting when the news of a collision returns from the far end of the cable. That's why classic Ethernet frames have a minimum length of sixty-four bytes: 512 bits, or 51.2 microseconds at ten megabits per second — enough to cover the round trip of a network a few kilometers across, repeaters included. CAN pays for the round trip in every single bit; early Ethernet paid for it once per frame.

Then Ethernet escaped. Twisted-pair cabling arrived in 1990, first with hubs, then with switches. Each cable now connected exactly two devices, and with full duplex, standardized in the late 1990s, collisions became impossible. With nothing to detect, the round-trip constraint simply vanished. From then on, the length of a link is limited by one thing only: how well a signal survives the cable.

That turned Ethernet into a story of ever cleverer physical layers. Manchester code over two pairs in 1990. Three-level MLT-3 for a hundred megabits in 1995. Five levels, echo cancellation and four pairs for gigabit Ethernet in 1999. In 2015, a single pair for cars. And in 2019, 10BASE-T1L applied the whole toolbox to a different goal: not speed, but distance.

Now let's look at Ethernet-APL with the same eyes. First, topology. There is no shared bus. Every link connects exactly two ports, point to point, and switches tie the links together.

A typical plant uses a trunk-and-spur layout. In the safe area, an APL power switch connects to the plant network and feeds a trunk cable up to one kilometer long, carrying both data and power, with a 2.4-volt peak-to-peak signal. Out in the hazardous area, a field switch takes that power and distributes it over spurs up to two hundred meters long. Each spur serves exactly one instrument, with a lower one-volt signal and intrinsically safe power. And because every spur is its own link, every instrument gets its own ten megabits per second, in each direction, all the time. Nothing is shared, so there's nothing to arbitrate.

From here on, we'll follow a single bit through the physical layer. A transmitter turns bits into voltages. A kilometer of twisted pair carries them — and mangles them on the way. And a receiver turns whatever arrives back into bits. We'll start in the middle, with the wire itself.

## 05 · The wire is a waveguide  `12:42`

In the summer of 1858, the first telegraph cable across the Atlantic went into service, from Ireland to Newfoundland. It was a triumph — and a disappointment. A crisp pulse sent at one end arrived at the other smeared out over seconds. Queen Victoria's ninety-eight-word greeting took most of a day to get through.

A few years earlier, William Thomson — later Lord Kelvin — had worked out why. He modelled the cable as a resistance and a capacitance per meter. The copper core, its gutta-percha insulation and the sea around it form one enormous capacitor, and every piece of it must be charged through the resistance of the copper before it. What comes out is exactly the equation Fourier had written for heat.

So a voltage step doesn't run down such a cable. It soaks in, the way heat creeps along a metal bar that's held in a flame at one end: quickly near the source, and ever more slowly further along.

At the far end, a short pulse shows up as a slow, low hump. Its peak arrives after a time proportional to R C x squared. Double the length, and the signal takes four times as long, and arrives four times weaker. That's Kelvin's law of squares.

The cable's chief electrician, Wildman Whitehouse, dismissed the theory as 'a fiction of the schools'. He tried to force the signals through with induction coils of around two thousand volts. Within weeks the insulation broke down, and the cable fell silent.

The cable of 1866 was far better built, and it worked — read with Kelvin's mirror galvanometer, which needs only a minute current. A tiny current twists a tiny mirror, and a beam of light turns that twist into a big swing of a spot across a scale.

The full picture came from Oliver Heaviside, a self-taught telegraph engineer, in the 1880s. He added what Kelvin had left out: the inductance — the magnetic inertia of the current — and the leakage through the insulation. His telegrapher's equations describe one short slice of line. At low frequencies, resistance wins and you get Kelvin's diffusion. But once omega L is much larger than R, the equations turn into the wave equation — the same one d'Alembert solved for a vibrating string in 1747. Its solutions are shapes that travel, unchanged, in both directions, at a speed of one over the square root of L C.

Side by side: in a resistance-capacitance line, a pulse spreads out and sinks away. In an inductance-capacitance line, the same pulse simply travels, keeping its shape.

For APL's fieldbus cable, resistance and inductive reactance are equal at around thirteen kilohertz. Below that lies Kelvin's world of diffusion. That's where HART's tones live — which is why HART's cable rules are written as a maximum R C time constant. Above it lies Heaviside's world of waves. APL's signals sit between about a hundred kilohertz and a few megahertz: firmly in the world of waves. So let's look at those waves.

If the wave equation feels abstract, picture a chain of masses joined by springs. Give the first mass a shove, and a compression pulse runs down the chain. A transmission line is the very same system. Inductance plays the role of mass: it resists any change in current, as mass resists any change in velocity. Capacitance plays the role of the springs: it stores energy as the voltage builds up. Voltage is the force; current is the velocity.

The wave speed follows directly: one over the square root of L C — just as a string's wave speed is the square root of tension over mass per length. For APL's fieldbus cable, about half a microhenry and fifty picofarads per meter give two hundred thousand kilometers per second: two-thirds of the speed of light, or five nanoseconds per meter.

So a kilometer of cable is five microseconds long. That's thirty-seven and a half APL symbols in flight, in each direction, at every moment. The cable isn't a wire that connects two points instantly. It's a conveyor belt.

A travelling wave carries voltage and current in a fixed ratio: the characteristic impedance, Z-naught. Here's why. As the edge advances, every second it charges another c meters of cable capacitance to the voltage V. That takes a current I equals C c V. So V over I is one over C c, which works out to the square root of L over C. For our cable: a hundred ohms. You can't measure it with an ohmmeter. It's the load a fast edge sees, because the edge only knows about the cable it has already charged.

If you've ever heard water hammer in a pipe, you've met the same idea. Slam a valve shut, and the pressure jumps by rho times a times delta v — Joukowsky's equation — and that pressure wave runs back up the pipe at the speed of sound. It's exactly V equals Z-naught times I.

What happens when the wave reaches the end of the line? The mismatch decides. The reflection coefficient is gamma equals Z L minus Z-naught, over Z L plus Z-naught. At an open end, no current can flow, so the wave reflects with the same sign — like a string with a free end. At a short circuit, the voltage must be zero, so the wave comes back inverted — like a string tied to a wall. Terminate the line with a resistor exactly equal to Z-naught, and nothing comes back at all. The resistor swallows the wave as if the cable went on forever. Mechanically, it's a dashpot tuned to the chain's impedance.

That's what CAN's 120-ohm terminators do at both ends of its bus. In APL, every link has exactly two ends, and each transceiver terminates its own end with a hundred ohms. Still, no real cable is perfect. Connectors, splices and manufacturing tolerances each reflect a small echo back towards the sender. Remember those echoes — the receiver will have to deal with them.

So far, our waves have travelled without loss. Real cables lose energy in two ways. Current flowing through the copper heats it: that's the series resistance, R. And the insulation absorbs a little energy from the alternating electric field between the wires: that's the shunt conductance, G. On a low-loss line, every meter takes away the same fraction of the wave, so the amplitude decays exponentially — e to the minus alpha x, with alpha about R over two Z-naught, plus G times Z-naught over two.

But R is not the DC resistance. At high frequencies, the current crowds towards the surface of the conductor: the skin effect. You know the same phenomenon from the ground beneath your feet. The daily temperature swing at the surface fades within a few tens of centimeters of soil; only the slow seasonal swing reaches meters deep. Fast changes only penetrate a thin layer. For the current in a wire, it's the same diffusion equation, and the penetration depth is delta equals the square root of two rho over omega mu. For copper at 3.75 megahertz, delta is just thirty-four micrometers. An 18-gauge conductor is a millimeter thick, so most of the copper sits idle: the resistance is almost eight times its DC value, and it keeps growing with the square root of frequency.

Add the dielectric losses, which grow in proportion to frequency, and you get the classic cable-loss curve: a square-root term plus a linear term. The standard allows up to about 25.6 dB of loss at 3.75 megahertz, over a one-kilometer link. In amplitude, that's a factor of nineteen. And the loss keeps climbing with frequency. Low frequencies get through; high frequencies are stripped away. The cable is a low-pass filter, one kilometer long.

Now send a single, crisp symbol into a kilometer of this cable. What comes out is lower, rounder and later — and it drags a long tail behind it that lasts for dozens of symbol periods. Send a stream of symbols, and every symbol's tail spills into the decisions about its neighbors. That's intersymbol interference. Mathematically, the received signal is a convolution: each symbol's response, shifted by one symbol period and scaled by the symbol's value, all added up.

Overlay every symbol period of the received waveform, and you get an eye diagram. Sent, it shows three clean levels. After a kilometer of cable, the eye is closed: from the raw voltage alone, plus, zero and minus can no longer be told apart. Prying that eye open again is the receiver's job. We'll get there.

One more enemy comes from outside: interference. A motor cable nearby produces a changing magnetic field. If our two wires ran side by side, they would form one long loop, and by Faraday's law that changing field would induce a voltage around it. Twist the wires, and the loop becomes a chain of small loops with alternating orientation. The voltages induced in neighbouring loops cancel. Whatever is left appears equally on both wires — common mode — and the differential receiver ignores it, just like CAN's. And the shield around the pair takes care of electric fields.

We know what the wire does to a signal. Now, on to the transmitter: how should bits become voltages?

## 06 · From bits to symbols  `22:36`

Given a cable like this, how fast can we signal? Engineers at Bell Labs asked exactly that about telegraph and telephone lines in the 1920s. In 1928, Harry Nyquist showed that a channel with a bandwidth of B hertz can carry at most two B independent pulses per second. The ideal pulse is the sinc function. It rings — but its ringing passes through zero at exactly every other pulse's sampling instant. Line them up, one symbol apart, sample at the right moments, and each sample sees only its own pulse. No interference, in a channel only half as wide as the symbol rate. For APL, 7.5 million symbols per second need at least 3.75 megahertz of bandwidth. That's the Nyquist frequency we keep meeting.

The same year, Ralph Hartley, also at Bell Labs, added the second dimension. If each pulse can take one of M distinguishable levels, it carries log two of M bits. Two levels: one bit. Four levels: two bits. Three levels: about one and a half. So the bit rate is two B times log two M — and apparently there's no limit, if you just use enough levels.

The catch is noise: levels packed too closely can no longer be told apart. In 1948, Claude Shannon settled the question for good. The capacity of a channel is C equals B times log two of one plus the signal-to-noise ratio. Below that rate, error-free communication is possible, with clever enough coding. Above it, it's impossible. So the designer has two knobs. The symbol rate costs bandwidth — and on our cable, bandwidth means loss. The number of levels costs signal-to-noise ratio. Let's see how 10BASE-T1L sets those two knobs.

Let's turn those knobs for ten megabits per second. The original twisted-pair Ethernet, 10BASE-T, used Manchester code: every bit is a transition in the middle of its bit period — up for a one, down for a zero. It's robust, and it carries its own clock. But it can need two transitions per bit, so its energy sits between about five and ten megahertz. On a kilometer of cable, that costs thirty to forty-five dB. Far too much.

Now compare the options for ten megabits per second, by the frequency they need and the loss at that frequency. Two levels at ten megabaud: Nyquist at five megahertz, and thirty dB of loss. Three levels at 7.5 megabaud: 3.75 megahertz, and 25.6 dB. Four levels at five megabaud: 2.5 megahertz, about twenty dB — but now the levels are packed closer together, so every dB saved in the cable is paid for in noise margin. 10BASE-T1L chose three levels: a compromise between cable loss, emissions and noise margin — combined with a code that keeps the signal free of DC.

The code is called 4B3T: four bits in, three ternary symbols out. Four bits have sixteen combinations; three ternary symbols have twenty-seven. And seven and a half million symbols per second, times four-thirds of a bit each, is exactly ten megabits per second.

The spare combinations buy something valuable. Many triplets have a non-zero sum, like plus, plus, zero. So each group of four bits gets two possible codes, mirror images of each other, and the encoder keeps a running sum of everything it has sent. When the sum is positive, it picks the version that pulls it back down, and vice versa. The running sum stays bounded, so the signal's average is zero. The idea isn't new: a 4B3T code carried ISDN over ordinary telephone pairs in the 1980s — also full duplex, with echo cancellation, over several kilometers.

Why does DC matter so much? Because the data path is AC-coupled. Capacitors and transformers — and, as we'll see, the network that lets power share the pair — block DC. Electrically, that's a high-pass filter. Feed it a signal with a DC component, and the output slowly drifts — baseline wander — until the levels no longer sit where the receiver's thresholds expect them. With a balanced code, there's nothing to drift. The baseline stays put.

One step comes before the coding: scrambling. Real data is anything but random: long runs of zeros, idle patterns, repeated headers. Sent as they are, they turn into periodic signals with strong spectral lines — tones that radiate and interfere — and long, monotonous stretches that tell the receiver nothing about timing.

So the transmitter mixes every bit with a pseudo-random sequence from a linear-feedback shift register: thirty-three flip-flops in a row, with two taps fed back through an exclusive-or gate. Each data bit is exclusive-or'ed with the register's output. The receiver runs an identical register in step, and applies the same exclusive-or — which restores the data exactly, because anything exclusive-or'ed twice with the same bit is unchanged. With this feedback polynomial, the sequence only repeats after two to the thirty-three, minus one bits: about a quarter of an hour at ten megabits per second. The result: whatever the data, the line signal looks like noise — a smooth spectrum with no tones, and plenty of transitions for the receiver's clock.

And one subtle detail. The two ends of a link use different polynomials: one plus x to the thirteen plus x to the thirty-three for the master, and its mirror image, with x to the twenty, for the slave. That makes the two directions statistically independent. Keep that in mind: the echo canceller will depend on it.

So here's the complete transmitter. Bits from the Ethernet MAC are scrambled, grouped in fours, and mapped onto ternary triplets. A digital-to-analog converter turns each symbol into one of three voltages, and a filter rounds off the edges to keep emissions low. Finally, a line driver with a hundred-ohm source impedance launches the wave into the cable: plus or minus 1.2 volts on a trunk, or plus or minus half a volt on an intrinsically safe spur.

Our symbols are on the wire. But the far end is transmitting too — at the same time, on the same two wires.

## 07 · Two directions, one pair  `29:17`

How can that possibly work? Because the cable is linear. Two waves travelling in opposite directions simply pass through each other. The voltage anywhere on the line is just their sum: v-plus of x minus c t, plus v-minus of x plus c t — d'Alembert's solution again. On a CAN bus, two transmitters at once means a contest between states, settled by arbitration. On a linear line, it's just addition.

Telephones have relied on this for well over a century. Your voice and the caller's voice share one pair of wires, and a circuit called a hybrid separates them, so that you hear the far end — and only a little of yourself. Long-distance lines with amplifiers split the two directions onto four wires. The hybrids at the ends were never perfectly balanced, so a little of your voice leaked back into the return path — which is why long-distance calls used to come with an echo.

Inside an APL transceiver, the hybrid works like this. The transmitter drives the line through a source resistance equal to the cable's hundred ohms. With the line matched, the voltage at the terminals is half of the transmitter's voltage — plus whatever arrives from the far end. A replica network, built from the same resistor and a model of the line's impedance, produces a copy of just that half. Subtract the two, and ideally your own signal vanishes, leaving only the far end. In reality, the cable's impedance isn't exactly a hundred ohms at every frequency, and every connector and splice reflects a little echo. So the analog hybrid removes a good part of the echo — but nowhere near enough.

How much is enough? Our own signal leaves at 2.4 volts peak to peak. The far end's signal arrives up to 25.6 dB weaker: about an eighth of a volt. To tell plus, zero and minus apart reliably, the receiver needs about 20 dB of signal-to-noise ratio, plus some margin. So the leftover echo has to end up around fifty dB below our own transmission — a factor of about three hundred in amplitude. Across all cables, lengths and temperatures, no fixed analog circuit can manage that on its own.

The rest of the job is done digitally, by the echo canceller. Its secret weapon: the transceiver knows exactly which symbols it has sent. The echo it receives is those symbols, convolved with the echo path's impulse response: first the leakage through the hybrid, then the small reflections from connectors and splices, arriving later — up to a full round trip, ten microseconds for a kilometer of cable.

So the canceller is a finite-impulse-response filter: a delay line that holds the most recently sent symbols — enough of them to span the whole round trip. Each one is multiplied by a weight, and everything is summed. That sum is an estimate of the echo, and it's subtracted from the received signal. And because the symbols are only plus one, zero or minus one, those multiplications come for free: add the weight, skip it, or subtract it.

How does it find the weights? It watches the error — whatever is left after the subtraction — and after every symbol, it nudges every weight a little: weight k changes by mu, times the error, times the symbol that sat at tap k. That's the least-mean-squares algorithm, published by Bernard Widrow and Ted Hoff at Stanford in 1960. It is gradient descent on the squared error, one tiny step per symbol. If you know the MIT rule from adaptive control, you've met its close cousin. Watch the weights take on the shape of the echo path, while the residual echo melts away. And because it never stops adapting, the canceller follows the cable as it warms up in the sun and cools down at night.

Now the scrambler detail pays off. The canceller learns by correlating the error with its own symbols. If the far end's symbols were correlated with ours, that second term wouldn't vanish, and the canceller would start cancelling part of the far-end signal too. With different scramblers in each direction, the two streams are statistically independent. The only thing the canceller can learn is its own echo.

Adaptive echo cancellers were developed at Bell Labs in the 1960s for satellite telephone calls, where the trip up to a geostationary satellite and back makes echoes return more than half a second late. Two decades later, they put full-duplex digital data onto ordinary telephone pairs, in ISDN. In 1999, gigabit Ethernet ran four echo-cancelled pairs at once; in 2015, a single pair for cars. APL's transceivers are their direct descendants.

And so we arrive at the deepest difference between the two physical layers. CAN uses a nonlinear medium, where dominant beats recessive, so that nodes can take turns. APL uses a linear medium plus signal processing, so that both ends can talk at once.

With its own echo removed, the receiver is left with the far end's signal — weak, smeared, and with a closed eye. Time to open it.

## 08 · Inside the receiver  `34:40`

Here's the whole receive path. An amplifier with automatic gain control, and an analog-to-digital converter. Then, all in the digital domain: the echo canceller, the equalizer, the decision, and finally the descrambler and the 4B3T decoder. Two feedback loops complete the picture: decision feedback, which we'll meet in a moment, and clock recovery, which decides when to sample.

Look again at one symbol's response after the cable, but now sampled once per symbol, the way the receiver sees it. One sample is the largest: the main cursor. Before it sits a small pre-cursor; after it, a long series of post-cursors: the tail. Every one of those samples lands in some other symbol's decision.

A feed-forward equalizer is another FIR filter, this time on the received samples. Its weights approximate the inverse of the cable: it boosts the high frequencies that the cable stripped away, so that the two together are flat again. The catch: boosting high frequencies also boosts the noise up there.

So the long tail is handled differently. Look at what one received sample is made of: a little of the current symbol, plus the tails of all the symbols before it. Here, the tails add up to far more than the symbol itself — so a raw decision would be wrong. But the receiver has already decided those earlier symbols, so it knows their tails exactly. The decision-feedback equalizer simply subtracts them. What's left is the current symbol. In one line: y-n is the filtered sample, minus the sum of b-j times the previous decisions. No noise gets amplified, because past decisions are clean numbers. The price: a wrong decision subtracts the wrong tail, so one error can drag a few more along with it.

Adaptive equalizers like these were pioneered by Robert Lucky at Bell Labs in 1965, to push data through telephone lines. Like the echo canceller, they adapt continuously, with the same least-mean-squares rule. Watch the eye open.

After the equalizer, the decision itself is beautifully simple: a slicer with two thresholds, halfway between the levels. Above the upper threshold: plus one. Below the lower one: minus one. In between: zero. But noise smears each level into a bell curve. An error happens whenever a sample strays past a threshold: the area in the tail of the bell curve, given by the Gaussian Q-function. For an error rate of one in a billion, each threshold must sit about six standard deviations away from its level — so neighbouring levels must be twelve sigma apart. That's a signal-to-noise ratio of about 20 dB at the slicer. That number is what the whole design is built around. Every dB the cable takes, every trace of residual echo, every pickup from a nearby motor eats into it. And 10BASE-T1L has no forward error correction to fall back on: the margin is the error correction.

One question remains: when exactly to sample? There's no clock wire, and the two ends run on separate crystal oscillators, a few millionths apart. So the receiver recovers the clock from the signal itself, with a phase-locked loop. A timing detector compares samples with decisions, and estimates whether the receiver is sampling early or late. That error drives a proportional-integral controller, which steers a numerically controlled oscillator — the receiver's sense of time. You know this loop from control theory. The oscillator integrates frequency into phase; the integral term removes the steady frequency offset between the crystals; the proportional term keeps the loop stable and well damped. Within a few thousand symbols, the sampling instant settles in the middle of the eye, and stays there. Compare that with CAN, which nudges its bit timing on occasional edges, by whole time quanta. APL's receiver tracks the phase continuously, to a small fraction of a symbol.

And there's one more twist. The slave doesn't transmit on its own crystal: it sends using the clock it recovered from the master. Both directions then tick in lockstep — which is exactly what the echo canceller needs, because its own echo and the far end's symbols now share the same time grid.

All of this has to come alive within moments of plugging in a cable. First, the two ends exchange a few slow, simple messages: auto-negotiation. Using a robust low-speed code, they agree on the transmit amplitude — 2.4 or 1 volt peak to peak — and on which end will be master, and which slave.

Then training begins. The master sends a scrambled stream of idle symbols, while the slave stays silent. The slave's receiver locks its clock to the master, trains its equalizer, and synchronizes its descrambler. Only then does the slave start transmitting — on the master's clock. Now the master trains its own receiver, and both sides fine-tune their echo cancellers. When both ends report that their receivers are happy, the link is up, and Ethernet frames can flow.

Let's follow one bit from end to end. It's scrambled, grouped with three others, and turned into three ternary symbols. A voltage step launches a wave into the cable, which carries it at two-thirds of the speed of light, strips away about ninety-five percent of its amplitude, and smears it across its neighbors — all while a wave travelling the other way passes straight through it. At the far end, the receiver subtracts its own echo, undoes the smearing, picks the right instant to sample, decides plus, zero or minus, and decodes and descrambles. Five microseconds and a few clever filters later, the bit is back — with fewer than one error in a billion.

## 09 · Power on the same pair  `40:44`

Power travels on the same two wires, and the trick is frequency, again. Power is direct current, at zero hertz. The data lives between roughly a hundred kilohertz and a few megahertz — and, thanks to the DC-free code, it contains no DC of its own.

So at each end of the cable, inductors pass the direct current to and from the power supply, but block the fast data, while capacitors pass the data to the transceiver, but block the DC. A mechanical engineer would recognize it immediately: a static load with a vibration riding on top, separated by a low-pass and a high-pass filter. Some numbers make it concrete. In a typical design, at 3.75 megahertz, a 220-microhenry inductor has an impedance of about five kilohms — fifty times the line's hundred ohms, so it barely loads the signal. A 220-nanofarad capacitor, at the same frequency, is just a fifth of an ohm. At DC, it's exactly the other way round.

Why does the trunk run at up to fifty volts? Because the cable's resistance burns I squared R. Deliver the same power at twice the voltage, and the current halves — so the loss drops to a quarter. And there's a hard ceiling. With a source voltage V and a loop resistance R, the most power that can ever reach the far end is V squared over four R — and only at fifty percent efficiency. So a long, powerful trunk needs both: voltage, and copper.

How much power? An APL power switch can feed a trunk with up to about ninety-two watts at the source. An instrument on an intrinsically safe spur gets roughly half a watt to one watt, depending on its power class. That sounds modest — but it's more than ten times the forty milliwatts or so that a four-to-twenty milliamp instrument has to live on.

## 10 · Intrinsic safety  `42:44`

Now the fourth wall: explosive atmospheres. An explosion needs three things: fuel, oxygen, and an ignition source. In a process plant, you can't always remove the first two.

Areas are classified into zones. Zone 0: an explosive atmosphere is present continuously or for long periods — inside a tank, for instance. Zone 1: likely in normal operation. Zone 2: not expected, and only briefly if it happens.

Intrinsic safety removes the ignition source. Voltage, current and power are limited — and so is the energy stored in the circuit's capacitance and inductance, one half C V squared and one half L I squared — so that even the spark from a broken wire or a short circuit stays below the minimum ignition energy of the gas. For hydrogen, that's only about twenty microjoules.

Protection level “i-a” means the circuit stays safe even with two simultaneous faults. That's what's required to enter Zone 0.

Traditionally, every intrinsically safe loop needed a calculation: does the source's voltage, current and power fit the device, and does the cable's capacitance and inductance fit what's left? 2-WISE replaces that with predefined port profiles. A 2-WISE field-switch port and a 2-WISE instrument with matching profiles are designed to be safe together, on up to two hundred meters of spur cable. You compare the labels, and you're done — much like FISCO did for fieldbus. CAN has no standardized plug-and-play equivalent: intrinsically safe CAN systems exist, but they're engineered case by case. For APL, intrinsic safety was a design goal from day one.

## 11 · Head to head  `44:34`

Let's put the two side by side. Bandwidth. On classic CAN, one megabit per second at most — and that's at forty meters — shared by every node on the bus. With ten nodes, each gets, on average, a tenth. On APL, every device has a private ten megabits per second, in each direction.

Distance. Back to our chart of bit rate versus cable length. CAN falls along that diagonal: double the length, halve the speed. 10BASE-T1L stays flat at ten megabits per second, all the way to a kilometer. Its speed-distance product is about two hundred times higher.

Frames. A CAN frame carries up to eight bytes, and names its content. An Ethernet frame carries up to fifteen hundred bytes, and names its destination and its source with MAC addresses — while IP addresses let it be routed across the whole plant network, or beyond.

What does that mean in practice? Take one megabyte — say, a firmware update, or a diagnostic log. Over HART: almost two hours. Over a fieldbus: about four minutes. Over CAN at one megabit per second: around fifteen seconds. Over Ethernet-APL: less than a second.

Power, and hazardous areas: CAN leaves both to the system designer. APL delivers power over the data pair, and it is intrinsically safe by design.

And underneath, the two physical layers could hardly be more different. CAN: two levels, bit stuffing, timing from occasional edges, a nonlinear wired-AND, and no signal processing at all. APL: three levels, scrambled and 4B3T-coded, a phase-locked clock, a linear line with echo cancellation, and adaptive equalization.

So is APL simply better? No. CAN is cheap: a CAN controller is built into countless microcontrollers, and its frames are tiny and efficient. Its arbitration gives hard, priority-based timing on short buses — exactly what vehicles and machines need. Ethernet-APL solves a different problem: long cables, hazardous areas, power over two wires, and rich data from every instrument — using the same IP-based networking as the rest of the enterprise.

## Summary  `47:00`

So, to sum up. CAN is a party line. Everyone shares one pair of wires, the most important voice always wins, and speed and distance trade off against each other. Ethernet-APL is a private line from every instrument: point to point, full duplex, ten megabits per second up to a kilometer, power and data on the same two wires, and intrinsically safe all the way into Zone 0.

And underneath that private line sits more than a century of ideas: Heaviside's waves, Nyquist's and Shannon's limits, the telephone hybrid, Widrow and Hoff's adaptive filters, Lucky's equalizers. All of it packed into a transceiver chip that runs on well under a tenth of a watt.

The four walls are down. After decades of four to twenty milliamps, the process plant can finally speak the same language as the rest of the network — from the sensor, all the way to the cloud.

Thanks for watching.
