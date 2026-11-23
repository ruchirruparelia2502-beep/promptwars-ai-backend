"""
Initial equipment seed data for LabLink platform.
Comprehensive multi-department inventory:
1. Electronics, Embedded & Telecommunications (ECE)
2. Computer Science, AI & Cloud Systems (CSE)
3. Mechanical, Robotics & Additive Manufacturing (Mech)
4. Biotechnology, Genomics & Chemistry (Biotech)
5. Thermal & Environmental Diagnostics
"""

SEED_EQUIPMENT = [
    # =================================================================
    # 1. ELECTRONICS, EMBEDDED & TELECOMMUNICATIONS (ECE)
    # =================================================================
    {
        "id": "equip_rpi_01",
        "name": "Raspberry Pi 5 Edge AI Prototyping Kit",
        "department": "Electronics & Communication",
        "category": "Edge AI / Embedded Systems",
        "location": "IoT Innovation Lab, Station CS-C08",
        "tier": "FRUGAL_ENTRY",
        "hourly_cost_estimate": "$0.50/hr",
        "specifications": {"SBC": "Raspberry Pi 5 8GB", "NPU": "Hailo-8L 13 TOPS Accelerator", "Sensors": "Camera Module 3 + BNO055 IMU"},
        "safety_level": "Standard",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["raspberry pi", "edge", "iot", "hailo", "npu", "embedded", "sensors", "python", "lightweight", "frugal"]
    },
    {
        "id": "equip_stm32_01",
        "name": "STM32H7 Dual-Core Nucleo Prototyping Station",
        "department": "Electronics & Communication",
        "category": "Embedded Microcontrollers",
        "location": "Embedded Systems Lab, Bench ECE-102",
        "tier": "FRUGAL_ENTRY",
        "hourly_cost_estimate": "$0.30/hr",
        "specifications": {"MCU": "STM32H745ZI 480MHz Cortex-M7 + 240MHz M4", "RAM": "1MB SRAM", "Debug": "ST-LINK/V3 embedded"},
        "safety_level": "Standard",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["stm32", "arm", "cortex", "microcontroller", "freertos", "bare-metal", "embedded", "c++", "frugal"]
    },
    {
        "id": "equip_rigol_01",
        "name": "Rigol DS1054Z 50-MHz 4-Channel Digital Oscilloscope",
        "department": "Electronics & Communication",
        "category": "General Circuit Diagnostics",
        "location": "Circuits & Electronics Lab, Bench ECE-107",
        "tier": "FRUGAL_ENTRY",
        "hourly_cost_estimate": "$0.80/hr",
        "specifications": {"Bandwidth": "50 MHz (4 Channels)", "Sample_Rate": "1 GS/s", "Memory_Depth": "24 Mpts"},
        "safety_level": "Standard",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["oscilloscope", "rigol", "circuits", "debugging", "voltage", "waveform", "bench", "frugal"]
    },
    {
        "id": "equip_fpga_basys_01",
        "name": "Digilent Basys 3 Artix-7 FPGA Trainer Board",
        "department": "Electronics & Communication",
        "category": "Digital Logic & FPGA Training",
        "location": "Digital Design Lab, Bench ECE-103",
        "tier": "FRUGAL_ENTRY",
        "hourly_cost_estimate": "$0.60/hr",
        "specifications": {"FPGA": "Xilinx Artix-7 XC7A35T", "Switches": "16 User Switches + 16 LEDs", "Display": "4-digit 7-segment"},
        "safety_level": "Standard ESD",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["fpga", "basys3", "artix7", "verilog", "vhdl", "digital logic", "switches", "frugal"]
    },
    {
        "id": "equip_jetson_nano_01",
        "name": "NVIDIA Jetson Orin Nano 8GB Dev Kit",
        "department": "Electronics & Communication",
        "category": "Edge AI / Embedded Systems",
        "location": "Robotics & AI Center, Bench ECE-100",
        "tier": "MID_RANGE",
        "hourly_cost_estimate": "$2.50/hr",
        "specifications": {"SOC": "NVIDIA Ampere 1024-core", "RAM": "8GB LPDDR5", "AI_Performance": "40 TOPS"},
        "safety_level": "Standard",
        "daily_bitmask": 0b000000000000000000001100,
        "status": "OPERATIONAL",
        "tags": ["jetson", "orin nano", "gpu", "cuda", "edge ai", "robotics", "computer vision"]
    },
    {
        "id": "equip_jetson_01",
        "name": "NVIDIA Jetson AGX Orin 64GB Industrial Dev Kit",
        "department": "Electronics & Communication",
        "category": "Edge AI / Autonomous Robotics",
        "location": "Robotics & AI Center, Bench ECE-101",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$12.00/hr",
        "specifications": {"SOC": "NVIDIA Ampere 2048-core + Tensor", "RAM": "64GB LPDDR5", "AI_Performance": "275 TOPS"},
        "safety_level": "Standard",
        "daily_bitmask": 0b000000000000001111000000,
        "status": "OPERATIONAL",
        "tags": ["jetson", "orin", "gpu", "cuda", "edge ai", "robotics", "slam", "ros", "autonomous", "heavy"]
    },
    {
        "id": "equip_scope_01",
        "name": "Tektronix 4-GHz 25-GS/s Mixed Signal Oscilloscope",
        "department": "Electronics & Communication",
        "category": "Precision RF & Signal Analysis",
        "location": "RF & Microwave Lab, Bench ECE-109",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$18.00/hr",
        "specifications": {"Bandwidth": "4 GHz", "Channels": "4 Analog + 16 Digital Logic", "Sample_Rate": "25 GS/s"},
        "safety_level": "Advanced ESD Certified",
        "daily_bitmask": 0b000000000000000000001100,
        "status": "OPERATIONAL",
        "tags": ["oscilloscope", "tektronix", "rf", "signal analysis", "high speed", "debugging", "waveform", "heavy"]
    },
    {
        "id": "equip_usrp_01",
        "name": "NI USRP-2974 High-Performance SDR",
        "department": "Electronics & Communication",
        "category": "Software Defined Radio",
        "location": "Telecommunications Lab, Bench ECE-202",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$14.00/hr",
        "specifications": {"Frequency": "10 MHz - 6 GHz", "Bandwidth": "160 MHz", "Processor": "Intel Core i7 onboard, Kintex-7 FPGA"},
        "safety_level": "Standard",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["sdr", "usrp", "radio", "5g", "telecom", "wireless", "rf", "satellite"]
    },
    {
        "id": "equip_keysight_01",
        "name": "Keysight E5080B 4.5-GHz Vector Network Analyzer",
        "department": "Electronics & Communication",
        "category": "RF & Microwave Characterization",
        "location": "RF & Microwave Lab, Bench RF-301",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$22.00/hr",
        "specifications": {"Frequency": "9 kHz to 4.5 GHz", "Ports": "4-port VNA", "Dynamic_Range": "140 dB"},
        "safety_level": "Advanced RF Certified",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["vna", "keysight", "rf", "s-parameters", "microwave", "antenna", "impedance"]
    },

    # =================================================================
    # 2. COMPUTER SCIENCE, AI & CLOUD SYSTEMS (CSE)
    # =================================================================
    {
        "id": "equip_rtx_01",
        "name": "Dual NVIDIA RTX 4090 AI Workstation Alpha",
        "department": "Computer Science & Engineering",
        "category": "Deep Learning Workstations",
        "location": "Advanced AI Lab, Station CS-B12",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$10.00/hr",
        "specifications": {"GPUs": "2x NVIDIA RTX 4090 24GB (48GB total)", "CPU": "AMD Threadripper 7970X (32-Core)", "RAM": "256GB DDR5 ECC"},
        "safety_level": "Standard",
        "daily_bitmask": 0b000011110000000000000000,
        "status": "OPERATIONAL",
        "tags": ["rtx 4090", "gpu", "deep learning", "llm", "transformers", "pytorch", "workstation", "cuda", "heavy"]
    },
    {
        "id": "equip_rtx_02",
        "name": "Dual NVIDIA RTX 4090 AI Workstation Beta",
        "department": "Computer Science & Engineering",
        "category": "Deep Learning Workstations",
        "location": "Advanced AI Lab, Station CS-B14",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$10.00/hr",
        "specifications": {"GPUs": "2x NVIDIA RTX 4090 24GB (48GB total)", "CPU": "AMD Threadripper 7970X (32-Core)", "RAM": "256GB DDR5 ECC"},
        "safety_level": "Standard",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["rtx 4090", "gpu", "deep learning", "llm", "transformers", "pytorch", "workstation", "cuda", "heavy"]
    },
    {
        "id": "equip_hpc_01",
        "name": "Campus HPC GPU Cluster Node (4x A100 80GB)",
        "department": "Computer Science & Engineering",
        "category": "High-Performance Computing Cluster",
        "location": "Campus Data Center, Rack 04-HPC",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$35.00/hr",
        "specifications": {"Accelerators": "4x NVIDIA A100 80GB SXM4 NVLink", "CPU": "Dual AMD EPYC 7763 64-Core", "Interconnect": "200Gb/s InfiniBand HDR"},
        "safety_level": "Server Room Admin Clearance",
        "daily_bitmask": 0b000000000011111100000000,
        "status": "OPERATIONAL",
        "tags": ["a100", "hpc", "cluster", "supercomputing", "distributed", "slurm", "deep learning", "llm"]
    },
    {
        "id": "equip_vr_quest_01",
        "name": "Meta Quest Pro & Valve Index Spatial Computing Bench",
        "department": "Computer Science & Engineering",
        "category": "AR/VR & Spatial Computing",
        "location": "Human-Computer Interaction Lab, Station CS-D04",
        "tier": "MID_RANGE",
        "hourly_cost_estimate": "$3.00/hr",
        "specifications": {"Headsets": "Meta Quest Pro + Valve Index", "Workstation": "Intel i9-14900K + RTX 4080", "Tracking": "Base Station 2.0 Full Body"},
        "safety_level": "Standard",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["vr", "ar", "spatial computing", "unity", "unreal", "quest", "valve index", "metaverse"]
    },

    # =================================================================
    # 3. MECHANICAL, ROBOTICS & ADDITIVE MANUFACTURING (MECH)
    # =================================================================
    {
        "id": "equip_ender_01",
        "name": "Creality Ender-3 V3 Plus FDM 3D Printer",
        "department": "Mechanical & Mechatronics",
        "category": "Additive Manufacturing (FDM)",
        "location": "Rapid Fab Workspace, Room ME-101",
        "tier": "FRUGAL_ENTRY",
        "hourly_cost_estimate": "$0.70/hr",
        "specifications": {"Build_Size": "300 x 300 x 330 mm", "Material": "PLA, PETG filament", "Speed": "Up to 600 mm/s"},
        "safety_level": "Standard",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["3d printer", "fdm", "creality", "ender3", "pla", "prototyping", "brackets", "frugal"]
    },
    {
        "id": "equip_strat_01",
        "name": "Stratasys F170 Industrial FDM 3D Printer",
        "department": "Mechanical & Mechatronics",
        "category": "Additive Manufacturing (FDM)",
        "location": "Rapid Prototyping Facility, Room ME-105",
        "tier": "MID_RANGE",
        "hourly_cost_estimate": "$4.50/hr",
        "specifications": {"Build_Size": "254 x 254 x 254 mm", "Materials": "ABS, PLA, TPU 92A, Diran 410MF07", "Accuracy": "±0.200 mm"},
        "safety_level": "Standard",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["3d printer", "fdm", "stratasys", "abs", "pla", "prototyping", "cad", "chassis", "brackets"]
    },
    {
        "id": "equip_form_01",
        "name": "Formlabs Form 4 SLA Precision Resin 3D Printer",
        "department": "Mechanical & Mechatronics",
        "category": "Additive Manufacturing (SLA/LFD)",
        "location": "Rapid Prototyping Facility, Room ME-102",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$16.00/hr",
        "specifications": {"Technology": "Low Force Display (LFD)", "Resolution": "50 microns XY", "Materials": "Tough 2000, Clear, BioMed Resins"},
        "safety_level": "Chemical PPE & Nitrile Gloves Required",
        "daily_bitmask": 0b000000000000111111000000,
        "status": "OPERATIONAL",
        "tags": ["3d printer", "sla", "formlabs", "prototyping", "cad", "resin", "precision", "high accuracy", "heavy"]
    },
    {
        "id": "equip_laser_01",
        "name": "Epilog Fusion Pro 48 CO2 Laser Cutter (80W)",
        "department": "Mechanical & Mechatronics",
        "category": "Subtractive Precision Machining",
        "location": "Makerspace Machine Shop, Room ME-110",
        "tier": "MID_RANGE",
        "hourly_cost_estimate": "$6.00/hr",
        "specifications": {"Work_Area": "1219 x 914 mm", "Laser_Source": "80W CO2 Laser", "Materials": "Acrylic, Delrin, Plywood, Leather"},
        "safety_level": "Laser Safety Certified",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["laser cutter", "epilog", "acrylic", "cutting", "engraving", "chassis", "flat-pack", "sheet"]
    },
    {
        "id": "equip_ur5e_01",
        "name": "Universal Robots UR5e Collaborative Robotic Arm",
        "department": "Mechanical & Mechatronics",
        "category": "Robotics & Automation",
        "location": "Robotics Automation Cell 01, ME-205",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$15.00/hr",
        "specifications": {"Payload": "5 kg", "Reach": "850 mm radius", "Sensors": "Integrated 6-Axis Force/Torque Sensor, Teach Pendant"},
        "safety_level": "Robotics Safety Certified",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["ur5e", "robotics", "manipulator", "arm", "kinematics", "ros", "automation", "mechatronics", "heavy"]
    },
    {
        "id": "equip_kuka_01",
        "name": "KUKA youBot Omnidirectional Mobile Robot with 5-DOF Arm",
        "department": "Mechanical & Mechatronics",
        "category": "Autonomous Mobile Robotics",
        "location": "Robotics Automation Cell 03, ME-208",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$14.00/hr",
        "specifications": {"Base": "4x Mecanum wheels (omni-directional)", "Arm": "5-DOF manipulator with two-finger gripper", "Sensors": "Hokuyo Laser Scanner"},
        "safety_level": "Robotics Safety Certified",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["kuka", "youbot", "mobile robot", "mecanum", "slam", "ros", "manipulation", "heavy"]
    },

    # =================================================================
    # 4. BIOTECHNOLOGY, GENOMICS & CHEMISTRY (BIOTECH)
    # =================================================================
    {
        "id": "equip_pcr_mini_01",
        "name": "Bento Lab Compact DNA Amplification & Gel Kit",
        "department": "Biotechnology",
        "category": "Molecular Biology & PCR",
        "location": "Undergraduate Bio Lab, Bench BT-104",
        "tier": "FRUGAL_ENTRY",
        "hourly_cost_estimate": "$1.20/hr",
        "specifications": {"PCR": "32 x 0.2ml PCR tubes", "Centrifuge": "Up to 13,300 rpm", "Gel_Box": "Integrated Blue LED transilluminator"},
        "safety_level": "BioSafety Level 1",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["pcr", "dna", "gel", "electrophoresis", "bento", "molecular", "frugal", "entry"]
    },
    {
        "id": "equip_pcr_01",
        "name": "Bio-Rad CFX96 Real-Time Quantitative PCR System",
        "department": "Biotechnology",
        "category": "Molecular Biology & Genomics",
        "location": "Molecular Wet Lab, Room BT-201",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$18.00/hr",
        "specifications": {"Capacity": "96-well plate (5-target multiplexing)", "Optics": "6 filtered LEDs + 6 photodiodes", "Thermal_Range": "0 to 100°C"},
        "safety_level": "BioSafety Level 2",
        "daily_bitmask": 0b000000000000000000111100,
        "status": "OPERATIONAL",
        "tags": ["pcr", "qpcr", "genomics", "dna", "rna", "biotech", "molecular", "thermal cycler", "heavy"]
    },
    {
        "id": "equip_hplc_01",
        "name": "Agilent 1260 Infinity II HPLC Chromatography System",
        "department": "Biotechnology",
        "category": "Analytical Chromatography",
        "location": "Analytical Chemistry Suite, Room BT-305",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$20.00/hr",
        "specifications": {"Pressure_Limit": "600 bar", "Detector": "Diode Array Detector (DAD WR)", "Autosampler": "Dual-needle multi-sampler"},
        "safety_level": "Chemical PPE & Solvent Hood Required",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["hplc", "chromatography", "agilent", "chemical", "purification", "spectrometry", "assay", "heavy"]
    },
    {
        "id": "equip_microscope_01",
        "name": "Olympus IX73 Inverted Phase-Contrast Fluorescence Microscope",
        "department": "Biotechnology",
        "category": "Cellular Bio-Imaging",
        "location": "Cell Culture Microscopy Suite, Room BT-212",
        "tier": "HIGH_END_CAPSTONE",
        "hourly_cost_estimate": "$16.00/hr",
        "specifications": {"Optics": "Inverted UIS2 Optical System", "Fluorescence": "LED Light Engine (DAPI/FITC/TRITC/Cy5)", "Camera": "Hamamatsu sCMOS"},
        "safety_level": "Darkroom & Laser Safety",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["microscope", "olympus", "fluorescence", "cells", "imaging", "live-cell", "biology", "heavy"]
    },

    # =================================================================
    # 5. CIVIL & ENVIRONMENTAL SENSING
    # =================================================================
    {
        "id": "equip_flir_01",
        "name": "FLIR T865 High-Resolution Thermal Imaging Camera",
        "department": "Mechanical & Mechatronics",
        "category": "Thermal Diagnostics & Infrared",
        "location": "Materials & Structures Lab, Bench ME-302",
        "tier": "MID_RANGE",
        "hourly_cost_estimate": "$8.00/hr",
        "specifications": {"IR_Resolution": "640 x 480 pixels", "Thermal_Sensitivity": "<30 mK at 30°C", "Temp_Range": "-40°C to 2000°C"},
        "safety_level": "Standard",
        "daily_bitmask": 0,
        "status": "OPERATIONAL",
        "tags": ["thermal", "flir", "infrared", "temperature", "heat transfer", "insulation", "pcb thermal"]
    }
]
