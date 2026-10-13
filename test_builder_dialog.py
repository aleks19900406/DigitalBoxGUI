"""
Test Builder Dialog - Visual test sequence creator
"""
import json
import os
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QBrush, QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QGroupBox, QSpinBox, QDoubleSpinBox,
    QComboBox, QFormLayout, QMessageBox, QFileDialog, QCheckBox,
    QLineEdit, QAbstractItemView, QWidget, QFrame, QGridLayout
)


def get_app_dir():
    return os.path.abspath(os.path.dirname(__file__))


def get_device_dir():
    return os.path.join(get_app_dir(), 'data')


def get_groups_dir():
    groups_dir = os.path.join(get_device_dir(), 'groups')
    os.makedirs(groups_dir, exist_ok=True)
    return groups_dir


STATE_MAPS = {}


class BBTDeviceConfig:
    DELAY_MIN = 0.0
    DELAY_MAX = 99999.0
    DELAY_DEFAULT = 5.0
    VOLTAGE_MIN = 0.0
    VOLTAGE_MAX = 30.0
    VOLTAGE_DEFAULT = 12.0
    VOLTAGE_STEP = 0.1
    PWM_DC_MIN = 0
    PWM_DC_MAX = 100
    PWM_DC_DEFAULT = 50

    @staticmethod
    def get_pwm_frequency_options(pwm_channel=None):
        return ["0 (OFF)", "100", "200", "500", "1000"]


class TestBuilderDialog(QDialog):
    """Dialog for building automated test sequences"""

    GCU_SECTION_GROUPS = {
        "Faults": ["Faults"],
        "Device Hardware": ["Sensors", "Inlet", "Turbidity", "Heater", "Diverter", "Hardware"],
        "Pumps": ["Circ Pump", "Drain Pump", "BLDC"],
        "Program": ["Program"],
        "Test Mode": ["Test Mode"],
        "Other": ["Settings", "Config", "Dispenser", "Protocol"],
        "Veeprom / Persist": ["Veeprom / Persist"],
        "GPIO": ["GPIO"],
        "Program Sequence": ["Program Sequence"],
        "Tank Sequence": ["Tank Sequence"],
        "Timers": ["Timers"],
    }

    GCU_WINDOWS = {
        "Faults": {
            "failure_handling_state": "Failure State",
            "failure_handling_failure_detected": "Failure Detected",
            "failure_handling_lifted_floater_flag": "Lifted Floater Flag",
            "failure_handling_grey_tank_timeout": "Grey Tank Timeout",
            "failure_handling_heatexchanger_tank_timeout": "HeatEx Tank Timeout"
        },
        "Sensors": {
            "temperature": "Temperature",
            "temperature_mode": "Temp Mode",
            "pressure_mmH2O": "Pressure (mmH2O)",
            "pressure_offset": "Pressure Offset",
            "pressure_frequency": "Pressure Frequency"
        },
        "Inlet": {
            "inlet_state": "Inlet State",
            "inlet_intake_size": "Inlet Intake Size",
            "inlet_type": "Inlet Type",
            "flowmeter_value": "Flowmeter Value",
            "flowmeter_pulses": "Flowmeter Pulses",
            "flowmeter_nsum": "Flowmeter N Sum",
            "flowmeter_n_sum_pulses": "Flow N Sum Pulses"
        },
        "Turbidity": {
            "turb_rpc_state": "Turb RPC State",
            "turb_measure_state": "Turb Measure",
            "turbidity": "Turbidity",
            "turbidity_voltage": "Turbidity Voltage",
            "turbidity_calib_voltage": "Turbidity Calib Voltage"
        },
        "Heater": {
            "heater_state": "Heater State",
            "heater_max_temp": "Heater Max Temp",
            "heater_min_temp": "Heater Min Temp",
            "heater_time_max": "Heater Time Max"
        },
        "Diverter": {
            "diverter_state": "Diverter State",
            "diverter_position": "Diverter Position",
            "diverter_request": "Diverter Request",
            "diverter_counter1": "Diverter Counter1",
            "diverter_counter2": "Diverter Counter2"
        },
        "Hardware": {
            "door_state": "Door State",
            "door_door_switch_state": "Door Switch State",
            "mdo": "MDO",
            "temperature_vals_t_mcu": "MCU Temp"
        },
        "Circ Pump": {"pumps_circ_req_speed": "Circ Req Speed"},
        "Drain Pump": {
            "pumps_drain_req_speed": "Drain Req Speed",
            "drain_state": "Drain State"
        },
        "Program": {
            "program_state": "Program State",
            "program_program_active": "Program Active",
            "program_program_selected": "Program Selected",
            "program_program_mode": "Program Mode",
            "remaining_time_remaining_time": "Remaining Time",
            "remaining_time_run_time": "Run Time",
            "prog_pause_state": "Pause State",
            "program_total_run_time": "Total Run Time",
            "program_number_of_cycles": "Num Cycles",
            "program_pwr_loss_detection_cntr": "Pwr Loss Cntr",
            "program_running_prog_energy_consumption_Wh": "Run Energy (Wh)",
            "program_option_ado": "Option ADO",
            "program_checkpoint_cntr": "Checkpoint",
            "program_running_prog_water_consumption": "Run Water",
            "program_flags_flags": "Program Flags"
        },
        "Test Mode": {
            "test_mode_state": "Test Mode State",
            "test_mode_flag": "Test Mode Flag",
            "service_state": "Service State",
            "service_status": "Service Status",
            "fun_test_state": "Fun Test State",
            "fun_test_current_step": "Fun Test Current Step",
            "fun_test_fault": "Fun Test Fault",
            "leak_test_state": "Leak Test State"
        },
        "Config": {
            "appliance_config_ado": "ADO",
            "appliance_config_softener": "Softener",
            "appliance_config_auto_dose_rinse_aid": "ADO Rinse Aid",
            "appliance_config_turbidity": "Turbidity",
            "appliance_config_sensor_dry": "Sensor Dry"
        },
        "Settings": {
            "parameters_variant": "Variant",
            "parameters_performance": "Performance",
            "appliance_settings_water_hardness": "Water Hardness",
            "appliance_settings_rinse_aid": "Rinse Aid",
            "appliance_settings_tab": "Tab",
            "appliance_settings_super_rinse": "Super Rinse",
            "appliance_settings_water_save": "Water Save"
        },
        "Dispenser": {
            "main_disp_state": "Main Disp State",
            "rinse_aid_disp_state": "Rinse Aid Disp State",
            "rinse_aid_disp_counter": "Rinse Aid Disp Counter",
            "scs_state": "SCS State",
            "soft_reg_state": "Soft Reg State",
            "soft_rinse_state": "Soft Rinse State",
            "fan_state": "Fan State",
            "fan_seq": "Fan Seq",
            "autodose_state": "Autodose State",
            "spray_arm_state": "Spray Arm State",
            "spray_arm_div_seq": "Spray Arm Div Seq",
            "inter_light_state": "Inter Light State"
        },
        "Veeprom / Persist": {
            "veeprom_write_cntr": "Veeprom Write Cntr",
            "veeprom_error_cntr": "Veeprom Error Cntr",
            "veeprom_settings_write_cntr": "Veeprom Settings Write",
            "veeprom_settings_error_cntr": "Veeprom Settings Error",
            "persist_data_write_cntr": "Persist Write Cntr",
            "persist_data_error_cntr": "Persist Error Cntr"
        },
        "Protocol": {
            "protocol_main_crc_error_cntr": "Main CRC Error Cntr",
            "protocol_main_no_frame_cntr": "Main No Frame Cntr",
            "protocol_bldc_crc_error_cntr": "BLDC CRC Error Cntr",
            "protocol_bldc_no_frame_cntr": "BLDC No Frame Cntr",
            "protocol_variant": "Variant",
            "protocol_zerocross_state": "Zerocross State",
            "protocol_bldc_version_major": "BLDC Version Major",
            "protocol_bldc_version_minor": "BLDC Version Minor",
            "protocol_bldc_version_reserved": "BLDC Version Reserved",
            "protocol_bldc_comm_failure_flag": "BLDC Comm Failure"
        },
        "Program Sequence": {
            "mdo": "MDO",
            "preheat": "PREHEAT",
            "pre": "PRE",
            "pw1": "PW1",
            "pw2": "PW2",
            "pw3": "PW3",
            "pw4": "PW4",
            "pw5": "PW5",
            "mw1": "MW1",
            "mw2": "MW2",
            "cf1": "CF1",
            "er1": "ER1",
            "ri1": "RI1",
            "ri2": "RI2",
            "ri5": "RI5",
            "er2": "ER2",
            "ri6": "RI6",
            "ri7": "RI7",
            "dry1": "DRY1",
            "dry2": "DRY2",
            "ion": "ION",
            "storage": "STORAGE"
        },
        "Tank Sequence": {
            "empty_tank_state": "Empty Tank",
            "empty_heat_tank_state": "Empty Heat Tank",
            "fill_tank_state": "Fill Tank",
            "tank_rinse_state": "Tank Rinse"
        },
        "Timers": {
            "tim1_prescaler": "TIM1 Prescaler",
            "tim1_period": "TIM1 Period",
            "tim1_ch_duty_diff": "TIM1 CH Duty Diff",
            "tim1_ch_enable": "TIM1 CH Enable",
            "tim3_prescaler": "TIM3 Prescaler",
            "tim3_period": "TIM3 Period",
            "tim3_ch_duty_diff": "TIM3 CH Duty Diff",
            "tim3_ch_enable": "TIM3 CH Enable",
            "tim14_prescaler": "TIM14 Prescaler",
            "tim14_period": "TIM14 Period",
            "tim14_ch_duty_diff": "TIM14 CH Duty Diff",
            "tim14_ch_enable": "TIM14 CH Enable",
            "tim15_prescaler": "TIM15 Prescaler",
            "tim15_period": "TIM15 Period",
            "tim15_ch_duty_diff": "TIM15 CH Duty Diff",
            "tim15_ch_enable": "TIM15 CH Enable",
            "tim16_prescaler": "TIM16 Prescaler",
            "tim16_period": "TIM16 Period",
            "tim16_ch_duty_diff": "TIM16 CH Duty Diff",
            "tim16_ch_enable": "TIM16 CH Enable"
        },
        "GPIO": {
            "gpio_pin_0": "5V_WIFI",
            "gpio_pin_1": "RTC_OUT1",
            "gpio_pin_2": "LOAD_BAL",
            "gpio_pin_3": "12V_VLED_SW",
            "gpio_pin_4": "12V_VLED",
            "gpio_pin_5": "HP_FAN",
            "gpio_pin_6": "SALT_LED",
            "gpio_pin_7": "SALT_SENS",
            "gpio_pin_8": "5V_PRESS",
            "gpio_pin_9": "FLOW_MTR",
            "gpio_pin_10": "TURB_SEL1",
            "gpio_pin_11": "TURB_SEL2",
            "gpio_pin_12": "RINSE_AID_S",
            "gpio_pin_13": "RINSE_AID_L",
            "gpio_pin_14": "ADO_DET_LED",
            "gpio_pin_15": "ADO_DET",
            "gpio_pin_16": "RO1",
            "gpio_pin_17": "RO2",
            "gpio_pin_18": "RO3",
            "gpio_pin_19": "DBG3",
            "gpio_pin_20": "DBG4",
            "gpio_pin_21": "RO_HVDC",
            "gpio_pin_22": "MDO_TX",
            "gpio_pin_23": "MDO_RX",
        }
    }

    FIELD_STATE_MAPS = {
        "failure_handling_state": "failure_handling",
        "drain_state": "drain",
        "pumps_circ_status": "pumps",
        "pumps_drain_status": "pumps",
        "heater_state": "heater",
        "program_state": "program",
        "inlet_state": "inlet",
        "door_state": "door",
        "door_door_switch_state": "door_switch",
        "diverter_state": "diverter",
        "prog_pause_state": "prog_pause",
        "test_mode_state": "test_mode",
        "service_state": "service",
        "fun_test_state": "fun_test",
        "leak_test_state": "leak_test",
        "turb_rpc_state": "turb",
        "turb_measure_state": "turbidity_measure",
        "main_disp_state": "main_disp",
        "rinse_aid_disp_state": "rinse_aid_disp",
        "scs_state": "scs",
        "soft_reg_state": "soft_reg",
        "soft_rinse_state": "soft_rinse",
        "fan_state": "fan",
        "autodose_state": "autodose",
        "spray_arm_state": "spray_arm",
        "inter_light_state": "inter_light",
        "empty_tank_state": "empty_tank",
        "empty_heat_tank_state": "empty_heat_tank",
        "fill_tank_state": "fill_tank",
        "tank_rinse_state": "tank_rinse",
        "protocol_zerocross_state": "zerocross",
        "mdo": "mdo",
        "preheat": "preheat",
        "pre": "pre",
        "pw1": "pw1",
        "pw2": "pw2",
        "pw3": "pw3",
        "pw4": "pw4",
        "pw5": "pw5",
        "mw1": "mw1",
        "mw2": "mw2",
        "cf1": "cf1",
        "er1": "er1",
        "ri1": "ri1",
        "ri2": "ri2",
        "ri5": "ri5",
        "er2": "er2",
        "ri6": "ri6",
        "ri7": "ri7",
        "dry1": "dry1",
        "dry2": "dry2",
        "ion": "ion",
        "storage": "storage",
        "gpio_pin_0": "gpio_pin",
        "gpio_pin_1": "gpio_pin",
        "gpio_pin_2": "gpio_pin",
        "gpio_pin_3": "gpio_pin",
        "gpio_pin_4": "gpio_pin",
        "gpio_pin_5": "gpio_pin",
        "gpio_pin_6": "gpio_pin",
        "gpio_pin_7": "gpio_pin",
        "gpio_pin_8": "gpio_pin",
        "gpio_pin_9": "gpio_pin",
        "gpio_pin_10": "gpio_pin",
        "gpio_pin_11": "gpio_pin",
        "gpio_pin_12": "gpio_pin",
        "gpio_pin_13": "gpio_pin",
        "gpio_pin_14": "gpio_pin",
        "gpio_pin_15": "gpio_pin",
        "gpio_pin_16": "gpio_pin",
        "gpio_pin_17": "gpio_pin",
        "gpio_pin_18": "gpio_pin",
        "gpio_pin_19": "gpio_pin",
        "gpio_pin_20": "gpio_pin",
        "gpio_pin_21": "gpio_pin",
        "gpio_pin_22": "gpio_pin",
        "gpio_pin_23": "gpio_pin",
    }

    ACTION_CATEGORIES = {
        "⚡ Power & Control": ["bbt_power", "set_relay", "set_all_relays", "set_voltage", "set_pwm"],
        "🔍 Checks": ["check_bbt_input", "check_gcu_triac_relay", "check_state"],
        "🔀 Logic": ["if_else", "bbt_auto_inlet", "bbt_auto_drain", "wait"],
        "📦 Groups": ["call_group"],
        "🖥 GCU Commands": [
            "gcu_program_start", "gcu_low_power", "gcu_end_program",
            "gcu_set_variant", "gcu_test_mode_flag", "gcu_stop_program",
            "gcu_flowmeter", "gcu_start_inlet", "gcu_turbidity_calibration",
            "gcu_temperature_value", "gcu_temperature_mode",
            "gcu_set_pressure", "gcu_pressure_calibration",
            "gcu_gpio", "gcu_program_flags_set", "gcu_program_flags_clear",
            "gcu_heater_process",
        ],
        "⚙ GCU Sequences": [
            "gcu_pumps_set_circ", "gcu_pumps_set_drain",
            "gcu_start_drain", "gcu_start_soft_rinse", "gcu_start_soft_reg",
            "gcu_start_rinse_aid_disp", "gcu_start_main_disp", "gcu_start_scs",
        ],
    }

    ACTION_COLORS = {
        "bbt_power": "#162b22",
        "set_relay": "#162b22",
        "set_all_relays": "#162b22",
        "set_voltage": "#162b22",
        "set_pwm": "#162b22",
        "check_bbt_input": "#122833",
        "check_gcu_triac_relay": "#122833",
        "check_state": "#122833",
        "wait": "#3A3520",
        "gcu_program_start": "#231a30",
        "gcu_low_power": "#231a30",
        "gcu_end_program": "#231a30",
        "gcu_set_variant": "#231a30",
        "gcu_test_mode_flag": "#231a30",
        "gcu_stop_program": "#231a30",
        "gcu_flowmeter": "#231a30",
        "gcu_start_inlet": "#231a30",
        "gcu_turbidity_calibration": "#231a30",
        "gcu_temperature_value": "#231a30",
        "gcu_temperature_mode": "#231a30",
        "gcu_set_pressure": "#231a30",
        "gcu_pressure_calibration": "#231a30",
        "gcu_gpio": "#231a30",
        "gcu_program_flags_set": "#231a30",
        "gcu_program_flags_clear": "#231a30",
        "gcu_heater_process": "#231a30",
        "gcu_pumps_set_circ": "#231a30",
        "gcu_pumps_set_drain": "#231a30",
        "gcu_start_drain": "#231a30",
        "gcu_start_soft_rinse": "#231a30",
        "gcu_start_soft_reg": "#231a30",
        "gcu_start_rinse_aid_disp": "#231a30",
        "gcu_start_main_disp": "#231a30",
        "gcu_start_scs": "#231a30",
        "if_else": "#300d0d",
        "bbt_auto_inlet": "#0d2a2a",
        "bbt_auto_drain": "#2a1a0a",
        "call_group": "#1a2535",
    }

    PARAM_LABELS = {
        "delay_s": "Delay (s)",
        "timeout_s": "Timeout (s)",
        "duration_s": "Duration (s)",
        "expected_value": "Expected Value",
        "expected_state": "Expected State",
        "wait_until": "Wait Until Match",
        "relay_index": "Relay",
        "gcu_relay_index": "GCU Relay",
        "input_index": "Input",
        "pwm_channel": "PWM Channel",
        "duty_cycle": "Duty Cycle (%)",
        "frequency": "Frequency (Hz)",
        "output": "Output",
        "state": "State",
        "program_id": "Program ID",
        "mode": "Mode",
        "ado": "ADO",
        "variant": "Variant",
        "flag": "Flag",
        "window": "Window",
        "section": "Section",
        "field": "Field",
        "time_max": "Time Max",
        "max_temp": "Max Temp",
        "min_temp": "Min Temp",
        "pos_req": "Position Request",
        "fan_seq": "Fan Sequence",
        "n_sum": "N Sum",
        "pulses": "Pulses",
        "n_sum_pulses": "N Sum Pulses",
        "idx": "Index",
        "tx": "TX Byte",
        "pump_speed": "Pump Speed",
        "div_seq": "Diverter Seq",
        "intake_size": "Intake Size",
        "dose": "Dose",
        "calib_voltage": "Calib Voltage (mV)",
        "t_water": "T Water (1/100°C)",
        "arg": "Arg",
    }

    PARAM_TOOLTIPS = {
        "delay_s": "Time to wait after the command executes",
        "timeout_s": "Maximum time to wait for the expected condition",
        "duration_s": "Total time to pause execution",
        "expected_value": "The value the GCU field must match",
        "expected_state": "The state the input or relay must be in",
        "wait_until": "If checked, waits until the condition is met (up to timeout). If unchecked, checks the condition once immediately.",
        "duty_cycle": "PWM duty cycle percentage (0 = off, 100 = fully on)",
        "frequency": "PWM frequency in Hz (0 = off)",
        "relay_index": "Which BBT relay to control",
        "input_index": "Which BBT input to monitor",
        "gcu_relay_index": "Which GCU relay/GPIO to check",
        "program_id": "Program ID to start",
        "variant": "Appliance variant identifier",
        "flag": "Test mode flag value",
        "pump_speed": "Pump speed value. Note: other pump will be reset to 0",
    }

    @staticmethod
    def _get_pwm_frequency_options():
        return BBTDeviceConfig.get_pwm_frequency_options()

    @staticmethod
    def _get_section_names():
        return list(TestBuilderDialog.GCU_SECTION_GROUPS.keys())

    @staticmethod
    def _get_windows_for_section(section_name):
        return TestBuilderDialog.GCU_SECTION_GROUPS.get(section_name, [section_name])

    @staticmethod
    def _get_gcu_window_names():
        return list(TestBuilderDialog.GCU_WINDOWS.keys())

    @staticmethod
    def _get_fields_for_window(window_name):
        return list(TestBuilderDialog.GCU_WINDOWS.get(window_name, {}).values())

    @staticmethod
    def _get_field_key_from_display(window_name, display_name):
        if window_name in TestBuilderDialog.GCU_WINDOWS:
            for key, value in TestBuilderDialog.GCU_WINDOWS[window_name].items():
                if value == display_name:
                    return key
        return None

    @staticmethod
    def _get_state_options_for_field(field_key):
        if field_key in TestBuilderDialog.FIELD_STATE_MAPS:
            state_map_key = TestBuilderDialog.FIELD_STATE_MAPS[field_key]
            return list(STATE_MAPS.get(state_map_key, {}).values())
        return None

    ACTIONS = {
        "bbt_power": {
            "name": "BBT Device Power",
            "icon": "🔋",
            "params": {
                "state": {"type": "choice", "options": ["ON", "OFF"], "default": "ON"},
                "delay_s": {"type": "float", "min": BBTDeviceConfig.DELAY_MIN, "max": BBTDeviceConfig.DELAY_MAX, "default": BBTDeviceConfig.DELAY_DEFAULT, "step": 0.1}
            }
        },
        "set_relay": {
            "name": "Set Relay State",
            "icon": "🎚️",
            "params": {
                "relay_index": {"type": "choice"},
                "state": {"type": "choice", "options": ["ON", "OFF"], "default": "ON"},
                "delay_s": {"type": "float", "min": BBTDeviceConfig.DELAY_MIN, "max": BBTDeviceConfig.DELAY_MAX, "default": BBTDeviceConfig.DELAY_DEFAULT, "step": 0.1}
            }
        },
        "set_all_relays": {
            "name": "Set All Relays",
            "icon": "🔌",
            "params": {
                "state": {"type": "choice", "options": ["ON", "OFF"], "default": "ON"},
                "delay_s": {"type": "float", "min": BBTDeviceConfig.DELAY_MIN, "max": BBTDeviceConfig.DELAY_MAX, "default": BBTDeviceConfig.DELAY_DEFAULT, "step": 0.1}
            }
        },
        "set_voltage": {
            "name": "Set Voltage",
            "icon": "⚡",
            "params": {
                "output": {"type": "choice"},
                "voltage": {"type": "float", "min": BBTDeviceConfig.VOLTAGE_MIN, "max": BBTDeviceConfig.VOLTAGE_MAX, "default": BBTDeviceConfig.VOLTAGE_DEFAULT, "step": BBTDeviceConfig.VOLTAGE_STEP},
                "delay_s": {"type": "float", "min": BBTDeviceConfig.DELAY_MIN, "max": BBTDeviceConfig.DELAY_MAX, "default": BBTDeviceConfig.DELAY_DEFAULT, "step": 0.1}
            }
        },
        "set_pwm": {
            "name": "Set PWM",
            "icon": "〜",
            "params": {
                "pwm_channel": {"type": "choice"},
                "frequency": {"type": "choice", "options": lambda: TestBuilderDialog._get_pwm_frequency_options(), "default": "0 (OFF)"},
                "duty_cycle": {"type": "int", "min": BBTDeviceConfig.PWM_DC_MIN, "max": BBTDeviceConfig.PWM_DC_MAX, "default": BBTDeviceConfig.PWM_DC_DEFAULT},
                "delay_s": {"type": "float", "min": BBTDeviceConfig.DELAY_MIN, "max": BBTDeviceConfig.DELAY_MAX, "default": BBTDeviceConfig.DELAY_DEFAULT, "step": 0.1}
            }
        },
        "check_bbt_input": {
            "name": "Check BBT Input",
            "icon": "🔌",
            "params": {
                "input_index": {"type": "choice"},
                "expected_state": {"type": "choice", "options": ["ON", "OFF"], "default": "ON"},
                "wait_until": {"type": "bool", "default": True, "label": "Wait until match"},
                "timeout_s": {"type": "float", "min": 1.0, "max": 99999.0, "default": 5.0, "step": 0.5}
            }
        },
        "check_gcu_triac_relay": {
            "name": "Check GCU Triac/Relay",
            "icon": "🔁",
            "params": {
                "gcu_relay_index": {"type": "choice"},
                "expected_state": {"type": "choice", "options": ["ON", "OFF"], "default": "ON"},
                "wait_until": {"type": "bool", "default": True, "label": "Wait until match"},
                "timeout_s": {"type": "float", "min": 1.0, "max": 99999.0, "default": 5.0, "step": 0.5}
            }
        },
        "check_state": {
            "name": "Check GCU State",
            "icon": "🔍",
            "params": {
                "section": {"type": "choice", "options": lambda: TestBuilderDialog._get_section_names(), "default": "Faults"},
                "window": {"type": "choice", "options": [], "default": "Faults"},
                "field": {"type": "choice", "options": [], "default": "Failure State"},
                "operator": {"type": "choice", "options": ["==", ">", ">=", "<", "<="], "default": "=="},
                "expected_value": {"type": "text", "default": ""},
                "wait_until": {"type": "bool", "default": True, "label": "Wait until match"},
                "timeout_s": {"type": "float", "min": 1.0, "max": 99999.0, "default": 5.0, "step": 0.5}
            }
        },
        "wait": {
            "name": "Wait (Delay)",
            "icon": "⏱",
            "params": {"duration_s": {"type": "float", "min": 0.1, "max": 99999.0, "default": 1.0, "step": 0.1}}
        },

    }

    def __init__(self, parent=None, bbt_widget=None):
        super().__init__(parent)
        self.setWindowTitle("Test Builder")
        self.resize(1600, 900)
        self.parent_widget = bbt_widget
        self._resolve_action_options()
        self.test_sequence = []
        self._current_step_row = -1
        self._row_border_frames = {}
        self._row_top_frames = {}
        self._row_bot_frames = {}
        self.init_ui()

    def _resolve_action_options(self):
        for action_id, action_data in self.ACTIONS.items():
            for param_name, param_info in action_data["params"].items():
                if "options" in param_info and callable(param_info["options"]):
                    param_info["options"] = param_info["options"]()
                elif param_name == "relay_index":
                    if self.parent_widget and hasattr(self.parent_widget, 'relay_names'):
                        param_info["options"] = list(self.parent_widget.relay_names)
                        param_info["default"] = self.parent_widget.relay_names[0] if self.parent_widget.relay_names else "Relay 0"
                    else:
                        param_info["options"] = [f"Relay {i}" for i in range(8)]
                        param_info["default"] = "Relay 0"
                elif param_name == "output":
                    if self.parent_widget and hasattr(self.parent_widget, 'output_names'):
                        param_info["options"] = list(self.parent_widget.output_names)
                        param_info["default"] = self.parent_widget.output_names[0] if self.parent_widget.output_names else "Output 0"
                    else:
                        param_info["options"] = [f"Output {i}" for i in range(4)]
                        param_info["default"] = "Output 0"
                elif param_name == "pwm_channel":
                    if self.parent_widget and hasattr(self.parent_widget, 'pwm_names'):
                        param_info["options"] = list(self.parent_widget.pwm_names)
                        param_info["default"] = self.parent_widget.pwm_names[0] if self.parent_widget.pwm_names else "PWM1"
                    else:
                        param_info["options"] = ["PWM1", "PWM2"]
                        param_info["default"] = "PWM1"
                elif param_name == "input_index":
                    if self.parent_widget and hasattr(self.parent_widget, 'input_names'):
                        param_info["options"] = list(self.parent_widget.input_names)
                        param_info["default"] = self.parent_widget.input_names[0] if self.parent_widget.input_names else "Input 0"
                    else:
                        param_info["options"] = [f"Input {i}" for i in range(24)]
                        param_info["default"] = "Input 0"
                elif param_name == "gcu_relay_index":
                    gcu = getattr(self.parent_widget, 'gcu_widget', None) if self.parent_widget else None
                    names = getattr(gcu, 'relays_names', None) if gcu else None
                    if names:
                        param_info["options"] = list(names)
                        param_info["default"] = names[0]
                    else:
                        param_info["options"] = [f"Relay {i+1}" for i in range(15)]
                        param_info["default"] = "Relay 1"

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        left_panel = self._create_actions_panel()
        middle_panel = self._create_sequence_panel()
        right_panel = self._create_parameters_panel()
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(middle_panel, 2)
        main_layout.addWidget(right_panel, 1)

    def _create_actions_panel(self):
        group = QGroupBox("Available Actions")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Double-click to add:"))
        self.actions_filter = QLineEdit()
        self.actions_filter.setPlaceholderText("🔍  Filter actions...")
        self.actions_filter.setClearButtonEnabled(True)
        self.actions_filter.textChanged.connect(self._filter_actions)
        layout.addWidget(self.actions_filter)
        self.actions_list = QListWidget()
        self.actions_list.setFont(QFont('Segoe UI', 12))
        self.actions_list.setStyleSheet("""
            QListWidget::item { padding: 6px 8px; }
            QScrollBar:vertical { background: #1a1a1a; width: 8px; margin: 0px; }
            QScrollBar::handle:vertical { background: #444444; min-height: 20px; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: #666666; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        for category_name, action_ids in self.ACTION_CATEGORIES.items():
            header_item = QListWidgetItem(f"  {category_name}")
            header_item.setFlags(Qt.NoItemFlags)
            header_item.setBackground(QBrush(QColor("#1a1a1a")))
            header_item.setForeground(QBrush(QColor("#b0b0b0")))
            font = header_item.font()
            font.setBold(True)
            font.setPointSize(9)
            header_item.setFont(font)
            self.actions_list.addItem(header_item)
            for action_id in action_ids:
                if action_id not in self.ACTIONS:
                    continue
                action_data = self.ACTIONS[action_id]
                item_text = f"   {action_data['icon']}  {action_data['name']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, action_id)
                color = self.ACTION_COLORS.get(action_id, "#2a2a2a")
                item.setBackground(QBrush(QColor(color)))
                item.setForeground(QBrush(QColor("#FFFFFF")))
                self.actions_list.addItem(item)
        self.actions_list.itemDoubleClicked.connect(self._add_action_to_sequence)
        layout.addWidget(self.actions_list)
        group.setLayout(layout)
        return group

    def _create_sequence_panel(self):
        self.sequence_group = QGroupBox("Test Sequence (0 steps)")
        group = self.sequence_group
        layout = QVBoxLayout()
        self.sequence_list = QListWidget()
        self.sequence_list.setStyleSheet("""
            QListWidget { font-size: 10pt; font-family: 'Segoe UI', 'Segoe UI Mono', monospace; font-weight: bold; outline: none; }
            QListWidget::item { border: none; padding: 0px; }
            QListWidget::item:selected { background: transparent; border: none; outline: none; }
            QListWidget::item:focus { background: transparent; border: none; outline: none; }
            QScrollBar:vertical { background: #1a1a1a; width: 8px; margin: 0px; }
            QScrollBar::handle:vertical { background: #444444; min-height: 20px; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: #666666; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        self.sequence_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.sequence_list.setDefaultDropAction(Qt.MoveAction)
        self.sequence_list.model().rowsMoved.connect(self._on_rows_moved)
        self.sequence_list.currentItemChanged.connect(self._on_sequence_item_selected)
        layout.addWidget(self.sequence_list)
        self.duration_label = QLabel("⏱ Est. duration: —")
        self.duration_label.setStyleSheet("color: #888; font-style: italic; padding: 2px 4px;")
        layout.addWidget(self.duration_label)
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Add")
        self.add_btn.clicked.connect(self._show_add_menu)
        button_layout.addWidget(self.add_btn)
        self.remove_btn = QPushButton("➖ Remove")
        self.remove_btn.clicked.connect(self._remove_selected_step)
        self.remove_btn.setEnabled(False)
        button_layout.addWidget(self.remove_btn)
        self.move_up_btn = QPushButton("▲ Up")
        self.move_up_btn.clicked.connect(self._move_step_up)
        self.move_up_btn.setEnabled(False)
        button_layout.addWidget(self.move_up_btn)
        self.move_down_btn = QPushButton("▼ Down")
        self.move_down_btn.clicked.connect(self._move_step_down)
        self.move_down_btn.setEnabled(False)
        button_layout.addWidget(self.move_down_btn)
        self.duplicate_btn = QPushButton("⧉ Duplicate")
        self.duplicate_btn.clicked.connect(self._duplicate_step)
        self.duplicate_btn.setEnabled(False)
        self.duplicate_btn.setToolTip("Duplicate selected step (Ctrl+D)")
        button_layout.addWidget(self.duplicate_btn)
        self.clear_all_btn = QPushButton("🗑 Clear All")
        self.clear_all_btn.clicked.connect(self._clear_all_steps)
        self.clear_all_btn.setToolTip("Remove all steps")
        button_layout.addWidget(self.clear_all_btn)
        layout.addLayout(button_layout)
        control_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save Test")
        self.save_btn.clicked.connect(self._save_test)
        control_layout.addWidget(self.save_btn)
        self.load_btn = QPushButton("📁 Load Test")
        self.load_btn.clicked.connect(self._load_test)
        control_layout.addWidget(self.load_btn)
        self.groups_btn = QPushButton("📦 Edit Groups")
        self.groups_btn.clicked.connect(self._open_group_editor)
        control_layout.addWidget(self.groups_btn)
        self.run_btn = QPushButton("▶️ Run Test")
        self.run_btn.clicked.connect(self._run_test)
        self.run_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        control_layout.addWidget(self.run_btn)
        layout.addLayout(control_layout)
        group.setLayout(layout)
        return group

    def _create_parameters_panel(self):
        self.params_group = QGroupBox("Step Parameters")
        self.params_layout = QFormLayout()
        info_label = QLabel("Select a step to edit its parameters")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        self.params_layout.addRow(info_label)
        self.params_group.setLayout(self.params_layout)
        self.param_widgets = {}
        return self.params_group

    def _add_action_to_sequence(self, item):
        action_id = item.data(Qt.UserRole)
        if action_id is None:
            return
        action_data = self.ACTIONS[action_id]
        step = {"action": action_id, "params": {}}
        for param_name, param_info in action_data["params"].items():
            default_value = param_info.get("default")
            if default_value is None and param_info.get("type") == "choice":
                options = param_info.get("options", [])
                default_value = options[0] if options else None
            step["params"][param_name] = default_value
        if action_id == "if_else":
            step["params"]["then_steps"] = []
            step["params"]["else_steps"] = []
            step["params"]["else_pass"] = True
        self.test_sequence.append(step)
        self._update_sequence_list()
        self.sequence_list.setCurrentRow(len(self.test_sequence) - 1)

    def _update_sequence_list(self):
        self.sequence_list.blockSignals(True)
        scroll_pos = self.sequence_list.verticalScrollBar().value()
        self.sequence_list.clear()
        n = len(self.test_sequence)
        self.sequence_group.setTitle(f"Test Sequence ({n} step{'s' if n != 1 else ''})")
        self._update_duration_label()
        if not self.test_sequence:
            placeholder = QListWidgetItem()
            placeholder.setFlags(Qt.NoItemFlags)
            placeholder.setSizeHint(QSize(0, 80))
            self.sequence_list.addItem(placeholder)
            hint_widget = QWidget()
            hint_layout = QVBoxLayout(hint_widget)
            hint_lbl = QLabel("Double-click an action\nto add it here")
            hint_lbl.setAlignment(Qt.AlignCenter)
            hint_lbl.setStyleSheet("color: #999; font-style: italic; font-size: 10pt;")
            hint_layout.addWidget(hint_lbl)
            self.sequence_list.setItemWidget(placeholder, hint_widget)
            self.sequence_list.blockSignals(False)
            return
        sel = self._current_step_row
        self._row_border_frames.clear()
        self._row_top_frames.clear()
        self._row_bot_frames.clear()
        for i, step in enumerate(self.test_sequence):
            action_data = self.ACTIONS[step["action"]]
            action_name = f"{action_data['icon']} {action_data['name']}"
            params_summary = self._format_step_params(step)
            item = QListWidgetItem()
            self.sequence_list.addItem(item)
            row_color = self.ACTION_COLORS.get(step["action"], "#3A3A3A")
            if row_color == "#162b22" and step["params"].get("state") == "OFF":
                row_color = "#0F1F1A"
            elif row_color == "#122833" and step["params"].get("expected_state") == "OFF":
                row_color = "#0B1A21"
            is_selected = (i == sel)
            outer_widget = QWidget()
            outer_layout = QVBoxLayout(outer_widget)
            outer_layout.setContentsMargins(0, 0, 0, 0)
            outer_layout.setSpacing(0)
            top_frame = QFrame()
            top_frame.setFixedHeight(2)
            top_frame.setStyleSheet("background-color: #FFFFFF;" if is_selected else "background-color: transparent;")
            outer_layout.addWidget(top_frame)
            self._row_top_frames[i] = top_frame
            row_widget = QWidget()
            row_widget.setStyleSheet(f"background-color: {row_color};")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 3, 4, 3)
            row_layout.setSpacing(6)
            border_frame = QFrame()
            border_frame.setFixedWidth(4)
            border_frame.setStyleSheet("background-color: #FFFFFF;" if is_selected else "background-color: transparent;")
            row_layout.addWidget(border_frame)
            self._row_border_frames[i] = border_frame
            outer_layout.addWidget(row_widget, 1)
            bot_frame = QFrame()
            bot_frame.setFixedHeight(2)
            bot_frame.setStyleSheet("background-color: #FFFFFF;" if is_selected else "background-color: rgba(255,255,255,25);")
            outer_layout.addWidget(bot_frame)
            self._row_bot_frames[i] = bot_frame
            badge = QLabel(str(i + 1))
            badge.setFixedSize(22, 22)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet("background-color: rgba(255,255,255,40); color: white; border-radius: 11px; font-weight: bold; font-size: 9pt;")
            row_layout.addWidget(badge)
            text_widget = QWidget()
            text_widget.setStyleSheet("background: transparent;")
            text_layout = QVBoxLayout(text_widget)
            text_layout.setContentsMargins(0, 0, 0, 0)
            text_layout.setSpacing(0)
            name_lbl = QLabel(action_name)
            name_lbl.setStyleSheet("color: #FFFFFF; background: transparent; font-weight: bold; font-size: 9pt;")
            text_layout.addWidget(name_lbl)
            if params_summary:
                params_lbl = QLabel(params_summary)
                params_lbl.setStyleSheet("color: rgba(255,255,255,175); background: transparent; font-size: 8pt; font-weight: normal;")
                text_layout.addWidget(params_lbl)
            row_layout.addWidget(text_widget, 1)
            drag_handle = QWidget()
            drag_handle.setFixedSize(18, 22)
            drag_handle.setToolTip("Drag to reorder")
            drag_handle.setCursor(Qt.SizeVerCursor)
            dh_layout = QVBoxLayout(drag_handle)
            dh_layout.setContentsMargins(2, 4, 2, 4)
            dh_layout.setSpacing(3)
            for _ in range(3):
                line = QFrame()
                line.setFixedHeight(2)
                line.setStyleSheet("background-color: rgba(255,255,255,120); border-radius: 1px;")
                dh_layout.addWidget(line)
            row_layout.addWidget(drag_handle)
            x_btn = QPushButton("✕")
            x_btn.setFixedSize(22, 22)
            x_btn.setStyleSheet("""
                QPushButton { background-color: transparent; color: rgba(255,255,255,160); font-weight: bold; border: none; font-size: 12pt; }
                QPushButton:hover { background-color: rgba(255,255,255,40); color: white; border-radius: 4px; }
            """)
            x_btn.clicked.connect(lambda checked, it=item: self._remove_step_by_item(it))
            row_layout.addWidget(x_btn)
            item.setSizeHint(QSize(0, 54))
            self.sequence_list.setItemWidget(item, outer_widget)
        if 0 <= sel < self.sequence_list.count():
            self.sequence_list.setCurrentRow(sel)
        self.sequence_list.verticalScrollBar().setValue(scroll_pos)
        self.sequence_list.blockSignals(False)

    def _remove_step_by_item(self, item):
        row = self.sequence_list.row(item)
        if row >= 0:
            del self.test_sequence[row]
            self._update_sequence_list()
            self._clear_parameters()

    def _on_rows_moved(self, parent, start, end, dest_parent, dest_row):
        moved = self.test_sequence.pop(start)
        insert_pos = dest_row - 1 if dest_row > start else dest_row
        self.test_sequence.insert(insert_pos, moved)
        self._update_sequence_list()

    def _on_sequence_item_selected(self, current, previous):
        has_selection = current is not None
        self.remove_btn.setEnabled(has_selection)
        self.move_up_btn.setEnabled(has_selection and self.sequence_list.currentRow() > 0)
        self.move_down_btn.setEnabled(has_selection and self.sequence_list.currentRow() < len(self.test_sequence) - 1)
        self.duplicate_btn.setEnabled(has_selection)
        new_row = self.sequence_list.currentRow() if has_selection else -1
        if new_row != self._current_step_row:
            old_row = self._current_step_row
            self._current_step_row = new_row
            self._refresh_row_border(old_row)
            self._refresh_row_border(new_row)
        if has_selection:
            self._show_parameters_for_step(self.sequence_list.currentRow())
        else:
            self._clear_parameters()

    def _refresh_row_border(self, row):
        is_selected = (row == self._current_step_row)
        frame = self._row_border_frames.get(row)
        if frame:
            frame.setStyleSheet("background-color: #FFFFFF;" if is_selected else "background-color: transparent;")
        top = self._row_top_frames.get(row)
        if top:
            top.setStyleSheet("background-color: #FFFFFF;" if is_selected else "background-color: transparent;")
        bot = self._row_bot_frames.get(row)
        if bot:
            bot.setStyleSheet("background-color: #FFFFFF;" if is_selected else "background-color: rgba(255,255,255,25);")

    def _show_parameters_for_step(self, step_index):
        if step_index < 0 or step_index >= len(self.test_sequence):
            return
        self._clear_parameters()
        step = self.test_sequence[step_index]
        action_id = step["action"]
        action_data = self.ACTIONS[action_id]
        self.params_group.setTitle(f"Step {step_index + 1}: {action_data['icon']} {action_data['name']}")
        self.param_widgets.clear()
        if action_id == "if_else":
            self._show_if_else_parameters(step_index)
            return
        if action_id == "call_group":
            self._show_call_group_parameters(step_index)
            return
        for param_name, param_info in action_data["params"].items():
            current_value = step["params"].get(param_name, param_info.get("default"))
            widget = None
            if param_info["type"] == "int":
                widget = QSpinBox()
                widget.setMinimum(param_info["min"])
                widget.setMaximum(param_info["max"])
                value = current_value if current_value is not None else param_info.get("default", param_info["min"])
                widget.setValue(int(value))
                widget.valueChanged.connect(lambda val, idx=step_index, name=param_name: self._update_parameter(idx, name, val))
            elif param_info["type"] == "float":
                widget = QDoubleSpinBox()
                widget.setMinimum(param_info["min"])
                widget.setMaximum(param_info["max"])
                widget.setSingleStep(param_info.get("step", 0.1))
                value = current_value if current_value is not None else param_info.get("default", param_info["min"])
                widget.setValue(float(value))
                widget.valueChanged.connect(lambda val, idx=step_index, name=param_name: self._update_parameter(idx, name, val))
            elif param_info["type"] == "choice":
                widget = QComboBox()
                if action_id == "check_state" and param_name == "field":
                    window_name = step["params"].get("window", "Faults")
                    if not window_name or window_name not in self.GCU_WINDOWS:
                        section_name = step["params"].get("section", "Faults")
                        window_name = self._get_windows_for_section(section_name)[0]
                    fields = self._get_fields_for_window(window_name)
                    widget.addItems(fields)
                    if current_value and str(current_value) in fields:
                        widget.setCurrentText(str(current_value))
                    elif fields:
                        widget.setCurrentIndex(0)
                elif action_id == "check_state" and param_name == "window":
                    section_name = step["params"].get("section", "Faults")
                    window_options = self._get_windows_for_section(section_name)
                    widget.addItems(window_options)
                    if current_value and str(current_value) in window_options:
                        widget.setCurrentText(str(current_value))
                    elif window_options:
                        widget.setCurrentIndex(0)
                    if len(window_options) <= 1:
                        widget.setVisible(False)
                        self._pending_hide_window_label = True
                elif action_id == "check_state" and param_name == "operator":
                    options = ["==", ">", ">=", "<", "<="]
                    widget.addItems(options)
                    if current_value and str(current_value) in options:
                        widget.setCurrentText(str(current_value))
                    else:
                        widget.setCurrentIndex(0)
                    window_name = step["params"].get("window", "Faults")
                    field_display = step["params"].get("field", "")
                    field_key = self._get_field_key_from_display(window_name, field_display)
                    if field_key:
                        state_options = self._get_state_options_for_field(field_key)
                        if state_options:
                            widget.setVisible(False)
                            self._pending_hide_operator_label = True
                elif action_id == "set_pwm" and param_name == "frequency":
                    pwm_ch_val = step["params"].get("pwm_channel", "")
                    pwm_names = getattr(self.parent_widget, 'pwm_names', []) if self.parent_widget else []
                    try:
                        ch_idx = pwm_names.index(pwm_ch_val) + 1
                    except (ValueError, AttributeError):
                        ch_idx = 1
                    options = BBTDeviceConfig.get_pwm_frequency_options(pwm_channel=ch_idx)
                    widget.addItems(options)
                    if current_value and str(current_value) in options:
                        widget.setCurrentText(str(current_value))
                    else:
                        widget.setCurrentIndex(0)
                elif "options" in param_info and param_info["options"]:
                    widget.addItems(param_info["options"])
                    if current_value and str(current_value) in param_info["options"]:
                        widget.setCurrentText(str(current_value))
                    elif current_value is None and "default" in param_info:
                        widget.setCurrentText(str(param_info["default"]))
                    else:
                        widget.setCurrentIndex(0)
                else:
                    widget.addItem(str(current_value) if current_value else "N/A")
                if action_id == "check_state" and param_name == "section":
                    widget.currentTextChanged.connect(lambda val, idx=step_index: self._update_check_state_section(idx, val))
                elif action_id == "check_state" and param_name == "window":
                    widget.currentTextChanged.connect(lambda val, idx=step_index: self._update_check_state_window(idx, val))
                elif action_id == "check_state" and param_name == "field":
                    widget.currentTextChanged.connect(lambda val, idx=step_index: self._update_check_state_field(idx, val))
                elif action_id == "set_pwm" and param_name == "pwm_channel":
                    widget.currentTextChanged.connect(lambda val, idx=step_index: self._update_pwm_channel(idx, val))
                else:
                    widget.currentTextChanged.connect(lambda val, idx=step_index, name=param_name: self._update_parameter(idx, name, val))
            elif param_info["type"] == "bool":
                widget = QCheckBox()
                value = current_value if current_value is not None else param_info.get("default", False)
                widget.setChecked(bool(value))
                widget.stateChanged.connect(lambda state, idx=step_index, name=param_name: self._update_parameter(idx, name, bool(state)))
            elif param_info["type"] == "gpio_pins":
                container = QWidget()
                grid = QGridLayout(container)
                grid.setContentsMargins(0, 0, 0, 0)
                grid.setSpacing(3)
                bitmask = int(current_value) if current_value is not None else param_info.get("default", 0)
                pin_names = list(self.GCU_WINDOWS["GPIO"].values())
                checkboxes = []
                for pin_idx, pin_name in enumerate(pin_names):
                    cb = QCheckBox(f"{pin_idx}: {pin_name}")
                    cb.setChecked(bool(bitmask & (1 << pin_idx)))
                    checkboxes.append(cb)
                    grid.addWidget(cb, pin_idx // 4, pin_idx % 4)
                def _make_gpio_handler(cbs, idx, name):
                    def _on_toggle():
                        val = sum(1 << i for i, cb in enumerate(cbs) if cb.isChecked())
                        self._update_parameter(idx, name, val)
                    return _on_toggle
                handler = _make_gpio_handler(checkboxes, step_index, param_name)
                for _cb in checkboxes:
                    _cb.stateChanged.connect(handler)
                widget = container
            elif param_info["type"] == "text":
                if action_id == "check_state" and param_name == "expected_value":
                    window_name = step["params"].get("window", "Faults")
                    field_display = step["params"].get("field", "Failure State")
                    field_key = self._get_field_key_from_display(window_name, field_display)
                    if field_key:
                        state_options = self._get_state_options_for_field(field_key)
                        if state_options:
                            widget = QComboBox()
                            widget.addItems(state_options)
                            if current_value and str(current_value) in state_options:
                                widget.setCurrentText(str(current_value))
                            else:
                                widget.setCurrentIndex(0)
                            widget.currentTextChanged.connect(lambda val, idx=step_index, name=param_name: self._update_parameter(idx, name, val))
                        else:
                            widget = QLineEdit()
                            value = current_value if current_value is not None else param_info.get("default", "")
                            widget.setText(str(value))
                            widget.setPlaceholderText("Enter expected value...")
                            widget.textChanged.connect(lambda val, idx=step_index, name=param_name: self._update_parameter(idx, name, val))
                    else:
                        widget = QLineEdit()
                        value = current_value if current_value is not None else param_info.get("default", "")
                        widget.setText(str(value))
                        widget.textChanged.connect(lambda val, idx=step_index, name=param_name: self._update_parameter(idx, name, val))
                else:
                    widget = QLineEdit()
                    value = current_value if current_value is not None else param_info.get("default", "")
                    widget.setText(str(value))
                    widget.textChanged.connect(lambda val, idx=step_index, name=param_name: self._update_parameter(idx, name, val))
            if widget is None:
                continue
            self.param_widgets[param_name] = widget
            label_text = param_info.get("label", self.PARAM_LABELS.get(param_name, param_name.replace("_", " ").title()))
            self.params_layout.addRow(f"{label_text}:", widget)
            if param_name in self.PARAM_TOOLTIPS:
                widget.setToolTip(self.PARAM_TOOLTIPS[param_name])
            if getattr(self, '_pending_hide_window_label', False):
                row_idx = self.params_layout.rowCount() - 1
                label_item = self.params_layout.itemAt(row_idx, QFormLayout.LabelRole)
                if label_item and label_item.widget():
                    label_item.widget().setVisible(False)
                self._pending_hide_window_label = False
            if getattr(self, '_pending_hide_operator_label', False):
                row_idx = self.params_layout.rowCount() - 1
                label_item = self.params_layout.itemAt(row_idx, QFormLayout.LabelRole)
                if label_item and label_item.widget():
                    label_item.widget().setVisible(False)
                self._pending_hide_operator_label = False

    def _clear_parameters(self):
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.param_widgets.clear()
        self.params_group.setTitle("Step Parameters")

    def _update_parameter(self, step_index, param_name, value):
        if step_index < len(self.test_sequence):
            self.test_sequence[step_index]["params"][param_name] = value
            self._update_sequence_list()
            self.sequence_list.setCurrentRow(step_index)

    def _update_pwm_channel(self, step_index, channel_name):
        self._update_parameter(step_index, "pwm_channel", channel_name)
        pwm_names = getattr(self.parent_widget, 'pwm_names', []) if self.parent_widget else []
        try:
            ch_idx = pwm_names.index(channel_name) + 1
        except (ValueError, AttributeError):
            ch_idx = 1
        if "frequency" in self.param_widgets:
            freq_combo = self.param_widgets["frequency"]
            options = BBTDeviceConfig.get_pwm_frequency_options(pwm_channel=ch_idx)
            freq_combo.blockSignals(True)
            freq_combo.clear()
            freq_combo.addItems(options)
            freq_combo.setCurrentIndex(0)
            freq_combo.blockSignals(False)
            if step_index < len(self.test_sequence):
                self.test_sequence[step_index]["params"]["frequency"] = options[0]

    def _update_check_state_window(self, step_index, window_name):
        if step_index >= len(self.test_sequence):
            return
        self.test_sequence[step_index]["params"]["window"] = window_name
        fields = self._get_fields_for_window(window_name)
        if "field" in self.param_widgets:
            field_combo = self.param_widgets["field"]
            field_combo.clear()
            field_combo.addItems(fields)
            if fields:
                self.test_sequence[step_index]["params"]["field"] = fields[0]
                self._update_check_state_field(step_index, fields[0])
        self._update_sequence_list()
        self.sequence_list.setCurrentRow(step_index)

    def _update_check_state_section(self, step_index, section_name):
        if step_index >= len(self.test_sequence):
            return
        self.test_sequence[step_index]["params"]["section"] = section_name
        windows = self._get_windows_for_section(section_name)
        if "window" in self.param_widgets:
            win_combo = self.param_widgets["window"]
            win_combo.blockSignals(True)
            win_combo.clear()
            win_combo.addItems(windows)
            win_combo.blockSignals(False)
            show_window = len(windows) > 1
            win_combo.setVisible(show_window)
            for row in range(self.params_layout.rowCount()):
                label_item = self.params_layout.itemAt(row, QFormLayout.LabelRole)
                field_item = self.params_layout.itemAt(row, QFormLayout.FieldRole)
                if field_item and field_item.widget() is win_combo:
                    if label_item and label_item.widget():
                        label_item.widget().setVisible(show_window)
                    break
            first_win = windows[0] if windows else "Faults"
            self.test_sequence[step_index]["params"]["window"] = first_win
            self._update_check_state_window(step_index, first_win)

    def _update_check_state_field(self, step_index, field_display_name):
        if step_index >= len(self.test_sequence):
            return
        self.test_sequence[step_index]["params"]["field"] = field_display_name
        window_name = self.test_sequence[step_index]["params"].get("window", "Faults")
        field_key = self._get_field_key_from_display(window_name, field_display_name)
        if not field_key:
            return
        state_options = self._get_state_options_for_field(field_key)
        if "operator" in self.param_widgets:
            op_widget = self.param_widgets["operator"]
            is_numeric = not bool(state_options)
            op_widget.setVisible(is_numeric)
            for row in range(self.params_layout.rowCount()):
                label_item = self.params_layout.itemAt(row, QFormLayout.LabelRole)
                field_item = self.params_layout.itemAt(row, QFormLayout.FieldRole)
                if field_item and field_item.widget() is op_widget:
                    if label_item and label_item.widget():
                        label_item.widget().setVisible(is_numeric)
                    break
            if not is_numeric:
                self.test_sequence[step_index]["params"]["operator"] = "=="
        if "expected_value" in self.param_widgets:
            old_widget = self.param_widgets["expected_value"]
            self.params_layout.removeRow(old_widget)
            if state_options:
                widget = QComboBox()
                widget.addItems(state_options)
                current_value = self.test_sequence[step_index]["params"].get("expected_value", "")
                if current_value in state_options:
                    widget.setCurrentText(current_value)
                else:
                    widget.setCurrentIndex(0)
                    self.test_sequence[step_index]["params"]["expected_value"] = state_options[0]
                widget.currentTextChanged.connect(lambda val, idx=step_index: self._update_parameter(idx, "expected_value", val))
            else:
                widget = QLineEdit()
                current_value = self.test_sequence[step_index]["params"].get("expected_value", "")
                widget.setText(str(current_value))
                widget.setPlaceholderText("Enter expected value...")
                widget.textChanged.connect(lambda val, idx=step_index: self._update_parameter(idx, "expected_value", val))
            self.param_widgets["expected_value"] = widget
            insert_position = -1
            for i in range(self.params_layout.rowCount()):
                label = self.params_layout.itemAt(i, QFormLayout.LabelRole)
                if label and label.widget() and label.widget().text() == self.PARAM_LABELS.get("field", "Field") + ":":
                    insert_position = i + 1
                    break
            ev_label = self.PARAM_LABELS.get("expected_value", "Expected Value")
            if insert_position >= 0:
                self.params_layout.insertRow(insert_position, f"{ev_label}:", widget)
            else:
                self.params_layout.addRow(f"{ev_label}:", widget)
        self._update_sequence_list()
        self.sequence_list.setCurrentRow(step_index)

    def _show_add_menu(self):
        if self.actions_list.currentItem():
            self._add_action_to_sequence(self.actions_list.currentItem())

    def _remove_selected_step(self):
        current_row = self.sequence_list.currentRow()
        if current_row >= 0:
            del self.test_sequence[current_row]
            self._update_sequence_list()

    def _move_step_up(self):
        current_row = self.sequence_list.currentRow()
        if current_row > 0:
            self.test_sequence[current_row], self.test_sequence[current_row - 1] = self.test_sequence[current_row - 1], self.test_sequence[current_row]
            self._update_sequence_list()
            self.sequence_list.setCurrentRow(current_row - 1)

    def _move_step_down(self):
        current_row = self.sequence_list.currentRow()
        if current_row < len(self.test_sequence) - 1:
            self.test_sequence[current_row], self.test_sequence[current_row + 1] = self.test_sequence[current_row + 1], self.test_sequence[current_row]
            self._update_sequence_list()
            self.sequence_list.setCurrentRow(current_row + 1)

    def _save_test(self):
        if not self.test_sequence:
            QMessageBox.warning(self, "Empty Test", "No test steps to save!")
            return
        tests_dir = os.path.join(get_device_dir(), 'tests')
        os.makedirs(tests_dir, exist_ok=True)
        filename, _ = QFileDialog.getSaveFileName(self, "Save Test Sequence", tests_dir, "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.test_sequence, f, indent=2)
                QMessageBox.information(self, "Success", f"Test saved to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save test:\n{str(e)}")

    def _load_test(self):
        tests_dir = os.path.join(get_device_dir(), 'tests')
        os.makedirs(tests_dir, exist_ok=True)
        filename, _ = QFileDialog.getOpenFileName(self, "Load Test Sequence", tests_dir, "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.test_sequence = json.load(f)
                self._update_sequence_list()
                QMessageBox.information(self, "Success", f"Test loaded from:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load test:\n{str(e)}")

    def _run_test(self):
        if not self.test_sequence:
            QMessageBox.warning(self, "Empty Test", "No test steps to run!")
            return
        self.accept()

    def _filter_actions(self, text):
        text = text.strip().lower()
        i = 0
        while i < self.actions_list.count():
            item = self.actions_list.item(i)
            action_id = item.data(Qt.UserRole)
            if action_id is None:
                header_item = item
                i += 1
                any_visible = False
                while i < self.actions_list.count():
                    child = self.actions_list.item(i)
                    if child.data(Qt.UserRole) is None:
                        break
                    if not text:
                        child.setHidden(False)
                        any_visible = True
                    else:
                        action_name = self.ACTIONS.get(child.data(Qt.UserRole), {}).get("name", "").lower()
                        hidden = text not in action_name
                        child.setHidden(hidden)
                        if not hidden:
                            any_visible = True
                    i += 1
                header_item.setHidden(bool(text) and not any_visible)
            else:
                i += 1

    def _update_duration_label(self):
        def _sum_steps(steps):
            t = 0.0
            for s in steps:
                p = s.get("params", {})
                t += float(p.get("delay_s", 0) or 0)
                t += float(p.get("duration_s", 0) or 0)
                if p.get("wait_until", False):
                    t += float(p.get("timeout_s", 0) or 0)
                if s.get("action") == "if_else":
                    t += max(_sum_steps(p.get("then_steps", [])), _sum_steps(p.get("else_steps", [])))
            return t
        total = _sum_steps(self.test_sequence)
        self.duration_label.setText(f"⏱ Est. duration: ~{total:.1f} s" if self.test_sequence else "⏱ Est. duration: —")

    def _format_step_params(self, step):
        params = step["params"]
        if step.get("action") == "if_else":
            ctype = params.get("condition_type", "GCU State")
            if ctype == "GCU State":
                cond = f"{params.get('field','?')}={params.get('expected_value','?')}"
            elif ctype == "BBT Input":
                cond = f"{params.get('input_index','?')}={params.get('input_expected_state','ON')}"
            else:
                cond = f"{params.get('gcu_relay_index','?')}={params.get('relay_expected_state','ON')}"
            then_n = len(params.get("then_steps", []))
            else_n = len(params.get("else_steps", []))
            else_pass = params.get("else_pass", True)
            else_txt = "PASS" if (else_pass and else_n == 0) else f"{else_n} step(s)"
            return f"IF {ctype}: {cond}  |  THEN: {then_n}  |  ELSE: {else_txt}"
        if step.get("action") == "call_group":
            gf = params.get("group_file", "")
            name = os.path.splitext(os.path.basename(gf))[0] if gf else "(none)"
            return f"→ {name}"
        parts = []
        if "state" in params:
            parts.append(f"→ {params['state']}")
        for k in ("relay_index", "input_index", "output", "pwm_channel", "gcu_relay_index"):
            if k in params and params[k] is not None:
                parts.append(str(params[k]))
                break
        if "voltage" in params:
            parts.append(f"{params['voltage']} V")
        if "frequency" in params and "duty_cycle" in params:
            parts.append(f"{params['frequency']} Hz  {params['duty_cycle']}%")
        if "expected_state" in params:
            parts.append(f"= {params['expected_state']}")
        if "window" in params and "field" in params:
            parts.append(f"{params['window']} › {params['field']}")
        if "expected_value" in params:
            parts.append(f"= {params['expected_value']}")
        if "program_id" in params:
            parts.append(f"prog {params['program_id']}")
        if "duration_s" in params:
            parts.append(f"{params['duration_s']} s")
        if "variant" in params:
            parts.append(f"variant={params['variant']}")
        if "flag" in params:
            parts.append(f"flag={params['flag']}")
        delay = params.get("delay_s")
        if delay is not None:
            parts.append(f"delay {delay} s")
        timeout = params.get("timeout_s")
        if timeout is not None:
            wait = params.get("wait_until", True)
            parts.append(f"timeout {timeout} s" + (" (wait)" if wait else " (check)"))
        return "  |  ".join(parts)

    def _duplicate_step(self):
        current_row = self.sequence_list.currentRow()
        if current_row < 0 or current_row >= len(self.test_sequence):
            return
        import copy
        step_copy = copy.deepcopy(self.test_sequence[current_row])
        self.test_sequence.insert(current_row + 1, step_copy)
        self._update_sequence_list()
        self.sequence_list.setCurrentRow(current_row + 1)

    def _clear_all_steps(self):
        if not self.test_sequence:
            return
        reply = QMessageBox.question(self, "Clear All Steps", f"Remove all {len(self.test_sequence)} step(s)?", QMessageBox.Yes | QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            self.test_sequence.clear()
            self._update_sequence_list()
            self._clear_parameters()

    def _show_call_group_parameters(self, step_index):
        step = self.test_sequence[step_index]
        params = step["params"]
        self.params_group.setTitle(f"Step {step_index + 1}: 📦 Call Group")
        groups_dir = get_groups_dir()
        group_files = sorted([f for f in os.listdir(groups_dir) if f.endswith('.json')]) if os.path.isdir(groups_dir) else []
        combo = QComboBox()
        if group_files:
            combo.addItems(group_files)
            current = params.get("group_file", "")
            current_basename = os.path.basename(current) if current else ""
            if current_basename in group_files:
                combo.setCurrentText(current_basename)
            else:
                combo.setCurrentIndex(0)
                params["group_file"] = os.path.join(groups_dir, group_files[0])
        else:
            combo.addItem("(no groups found)")
            combo.setEnabled(False)
        def _on_group_selected(name, idx=step_index):
            self.test_sequence[idx]["params"]["group_file"] = os.path.join(get_groups_dir(), name)
            self._update_sequence_list()
            self.sequence_list.setCurrentRow(idx)
        combo.currentTextChanged.connect(_on_group_selected)
        self.params_layout.addRow("Group:", combo)
        self.param_widgets["group_file"] = combo
        refresh_btn = QPushButton("🔄 Refresh list")
        refresh_btn.clicked.connect(lambda: self._show_call_group_parameters(step_index))
        self.params_layout.addRow("", refresh_btn)

    def _open_group_editor(self):
        groups_dir = get_groups_dir()
        editor = _GroupEditorDialog(groups_dir=groups_dir, parent=self, bbt_widget=self.parent_widget)
        editor.show()

    def _show_if_else_parameters(self, step_index):
        step = self.test_sequence[step_index]
        params = step["params"]
        self.params_group.setTitle(f"Step {step_index + 1}: 🔀 IF / ELSE Block")
        ctype_combo = QComboBox()
        ctype_combo.addItems(["GCU State", "BBT Input", "GCU Triac/Relay"])
        ctype_combo.setCurrentText(params.get("condition_type", "GCU State"))
        self.params_layout.addRow("Condition Type:", ctype_combo)
        self.param_widgets["condition_type"] = ctype_combo
        self._condition_container = QWidget()
        self._condition_layout = QFormLayout(self._condition_container)
        self._condition_layout.setContentsMargins(0, 0, 0, 0)
        self._condition_layout.setSpacing(4)
        self.params_layout.addRow(self._condition_container)
        self._fill_condition_layout(step_index, ctype_combo.currentText())
        ctype_combo.currentTextChanged.connect(lambda val, idx=step_index: self._on_if_else_condition_type_changed(idx, val))
        wait_check = QCheckBox("Wait until condition is met")
        wait_check.setChecked(bool(params.get("wait_until", True)))
        wait_check.stateChanged.connect(lambda state, idx=step_index: self._update_if_else_param(idx, "wait_until", bool(state)))
        self.params_layout.addRow("Wait Until:", wait_check)
        self.param_widgets["wait_until"] = wait_check
        timeout_spin = QDoubleSpinBox()
        timeout_spin.setMinimum(1.0)
        timeout_spin.setMaximum(99999.0)
        timeout_spin.setSingleStep(0.5)
        timeout_spin.setValue(float(params.get("timeout_s", 5.0)))
        timeout_spin.valueChanged.connect(lambda val, idx=step_index: self._update_if_else_param(idx, "timeout_s", val))
        self.params_layout.addRow("Timeout (s):", timeout_spin)
        self.param_widgets["timeout_s"] = timeout_spin
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("color: #555;")
        self.params_layout.addRow(sep1)
        then_widget = self._build_branch_widget(step_index, "then_steps")
        self.params_layout.addRow("THEN Steps:", then_widget)
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #555;")
        self.params_layout.addRow(sep2)
        else_pass_check = QCheckBox("Pass (continue) if condition is NOT met")
        else_pass_check.setChecked(bool(params.get("else_pass", True)))
        else_pass_check.stateChanged.connect(lambda state, idx=step_index: self._update_if_else_param(idx, "else_pass", bool(state)))
        self.params_layout.addRow("ELSE:", else_pass_check)
        self.param_widgets["else_pass"] = else_pass_check
        else_widget = self._build_branch_widget(step_index, "else_steps")
        self.params_layout.addRow("ELSE Steps:", else_widget)

    def _fill_condition_layout(self, step_index, ctype):
        params = self.test_sequence[step_index]["params"]
        layout = self._condition_layout
        while layout.count():
            it = layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        if ctype == "GCU State":
            section_name = params.get("section", "Faults")
            section_combo = QComboBox()
            section_combo.addItems(self._get_section_names())
            section_combo.setCurrentText(section_name)
            layout.addRow("Section:", section_combo)
            win_combo = QComboBox()
            win_options = self._get_windows_for_section(section_name)
            win_combo.addItems(win_options)
            current_win = params.get("window", win_options[0] if win_options else "Faults")
            if current_win in win_options:
                win_combo.setCurrentText(current_win)
            elif win_options:
                win_combo.setCurrentIndex(0)
                params["window"] = win_options[0]
            show_win = len(win_options) > 1
            win_label = QLabel("Window:")
            win_label.setVisible(show_win)
            win_combo.setVisible(show_win)
            layout.addRow(win_label, win_combo)
            field_combo = QComboBox()
            fields = self._get_fields_for_window(win_combo.currentText())
            field_combo.addItems(fields)
            current_field = params.get("field", "")
            if current_field in fields:
                field_combo.setCurrentText(current_field)
            elif fields:
                field_combo.setCurrentIndex(0)
                params["field"] = fields[0]
            layout.addRow("Field:", field_combo)
            field_key = self._get_field_key_from_display(win_combo.currentText(), field_combo.currentText())
            state_options = self._get_state_options_for_field(field_key) if field_key else None
            if state_options:
                params["operator"] = "=="
                val_widget = QComboBox()
                val_widget.addItems(state_options)
                cur_val = str(params.get("expected_value", ""))
                if cur_val in state_options:
                    val_widget.setCurrentText(cur_val)
                else:
                    val_widget.setCurrentIndex(0)
                    params["expected_value"] = state_options[0]
                val_widget.currentTextChanged.connect(lambda v, idx=step_index: self._update_if_else_param(idx, "expected_value", v))
                layout.addRow("Expected Value:", val_widget)
            else:
                op_widget = QComboBox()
                op_widget.addItems(["==", ">", ">=", "<", "<="]) 
                cur_op = str(params.get("operator", "=="))
                if cur_op in ["==", ">", ">=", "<", "<="]:
                    op_widget.setCurrentText(cur_op)
                op_widget.currentTextChanged.connect(lambda v, idx=step_index: self._update_if_else_param(idx, "operator", v))
                layout.addRow("Operator:", op_widget)
                val_widget = QLineEdit()
                val_widget.setText(str(params.get("expected_value", "")))
                val_widget.setPlaceholderText("Expected value…")
                val_widget.textChanged.connect(lambda v, idx=step_index: self._update_if_else_param(idx, "expected_value", v))
                layout.addRow("Expected Value:", val_widget)
            def _on_section(s, idx=step_index):
                self._update_if_else_param(idx, "section", s)
                wins = self._get_windows_for_section(s)
                self._update_if_else_param(idx, "window", wins[0] if wins else "Faults")
                while self._condition_layout.count():
                    it = self._condition_layout.takeAt(0)
                    if it.widget():
                        it.widget().deleteLater()
                self._fill_condition_layout(idx, "GCU State")
            def _on_win(w, idx=step_index):
                self._update_if_else_param(idx, "window", w)
                while self._condition_layout.count():
                    it = self._condition_layout.takeAt(0)
                    if it.widget():
                        it.widget().deleteLater()
                self._fill_condition_layout(idx, "GCU State")
            def _on_field(f, idx=step_index):
                self._update_if_else_param(idx, "field", f)
                while self._condition_layout.count():
                    it = self._condition_layout.takeAt(0)
                    if it.widget():
                        it.widget().deleteLater()
                self._fill_condition_layout(idx, "GCU State")
            section_combo.currentTextChanged.connect(_on_section)
            win_combo.currentTextChanged.connect(_on_win)
            field_combo.currentTextChanged.connect(_on_field)
        elif ctype == "BBT Input":
            options = self.ACTIONS["if_else"]["params"]["input_index"].get("options", [])
            inp_combo = QComboBox()
            inp_combo.addItems(options)
            cur = params.get("input_index", "")
            if cur in options:
                inp_combo.setCurrentText(cur)
            elif options:
                inp_combo.setCurrentIndex(0)
                params["input_index"] = options[0]
            layout.addRow("Input:", inp_combo)
            inp_combo.currentTextChanged.connect(lambda v, idx=step_index: self._update_if_else_param(idx, "input_index", v))
            state_combo = QComboBox()
            state_combo.addItems(["ON", "OFF"])
            state_combo.setCurrentText(params.get("input_expected_state", "ON"))
            layout.addRow("Expected State:", state_combo)
            state_combo.currentTextChanged.connect(lambda v, idx=step_index: self._update_if_else_param(idx, "input_expected_state", v))
        elif ctype == "GCU Triac/Relay":
            options = self.ACTIONS["if_else"]["params"]["gcu_relay_index"].get("options", [])
            relay_combo = QComboBox()
            relay_combo.addItems(options)
            cur = params.get("gcu_relay_index", "")
            if cur in options:
                relay_combo.setCurrentText(cur)
            elif options:
                relay_combo.setCurrentIndex(0)
                params["gcu_relay_index"] = options[0]
            layout.addRow("GCU Triac/Relay:", relay_combo)
            relay_combo.currentTextChanged.connect(lambda v, idx=step_index: self._update_if_else_param(idx, "gcu_relay_index", v))
            state_combo = QComboBox()
            state_combo.addItems(["ON", "OFF"])
            state_combo.setCurrentText(params.get("relay_expected_state", "ON"))
            layout.addRow("Expected State:", state_combo)
            state_combo.currentTextChanged.connect(lambda v, idx=step_index: self._update_if_else_param(idx, "relay_expected_state", v))

    def _on_if_else_condition_type_changed(self, step_index, ctype):
        self.test_sequence[step_index]["params"]["condition_type"] = ctype
        while self._condition_layout.count():
            it = self._condition_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self._fill_condition_layout(step_index, ctype)
        self._update_if_else_param(step_index, "condition_type", ctype)

    def _build_branch_widget(self, step_index, branch_key):
        params = self.test_sequence[step_index]["params"]
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        list_widget = QListWidget()
        list_widget.setFixedHeight(110)
        list_widget.setStyleSheet("QListWidget { font-size: 9pt; } QListWidget::item { padding: 2px 4px; }")
        def _refresh():
            list_widget.clear()
            for sub in params.get(branch_key, []):
                ad = self.ACTIONS.get(sub.get("action", ""), {})
                icon = ad.get("icon", "")
                name = ad.get("name", sub.get("action", "?"))
                summary = self._format_step_params(sub)
                text = f"{icon} {name}" + (f"  —  {summary}" if summary else "")
                list_widget.addItem(text)
        _refresh()
        layout.addWidget(list_widget)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        action_combo = QComboBox()
        for cat_ids in self.ACTION_CATEGORIES.values():
            for aid in cat_ids:
                if aid == "if_else":
                    continue
                ad = self.ACTIONS.get(aid, {})
                action_combo.addItem(f"{ad.get('icon','')} {ad.get('name', aid)}", aid)
        btn_row.addWidget(action_combo, 1)
        def _add():
            aid = action_combo.currentData()
            if not aid:
                return
            ad = self.ACTIONS[aid]
            sub_step = {"action": aid, "params": {}}
            for pname, pinfo in ad["params"].items():
                dv = pinfo.get("default")
                if dv is None and pinfo.get("type") == "choice":
                    opts = pinfo.get("options", [])
                    dv = opts[0] if opts else None
                sub_step["params"][pname] = dv
            dlg = SubStepDialog(aid, sub_step["params"], parent=self)
            if dlg.exec() == QDialog.Accepted:
                sub_step["params"] = dlg.get_params()
                params.setdefault(branch_key, []).append(sub_step)
                _refresh()
                self._update_if_else_param(step_index, branch_key, params[branch_key])
        def _edit():
            idx = list_widget.currentRow()
            branch = params.get(branch_key, [])
            if idx < 0 or idx >= len(branch):
                return
            sub_step = branch[idx]
            dlg = SubStepDialog(sub_step["action"], sub_step["params"], parent=self)
            if dlg.exec() == QDialog.Accepted:
                sub_step["params"] = dlg.get_params()
                _refresh()
                self._update_if_else_param(step_index, branch_key, params[branch_key])
        def _remove():
            idx = list_widget.currentRow()
            branch = params.get(branch_key, [])
            if 0 <= idx < len(branch):
                del branch[idx]
                _refresh()
                self._update_if_else_param(step_index, branch_key, branch)
        def _move_up():
            idx = list_widget.currentRow()
            branch = params.get(branch_key, [])
            if idx > 0:
                branch[idx - 1], branch[idx] = branch[idx], branch[idx - 1]
                _refresh()
                list_widget.setCurrentRow(idx - 1)
                self._update_if_else_param(step_index, branch_key, branch)
        def _move_down():
            idx = list_widget.currentRow()
            branch = params.get(branch_key, [])
            if 0 <= idx < len(branch) - 1:
                branch[idx], branch[idx + 1] = branch[idx + 1], branch[idx]
                _refresh()
                list_widget.setCurrentRow(idx + 1)
                self._update_if_else_param(step_index, branch_key, branch)
        add_btn = QPushButton("Add")
        add_btn.setFixedWidth(40)
        add_btn.clicked.connect(_add)
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedWidth(40)
        edit_btn.clicked.connect(_edit)
        rm_btn = QPushButton("✕")
        rm_btn.setFixedWidth(28)
        rm_btn.clicked.connect(_remove)
        up_btn = QPushButton("▲")
        up_btn.setFixedWidth(28)
        up_btn.clicked.connect(_move_up)
        dn_btn = QPushButton("▼")
        dn_btn.setFixedWidth(28)
        dn_btn.clicked.connect(_move_down)
        for b in (add_btn, edit_btn, rm_btn, up_btn, dn_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)
        return container

    def _update_if_else_param(self, step_index, param_name, value):
        if step_index < len(self.test_sequence):
            self.test_sequence[step_index]["params"][param_name] = value
            self._update_sequence_list()
            self.sequence_list.blockSignals(True)
            self.sequence_list.setCurrentRow(step_index)
            self.sequence_list.blockSignals(False)

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        if key == Qt.Key_Delete:
            self._remove_selected_step()
        elif key == Qt.Key_D and mods == Qt.ControlModifier:
            self._duplicate_step()
        elif key == Qt.Key_Up and mods == Qt.ControlModifier:
            self._move_step_up()
        elif key == Qt.Key_Down and mods == Qt.ControlModifier:
            self._move_step_down()
        else:
            super().keyPressEvent(event)

    def get_test_sequence(self):
        return self.test_sequence


class SubStepDialog(QDialog):
    def __init__(self, action_id: str, step_params: dict, parent=None):
        super().__init__(parent)
        self.action_id = action_id
        self.step_params = dict(step_params)
        self._widgets = {}
        self._check_state_form = None
        self._setup_ui()

    def _setup_ui(self):
        action_data = TestBuilderDialog.ACTIONS.get(self.action_id, {})
        icon = action_data.get("icon", "")
        name = action_data.get("name", self.action_id)
        self.setWindowTitle(f"Edit sub-step: {icon} {name}")
        self.setMinimumWidth(420)
        self.setWindowModality(Qt.ApplicationModal)
        self._main_layout = QVBoxLayout(self)
        if self.action_id == "check_state":
            self._check_state_form = QFormLayout()
            self._check_state_form.setSpacing(6)
            self._main_layout.addLayout(self._check_state_form)
            self._rebuild_check_state_rows()
        else:
            form = QFormLayout()
            form.setSpacing(6)
            self._main_layout.addLayout(form)
            for param_name, param_info in action_data.get("params", {}).items():
                ptype = param_info.get("type", "text")
                if ptype not in ("int", "float", "choice", "bool", "text"):
                    continue
                current = self.step_params.get(param_name, param_info.get("default"))
                widget = self._make_widget(param_name, param_info, current)
                label_text = TestBuilderDialog.PARAM_LABELS.get(param_name, param_name.replace("_", " ").title())
                form.addRow(f"{label_text}:", widget)
                if param_name in TestBuilderDialog.PARAM_TOOLTIPS:
                    widget.setToolTip(TestBuilderDialog.PARAM_TOOLTIPS[param_name])
                self._widgets[param_name] = widget
        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        self._main_layout.addLayout(btn_row)

    def _rebuild_check_state_rows(self):
        form = self._check_state_form
        self._widgets.clear()
        while form.count():
            it = form.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        section_names = TestBuilderDialog._get_section_names()
        section_combo = QComboBox()
        section_combo.addItems(section_names)
        cur_section = self.step_params.get("section", "Faults")
        if cur_section in section_names:
            section_combo.setCurrentText(cur_section)
        else:
            section_combo.setCurrentIndex(0)
            self.step_params["section"] = section_combo.currentText()
        form.addRow("Section:", section_combo)
        self._widgets["section"] = section_combo
        section_name = section_combo.currentText()
        win_options = TestBuilderDialog._get_windows_for_section(section_name)
        win_combo = QComboBox()
        win_combo.addItems(win_options)
        cur_win = self.step_params.get("window", win_options[0] if win_options else "")
        if cur_win in win_options:
            win_combo.setCurrentText(cur_win)
        else:
            win_combo.setCurrentIndex(0)
            self.step_params["window"] = win_combo.currentText()
        show_win = len(win_options) > 1
        win_label = QLabel("Window:")
        win_label.setVisible(show_win)
        win_combo.setVisible(show_win)
        form.addRow(win_label, win_combo)
        self._widgets["window"] = win_combo
        fields = self._get_fields_for_window(win_combo.currentText())
        field_combo = QComboBox()
        field_combo.addItems(fields)
        cur_field = self.step_params.get("field", fields[0] if fields else "")
        if cur_field in fields:
            field_combo.setCurrentText(cur_field)
        else:
            field_combo.setCurrentIndex(0)
            self.step_params["field"] = field_combo.currentText()
        form.addRow("Field:", field_combo)
        self._widgets["field"] = field_combo
        field_key = self._get_field_key_from_display(win_combo.currentText(), field_combo.currentText())
        state_options = self._get_state_options_for_field(field_key) if field_key else None
        if state_options:
            val_widget = QComboBox()
            val_widget.addItems(state_options)
            cur_val = str(self.step_params.get("expected_value", ""))
            if cur_val in state_options:
                val_widget.setCurrentText(cur_val)
            else:
                val_widget.setCurrentIndex(0)
                self.step_params["expected_value"] = val_widget.currentText()
        else:
            val_widget = QLineEdit()
            val_widget.setText(str(self.step_params.get("expected_value", "")))
            val_widget.setPlaceholderText("Expected value…")
        form.addRow("Expected Value:", val_widget)
        self._widgets["expected_value"] = val_widget
        wait_check = QCheckBox()
        wait_check.setChecked(bool(self.step_params.get("wait_until", True)))
        form.addRow("Wait Until Match:", wait_check)
        self._widgets["wait_until"] = wait_check
        timeout_spin = QDoubleSpinBox()
        timeout_spin.setMinimum(1.0)
        timeout_spin.setMaximum(99999.0)
        timeout_spin.setSingleStep(0.5)
        timeout_spin.setValue(float(self.step_params.get("timeout_s", 5.0)))
        form.addRow("Timeout (s):", timeout_spin)
        self._widgets["timeout_s"] = timeout_spin
        def _on_section(s):
            self.step_params["section"] = s
            wins = TestBuilderDialog._get_windows_for_section(s)
            self.step_params["window"] = wins[0] if wins else "Faults"
            self.step_params["field"] = ""
            self.step_params["expected_value"] = ""
            self._rebuild_check_state_rows()
        def _on_window(w):
            self.step_params["window"] = w
            flds = TestBuilderDialog._get_fields_for_window(w)
            self.step_params["field"] = flds[0] if flds else ""
            self.step_params["expected_value"] = ""
            self._rebuild_check_state_rows()
        def _on_field(f):
            self.step_params["field"] = f
            self.step_params["expected_value"] = ""
            self._rebuild_check_state_rows()
        section_combo.currentTextChanged.connect(_on_section)
        win_combo.currentTextChanged.connect(_on_window)
        field_combo.currentTextChanged.connect(_on_field)

    def _make_widget(self, param_name, param_info, current_value):
        ptype = param_info.get("type")
        if ptype == "int":
            w = QSpinBox()
            w.setMinimum(param_info.get("min", 0))
            w.setMaximum(param_info.get("max", 999999))
            w.setValue(int(current_value) if current_value is not None else param_info.get("default", 0))
            return w
        elif ptype == "float":
            w = QDoubleSpinBox()
            w.setMinimum(param_info.get("min", 0.0))
            w.setMaximum(param_info.get("max", 99999.0))
            w.setSingleStep(param_info.get("step", 0.1))
            w.setValue(float(current_value) if current_value is not None else param_info.get("default", 0.0))
            return w
        elif ptype == "choice":
            w = QComboBox()
            options = param_info.get("options", [])
            if callable(options):
                options = options()
            w.addItems([str(o) for o in options])
            cur_str = str(current_value) if current_value is not None else ""
            if cur_str in [str(o) for o in options]:
                w.setCurrentText(cur_str)
            elif options:
                w.setCurrentIndex(0)
            return w
        elif ptype == "bool":
            w = QCheckBox()
            w.setChecked(bool(current_value) if current_value is not None else param_info.get("default", False))
            return w
        elif ptype == "text":
            w = QLineEdit()
            w.setText(str(current_value) if current_value is not None else "")
            return w
        return QLineEdit()

    def _accept(self):
        for param_name, w in self._widgets.items():
            if w is None:
                continue
            if isinstance(w, QSpinBox):
                self.step_params[param_name] = w.value()
            elif isinstance(w, QDoubleSpinBox):
                self.step_params[param_name] = w.value()
            elif isinstance(w, QComboBox):
                self.step_params[param_name] = w.currentText()
            elif isinstance(w, QCheckBox):
                self.step_params[param_name] = w.isChecked()
            elif isinstance(w, QLineEdit):
                self.step_params[param_name] = w.text()
        self.accept()

    def get_params(self) -> dict:
        return self.step_params


class _GroupEditorDialog(TestBuilderDialog):
    def __init__(self, groups_dir: str, parent=None, bbt_widget=None):
        self._groups_dir = groups_dir
        super().__init__(parent=parent, bbt_widget=bbt_widget)
        self.setWindowTitle("Group Editor")
        self.groups_btn.hide()
        self.save_btn.setText("💾 Save Group")
        self.load_btn.setText("📁 Load Group")

    def _save_test(self):
        if not self.test_sequence:
            QMessageBox.warning(self, "Empty Group", "No steps to save!")
            return
        os.makedirs(self._groups_dir, exist_ok=True)
        filename, _ = QFileDialog.getSaveFileName(self, "Save Group", self._groups_dir, "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.test_sequence, f, indent=2)
            except OSError as e:
                QMessageBox.critical(self, "Save Error", str(e))

    def _load_test(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Group", self._groups_dir, "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.test_sequence = json.load(f)
                self._update_sequence_list()
            except (OSError, ValueError) as e:
                QMessageBox.critical(self, "Load Error", str(e))

    def _run_test(self):
        QMessageBox.information(self, "Run Group", "Groups cannot be run directly. Add them to a test with a 'Call Group' step.")

    def _open_group_editor(self):
        QMessageBox.information(self, "Nested Groups", "Groups cannot call other groups.")
