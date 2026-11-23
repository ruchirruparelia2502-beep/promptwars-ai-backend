"""
Thread-Safe In-Memory Datastore for LabLink
Stores multi-department specialized laboratory equipment, slot reservations,
active BookMyShow leased holds, project proposals, and student usage profiles.

Time Complexity:
- Equipment Lookup: O(1) via hash map
- Inverted Index Tag Search: O(1) to O(K)
- Concurrency Control: Python threading.Lock prevents race conditions
"""

import threading
import time
from typing import Dict, List, Optional, Any
from app.core.bitmask import create_interval_mask, apply_reservation, cancel_reservation, calculate_utilization_percentage


class InMemoryLabDatabase:
    def __init__(self):
        self._lock = threading.Lock()
        self.equipment: Dict[str, Dict[str, Any]] = {}
        self.bookings: Dict[str, Dict[str, Any]] = {}
        self.proposals: Dict[str, Dict[str, Any]] = {}
        self.student_profiles: Dict[str, Dict[str, Any]] = {}
        self.inverted_index: Dict[str, List[str]] = {}
        self._seed_data()

    def _seed_data(self):
        """Initializes realistic cross-departmental laboratory resources."""
        raw_equipment = [
            # ECE & Embedded Hardware
            {
                "id": "equip_jetson_01",
                "name": "NVIDIA Jetson AGX Orin 64GB Dev Kit",
                "department": "Electronics & Communication",
                "category": "Edge AI / Embedded Systems",
                "location": "Robotics & AI Center, Bench ECE-101",
                "specifications": {"SOC": "NVIDIA Ampere 2048-core", "RAM": "64GB LPDDR5", "AI_Performance": "275 TOPS"},
                "safety_level": "Standard",
                "daily_bitmask": 0b000000000000001111000000, # Slots 6..9 booked
                "status": "OPERATIONAL",
                "tags": ["jetson", "orin", "gpu", "cuda", "edge ai", "robotics", "computer vision", "slam", "deep learning"]
            },
            {
                "id": "equip_fpga_01",
                "name": "Xilinx Zynq UltraScale+ MPSoC ZCU102",
                "department": "Electronics & Communication",
                "category": "FPGA & VLSI Prototyping",
                "location": "VLSI Design Lab, Bench ECE-104",
                "specifications": {"FPGA": "XCZU9EG", "Cores": "Quad ARM Cortex-A53", "Memory": "4GB DDR4"},
                "safety_level": "Advanced ESD Certified",
                "daily_bitmask": 0b000000001110000000000000, # Slots 13..15 booked
                "status": "OPERATIONAL",
                "tags": ["fpga", "xilinx", "zynq", "verilog", "vhdl", "hardware acceleration", "dsp", "vlsi"]
            },
            {
                "id": "equip_tek_01",
                "name": "Tektronix 4-GHz Mixed Signal Oscilloscope",
                "department": "Electronics & Communication",
                "category": "Precision RF & Signal Analysis",
                "location": "RF & Microwave Lab, Bench ECE-109",
                "specifications": {"Bandwidth": "4 GHz", "Channels": "4 Analog + 16 Digital", "Sample_Rate": "25 GS/s"},
                "safety_level": "Standard",
                "daily_bitmask": 0b000000000000000000001100, # Slots 2..3 booked
                "status": "OPERATIONAL",
                "tags": ["oscilloscope", "tektronix", "rf", "signal analysis", "high speed", "debugging", "waveform"]
            },
            {
                "id": "equip_usrp_01",
                "name": "NI USRP-2974 High-Performance SDR",
                "department": "Electronics & Communication",
                "category": "Software Defined Radio",
                "location": "Telecommunications Lab, Bench ECE-202",
                "specifications": {"Frequency": "10 MHz - 6 GHz", "Bandwidth": "160 MHz", "Processor": "Intel Core i7 onboard"},
                "safety_level": "Standard",
                "daily_bitmask": 0,
                "status": "OPERATIONAL",
                "tags": ["sdr", "usrp", "radio", "5g", "telecom", "wireless", "rf", "satellite"]
            },

            # CSE & High-Performance Computing
            {
                "id": "equip_rtx_01",
                "name": "Dual NVIDIA RTX 4090 AI Workstation Alpha",
                "department": "Computer Science & Engineering",
                "category": "Deep Learning Workstations",
                "location": "Advanced AI Lab, Station CS-B12",
                "specifications": {"GPUs": "2x NVIDIA RTX 4090 24GB", "CPU": "AMD Threadripper 7970X", "RAM": "256GB ECC"},
                "safety_level": "Standard",
                "daily_bitmask": 0b000011110000000000000000, # Slots 16..19 booked
                "status": "OPERATIONAL",
                "tags": ["rtx 4090", "gpu", "deep learning", "llm", "transformers", "pytorch", "workstation", "cuda"]
            },
            {
                "id": "equip_rtx_02",
                "name": "Dual NVIDIA RTX 4090 AI Workstation Beta",
                "department": "Computer Science & Engineering",
                "category": "Deep Learning Workstations",
                "location": "Advanced AI Lab, Station CS-B14",
                "specifications": {"GPUs": "2x NVIDIA RTX 4090 24GB", "CPU": "AMD Threadripper 7970X", "RAM": "256GB ECC"},
                "safety_level": "Standard",
                "daily_bitmask": 0,
                "status": "OPERATIONAL",
                "tags": ["rtx 4090", "gpu", "deep learning", "llm", "transformers", "pytorch", "workstation", "cuda"]
            },
            {
                "id": "equip_rpi_01",
                "name": "Raspberry Pi 5 Edge AI Prototyping Kit",
                "department": "Computer Science & Engineering",
                "category": "IoT & Edge Computing",
                "location": "IoT Innovation Lab, Station CS-C08",
                "specifications": {"SBC": "Raspberry Pi 5 8GB", "NPU": "Hailo-8L 13 TOPS Accelerator", "Sensors": "Camera + IMU"},
                "safety_level": "Standard",
                "daily_bitmask": 0,
                "status": "OPERATIONAL",
                "tags": ["raspberry pi", "edge", "iot", "hailo", "npu", "embedded", "sensors", "python"]
            },

            # Mechanical & Robotics
            {
                "id": "equip_form_01",
                "name": "Formlabs Form 4 SLA Precision 3D Printer",
                "department": "Mechanical & Mechatronics",
                "category": "Additive Manufacturing",
                "location": "Rapid Prototyping Facility, Room ME-102",
                "specifications": {"Technology": "Low Force Display (LFD)", "Resolution": "50 microns", "Materials": "Tough/Bio/Elastic Resins"},
                "safety_level": "Chemical PPE Required",
                "daily_bitmask": 0b000000000000111111000000, # Slots 6..11 booked
                "status": "OPERATIONAL",
                "tags": ["3d printer", "sla", "formlabs", "prototyping", "cad", "resin", "enclosure", "fabrication"]
            },
            {
                "id": "equip_ur5e_01",
                "name": "Universal Robots UR5e Collaborative Robotic Arm",
                "department": "Mechanical & Mechatronics",
                "category": "Robotics & Automation",
                "location": "Robotics Automation Cell 01, ME-205",
                "specifications": {"Payload": "5 kg", "Reach": "850 mm", "Sensors": "Integrated 6-Axis Force/Torque Sensor"},
                "safety_level": "Robotics Safety Certified",
                "daily_bitmask": 0,
                "status": "OPERATIONAL",
                "tags": ["ur5e", "robotics", "manipulator", "arm", "kinematics", "ros", "automation", "mechatronics"]
            },
            {
                "id": "equip_strat_01",
                "name": "Stratasys F170 Industrial FDM 3D Printer",
                "department": "Mechanical & Mechatronics",
                "category": "Additive Manufacturing",
                "location": "Rapid Prototyping Facility, Room ME-105",
                "specifications": {"Build_Size": "254 x 254 x 254 mm", "Materials": "ABS, PLA, TPU 92A, Diran"},
                "safety_level": "Standard",
                "daily_bitmask": 0,
                "status": "OPERATIONAL",
                "tags": ["3d printer", "fdm", "stratasys", "abs", "pla", "prototyping", "cad"]
            },

            # Biotechnology & Chemistry
            {
                "id": "equip_pcr_01",
                "name": "Bio-Rad CFX96 Real-Time PCR Detection System",
                "department": "Biotechnology",
                "category": "Molecular Biology & Genomics",
                "location": "Molecular Wet Lab, Room BT-201",
                "specifications": {"Capacity": "96 wells", "Excitation": "6 filtered LEDs", "Detection": "6 photodiodes"},
                "safety_level": "BioSafety Level 2",
                "daily_bitmask": 0b000000000000000000111100, # Slots 2..5 booked
                "status": "OPERATIONAL",
                "tags": ["pcr", "genomics", "dna", "rna", "qpcr", "biotech", "molecular", "thermal cycler"]
            },
            {
                "id": "equip_hplc_01",
                "name": "Agilent 1260 Infinity II HPLC System",
                "department": "Biotechnology",
                "category": "Analytical Chromatography",
                "location": "Analytical Chemistry Suite, Room BT-305",
                "specifications": {"Pressure_Limit": "600 bar", "Detector": "Diode Array Detector (DAD)", "Autosampler": "Integrated"},
                "safety_level": "Chemical PPE Required",
                "daily_bitmask": 0,
                "status": "OPERATIONAL",
                "tags": ["hplc", "chromatography", "agilent", "chemical", "purification", "spectrometry", "assay"]
            }
        ]

        for item in raw_equipment:
            self.equipment[item["id"]] = item
            # Populate inverted index
            for tag in item["tags"]:
                tag_lower = tag.lower().strip()
                if tag_lower not in self.inverted_index:
                    self.inverted_index[tag_lower] = []
                self.inverted_index[tag_lower].append(item["id"])

        # Pre-seed realistic student usage records
        self.student_profiles = {
            "stu_arjun_01": {
                "id": "stu_arjun_01",
                "name": "Arjun Sharma",
                "department": "Electronics & Communication",
                "hours_used_this_month": 4.5,
                "has_safety_cert": True,
                "active_project": "Real-Time Quadrotor SLAM with Jetson Orin"
            },
            "stu_priya_02": {
                "id": "stu_priya_02",
                "name": "Priya Nair",
                "department": "Computer Science & Engineering",
                "hours_used_this_month": 32.0, # High usage (tests anti-hoarding fairness)
                "has_safety_cert": True,
                "active_project": "Benchmarking Vision Transformers on Edge Hardware"
            },
            "stu_rohit_03": {
                "id": "stu_rohit_03",
                "name": "Rohit Verma",
                "department": "Mechanical & Mechatronics",
                "hours_used_this_month": 1.0,
                "has_safety_cert": True,
                "active_project": "Design of SLA-Printed Compliant Grippers"
            }
        }

        # Pre-seed faculty approval proposal
        self.proposals["prop_sample_01"] = {
            "proposal_id": "prop_sample_01",
            "project_title": "Edge-Accelerated LiDAR SLAM for Autonomous Campus Buggy",
            "student_id": "stu_arjun_01",
            "student_name": "Arjun Sharma",
            "faculty_advisor": "Dr. K. Ramanathan (Professor, ECE)",
            "target_equipment_id": "equip_jetson_01",
            "submission_deadline_days": 3,
            "academic_tier": "capstone",
            "abstract": "We are implementing a point-cloud SLAM pipeline on the Jetson AGX Orin to navigate an autonomous delivery vehicle across campus buildings. Requires 4 hours of daily hardware-in-the-loop bench testing.",
            "status": "PENDING_FACULTY",
            "submission_time": time.time() - 3600,
            "ai_assessment": {
                "feasibility_score": 94,
                "equipment_appropriateness": "High Match (Jetson AGX Orin 64GB has dedicated Tensor/Ampere cores required for 3D point cloud processing)",
                "safety_check": "Cleared (Student holds Standard Lab Safety Certificate)",
                "recommendation": "RECOMMENDED FOR IMMEDIATE APPROVAL"
            }
        }

    # Thread-Safe Queries
    def get_all_equipment(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.equipment.values())

    def get_equipment_by_id(self, equip_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.equipment.get(equip_id)

    def search_by_tag_or_keyword(self, query: str) -> List[Dict[str, Any]]:
        """O(1) to O(K) lookup across inverted index + fuzzy substring scan."""
        tokens = [t.lower().strip() for t in query.split() if len(t) > 2]
        matched_ids = set()

        with self._lock:
            for token in tokens:
                if token in self.inverted_index:
                    matched_ids.update(self.inverted_index[token])
            
            # Substring fallback
            if not matched_ids:
                for eid, item in self.equipment.items():
                    if query.lower() in item["name"].lower() or query.lower() in item["category"].lower():
                        matched_ids.add(eid)

            return [self.equipment[eid] for eid in matched_ids if eid in self.equipment]

    def reserve_slot_atomic(self, equipment_id: str, slot_mask: int) -> bool:
        """Atomic reservation under lock."""
        with self._lock:
            equip = self.equipment.get(equipment_id)
            if not equip:
                return False
            current = equip["daily_bitmask"]
            if (current & slot_mask) != 0:
                return False # Conflict detected
            equip["daily_bitmask"] = apply_reservation(current, slot_mask)
            return True

    def release_slot_atomic(self, equipment_id: str, slot_mask: int) -> bool:
        """Atomic slot release."""
        with self._lock:
            equip = self.equipment.get(equipment_id)
            if not equip:
                return False
            equip["daily_bitmask"] = cancel_reservation(equip["daily_bitmask"], slot_mask)
            return True

    def add_booking(self, booking_dict: Dict[str, Any]):
        with self._lock:
            self.bookings[booking_dict["booking_id"]] = booking_dict

    def get_all_bookings(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.bookings.values())

    def add_proposal(self, proposal_dict: Dict[str, Any]):
        with self._lock:
            self.proposals[proposal_dict["proposal_id"]] = proposal_dict

    def get_all_proposals(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.proposals.values())

    def update_proposal_status(self, proposal_id: str, new_status: str, notes: Optional[str] = None) -> bool:
        with self._lock:
            prop = self.proposals.get(proposal_id)
            if not prop:
                return False
            prop["status"] = new_status
            if notes:
                prop["faculty_notes"] = notes
            prop["updated_at"] = time.time()
            return True


# Global database instance
db = InMemoryLabDatabase()
