typedef signed char int8_t;
typedef unsigned char uint8_t;
typedef short int16_t;
typedef unsigned short uint16_t;
typedef int int32_t;
typedef unsigned uint32_t;
typedef long long int64_t;
typedef unsigned long long uint64_t;
typedef struct
{
        uint16_t value;
        uint16_t RESERVED;
} protocol_crc_t;
typedef struct
{
        uint8_t id;
        uint8_t id_req;
        uint16_t RESERVED;
} protocol_header_t;
enum frame_id_enum
{
        FRAME_ID_UI_DATA_REQUEST,
        FRAME_ID_UI_COMMAND,
        FRAME_ID_UI_STARTUP_INFO_RESPONSE,
        FRAME_ID_UI_DEVICE_STATUS_RESPONSE,
        FRAME_ID_UI_VARIANT_SETUP_RESPONSE,
        FRAME_ID_UI_PROGRAM_POSITIONS_MAP_RESPONSE,
        FRAME_ID_UI_PROGRAM_DATA_RESPONSE,
        FRAME_ID_UI_SERVICE_DATA_RESPONSE,
        FRAME_ID_UI_DEVICE_LIFETIME_STATS_RESPONSE,
        FRAME_ID_UI_PRODUCTION_TEST_STATUS_RESPONSE,
        FRAME_ID_UI_VERSION_RESPONSE,
        FRAME_ID_UI_FAULT_INFO,
        FRAME_ID_UI_COMMAND_ACKNOWLEDGE,
        FRAME_ID_UI_STATUS_GET,
        FRAME_ID_UI_STATUS,
        FRAME_ID_UI_COMMAND_ORIG,
        FRAME_ID_UI_COMMAND_ACK,
};
typedef enum _program_mode_e
{
        PROGRAM_MODE_NORMAL,
        PROGRAM_MODE_SPEED,
        PROGRAM_MODE_GREEN,
        PROGRAM_MODE_NIGHT,
        PROGRAM_MODE_INTENSIVE,
        PROGRAM_MODE_UV,
} program_mode_e;
typedef enum _test_mode_flag_e
{
        TEST_MODE_NONE,
        TEST_MODE_FUNCTIONAL,
        TEST_MODE_LEAKAGE,
        TEST_MODE_LONGTERM,
} test_mode_flag_e;
typedef enum _program_control_action_e
{
        PROGRAM_CONTROL_ACTION_START,
        PROGRAM_CONTROL_ACTION_PAUSE,
        PROGRAM_CONTROL_ACTION_RESUME,
        PROGRAM_CONTROL_ACTION_STOP,
} program_control_action_e;
typedef union _program_options_u
{
        struct options
        {
                uint8_t auto_door_open : 1;
                program_mode_e program_mode : 3;
                uint8_t action : 2;
                uint8_t dummy : 2;
        } as_bits;
        uint8_t as_byte;
} program_options_u;
typedef enum _data_request_type_e
{
        DATA_REQUEST_STARTUP_INFO,
        DATA_REQUEST_DEVICE_STATUS,
        DATA_REQUEST_VARIANT_SETUP,
        DATA_REQUEST_PROGRAM_POSITIONS_MAP,
        DATA_REQUEST_PROGRAM_DATA,
        DATA_REQUEST_SERVICE_DATA,
        DATA_REQUEST_DEVICE_LIFETIME_STATS,
        DATA_REQUEST_PRODUCTION_TEST_STATUS,
        DATA_REQUEST_VERSION,
        DATA_REQUEST_FAULT_INFO,
} data_request_type_e;
typedef enum _service_data_request_e
{
        SERVICE_DATA_DRAIN_PUMP_RPM,
        SERVICE_DATA_FLOW_METER_VALUE,
        SERVICE_DATA_PRESSURE_SENSOR_VALUE,
        SERVICE_DATA_CIRCULATION_PUMP_RPM,
        SERVICE_DATA_TEMPERATURE,
        SERVICE_DATA_DIVERTER_POSITION,
} service_data_request_e;
typedef enum _device_lifetime_stats_request_e
{
        DEVICE_LIFETIME_STAT_TOTAL_RUNTIME,
        DEVICE_LIFETIME_STAT_TOTAL_WATER,
        DEVICE_LIFETIME_STAT_NUMBER_OF_CYCLES,
} device_lifetime_stats_request_e;
typedef enum _version_request_e
{
        VERSION_REQUEST_GCU_SW,
        VERSION_REQUEST_GCU_BLDC,
        VERSION_REQUEST_WIFI,
} version_request_e;
typedef struct _protocol_frame_ui_data_request_data_t
{
        data_request_type_e request_type;
        uint8_t request_param;
        program_options_u options;
} protocol_frame_ui_data_request_data_t;
typedef struct _protocol_frame_ui_data_request_t
{
        protocol_header_t header;
        protocol_frame_ui_data_request_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_data_request_t;
typedef enum _ui_gcu_command_e
{
        UI_GCU_COMMAND_PROGRAM_CONTROL,
        UI_GCU_COMMAND_DEVICE_SETUP,
        UI_GCU_COMMAND_VARIANT_SET,
        UI_GCU_COMMAND_RUN_PRESSURE_CALIBRATION,
        UI_GCU_COMMAND_TEST_DRAIN_PUMP,
        UI_GCU_COMMAND_MEASURE_FLOW,
        UI_GCU_COMMAND_MEASURE_PRESSURE,
        UI_GCU_COMMAND_TEST_CIRCULATION_PUMP,
        UI_GCU_COMMAND_TEST_HEATER,
        UI_GCU_COMMAND_TEST_SALT,
        UI_GCU_COMMAND_TEST_COMBI_DISPENSER,
        UI_GCU_COMMAND_TEST_AUTO_DOSE,
        UI_GCU_COMMAND_TEST_FAN_AND_WAX,
        UI_GCU_COMMAND_TEST_DOOR_OPEN,
        UI_GCU_COMMAND_TEST_DIVERTER,
        UI_GCU_COMMAND_TEST_UV_LIGHT,
        UI_GCU_COMMAND_SET_INLET_TYPE,
        UI_GCU_COMMAND_SET_FAN_SEQUENCE,
        UI_GCU_COMMAND_SET_HEAT_PUMP,
        UI_GCU_COMMAND_SET_TEST_MODE_FLAG,
        UI_GCU_COMMAND_TOTAL_RESET,
        UI_GCU_COMMAND_INVALIDATE_VARIANT,
        UI_GCU_COMMAND_SET_INTERIOR_LIGHT,
        UI_GCU_COMMAND_SET_LOW_POWER,
        UI_GCU_COMMAND_REQUEST_DEVICE_REBOOT,
} ui_gcu_command_e;
typedef enum _inlet_type_e
{
        INLET_TYPE_P,
        INLET_TYPE_P50,
        INLET_TYPE_T,
} inlet_type_e;
typedef enum _fan_sequence_e
{
        FAN_SEQUENCE_ALWAYS_OFF,
        FAN_SEQUENCE_INTERMITTENT,
        FAN_SEQUENCE_ALWAYS_ON,
} fan_sequence_e;
typedef enum _auto_dose_e
{
        AUTO_DOSE_OFF,
        AUTO_DOSE_15_ML,
        AUTO_DOSE_20_ML,
        AUTO_DOSE_25_ML,
        AUTO_DOSE_30_ML,
        AUTO_DOSE_35_ML,
        AUTO_DOSE_40_ML,
} auto_dose_e;
typedef struct _program_start_parameters_t
{
        program_options_u options;
        uint8_t room_temperature;
} program_start_parameters_t;
typedef struct _device_setup_parameters_t
{
        uint8_t super_rinse : 1;
        auto_dose_e auto_dose : 3;
        uint8_t rinse_aid : 3;
        uint8_t dummy : 1;
        uint8_t odour_control : 1;
        uint8_t interior_light_at_power_off : 1;
        uint8_t energy_save : 1;
        uint8_t water_save : 1;
        uint8_t water_hardness : 4;
} device_setup_parameters_t;
typedef union _command_extended_params_u
{
        program_start_parameters_t program_start_parameters;
        device_setup_parameters_t device_setup_parameters;
        uint16_t variant_id;
        uint16_t raw_memory;
} command_extended_params_u;
typedef union _command_param_u
{
        uint8_t program_id;
        inlet_type_e inlet_type;
        fan_sequence_e fan_sequence;
        uint8_t heat_pump_state;
        test_mode_flag_e test_mode_flag;
        uint8_t interior_light_state;
        uint8_t low_power_state;
        uint8_t raw_memory;
} command_param_u;
typedef struct _protocol_frame_ui_command_data_t
{
        ui_gcu_command_e command;
        command_param_u param;
        command_extended_params_u extended_params;
} protocol_frame_ui_command_data_t;
typedef struct _protocol_frame_ui_command_t
{
        protocol_header_t header;
        protocol_frame_ui_command_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_command_t;
typedef struct _protocol_frame_ui_startup_info_data_t
{
        test_mode_flag_e test_mode_flag;
        uint8_t power_fail_flag;
} protocol_frame_ui_startup_info_data_t;
typedef struct _protocol_frame_ui_startup_info_t
{
        protocol_header_t header;
        protocol_frame_ui_startup_info_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_startup_info_t;
typedef enum _program_status_e
{
        PROGRAM_STATUS_IDLE,
        PROGRAM_STATUS_PAUSED,
        PROGRAM_STATUS_RUNNING,
} program_status_e;
typedef enum _program_seq_id_e
{
        SEQ_NONE,
        SEQ_PRE,
        SEQ_PW1,
        SEQ_PW2,
        SEQ_PW3,
        SEQ_PW4,
        SEQ_PW5,
        SEQ_CF1,
        SEQ_MW1,
        SEQ_MW2,
        SEQ_ER1,
        SEQ_ER2,
        SEQ_RI1,
        SEQ_RI2,
        SEQ_RI5,
        SEQ_RI6,
        SEQ_RI7,
        SEQ_DRY1,
        SEQ_DRY2,
        SEQ_ION,
} program_seq_id_e;
typedef struct _device_status_flags_t
{
        program_status_e program_status : 2;
        uint8_t door_open : 1;
        uint8_t fault_occurred : 1;
        uint8_t self_clean_needed : 1;
        uint8_t salt_fill_needed : 1;
        uint8_t rinse_aid_fill_needed : 1;
        uint8_t auto_dose_fill_needed : 1;
} device_status_flags_t;
typedef struct _protocol_frame_ui_device_status_data_t
{
        device_status_flags_t flags;
        program_seq_id_e active_program_sequence;
        uint16_t program_remaining_time;
} protocol_frame_ui_device_status_data_t;
typedef struct _protocol_frame_ui_device_status_t
{
        protocol_header_t header;
        protocol_frame_ui_device_status_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_device_status_t;
typedef enum _mutually_exclusive_0_e
{
        ME_0_ALL_OFF,
        ME_0_HEAT_EXCHANGER,
        ME_0_GREY_TANK,
        ME_0_IONIZER,
        ME_0_GREY_TANK_IONIZER,
        ME_0_PROF_INLET,
} mutually_exclusive_0_e;
typedef enum _mutually_exclusive_1_e
{
        ME_1_ALL_OFF,
        ME_1_HEAT_PUMP,
        ME_1_SEMI_PROF,
        ME_1_PROF,
} mutually_exclusive_1_e;
typedef enum _mutually_exclusive_2_e
{
        ME_2_ALL_OFF,
        ME_2_UV_LIGHT,
        ME_2_PROF_SOFT,
} mutually_exclusive_2_e;
typedef enum _mutually_exclusive_3_e
{
        ME_3_ALL_OFF,
        ME_3_AUTO_DOSE_INTERNAL,
        ME_3_AUTO_DOSE_EXT_DETERGENT,
} mutually_exclusive_3_e;
typedef enum _type_of_english_e
{
        ENGLISH_UK,
        ENGLISH_AU,
        ENGLISH_US,
} type_of_english_e;
typedef enum _type_of_swedish_e
{
        SWEDISH_ASKO,
        SWEDISH_CYLINDA,
} type_of_swedish_e;
typedef enum _temperature_unit_e
{
        TEMPERATURE_UNIT_C,
        TEMPERATURE_UNIT_F,
} temperature_unit_e;
typedef enum _heater_power_e
{
        HEATER_POWER_10_A,
        HEATER_POWER_16_A,
} heater_power_e;
typedef struct _protocol_frame_ui_variant_setup_data_t
{
        mutually_exclusive_0_e mutually_exclusive_0 : 3;
        uint8_t td_fan : 1;
        uint8_t variant_valid : 1;
        uint8_t dummy : 3;
        uint8_t pressure_sensor : 1;
        uint8_t connectivity : 1;
        uint8_t softener : 1;
        mutually_exclusive_2_e mutually_exclusive_2 : 2;
        mutually_exclusive_1_e mutually_exclusive_1 : 2;
        uint8_t auto_door_open : 1;
        uint8_t program_memory_menu : 1;
        uint8_t program_memory : 1;
        uint8_t asko_flag : 1;
        uint8_t us_flag : 1;
        uint8_t interior_light : 1;
        uint8_t auto_dose_ext_rinse_aid : 1;
        mutually_exclusive_3_e mutually_exclusive_3 : 2;
        uint8_t feedback_volume_default : 2;
        uint8_t display_contrast_default : 2;
        uint8_t two_button_self_clean : 1;
        type_of_swedish_e type_of_swedish : 1;
        type_of_english_e type_of_english : 2;
        auto_dose_e auto_dose_default : 3;
        uint8_t rinse_aid_default : 3;
        uint8_t notification_volume_default : 2;
        heater_power_e heater_power_default : 1;
        temperature_unit_e temperature_unit_default : 1;
        uint8_t interior_light_default : 1;
        uint8_t child_lock_default : 1;
        uint8_t water_hardness_default : 4;
        uint16_t variant_id;
} protocol_frame_ui_variant_setup_data_t;
typedef struct _protocol_frame_ui_variant_setup_t
{
        protocol_header_t header;
        protocol_frame_ui_variant_setup_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_variant_setup_t;
typedef struct _protocol_frame_ui_program_positions_map_data_t
{
        uint8_t map_part;
        uint8_t program_ids[(7)];
} protocol_frame_ui_program_positions_map_data_t;
typedef struct _protocol_frame_ui_program_positions_map_t
{
        protocol_header_t header;
        protocol_frame_ui_program_positions_map_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_program_positions_map_t;
typedef struct _program_data_flags_t
{
        uint8_t night_mode_available : 1;
        uint8_t intensive_mode_available : 1;
        uint8_t uv_mode_available : 1;
        uint8_t available : 1;
        uint8_t dummy : 4;
        uint8_t auto_door_open_default : 1;
        uint8_t auto_door_open_possible : 1;
        uint8_t delayed_start_possible : 1;
        uint8_t is_time_program : 1;
        uint8_t disable_possible : 1;
        uint8_t normal_mode_available : 1;
        uint8_t speed_mode_available : 1;
        uint8_t green_mode_available : 1;
} program_data_flags_t;
typedef struct _protocol_frame_ui_program_data_data_t
{
        uint8_t program_id;
        uint8_t dummy;
        program_data_flags_t flags;
        uint16_t duration;
} protocol_frame_ui_program_data_data_t;
typedef struct _protocol_frame_ui_program_data_t
{
        protocol_header_t header;
        protocol_frame_ui_program_data_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_program_data_t;
typedef struct _protocol_frame_ui_service_data_data_t
{
        uint32_t response_id : 7;
        uint32_t action_in_progress : 1;
        uint32_t value : 24;
} protocol_frame_ui_service_data_data_t;
typedef struct _protocol_frame_ui_service_data_t
{
        protocol_header_t header;
        protocol_frame_ui_service_data_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_service_data_t;
typedef struct _protocol_frame_ui_device_lifetime_stats_data_t
{
        uint32_t stat_id : 8;
        uint32_t value : 24;
} protocol_frame_ui_device_lifetime_stats_data_t;
typedef struct _protocol_frame_ui_device_lifetime_stats_t
{
        protocol_header_t header;
        protocol_frame_ui_device_lifetime_stats_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_device_lifetime_stats_t;
typedef struct _protocol_frame_ui_production_test_status_data_t
{
        uint8_t current_step;
        uint8_t fault;
        uint16_t dummy;
} protocol_frame_ui_production_test_status_data_t;
typedef struct _protocol_frame_ui_production_test_status_t
{
        protocol_header_t header;
        protocol_frame_ui_production_test_status_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_production_test_status_t;
typedef struct _protocol_frame_ui_version_data_t
{
        uint32_t version_id : 8;
        uint32_t data : 24;
} protocol_frame_ui_version_data_t;
typedef struct _protocol_frame_ui_version_t
{
        protocol_header_t header;
        protocol_frame_ui_version_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_version_t;
typedef enum _fault_severity_e
{
        FAULT_SEVERITY_SILENT,
        FAULT_SEVERITY_NORMAL,
        FAULT_SEVERITY_UNKNOWN,
} fault_severity_e;
typedef struct _protocol_frame_ui_fault_info_data_t
{
        uint8_t fault_id;
        fault_severity_e severity;
        uint16_t dummy;
} protocol_frame_ui_fault_info_data_t;
typedef struct _protocol_frame_ui_fault_info_t
{
        protocol_header_t header;
        protocol_frame_ui_fault_info_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_fault_info_t;
typedef enum _command_status_e
{
        COMMAND_STATUS_OK,
        COMMAND_STATUS_ERROR,
        COMMAND_STATUS_UNKNOWN,
} command_status_e;
typedef struct _protocol_frame_ui_command_acknowledge_data_t
{
        ui_gcu_command_e command;
        command_status_e status;
        uint16_t dummy;
} protocol_frame_ui_command_acknowledge_data_t;
typedef struct _protocol_frame_ui_command_acknowledge_t
{
        protocol_header_t header;
        protocol_frame_ui_command_acknowledge_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_command_acknowledge_t;
typedef struct _protocol_frame_ui_status_data_t
{
        uint32_t remaining_program_time;
        program_status_e program_status;
        uint8_t fault_id;
} protocol_frame_ui_status_data_t;
typedef struct _protocol_frame_ui_status_t
{
        protocol_header_t header;
        protocol_frame_ui_status_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_status_t;
typedef struct _protocol_frame_ui_status_get_t
{
        protocol_header_t header;
        protocol_crc_t crc;
} protocol_frame_ui_status_get_t;
typedef enum _dw60_3_ui_cmd_e
{
        dw60_3_ui_cmd_program_start_eco,
        dw60_3_ui_cmd_program_start_intensive,
        dw60_3_ui_cmd_program_stop,
} dw60_3_ui_cmd_e;
typedef struct _protocol_frame_ui_cmd_data_t
{
        dw60_3_ui_cmd_e cmd;
} protocol_frame_ui_cmd_data_t;
typedef struct _protocol_frame_ui_cmd_
{
        protocol_header_t header;
        protocol_frame_ui_cmd_data_t data;
        protocol_crc_t crc;
} protocol_frame_ui_cmd_t;
typedef struct _protocol_frame_ui_command_ack_t
{
        protocol_header_t header;
        protocol_crc_t crc;
} protocol_frame_ui_command_ack_t;
typedef enum _day
{
        Monday,
        Tuesday,
        Wednesday,
        Thursday,
        Friday,
        Saturday,
        Sunday
} week;
enum mood
{
        Happy,
        Sad,
        Neutral
};
typedef enum mood mood_t;
struct wish;
struct happy
{
        struct wish *parent;
        uint16_t new;
        uint32_t year;
        week day;
        mood_t mood;
        struct _assignee
        {
                int manager;
                char name[20];
        } assignee;
        enum data
        {
                sparse = 12,
        } data;
};
typedef struct happy happy_t;
struct wish
{
        struct happy *data;
};
struct simple1
{
        int id;
};
typedef struct simple_struct
{
        week day;
        struct simple1 simple;
} simple_struct;
typedef struct uart
{
        int fd;
        char rx_buff[1024];
        char tx_buff[1024];
} uart_t;
int my_f(int a, char *b, struct happy c) {}
const char msg[6][30] = {
    "Hello", "C++", "World", "from", "VS Code", "and the C++ extension!"};
uart_t uart;
int main(int nargs, char **argv)
{
        program_options_u bla;
        struct happy my_happy;
        my_f(1, "asdf", my_happy);
        for (uint32_t i = 0; i < (sizeof(msg) / sizeof(msg[0])); ++i)
        {
        }
}
