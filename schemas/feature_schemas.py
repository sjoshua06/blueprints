# FEATURE_SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────
# Keyed by SUBCATEGORY (Spring, Copper, Sensor …) — NOT by component_type.
#
# Each list is the ordered feature vector for that subcategory's FAISS index.
# The order defines which position in the vector each spec occupies.
# Every entry matches the exact spec_name values stored in component_specifications.
#
# Rules:
#   - Numeric specs map directly to float.
#   - Categorical specs (Grade, Material …) are hashed to int via
#     abs(hash(value)) % 1000 in vector_builder.convert_value().
#   - Adding or removing a spec here requires rebuilding all FAISS indexes
#     (re-run setup_pipeline / POST /setup/build-indexes).

FEATURE_SCHEMAS = {

    # ── Mechanical ────────────────────────────────────────────────────────
    "Spring": [
        "Wire Diameter",      # mm
        "Outer Diameter",     # mm
        "Free Length",        # mm
        "Spring Rate",        # N/mm
        "Max Load",           # N
        "Material",           # categorical → hashed
    ],

    "Shaft": [
        "Diameter",           # mm
        "Length",             # mm
        "Straightness",       # mm/m
        "Tensile Strength",   # MPa
        "Surface Roughness",  # µm
        "Material",           # categorical → hashed
    ],

    "Bearing": [
        "Inner Diameter",     # mm
        "Outer Diameter",     # mm
        "Width",              # mm
        "Dynamic Load",       # kN
        "Static Load",        # kN
        "Max RPM",            # rpm
    ],

    "Gear": [
        "Module",             # mm
        "Number of Teeth",    # count
        "Pressure Angle",     # degrees
        "Face Width",         # mm
        "Pitch Diameter",     # mm
        "Material",           # categorical → hashed
    ],

    # ── Electronics ───────────────────────────────────────────────────────
    "Sensor": [
        "Supply Voltage",     # V
        "Output Range",       # V
        "Accuracy",           # %
        "Response Time",      # ms
        "Operating Temp",     # °C
        "IP Rating",          # categorical → hashed
    ],

    "Capacitor": [
        "Capacitance",        # µF
        "Voltage Rating",     # V
        "Tolerance",          # categorical → hashed
        "ESR",                # mΩ
        "Operating Temp",     # °C
        "Max Temp",           # °C
    ],

    "PCB": [
        "Board Thickness",    # mm
        "Copper Weight",      # oz/ft²
        "Layer Count",        # count
        "Min Trace Width",    # mm
        "Board Length",       # mm
        "Board Width",        # mm
    ],

    "Microcontroller": [
        "Clock Speed",        # MHz
        "Flash Memory",       # KB
        "RAM",                # KB
        "GPIO Pins",          # count
        "Supply Voltage",     # V
        "Operating Temp",     # °C
    ],

    # ── Fastener ──────────────────────────────────────────────────────────
    "Bolt": [
        "Diameter",           # mm
        "Length",             # mm
        "Thread Pitch",       # mm
        "Tensile Strength",   # MPa
        "Grade",              # categorical → hashed
        "Material",           # categorical → hashed
    ],

    "Nut": [
        "Thread Size",        # mm
        "Width Across Flats", # mm
        "Height",             # mm
        "Proof Load",         # MPa
        "Grade",              # categorical → hashed
        "Material",           # categorical → hashed
    ],

    "Screw": [
        "Diameter",           # mm
        "Length",             # mm
        "Thread Pitch",       # mm
        "Head Type",          # categorical → hashed
        "Drive Type",         # categorical → hashed
        "Material",           # categorical → hashed
    ],

    "Washer": [
        "Inner Diameter",     # mm
        "Outer Diameter",     # mm
        "Thickness",          # mm
        "Hardness",           # HV
        "Surface Finish",     # categorical → hashed
        "Material",           # categorical → hashed
    ],

    # ── Raw Material ──────────────────────────────────────────────────────
    "Aluminum": [
        "Alloy Grade",        # categorical → hashed
        "Tensile Strength",   # MPa
        "Yield Strength",     # MPa
        "Density",            # g/cm³
        "Hardness",           # HB
        "Elongation",         # %
    ],

    "Copper": [
        "Grade",              # categorical → hashed
        "Tensile Strength",   # MPa
        "Yield Strength",     # MPa
        "Conductivity",       # % IACS
        "Density",            # g/cm³
        "Elongation",         # %
    ],

    "Steel": [
        "Grade",              # categorical → hashed
        "Tensile Strength",   # MPa
        "Yield Strength",     # MPa
        "Hardness",           # HB
        "Density",            # g/cm³
        "Elongation",         # %
    ],

    "Plastic": [
        "Polymer Type",       # categorical → hashed
        "Tensile Strength",   # MPa
        "Flexural Modulus",   # GPa
        "Density",            # g/cm³
        "Melting Point",      # °C
        "Elongation",         # %
    ],
}