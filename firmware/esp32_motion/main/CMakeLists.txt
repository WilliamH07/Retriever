idf_component_register(
    SRCS "main.c" "motors.c" "motor_control.c"
    INCLUDE_DIRS "."
    REQUIRES
        retriever_link
        retriever_protocol
        driver
        esp_system
        esp_timer
)
