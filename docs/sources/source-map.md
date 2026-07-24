# Source Map

## Current primary sources

### Structured parts and retail pricing

- Unofficial PCPartPicker wrapper at [JonathanVusich/pcpartpicker](https://github.com/JonathanVusich/pcpartpicker)
- Documented supported regions include NZ and AU at [JonathanVusich/pcpartpicker](https://github.com/JonathanVusich/pcpartpicker)
- Documented supported part categories include CPU, motherboard, memory, video card, power supply, case, storage, and networking categories at [JonathanVusich/pcpartpicker](https://github.com/JonathanVusich/pcpartpicker)

### Benchmarks

- CPU aggregate benchmarks from [PassMark CPU Benchmarks](https://www.cpubenchmark.net)
- GPU aggregate benchmarks from [PassMark VideoCard Benchmarks](https://www.videocardbenchmark.net)
- Linux-native and automated benchmark execution from [phoronix-test-suite/phoronix-test-suite](https://github.com/phoronix-test-suite/phoronix-test-suite)

PassMark states that CPU charts reflect benchmark results, user submissions, and internal testing and are updated daily at [PassMark CPU Benchmarks](https://www.cpubenchmark.net).

### Linux compatibility

- Compatibility evidence from [Linux Hardware Database](https://linux-hardware.org)
- Probe-based operability and driver discovery from [linuxhw/hw-probe](https://github.com/linuxhw/hw-probe)

Linux Hardware Database states that it collects hardware details, helps check Linux compatibility, and helps find drivers across 334,512 tested computers and 579,366 tested parts at [linux-hardware.org](https://linux-hardware.org).

### Firmware and lifecycle

- Open firmware support tracking from [coreboot/coreboot](https://github.com/coreboot/coreboot)
- Firmware delivery ecosystem from [fwupd.org](https://fwupd.org)
- fwupd client and protocol support from [fwupd/fwupd](https://github.com/fwupd/fwupd)

LVFS documents that vendors upload redistributable firmware packages and Linux metadata for fwupd consumption at [fwupd.org](https://fwupd.org).

### Used-market pricing

- NZ used-market source: [Trade Me components](https://www.trademe.co.nz/a/marketplace/computers/components)
- Example search source: [Trade Me RTX 3060](https://www.trademe.co.nz/a/marketplace/s/rtx-3060/k2c0-2)

## Source classes and trust order

1. Official vendor specs and manuals
2. Vendor firmware and support pages
3. Structured aggregator data
4. Benchmark databases
5. Linux field-evidence databases
6. Marketplace listings
7. Community issue trackers and forums

## Known limitations

- The PCPartPicker wrapper is unofficial and relatively old, so schema drift risk should be assumed.
- Marketplace pricing is noisy and often needs normalization by condition and shipping.
- New platforms may lack sufficient Linux field evidence early in their lifecycle.
- Shipping-to-NZ estimates may require browser-assisted collection for AU sources.
