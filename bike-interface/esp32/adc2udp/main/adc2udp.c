/* adc2udp VCE
 *
 * read values of a hall sensor with the help of the adc and send them via udp

   This example code is in the Public Domain (or CC0 licensed, at your option.)

   Unless required by applicable law or agreed to in writing, this
   software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied.
*/
// #include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/param.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
// #include "nvs_flash.h"
#include "driver/gpio.h"
// #include "driver/adc.h"
// #include "esp_adc_cal.h"

#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include <lwip/netdb.h>

//-------- WIFI declarations --------------------------------------
/* The examples use simple WiFi configuration that you can set via
   'make menuconfig'.
   If you'd rather not, just change the below entries to strings with
   the config you want - ie #define EXAMPLE_WIFI_SSID "mywifissid"
*/
#define EXAMPLE_WIFI_SSID CONFIG_WIFI_SSID
#define EXAMPLE_WIFI_PASS CONFIG_WIFI_PASSWORD

#define BICYCLE_MODEL_HOST CONFIG_BICYCLE_MODEL_HOST
#define PORT CONFIG_BICYCLE_MODEL_PORT

static const char *TAG = "adc2udp";

//-------- ADC declarations ---------------------------------------
// #define DEFAULT_VREF    1100                                    //Use adc2_vref_to_gpio() to obtain a better estimate
// #define NO_OF_SAMPLES   CONFIG_NUMBER_OF_SAMPLES_PER_VALUE      //Multisampling
//
// static esp_adc_cal_characteristics_t *adc_chars;
// static const adc_channel_t channel = ADC_CHANNEL_6;     //GPIO34 if ADC1, GPIO14 if ADC2
// static const adc_atten_t atten = ADC_ATTEN_DB_11;       //Use ADC_ATTEN_DB_11 for a maxium voltage of 3.9V
// static const adc_unit_t unit = ADC_UNIT_1;

//-------- GPIO declarations --------------------------------------
//GPIO setup based on this example:
//https://github.com/espressif/esp-idf/blob/09f7589ef23a6b78339224efd372257a57e1be4b/examples/peripherals/gpio/generic_gpio/main/gpio_example_main.c

//1ULL = 1 'unsigned long long' = 1 as u64
#define GPIO_PIN_IR_SENSOR CONFIG_GPIO_IR_SENSOR
#define GPIO_IR_SENSOR_PIN_BITMASK (1ULL<<CONFIG_GPIO_IR_SENSOR)
#define GPIO_PIN_IR_SENSOR_EN CONFIG_GPIO_IR_SENSOR_EN
#define ESP_INTR_FLAG_DEFAULT 0
#define IR_SENSOR_HAS_EN_PIN CONFIG_IR_SENSOR_HAS_EN_PIN

//-------- Speed sensor variables ---------------------------------
static uint32_t ir_sensor_tick_counter = 0;
static int64_t ir_sensor_last_tick_time_us = 0;
#define SPEED_SENSOR_WINDOW_SIZE CONFIG_SPEED_SENSOR_WINDOW_SIZE
#define SPEED_SENSOR_TIMEOUT_US 500000
// Assuming a maximum of 48 spokes per wheel, a diameter of 0.6 m, and a max speed vmax of
// 45 km/h = 12.5 m/s
// -> distance per rotation dpr = pi*d = 1.88 m
// -> max rotations per second rps = vmax / dpr = 6.65
// -> max spokes per second = rps * 48 = 319.2
// -> min time between spokes = 1 / 319.2 = 3.1 ms
#define SPEED_SENSOR_MIN_TICK_TIME_MS 3
static int64_t speed_sensor_intervals[SPEED_SENSOR_WINDOW_SIZE];
static float speed_sensor_ticks_per_second = 0;
static const float speed_sensor_filter_factor = 0.75;
QueueHandle_t speed_sensor_gpio_queue = NULL;


//----------- freertos task ------------------------------------------
static void udp_transmit_task(void *pvParameters)
{
    // TODO: integrate speed sensor by having ir sensor ticks add values to a queue that we process here in a loop…
    // cp. the queuing in the gpio example: https://github.com/espressif/esp-idf/blob/09f7589ef23a6b78339224efd372257a57e1be4b/examples/peripherals/gpio/generic_gpio/main/gpio_example_main.c

    char sendbuf[128];
    char addr_str[128];
    int addr_family;
    int ip_protocol;
    int delayInMs = 1000 / CONFIG_UDP_PACKET_FREQUENCY;
    int failures = 0;

    ESP_LOGI(TAG, "Running speed sensor task.");

#ifdef CONFIG_IPV4
    struct sockaddr_in destAddr;
    destAddr.sin_addr.s_addr = inet_addr(BICYCLE_MODEL_HOST);
    destAddr.sin_family = AF_INET;
    destAddr.sin_port = htons(PORT);
    addr_family = AF_INET;
    ip_protocol = IPPROTO_IP;
    inet_ntoa_r(destAddr.sin_addr, addr_str, sizeof(addr_str) - 1);
#else // IPV6
    struct sockaddr_in6 destAddr;
    bzero(&destAddr.sin6_addr.un, sizeof(destAddr.sin6_addr.un));
    destAddr.sin6_family = AF_INET6;
    destAddr.sin6_port = htons(PORT);
    addr_family = AF_INET6;
    ip_protocol = IPPROTO_IPV6;
    inet6_ntoa_r(destAddr.sin6_addr, addr_str, sizeof(addr_str) - 1);
#endif

    int sock = socket(addr_family, SOCK_DGRAM, ip_protocol);
    if (sock < 0) {
        ESP_LOGE(TAG, "Unable to create socket: errno %d", errno);
        return;
    }
    int err = connect(sock, (struct sockaddr *)&destAddr, sizeof(destAddr));
    if (err < 0) {
        ESP_LOGE(TAG, "Socket unable to connect: errno %d", errno);
        return;
    }
    ESP_LOGI(TAG, "Socket connected to %s:%d.", addr_str, PORT);

    while(1) {
        //Ignoring ADC values for now; only using the IR sensor ticks for the speed sensor
        // uint32_t adc_reading = 0;
        // failures = 0;
        // //Multisampling
        // for (int i = 0; i < NO_OF_SAMPLES; i++) {
        //     if (unit == ADC_UNIT_1) {
        //         adc_reading += adc1_get_raw((adc1_channel_t)channel);
        //     } else {
        //         int raw;
        //         adc2_get_raw((adc2_channel_t)channel, ADC_WIDTH_BIT_12, &raw);
        //         adc_reading += raw;
        //     }
        // }
        // adc_reading /= NO_OF_SAMPLES;

        //Convert adc_reading to voltage in mV
        // uint32_t voltage = esp_adc_cal_raw_to_voltage(adc_reading, adc_chars);
        // ESP_LOGI(TAG, "Raw: %d\tVoltage: %dmV", adc_reading, voltage);

        //Send adc value
        // int len = sprintf(sendbuf, "%d", adc_reading);
        int len = sprintf(sendbuf, "%0.2f", speed_sensor_ticks_per_second);
        int err = sendto(sock, sendbuf, len, 0,(struct sockaddr *)&destAddr, sizeof(destAddr));  // returns -1 if something fails
        // ESP_LOGI(TAG, "send adc value: %d\t to %s:%d\n.", adc_reading, addr_str, PORT);
        while (err < 0) {
            ESP_LOGE(TAG, "Error occurred during sending: errno %d", errno);
            if (errno == 12) {  // ENOMEM
                failures++;
                err = sendto(sock, sendbuf, len, 0,(struct sockaddr *)&destAddr, sizeof(destAddr));
            }
        }
        // ESP_LOGI(TAG, "Sent speed sensor value: %s with %d failures.", sendbuf, failures);
        vTaskDelay(pdMS_TO_TICKS(delayInMs));
     }

    if (sock != -1) {
        ESP_LOGE(TAG, "Shutting down socket and restarting...");
        shutdown(sock, 0);
        close(sock);
    }
    vTaskDelete(NULL);
}

//--------- WIFI functions -----------------------------------------
static void event_handler(void *arg, esp_event_base_t event_base, int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT) {
        switch (event_id) {
            case WIFI_EVENT_STA_START:
                ESP_ERROR_CHECK(esp_wifi_connect());
                ESP_LOGI(TAG, "SYSTEM_EVENT_STA_START");
                break;
            case WIFI_EVENT_STA_CONNECTED:
                ESP_LOGI(TAG, "SYSTEM_EVENT_STA_CONNECTED");
                break;
            case WIFI_EVENT_STA_DISCONNECTED:
                ESP_LOGI(TAG, "SYSTEM_EVENT_STA_DISCONNECTED");
                esp_wifi_connect();
                break;
            default:
                ESP_LOGI(TAG, "Unknown event_id: %d.", event_id);
                break;
        }
    } else if (event_base == IP_EVENT) {
        switch (event_id) {
            case IP_EVENT_STA_GOT_IP:
                ESP_LOGI(TAG, "SYSTEM_EVENT_STA_GOT_IP");
                xTaskCreate(udp_transmit_task, "udp_transmit_task", 16384, NULL, 5, NULL);
                break;
            default:
                ESP_LOGI(TAG, "Unknown event_id: %d.", event_id);
                break;
        }
    } else {
        ESP_LOGI(TAG, "Unknown event base.");
    }
}

static void initialise_wifi(void)
{
    esp_netif_init();
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK( esp_wifi_init(&cfg) );

    esp_event_handler_instance_t instance_got_ip;
    esp_event_handler_instance_t instance_any_id;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                        IP_EVENT_STA_GOT_IP,
                                                        &event_handler,
                                                        NULL,
                                                        &instance_got_ip));

    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &event_handler,
                                                        NULL,
                                                        &instance_any_id));

    wifi_config_t wifi_config = {
        .sta = {
            .ssid = EXAMPLE_WIFI_SSID,
            .password = EXAMPLE_WIFI_PASS,
            .scan_method = WIFI_AUTH_WPA2_PSK,
            .bssid_set = 0,
            .channel = 0,
            .threshold = {
                .rssi = 0,
                .authmode = WIFI_AUTH_OPEN,
            },
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));
    ESP_LOGI(TAG, "Setting WiFi configuration SSID %s...", wifi_config.sta.ssid);
    ESP_ERROR_CHECK( esp_wifi_set_mode(WIFI_MODE_STA) );
    ESP_ERROR_CHECK( esp_wifi_set_config(ESP_IF_WIFI_STA, &wifi_config) );
    ESP_ERROR_CHECK( esp_wifi_start() );
}

//-------- ADC functions -----------------------------------------------
// static void check_efuse()
// {
//     //Check TP is burned into eFuse
//     if (esp_adc_cal_check_efuse(ESP_ADC_CAL_VAL_EFUSE_TP) == ESP_OK) {
//         printf("eFuse Two Point: Supported\n");
//     } else {
//         printf("eFuse Two Point: NOT supported\n");
//     }
//
//     //Check Vref is burned into eFuse
//     if (esp_adc_cal_check_efuse(ESP_ADC_CAL_VAL_EFUSE_VREF) == ESP_OK) {
//         printf("eFuse Vref: Supported\n");
//     } else {
//         printf("eFuse Vref: NOT supported\n");
//     }
// }

// static void print_char_val_type(esp_adc_cal_value_t val_type)
// {
//     if (val_type == ESP_ADC_CAL_VAL_EFUSE_TP) {
//         printf("Characterized using Two Point Value\n");
//     } else if (val_type == ESP_ADC_CAL_VAL_EFUSE_VREF) {
//         printf("Characterized using eFuse Vref\n");
//     } else {
//         printf("Characterized using Default Vref\n");
//     }
// }

// static void configure_adc(void)
// {
//     //Check if Two Point or Vref are burned into eFuse
//     check_efuse();
//
//     //Configure ADC
//     if (unit == ADC_UNIT_1) {
//         adc1_config_width(ADC_WIDTH_BIT_12);
//         adc1_config_channel_atten((adc1_channel_t)channel, atten);
//     } else {
//         adc2_config_channel_atten((adc2_channel_t)channel, atten);
//     }
//
//     //Characterize ADC
//     adc_chars = calloc(1, sizeof(esp_adc_cal_characteristics_t));
//     esp_adc_cal_value_t val_type = esp_adc_cal_characterize(unit, atten, ADC_WIDTH_BIT_12, DEFAULT_VREF, adc_chars);
//     print_char_val_type(val_type);
// }

static int64_t get_time_us()
{
    //Get time in us according to
    //https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/system_time.html
    struct timeval tv_now;
    gettimeofday(&tv_now, NULL);
    return (int64_t)tv_now.tv_sec * 1000000L + (int64_t)tv_now.tv_usec;
}

static void reset_speed_sensor()
{
    for (size_t i=0; i < SPEED_SENSOR_WINDOW_SIZE; ++i)
    {
        speed_sensor_intervals[i] = 0;
    }
    speed_sensor_ticks_per_second = 0;
    ir_sensor_tick_counter = 0;
}

// Called in speed_sensor_task whenever a gpio event is detected from the IR sensor.
// This function is used to determine speed_sensor_ticks_per_second,
// which is to be transmitted in udp_transmit_task().
static void IRAM_ATTR ir_sensor_tick()
{
    int64_t dt_us = get_time_us() - ir_sensor_last_tick_time_us;
    ir_sensor_last_tick_time_us = get_time_us();

    ESP_LOGI(TAG, "speed sensor tick %d in %d us!", ir_sensor_tick_counter + 1, (uint32_t) dt_us);

    ir_sensor_tick_counter++;
    size_t window_end = (ir_sensor_tick_counter - 1) % SPEED_SENSOR_WINDOW_SIZE;
    speed_sensor_intervals[window_end] = dt_us;

    int64_t intervals_sum_us = 0;
    for (size_t i=0; i < SPEED_SENSOR_WINDOW_SIZE; ++i)
    {
        intervals_sum_us += speed_sensor_intervals[i];
    }
    speed_sensor_ticks_per_second = 1e6 / (intervals_sum_us / SPEED_SENSOR_WINDOW_SIZE);
}

static void speed_sensor_task(void *pvParameters)
{
    uint32_t io_num;
    for (;;)
    {
        if (speed_sensor_gpio_queue == 0) continue;
        int64_t dt_us = get_time_us() - ir_sensor_last_tick_time_us;

        // Block for SPEED_SENSOR_QUEUE_INTV_TICKS if a message is not immediately available:
        if (xQueueReceive(speed_sensor_gpio_queue, &io_num, pdMS_TO_TICKS(50)))
        {
            if (dt_us < SPEED_SENSOR_MIN_TICK_TIME_MS * 1000)
            {
                continue;
            }
            if (IR_SENSOR_HAS_EN_PIN) {
                // Disabling IR sensor regularly b/c of automatic gain control:
                //  http://irsensor.wizecode.com/
                // Also to hopefully avoid some of the phantom ticks.
                gpio_set_level(GPIO_PIN_IR_SENSOR_EN, 0);
                gpio_intr_disable(GPIO_PIN_IR_SENSOR);
            }

            ir_sensor_tick();

            if (IR_SENSOR_HAS_EN_PIN) {
                vTaskDelay(pdMS_TO_TICKS(3));
                gpio_set_level(GPIO_PIN_IR_SENSOR_EN, 1);
                vTaskDelay(pdMS_TO_TICKS(1));
                gpio_intr_enable(GPIO_PIN_IR_SENSOR);
            }
        }
        else if (dt_us > SPEED_SENSOR_TIMEOUT_US)
        {
            reset_speed_sensor();
            continue;
        }
    }
}

//on IRAM_ATTR: https://esp32.com/viewtopic.php?t=4978
//-> Apparently, ensure that this function is stored in RAM, not
//in slower flash memory…
static void IRAM_ATTR gpio_isr_handler(void* arg)
{
    // Don't run normal C code here!
    // Instead, we push an event to xQueue to be read in speed_sensor_task.

    uint32_t gpio_num = (uint32_t)arg;
    //Should be equal to CONFIG_GPIO_IR_SENSOR if no other pins are used for GPIO?
    xQueueSendFromISR(speed_sensor_gpio_queue, &gpio_num, NULL);
}

static void configure_gpio(void)
{
    // Configuration for the IR sensor input pin:
    gpio_config_t io_conf = {};
    //Interrupt of rising edge:
    io_conf.intr_type = GPIO_INTR_POSEDGE;
    io_conf.pin_bit_mask = GPIO_IR_SENSOR_PIN_BITMASK;
    io_conf.mode = GPIO_MODE_INPUT;
    io_conf.pull_down_en = 0;
    io_conf.pull_up_en = 1;
    int gpioconf_result = gpio_config(&io_conf);
    if (gpioconf_result == ESP_ERR_INVALID_ARG) {
        ESP_LOGE(TAG, "Invalid argument in GPIO configuration for IR input pin");
    }
    ESP_LOGI(TAG, "Ran gpio_config, IR sensor on pin %d", GPIO_PIN_IR_SENSOR);

    if (IR_SENSOR_HAS_EN_PIN) {
        // Configuration for the IR sensor output pin
        // (if it has an enable (EN) pin):
        io_conf.pin_bit_mask = 1ULL << GPIO_PIN_IR_SENSOR_EN;
        io_conf.mode = GPIO_MODE_OUTPUT;
        io_conf.pull_down_en = 1;
        io_conf.pull_up_en = 0;
        gpioconf_result = gpio_config(&io_conf);
        if (gpioconf_result == ESP_ERR_INVALID_ARG) {
            ESP_LOGE(TAG, "Invalid argument in GPIO configuration for IR EN pin");
        }
        gpio_set_level(GPIO_PIN_IR_SENSOR_EN, 1); // Enable IR sensor on startup.
        ESP_LOGI(TAG, "Ran gpio_config, IR sensor EN on pin %d", GPIO_PIN_IR_SENSOR_EN);
    }

    gpio_intr_enable(GPIO_PIN_IR_SENSOR);
    // gpio_set_intr_type(GPIO_PIN_IR_SENSOR, GPIO_INTR_ANYEDGE); // ?

    gpio_install_isr_service(ESP_INTR_FLAG_DEFAULT);
    //hook isr handler for specific gpio pin:
    int isr_result = gpio_isr_handler_add(GPIO_PIN_IR_SENSOR, gpio_isr_handler, (void*) GPIO_PIN_IR_SENSOR);
    switch (isr_result)
    {
        case ESP_OK:
            ESP_LOGI(TAG, "Set up gpio_isr_handler");
            break;
        case ESP_ERR_INVALID_STATE:
            ESP_LOGE(TAG, "Invalid state for gpio_isr_handler_add");
            break;
        case ESP_ERR_INVALID_ARG:
            ESP_LOGE(TAG, "Invalid argument for gpio_isr_handler_add");
            break;
    }

    speed_sensor_gpio_queue = xQueueCreate(10, sizeof(uint32_t));
    xTaskCreate(speed_sensor_task, "speed_sensor_task", 16384, NULL, 5, NULL);
}

void app_main()
{
    ESP_LOGI(TAG, "Starting adc2udp");
    reset_speed_sensor();
    ESP_LOGI(TAG, "Reset speed sensor for the first time");
    // ESP_ERROR_CHECK( nvs_flash_init() );
    // ESP_LOGI(TAG, "checked nvs flash.");
    // configure_adc(); // TODO: remove?
    configure_gpio();
    ESP_LOGI(TAG, "Configured GPIO");
    initialise_wifi();
}
