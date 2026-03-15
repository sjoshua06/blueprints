FEATURE_SCHEMAS = {

    "regulator": [
        "output_voltage",
        "input_voltage_max",
        "output_current",
        "dropout_voltage"
    ],

    "LDO regulator": [
        "output_voltage",
        "input_voltage_max",
        "output_current",
        "dropout_voltage"
    ],

    "resistor": [
        "resistance",
        "tolerance",
        "power_rating",
        "temperature"
    ],

    "capacitor": [
        "capacitance",
        "voltage_rating",
        "tolerance",
        "temperature"
    ],

    "inductor": [
        "inductance",
        "current_rating",
        "dc_resistance",
        "saturation_current"
    ],

    "WiFi module": [
        "frequency",
        "tx_power",
        "interface",
        "voltage"
    ],

    "USB bridge": [
        "protocol",
        "data_rate",
        "interface",
        "voltage"
    ],

    "IMU sensor": [
        "acc_range",
        "gyro_range",
        "interface",
        "voltage"
    ],

    "env sensor": [
        "temperature_range",
        "humidity_range",
        "interface",
        "voltage"
    ],

    "level shifter": [
        "voltage_low",
        "voltage_high",
        "channels"
    ],

    "ADC": [
        "resolution",
        "sampling_rate",
        "channels"
    ],

    "op-amp": [
        "gain_bandwidth",
        "input_offset",
        "supply_voltage"
    ],

    "MOSFET": [
        "vds",
        "id",
        "rds_on",
        "gate_charge"
    ],

    "power MOSFET": [
        "vds",
        "id",
        "rds_on",
        "power_dissipation"
    ],

    "diode": [
        "forward_voltage",
        "current_rating",
        "reverse_voltage"
    ],

    "Schottky diode": [
        "forward_voltage",
        "current_rating",
        "reverse_voltage"
    ],

    "LED": [
        "forward_voltage",
        "current_rating",
        "wavelength"
    ],

    "display": [
        "resolution",
        "interface",
        "size"
    ],

    "crystal": [
        "frequency",
        "load_capacitance",
        "tolerance"
    ],

    "fuse": [
        "current_rating",
        "voltage_rating",
        "breaking_capacity"
    ],
    "microcontroller": [
        "flash_memory",
        "ram",
        "clock_speed",
        "gpio_count",
        "adc_channels",
        "dac_channels",
        "supply_voltage",
        "package"
    ]
}