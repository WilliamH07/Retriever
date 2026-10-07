/* Minimal host model of the GPIO/LEDC API used by motors.c. */
#ifndef RT_FAKE_IDF_H
#define RT_FAKE_IDF_H
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdarg.h>
typedef int esp_err_t;
typedef int gpio_num_t;
typedef int ledc_channel_t;
typedef int ledc_timer_bit_t;
typedef uint32_t TickType_t;
typedef int portMUX_TYPE;
#define ESP_OK 0
#define ESP_FAIL -1
#define ESP_ERR_INVALID_STATE -2
#define ESP_ERR_INVALID_ARG -3
#define ESP_ERR_NO_MEM -4
#define portMUX_INITIALIZER_UNLOCKED 0
#define portENTER_CRITICAL(p) ((void)(p))
#define portEXIT_CRITICAL(p) ((void)(p))
#define pdMS_TO_TICKS(ms) (ms)
#define pdPASS 1
#define GPIO_IS_VALID_OUTPUT_GPIO(p) ((p) >= 0 && (p) <= 33)
#define GPIO_MODE_INPUT_OUTPUT 1
#define GPIO_MODE_INPUT_OUTPUT_OD 2
#define GPIO_PULLUP_DISABLE 0
#define GPIO_PULLDOWN_DISABLE 0
#define GPIO_INTR_DISABLE 0
#define LEDC_LOW_SPEED_MODE 0
#define LEDC_TIMER_0 0
#define LEDC_AUTO_CLK 0
#define LEDC_INTR_DISABLE 0
typedef struct { uint64_t pin_bit_mask; int mode, pull_up_en, pull_down_en, intr_type; } gpio_config_t;
typedef struct { int speed_mode, duty_resolution, timer_num; uint32_t freq_hz; int clk_cfg; } ledc_timer_config_t;
typedef struct { int gpio_num, speed_mode, channel, intr_type, timer_sel; uint32_t duty, hpoint; } ledc_channel_config_t;
esp_err_t gpio_set_level(gpio_num_t pin, int level);
int gpio_get_level(gpio_num_t pin);
esp_err_t gpio_config(const gpio_config_t *cfg);
esp_err_t ledc_set_duty(int mode, ledc_channel_t channel, uint32_t duty);
esp_err_t ledc_update_duty(int mode, ledc_channel_t channel);
uint32_t ledc_get_duty(int mode, ledc_channel_t channel);
esp_err_t ledc_timer_config(const ledc_timer_config_t *cfg);
esp_err_t ledc_channel_config(const ledc_channel_config_t *cfg);
uint32_t ledc_get_freq(int mode, int timer);
int64_t esp_timer_get_time(void);
esp_err_t esp_task_wdt_add(void *task);
esp_err_t esp_task_wdt_reset(void);
TickType_t xTaskGetTickCount(void);
void vTaskDelay(TickType_t ticks);
void vTaskDelayUntil(TickType_t *wake, TickType_t ticks);
void vTaskDelete(void *task);
int xTaskCreate(void (*task)(void *), const char *name, int stack, void *arg, int priority, void *handle);
static inline void fake_log(const char *tag, const char *fmt, ...) { (void)tag; (void)fmt; }
static inline const char *esp_err_to_name(esp_err_t err) { (void)err; return "fake error"; }
#define ESP_LOGI(...) fake_log(__VA_ARGS__)
#define ESP_LOGE(...) fake_log(__VA_ARGS__)
#endif
